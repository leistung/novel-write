"""书籍API路由"""
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from db.crud import create_book, get_book, get_books, update_book, delete_book
from store.manager import store_manager

logger = logging.getLogger(__name__)

router = APIRouter()


class BookCreate(BaseModel):
    """创建书籍请求"""
    title: str
    genre: str
    platform: str = "通用"
    chapter_words: int = 3000
    target_chapters: int = 100
    outline: str = ""


class BookUpdate(BaseModel):
    """更新书籍请求"""
    title: Optional[str] = None
    genre: Optional[str] = None
    platform: Optional[str] = None
    chapter_words: Optional[int] = None
    target_chapters: Optional[int] = None
    outline: Optional[str] = None


class BookResponse(BaseModel):
    """书籍响应"""
    id: int
    title: str
    genre: str
    platform: str
    chapter_words: int
    target_chapters: int
    outline: str
    created_at: str
    # 工作流生成的状态字段
    story_bible: str = ""
    volume_outline: str = ""
    current_state: str = ""
    pending_hooks: str = ""
    character_matrix: str = ""
    emotional_arcs: str = ""
    
    class Config:
        from_attributes = True


@router.post("/books", response_model=BookResponse)
async def create_new_book(
    request: Request,
    book_request: BookCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建新书籍"""
    request_id = getattr(request.state, 'request_id', 'unknown')
    logger.info(f"[{request_id}] 创建书籍请求: title={book_request.title}, genre={book_request.genre}")
    
    try:
        book = await create_book(
            db=db,
            title=book_request.title,
            genre=book_request.genre,
            platform=book_request.platform,
            chapter_words=book_request.chapter_words,
            target_chapters=book_request.target_chapters,
            outline=book_request.outline
        )
        
        # 初始化存储目录
        try:
            store_manager._ensure_book_dir(book.id)
            logger.info(f"[{request_id}] 书籍存储目录创建成功: book_id={book.id}")
        except Exception as e:
            logger.warning(f"[{request_id}] 书籍存储目录创建失败（不影响创建）: {str(e)}")
        
        logger.info(f"[{request_id}] 书籍创建成功: book_id={book.id}")
        
        return {
            "id": book.id,
            "title": book.title,
            "genre": book.genre,
            "platform": book.platform,
            "chapter_words": book.chapter_words,
            "target_chapters": book.target_chapters,
            "outline": book.outline,
            "created_at": book.created_at.isoformat() if book.created_at else ""
        }
    except Exception as e:
        logger.error(f"[{request_id}] 创建书籍失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"创建书籍失败: {str(e)}")


@router.get("/books", response_model=List[BookResponse])
async def list_books(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """获取书籍列表"""
    request_id = getattr(request.state, 'request_id', 'unknown')
    logger.info(f"[{request_id}] 获取书籍列表: skip={skip}, limit={limit}")
    
    try:
        # get_books 返回 (items, total) 元组
        result = await get_books(db, skip=skip, limit=limit)
        
        # 处理元组返回值
        if isinstance(result, tuple):
            items, total = result
        else:
            items = result
            total = len(items) if items else 0
        
        logger.info(f"[{request_id}] 获取书籍列表成功: total={total}")
        
        return [
            {
                "id": book.id,
                "title": book.title,
                "genre": book.genre,
                "platform": book.platform,
                "chapter_words": book.chapter_words,
                "target_chapters": book.target_chapters,
                "outline": book.outline,
                "created_at": book.created_at.isoformat() if book.created_at else ""
            }
            for book in items
        ]
    except Exception as e:
        logger.error(f"[{request_id}] 获取书籍列表失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取书籍列表失败: {str(e)}")


@router.get("/books/{book_id}", response_model=BookResponse)
async def get_book_detail(
    request: Request,
    book_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取书籍详情"""
    request_id = getattr(request.state, 'request_id', 'unknown')
    logger.info(f"[{request_id}] 获取书籍详情: book_id={book_id}")
    
    book = await get_book(db, book_id)
    if not book:
        logger.warning(f"[{request_id}] 书籍不存在: book_id={book_id}")
        raise HTTPException(status_code=404, detail="书籍不存在")
    
    # 获取存储结构
    structure = store_manager.get_book_structure(book_id)
    
    return {
        "id": book.id,
        "title": book.title,
        "genre": book.genre,
        "platform": book.platform,
        "chapter_words": book.chapter_words,
        "target_chapters": book.target_chapters,
        "outline": book.outline,
        "created_at": book.created_at.isoformat() if book.created_at else "",
        # 工作流生成的状态字段
        "story_bible": book.story_bible or "",
        "volume_outline": book.volume_outline or "",
        "current_state": book.current_state or "",
        "pending_hooks": book.pending_hooks or "",
        "character_matrix": book.character_matrix or "",
        "emotional_arcs": book.emotional_arcs or "",
        "store_structure": structure
    }


@router.put("/books/{book_id}", response_model=BookResponse)
async def update_book_info(
    request: Request,
    book_id: int,
    book_update: BookUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新书籍信息"""
    request_id = getattr(request.state, 'request_id', 'unknown')
    logger.info(f"[{request_id}] 更新书籍: book_id={book_id}")
    
    update_data = book_update.model_dump(exclude_unset=True)
    logger.debug(f"[{request_id}] 更新数据: {update_data}")
    
    book = await update_book(db, book_id, update_data)
    if not book:
        logger.warning(f"[{request_id}] 更新失败，书籍不存在: book_id={book_id}")
        raise HTTPException(status_code=404, detail="书籍不存在")
    
    logger.info(f"[{request_id}] 书籍更新成功: book_id={book_id}")
    
    return {
        "id": book.id,
        "title": book.title,
        "genre": book.genre,
        "platform": book.platform,
        "chapter_words": book.chapter_words,
        "target_chapters": book.target_chapters,
        "outline": book.outline,
        "created_at": book.created_at.isoformat() if book.created_at else ""
    }


@router.delete("/books/{book_id}")
async def delete_book_endpoint(
    request: Request,
    book_id: int,
    db: AsyncSession = Depends(get_db)
):
    """删除书籍"""
    request_id = getattr(request.state, 'request_id', 'unknown')
    logger.info(f"[{request_id}] 删除书籍: book_id={book_id}")
    
    try:
        success = await delete_book(db, book_id)
        if not success:
            logger.warning(f"[{request_id}] 删除失败，书籍不存在: book_id={book_id}")
            raise HTTPException(status_code=404, detail="书籍不存在")
        
        # 清理文件系统存储
        try:
            book_path = store_manager._get_book_path(book_id)
            if book_path.exists():
                import shutil
                shutil.rmtree(book_path, ignore_errors=True)
                logger.info(f"[{request_id}] 书籍文件清理成功: book_id={book_id}")
        except Exception as e:
            logger.warning(f"[{request_id}] 书籍文件清理失败: {str(e)}")
        
        logger.info(f"[{request_id}] 书籍删除成功: book_id={book_id}")
        return {"message": "书籍已删除"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{request_id}] 删除书籍失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"删除书籍失败: {str(e)}")


@router.get("/books/{book_id}/structure")
async def get_book_structure(
    request: Request,
    book_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取书籍存储结构"""
    request_id = getattr(request.state, 'request_id', 'unknown')
    logger.info(f"[{request_id}] 获取书籍结构: book_id={book_id}")
    
    book = await get_book(db, book_id)
    if not book:
        logger.warning(f"[{request_id}] 书籍不存在: book_id={book_id}")
        raise HTTPException(status_code=404, detail="书籍不存在")
    
    structure = store_manager.get_book_structure(book_id)
    return structure
