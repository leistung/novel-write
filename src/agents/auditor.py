"""AuditorAgent - 评分审核 Agent，负责对章节内容进行综合评分"""
from typing import Dict, Any, Optional, List
from src.agents.base import BaseAgent, AgentContext
from src.prompts import AUTHOR_PROMPTS
import os

class ScoreResult:
    """评分结果"""
    def __init__(self, score: int, detailed_scores: Dict[str, int], 
                 comments: str, suggestions: str, passed: bool):
        self.score = score
        self.detailed_scores = detailed_scores
        self.comments = comments
        self.suggestions = suggestions
        self.passed = passed

class AuditorAgent(BaseAgent):
    """评分审核 Agent - 负责对章节内容进行综合评分和审核"""
    
    def __init__(self, llm):
        super().__init__(llm)
        self._pass_threshold = 80  # 通过阈值
    
    def score_chapter(self, book: Dict[str, Any], chapter_num: int, 
                     chapter_content: str, chapter_summary: str,
                     book_dir: Optional[str] = None) -> ScoreResult:
        """对章节进行评分
        
        Args:
            book: 书籍信息字典
            chapter_num: 章节号
            chapter_content: 章节内容
            chapter_summary: 章节摘要
            book_dir: 书籍目录路径
        
        Returns:
            ScoreResult: 评分结果对象
        """
        genre = book.get('genre', '未知')
        title = book.get('title', '未知')
        platform = book.get('platform', '其他')

        # 加载相关文件
        story_bible = self._read_file(book_dir, "story_bible.md") if book_dir else ""
        volume_outline = self._read_file(book_dir, "volume_outline.md") if book_dir else ""
        current_state = self._read_file(book_dir, "current_state.md") if book_dir else ""
        chapter_summaries = self._read_file(book_dir, "chapter_summaries.md") if book_dir else ""
        character_matrix = self._read_file(book_dir, "character_matrix.md") if book_dir else ""

        # 获取题材技能增强
        genre_enhancement = self.get_genre_enhancement(genre)

        # 构建系统提示
        system_prompt = AUTHOR_PROMPTS["score_chapter"].format(
            genre=genre,
            title=title,
            platform=platform,
            pass_threshold=self._pass_threshold,
            genre_enhancement=genre_enhancement if genre_enhancement else ""
        )

        # 构建用户提示
        user_prompt = self._build_score_user_prompt(
            chapter_num, chapter_content, chapter_summary,
            story_bible, volume_outline, current_state,
            chapter_summaries, character_matrix
        )

        # 创建提示词并运行
        prompt = self.create_prompt(system_prompt, user_prompt)
        response = self.run_chain(prompt)

        # 解析输出
        return self._parse_score_response(response['content'])
    
    def evaluate_book(self, book: Dict[str, Any], book_dir: str) -> Dict[str, Any]:
        """评估整本书的质量
        
        Args:
            book: 书籍信息字典
            book_dir: 书籍目录路径
        
        Returns:
            Dict[str, Any]: 评估结果
        """
        genre = book.get('genre', '未知')
        title = book.get('title', '未知')

        # 加载相关文件
        story_bible = self._read_file(book_dir, "story_bible.md")
        volume_outline = self._read_file(book_dir, "volume_outline.md")
        chapter_summaries = self._read_file(book_dir, "chapter_summaries.md")

        # 获取题材技能增强
        genre_enhancement = self.get_genre_enhancement(genre)

        # 构建系统提示
        system_prompt = AUTHOR_PROMPTS["evaluate_book"].format(
            genre=genre,
            title=title,
            genre_enhancement=genre_enhancement if genre_enhancement else ""
        )

        # 构建用户提示
        user_prompt = f"""## 故事圣经\n{story_bible}\n\n## 卷纲\n{volume_outline}\n\n## 章节摘要\n{chapter_summaries}\n\n请对整本书进行综合评估。"""

        # 创建提示词并运行
        prompt = self.create_prompt(system_prompt, user_prompt)
        response = self.run_chain(prompt)

        return {
            'evaluation': response['content']
        }
    
    def _build_score_user_prompt(self, chapter_num: int, chapter_content: str, 
                                chapter_summary: str, story_bible: str,
                                volume_outline: str, current_state: str,
                                chapter_summaries: str, character_matrix: str) -> str:
        """构建评分用户提示"""
        summaries_block = f"\n## 章节摘要\n{chapter_summaries}\n" if chapter_summaries and chapter_summaries != "(章节摘要尚未创建)" else ""
        matrix_block = f"\n## 角色交互矩阵\n{character_matrix}\n" if character_matrix and character_matrix != "(角色交互矩阵尚未创建)" else ""
        
        return f"""请对第{chapter_num}章进行评分。

## 章节内容
{chapter_content}

## 章节摘要
{chapter_summary}

{summaries_block}
{matrix_block}

## 世界观设定
{story_bible}

## 卷纲
{volume_outline}

## 当前状态卡
{current_state}

请按照要求的格式输出评分结果。"""
    
    def _parse_score_response(self, content: str) -> ScoreResult:
        """解析评分响应"""
        import re
        
        # 提取总分
        total_match = re.search(r'总分：(\d+)', content)
        score = int(total_match.group(1)) if total_match else 0
        
        # 提取各项分数
        detailed_scores = {}
        
        # 情节一致性
        plot_match = re.search(r'情节一致性：(\d+)', content)
        if plot_match:
            detailed_scores['plot_consistency'] = int(plot_match.group(1))
        
        # 文本一致性
        text_match = re.search(r'文本一致性：(\d+)', content)
        if text_match:
            detailed_scores['text_consistency'] = int(text_match.group(1))
        
        # 人物表现
        character_match = re.search(r'人物表现：(\d+)', content)
        if character_match:
            detailed_scores['character_performance'] = int(character_match.group(1))
        
        # 文笔质量
        writing_match = re.search(r'文笔质量：(\d+)', content)
        if writing_match:
            detailed_scores['writing_quality'] = int(writing_match.group(1))
        
        # 提取评语
        comments_start = content.find("## 评语")
        suggestions_start = content.find("## 建议")
        comments = ""
        suggestions = ""
        
        if comments_start != -1:
            if suggestions_start != -1:
                comments = content[comments_start:suggestions_start].strip()
                suggestions = content[suggestions_start:].strip()
            else:
                comments = content[comments_start:].strip()
        
        # 判断是否通过
        explicit_failed = "通过：否" in content or "不通过" in content
        passed = score >= self._pass_threshold and not explicit_failed
        
        return ScoreResult(
            score=score,
            detailed_scores=detailed_scores,
            comments=comments,
            suggestions=suggestions,
            passed=passed
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
        task_type = context.get('task_type', 'score_chapter')
        
        if task_type == 'score_chapter':
            book = context.get('book', {})
            chapter_num = context.chapter_num or 1
            chapter_content = context.get('chapter_content', '')
            chapter_summary = context.get('chapter_summary', '')
            book_dir = context.get('book_dir')
            
            result = self.score_chapter(book, chapter_num, chapter_content, chapter_summary, book_dir)
            
            return {
                'score': result.score,
                'detailed_scores': result.detailed_scores,
                'comments': result.comments,
                'suggestions': result.suggestions,
                'passed': result.passed
            }
        
        elif task_type == 'evaluate_book':
            book = context.get('book', {})
            book_dir = context.get('book_dir', '')
            
            return self.evaluate_book(book, book_dir)
        
        else:
            raise ValueError(f"未知任务类型: {task_type}")
