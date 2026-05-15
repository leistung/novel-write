"""章节API路由"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from db.crud import (
    get_chapter, get_chapters_by_book, update_chapter, 
    delete_chapter, get_chapter_by_number
)
from store.manager import store_manager

router = APIRouter()


class ChapterUpdate(BaseModel):
    """更新章节请求"""
    title: Optional[str] = None
    content: Optional[str] = None
    status: Optional[str] = None


class ChapterResponse(BaseModel):
    """章节响应"""
    id: int
    book_id: int
    chapter_number: int
    title: str
    word_count: int
    audit_score: float
    continuity_score: float
    chapter_type: str
    status: str
    
    class Config:
        from_attributes = True


@router.get("/books/{book_id}/chapters", response_model=List[ChapterResponse])
async def list_chapters(
    book_id: int,
    skip: int = 0,
    limit: int = 1000,
    db: AsyncSession = Depends(get_db)
):
    """获取书籍的所有章节"""
    chapters = await get_chapters_by_book(db, book_id, skip=skip, limit=limit)
    return [
        {
            "id": ch.id,
            "book_id": ch.book_id,
            "chapter_number": ch.chapter_number,
            "title": ch.title,
            "word_count": ch.word_count,
            "audit_score": ch.audit_score,
            "continuity_score": ch.continuity_score,
            "chapter_type": ch.chapter_type,
            "status": ch.status
        }
        for ch in chapters
    ]


@router.get("/books/{book_id}/chapters/{chapter_num}")
async def get_chapter_detail(
    book_id: int,
    chapter_num: int,
    db: AsyncSession = Depends(get_db)
):
    """获取章节详情"""
    chapter = await get_chapter_by_number(db, book_id, chapter_num)
    if not chapter:
        raise HTTPException(status_code=404, detail="章节不存在")
    
    return {
        "id": chapter.id,
        "book_id": chapter.book_id,
        "chapter_number": chapter.chapter_number,
        "title": chapter.title,
        "content": chapter.content,
        "word_count": chapter.word_count,
        "audit_score": chapter.audit_score,
        "audit_details": chapter.audit_details,
        "continuity_score": chapter.continuity_score,
        "continuity_details": chapter.continuity_details,
        "chapter_type": chapter.chapter_type,
        "status": chapter.status
    }


@router.put("/books/{book_id}/chapters/{chapter_num}")
async def update_chapter_endpoint(
    book_id: int,
    chapter_num: int,
    request: ChapterUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新章节"""
    chapter = await get_chapter_by_number(db, book_id, chapter_num)
    if not chapter:
        raise HTTPException(status_code=404, detail="章节不存在")
    
    update_data = request.model_dump(exclude_unset=True)
    updated = await update_chapter(db, chapter.id, update_data)
    
    # 同步更新store文件
    if updated:
        await store_manager.save_chapter_file(
            book_id=book_id,
            chapter_num=chapter_num,
            title=updated.title,
            content=updated.content
        )
    
    return {
        "id": updated.id,
        "book_id": updated.book_id,
        "chapter_number": updated.chapter_number,
        "title": updated.title,
        "word_count": updated.word_count,
        "status": updated.status
    }


@router.delete("/books/{book_id}/chapters/{chapter_num}")
async def delete_chapter_endpoint(
    book_id: int,
    chapter_num: int,
    db: AsyncSession = Depends(get_db)
):
    """删除章节"""
    chapter = await get_chapter_by_number(db, book_id, chapter_num)
    if not chapter:
        raise HTTPException(status_code=404, detail="章节不存在")
    
    success = await delete_chapter(db, chapter.id)
    if not success:
        raise HTTPException(status_code=500, detail="删除失败")
    
    return {"message": "章节已删除"}


@router.get("/books/{book_id}/chapters/{chapter_num}/content")
async def get_chapter_content(
    book_id: int,
    chapter_num: int,
    db: AsyncSession = Depends(get_db)
):
    """获取章节内容（从store）"""
    chapter_data = await store_manager.load_chapter_file(book_id, chapter_num)
    if not chapter_data:
        raise HTTPException(status_code=404, detail="章节文件不存在")
    
    return chapter_data
