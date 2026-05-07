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
            update_book(db, book_id, {'outline': new_outline})

            self.log_manager.log_workflow('update_outline', '保存到数据库', {'book_id': book_id, 'book_title': book.title})

            return {
                'result': {
                    'book_id': book_id,
                    'message': '大纲修改成功'
                }
            }

        graph = StateGraph(BaseWorkflowState)
        graph.add_node('update_outline', update_outline)
        graph.set_entry_point('update_outline')
        graph.add_edge('update_outline', END)

        return graph
