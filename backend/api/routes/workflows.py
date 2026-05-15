"""工作流API路由 - 支持同步执行模式（不需要Redis）"""
from typing import Optional
import asyncio

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from db.crud import get_book
from checkpoint.manager import checkpoint_manager
from store.manager import store_manager
from workflow.engine import WorkflowEngine

router = APIRouter()

# 全局工作流引擎
workflow_engine = WorkflowEngine()

# 工作流状态存储（内存缓存，用于同步模式）
_workflow_status: dict = {}


# ==================== 请求模型 ====================

class GenerateOutlineRequest(BaseModel):
    """生成大纲请求"""
    book_id: int


class ContinueChaptersRequest(BaseModel):
    """续写章节请求"""
    book_id: int
    start_chapter: int
    count: int = 1
    external_context: str = ""


class RewriteChapterRequest(BaseModel):
    """重写章节请求"""
    book_id: int
    chapter_num: int
    rewrite_requirements: str
    keep_plot: bool = True


class ProtectAndUpdateRequest(BaseModel):
    """保护章节并更新大纲请求"""
    book_id: int
    protected_chapter: int
    new_outline: str


class ExtractOutlineRequest(BaseModel):
    """提取大纲请求"""
    book_id: int


class ExpandSkillRequest(BaseModel):
    """扩写Skill请求"""
    book_id: int


# ==================== 同步执行辅助函数 ====================

async def run_generate_outline_sync(
    workflow_id: str,
    book_id: int
):
    """同步执行生成大纲工作流"""
    import asyncio
    from db.database import async_session_factory
    
    # 创建新的事件循环
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # 等待一小段时间，让主请求完成提交
    await asyncio.sleep(1)
    
    async with async_session_factory() as db:
        try:
            await workflow_engine.run_generate_outline(
                workflow_id=workflow_id,
                book_id=book_id,
                db=db
            )
            await db.commit()
            _workflow_status[workflow_id] = {
                "status": "completed",
                "progress": 100,
                "current_node": "completed"
            }
        except Exception as e:
            await db.rollback()
            _workflow_status[workflow_id] = {
                "status": "failed",
                "error": str(e),
                "progress": 0,
                "current_node": "error"
            }


async def run_continue_chapters_sync(
    workflow_id: str,
    book_id: int,
    start_chapter: int,
    count: int,
    external_context: str
):
    """同步执行续写章节工作流"""
    import asyncio
    from db.database import async_session_factory
    
    # 创建新的事件循环
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # 等待一小段时间，让主请求完成提交
    await asyncio.sleep(1)
    
    async with async_session_factory() as db:
        try:
            await workflow_engine.run_continue_chapters(
                workflow_id=workflow_id,
                book_id=book_id,
                start_chapter=start_chapter,
                count=count,
                external_context=external_context,
                db=db
            )
            await db.commit()
            _workflow_status[workflow_id] = {
                "status": "completed",
                "progress": 100,
                "current_node": "completed"
            }
        except Exception as e:
            await db.rollback()
            _workflow_status[workflow_id] = {
                "status": "failed",
                "error": str(e),
                "progress": 0,
                "current_node": "error"
            }


async def run_rewrite_chapter_sync(
    workflow_id: str,
    book_id: int,
    chapter_num: int,
    rewrite_requirements: str,
    keep_plot: bool
):
    """同步执行重写章节工作流"""
    import asyncio
    from db.database import async_session_factory
    
    # 创建新的事件循环
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # 等待一小段时间，让主请求完成提交
    await asyncio.sleep(1)
    
    async with async_session_factory() as db:
        try:
            await workflow_engine.run_rewrite_chapter(
                workflow_id=workflow_id,
                book_id=book_id,
                chapter_num=chapter_num,
                rewrite_requirements=rewrite_requirements,
                keep_plot=keep_plot,
                db=db
            )
            await db.commit()
            _workflow_status[workflow_id] = {
                "status": "completed",
                "progress": 100,
                "current_node": "completed"
            }
        except Exception as e:
            await db.rollback()
            _workflow_status[workflow_id] = {
                "status": "failed",
                "error": str(e),
                "progress": 0,
                "current_node": "error"
            }


# ==================== API 端点 ====================

