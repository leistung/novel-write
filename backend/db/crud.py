"""数据库CRUD操作"""
import re
from typing import Optional, List, Dict, Any, Tuple

from sqlalchemy import select, desc, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Book, Chapter, WorkflowExecution, WorkflowNode, SkillTemplate


# ========== 工具函数 ==========

def count_chinese_chars(text: str) -> int:
    """准确计算中文字数（仅统计中文字符）"""
    return len(re.findall(r'[\u4e00-\u9fff]', text))


# ========== 字段白名单 ==========

UPDATABLE_BOOK_FIELDS = {
    # 基础信息
    "title", "genre", "platform", "chapter_words", "target_chapters", "outline", "status",
    # 工作流生成的状态字段
    "story_bible", "volume_outline", "book_rules", "current_state",
    "pending_hooks", "character_matrix", "emotional_arcs",
    "subplot_board", "chapter_summaries", "writing_style",
}


# ========== Book CRUD ==========

async def create_book(
    db: AsyncSession,
    title: str,
    genre: str,
    platform: str = "通用",
    chapter_words: int = 3000,
    target_chapters: int = 100,
    outline: str = "",
    **kwargs
) -> Book:
    """创建书籍"""
    book = Book(
        title=title,
        genre=genre,
        platform=platform,
        chapter_words=chapter_words,
        target_chapters=target_chapters,
        outline=outline,
        **kwargs
    )
    db.add(book)
    await db.flush()
    await db.refresh(book)
    return book


async def get_book(db: AsyncSession, book_id: int) -> Optional[Book]:
    """获取书籍"""
    result = await db.execute(select(Book).where(Book.id == book_id))
    return result.scalar_one_or_none()


async def get_books(db: AsyncSession, skip: int = 0, limit: int = 100) -> Tuple[List[Book], int]:
    """获取书籍列表，返回 (items, total) 元组"""
    # 查询总数
    count_result = await db.execute(select(func.count(Book.id)))
    total = count_result.scalar()

    # 查询分页数据
    result = await db.execute(
        select(Book).order_by(desc(Book.created_at)).offset(skip).limit(limit)
    )
    items = result.scalars().all()
    return items, total


async def update_book(
    db: AsyncSession,
    book_id: int,
    update_data: Dict[str, Any]
) -> Optional[Book]:
    """更新书籍（仅允许更新白名单字段）"""
    book = await get_book(db, book_id)
    if not book:
        return None

    for key, value in update_data.items():
        if key in UPDATABLE_BOOK_FIELDS and hasattr(book, key):
            setattr(book, key, value)

    await db.flush()
    await db.refresh(book)
    return book


async def delete_book(db: AsyncSession, book_id: int) -> bool:
    """删除书籍"""
    book = await get_book(db, book_id)
    if not book:
        return False

    await db.delete(book)
    # 不手动commit，由 get_db 统一管理事务
    return True


# ========== Chapter CRUD ==========

async def create_chapter(
    db: AsyncSession,
    book_id: int,
    chapter_number: int,
    title: str = "",
    content: str = "",
    chapter_type: str = "normal",
    **kwargs
) -> Chapter:
    """创建章节"""
    chapter = Chapter(
        book_id=book_id,
        chapter_number=chapter_number,
        title=title,
        content=content,
        word_count=len(content),
        chapter_type=chapter_type,
        **kwargs
    )
    db.add(chapter)
    await db.flush()
    await db.refresh(chapter)
    return chapter


async def get_chapter(db: AsyncSession, chapter_id: int) -> Optional[Chapter]:
    """获取章节"""
    result = await db.execute(select(Chapter).where(Chapter.id == chapter_id))
    return result.scalar_one_or_none()


async def get_chapter_by_number(
    db: AsyncSession,
    book_id: int,
    chapter_number: int
) -> Optional[Chapter]:
    """根据章节号获取章节"""
    result = await db.execute(
        select(Chapter).where(
            and_(Chapter.book_id == book_id, Chapter.chapter_number == chapter_number)
        )
    )
    return result.scalar_one_or_none()


async def get_chapters_by_book(
    db: AsyncSession,
    book_id: int,
    skip: int = 0,
    limit: int = 1000
) -> Tuple[List[Chapter], int]:
    """获取书籍的所有章节，返回 (items, total) 元组"""
    # 查询总数
    count_result = await db.execute(
        select(func.count(Chapter.id)).where(Chapter.book_id == book_id)
    )
    total = count_result.scalar()

    # 查询分页数据
    result = await db.execute(
        select(Chapter)
        .where(Chapter.book_id == book_id)
        .order_by(Chapter.chapter_number)
        .offset(skip)
        .limit(limit)
    )
    items = result.scalars().all()
    return items, total


