from typing import Dict, Any
from langgraph.graph import StateGraph, END
from src.db.crud import get_book, get_chapters_by_book
from src.db.config import get_db
from src.workflow.base_workflow import BaseWorkflow, BaseWorkflowState


class AuditBookWorkflow(BaseWorkflow):
    def build(self) -> StateGraph:
        def audit_book(state: BaseWorkflowState) -> Dict[str, Any]:
            book_id = state['book_id']
            db = next(get_db())
            book = get_book(db, book_id)
            if not book:
                return {'error': '书籍不存在'}

            chapters = get_chapters_by_book(db, book_id)
            book_data = {
                'id': book.id,
                'title': book.title,
                'genre': book.genre,
                'platform': book.platform,
                'chapter_words': book.chapter_words,
                'target_chapters': book.target_chapters,
                'outline': book.outline,
                'chapter_count': len(chapters)
            }
            book_dir = self.file_manager.get_book_dir(book_id)
            evaluation = self.author_agent.evaluate_book(book_data, book_dir)
            result = {
                'book_id': book_id,
                'chapter_count': len(chapters),
                'evaluation': evaluation.get('evaluation', '')
            }
            self.remember(('book', str(book_id), 'audit'), 'latest', result)
            return {'result': result}

        def handle_error(state: BaseWorkflowState) -> Dict[str, Any]:
            return {'result': {'error': state['error']}}

        def check_error(state: BaseWorkflowState) -> bool:
            return 'error' in state

        graph = StateGraph(BaseWorkflowState)
        graph.add_node('audit_book', audit_book)
        graph.add_node('handle_error', handle_error)
        graph.set_entry_point('audit_book')
        graph.add_conditional_edges('audit_book', check_error, {True: 'handle_error', False: END})
        graph.add_edge('handle_error', END)
        return graph
