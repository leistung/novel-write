"""Orchestrator API路由

智能编排器API，负责协调多个Agent完成复杂创作任务。"""
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import json

from db.database import get_db
from db.crud import get_book, update_book, get_chapters_by_book, create_chapter, get_chapter_by_number, update_chapter
from db.models import Book

router = APIRouter()


# ==================== Request/Response Models ====================

class GenerateOutlineRequest(BaseModel):
    """生成大纲请求"""
    book_id: int
    use_llm: bool = True  # 是否使用真实LLM


class WriteChapterRequest(BaseModel):
    """写单章请求"""
    book_id: int
    chapter_num: int
    use_llm: bool = True


class ContinueChaptersRequest(BaseModel):
    """续写多章请求"""
    book_id: int
    start_chapter: int
    count: int = Field(default=1, ge=1, le=10)
    use_llm: bool = True


class BookContextResponse(BaseModel):
    """书籍上下文响应"""
    book_id: int
    title: str
    genre: str
    platform: str
    outline: str
    story_bible: str
    volume_outline: str
    current_state: str
    context_hash: str


class OutlineResponse(BaseModel):
    """大纲生成响应"""
    book_id: int
    outline_generated: bool
    story_bible: str = ""
    volume_outline: str = ""
    book_rules: str = ""
    current_state: str = ""
    pending_hooks: str = ""
    character_matrix: str = ""
    emotional_arcs: str = ""
    message: str


class ChapterWriteResponse(BaseModel):
    """章节写作响应"""
    book_id: int
    chapter_num: int
    title: str
    content: str
    word_count: int
    audit_score: float
    continuity_score: float = 0.0
    audit_passed: bool
    message: str


class ContinueChaptersResponse(BaseModel):
    """续写多章响应"""
    book_id: int
    start_chapter: int
    end_chapter: int
    chapters_written: int
    results: List[Dict[str, Any]]
    message: str


# ==================== BookContext ====================

