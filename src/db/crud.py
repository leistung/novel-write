from sqlalchemy.orm import Session
from .models import Book, Chapter

# Book CRUD operations
def create_book(db: Session, book_data: dict) -> Book:
    db_book = Book(**book_data)
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book

def get_book(db: Session, book_id: int) -> Book:
    return db.query(Book).filter(Book.id == book_id).first()

def get_books(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Book).offset(skip).limit(limit).all()

def update_book(db: Session, book_id: int, book_data: dict) -> Book:
    db_book = get_book(db, book_id)
    if db_book:
        for key, value in book_data.items():
            setattr(db_book, key, value)
        db.commit()
        db.refresh(db_book)
    return db_book

def delete_book(db: Session, book_id: int) -> bool:
    db_book = get_book(db, book_id)
    if db_book:
        db.delete(db_book)
        db.commit()
        return True
    return False

# Chapter CRUD operations
def create_chapter(db: Session, chapter_data: dict) -> Chapter:
    db_chapter = Chapter(**chapter_data)
    db.add(db_chapter)
    db.commit()
    db.refresh(db_chapter)
    return db_chapter

def get_chapter(db: Session, chapter_id: int) -> Chapter:
    return db.query(Chapter).filter(Chapter.id == chapter_id).first()

def get_chapters_by_book(db: Session, book_id: int):
    return db.query(Chapter).filter(Chapter.book_id == book_id).order_by(Chapter.chapter_number).all()

def get_chapter_by_number(db: Session, book_id: int, chapter_number: int) -> Chapter:
    return db.query(Chapter).filter(Chapter.book_id == book_id, Chapter.chapter_number == chapter_number).first()

def update_chapter(db: Session, chapter_id: int, chapter_data: dict) -> Chapter:
    db_chapter = get_chapter(db, chapter_id)
    if db_chapter:
        for key, value in chapter_data.items():
            setattr(db_chapter, key, value)
        db.commit()
        db.refresh(db_chapter)
    return db_chapter

def delete_chapter(db: Session, chapter_id: int) -> bool:
    db_chapter = get_chapter(db, chapter_id)
    if db_chapter:
        db.delete(db_chapter)
        db.commit()
        return True
    return False

def delete_chapters_after(db: Session, book_id: int, chapter_number: int) -> int:
    deleted = db.query(Chapter).filter(
        Chapter.book_id == book_id,
        Chapter.chapter_number >= chapter_number
    ).delete()
    db.commit()
    return deleted
