"""P1-9 社区 API：帖子 CRUD + 搜索 + [[book:id]] 解析."""
from __future__ import annotations
import re
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, or_, delete
from sqlalchemy.ext.asyncio import AsyncSession
from ..core.deps import get_current_user
from ..database import get_db
from ..models import Book, Post, PostBookLink, User
from ..schemas import (
    PostCreateIn, PostUpdateIn, PostOut, PostListOut,
    BookLinkOut, SearchResultOut,
)

router = APIRouter(prefix="/community", tags=["community"])

BOOK_LINK_RE = re.compile(r"\[\[book:(\d+)\]\]")


async def _post_to_out(db: AsyncSession, p: Post, include_links: bool = True) -> PostOut:
    """将 Post ORM 转为 PostOut，解析 [[book:id]] 链接."""
    u = await db.get(User, p.user_id)
    author_name = u.username if u else ""
    book_links: list[BookLinkOut] = []
    if include_links:
        links = await db.scalars(select(PostBookLink).where(PostBookLink.post_id == p.id))
        for link in links:
            b = await db.get(Book, link.book_id)
            if b:
                book_links.append(BookLinkOut(
                    book_id=b.id, book_title=b.title, book_cover_url=b.cover_url))
    return PostOut(
        id=p.id, user_id=p.user_id, author_name=author_name,
        title=p.title, content_html=p.content_html, content_text=p.content_text,
        book_links=book_links, created_at=p.created_at, updated_at=p.updated_at,
    )


def _extract_book_ids(content: str) -> list[int]:
    """从内容中提取 [[book:id]] 的 book_id 列表."""
    return [int(m) for m in BOOK_LINK_RE.findall(content)]


def _render_book_links(content_html: str) -> str:
    """将 [[book:id]] 替换为 <a href='/read/{id}'>链接</a>."""
    def replacer(m):
        bid = m.group(1)
        return f'<a href="/read/{bid}" class="book-link">📖 查看作品 #{bid}</a>'
    return BOOK_LINK_RE.sub(replacer, content_html)


@router.get("/posts", response_model=PostListOut)
async def list_posts(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """列出帖子（公开，分页，不含 content_html 详情，但含 book_links）."""
    offset = (page - 1) * size
    total = await db.scalar(select(func.count(Post.id)))
    rs = await db.scalars(select(Post).order_by(
        Post.created_at.desc()
    ).offset(offset).limit(size))
    items = [await _post_to_out(db, p, include_links=True) for p in rs]
    return PostListOut(items=items, total=total or 0, page=page, page_size=size)


@router.get("/posts/{pid}", response_model=PostOut)
async def get_post(pid: int, db: AsyncSession = Depends(get_db)):
    """获取帖子详情（公开，渲染 [[book:id]] 为链接）."""
    p = await db.get(Post, pid)
    if not p:
        raise HTTPException(404, "帖子不存在")
    out = await _post_to_out(db, p, include_links=True)
    out.content_html = _render_book_links(out.content_html)
    return out


@router.post("/posts", response_model=PostOut)
async def create_post(
    data: PostCreateIn,
    u: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建帖子（需登录），自动解析 [[book:id]] 关联."""
    p = Post(user_id=u.id, title=data.title, content_html=data.content_html, content_text=data.content_text)
    db.add(p)
    await db.flush()
    # 提取并存储 book links
    book_ids = _extract_book_ids(data.content_html + " " + data.content_text)
    for bid in set(book_ids):
        b = await db.get(Book, bid)
        if b:
            db.add(PostBookLink(post_id=p.id, book_id=bid))
    await db.commit()
    await db.refresh(p)
    return await _post_to_out(db, p, include_links=True)


@router.put("/posts/{pid}", response_model=PostOut)
async def update_post(
    pid: int, data: PostUpdateIn,
    u: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新帖子（仅作者）."""
    p = await db.get(Post, pid)
    if not p or p.user_id != u.id:
        raise HTTPException(404, "帖子不存在或无权限")
    if data.title is not None:
        p.title = data.title
    if data.content_html is not None:
        p.content_html = data.content_html
    if data.content_text is not None:
        p.content_text = data.content_text
    # 重新解析 book links
    await db.execute(delete(PostBookLink).where(PostBookLink.post_id == pid))
    content = (data.content_html or "") + " " + (data.content_text or "")
    book_ids = _extract_book_ids(content)
    for bid in set(book_ids):
        b = await db.get(Book, bid)
        if b:
            db.add(PostBookLink(post_id=pid, book_id=bid))
    await db.commit()
    await db.refresh(p)
    return await _post_to_out(db, p, include_links=True)


@router.delete("/posts/{pid}")
async def delete_post(
    pid: int,
    u: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除帖子（仅作者）."""
    p = await db.get(Post, pid)
    if not p or p.user_id != u.id:
        raise HTTPException(404, "帖子不存在或无权限")
    await db.delete(p)
    await db.commit()
    return {"ok": True, "id": pid}


@router.get("/search", response_model=SearchResultOut)
async def search(
    q: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_db),
):
    """搜索帖子内容/书名/简介."""
    kw = f"%{q}%"
    # 搜索帖子
    post_rs = await db.scalars(select(Post).where(
        or_(Post.title.ilike(kw), Post.content_text.ilike(kw))
    ).order_by(Post.created_at.desc()).limit(20))
    posts = [await _post_to_out(db, p, include_links=True) for p in post_rs]
    # 搜索书籍
    book_rs = await db.scalars(select(Book).where(
        or_(Book.title.ilike(kw), Book.intro.ilike(kw), Book.genre.ilike(kw))
    ).limit(20))
    books = [{"id": b.id, "title": b.title, "intro": b.intro or "",
              "genre": b.genre, "cover_url": b.cover_url} for b in book_rs]
    return SearchResultOut(posts=posts, books=books, total=len(posts) + len(books))


@router.get("/books/{bid}/read", response_model=dict)
async def get_book_for_read(bid: int, db: AsyncSession = Depends(get_db)):
    """只读阅读页：获取书籍基本信息（公开，不含编辑权限）."""
    b = await db.get(Book, bid)
    if not b:
        raise HTTPException(404, "书籍不存在")
    return {
        "id": b.id, "title": b.title, "intro": b.intro or "",
        "genre": b.genre, "cover_url": b.cover_url,
        "protagonist_name": b.protagonist_name or "",
        "protagonist_intro": b.protagonist_intro or "",
    }


@router.get("/books/{bid}/read/chapters", response_model=list)
async def list_chapters_for_read(bid: int, db: AsyncSession = Depends(get_db)):
    """只读阅读页：列出章节（公开，返回 id/number/title）."""
    from ..models import Chapter
    rs = await db.scalars(select(Chapter).where(
        Chapter.book_id == bid
    ).order_by(Chapter.number))
    return [{"id": c.id, "number": c.number, "title": c.title,
             "word_count": c.word_count} for c in rs]


@router.get("/books/{bid}/read/chapters/{cid}", response_model=dict)
async def get_chapter_for_read(bid: int, cid: int, db: AsyncSession = Depends(get_db)):
    """只读阅读页：获取章节内容（公开）."""
    from ..models import Chapter
    c = await db.get(Chapter, cid)
    if not c or c.book_id != bid:
        raise HTTPException(404, "章节不存在")
    return {"id": c.id, "number": c.number, "title": c.title,
            "content": c.content, "word_count": c.word_count}
