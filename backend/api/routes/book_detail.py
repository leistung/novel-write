"""书籍详情API路由 - 大纲文件、状态文件、统计等"""
from typing import Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from db.crud import get_book, get_chapters_by_book, update_book
from store.manager import store_manager

router = APIRouter()


# 大纲文件名映射
OUTLINE_FILES = [
    {"key": "worldview", "name": "01-worldview.md", "label": "世界观设定"},
    {"key": "characters", "name": "02-characters.md", "label": "角色设定"},
    {"key": "plot", "name": "03-plot.md", "label": "主线剧情"},
    {"key": "arcs", "name": "04-arcs.md", "label": "情感弧线"},
    {"key": "hooks", "name": "05-hooks.md", "label": "伏笔设计"},
    {"key": "settings", "name": "06-settings.md", "label": "场景设定"},
    {"key": "power_system", "name": "07-power-system.md", "label": "力量体系"},
    {"key": "outline", "name": "08-outline.md", "label": "卷纲大纲"},
    {"key": "rules", "name": "09-rules.md", "label": "创作规则"},
]


class OutlineUpdateRequest(BaseModel):
    """更新大纲文件请求"""
    key: str
    content: str


class BookStateUpdateRequest(BaseModel):
    """更新书籍状态请求"""
    outline: Optional[str] = None
    writing_style: Optional[str] = None


@router.get("/books/{book_id}/outline")
async def get_book_outline(
    book_id: int,
    key: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """获取书籍大纲文件
    
    - 不传key: 返回所有大纲文件列表及内容摘要
    - 传key: 返回指定大纲文件完整内容
    """
    book = await get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="书籍不存在")
    
    if key:
        # 返回单个文件
        filename = None
        for f in OUTLINE_FILES:
            if f["key"] == key:
                filename = f["name"]
                break
        if not filename:
            raise HTTPException(status_code=400, detail=f"无效的大纲文件key: {key}")
        
        content = await store_manager.load_outline_file(book_id, filename)
        return {
            "book_id": book_id,
            "key": key,
            "filename": filename,
            "content": content or ""
        }
    else:
        # 返回所有文件列表
        structure = store_manager.get_book_structure(book_id)
        files = []
        for f in OUTLINE_FILES:
            files.append({
                "key": f["key"],
                "name": f["name"],
                "label": f["label"],
                "exists": f["name"] in structure.get("outline_files", [])
            })
        
        return {
            "book_id": book_id,
            "files": files,
            "outline_files": structure.get("outline_files", [])
        }


@router.put("/books/{book_id}/outline")
async def update_book_outline(
    book_id: int,
    request: OutlineUpdateRequest,
    db: AsyncSession = Depends(get_db)
):
    """更新大纲文件"""
    book = await get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="书籍不存在")
    
    filename = None
    for f in OUTLINE_FILES:
        if f["key"] == request.key:
            filename = f["name"]
            break
    if not filename:
        raise HTTPException(status_code=400, detail=f"无效的大纲文件key: {request.key}")
    
    await store_manager.save_outline_file(book_id, filename, request.content)
    
    return {"message": f"大纲文件 {request.key} 已更新"}


@router.get("/books/{book_id}/state")
async def get_book_state(
    book_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取书籍当前状态"""
    book = await get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="书籍不存在")
    
    return {
        "book_id": book_id,
        "current_state": book.current_state or "",
        "pending_hooks": book.pending_hooks or "",
        "character_matrix": book.character_matrix or "",
        "emotional_arcs": book.emotional_arcs or "",
        "subplot_board": book.subplot_board or "",
        "chapter_summaries": book.chapter_summaries or ""
    }


@router.get("/books/{book_id}/statistics")
async def get_book_statistics(
    book_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取书籍统计数据"""
    book = await get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="书籍不存在")
    
    chapters = await get_chapters_by_book(db, book_id)
    
    total_words = sum(ch.word_count for ch in chapters)
    total_chapters = len(chapters)
    avg_score = 0
    avg_continuity = 0
    scored_chapters = [ch for ch in chapters if ch.audit_score > 0]
    
    if scored_chapters:
        avg_score = sum(ch.audit_score for ch in scored_chapters) / len(scored_chapters)
        continuity_chapters = [ch for ch in scored_chapters if ch.continuity_score > 0]
        if continuity_chapters:
            avg_continuity = sum(ch.continuity_score for ch in continuity_chapters) / len(continuity_chapters)
    
    # 章节类型分布
    type_distribution = {}
    for ch in chapters:
        t = ch.chapter_type or "normal"
        type_distribution[t] = type_distribution.get(t, 0) + 1
    
    # 评分趋势（最近10章）
    recent_scores = [
        {"chapter": ch.chapter_number, "audit": ch.audit_score, "continuity": ch.continuity_score}
        for ch in chapters[-10:]
    ]
    
    # 锁状态
    structure = store_manager.get_book_structure(book_id)
    
    return {
        "book_id": book_id,
        "title": book.title,
        "genre": book.genre,
        "total_chapters": total_chapters,
        "target_chapters": book.target_chapters,
        "total_words": total_words,
        "avg_audit_score": round(avg_score, 1),
        "avg_continuity_score": round(avg_continuity, 1),
        "type_distribution": type_distribution,
        "recent_scores": recent_scores,
        "progress_percent": round(total_chapters / max(book.target_chapters, 1) * 100, 1),
        "active_locks": structure.get("locks", [])
    }


@router.put("/books/{book_id}/state")
async def update_book_state(
    book_id: int,
    request: BookStateUpdateRequest,
    db: AsyncSession = Depends(get_db)
):
    """更新书籍状态（大纲、写作风格等）"""
    book = await get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="书籍不存在")
    
    update_data = {}
    if request.outline is not None:
        update_data["outline"] = request.outline
    if request.writing_style is not None:
        update_data["writing_style"] = request.writing_style
    
    if update_data:
        await update_book(db, book_id, update_data)
    
    return {"message": "书籍状态已更新"}


@router.get("/books/{book_id}/locks")
async def get_book_locks(
    book_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取书籍当前的锁状态"""
    book = await get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="书籍不存在")
    
    structure = store_manager.get_book_structure(book_id)
    locks = []
    for lock_name in structure.get("locks", []):
        lock_info = store_manager.check_lock(book_id, lock_name)
        locks.append({
            "name": lock_name,
            "info": lock_info
        })
    
    return {"book_id": book_id, "locks": locks}
