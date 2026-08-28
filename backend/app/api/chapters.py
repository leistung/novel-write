import re

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.deps import get_current_user
from ..database import get_db
from ..models import Book, Chapter, User, Volume
from ..schemas import ChapterCreateIn, ChapterDetailOut, ChapterOut, ChapterUpdateIn

router = APIRouter(prefix="/chapters", tags=["chapters"])


def _count_words(text: str) -> int:
    if not text:
        return 0
    text = re.sub(r"<[^>]+>", "", text)  # 去 HTML 标签
    return len(re.sub(r"\s+", "", text))


async def _check_book(bid: int, u: User, db: AsyncSession) -> Book:
    b = await db.get(Book, bid)
    if not b or b.user_id != u.id:
        raise HTTPException(404, "书籍不存在")
    return b


async def _own_chapter(cid: int, u: User, db: AsyncSession) -> Chapter:
    c = await db.get(Chapter, cid)
    if not c:
        raise HTTPException(404, "章节不存在")
    b = await db.get(Book, c.book_id)
    if not b or b.user_id != u.id:
        raise HTTPException(404, "章节不存在")
    return c


@router.get("/books/{bid}", response_model=list[ChapterOut])
async def list_chapters(bid: int, u: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await _check_book(bid, u, db)
    rs = await db.scalars(select(Chapter).where(Chapter.book_id == bid).order_by(Chapter.number))
    return [ChapterOut.model_validate(c) for c in rs]


@router.post("/books/{bid}", response_model=ChapterDetailOut)
async def create_chapter(bid: int, data: ChapterCreateIn, u: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await _check_book(bid, u, db)
    max_num = await db.scalar(select(func.max(Chapter.number)).where(Chapter.book_id == bid)) or 0
    if data.volume_id:
        v = await db.get(Volume, data.volume_id)
        if not v or v.book_id != bid:
            raise HTTPException(400, "卷不存在")
    c = Chapter(book_id=bid, volume_id=data.volume_id, number=max_num + 1,
                title=data.title, content="", word_count=0)
    db.add(c)
    await db.commit()
    await db.refresh(c)
    return ChapterDetailOut.model_validate(c)


@router.get("/{cid}", response_model=ChapterDetailOut)
async def get_chapter(cid: int, u: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    c = await _own_chapter(cid, u, db)
    return ChapterDetailOut.model_validate(c)


@router.put("/{cid}", response_model=ChapterDetailOut)
async def update_chapter(cid: int, data: ChapterUpdateIn, u: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    c = await _own_chapter(cid, u, db)
    if data.title is not None:
        c.title = data.title
    if data.volume_id is not None:
        c.volume_id = data.volume_id
    if data.content is not None:
        c.content = data.content
        c.word_count = _count_words(data.content)
    await db.commit()
    await db.refresh(c)
    return ChapterDetailOut.model_validate(c)


@router.delete("/{cid}")
async def delete_chapter(cid: int, u: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    c = await _own_chapter(cid, u, db)
    await db.delete(c)
    await db.commit()
    return {"ok": True}
