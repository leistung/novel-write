from typing import Dict, Any
from langgraph.graph import StateGraph, END
from src.db.crud import get_chapter_by_number, update_chapter
from src.db.config import get_db
from src.workflow.base_workflow import BaseWorkflow, BaseWorkflowState


class UpdateChapterWorkflow(BaseWorkflow):
    def __init__(self):
        super().__init__()

    def build(self) -> StateGraph:
        def update_chapter_content(state: BaseWorkflowState) -> Dict[str, Any]:
            book_id = state['book_id']
            chapter_num = state['chapter_num']
            new_content = state['new_content']

            db = next(get_db())
            chapter = get_chapter_by_number(db, book_id, chapter_num)
            if chapter:
                update_chapter(db, chapter.id, {'content': new_content, 'word_count': len(new_content)})
                return {
                    'result': {
                        'chapter_id': chapter.id,
                        'message': '章节修改成功'
                    }
                }
            else:
                return {'error': '章节不存在'}

        def handle_error(state: BaseWorkflowState) -> Dict[str, Any]:
            return {'result': {'error': state['error']}}

        def check_error(state: BaseWorkflowState) -> bool:
            return 'error' in state

        graph = StateGraph(BaseWorkflowState)
        graph.add_node('update_chapter_content', update_chapter_content)
        graph.add_node('handle_error', handle_error)

        graph.set_entry_point('update_chapter_content')
        graph.add_conditional_edges(
            'update_chapter_content',
            check_error,
            {True: 'handle_error', False: END}
        )
        graph.add_edge('handle_error', END)

        return graph
