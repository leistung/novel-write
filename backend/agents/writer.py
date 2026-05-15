"""写手Agent - 使用 prompts 模板系统"""
import re
from typing import Dict, Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from agents.base import BaseAgent, AgentResult
from db.crud import get_book, get_chapter_by_number


class WriterAgent(BaseAgent):
    """写手Agent - 负责章节内容创作
    
    Public Methods (3个):
    1. write_chapter - 撰写章节内容
    2. rewrite_chapter - 重写章节
    3. expand_outline - 扩写大纲为章节规划
    """
    
    def __init__(self):
        super().__init__("Writer")
    
    async def execute(self, task: str, **kwargs) -> AgentResult:
        """执行写手任务"""
        if task == "write_chapter":
            return await self.write_chapter(**kwargs)
        elif task == "rewrite_chapter":
            return await self.rewrite_chapter(**kwargs)
        elif task == "expand_outline":
            return await self.expand_outline(**kwargs)
        else:
            return self.failure(task, f"未知任务: {task}")
    
    # ==================== PUBLIC METHODS ====================
    
    async def write_chapter(
        self,
        book_id: int,
        chapter_num: int,
        chapter_plan: str,
        db: AsyncSession = None,
        **kwargs
    ) -> AgentResult:
        """【Public】撰写章节内容"""
        if db is None:
            return self.failure("write_chapter", "需要数据库会话")
        
        book = await get_book(db, book_id)
        if not book:
            return self.failure("write_chapter", f"书籍不存在: {book_id}")
        
        # 获取前一章结尾作为衔接
        prev_ending = await self._get_previous_ending(db, book_id, chapter_num)
        
        try:
            # 使用 prompts 渲染提示词
            system_prompt, user_prompt = self._render_prompt("writer/chapter", {
                "chapter_number": chapter_num,
                "chapter_title": f"第{chapter_num}章",
                "outline": chapter_plan,
                "characters": [],  # 可以从 book 数据中提取
                "word_count": book.chapter_words,
                "previous_chapter": prev_ending if prev_ending != "这是第一章，无需衔接" else "",
                "style_guide": kwargs.get("style_reference", "")
            })
            
            # 添加题材专家知识
            system_prompt = self._build_system_prompt(system_prompt, book.genre)
            
            # 添加书籍特定信息到 user_prompt
            user_prompt = f"""{user_prompt}

## 小说信息
- 书名：{book.title}
- 题材：{book.genre}
- 平台：{book.platform}
- 目标字数：{book.chapter_words}字（误差不超过10%）
- 最少字数：{int(book.chapter_words * 0.9)}字

## 章节规划
{chapter_plan}

请直接输出章节正文，包含标题。标题格式：第{chapter_num}章 章节标题
"""
            
            response = await self.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.8,
                max_tokens=6000
            )
            
            content = response.content
            title = self._extract_title(content, chapter_num)
            word_count = len(content)
            
            # 检查字数
            min_words = int(book.chapter_words * 0.9)
            if word_count < min_words:
                return self.failure(
                    "write_chapter",
                    f"字数不足: {word_count} < {min_words}",
                    data={"content": content, "word_count": word_count}
                )
            
            return self.success(
                task="write_chapter",
                data={
                    "title": title,
                    "content": content,
                    "word_count": word_count,
                    "chapter_num": chapter_num
                },
                feedback=f"成功撰写第{chapter_num}章，字数: {word_count}",
                token_usage={
                    "prompt_tokens": response.prompt_tokens,
                    "completion_tokens": response.completion_tokens,
                    "total_tokens": response.total_tokens
                }
            )
        except Exception as e:
            return self.failure("write_chapter", str(e))
    
    async def rewrite_chapter(
        self,
        book_id: int,
        chapter_num: int,
        rewrite_requirements: str,
        keep_plot: bool = True,
        db: AsyncSession = None,
        **kwargs
    ) -> AgentResult:
        """【Public】重写章节"""
        if db is None:
            return self.failure("rewrite_chapter", "需要数据库会话")
        
        book = await get_book(db, book_id)
        if not book:
            return self.failure("rewrite_chapter", f"书籍不存在: {book_id}")
        
        # 获取原章节
        original_chapter = await get_chapter_by_number(db, book_id, chapter_num)
        original_content = original_chapter.content if original_chapter else ""
        
        # 获取前后章节衔接
        prev_ending = await self._get_previous_ending(db, book_id, chapter_num)
        next_beginning = await self._get_next_beginning(db, book_id, chapter_num)
        
        try:
            # 使用 prompts 渲染提示词
            system_prompt, user_prompt = self._render_prompt("writer/rewrite", {
                "chapter_number": chapter_num,
                "original_content": original_content,
                "rewrite_requirements": rewrite_requirements,
                "keep_plot": keep_plot,
                "genre": book.genre,
                "prev_ending": prev_ending if prev_ending != "这是第一章，无需衔接" else "",
                "next_beginning": next_beginning
            })
            
            # 添加题材专家知识
            system_prompt = self._build_system_prompt(system_prompt, book.genre)
            
            response = await self.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.8,
                max_tokens=6000
            )
            
            content = response.content
            title = self._extract_title(content, chapter_num)
            word_count = len(content)
            
            return self.success(
                task="rewrite_chapter",
                data={
                    "title": title,
                    "content": content,
                    "word_count": word_count,
                    "chapter_num": chapter_num,
                    "original_content": original_content if not keep_plot else None
                },
                feedback=f"成功重写第{chapter_num}章，字数: {word_count}",
                token_usage={
                    "prompt_tokens": response.prompt_tokens,
                    "completion_tokens": response.completion_tokens,
                    "total_tokens": response.total_tokens
                }
            )
        except Exception as e:
            return self.failure("rewrite_chapter", str(e))
    
    async def expand_outline(
        self,
        book_id: int,
        outline_files: Dict[str, str],
        db: AsyncSession = None,
        **kwargs
    ) -> AgentResult:
        """【Public】扩写大纲为章节规划"""
        if db is None:
            return self.failure("expand_outline", "需要数据库会话")
        
        book = await get_book(db, book_id)
        if not book:
            return self.failure("expand_outline", f"书籍不存在: {book_id}")
        
        try:
            # 使用 prompts 渲染提示词
            system_prompt, user_prompt = self._render_prompt("writer/expand_outline", {
                "title": book.title,
                "genre": book.genre,
                "target_chapters": book.target_chapters,
                "chapter_words": book.chapter_words,
                "outline_files": outline_files
            })
            
            # 添加题材专家知识
            system_prompt = self._build_system_prompt(system_prompt, book.genre)
            
            response = await self.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.7,
                max_tokens=8000
            )
            
            # 解析章节规划
            chapter_plans = self._parse_chapter_plans(response.content)
            
            return self.success(
                task="expand_outline",
                data={
                    "chapter_plans": chapter_plans,
                    "total_chapters": len(chapter_plans),
                    "raw_content": response.content
                },
                feedback=f"成功生成{len(chapter_plans)}章的详细规划",
                token_usage={
                    "prompt_tokens": response.prompt_tokens,
                    "completion_tokens": response.completion_tokens,
                    "total_tokens": response.total_tokens
                }
            )
        except Exception as e:
            return self.failure("expand_outline", str(e))
    
    # ==================== PRIVATE METHODS ====================
    
    async def _get_previous_ending(
        self,
        db: AsyncSession,
        book_id: int,
        chapter_num: int
    ) -> str:
        """【Private】获取前一章结尾"""
        if chapter_num <= 1:
            return "这是第一章，无需衔接"
        
        prev_chapter = await get_chapter_by_number(db, book_id, chapter_num - 1)
        if prev_chapter and prev_chapter.content:
            # 取最后300字
            return prev_chapter.content[-300:]
        return "暂无前一章"
    
    async def _get_next_beginning(
        self,
        db: AsyncSession,
        book_id: int,
        chapter_num: int
    ) -> str:
        """【Private】获取后一章开头"""
        next_chapter = await get_chapter_by_number(db, book_id, chapter_num + 1)
        if next_chapter and next_chapter.content:
            # 取前300字
            return next_chapter.content[:300]
        return ""
    
    def _extract_title(self, content: str, chapter_num: int) -> str:
        """【Private】从内容中提取章节标题"""
        lines = content.split("\n")
        for line in lines[:5]:
            line = line.strip()
            if f"第{chapter_num}章" in line:
                # 提取标题部分
                return line.replace(f"第{chapter_num}章", "").strip()
        return f"第{chapter_num}章"
    
    def _parse_chapter_plans(self, content: str) -> Dict[int, Dict[str, str]]:
        """【Private】解析章节规划"""
        plans = {}
        current_chapter = None
        current_content = []
        
        for line in content.split("\n"):
            # 匹配章节标题行
            match = re.match(r'^第(\d+)章\s*(.+)?$', line.strip())
            if match:
                if current_chapter:
                    plans[current_chapter] = {
                        "title": "",
                        "content": "\n".join(current_content)
                    }
                current_chapter = int(match.group(1))
                current_content = [line]
            elif current_chapter:
                current_content.append(line)
        
        # 保存最后一个章节
        if current_chapter:
            plans[current_chapter] = {
                "title": "",
                "content": "\n".join(current_content)
            }
        
        return plans
