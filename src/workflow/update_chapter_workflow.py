from typing import Dict, Any
from langgraph.graph import StateGraph, END
from src.db.crud import get_book, get_chapter_by_number, update_chapter
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
            book = get_book(db, book_id)
            if not book:
                return {'error': '书籍不存在'}

            chapter = get_chapter_by_number(db, book_id, chapter_num)
            if chapter:
                book_data = {
                    'id': book.id,
                    'title': book.title,
                    'genre': book.genre,
                    'platform': book.platform,
                    'chapter_words': book.chapter_words,
                    'target_chapters': book.target_chapters,
                    'outline': book.outline
                }
                book_dir = self.file_manager.get_book_dir(book_id)
                previous_chapter = get_chapter_by_number(db, book_id, chapter_num - 1)
                previous_content = previous_chapter.content if previous_chapter else ""
                consistency = self.consistency_agent.check_chapter_consistency(
                    book_data, chapter_num, new_content, previous_content, book_dir
                )
                score = self.author_agent.score_chapter(
                    book_data, chapter_num, new_content, chapter.chapter_outline or "", book_dir
                )
                update_chapter(db, chapter.id, {
                    'content': new_content,
                    'word_count': len(new_content),
                    'continuity_score': consistency.score,
                    'audit_score': score.score
                })
                self.file_manager.save_chapter_content(book_id, chapter_num, new_content)
                return {
                    'result': {
                        'chapter_id': chapter.id,
                        'message': '章节修改成功',
                        'continuity_score': consistency.score,
                        'audit_score': score.score,
                        'warnings': [] if consistency.is_consistent and score.passed else [
                            consistency.suggestions,
                            score.suggestions
                        ]
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
