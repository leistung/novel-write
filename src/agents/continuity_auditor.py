"""ContinuityAuditor - 连续性审核 Agent，负责检查章节内容的连续性"""
from typing import Dict, Any, Optional, List, Tuple
from src.agents.base import BaseAgent, AgentContext
from src.prompts import CONSISTENCY_PROMPTS
import os
import re

class ContinuityCheckResult:
    """连续性检查结果"""
    def __init__(self, is_consistent: bool, score: int, 
                 consistency_report: str, plot_breaks: List[str], 
                 character_breaks: List[str], setting_breaks: List[str],
                 suggestions: str, warning_count: int, error_count: int):
        self.is_consistent = is_consistent
        self.score = score
        self.consistency_report = consistency_report
        self.plot_breaks = plot_breaks
        self.character_breaks = character_breaks
        self.setting_breaks = setting_breaks
        self.suggestions = suggestions
        self.warning_count = warning_count
        self.error_count = error_count

class ContinuityAuditor(BaseAgent):
    """连续性审核 Agent - 负责检查章节内容的情节连续性和文本一致性"""
    
    def __init__(self, llm):
        super().__init__(llm)
    
    def check_chapter_consistency(self, book: Dict[str, Any], chapter_num: int, 
                                 chapter_content: str, previous_chapter: str,
                                 book_dir: Optional[str] = None) -> ContinuityCheckResult:
        """检查章节连续性
        
        Args:
            book: 书籍信息字典
            chapter_num: 章节号
            chapter_content: 当前章节内容
            previous_chapter: 上一章内容
            book_dir: 书籍目录路径
        
        Returns:
            ContinuityCheckResult: 连续性检查结果对象
        """
        genre = book.get('genre', '未知')
        title = book.get('title', '未知')

        # 加载状态文件
        story_bible = self._read_file(book_dir, "story_bible.md") if book_dir else ""
        current_state = self._read_file(book_dir, "current_state.md") if book_dir else ""
        character_matrix = self._read_file(book_dir, "character_matrix.md") if book_dir else ""
        chapter_summaries = self._read_file(book_dir, "chapter_summaries.md") if book_dir else ""

        # 获取题材技能增强
        genre_enhancement = self.get_genre_enhancement(genre)

        # 构建系统提示
        system_prompt = CONSISTENCY_PROMPTS["check_consistency"].format(
            genre=genre,
            title=title,
            chapter_num=chapter_num,
            genre_enhancement=genre_enhancement if genre_enhancement else ""
        )

        # 构建用户提示
        user_prompt = self._build_consistency_user_prompt(
            chapter_num, chapter_content, previous_chapter,
            story_bible, current_state, character_matrix, chapter_summaries
        )

        # 创建提示词并运行
        prompt = self.create_prompt(system_prompt, user_prompt)
        response = self.run_chain(prompt)

        # 解析输出
        return self._parse_consistency_response(response['content'])
    
    def check_outline_consistency(self, book: Dict[str, Any], outline: str, 
                                 book_dir: Optional[str] = None) -> Dict[str, Any]:
        """检查大纲与已有设定的一致性
        
        Args:
            book: 书籍信息字典
            outline: 章节大纲内容
            book_dir: 书籍目录路径
        
        Returns:
            Dict[str, Any]: 包含 is_consistent 和 suggestions 的检查结果
        """
        genre = book.get('genre', '未知')
        title = book.get('title', '未知')

        # 加载状态文件
        story_bible = self._read_file(book_dir, "story_bible.md") if book_dir else ""
        volume_outline = self._read_file(book_dir, "volume_outline.md") if book_dir else ""
        current_state = self._read_file(book_dir, "current_state.md") if book_dir else ""

        # 获取题材技能增强
        genre_enhancement = self.get_genre_enhancement(genre)

        # 构建系统提示
        system_prompt = CONSISTENCY_PROMPTS["check_outline"].format(
            genre=genre,
            title=title,
            genre_enhancement=genre_enhancement if genre_enhancement else ""
        )

        # 构建用户提示
        user_prompt = f"""## 待审核大纲\n{outline}\n\n## 故事圣经\n{story_bible}\n\n## 卷纲\n{volume_outline}\n\n## 当前状态\n{current_state}\n\n请审核上述大纲是否与已有设定保持一致。"""

        # 创建提示词并运行
        prompt = self.create_prompt(system_prompt, user_prompt)
        response = self.run_chain(prompt)

        # 解析结果
        content = response['content']
        is_consistent = "一致" in content or "通过" in content

        return {
            'is_consistent': is_consistent,
            'suggestions': content
        }
    
    def _build_consistency_user_prompt(self, chapter_num: int, chapter_content: str, 
                                      previous_chapter: str, story_bible: str, 
                                      current_state: str, character_matrix: str,
                                      chapter_summaries: str) -> str:
        """构建连续性检查用户提示"""
        summaries_block = f"\n## 章节摘要\n{chapter_summaries}\n" if chapter_summaries and chapter_summaries != "(章节摘要尚未创建)" else ""
        matrix_block = f"\n## 角色交互矩阵\n{character_matrix}\n" if character_matrix and character_matrix != "(角色交互矩阵尚未创建)" else ""
        
        return f"""请检查第{chapter_num}章的连续性。

## 当前章节内容
{chapter_content}

## 上一章内容
{previous_chapter}

{summaries_block}
{matrix_block}

## 世界观设定
{story_bible}

## 当前状态卡
{current_state}

请按照要求的格式输出连续性检查报告。"""
    
    def _parse_consistency_response(self, content: str) -> ContinuityCheckResult:
        """解析连续性检查响应"""
        # 提取分数
        score_match = re.search(r'分数：(\d+)', content)
        score = int(score_match.group(1)) if score_match else 0
        
        # 判断是否通过
        is_consistent = score >= 80
        
        # 提取报告内容
        report_start = content.find("## 检查报告")
        report_end = content.find("## 建议")
        consistency_report = content[report_start:report_end].strip() if report_start != -1 and report_end != -1 else ""
        
        # 提取建议
        suggestions_start = content.find("## 建议")
        suggestions = content[suggestions_start:].strip() if suggestions_start != -1 else ""
        
        # 统计错误和警告
        error_count = content.count("错误")
        warning_count = content.count("警告")
        
        # 提取问题列表
        plot_breaks = []
        character_breaks = []
        setting_breaks = []
        
        if "情节断层" in content:
            plot_section = content.split("情节断层")[1].split("人物断层")[0] if "人物断层" in content else content.split("情节断层")[1]
            plot_breaks = [line.strip() for line in plot_section.split("\n") if line.strip()]
        
        if "人物断层" in content:
            char_section = content.split("人物断层")[1].split("场景断层")[0] if "场景断层" in content else content.split("人物断层")[1]
            character_breaks = [line.strip() for line in char_section.split("\n") if line.strip()]
        
        if "场景断层" in content:
            setting_section = content.split("场景断层")[1]
            setting_breaks = [line.strip() for line in setting_section.split("\n") if line.strip()]
        
        return ContinuityCheckResult(
            is_consistent=is_consistent,
            score=score,
            consistency_report=consistency_report,
            plot_breaks=plot_breaks,
            character_breaks=character_breaks,
            setting_breaks=setting_breaks,
            suggestions=suggestions,
            warning_count=warning_count,
            error_count=error_count
        )
    
    def _read_file(self, book_dir: str, filename: str) -> str:
        """读取文件内容"""
        if not book_dir:
            return ""
        
        file_path = os.path.join(book_dir, filename)
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception:
                return ""
        return ""
    
    def execute(self, context: AgentContext) -> Dict[str, Any]:
        """执行 Agent 核心逻辑
        
        Args:
            context: 执行上下文
        
        Returns:
            Dict[str, Any]: 执行结果
        """
        task_type = context.get('task_type', 'check_chapter_consistency')
        
        if task_type == 'check_chapter_consistency':
            book = context.get('book', {})
            chapter_num = context.chapter_num or 1
            chapter_content = context.get('chapter_content', '')
            previous_chapter = context.get('previous_chapter', '')
            book_dir = context.get('book_dir')
            
            result = self.check_chapter_consistency(book, chapter_num, chapter_content, previous_chapter, book_dir)
            
            return {
                'is_consistent': result.is_consistent,
                'score': result.score,
                'consistency_report': result.consistency_report,
                'plot_breaks': result.plot_breaks,
                'character_breaks': result.character_breaks,
                'setting_breaks': result.setting_breaks,
                'suggestions': result.suggestions,
                'warning_count': result.warning_count,
                'error_count': result.error_count
            }
        
        elif task_type == 'check_outline_consistency':
            book = context.get('book', {})
            outline = context.get('outline', '')
            book_dir = context.get('book_dir')
            
            return self.check_outline_consistency(book, outline, book_dir)
        
        else:
            raise ValueError(f"未知任务类型: {task_type}")