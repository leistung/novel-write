from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, TypedDict, Union
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import InMemorySaver
from pydantic_settings import BaseSettings
from src.agents.architect import ArchitectAgent
from src.agents.writer import WriterAgent
from src.agents.continuity_auditor import ContinuityAuditor
from src.agents.auditor import AuditorAgent
from src.db.crud import create_book, get_book, update_book, create_chapter, get_chapter_by_number, update_chapter, delete_chapters_after
from src.db.config import get_db
from src.llm.provider import llm_client
from src.utils.file_manager import FileManager
from src.utils.log_manager import LogManager
import os
import sqlite3


class WorkflowConfig(BaseSettings):
    max_retries: int = 3
    timeout: int = 300

    model_config = {
        "env_file": ".env",
        "env_prefix": "novel_write_workflow_",
        "case_sensitive": False,
        "extra": "ignore"
    }


class BaseWorkflowState(TypedDict, total=False):
    book_id: Optional[int]
    book_data: Optional[Dict[str, Any]]
    chapter_num: Optional[int]
    chapter_content: Optional[Any]
    chapter_outline: Optional[str]
    external_context: Optional[str]
    current_state: Optional[str]
    previous_chapter_summary: Optional[str]
    error: Optional[str]
    result: Optional[Dict[str, Any]]
    chapter_plan: Optional[Any]
    check_result: Optional[Dict[str, Any]]
    consistency_result: Optional[Any]
    score_result: Optional[Any]
    architect_retry_count: int
    writer_retry_count: int
    architect_feedback: str
    writer_feedback: str
    consistency_passed: bool
    score_passed: bool


class BaseWorkflow(ABC):
    _checkpoint_saver = None

    def __init__(self):
        self.file_manager = FileManager()
        self.log_manager = LogManager()
        self.architect_agent = ArchitectAgent(llm_client.client)
        self.writer_agent = WriterAgent(llm_client.client)
        self.consistency_agent = ContinuityAuditor(llm_client.client)
        self.author_agent = AuditorAgent(llm_client.client)
        self._ensure_checkpoint_saver()

    @classmethod
    def _ensure_checkpoint_saver(cls):
        if cls._checkpoint_saver is None:
            cls._checkpoint_saver = InMemorySaver()

    @abstractmethod
    def build(self) -> StateGraph:
        pass

    def compile(self, with_checkpoint: bool = True) -> Any:
        graph = self.build()
        if with_checkpoint and self._checkpoint_saver:
            return graph.compile(checkpointer=self._checkpoint_saver)
        return graph.compile()

    def create_thread_id(self, book_id: int, chapter_num: Optional[int] = None) -> str:
        if chapter_num is not None:
            return f"book_{book_id}_chapter_{chapter_num}"
        return f"book_{book_id}_create"

    def get_checkpoint(self, thread_id: str) -> Optional[Dict[str, Any]]:
        if self._checkpoint_saver is None:
            return None
        from langchain_core.runnables import RunnableConfig
        config = RunnableConfig()
        checkpoint = self._checkpoint_saver.get(thread_id, config)
        if checkpoint:
            return {
                'thread_id': thread_id,
                'checkpoint': checkpoint,
                'metadata': checkpoint.get('metadata', {})
            }
        return None

    def list_checkpoints(self, book_id: Optional[int] = None) -> list:
        if self._checkpoint_saver is None:
            return []
        
        checkpoints = []
        from langchain_core.runnables import RunnableConfig
        config = RunnableConfig()
        
        try:
            for thread_id in self._checkpoint_saver.list(config):
                if book_id is None or thread_id.startswith(f"book_{book_id}"):
                    checkpoint = self._checkpoint_saver.get(thread_id, config)
                    if checkpoint:
                        checkpoints.append({
                            'thread_id': thread_id,
                            'created_at': checkpoint.get('metadata', {}).get('created_at'),
                            'status': checkpoint.get('metadata', {}).get('status', 'unknown')
                        })
        except Exception as e:
            self.log_manager.log_workflow('checkpoint', f'列出checkpoint失败: {e}', {})
        
        return checkpoints

    def delete_checkpoint(self, thread_id: str) -> bool:
        if self._checkpoint_saver is None:
            return False
        try:
            from langchain_core.runnables import RunnableConfig
            config = RunnableConfig()
            self._checkpoint_saver.delete(thread_id, config)
            return True
        except Exception:
            return False

    def continue_from_checkpoint(self, thread_id: str, inputs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if self._checkpoint_saver is None:
            return {'error': 'Checkpoint saver not initialized'}
        
        checkpoint = self.get_checkpoint(thread_id)
        if not checkpoint:
            return {'error': f'No checkpoint found for thread_id: {thread_id}'}
        
        workflow = self.compile(with_checkpoint=True)
        config = {'configurable': {'thread_id': thread_id}}
        
        try:
            if inputs:
                result = workflow.invoke(inputs, config)
            else:
                result = workflow.invoke({}, config)
            return {'success': True, 'result': result}
        except Exception as e:
            return {'error': str(e)}
