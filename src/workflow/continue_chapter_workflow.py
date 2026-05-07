from typing import Dict, Any
from langgraph.graph import StateGraph, END
from src.db.crud import get_book, get_chapter_by_number, create_chapter, update_book
from src.db.config import get_db
from src.workflow.base_workflow import BaseWorkflow, BaseWorkflowState


class ContinueChapterWorkflow(BaseWorkflow):
    def __init__(self):
        super().__init__()

    def build(self) -> StateGraph:
        def plan_chapter(state: BaseWorkflowState) -> Dict[str, Any]:
            book_id = state['book_id']
            chapter_num = state['chapter_num']
            external_context = state.get('external_context', '')
            revision_feedback = state.get('writer_feedback', '')
            architect_feedback = state.get('architect_feedback', '')
            architect_retry_count = state.get('architect_retry_count', 0)

            self.log_manager.log_workflow('continue_chapter', f'开始规划章节（第{architect_retry_count + 1}次尝试）', {
                'book_id': book_id, 'chapter_num': chapter_num
            })

            db = next(get_db())
            book = get_book(db, book_id)
            book_data = {
                'id': book.id,
                'title': book.title,
                'genre': book.genre,
                'platform': book.platform,
                'chapter_words': book.chapter_words,
                'target_chapters': book.target_chapters,
                'outline': book.outline
            }

            previous_chapter = get_chapter_by_number(db, book_id, chapter_num - 1)
            previous_chapter_summary = previous_chapter.chapter_outline if previous_chapter else ""

            combined_feedback = external_context
            if architect_feedback:
                combined_feedback = f"{external_context}\n\n【上次问题反馈】\n{architect_feedback}" if external_context else architect_feedback

            chapter_plan = self.architect_agent.plan_chapter(
                book_data, chapter_num, book.current_state or "", previous_chapter_summary, combined_feedback
            )

            self.log_manager.log_agent('Architect', '规划章节完成', {
                'book_id': book_id,
                'chapter_num': chapter_num,
                'retry_count': architect_retry_count,
                'chapter_outline': chapter_plan.chapter_outline[:100] + '...' if chapter_plan.chapter_outline else ''
            })

            return {
                'book_data': book_data,
                'chapter_plan': chapter_plan,
                'current_state': book.current_state or "",
                'chapter_num': chapter_num,
                'external_context': external_context,
                'architect_retry_count': architect_retry_count,
                'architect_feedback': '',
                'writer_feedback': '',
                'consistency_passed': False,
                'score_passed': False
            }

        def check_outline(state: BaseWorkflowState) -> Dict[str, Any]:
            chapter_plan = state['chapter_plan']
            book_data = state['book_data']
            chapter_num = state['chapter_num']
            writer_retry_count = state.get('writer_retry_count', 0)

            self.log_manager.log_workflow('continue_chapter', f'开始检查章节大纲（第{writer_retry_count + 1}次尝试）', {
                'book_id': book_data['id'], 'chapter_num': chapter_num
            })

            check_result = self.writer_agent.validate_chapter_outline(chapter_plan.chapter_outline, book_data)

            self.log_manager.log_agent('Writer', '检查章节大纲完成', {
                'book_id': book_data['id'],
                'chapter_num': chapter_num,
                'is_valid': check_result['is_valid'],
                'suggestions': check_result['suggestions'][:100] + '...' if check_result['suggestions'] else '',
                'retry_count': writer_retry_count
            })

            if not check_result['is_valid']:
                new_retry_count = writer_retry_count + 1
                if new_retry_count >= 3:
                    return {'error': f"章节大纲连续3次不合理，终止: {check_result['suggestions']}"}

                self.log_manager.log_agent('Writer', '大纲不合理，打回Architect重试', {
                    'retry_count': new_retry_count,
                    'suggestions': check_result['suggestions']
                })

                return {
                    'chapter_plan': chapter_plan,
                    'book_data': book_data,
                    'chapter_num': chapter_num,
                    'current_state': state.get('current_state'),
                    'external_context': state.get('external_context'),
                    'architect_retry_count': state.get('architect_retry_count', 0) + 1,
                    'writer_retry_count': new_retry_count,
                    'architect_feedback': f"Writer检查：大纲不合理 - {check_result['suggestions']}",
                    'writer_feedback': '',
                    'consistency_passed': False,
                    'score_passed': False
                }

            return {
                'check_result': check_result,
                'book_data': book_data,
                'chapter_plan': chapter_plan,
                'current_state': state.get('current_state'),
                'chapter_num': chapter_num,
                'external_context': state.get('external_context'),
                'architect_retry_count': state.get('architect_retry_count', 0),
                'writer_retry_count': writer_retry_count,
                'architect_feedback': state.get('architect_feedback', ''),
                'writer_feedback': '',
                'consistency_passed': False,
                'score_passed': False
            }

        def write_chapter(state: BaseWorkflowState) -> Dict[str, Any]:
            book_data = state['book_data']
            chapter_num = state['chapter_num']
            chapter_plan = state['chapter_plan']
            current_state = state['current_state']
            external_context = state.get('external_context', '')
            revision_feedback = state.get('writer_feedback', '')

            self.log_manager.log_workflow('continue_chapter', '开始写章节', {
                'book_id': book_data['id'], 'chapter_num': chapter_num
            })

            from src.agents.writer import WriteChapterInput
            book_dir = self.file_manager.get_book_dir(book_data['id'])

            chapter_plan_dict = {
                'chapter_outline': chapter_plan.chapter_outline if hasattr(chapter_plan, 'chapter_outline') else str(chapter_plan),
                'character_states': chapter_plan.character_states if hasattr(chapter_plan, 'character_states') else '',
                'setting': chapter_plan.setting if hasattr(chapter_plan, 'setting') else '',
                'plot_points': chapter_plan.plot_points if hasattr(chapter_plan, 'plot_points') else []
            }

            input_data = WriteChapterInput(
                book=book_data,
                chapter_number=chapter_num,
                chapter_plan=chapter_plan_dict,
                external_context=external_context,
                word_count_override=book_data['chapter_words'],
                book_dir=book_dir,
                revision_feedback=revision_feedback
            )
            chapter_content = self.writer_agent.write_chapter(input_data)

            token_usage_info = chapter_content.token_usage if chapter_content.token_usage else {}
            self.log_manager.log_agent('Writer', '写章节完成', {
                'book_id': book_data['id'],
                'chapter_num': chapter_num,
                'word_count': len(chapter_content.content),
                'title': chapter_content.title,
                'token_usage': token_usage_info
            })

            return {
                'chapter_content': chapter_content,
                'book_data': book_data,
                'chapter_num': chapter_num,
                'chapter_plan': chapter_plan,
                'current_state': current_state,
                'external_context': external_context,
                'architect_retry_count': state.get('architect_retry_count', 0),
                'writer_retry_count': state.get('writer_retry_count', 0),
                'architect_feedback': state.get('architect_feedback', ''),
                'writer_feedback': state.get('writer_feedback', ''),
                'consistency_passed': False,
                'score_passed': False
            }

        def check_consistency(state: BaseWorkflowState) -> Dict[str, Any]:
            book_data = state['book_data']
            chapter_content = state['chapter_content']
            chapter_num = state['chapter_num']

            self.log_manager.log_workflow('continue_chapter', '开始检查连续性', {
                'book_id': book_data['id'], 'chapter_num': chapter_num
            })

            db = next(get_db())
            previous_chapter = get_chapter_by_number(db, book_data['id'], chapter_num - 1)
            previous_chapter_content = previous_chapter.content if previous_chapter else ""

            consistency_result = self.consistency_agent.check_chapter_consistency(
                book_data, chapter_num, chapter_content.content, previous_chapter_content
            )

            issues = []
            if consistency_result.plot_breaks:
                issues.extend([{'type': 'plot', 'message': msg} for msg in consistency_result.plot_breaks])
            if consistency_result.character_breaks:
                issues.extend([{'type': 'character', 'message': msg} for msg in consistency_result.character_breaks])
            if consistency_result.setting_breaks:
                issues.extend([{'type': 'setting', 'message': msg} for msg in consistency_result.setting_breaks])

            issue_messages = [issue.get('message', '') for issue in issues[:3]]
            self.log_manager.log_agent('Consistency', '检查连续性完成', {
                'book_id': book_data['id'],
                'chapter_num': chapter_num,
                'issue_count': len(issues),
                'score': consistency_result.score,
                'issues': issue_messages
            })

            if issues or not consistency_result.is_consistent or consistency_result.score < 80:
                if not issue_messages:
                    issue_messages = [consistency_result.suggestions or consistency_result.consistency_report or f"连续性评分过低：{consistency_result.score}"]
                new_retry_count = state.get('writer_retry_count', 0) + 1
                if new_retry_count >= 3:
                    return {'error': f"连续性问题连续3次无法解决，终止: {issue_messages}"}

                self.log_manager.log_agent('Consistency', '连续性问题，打回Writer重写', {
                    'retry_count': new_retry_count,
                    'issues': issue_messages
                })

                return {
                    'chapter_content': chapter_content,
                    'book_data': book_data,
                    'chapter_num': chapter_num,
                    'chapter_plan': state.get('chapter_plan'),
                    'current_state': state.get('current_state'),
                    'external_context': state.get('external_context'),
                    'architect_retry_count': state.get('architect_retry_count', 0),
                    'writer_retry_count': new_retry_count,
                    'architect_feedback': state.get('architect_feedback', ''),
                    'writer_feedback': f"Checker检查：连续性问题 - {'; '.join(issue_messages)}",
                    'consistency_passed': False,
                    'score_passed': False
                }

            return {
                'consistency_result': consistency_result,
                'chapter_content': chapter_content,
                'book_data': book_data,
                'chapter_num': chapter_num,
                'chapter_plan': state.get('chapter_plan'),
                'current_state': state.get('current_state'),
                'external_context': state.get('external_context'),
                'architect_retry_count': state.get('architect_retry_count', 0),
                'writer_retry_count': state.get('writer_retry_count', 0),
                'architect_feedback': '',
                'writer_feedback': '',
                'consistency_passed': True,
                'score_passed': False
            }

        def score_chapter(state: BaseWorkflowState) -> Dict[str, Any]:
            book_data = state['book_data']
            chapter_content = state['chapter_content']
            chapter_num = state['chapter_num']
            architect_retry_count = state.get('architect_retry_count', 0)

            self.log_manager.log_workflow('continue_chapter', '开始评分章节', {
                'book_id': book_data['id'], 'chapter_num': chapter_num
            })

            book_dir = self.file_manager.get_book_dir(book_data['id'])
            chapter_summary = getattr(chapter_content, 'chapter_summary', '')
            score_result = self.author_agent.score_chapter(book_data, chapter_num, chapter_content.content, chapter_summary, book_dir)

            suggestions = score_result.suggestions
            feedback = suggestions if suggestions else ''
            score = score_result.score

            self.log_manager.log_agent('Author', '评分章节完成', {
                'book_id': book_data['id'],
                'chapter_num': chapter_num,
                'score': score,
                'feedback': feedback[:100] + '...' if feedback else '',
                'retry_count': architect_retry_count
            })

            if score < 80:
                new_retry_count = architect_retry_count + 1
                if new_retry_count >= 3:
                    return {'error': f"章节评分连续3次低于80分，终止: {feedback}"}

                self.log_manager.log_agent('Author', '评分过低，打回Architect重写', {
                    'retry_count': new_retry_count,
                    'score': score,
                    'feedback': feedback
                })

                return {
                    'chapter_content': chapter_content,
                    'book_data': book_data,
                    'chapter_num': chapter_num,
                    'chapter_plan': state.get('chapter_plan'),
                    'current_state': state.get('current_state'),
                    'external_context': state.get('external_context'),
                    'architect_retry_count': new_retry_count,
                    'writer_retry_count': 0,
                    'architect_feedback': f"Author评分{score}分：{feedback}",
                    'writer_feedback': '',
                    'consistency_passed': True,
                    'score_passed': False
                }

            return {
                'score_result': score_result,
                'consistency_result': state.get('consistency_result'),
                'chapter_content': chapter_content,
                'book_data': book_data,
                'chapter_num': chapter_num,
                'chapter_plan': state.get('chapter_plan'),
                'current_state': state.get('current_state'),
                'external_context': state.get('external_context'),
                'architect_retry_count': architect_retry_count,
                'writer_retry_count': state.get('writer_retry_count', 0),
                'architect_feedback': '',
                'writer_feedback': '',
                'consistency_passed': True,
                'score_passed': True
            }

        def update_book_state(state: BaseWorkflowState) -> Dict[str, Any]:
            book_id = state['book_id']
            book_data = state['book_data']
            chapter_num = state['chapter_num']
            chapter_content = state['chapter_content']
            chapter_plan = state['chapter_plan']

            self.log_manager.log_workflow('continue_chapter', '开始更新书籍状态', {
                'book_id': book_id, 'chapter_num': chapter_num
            })

            existing_summary = self.file_manager.read_chapter_summary(book_id)
            new_chapter_summary = f"第{chapter_num}章 {chapter_content.title}：{chapter_content.chapter_summary}"
            updated_chapter_summary = existing_summary + "\n" + new_chapter_summary if existing_summary else new_chapter_summary

            final_updated_state = chapter_content.updated_state
            final_updated_hooks = chapter_content.updated_hooks
            final_updated_subplots = chapter_content.updated_subplots
            final_updated_emotional_arcs = chapter_content.updated_emotional_arcs
            final_updated_character_matrix = chapter_content.updated_character_matrix

            self.log_manager.log_agent('Writer', '使用结算结果更新状态文件', {
                'book_id': book_id, 'chapter_num': chapter_num
            })

            db = next(get_db())
            chapter_outline_str = chapter_plan.chapter_outline if hasattr(chapter_plan, 'chapter_outline') else str(chapter_plan)

            score_result = state.get('score_result')
            consistency_result = state.get('consistency_result')
            audit_score = score_result.score if score_result else 0
            continuity_score = consistency_result.score if consistency_result else 0

            chapter = create_chapter(db, {
                'book_id': book_id,
                'chapter_number': chapter_num,
                'title': chapter_content.title,
                'content': chapter_content.content,
                'chapter_outline': chapter_outline_str,
                'word_count': chapter_content.word_count,
                'audit_score': audit_score,
                'continuity_score': continuity_score
            })

            update_book(db, book_id, {
                'current_state': final_updated_state,
                'pending_hooks': final_updated_hooks,
                'subplot_board': final_updated_subplots,
                'emotional_arcs': final_updated_emotional_arcs,
                'character_matrix': final_updated_character_matrix,
                'chapter_summaries': updated_chapter_summary
            })

            self.log_manager.log_workflow('continue_chapter', '保存到数据库', {
                'book_id': book_id, 'chapter_id': chapter.id, 'chapter_num': chapter_num
            })

            self.file_manager.save_current_state(book_id, final_updated_state)
            self.file_manager.save_chapter_content(book_id, chapter_num, chapter_content.content)
            self.file_manager.save_pending_hooks(book_id, final_updated_hooks)
            self.file_manager.save_subplot_board(book_id, final_updated_subplots)
            self.file_manager.save_emotional_arcs(book_id, final_updated_emotional_arcs)
            self.file_manager.save_character_matrix(book_id, final_updated_character_matrix)
            self.file_manager.save_chapter_summary(book_id, updated_chapter_summary)

            self.log_manager.log_workflow('continue_chapter', '保存状态到文件系统', {'book_id': book_id})

            return {
                'result': {
                    'chapter_id': chapter.id,
                    'chapter_number': chapter_num,
                    'title': chapter_content.title,
                    'content': chapter_content.content,
                    'word_count': chapter_content.word_count,
                    'audit_score': audit_score,
                    'continuity_score': continuity_score
                }
            }

        def route_next_step(state: BaseWorkflowState) -> str:
            if 'error' in state:
                return 'handle_error'

            consistency_passed = state.get('consistency_passed', False)
            score_passed = state.get('score_passed', False)
            architect_retry_count = state.get('architect_retry_count', 0)
            writer_retry_count = state.get('writer_retry_count', 0)

            if state.get('architect_feedback', ''):
                return 'plan_chapter'
            elif state.get('writer_feedback', ''):
                return 'write_chapter'

            if consistency_passed and score_passed:
                return 'update_book_state'

            if not consistency_passed:
                return 'write_chapter'

            if consistency_passed and not score_passed:
                return 'score_chapter'

            return 'update_book_state'

        def handle_error(state: BaseWorkflowState) -> Dict[str, Any]:
            return {'result': {'error': state['error']}}

        graph = StateGraph(BaseWorkflowState)
        graph.add_node('plan_chapter', plan_chapter)
        graph.add_node('check_outline', check_outline)
        graph.add_node('write_chapter', write_chapter)
        graph.add_node('check_consistency', check_consistency)
        graph.add_node('score_chapter', score_chapter)
        graph.add_node('update_book_state', update_book_state)
        graph.add_node('handle_error', handle_error)

        graph.set_entry_point('plan_chapter')
        graph.add_edge('plan_chapter', 'check_outline')
        graph.add_conditional_edges('check_outline', route_next_step, {
            'plan_chapter': 'plan_chapter',
            'write_chapter': 'write_chapter',
            'update_book_state': 'update_book_state',
            'handle_error': 'handle_error'
        })
        graph.add_edge('write_chapter', 'check_consistency')
        graph.add_conditional_edges('check_consistency', route_next_step, {
            'write_chapter': 'write_chapter',
            'plan_chapter': 'plan_chapter',
            'score_chapter': 'score_chapter',
            'update_book_state': 'update_book_state',
            'handle_error': 'handle_error'
        })
        graph.add_conditional_edges('score_chapter', route_next_step, {
            'plan_chapter': 'plan_chapter',
            'write_chapter': 'write_chapter',
            'update_book_state': 'update_book_state',
            'handle_error': 'handle_error'
        })
        graph.add_edge('update_book_state', END)
        graph.add_edge('handle_error', END)

        return graph
