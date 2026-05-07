import os
import shutil
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from src.db.crud import get_book, delete_chapters_after
from src.db.config import get_db
from src.workflow.base_workflow import BaseWorkflow, BaseWorkflowState


class RewriteFromChapterWorkflow(BaseWorkflow):
    def build(self) -> StateGraph:
        def prepare_rewrite(state: BaseWorkflowState) -> Dict[str, Any]:
            book_id = state['book_id']
            start_chapter = state['start_chapter']

            db = next(get_db())
            book = get_book(db, book_id)
            if not book:
                return {'error': '书籍不存在'}

            deleted_count = delete_chapters_after(db, book_id, start_chapter)
            book_dir = self.file_manager.get_book_dir(book_id)
            removed_dirs = []

            for name in os.listdir(book_dir):
                if not name.startswith("chapter_"):
                    continue
                try:
                    chapter_num = int(name.split("_", 1)[1])
                except ValueError:
                    continue
                if chapter_num >= start_chapter:
                    chapter_dir = os.path.abspath(os.path.join(book_dir, name))
                    if os.path.commonpath([os.path.abspath(book_dir), chapter_dir]) == os.path.abspath(book_dir):
                        shutil.rmtree(chapter_dir, ignore_errors=True)
                        removed_dirs.append(name)

            result = {
                'book_id': book_id,
                'start_chapter': start_chapter,
                'deleted_count': deleted_count,
                'removed_dirs': removed_dirs,
                'message': f'已清理第{start_chapter}章及之后内容'
            }
            self.remember(('book', str(book_id), 'rewrite'), 'latest', result)
            return {'result': result}

        def handle_error(state: BaseWorkflowState) -> Dict[str, Any]:
            return {'result': {'error': state['error']}}

        def check_error(state: BaseWorkflowState) -> bool:
            return 'error' in state

        graph = StateGraph(BaseWorkflowState)
        graph.add_node('prepare_rewrite', prepare_rewrite)
        graph.add_node('handle_error', handle_error)
        graph.set_entry_point('prepare_rewrite')
        graph.add_conditional_edges('prepare_rewrite', check_error, {True: 'handle_error', False: END})
        graph.add_edge('handle_error', END)
        return graph
