from typing import Dict, Any
from langgraph.graph import StateGraph, END
from src.db.crud import create_book
from src.db.config import get_db
from src.workflow.base_workflow import BaseWorkflow, BaseWorkflowState


class CreateBookWorkflow(BaseWorkflow):
    def __init__(self):
        super().__init__()

    def build(self) -> StateGraph:
        def generate_foundation(state: BaseWorkflowState) -> Dict[str, Any]:
            book_data = state['book_data']
            external_context = state.get('external_context', '')

            self.log_manager.log_workflow('create_book', '开始生成基础设定', {'book_title': book_data.get('title')})

            foundation = self.architect_agent.generate_foundation(book_data, external_context)

            self.log_manager.log_agent('Architect', '生成基础设定完成', {'book_title': book_data.get('title')})

            db = next(get_db())
            book_data.update({
                'story_bible': foundation.story_bible,
                'volume_outline': foundation.volume_outline,
                'book_rules': foundation.book_rules,
                'current_state': foundation.current_state,
                'pending_hooks': foundation.pending_hooks
            })
            book = create_book(db, book_data)

            self.log_manager.log_workflow('create_book', '保存到数据库', {'book_id': book.id, 'book_title': book.title})

            self.file_manager.save_story_bible(book.id, foundation.story_bible)
            self.file_manager.save_volume_outline(book.id, foundation.volume_outline)
            self.file_manager.save_book_rules(book.id, foundation.book_rules)
            self.file_manager.save_current_state(book.id, foundation.current_state)
            self.file_manager.save_pending_hooks(book.id, foundation.pending_hooks)

            self.log_manager.log_workflow('create_book', '保存到文件系统', {
                'book_id': book.id,
                'files': ['story_bible.md', 'volume_outline.md', 'book_rules.md', 'current_state.md', 'pending_hooks.md']
            })

            return {
                'book_id': book.id,
                'book_data': book_data,
                'result': {
                    'story_bible': foundation.story_bible,
                    'volume_outline': foundation.volume_outline,
                    'book_rules': foundation.book_rules
                }
            }

        graph = StateGraph(BaseWorkflowState)
        graph.add_node('generate_foundation', generate_foundation)
        graph.set_entry_point('generate_foundation')
        graph.add_edge('generate_foundation', END)

        return graph
