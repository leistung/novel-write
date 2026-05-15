"""连续性检查Agent"""
import re
from typing import Dict, Any, List

from sqlalchemy.ext.asyncio import AsyncSession

from agents.base import BaseAgent, AgentResult
from db.crud import get_book, get_chapter_by_number, get_chapters_by_book


class ContinuityAuditor(BaseAgent):
    """连续性检查Agent - 负责连贯性检查
    
    Public Methods (2个):
    1. check_continuity - 检查章节连续性
    2. check_character_consistency - 检查角色一致性
    """
    
    PASS_SCORE = 80
    
    def __init__(self):
        super().__init__("ContinuityAuditor")
    
    async def execute(self, task: str, **kwargs) -> AgentResult:
        """执行连续性检查任务"""
        if task == "check_continuity":
            return await self.check_continuity(**kwargs)
        elif task == "check_character_consistency":
            return await self.check_character_consistency(**kwargs)
        else:
            return self.failure(task, f"未知任务: {task}")
    
    # ==================== PUBLIC METHODS ====================
    
    async def check_continuity(
        self,
        book_id: int,
        chapter_num: int,
        chapter_content: str,
        db: AsyncSession = None,
        **kwargs
    ) -> AgentResult:
        """【Public】检查章节连续性
        
        检查新章节与前面章节的连贯性:
        - 情节衔接
        - 角色一致性
        - 时间线连贯
        - 伏笔呼应
        """
        if db is None:
            return self.failure("check_continuity", "需要数据库会话")
        
        book = await get_book(db, book_id)
        if not book:
            return self.failure("check_continuity", f"书籍不存在: {book_id}")
        
        # 获取前一章内容
        prev_chapter = await get_chapter_by_number(db, book_id, chapter_num - 1)
        prev_content = prev_chapter.content if prev_chapter else ""
        
        system_prompt = self._build_system_prompt(self._get_continuity_system_prompt(), book.genre)
        user_prompt = self._get_continuity_user_prompt(
            book=book,
            chapter_num=chapter_num,
            prev_content=prev_content,
            new_content=chapter_content
        )
        
        try:
            response = await self.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.5,
                max_tokens=4000
            )
            
            # 解析评分
            score = self._parse_score(response.content)
            passed = score >= self.PASS_SCORE
            
            return self.success(
                task="check_continuity",
                data={
                    "score": score,
                    "passed": passed,
                    "report": response.content,
                    "chapter_num": chapter_num
                },
                score=score,
                feedback="连续性检查通过" if passed else f"连续性检查未通过(需{self.PASS_SCORE}分)",
                token_usage={
                    "prompt_tokens": response.prompt_tokens,
                    "completion_tokens": response.completion_tokens,
                    "total_tokens": response.total_tokens
                }
            )
        except Exception as e:
            return self.failure("check_continuity", str(e))
    
    async def check_character_consistency(
        self,
        book_id: int,
        character_name: str,
        db: AsyncSession = None,
        **kwargs
    ) -> AgentResult:
        """【Public】检查角色全书一致性
        
        检查特定角色在全书中的一致性:
        - 性格一致性
        - 能力变化合理性
        - 关系变化合理性
        """
        if db is None:
            return self.failure("check_character_consistency", "需要数据库会话")
        
        book = await get_book(db, book_id)
        if not book:
            return self.failure("check_character_consistency", f"书籍不存在: {book_id}")
        
        # 获取包含该角色的章节
        chapters = await get_chapters_by_book(db, book_id)
        character_appearances = []
        
        for ch in chapters:
            if character_name in ch.content:
                character_appearances.append({
                    "chapter_num": ch.chapter_number,
                    "title": ch.title,
                    "content_snippet": self._extract_character_snippet(ch.content, character_name)
                })
        
        system_prompt = self._build_system_prompt(self._get_character_check_system_prompt(), book.genre)
        user_prompt = self._get_character_check_user_prompt(
            book=book,
            character_name=character_name,
            appearances=character_appearances
        )
        
        try:
            response = await self.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.5,
                max_tokens=4000
            )
            
            return self.success(
                task="check_character_consistency",
                data={
                    "character_name": character_name,
                    "appearances_count": len(character_appearances),
                    "consistency_report": response.content
                },
                feedback=f"完成角色'{character_name}'的一致性检查",
                token_usage={
                    "prompt_tokens": response.prompt_tokens,
                    "completion_tokens": response.completion_tokens,
                    "total_tokens": response.total_tokens
                }
            )
        except Exception as e:
            return self.failure("check_character_consistency", str(e))
    
    # ==================== PRIVATE METHODS ====================
    
    def _get_continuity_system_prompt(self) -> str:
        """【Private】获取连续性检查系统提示词"""
        return """你是一位专业的小说连续性审计员，负责检查章节的连贯性。

检查维度：
1. 情节衔接：新章节是否承接上一章结尾
2. 角色一致性：角色行为是否符合设定
3. 时间线连贯：时间推进是否合理
4. 场景连续性：场景转换是否自然
5. 伏笔呼应：伏笔是否得到正确处理

评分标准（0-100）：
- 90-100：完美衔接，无问题
- 80-89：基本连贯，小问题
- 60-79：有明显断层
- 0-59：严重不连贯

输出格式：
分数：XX分
通过：（是/否）

## 检查报告
（详细报告）

## 情节断层
（如有）

## 人物断层
（如有）

## 场景断层
（如有）

## 建议
（改进建议）
"""
    
    def _get_continuity_user_prompt(
        self,
        book,
        chapter_num: int,
        prev_content: str,
        new_content: str
    ) -> str:
        """【Private】获取连续性检查用户提示词"""
        return f"""请检查第{chapter_num}章的连续性：

小说：{book.title}（{book.genre}）

前一章结尾（最后500字）：
{prev_content[-500:] if prev_content else "（这是第一章）"}

新章节开头（前500字）：
{new_content[:500]}

新章节内容概要：
{new_content[:1000]}

请检查两章之间的连续性。
"""
    
    def _get_character_check_system_prompt(self) -> str:
        """【Private】获取角色检查系统提示词"""
        return """你是一位专业的角色分析师，负责检查角色在全书中的一致性。

检查维度：
1. 性格一致性：性格是否前后一致
2. 能力变化：能力提升是否合理
3. 关系变化：关系发展是否自然
4. 价值观：价值观是否稳定

输出格式：
一致性评分：XX分

## 性格分析
## 能力轨迹
## 关系演变
## 发现的问题
## 建议
"""
    
    def _get_character_check_user_prompt(
        self,
        book,
        character_name: str,
        appearances: List[Dict]
    ) -> str:
        """【Private】获取角色检查用户提示词"""
        appearances_text = "\n\n".join([
            f"第{a['chapter_num']}章:\n{a['content_snippet']}"
            for a in appearances[:5]  # 只取前5次出场
        ])
        
        return f"""请检查角色'{character_name}'在全书中的一致性：

小说：{book.title}（{book.genre}）

角色出场记录：
{appearances_text}

角色矩阵：
{book.character_matrix[:500] if book.character_matrix else "暂无"}

请分析该角色的一致性。
"""
    
    def _parse_score(self, content: str) -> float:
        """【Private】解析分数"""
        match = re.search(r'分数[：:]\s*(\d+)', content)
        if match:
            return float(match.group(1))
        
        # 尝试其他格式
        match = re.search(r'(\d+)\s*分', content)
        if match:
            return float(match.group(1))
        
        return 0.0
    
    def _extract_character_snippet(self, content: str, character_name: str, context: int = 200) -> str:
        """【Private】提取角色出场片段"""
        idx = content.find(character_name)
        if idx == -1:
            return ""
        
        start = max(0, idx - context)
        end = min(len(content), idx + context)
        return content[start:end]
