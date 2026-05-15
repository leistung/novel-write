"""审核编辑Agent"""
import re
from typing import Dict, Any, List

from sqlalchemy.ext.asyncio import AsyncSession

from agents.base import BaseAgent, AgentResult
from db.crud import get_book, get_chapters_by_book


class AuditorAgent(BaseAgent):
    """审核编辑Agent - 负责质量评估
    
    Public Methods (3个):
    1. audit_chapter - 审核章节质量
    2. audit_book - 整书审核
    3. compare_versions - 对比版本
    """
    
    PASS_THRESHOLD = 80
    
    def __init__(self):
        super().__init__("Auditor")
    
    async def execute(self, task: str, **kwargs) -> AgentResult:
        """执行审核任务"""
        if task == "audit_chapter":
            return await self.audit_chapter(**kwargs)
        elif task == "audit_book":
            return await self.audit_book(**kwargs)
        elif task == "compare_versions":
            return await self.compare_versions(**kwargs)
        else:
            return self.failure(task, f"未知任务: {task}")
    
    # ==================== PUBLIC METHODS ====================
    
    async def audit_chapter(
        self,
        book_id: int,
        chapter_num: int,
        chapter_content: str,
        db: AsyncSession = None,
        **kwargs
    ) -> AgentResult:
        """【Public】审核章节质量
        
        多维度评分:
        - 情节一致性
        - 文本质量
        - 人物表现
        - 文笔评分
        """
        if db is None:
            return self.failure("audit_chapter", "需要数据库会话")
        
        book = await get_book(db, book_id)
        if not book:
            return self.failure("audit_chapter", f"书籍不存在: {book_id}")
        
        system_prompt = self._build_system_prompt(self._get_audit_system_prompt(book.platform), book.genre)
        user_prompt = self._get_audit_user_prompt(
            book=book,
            chapter_num=chapter_num,
            chapter_content=chapter_content
        )
        
        try:
            response = await self.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.5,
                max_tokens=4000
            )
            
            # 解析评分
            scores = self._parse_scores(response.content)
            total_score = scores.get("total", 0)
            passed = total_score >= self.PASS_THRESHOLD
            
            return self.success(
                task="audit_chapter",
                data={
                    "scores": scores,
                    "total_score": total_score,
                    "passed": passed,
                    "audit_report": response.content,
                    "chapter_num": chapter_num
                },
                score=total_score,
                feedback="审核通过" if passed else f"审核未通过(需{self.PASS_THRESHOLD}分)",
                token_usage={
                    "prompt_tokens": response.prompt_tokens,
                    "completion_tokens": response.completion_tokens,
                    "total_tokens": response.total_tokens
                }
            )
        except Exception as e:
            return self.failure("audit_chapter", str(e))
    
    async def audit_book(
        self,
        book_id: int,
        db: AsyncSession = None,
        **kwargs
    ) -> AgentResult:
        """【Public】整书审核
        
        评估整本书的质量和完成度
        """
        if db is None:
            return self.failure("audit_book", "需要数据库会话")
        
        book = await get_book(db, book_id)
        if not book:
            return self.failure("audit_book", f"书籍不存在: {book_id}")
        
        # 获取所有章节
        chapters, _ = await get_chapters_by_book(db, book_id)
        
        system_prompt = self._build_system_prompt(self._get_book_audit_system_prompt(), book.genre)
        user_prompt = self._get_book_audit_user_prompt(
            book=book,
            chapters=chapters
        )
        
        try:
            response = await self.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.5,
                max_tokens=4000
            )
            
            return self.success(
                task="audit_book",
                data={
                    "audit_report": response.content,
                    "total_chapters": len(chapters),
                    "book_id": book_id
                },
                feedback="完成整书审核",
                token_usage={
                    "prompt_tokens": response.prompt_tokens,
                    "completion_tokens": response.completion_tokens,
                    "total_tokens": response.total_tokens
                }
            )
        except Exception as e:
            return self.failure("audit_book", str(e))
    
    async def compare_versions(
        self,
        book_id: int,
        chapter_num: int,
        version_a: str,
        version_b: str,
        db: AsyncSession = None,
        **kwargs
    ) -> AgentResult:
        """【Public】对比两个版本
        
        分析两个版本章节的优劣
        """
        if db is None:
            return self.failure("compare_versions", "需要数据库会话")
        
        book = await get_book(db, book_id)
        if not book:
            return self.failure("compare_versions", f"书籍不存在: {book_id}")
        
        system_prompt = self._build_system_prompt(self._get_compare_system_prompt(), book.genre)
        user_prompt = self._get_compare_user_prompt(
            book=book,
            chapter_num=chapter_num,
            version_a=version_a,
            version_b=version_b
        )
        
        try:
            response = await self.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.5,
                max_tokens=4000
            )
            
            # 解析推荐
            recommendation = self._parse_recommendation(response.content)
            
            return self.success(
                task="compare_versions",
                data={
                    "comparison_report": response.content,
                    "recommendation": recommendation,
                    "chapter_num": chapter_num
                },
                feedback=f"推荐选择: {recommendation}",
                token_usage={
                    "prompt_tokens": response.prompt_tokens,
                    "completion_tokens": response.completion_tokens,
                    "total_tokens": response.total_tokens
                }
            )
        except Exception as e:
            return self.failure("compare_versions", str(e))
    
    # ==================== PRIVATE METHODS ====================
    
    def _get_audit_system_prompt(self, platform: str) -> str:
        """【Private】获取审核系统提示词"""
        return f"""你是一个专业的网络小说审核员，负责审核小说章节质量。
你熟悉{platform}平台的读者偏好，能够准确评估章节质量。

审核维度（每项0-100分）：
1. 情节一致性：情节逻辑连贯，无矛盾
2. 文本质量：语言流畅，无语法错误
3. 人物表现：人物刻画鲜明，性格一致
4. 文笔评分：写作风格符合题材，有吸引力

输出格式：
总分：XX分
通过：（是/否）
情节一致性：XX分
文本质量：XX分
人物表现：XX分
文笔评分：XX分

## 评语
（简要评语）

## 建议
（可执行的改进建议）
"""
    
    def _get_audit_user_prompt(
        self,
        book,
        chapter_num: int,
        chapter_content: str
    ) -> str:
        """【Private】获取审核用户提示词"""
        return f"""请审核以下章节：

小说信息：
- 标题：{book.title}
- 题材：{book.genre}
- 平台：{book.platform}
- 章节：第{chapter_num}章

章节内容（前3000字）：
{chapter_content[:3000]}

请按照审核维度进行评分，通过阈值为80分。
"""
    
    def _get_book_audit_system_prompt(self) -> str:
        """【Private】获取整书审核系统提示词"""
        return """你是一个专业的网络小说审核员，负责评估整本书的质量。

评估维度：
1. 世界观完整性
2. 人物塑造
3. 情节发展
4. 主线清晰度
5. 支线处理
6. 伏笔回收
7. 结局满意度

输出格式：
总评：（一句话总结）
完成度：（0-100）
主要优点：（列表）
主要风险：（列表）
下一步建议：（列表）
"""
    
    def _get_book_audit_user_prompt(self, book, chapters) -> str:
        """【Private】获取整书审核用户提示词"""
        chapter_info = "\n".join([
            f"- 第{ch.chapter_number}章: {ch.title} (字数:{ch.word_count}, 评分:{ch.audit_score})"
            for ch in chapters[:10]  # 只显示前10章
        ])
        
        return f"""请评估整本书的质量：

小说信息：
- 标题：{book.title}
- 题材：{book.genre}
- 总章节：{len(chapters)}章

章节列表（前10章）：
{chapter_info}

世界观设定：
{book.story_bible[:500] if book.story_bible else "暂无"}

请进行全面评估。
"""
    
    def _get_compare_system_prompt(self) -> str:
        """【Private】获取对比系统提示词"""
        return """你是一个专业的小说编辑，负责对比两个版本的章节。

对比维度：
1. 情节完整性
2. 文笔流畅度
3. 人物表现
4. 节奏把控
5. 吸引力

输出格式：
版本A评分：XX分
版本B评分：XX分

## 版本A优点
## 版本A缺点

## 版本B优点
## 版本B缺点

## 推荐选择
（推荐A或B，并说明理由）
"""
    
    def _get_compare_user_prompt(
        self,
        book,
        chapter_num: int,
        version_a: str,
        version_b: str
    ) -> str:
        """【Private】获取对比用户提示词"""
        return f"""请对比第{chapter_num}章的两个版本：

小说：{book.title}（{book.genre}）

版本A：
{version_a[:2000]}

版本B：
{version_b[:2000]}

请进行详细对比并给出推荐。
"""
    
    def _parse_scores(self, content: str) -> Dict[str, float]:
        """【Private】解析评分"""
        scores = {}
        
        # 解析总分
        total_match = re.search(r'总分[：:]\s*(\d+)', content)
        if total_match:
            scores["total"] = float(total_match.group(1))
        
        # 解析各项分数
        patterns = [
            ("plot", r'情节一致性[：:]\s*(\d+)'),
            ("text", r'文本质量[：:]\s*(\d+)'),
            ("character", r'人物表现[：:]\s*(\d+)'),
            ("writing", r'文笔评分[：:]\s*(\d+)')
        ]
        
        for key, pattern in patterns:
            match = re.search(pattern, content)
            if match:
                scores[key] = float(match.group(1))
        
        return scores
    
    def _parse_recommendation(self, content: str) -> str:
        """【Private】解析推荐"""
        if "推荐选择" in content:
            # 提取推荐部分
            match = re.search(r'推荐选择\s*[:：]\s*(.+?)(?:\n|$)', content, re.DOTALL)
            if match:
                rec = match.group(1).strip()
                if "A" in rec:
                    return "A"
                elif "B" in rec:
                    return "B"
        
        # 默认根据评分判断
        score_a = re.search(r'版本A评分[：:]\s*(\d+)', content)
        score_b = re.search(r'版本B评分[：:]\s*(\d+)', content)
        
        if score_a and score_b:
            return "A" if int(score_a.group(1)) >= int(score_b.group(1)) else "B"
        
        return "A"
