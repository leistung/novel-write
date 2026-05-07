from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, TypedDict, Union
from langgraph.graph import StateGraph, END
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
import pickle


class PickleSerializer:
    def dumps_typed(self, obj: Any) -> tuple[str, bytes]:
        return "pickle", pickle.dumps(obj)

    def loads_typed(self, data: tuple[str, bytes]) -> Any:
        _type, payload = data
        return pickle.loads(payload)


class WorkflowConfig(BaseSettings):
    max_retries: int = 3
    timeout: int = 300
    checkpoint_db: str = "data/workflow_checkpoints.sqlite"
    store_db: str = "data/workflow_store.sqlite"

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
    new_outline: Optional[str]
    new_content: Optional[str]
    start_chapter: Optional[int]
    count: Optional[int]
    impact_analysis: Optional[Any]


class BaseWorkflow(ABC):
    _checkpoint_saver = None
    _store = None
    _checkpoint_conn = None
    _store_conn = None
    config = WorkflowConfig()

    def __init__(self):
        self.file_manager = FileManager()
        self.log_manager = LogManager()
        self.architect_agent = ArchitectAgent(llm_client.client)
        self.writer_agent = WriterAgent(llm_client.client)
        self.consistency_agent = ContinuityAuditor(llm_client.client)
        self.author_agent = AuditorAgent(llm_client.client)
        self._ensure_persistence()

    @classmethod
    def _ensure_persistence(cls):
        base = BaseWorkflow
        if base._checkpoint_saver is None:
            checkpoint_path = base._resolve_path(base.config.checkpoint_db)
            base._checkpoint_saver = base._build_sqlite_checkpoint_saver(checkpoint_path)

        if base._store is None:
            store_path = base._resolve_path(base.config.store_db)
            base._store = base._build_sqlite_store(store_path)

        cls._checkpoint_saver = base._checkpoint_saver
        cls._store = base._store

    @classmethod
    def _build_sqlite_checkpoint_saver(cls, path: str):
        from langgraph.checkpoint.sqlite import SqliteSaver

        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            cls._checkpoint_conn = cls._open_sqlite(path)
            saver = SqliteSaver(cls._checkpoint_conn, serde=PickleSerializer())
            saver.setup()
            return saver
        except sqlite3.OperationalError:
            fallback = cls._fallback_sqlite_path(path, "checkpoint")
            os.makedirs(os.path.dirname(fallback), exist_ok=True)
            cls._checkpoint_conn = cls._open_sqlite(fallback)
            saver = SqliteSaver(cls._checkpoint_conn, serde=PickleSerializer())
            saver.setup()
            return saver

    @classmethod
    def _build_sqlite_store(cls, path: str):
        from langgraph.store.sqlite import SqliteStore

        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            cls._store_conn = cls._open_sqlite(path)
            store = SqliteStore(cls._store_conn)
            store.setup()
            return store
        except sqlite3.OperationalError:
            fallback = cls._fallback_sqlite_path(path, "store")
            os.makedirs(os.path.dirname(fallback), exist_ok=True)
            cls._store_conn = cls._open_sqlite(fallback)
            store = SqliteStore(cls._store_conn)
            store.setup()
            return store

    @staticmethod
    def _open_sqlite(path: str) -> sqlite3.Connection:
        conn = sqlite3.connect(path, timeout=1, check_same_thread=False, isolation_level=None)
        try:
            conn.execute("PRAGMA journal_mode=WAL")
        except sqlite3.OperationalError:
            pass
        conn.execute("PRAGMA busy_timeout=1000")
        return conn

    @staticmethod
    def _fallback_sqlite_path(path: str, suffix: str) -> str:
        base, ext = os.path.splitext(path)
        return f"{base}_{suffix}_{os.getpid()}{ext or '.sqlite'}"

    @staticmethod
    def _resolve_path(path: str) -> str:
        if os.path.isabs(path):
            return path
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        return os.path.join(project_root, path)

    @abstractmethod
    def build(self) -> StateGraph:
        pass

    def compile(self, with_checkpoint: bool = True) -> Any:
        graph = self.build()
        if with_checkpoint and self._checkpoint_saver:
            return graph.compile(checkpointer=self._checkpoint_saver, store=self._store)
        return graph.compile(store=self._store)

    def create_thread_id(self, book_id: int, chapter_num: Optional[int] = None) -> str:
        if chapter_num is not None:
            return f"book_{book_id}_chapter_{chapter_num}"
        return f"book_{book_id}_create"

    def get_checkpoint(self, thread_id: str) -> Optional[Dict[str, Any]]:
        if self._checkpoint_saver is None:
            return None
        config = {'configurable': {'thread_id': thread_id, 'checkpoint_ns': ''}}
        checkpoint = self._checkpoint_saver.get(config)
        if checkpoint:
            return {
                'thread_id': thread_id,
                'checkpoint': checkpoint,
                'metadata': checkpoint.get('metadata', {}) if isinstance(checkpoint, dict) else {}
            }
        return None

    def list_checkpoints(self, book_id: Optional[int] = None) -> list:
        if self._checkpoint_saver is None:
            return []
        
        checkpoints = []
        config = None
        
        try:
            for item in self._checkpoint_saver.list(config):
                item_config = getattr(item, 'config', {}) or {}
                configurable = item_config.get('configurable', {})
                thread_id = configurable.get('thread_id', '')
                if thread_id and (book_id is None or thread_id.startswith(f"book_{book_id}")):
                    metadata = getattr(item, 'metadata', {}) or {}
                    checkpoints.append({
                        'thread_id': thread_id,
                        'checkpoint_id': configurable.get('checkpoint_id'),
                        'created_at': metadata.get('created_at'),
                        'status': metadata.get('status', 'available')
                    })
        except Exception as e:
            self.log_manager.log_workflow('checkpoint', f'列出checkpoint失败: {e}', {})
        
        return checkpoints

    def delete_checkpoint(self, thread_id: str) -> bool:
        if self._checkpoint_saver is None:
            return False
        try:
            self._checkpoint_saver.delete_thread(thread_id)
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
        config = {'configurable': {'thread_id': thread_id, 'checkpoint_ns': ''}}
        
        try:
            if inputs:
                result = workflow.invoke(inputs, config)
            else:
                result = workflow.invoke({}, config)
            return {'success': True, 'result': result}
        except Exception as e:
            return {'error': str(e)}

    def remember(self, namespace: tuple, key: str, value: Dict[str, Any]) -> None:
        if self._store is not None:
            self._store.put(namespace, key, value)

    def recall(self, namespace: tuple, key: str) -> Optional[Dict[str, Any]]:
        if self._store is None:
            return None
        item = self._store.get(namespace, key)
        return item.value if item else None
