from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from src.llm.provider import LLMClient

class AgentContext:
    def __init__(self, book_id: str, chapter_num: Optional[int] = None, **kwargs):
        self.book_id = book_id
        self.chapter_num = chapter_num
        self.kwargs = kwargs

class BaseAgent:
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
