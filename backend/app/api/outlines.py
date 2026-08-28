import json

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..core.deps import get_current_user
from ..database import get_db
from ..models import Book, Outline, User
from ..schemas import OutlineOut, OutlineUpdateIn

router = APIRouter(prefix="/books", tags=["outlines"])


async def _get_owned_book(bid: int, u: User, db: AsyncSession) -> Book:
    b = await db.get(Book, bid)
    if not b or b.user_id != u.id:
        raise HTTPException(404, "书籍不存在")
    return b


async def _call_langgraph(meta: dict) -> tuple[dict, str | None]:
    """调用大纲工作流（进程内直接调 graph）.

    docker 镜像加速器 403 导致 langgraph-api 镜像暂不可用，
    临时改为进程内调用；镜像就绪后可切回 httpx 调 LANGGRAPH_URL。
    """
    try:
        from storyclaw.graph import outline_graph
    except ImportError as e:
        raise HTTPException(500, f"未加载大纲图: {e}")
    try:
        result = await outline_graph.ainvoke({"book_meta": meta})
    except Exception as e:
        raise HTTPException(500, f"大纲生成失败: {e}")
    outline = result.get("outline") or {}
    err = result.get("error")
    if not outline:
        raise HTTPException(500, f"未返回大纲: {result}")
    return outline, err


@router.post("/{bid}/outline/generate", response_model=OutlineOut)
async def generate_outline(bid: int, u: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    b = await _get_owned_book(bid, u, db)
    meta = {
        "title": b.title, "intro": b.intro or "", "genre": b.genre,
        "protagonist_name": b.protagonist_name or "", "protagonist_intro": b.protagonist_intro or "",
        "target_chapters": b.target_chapters, "target_words": b.target_words,
        "per_chapter_words": b.per_chapter_words,
    }
    outline, err = await _call_langgraph(meta)
    existing = await db.scalar(select(Outline).where(Outline.book_id == bid))
    if existing:
        existing.content = json.dumps(outline, ensure_ascii=False)
    else:
        existing = Outline(book_id=bid, content=json.dumps(outline, ensure_ascii=False))
        db.add(existing)
    await db.commit()
    await db.refresh(existing)
    return OutlineOut(id=existing.id, book_id=existing.book_id, content=outline, error=err,
                      created_at=existing.created_at, updated_at=existing.updated_at)


@router.get("/{bid}/outline", response_model=OutlineOut)
async def get_outline(bid: int, u: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await _get_owned_book(bid, u, db)
    o = await db.scalar(select(Outline).where(Outline.book_id == bid))
    if not o:
        raise HTTPException(404, "大纲不存在，请先生成")
    try:
        content = json.loads(o.content) if o.content else {}
    except Exception:
        content = {"raw": o.content}
    return OutlineOut(id=o.id, book_id=o.book_id, content=content,
                      created_at=o.created_at, updated_at=o.updated_at)


@router.put("/{bid}/outline", response_model=OutlineOut)
async def update_outline(bid: int, data: OutlineUpdateIn, u: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await _get_owned_book(bid, u, db)
    o = await db.scalar(select(Outline).where(Outline.book_id == bid))
    content_str = json.dumps(data.content, ensure_ascii=False)
    if o:
        o.content = content_str
    else:
        o = Outline(book_id=bid, content=content_str)
        db.add(o)
    await db.commit()
    await db.refresh(o)
    return OutlineOut(id=o.id, book_id=o.book_id, content=data.content,
                      created_at=o.created_at, updated_at=o.updated_at)
