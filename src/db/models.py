from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from .config import Base

class Book(Base):
    __tablename__ = "books"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    genre = Column(String(100), nullable=False)
    platform = Column(String(100), nullable=False)
    chapter_words = Column(Integer, nullable=False, default=3000)
    target_chapters = Column(Integer, nullable=False, default=20)
    outline = Column(Text, nullable=False)
    story_bible = Column(Text, nullable=False)
    volume_outline = Column(Text, nullable=False)
    book_rules = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 状态文件（随章节更新）
    current_state = Column(Text, nullable=True)
    pending_hooks = Column(Text, nullable=True)
    chapter_summaries = Column(Text, nullable=True)
    subplot_board = Column(Text, nullable=True)
    emotional_arcs = Column(Text, nullable=True)
    character_matrix = Column(Text, nullable=True)
    
    # 关系
    chapters = relationship("Chapter", back_populates="book", cascade="all, delete-orphan")

class Chapter(Base):
    __tablename__ = "chapters"
    
    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    chapter_number = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    chapter_outline = Column(Text, nullable=False)
    word_count = Column(Integer, nullable=False)
    audit_score = Column(Float, nullable=True)
    continuity_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    book = relationship("Book", back_populates="chapters")
