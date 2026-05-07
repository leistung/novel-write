from typing import Dict, Any
from langgraph.graph import StateGraph, END
from src.db.crud import get_book, update_book
from src.db.config import get_db
from src.workflow.base_workflow import BaseWorkflow, BaseWorkflowState


class UpdateOutlineWorkflow(BaseWorkflow):
    def __init__(self):
        super().__init__()

    def build(self) -> StateGraph:
        def update_outline(state: BaseWorkflowState) -> Dict[str, Any]:
            book_id = state['book_id']
            new_outline = state['new_outline']

            self.log_manager.log_workflow('update_outline', '开始修改大纲', {'book_id': book_id})

            db = next(get_db())
            book = get_book(db, book_id)
            if not book:
                return {'error': '书籍不存在'}

            book_data = {
                'id': book.id,
                'title': book.title,
                'genre': book.genre,
                'platform': book.platform,
                'chapter_words': book.chapter_words,
                'target_chapters': book.target_chapters,
                'outline': book.outline
            }
            impact = self.architect_agent.analyze_outline_impact(
                book.outline or "",
                new_outline,
                book_data,
                state.get('external_context')
            )

            update_book(db, book_id, {'outline': new_outline})
            self.file_manager.save_outline(book_id, new_outline)
            self.remember(
                ('book', str(book_id), 'outline_updates'),
                'latest',
                {
                    'analysis': impact.analysis,
                    'suggestions': impact.suggestions,
                    'major_impact': impact.major_impact,
                    'minor_impact': impact.minor_impact,
                    'affected_chapters': impact.affected_chapters
                }
            )

            self.log_manager.log_workflow('update_outline', '保存到数据库', {'book_id': book_id, 'book_title': book.title})

            return {
                'result': {
                    'book_id': book_id,
                    'message': '大纲修改成功',
                    'impact_analysis': impact.analysis,
                    'suggestions': impact.suggestions,
                    'major_impact': impact.major_impact,
                    'minor_impact': impact.minor_impact,
                    'affected_chapters': impact.affected_chapters
                }
            }

        def handle_error(state: BaseWorkflowState) -> Dict[str, Any]:
            return {'result': {'error': state['error']}}

        def check_error(state: BaseWorkflowState) -> bool:
            return 'error' in state

        graph = StateGraph(BaseWorkflowState)
        graph.add_node('update_outline', update_outline)
        graph.add_node('handle_error', handle_error)
        graph.set_entry_point('update_outline')
        graph.add_conditional_edges('update_outline', check_error, {True: 'handle_error', False: END})
        graph.add_edge('handle_error', END)

        return graph