async def update_chapter(
    db: AsyncSession,
    chapter_id: int,
    update_data: Dict[str, Any]
) -> Optional[Chapter]:
    """更新章节"""
    chapter = await get_chapter(db, chapter_id)
    if not chapter:
        return None

    for key, value in update_data.items():
        if hasattr(chapter, key):
            setattr(chapter, key, value)
            if key == "content":
                chapter.word_count = len(value)

    await db.flush()
    await db.refresh(chapter)
    return chapter


async def delete_chapter(db: AsyncSession, chapter_id: int) -> bool:
    """删除章节"""
    chapter = await get_chapter(db, chapter_id)
    if not chapter:
        return False

    await db.delete(chapter)
    await db.flush()
    return True


# ========== Workflow CRUD ==========

async def create_workflow_execution(
    db: AsyncSession,
    workflow_id: str,
    book_id: int,
    workflow_type: str,
    input_data: Dict[str, Any] = None
) -> WorkflowExecution:
    """创建工作流执行记录"""
    workflow = WorkflowExecution(
        workflow_id=workflow_id,
        book_id=book_id,
        workflow_type=workflow_type,
        input_data=input_data or {}
    )
    db.add(workflow)
    await db.flush()
    await db.refresh(workflow)
    return workflow


async def get_workflow_execution(
    db: AsyncSession,
    workflow_id: str
) -> Optional[WorkflowExecution]:
    """获取工作流执行记录"""
    result = await db.execute(
        select(WorkflowExecution).where(WorkflowExecution.workflow_id == workflow_id)
    )
    return result.scalar_one_or_none()


async def update_workflow_status(
    db: AsyncSession,
    workflow_id: str,
    status: str,
    **kwargs
) -> Optional[WorkflowExecution]:
    """更新工作流状态"""
    workflow = await get_workflow_execution(db, workflow_id)
    if not workflow:
        return None

    workflow.status = status
    for key, value in kwargs.items():
        if hasattr(workflow, key):
            setattr(workflow, key, value)

    await db.flush()
    await db.refresh(workflow)
    return workflow


async def create_workflow_node(
    db: AsyncSession,
    workflow_execution_id: int,
    node_id: str,
    node_type: str,
    node_name: str = "",
    input_data: Dict[str, Any] = None
) -> WorkflowNode:
    """创建工作流节点记录"""
    node = WorkflowNode(
        workflow_id=workflow_execution_id,
        node_id=node_id,
        node_type=node_type,
        node_name=node_name,
        input_data=input_data or {}
    )
    db.add(node)
    await db.flush()
    await db.refresh(node)
    return node


async def update_workflow_node(
    db: AsyncSession,
    node_id: int,
    status: str,
    output_data: Dict[str, Any] = None,
    **kwargs
) -> Optional[WorkflowNode]:
    """更新工作流节点"""
    result = await db.execute(select(WorkflowNode).where(WorkflowNode.id == node_id))
    node = result.scalar_one_or_none()
    if not node:
        return None

    node.status = status
    if output_data:
        node.output_data = output_data

    for key, value in kwargs.items():
        if hasattr(node, key):
            setattr(node, key, value)

    await db.flush()
    await db.refresh(node)
    return node


# ========== Skill CRUD ==========

async def create_skill_template(
    db: AsyncSession,
    name: str,
    genre: str,
    category: str,
    description: str = "",
    skill_content: str = "",
    references: Dict[str, Any] = None
) -> SkillTemplate:
    """创建Skill模板"""
    skill = SkillTemplate(
        name=name,
        genre=genre,
        category=category,
        description=description,
        skill_content=skill_content,
        references=references or {}
    )
    db.add(skill)
    await db.flush()
    await db.refresh(skill)
    return skill


async def get_skill_template(
    db: AsyncSession,
    skill_name: str
) -> Optional[SkillTemplate]:
    """获取Skill模板"""
    result = await db.execute(
        select(SkillTemplate).where(SkillTemplate.name == skill_name)
    )
    return result.scalar_one_or_none()


async def get_skill_templates(
    db: AsyncSession,
    category: str = None,
    skip: int = 0,
    limit: int = 100
) -> List[SkillTemplate]:
    """获取Skill模板列表"""
    query = select(SkillTemplate)
    if category:
        query = query.where(SkillTemplate.category == category)

    result = await db.execute(query.offset(skip).limit(limit))
    return result.scalars().all()