@router.post("/workflows/generate-outline")
async def workflow_generate_outline(
    request: GenerateOutlineRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """工作流①: 生成大纲"""
    book = await get_book(db, request.book_id)
    if not book:
        raise HTTPException(status_code=404, detail="书籍不存在")
    
    # 检查锁
    lock = store_manager.check_lock(request.book_id, "generate_outline")
    if lock:
        raise HTTPException(status_code=409, detail="该书籍正在生成大纲中")
    
    # 创建工作流记录
    workflow_id = await checkpoint_manager.create_workflow(
        db=db,
        book_id=request.book_id,
        workflow_type="generate_outline",
        input_data={"book_id": request.book_id}
    )
    
    # 创建锁
    await store_manager.create_lock(
        book_id=request.book_id,
        lock_type="generate_outline",
        metadata={"workflow_id": workflow_id}
    )
    
    # 初始化状态
    _workflow_status[workflow_id] = {
        "status": "running",
        "progress": 0,
        "current_node": "starting"
    }
    
    # 使用后台任务执行（同步模式）
    background_tasks.add_task(
        asyncio.run,
        run_generate_outline_sync(workflow_id, request.book_id)
    )
    
    return {
        "workflow_id": workflow_id,
        "task_id": workflow_id,  # 同步模式下 task_id = workflow_id
        "status": "queued",
        "message": "大纲生成工作流已启动"
    }


@router.post("/workflows/continue-chapters")
async def workflow_continue_chapters(
    request: ContinueChaptersRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """工作流②: 续写章节"""
    book = await get_book(db, request.book_id)
    if not book:
        raise HTTPException(status_code=404, detail="书籍不存在")
    
    # 检查锁
    lock = store_manager.check_lock(request.book_id, "continue_chapters")
    if lock:
        raise HTTPException(status_code=409, detail="该书籍正在续写章节中")
    
    # 创建工作流记录
    workflow_id = await checkpoint_manager.create_workflow(
        db=db,
        book_id=request.book_id,
        workflow_type="continue_chapters",
        input_data={
            "book_id": request.book_id,
            "start_chapter": request.start_chapter,
            "count": request.count,
            "external_context": request.external_context
        }
    )
    
    # 创建锁
    await store_manager.create_lock(
        book_id=request.book_id,
        lock_type="continue_chapters",
        metadata={"workflow_id": workflow_id}
    )
    
    # 初始化状态
    _workflow_status[workflow_id] = {
        "status": "running",
        "progress": 0,
        "current_node": "starting"
    }
    
    # 使用后台任务执行
    background_tasks.add_task(
        asyncio.run,
        run_continue_chapters_sync(
            workflow_id, request.book_id,
            request.start_chapter, request.count, request.external_context
        )
    )
    
    return {
        "workflow_id": workflow_id,
        "task_id": workflow_id,
        "status": "queued",
        "message": f"续写{request.count}章工作流已启动"
    }


@router.post("/workflows/rewrite-chapter")
async def workflow_rewrite_chapter(
    request: RewriteChapterRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """工作流③: 重写章节"""
    book = await get_book(db, request.book_id)
    if not book:
        raise HTTPException(status_code=404, detail="书籍不存在")
    
    # 检查锁
    lock = store_manager.check_lock(request.book_id, "rewrite_chapter")
    if lock:
        raise HTTPException(status_code=409, detail="该书籍正在重写章节中")
    
    # 创建工作流记录
    workflow_id = await checkpoint_manager.create_workflow(
        db=db,
        book_id=request.book_id,
        workflow_type="rewrite_chapter",
        input_data={
            "book_id": request.book_id,
            "chapter_num": request.chapter_num,
            "rewrite_requirements": request.rewrite_requirements,
            "keep_plot": request.keep_plot
        }
    )
    
    # 创建锁
    await store_manager.create_lock(
        book_id=request.book_id,
        lock_type="rewrite_chapter",
        metadata={"workflow_id": workflow_id}
    )
    
    # 初始化状态
    _workflow_status[workflow_id] = {
        "status": "running",
        "progress": 0,
        "current_node": "starting"
    }
    
    # 使用后台任务执行
    background_tasks.add_task(
        asyncio.run,
        run_rewrite_chapter_sync(
            workflow_id, request.book_id,
            request.chapter_num, request.rewrite_requirements, request.keep_plot
        )
    )
    
    return {
        "workflow_id": workflow_id,
        "task_id": workflow_id,
        "status": "queued",
        "message": f"重写第{request.chapter_num}章工作流已启动"
    }


@router.get("/workflows/{workflow_id}/status")
async def get_workflow_status(workflow_id: str):
    """获取工作流状态"""
    # 先检查内存缓存
    if workflow_id in _workflow_status:
        return _workflow_status[workflow_id]
    
    # 再检查数据库
    from db.database import async_session_factory
    
    async with async_session_factory() as db:
        status = await checkpoint_manager.get_workflow_status(db, workflow_id)
        if status:
            return {
                "status": status.get("status", "unknown"),
                "progress": status.get("progress", 0),
                "current_node": status.get("current_node", ""),
                "output_data": status.get("output_data")
            }
    
    return {"status": "not_found", "progress": 0, "current_node": ""}


@router.post("/workflows/{workflow_id}/pause")
async def pause_workflow(workflow_id: str):
    """暂停工作流"""
    if workflow_id in _workflow_status:
        _workflow_status[workflow_id]["status"] = "paused"
    return {"workflow_id": workflow_id, "status": "paused"}


@router.post("/workflows/{workflow_id}/resume")
async def resume_workflow(workflow_id: str):
    """恢复工作流"""
    if workflow_id in _workflow_status:
        _workflow_status[workflow_id]["status"] = "running"
    return {"workflow_id": workflow_id, "status": "running"}


@router.post("/workflows/protect-and-update")
async def workflow_protect_and_update(
    request: ProtectAndUpdateRequest,
    db: AsyncSession = Depends(get_db)
):
    """工作流④: 保护章节并更新大纲"""
    book = await get_book(db, request.book_id)
    if not book:
        raise HTTPException(status_code=404, detail="书籍不存在")
    
    return {
        "workflow_id": "not_implemented",
        "status": "error",
        "message": "此工作流尚未实现"
    }


@router.post("/workflows/extract-outline")
async def workflow_extract_outline(
    request: ExtractOutlineRequest,
    db: AsyncSession = Depends(get_db)
):
    """工作流⑤: 从已有内容提取大纲"""
    book = await get_book(db, request.book_id)
    if not book:
        raise HTTPException(status_code=404, detail="书籍不存在")
    
    return {
        "workflow_id": "not_implemented",
        "status": "error",
        "message": "此工作流尚未实现"
    }


@router.post("/workflows/expand-skill")
async def workflow_expand_skill(
    request: ExpandSkillRequest,
    db: AsyncSession = Depends(get_db)
):
    """工作流⑥: 扩写Skill"""
    book = await get_book(db, request.book_id)
    if not book:
        raise HTTPException(status_code=404, detail="书籍不存在")
    
    return {
        "workflow_id": "not_implemented",
        "status": "error",
        "message": "此工作流尚未实现"
    }