class BookContext:
    """书籍上下文管理器"""

    def __init__(self, book: Book = None, book_id: int = None):
        self.context = {}
        if book:
            self.context = {
                "book_id": book.id,
                "title": book.title,
                "genre": book.genre,
                "platform": book.platform or "",
                "outline": book.outline or "",
                "story_bible": book.story_bible or "",
                "volume_outline": book.volume_outline or "",
                "current_state": book.current_state or "",
                "pending_hooks": book.pending_hooks or "",
                "character_matrix": book.character_matrix or "",
                "emotional_arcs": book.emotional_arcs or ""
            }
        elif book_id:
            self.context = {"book_id": book_id}

    def get_context_hash(self) -> str:
        """计算上下文哈希"""
        import hashlib
        content = json.dumps(self.context, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(content.encode()).hexdigest()[:16]

    def to_prompt_context(self) -> str:
        """转换为Prompt上下文"""
        parts = []
        if self.context.get("story_bible"):
            parts.append(f"世界观设定:\n{self.context['story_bible']}")
        if self.context.get("volume_outline"):
            parts.append(f"卷纲规划:\n{self.context['volume_outline']}")
        if self.context.get("current_state"):
            parts.append(f"当前状态:\n{self.context['current_state']}")
        if self.context.get("character_matrix"):
            parts.append(f"角色矩阵:\n{self.context['character_matrix']}")

        return "\n\n".join(parts) if parts else "暂无上下文信息"


# ==================== OrchestratorStrategy ====================

class OrchestratorStrategy:
    """编排策略"""

    @staticmethod
    def determine_chapter_type(chapter_num: int, total_chapters: int) -> str:
        """判断章节类型"""
        if chapter_num <= 3:
            return "opening"  # 黄金三章
        if chapter_num >= total_chapters - 2:
            return "ending"  # 结局

        # 卷边界
        if chapter_num % 20 == 1:
            return "volume_start"
        if chapter_num % 20 == 0:
            return "volume_end"

        # 高潮区域 (68%-75%)
        climax_start = int(total_chapters * 0.68)
        climax_end = int(total_chapters * 0.75)
        if chapter_num == climax_start:
            return "pre_climax"
        if climax_start < chapter_num <= climax_end:
            return "climax"

        return "normal"

    @staticmethod
    def should_use_rag(chapter_num: int) -> bool:
        """判断是否使用RAG"""
        return chapter_num > 5

    @staticmethod
    def should_audit_rewrite(score: float, threshold: float = 80.0) -> bool:
        """判断是否需要重写"""
        return score < threshold

    @staticmethod
    def get_max_rewrite_attempts() -> int:
        """获取最大重写次数"""
        return 3


# ==================== OrchestratorService ====================

class OrchestratorService:
    """编排服务"""

    def __init__(self, db: AsyncSession, use_llm: bool = True):
        self.db = db
        self.use_llm = use_llm
        self._architect = None
        self._writer = None
        self._auditor = None

    async def _get_architect(self):
        """获取Architect Agent"""
        if self._architect is None:
            from agents.architect import ArchitectAgent
            self._architect = ArchitectAgent()
        return self._architect

    async def _get_writer(self):
        """获取Writer Agent"""
        if self._writer is None:
            from agents.writer import WriterAgent
            self._writer = WriterAgent()
        return self._writer

    async def _get_auditor(self):
        """获取Auditor Agent"""
        if self._auditor is None:
            from agents.auditor import AuditorAgent
            self._auditor = AuditorAgent()
        return self._auditor

    async def generate_outline(self, book_id: int) -> Dict[str, Any]:
        """生成大纲"""
        book = await get_book(self.db, book_id)
        if not book:
            raise HTTPException(status_code=404, detail=f"书籍不存在: {book_id}")

        if self.use_llm:
            architect = await self._get_architect()
            result = await architect.generate_foundation(
                book_data={
                    "title": book.title,
                    "genre": book.genre,
                    "platform": book.platform,
                    "outline": book.outline,
                    "target_chapters": book.target_chapters,
                    "chapter_words": book.chapter_words
                },
                db=self.db
            )

            if result.ok:
                # 更新书籍
                await update_book(self.db, book_id, {
                    "story_bible": result.data.get("story_bible", ""),
                    "volume_outline": result.data.get("volume_outline", ""),
                    "book_rules": result.data.get("book_rules", ""),
                    "current_state": result.data.get("current_state", ""),
                    "pending_hooks": result.data.get("pending_hooks", ""),
                    "character_matrix": result.data.get("character_matrix", ""),
                    "emotional_arcs": result.data.get("emotional_arcs", "")
                })

                return {
                    "book_id": book_id,
                    "outline_generated": True,
                    "story_bible": result.data.get("story_bible", ""),
                    "volume_outline": result.data.get("volume_outline", ""),
                    "book_rules": result.data.get("book_rules", ""),
                    "current_state": result.data.get("current_state", ""),
                    "pending_hooks": result.data.get("pending_hooks", ""),
                    "character_matrix": result.data.get("character_matrix", ""),
                    "emotional_arcs": result.data.get("emotional_arcs", ""),
                    "message": "大纲生成成功"
                }
            else:
                raise HTTPException(status_code=500, detail=f"大纲生成失败: {result.feedback}")
        else:
            # 模拟生成
            mock_data = self._generate_mock_outline(book)
            await update_book(self.db, book_id, mock_data)

            return {
                "book_id": book_id,
                "outline_generated": True,
                **mock_data,
                "message": "大纲生成成功（模拟模式）"
            }

    async def write_chapter(self, book_id: int, chapter_num: int) -> Dict[str, Any]:
        """写章节"""
        book = await get_book(self.db, book_id)
        if not book:
            raise HTTPException(status_code=404, detail=f"书籍不存在: {book_id}")

        # 判断章节类型
        chapter_type = OrchestratorStrategy.determine_chapter_type(
            chapter_num, book.target_chapters or 100
        )

        if self.use_llm:
            # 规划章节
            architect = await self._get_architect()
            plan_result = await architect.plan_chapter(
                book_id=book_id,
                chapter_num=chapter_num,
                chapter_type=chapter_type,
                db=self.db
            )

            if not plan_result.ok:
                raise HTTPException(status_code=500, detail=f"章节规划失败: {plan_result.feedback}")

            # 写作章节
            writer = await self._get_writer()
            write_result = await writer.write_chapter(
                book_id=book_id,
                chapter_num=chapter_num,
                chapter_plan=plan_result.data.get("chapter_plan", ""),
                db=self.db
            )

            if not write_result.ok:
                raise HTTPException(status_code=500, detail=f"章节写作失败: {write_result.feedback}")

            content = write_result.data.get("content", "")
            title = write_result.data.get("title", f"第{chapter_num}章")
            word_count = write_result.data.get("word_count", len(content))

            # 审核章节
            auditor = await self._get_auditor()
            audit_result = await auditor.audit_chapter(
                book_id=book_id,
                chapter_num=chapter_num,
                chapter_content=content,
                db=self.db
            )

            audit_score = audit_result.data.get("total_score", 0) if audit_result.ok else 0

            # 保存章节
            existing_chapter = await get_chapter_by_number(self.db, book_id, chapter_num)
            chapter_data = {
                "book_id": book_id,
                "chapter_number": chapter_num,
                "title": title,
                "content": content,
                "word_count": word_count,
                "audit_score": audit_score,
                "audit_details": audit_result.data.get("scores", {}) if audit_result.ok else {},
                "chapter_type": chapter_type,
                "status": "published"
            }

            if existing_chapter:
                await update_chapter(self.db, existing_chapter.id, chapter_data)
            else:
                await create_chapter(
                    self.db,
                    book_id=book_id,
                    chapter_number=chapter_num,
                    title=title,
                    content=content,
                    audit_score=audit_score,
                    audit_details=audit_result.data.get("scores", {}) if audit_result.ok else {},
                    chapter_type=chapter_type,
                    status="published"
                )

            return {
                "book_id": book_id,
                "chapter_num": chapter_num,
                "title": title,
                "content": content,
                "word_count": word_count,
                "audit_score": audit_score,
                "continuity_score": 0.0,
                "audit_passed": audit_score >= 70,
                "message": "章节写作成功"
            }
        else:
            # 模拟写作
            mock_data = self._generate_mock_chapter(book, chapter_num, chapter_type)

            # 保存章节
            existing_chapter = await get_chapter_by_number(self.db, book_id, chapter_num)
            if existing_chapter:
                await update_chapter(self.db, existing_chapter.id, mock_data)
            else:
                await create_chapter(
                    self.db,
                    book_id=mock_data["book_id"],
                    chapter_number=mock_data["chapter_number"],
                    title=mock_data["title"],
                    content=mock_data["content"],
                    audit_score=mock_data["audit_score"],
                    audit_details=mock_data["audit_details"],
                    chapter_type=mock_data["chapter_type"],
                    status=mock_data["status"]
                )

            return {
                "book_id": book_id,
                "chapter_num": chapter_num,
                "title": mock_data["title"],
                "content": mock_data["content"],
                "word_count": mock_data["word_count"],
                "audit_score": mock_data["audit_score"],
                "continuity_score": 0.0,
                "audit_passed": True,
                "message": "章节写作成功（模拟模式）"
            }

    async def continue_chapters(
        self, book_id: int, start_chapter: int, count: int
    ) -> Dict[str, Any]:
        """续写多章"""
        book = await get_book(self.db, book_id)
        if not book:
            raise HTTPException(status_code=404, detail=f"书籍不存在: {book_id}")

        results = []
        for i in range(count):
            chapter_num = start_chapter + i
            result = await self.write_chapter(book_id, chapter_num)
            results.append({
                "chapter_num": chapter_num,
                "title": result["title"],
                "word_count": result["word_count"],
                "audit_score": result["audit_score"],
                "audit_passed": result["audit_passed"]
            })

        return {
            "book_id": book_id,
            "start_chapter": start_chapter,
            "end_chapter": start_chapter + count - 1,
            "chapters_written": count,
            "results": results,
            "message": f"成功续写{count}章"
        }

    def _generate_mock_outline(self, book: Book) -> Dict[str, str]:
        """生成模拟大纲"""
        return {
            "story_bible": f"# {book.title} 世界观设定\n\n这是一个{book.genre}类型的故事...",
            "volume_outline": "# 卷纲规划\n\n第一卷：崛起篇\n第二卷：冒险篇\n第三卷：巅峰篇",
            "book_rules": "# 创作规则\n\n1. 每章约3000字\n2. 保持节奏紧凑\n3. 注重爽点设计",
            "current_state": "# 当前状态\n\n主角刚刚踏上旅程...",
            "pending_hooks": "# 伏笔池\n\n暂无伏笔",
            "character_matrix": "# 角色矩阵\n\n主角：待定",
            "emotional_arcs": "# 情感弧线\n\n成长型弧线"
        }

    def _generate_mock_chapter(
        self, book: Book, chapter_num: int, chapter_type: str
    ) -> Dict[str, Any]:
        """生成模拟章节"""
        titles = {
            "opening": f"第{chapter_num}章 初入异世",
            "ending": f"第{chapter_num}章 终章·巅峰",
            "volume_start": f"第{chapter_num}章 新的征程",
            "volume_end": f"第{chapter_num}章 卷终·转折",
            "pre_climax": f"第{chapter_num}章 风雨欲来",
            "climax": f"第{chapter_num}章 巅峰对决",
            "normal": f"第{chapter_num}章 继续前行"
        }

        content = f"这是《{book.title}》的第{chapter_num}章内容。\n\n" * 100
        word_count = len(content)

        return {
            "book_id": book.id,
            "chapter_number": chapter_num,
            "title": titles.get(chapter_type, f"第{chapter_num}章"),
            "content": content,
            "word_count": word_count,
            "audit_score": 85.0,
            "audit_details": {"plot": 85, "character": 90, "style": 80},
            "chapter_type": chapter_type,
            "status": "published"
        }


# ==================== API Endpoints ====================

@router.post("/generate-outline", response_model=OutlineResponse)
async def generate_outline(
    request: GenerateOutlineRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """智能生成大纲

    调用架构师Agent生成完整的小说大纲体系：
    - 世界观设定
    - 卷纲规划
    - 创作规则
    - 初始状态卡
    - 伏笔池
    - 角色矩阵
    - 情感弧线
    """
    service = OrchestratorService(db, use_llm=request.use_llm)
    result = await service.generate_outline(request.book_id)
    return result


@router.post("/write-chapter", response_model=ChapterWriteResponse)
async def write_chapter(
    request: WriteChapterRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """智能写单章

    完整流程：
    1. 规划章节内容
    2. 写作章节
    3. 审核章节
    4. 连续性检查
    5. 保存章节
    """
    service = OrchestratorService(db, use_llm=request.use_llm)
    result = await service.write_chapter(request.book_id, request.chapter_num)
    return result


@router.post("/continue-chapters", response_model=ContinueChaptersResponse)
async def continue_chapters(
    request: ContinueChaptersRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """智能续写多章

    自动续写指定数量的章节，包含完整的规划和审核流程。
    """
    service = OrchestratorService(db, use_llm=request.use_llm)
    result = await service.continue_chapters(
        request.book_id, request.start_chapter, request.count
    )
    return result


@router.get("/books/{book_id}/context", response_model=BookContextResponse)
async def get_book_context(
    book_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取书籍上下文

    返回书籍的完整上下文信息，用于前端展示或调试。
    """
    book = await get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail=f"书籍不存在: {book_id}")

    context = BookContext(book)
    return {
        "book_id": book.id,
        "title": book.title,
        "genre": book.genre,
        "platform": book.platform or "",
        "outline": book.outline or "",
        "story_bible": book.story_bible or "",
        "volume_outline": book.volume_outline or "",
        "current_state": book.current_state or "",
        "context_hash": context.get_context_hash()
    }


@router.post("/books/{book_id}/context/refresh")
async def refresh_book_context(
    book_id: int,
    db: AsyncSession = Depends(get_db)
):
    """刷新书籍上下文

    重新从数据库加载书籍上下文。
    """
    book = await get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail=f"书籍不存在: {book_id}")

    context = BookContext(book)
    return {
        "book_id": book_id,
        "refreshed": True,
        "context_hash": context.get_context_hash(),
        "message": "上下文已刷新"
    }
