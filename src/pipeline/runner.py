from typing import Dict, Any, Optional, List
from src.agents.architect import ArchitectAgent, ChapterPlanOutput
from src.agents.writer import WriterAgent, WriteChapterInput
from src.agents.continuity import ContinuityAuditor
from src.agents.auditor import AuditorAgent
from src.llm.provider import LLMClient
import os
import shutil
from datetime import datetime

class PipelineConfig:
    def __init__(self, max_retries: int = 3, min_audit_score: float = 80.0):
        self.max_retries = max_retries
        self.min_audit_score = min_audit_score

class ChapterPipelineResult:
    def __init__(self, chapter_num: int, title: str, content: str, word_count: int, audit_score: float, continuity_score: float, revisions: int, updated_state: str, updated_hooks: str, chapter_summary: str):
        self.chapter_num = chapter_num
        self.title = title
        self.content = content
        self.word_count = word_count
        self.audit_score = audit_score
        self.continuity_score = continuity_score
        self.revisions = revisions
        self.updated_state = updated_state
        self.updated_hooks = updated_hooks
        self.chapter_summary = chapter_summary

class PipelineRunner:
    def __init__(self, llm_client: LLMClient, config: PipelineConfig = PipelineConfig()):
        self.llm_client = llm_client
        self.config = config
        self.architect = ArchitectAgent(llm_client)
        self.writer = WriterAgent(llm_client)
        self.checker = ContinuityAuditor(llm_client)
        self.author = AuditorAgent(llm_client)

    def run(self, book: Dict[str, Any], chapter_num: int, external_context: Optional[str] = None, word_count_override: Optional[int] = None, book_dir: Optional[str] = None) -> Dict[str, Any]:
        """Run the full 4-agent workflow for chapter generation"""
        retries = 0
        
        while retries < self.config.max_retries:
            try:
                # 1. Architect: Plan chapter content
                print(f"[Architect] Planning chapter {chapter_num}...")
                current_state = self._read_file(book_dir, "current_state.md")
                previous_summary = self._get_previous_summary(book_dir, chapter_num)
                
                # 调用架构师的plan_chapter方法
                chapter_plan = self.architect.plan_chapter(
                    book=book,
                    chapter_num=chapter_num,
                    current_state=current_state,
                    previous_chapter_summary=previous_summary,
                    external_context=external_context
                )
                
                # 2. Writer: Generate chapter content
                print(f"[Writer] Writing chapter {chapter_num}...")
                write_input = WriteChapterInput(
                    book=book,
                    chapter_number=chapter_num,
                    chapter_plan={
                        'chapter_outline': chapter_plan.chapter_outline,
                        'character_states': chapter_plan.character_states,
                        'setting': chapter_plan.setting,
                        'plot_points': chapter_plan.plot_points
                    },
                    external_context=external_context,
                    word_count_override=word_count_override,
                    book_dir=book_dir
                )
                writer_output = self.writer.write_chapter(write_input)
                
                # 3. Checker: Check continuity
                print(f"[Checker] Checking continuity for chapter {chapter_num}...")
                checker_result = self.checker.check_continuity(
                    book_title=book.get('title', 'Unknown'),
                    chapter_num=chapter_num,
                    chapter_content=writer_output.content,
                    previous_summary=previous_summary,
                    current_state=writer_output.updated_state
                )
                
                if not checker_result['passed']:
                    print(f"[Checker] Continuity check failed: {checker_result['issues']}")
                    retries += 1
                    continue
                
                # 4. Author: Audit and score
                print(f"[Author] Auditing chapter {chapter_num}...")
                author_result = self.author.score_chapter(
                    content=writer_output.content,
                    book=book,
                    chapter_num=chapter_num
                )
                
                if author_result['score'] < self.config.min_audit_score:
                    print(f"[Author] Audit score too low: {author_result['score']}")
                    retries += 1
                    continue
                
                # All checks passed
                print(f"[Pipeline] Chapter {chapter_num} completed successfully")
                return {
                    'chapter_num': chapter_num,
                    'title': writer_output.title,
                    'content': writer_output.content,
                    'word_count': writer_output.word_count,
                    'audit_score': author_result['score'],
                    'continuity_score': checker_result['score'],
                    'revisions': retries,
                    'updated_state': writer_output.updated_state,
                    'updated_hooks': writer_output.updated_hooks,
                    'chapter_summary': writer_output.chapter_summary,
                    'updated_ledger': writer_output.updated_ledger,
                    'updated_subplots': writer_output.updated_subplots,
                    'updated_emotional_arcs': writer_output.updated_emotional_arcs,
                    'updated_character_matrix': writer_output.updated_character_matrix
                }
                
            except Exception as e:
                print(f"[Pipeline] Error: {str(e)}")
                retries += 1
                continue
        
        # Max retries reached
        raise Exception(f"Failed to generate chapter after {self.config.max_retries} retries")

    def _get_previous_summary(self, book_dir: Optional[str], chapter_num: int) -> str:
        """Get summary of previous chapter"""
        if not book_dir or chapter_num == 1:
            return ""
        
        summary_file = os.path.join(book_dir, "chapter_summaries.md")
        if os.path.exists(summary_file):
            try:
                with open(summary_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Extract summary for chapter_num - 1
                    import re
                    pattern = r"## 第" + str(chapter_num - 1) + r"章[\s\S]*?(?=## 第" + str(chapter_num) + r"章|$)"
                    match = re.search(pattern, content)
                    if match:
                        return match.group(0)
            except Exception:
                pass
        return ""

    def _read_file(self, book_dir: Optional[str], filename: str) -> str:
        """读取文件内容"""
        if not book_dir:
            return f"({filename.replace('.md', '').replace('_', ' ')}尚未创建)"
        
        file_path = os.path.join(book_dir, filename)
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception:
                return f"({filename.replace('.md', '').replace('_', ' ')}读取失败)"
        return f"({filename.replace('.md', '').replace('_', ' ')}尚未创建)"

    def create_book_foundation(self, book: Dict[str, Any], external_context: Optional[str] = None) -> Dict[str, Any]:
        """创建书籍基础设定"""
        print(f"[Architect] Creating book foundation for {book.get('title', 'Unknown')}...")
        foundation = self.architect.generate_foundation(book, external_context)
        
        return {
            'story_bible': foundation.story_bible,
            'volume_outline': foundation.volume_outline,
            'book_rules': foundation.book_rules,
            'current_state': foundation.current_state,
            'pending_hooks': foundation.pending_hooks
        }

    def rewrite_chapter(self, book: Dict[str, Any], chapter_num: int, external_context: Optional[str] = None, word_count_override: Optional[int] = None, book_dir: Optional[str] = None) -> Dict[str, Any]:
        """重写章节"""
        print(f"[Pipeline] Rewriting chapter {chapter_num}...")
        return self.run(book, chapter_num, external_context, word_count_override, book_dir)

    def rewrite_from_chapter(self, book: Dict[str, Any], chapter_num: int, external_context: Optional[str] = None, word_count_override: Optional[int] = None, book_dir: Optional[str] = None) -> Dict[str, Any]:
        """从指定章节开始重写"""
        print(f"[Pipeline] Rewriting from chapter {chapter_num}...")
        # 这里可以添加删除后续章节的逻辑
        return self.run(book, chapter_num, external_context, word_count_override, book_dir)

    def audit_chapter(self, content: str, book: Dict[str, Any], chapter_num: int) -> Dict[str, Any]:
        """审核章节内容"""
        print(f"[Author] Auditing chapter {chapter_num}...")
        return self.author.score_chapter(
            content=content,
            book=book,
            chapter_num=chapter_num
        )

    def update_story_outline(self, book: Dict[str, Any], new_outline: str, outline_context: Optional[str] = None, book_dir: Optional[str] = None) -> Dict[str, Any]:
        """修改故事大纲"""
        print(f"[Architect] Updating story outline for {book.get('title', 'Unknown')}...")
        
        # 分析大纲变化
        old_outline = book.get('outline', '')
        outline_change_ratio = len(new_outline) / len(old_outline) if old_outline else 0
        
        # 备份数据
        backup_dir = self._backup_book_data(book_dir, book['id'])
        
        # 分析大纲变化对现有章节的影响
        impact_analysis = self.architect.analyze_outline_impact(
            old_outline=old_outline,
            new_outline=new_outline,
            book=book,
            outline_context=outline_context
        )
        
        return {
            'backup_dir': backup_dir,
            'outline_change_ratio': outline_change_ratio,
            'impact_analysis': impact_analysis,
            'recommendation': self._generate_recommendation(outline_change_ratio, impact_analysis)
        }

    def _backup_book_data(self, book_dir: Optional[str], book_id: int) -> str:
        """备份书籍数据"""
        if not book_dir or not os.path.exists(book_dir):
            return ""
        
        backup_dir = os.path.join('data', f'backup_{book_id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
        shutil.copytree(book_dir, backup_dir)
        return backup_dir

    def _generate_recommendation(self, outline_change_ratio: float, impact_analysis: Dict[str, Any]) -> str:
        """生成大纲修改建议"""
        if outline_change_ratio > 1.5 or outline_change_ratio < 0.5:
            return "大纲变化较大，建议重开一本书或从第一章开始重写"
        elif impact_analysis.get('major_impact', False):
            return "大纲变化对现有章节有重大影响，建议从受影响的章节开始重写"
        elif impact_analysis.get('minor_impact', False):
            return "大纲变化对现有章节有轻微影响，建议修改后续章节"
        else:
            return "大纲变化对现有章节无影响，可以直接更新"

    def continue_next_chapter(self, book: Dict[str, Any], chapter_num: int, external_context: Optional[str] = None, word_count_override: Optional[int] = None, book_dir: Optional[str] = None) -> Dict[str, Any]:
        """续写下一章"""
        print(f"[Pipeline] Continuing with chapter {chapter_num}...")
        result = self.run(book, chapter_num, external_context, word_count_override, book_dir)
        
        # 5. 更新各个md内容
        print(f"[Architect] Updating book state files...")
        update_result = self.architect.update_book_state(
            book=book,
            chapter_num=chapter_num,
            chapter_content=result['content'],
            chapter_summary=result['chapter_summary'],
            current_state=result['updated_state'],
            pending_hooks=result['updated_hooks'],
            book_dir=book_dir
        )
        
        result.update({
            'state_update': update_result
        })
        
        return result
