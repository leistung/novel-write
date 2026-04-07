from pydantic import BaseModel, Field
from typing import Optional, List

class ChapterStatus(str):
    DRAFT = "draft"
    AUDITED = "audited"
    REVISED = "revised"
    PUBLISHED = "published"

class ChapterMeta(BaseModel):
    chapter_num: int = Field(ge=1)
    title: str
    status: ChapterStatus = ChapterStatus.DRAFT
    word_count: int = Field(ge=0)
    created_at: str  # ISO format
    updated_at: str  # ISO format
    summary: Optional[str] = None
    hooks: Optional[List[str]] = None
    characters: Optional[List[str]] = None
