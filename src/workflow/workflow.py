from typing import Dict, Any, Optional
from langgraph.graph import StateGraph, END
from src.agents.architect import ArchitectAgent
from src.agents.writer import WriterAgent
from src.agents.continuity import ContinuityAuditor as ConsistencyAgent
from src.agents.auditor import AuditorAgent as AuthorAgent
from src.db.crud import create_book, get_book, update_book, create_chapter, get_chapter_by_number, update_chapter, delete_chapters_after
from src.db.config import get_db
from src.llm.provider import llm_client
from src.utils.file_manager import FileManager
from src.utils.log_manager import LogManager
from sqlalchemy.orm import Session

class WorkflowState:
    """工作流状态"""
    def __init__(self):
        self.book_id: Optional[int] = None
        self.book_data: Optional[Dict[str, Any]] = None
        self.chapter_num: Optional[int] = None
        self.chapter_content: Optional[str] = None
        self.chapter_outline: Optional[str] = None
        self.external_context: Optional[str] = None
        self.current_state: Optional[str] = None
        self.previous_chapter_summary: Optional[str] = None
        self.error: Optional[str] = None
        self.result: Optional[Dict[str, Any]] = None

class NovelWriteWorkflow:
    def __init__(self):
        # 初始化工具
        self.file_manager = FileManager()
        self.log_manager = LogManager()
        
        # 初始化agent
        self.architect_agent = ArchitectAgent(llm_client.client)
        self.writer_agent = WriterAgent(llm_client.client)
        self.consistency_agent = ConsistencyAgent(llm_client.client)
        self.author_agent = AuthorAgent(llm_client.client)
        self.create_book_workflow = self._build_create_book_workflow()
        self.continue_chapter_workflow = self._build_continue_chapter_workflow()
        self.update_outline_workflow = self._build_update_outline_workflow()
        self.update_chapter_workflow = self._build_update_chapter_workflow()
    
    def _build_create_book_workflow(self):
        """构建创建新书工作流"""
        def generate_foundation(state: Dict[str, Any]) -> Dict[str, Any]:
            """生成基础设定"""
            book_data = state['book_data']
            external_context = state.get('external_context', '')
            
            # 记录工作流开始
            self.log_manager.log_workflow('create_book', '开始生成基础设定', {'book_title': book_data.get('title')})
            
            # 生成基础设定
            foundation = self.architect_agent.generate_foundation(book_data, external_context)
            
            # 记录Agent执行
            self.log_manager.log_agent('Architect', '生成基础设定完成', {'book_title': book_data.get('title')})
            
            # 保存到数据库
            db = next(get_db())
            book_data.update({
                'story_bible': foundation.story_bible,
                'volume_outline': foundation.volume_outline,
                'book_rules': foundation.book_rules,
                'current_state': foundation.current_state,
                'pending_hooks': foundation.pending_hooks
            })
            book = create_book(db, book_data)
            
            # 记录数据库操作
            self.log_manager.log_workflow('create_book', '保存到数据库', {'book_id': book.id, 'book_title': book.title})
            
            # 保存到文件系统
            self.file_manager.save_story_bible(book.id, foundation.story_bible)
            self.file_manager.save_volume_outline(book.id, foundation.volume_outline)
            self.file_manager.save_book_rules(book.id, foundation.book_rules)
            self.file_manager.save_current_state(book.id, foundation.current_state)
            self.file_manager.save_pending_hooks(book.id, foundation.pending_hooks)
            
            # 记录文件保存
            self.log_manager.log_workflow('create_book', '保存到文件系统', {'book_id': book.id, 'files': ['story_bible.md', 'volume_outline.md', 'book_rules.md', 'current_state.md', 'pending_hooks.md']})
            
            return {
                'book_id': book.id,
                'book_data': book_data,
                'result': {
                    'story_bible': foundation.story_bible,
                    'volume_outline': foundation.volume_outline,
                    'book_rules': foundation.book_rules
                }
            }
        
        graph = StateGraph(Dict[str, Any])
        graph.add_node('generate_foundation', generate_foundation)
        graph.set_entry_point('generate_foundation')
        graph.add_edge('generate_foundation', END)
        
        return graph.compile()
    
    def _build_continue_chapter_workflow(self):
        """构建续写下一章工作流"""
        def plan_chapter(state: Dict[str, Any]) -> Dict[str, Any]:
            """规划章节内容"""
            book_id = state['book_id']
            chapter_num = state['chapter_num']
            external_context = state.get('external_context', '')
            
            # 记录工作流开始
            self.log_manager.log_workflow('continue_chapter', '开始规划章节', {'book_id': book_id, 'chapter_num': chapter_num})
            
            # 获取书籍信息
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
            
            # 获取前一章摘要
            previous_chapter = get_chapter_by_number(db, book_id, chapter_num - 1)
            previous_chapter_summary = previous_chapter.chapter_outline if previous_chapter else ""
            
            # 规划章节
            chapter_plan = self.architect_agent.plan_chapter(
                book_data, chapter_num, book.current_state or "", previous_chapter_summary, external_context
            )
            
            # 记录Agent执行
            self.log_manager.log_agent('Architect', '规划章节完成', {
                'book_id': book_id, 
                'chapter_num': chapter_num,
                'chapter_outline': chapter_plan.chapter_outline[:100] + '...' if chapter_plan.chapter_outline else ''
            })
            
            return {
                'book_data': book_data,
                'chapter_plan': chapter_plan,
                'current_state': book.current_state or "",
                'chapter_num': chapter_num,
                'external_context': external_context
            }
        
        def check_outline(state: Dict[str, Any]) -> Dict[str, Any]:
            """检查章节大纲是否合理"""
            chapter_plan = state['chapter_plan']
            book_data = state['book_data']
            chapter_num = state.get('chapter_num')
            
            # 记录工作流开始
            self.log_manager.log_workflow('continue_chapter', '开始检查章节大纲', {'book_id': book_data['id'], 'chapter_num': chapter_num})
            
            # 检查大纲
            check_result = self.writer_agent.check_chapter_outline(chapter_plan.chapter_outline, book_data)
            
            # 记录Agent执行
            self.log_manager.log_agent('Writer', '检查章节大纲完成', {
                'book_id': book_data['id'], 
                'chapter_num': chapter_num, 
                'is_valid': check_result['is_valid'],
                'suggestions': check_result['suggestions'][:100] + '...' if check_result['suggestions'] else ''
            })
            
            if not check_result['is_valid']:
                return {'error': f"章节大纲不合理: {check_result['suggestions']}"}
            
            return {
                'check_result': check_result,
                'book_data': book_data,
                'chapter_plan': chapter_plan,
                'current_state': state.get('current_state'),
                'chapter_num': chapter_num,
                'external_context': state.get('external_context')
            }
        
        def write_chapter(state: Dict[str, Any]) -> Dict[str, Any]:
            """写下一章"""
            book_data = state['book_data']
            chapter_num = state['chapter_num']
            chapter_plan = state['chapter_plan']
            current_state = state['current_state']
            external_context = state.get('external_context', '')
            
            # 记录工作流开始
            self.log_manager.log_workflow('continue_chapter', '开始写章节', {'book_id': book_data['id'], 'chapter_num': chapter_num})
            
            # 导入WriteChapterInput
            from src.agents.writer import WriteChapterInput
            
            # 写章节
            input_data = WriteChapterInput(
                book=book_data,
                chapter_number=chapter_num,
                chapter_plan=chapter_plan,
                external_context=external_context,
                word_count_override=book_data['chapter_words']
            )
            chapter_content = self.writer_agent.write_chapter(input_data)
            
            # 记录Agent执行
            token_usage_info = chapter_content.token_usage if chapter_content.token_usage else {}
            self.log_manager.log_agent('Writer', '写章节完成', {
                'book_id': book_data['id'], 
                'chapter_num': chapter_num, 
                'word_count': len(chapter_content.content),
                'title': chapter_content.title,
                'token_usage': token_usage_info,
                'content_preview': chapter_content.content[:100] + '...' if chapter_content.content else ''
            })
            
            # 保存到文件系统
            self.file_manager.save_chapter_content(book_data['id'], chapter_num, chapter_content.content)
            
            # 记录文件保存
            self.log_manager.log_workflow('continue_chapter', '保存章节到文件系统', {'book_id': book_data['id'], 'chapter_num': chapter_num})
            
            return {
                'chapter_content': chapter_content,
                'book_data': book_data,
                'chapter_num': chapter_num,
                'chapter_plan': state.get('chapter_plan'),
                'current_state': state.get('current_state'),
                'book_id': book_data['id']
            }
        
        def check_consistency(state: Dict[str, Any]) -> Dict[str, Any]:
            """检查连续性"""
            book_data = state['book_data']
            chapter_content = state['chapter_content']
            chapter_num = state['chapter_num']
            
            # 记录工作流开始
            self.log_manager.log_workflow('continue_chapter', '开始检查连续性', {'book_id': book_data['id'], 'chapter_num': chapter_num})
            
            # 获取前一章内容
            db = next(get_db())
            previous_chapter = get_chapter_by_number(db, book_data['id'], chapter_num - 1)
            previous_chapter_content = previous_chapter.content if previous_chapter else ""
            
            # 检查连续性
            consistency_result = self.consistency_agent.check_consistency(
                chapter_content.content, previous_chapter_content, book_data
            )
            
            # 记录Agent执行
            issues = consistency_result.get('issues', [])
            issue_messages = [issue.get('message', '') for issue in issues[:3]] + ['...'] if len(issues) > 3 else [issue.get('message', '') for issue in issues]
            self.log_manager.log_agent('Consistency', '检查连续性完成', {
                'book_id': book_data['id'], 
                'chapter_num': chapter_num, 
                'issue_count': len(issues),
                'issues': issue_messages
            })
            
            if issues:
                return {'error': f"连续性问题: {issue_messages}"}
            
            return {
                'consistency_result': consistency_result,
                'book_data': book_data,
                'chapter_content': chapter_content,
                'chapter_num': chapter_num,
                'chapter_plan': state.get('chapter_plan'),
                'current_state': state.get('current_state'),
                'book_id': book_data['id']
            }
        
        def score_chapter(state: Dict[str, Any]) -> Dict[str, Any]:
            """评分"""
            book_data = state['book_data']
            chapter_content = state['chapter_content']
            chapter_num = state['chapter_num']
            
            # 记录工作流开始
            self.log_manager.log_workflow('continue_chapter', '开始评分章节', {'book_id': book_data['id'], 'chapter_num': chapter_num})
            
            # 评分章节
            score_result = self.author_agent.score_chapter(chapter_content.content, book_data)
            
            # 记录Agent执行
            suggestions = score_result.get('suggestions', [])
            feedback = ' '.join(suggestions) if suggestions else ''
            self.log_manager.log_agent('Author', '评分章节完成', {
                'book_id': book_data['id'], 
                'chapter_num': chapter_num, 
                'score': score_result.get('score', 0),
                'feedback': feedback[:100] + '...' if feedback else ''
            })
            
            if score_result.get('score', 0) < 70:
                return {'error': f"章节评分过低: {feedback}"}
            
            return {
                'score_result': score_result,
                'consistency_result': state.get('consistency_result'),
                'book_data': book_data,
                'chapter_content': chapter_content,
                'chapter_num': chapter_num,
                'chapter_plan': state.get('chapter_plan'),
                'current_state': state.get('current_state'),
                'book_id': book_data['id']
            }
        
        def update_book_state(state: Dict[str, Any]) -> Dict[str, Any]:
            """更新书籍状态"""
            book_id = state['book_id']
            book_data = state['book_data']
            chapter_num = state['chapter_num']
            chapter_content = state['chapter_content']
            chapter_plan = state['chapter_plan']
            current_state = state['current_state']
            
            # 记录工作流开始
            self.log_manager.log_workflow('continue_chapter', '开始更新书籍状态', {'book_id': book_id, 'chapter_num': chapter_num})
            
            # 更新状态
            updated_state = self.architect_agent.update_book_state(
                book_data, chapter_num, chapter_content.content, "", current_state, ""
            )
            
            # 记录Agent执行
            self.log_manager.log_agent('Architect', '更新书籍状态完成', {'book_id': book_id, 'chapter_num': chapter_num})
            
            # 保存到数据库
            db = next(get_db())
            chapter = create_chapter(db, {
                'book_id': book_id,
                'chapter_number': chapter_num,
                'title': chapter_content.title,
                'content': chapter_content.content,
                'chapter_outline': chapter_plan.chapter_outline,
                'word_count': chapter_content.word_count,
                'audit_score': state['score_result']['score'],
                'continuity_score': state['consistency_result']['score']
            })
            
            # 更新书籍状态
            update_book(db, book_id, {
                'current_state': updated_state['updated_state'],
                'pending_hooks': updated_state['updated_hooks'],
                'subplot_board': updated_state['updated_subplots'],
                'emotional_arcs': updated_state['updated_emotional_arcs'],
                'character_matrix': updated_state['updated_character_matrix']
            })
            
            # 记录数据库操作
            self.log_manager.log_workflow('continue_chapter', '保存到数据库', {'book_id': book_id, 'chapter_id': chapter.id, 'chapter_num': chapter_num})
            
            # 保存到文件系统
            self.file_manager.save_current_state(book_id, updated_state['updated_state'])
            self.file_manager.save_pending_hooks(book_id, updated_state['updated_hooks'])
            self.file_manager.save_subplot_board(book_id, updated_state['updated_subplots'])
            self.file_manager.save_emotional_arcs(book_id, updated_state['updated_emotional_arcs'])
            self.file_manager.save_character_matrix(book_id, updated_state['updated_character_matrix'])
            
            # 记录文件保存
            self.log_manager.log_workflow('continue_chapter', '保存状态到文件系统', {'book_id': book_id, 'files': ['current_state.md', 'pending_hooks.md', 'subplot_board.md', 'emotional_arcs.md', 'character_matrix.md']})
            
            return {
                'result': {
                    'chapter_id': chapter.id,
                    'chapter_number': chapter_num,
                    'title': chapter_content.title,
                    'content': chapter_content.content,
                    'word_count': chapter_content.word_count,
                    'audit_score': state['score_result'].get('score', 0),
                    'continuity_score': state['consistency_result'].get('score', 0)
                }
            }
        
        def handle_error(state: Dict[str, Any]) -> Dict[str, Any]:
            """处理错误"""
            return {'result': {'error': state['error']}}
        
        graph = StateGraph(Dict[str, Any])
        graph.add_node('plan_chapter', plan_chapter)
        graph.add_node('check_outline', check_outline)
        graph.add_node('write_chapter', write_chapter)
        graph.add_node('check_consistency', check_consistency)
        graph.add_node('score_chapter', score_chapter)
        graph.add_node('update_book_state', update_book_state)
        graph.add_node('handle_error', handle_error)
        
        graph.set_entry_point('plan_chapter')
        graph.add_edge('plan_chapter', 'check_outline')
        graph.add_conditional_edges('check_outline', lambda s: 'error' in s, {True: 'handle_error', False: 'write_chapter'})
        graph.add_edge('write_chapter', 'check_consistency')
        graph.add_conditional_edges('check_consistency', lambda s: 'error' in s, {True: 'handle_error', False: 'score_chapter'})
        graph.add_conditional_edges('score_chapter', lambda s: 'error' in s, {True: 'handle_error', False: 'update_book_state'})
        graph.add_edge('update_book_state', END)
        graph.add_edge('handle_error', END)
        
        return graph.compile()
    
    def _build_update_outline_workflow(self):
        """构建修改大纲工作流"""
        def update_outline(state: Dict[str, Any]) -> Dict[str, Any]:
            """修改大纲"""
            book_id = state['book_id']
            new_outline = state['new_outline']
            
            # 记录工作流开始
            self.log_manager.log_workflow('update_outline', '开始修改大纲', {'book_id': book_id})
            
            # 保存到数据库
            db = next(get_db())
            book = get_book(db, book_id)
            update_book(db, book_id, {'outline': new_outline})
            
            # 记录数据库操作
            self.log_manager.log_workflow('update_outline', '保存到数据库', {'book_id': book_id, 'book_title': book.title})
            
            return {
                'result': {
                    'book_id': book_id,
                    'message': '大纲修改成功'
                }
            }
        
        graph = StateGraph(Dict[str, Any])
        graph.add_node('update_outline', update_outline)
        graph.set_entry_point('update_outline')
        graph.add_edge('update_outline', END)
        
        return graph.compile()
    
    def _build_update_chapter_workflow(self):
        """构建修改章节工作流"""
        def update_chapter_content(state: Dict[str, Any]) -> Dict[str, Any]:
            """修改章节内容"""
            book_id = state['book_id']
            chapter_num = state['chapter_num']
            new_content = state['new_content']
            
            # 保存到数据库
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
        
        def handle_error(state: Dict[str, Any]) -> Dict[str, Any]:
            """处理错误"""
            return {'result': {'error': state['error']}}
        
        graph = StateGraph(Dict[str, Any])
        graph.add_node('update_chapter_content', update_chapter_content)
        graph.add_node('handle_error', handle_error)
        
        graph.set_entry_point('update_chapter_content')
        graph.add_conditional_edges('update_chapter_content', lambda s: 'error' in s, {True: 'handle_error', False: END})
        graph.add_edge('handle_error', END)
        
        return graph.compile()
    
    def create_book(self, book_data: Dict[str, Any], external_context: Optional[str] = None) -> Dict[str, Any]:
        """创建新书"""
        result = self.create_book_workflow.invoke({
            'book_data': book_data,
            'external_context': external_context
        })
        return result
    
    def continue_chapter(self, book_id: int, chapter_num: int, external_context: Optional[str] = None) -> Dict[str, Any]:
        """续写下一章"""
        result = self.continue_chapter_workflow.invoke({
            'book_id': book_id,
            'chapter_num': chapter_num,
            'external_context': external_context
        })
        return result
    
    def update_outline(self, book_id: int, new_outline: str) -> Dict[str, Any]:
        """修改大纲"""
        result = self.update_outline_workflow.invoke({
            'book_id': book_id,
            'new_outline': new_outline
        })
        return result.get('result', {})
    
    def update_chapter(self, book_id: int, chapter_num: int, new_content: str) -> Dict[str, Any]:
        """修改章节内容"""
        result = self.update_chapter_workflow.invoke({
            'book_id': book_id,
            'chapter_num': chapter_num,
            'new_content': new_content
        })
        return result.get('result', {})
