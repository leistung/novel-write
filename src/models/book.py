from pydantic import BaseModel, Field
from typing import Optional, List

class Platform(str):
    QIDIAN = "qidian"
    FANQIE = "fanqie"
    JINJIANG = "jinjiang"
    OTHER = "other"

class Genre(str):
    XUANHUAN = "xuanhuan"
    XIANXIA = "xianxia"
    URBAN = "urban"
    SCI_FI = "sci-fi"
    HORROR = "horror"
    MYSTERY = "mystery"
    ROMANCE = "romance"
    OTHER = "other"

class BookStatus(str):
    PLANNING = "planning"
    WRITING = "writing"
    COMPLETED = "completed"
    HIATUS = "hiatus"

class FanficMode(str):
    CANON = "canon"
    AU = "au"
    OOC = "ooc"
    CP = "cp"

class BookConfig(BaseModel):
    title: str
    genre: Genre
    platform: Platform = Platform.OTHER
    chapter_words: int = Field(default=10000, ge=1000, le=50000)
    target_chapters: int = Field(default=100, ge=1, le=1000)
    status: BookStatus = BookStatus.PLANNING
    fanfic_mode: Optional[FanficMode] = None
    parent_book: Optional[str] = None
    brief: Optional[str] = None
