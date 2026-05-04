from typing import Dict, Any, Optional, TypedDict
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

class WorkflowState(TypedDict, total=False):
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
    consistency_result: Optional[Dict[str, Any]]
    score_result: Optional[Dict[str, Any]]

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
        
        graph = StateGraph(WorkflowState)
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
                'chapter_outline': chapter_plan.chapter_outline + '...' if chapter_plan.chapter_outline else ''
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
                'suggestions': check_result['suggestions'] + '...' if check_result['suggestions'] else ''
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
            
            # 获取书籍目录
            book_dir = self.file_manager.get_book_dir(book_data['id'])
            
            # 将chapter_plan对象转换为字典
            chapter_plan_dict = {
                'chapter_outline': chapter_plan.chapter_outline if hasattr(chapter_plan, 'chapter_outline') else str(chapter_plan),
                'character_states': chapter_plan.character_states if hasattr(chapter_plan, 'character_states') else '',
                'setting': chapter_plan.setting if hasattr(chapter_plan, 'setting') else '',
                'plot_points': chapter_plan.plot_points if hasattr(chapter_plan, 'plot_points') else []
            }
            
            # 写章节
            input_data = WriteChapterInput(
                book=book_data,
                chapter_number=chapter_num,
                chapter_plan=chapter_plan_dict,
                external_context=external_context,
                word_count_override=book_data['chapter_words'],
                book_dir=book_dir
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
                'content_preview': chapter_content.content + '...' if chapter_content.content else ''
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
                'feedback': feedback + '...' if feedback else ''
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
            
            # 记录工作流开始
            self.log_manager.log_workflow('continue_chapter', '开始更新书籍状态', {'book_id': book_id, 'chapter_num': chapter_num})
            
            # 读取历史章节摘要
            existing_summary = self.file_manager.read_chapter_summary(book_id)
            
            # 构建新章节摘要 - 使用 writer_agent 生成的 chapter_summary
            new_chapter_summary = f"第{chapter_num}章 {chapter_content.title}：{chapter_content.chapter_summary}"
            
            # 追加新章节摘要
            if existing_summary:
                updated_chapter_summary = existing_summary + "\n" + new_chapter_summary
            else:
                updated_chapter_summary = new_chapter_summary
            
            # 直接使用 writer_agent 结算返回的结果，不要再调用 architect_agent
            final_updated_state = chapter_content.updated_state
            final_updated_hooks = chapter_content.updated_hooks
            final_updated_subplots = chapter_content.updated_subplots
            final_updated_emotional_arcs = chapter_content.updated_emotional_arcs
            final_updated_character_matrix = chapter_content.updated_character_matrix
            
            # 记录使用 writer_agent 结果
            self.log_manager.log_agent('Writer', '使用结算结果更新状态文件', {'book_id': book_id, 'chapter_num': chapter_num})
            
            # 保存到数据库
            db = next(get_db())
            chapter_outline_str = chapter_plan.chapter_outline if hasattr(chapter_plan, 'chapter_outline') else chapter_plan.get('chapter_outline', '') if isinstance(chapter_plan, dict) else str(chapter_plan)
            chapter = create_chapter(db, {
                'book_id': book_id,
                'chapter_number': chapter_num,
                'title': chapter_content.title,
                'content': chapter_content.content,
                'chapter_outline': chapter_outline_str,
                'word_count': chapter_content.word_count,
                'audit_score': state['score_result']['score'],
                'continuity_score': state['consistency_result']['score']
            })
            
            # 更新书籍状态
            update_book(db, book_id, {
                'current_state': final_updated_state,
                'pending_hooks': final_updated_hooks,
                'subplot_board': final_updated_subplots,
                'emotional_arcs': final_updated_emotional_arcs,
                'character_matrix': final_updated_character_matrix,
                'chapter_summaries': updated_chapter_summary
            })
            
            # 记录数据库操作
            self.log_manager.log_workflow('continue_chapter', '保存到数据库', {'book_id': book_id, 'chapter_id': chapter.id, 'chapter_num': chapter_num})
            
            # 保存到文件系统
            self.file_manager.save_current_state(book_id, final_updated_state)
            self.file_manager.save_pending_hooks(book_id, final_updated_hooks)
            self.file_manager.save_subplot_board(book_id, final_updated_subplots)
            self.file_manager.save_emotional_arcs(book_id, final_updated_emotional_arcs)
            self.file_manager.save_character_matrix(book_id, final_updated_character_matrix)
            self.file_manager.save_chapter_summary(book_id, updated_chapter_summary)
            
            # 记录文件保存
            self.log_manager.log_workflow('continue_chapter', '保存状态到文件系统', {'book_id': book_id, 'files': ['current_state.md', 'pending_hooks.md', 'subplot_board.md', 'emotional_arcs.md', 'character_matrix.md', 'chapter_summaries.md']})
            
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
        
        graph = StateGraph(WorkflowState)
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
        
        graph = StateGraph(WorkflowState)
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
        
        graph = StateGraph(WorkflowState)
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
    
    def continue_chapters(self, book_id: int, start_chapter: int, count: int, external_context: Optional[str] = None) -> Dict[str, Any]:
        """连续续写多个章节
        
        Args:
            book_id: 书籍ID
            start_chapter: 起始章节号
            count: 续写章节数量
            external_context: 外部指令（可选）
            
        Returns:
            包含成功信息的字典
        """
        results = []
        current_chapter = start_chapter
        
        for i in range(count):
            self.log_manager.log_workflow('continue_chapters', f'开始续写第{current_chapter}章（{i+1}/{count}）', {'book_id': book_id, 'chapter_num': current_chapter})
            
            result = self.continue_chapter_workflow.invoke({
                'book_id': book_id,
                'chapter_num': current_chapter,
                'external_context': external_context
            })
            
            if 'error' in result:
                self.log_manager.log_workflow('continue_chapters', f'第{current_chapter}章续写失败', {'error': result['error']})
                return {
                    'error': result['error'],
                    'completed_count': i,
                    'results': results
                }
            
            results.append({
                'chapter_num': current_chapter,
                'result': result.get('result', {})
            })
            
            self.log_manager.log_workflow('continue_chapters', f'第{current_chapter}章续写完成', {'chapter_num': current_chapter})
            current_chapter += 1
        
        return {
            'completed_count': count,
            'results': results
        }
    
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

    def export_workflow_diagram(self, workflow_type: str = 'continue_chapter', output_path: str = None):
        """导出工作流图

        Args:
            workflow_type: 工作流类型 ('create_book', 'continue_chapter', 'update_outline', 'update_chapter')
            output_path: 输出文件路径，默认为 None 则返回图片数据

        Returns:
            如果 output_path 为 None，返回 Mermaid 图表定义字符串
        """
        workflow_map = {
            'create_book': self.create_book_workflow,
            'continue_chapter': self.continue_chapter_workflow,
            'update_outline': self.update_outline_workflow,
            'update_chapter': self.update_chapter_workflow
        }

        if workflow_type not in workflow_map:
            raise ValueError(f"不支持的工作流类型: {workflow_type}，可选: {list(workflow_map.keys())}")

        workflow = workflow_map[workflow_type]

        try:
            img_data = workflow.get_graph().draw_mermaid_png()
            if output_path:
                with open(output_path, 'wb') as f:
                    f.write(img_data)
                return output_path
            return img_data
        except Exception as e:
            workflow_mermaid = {
                'create_book': '''graph TB
    A([开始]) --> B[generate_foundation]
    B --> C([结束])''',
                'continue_chapter': '''graph TB
    A([开始]) --> B[plan_chapter]
    B --> C{check_outline}
    C -->|失败| H[handle_error]
    C -->|成功| D[write_chapter]
    D --> E{check_consistency}
    E -->|失败| H
    E -->|成功| F[score_chapter]
    F -->|失败| H
    F -->|成功| G[update_book_state]
    G --> I([结束])
    H --> J([结束])''',
                'update_outline': '''graph TB
    A([开始]) --> B[update_outline]
    B --> C([结束])''',
                'update_chapter': '''graph TB
    A([开始]) --> B[update_chapter]
    B --> C([结束])'''
            }
            return workflow_mermaid.get(workflow_type, '')

    def print_workflow_structure(self, workflow_type: str = 'continue_chapter'):
        """打印工作流结构（文本形式）

        Args:
            workflow_type: 工作流类型
        """
        workflow_structures = {
            'create_book': {
                'name': '创建书籍',
                'nodes': ['generate_foundation'],
                'edges': ['generate_foundation -> END']
            },
            'continue_chapter': {
                'name': '续写章节',
                'nodes': ['plan_chapter', 'check_outline', 'write_chapter', 'check_consistency', 'score_chapter', 'update_book_state', 'handle_error'],
                'edges': [
                    'plan_chapter -> check_outline',
                    'check_outline --[失败]--> handle_error',
                    'check_outline --[成功]--> write_chapter',
                    'write_chapter -> check_consistency',
                    'check_consistency --[失败]--> handle_error',
                    'check_consistency --[成功]--> score_chapter',
                    'score_chapter --[失败]--> handle_error',
                    'score_chapter --[成功]--> update_book_state',
                    'update_book_state -> END',
                    'handle_error -> END'
                ]
            },
            'update_outline': {
                'name': '修改大纲',
                'nodes': ['update_outline'],
                'edges': ['update_outline -> END']
            },
            'update_chapter': {
                'name': '修改章节',
                'nodes': ['update_chapter'],
                'edges': ['update_chapter -> END']
            }
        }

        if workflow_type not in workflow_structures:
            print(f"不支持的工作流类型: {workflow_type}，可选: {list(workflow_structures.keys())}")
            return

        structure = workflow_structures[workflow_type]

        print(f"\n{'='*60}")
        print(f"工作流: {workflow_type} ({structure['name']})")
        print('='*60)

        print(f"\n节点 ({len(structure['nodes'])}):")
        for i, node in enumerate(structure['nodes'], 1):
            print(f"  {i}. {node}")

        print("\n流程:")
        for edge in structure['edges']:
            print(f"  {edge}")

        print("\n说明:")
        if workflow_type == 'continue_chapter':
            print("  1. plan_chapter: 规划章节内容")
            print("  2. check_outline: 检查章节大纲是否合理")
            print("  3. write_chapter: 写章节")
            print("  4. check_consistency: 检查连续性（与前一章的衔接）")
            print("  5. score_chapter: 评分章节")
            print("  6. update_book_state: 更新书籍状态（当前状态、伏笔、支线等）")
            print("  7. handle_error: 处理错误")

        print('='*60 + "\n")
