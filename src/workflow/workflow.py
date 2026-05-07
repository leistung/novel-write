from typing import Dict, Any, Optional, List
from src.workflow.create_book_workflow import CreateBookWorkflow
from src.workflow.continue_chapter_workflow import ContinueChapterWorkflow
from src.workflow.update_outline_workflow import UpdateOutlineWorkflow
from src.workflow.update_chapter_workflow import UpdateChapterWorkflow
from src.workflow.rewrite_from_chapter_workflow import RewriteFromChapterWorkflow
from src.workflow.audit_book_workflow import AuditBookWorkflow
from src.utils.log_manager import LogManager


class NovelWriteWorkflow:
    def __init__(self):
        self.log_manager = LogManager()
        # 保存工作流实例（不是编译后的对象）
        self.create_book_workflow_instance = CreateBookWorkflow()
        self.continue_chapter_workflow_instance = ContinueChapterWorkflow()
        self.update_outline_workflow_instance = UpdateOutlineWorkflow()
        self.update_chapter_workflow_instance = UpdateChapterWorkflow()
        self.rewrite_from_chapter_workflow_instance = RewriteFromChapterWorkflow()
        self.audit_book_workflow_instance = AuditBookWorkflow()
        
        # 使用 SQLite checkpoint + SQLite store，支持长流程恢复与跨流程记忆。
        self.create_book_workflow = self.create_book_workflow_instance.compile(with_checkpoint=True)
        self.continue_chapter_workflow = self.continue_chapter_workflow_instance.compile(with_checkpoint=True)
        self.update_outline_workflow = self.update_outline_workflow_instance.compile(with_checkpoint=True)
        self.update_chapter_workflow = self.update_chapter_workflow_instance.compile(with_checkpoint=True)
        self.rewrite_from_chapter_workflow = self.rewrite_from_chapter_workflow_instance.compile(with_checkpoint=True)
        self.audit_book_workflow = self.audit_book_workflow_instance.compile(with_checkpoint=True)

    @staticmethod
    def _config(thread_id: str) -> Dict[str, Any]:
        return {'configurable': {'thread_id': thread_id, 'checkpoint_ns': ''}}

    @staticmethod
    def _normalize_result(result: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(result, dict):
            return {'result': result}
        nested_result = result.get('result')
        if isinstance(nested_result, dict) and nested_result.get('error'):
            return {'error': nested_result['error'], 'result': nested_result}
        if result.get('error'):
            return {'error': result['error'], 'result': result}
        return result

    def create_book(self, book_data: Dict[str, Any], external_context: Optional[str] = None) -> Dict[str, Any]:
        book_id = book_data.get('id', 'new')
        thread_id = f"book_{book_id}_create"
        
        config = self._config(thread_id)
        
        result = self.create_book_workflow.invoke({
            'book_data': book_data,
            'external_context': external_context
        }, config)
        
        self.log_manager.log_workflow('create_book', '工作流完成', {})
        
        return self._normalize_result(result)

    def continue_chapter(self, book_id: int, chapter_num: int, external_context: Optional[str] = None) -> Dict[str, Any]:
        thread_id = f"book_{book_id}_chapter_{chapter_num}"
        
        config = self._config(thread_id)
        
        result = self.continue_chapter_workflow.invoke({
            'book_id': book_id,
            'chapter_num': chapter_num,
            'external_context': external_context
        }, config)
        
        self.log_manager.log_workflow('continue_chapter', '工作流完成', {})
        
        return self._normalize_result(result)

    def continue_chapters(self, book_id: int, start_chapter: int, count: int, external_context: Optional[str] = None) -> Dict[str, Any]:
        results = []
        current_chapter = start_chapter

        for i in range(count):
            self.log_manager.log_workflow('continue_chapters', f'开始续写第{current_chapter}章（{i+1}/{count}）', {
                'book_id': book_id, 'chapter_num': current_chapter
            })

            thread_id = f"book_{book_id}_chapter_{current_chapter}"
            config = self._config(thread_id)

            result = self.continue_chapter_workflow.invoke({
                'book_id': book_id,
                'chapter_num': current_chapter,
                'external_context': external_context
            }, config)

            result = self._normalize_result(result)

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
        thread_id = f"book_{book_id}_update_outline"
        config = self._config(thread_id)
        
        result = self.update_outline_workflow.invoke({
            'book_id': book_id,
            'new_outline': new_outline
        }, config)
        
        self.log_manager.log_workflow('update_outline', '工作流完成', {})
        
        return self._normalize_result(result).get('result', self._normalize_result(result))

    def update_chapter(self, book_id: int, chapter_num: int, new_content: str) -> Dict[str, Any]:
        thread_id = f"book_{book_id}_update_chapter_{chapter_num}"
        config = self._config(thread_id)
        
        result = self.update_chapter_workflow.invoke({
            'book_id': book_id,
            'chapter_num': chapter_num,
            'new_content': new_content
        }, config)
        
        self.log_manager.log_workflow('update_chapter', '工作流完成', {})
        
        return self._normalize_result(result).get('result', self._normalize_result(result))

    def rewrite_from_chapter(self, book_id: int, start_chapter: int, count: int = 1, external_context: Optional[str] = None) -> Dict[str, Any]:
        thread_id = f"book_{book_id}_rewrite_from_{start_chapter}"
        config = self._config(thread_id)

        cleanup = self.rewrite_from_chapter_workflow.invoke({
            'book_id': book_id,
            'start_chapter': start_chapter
        }, config)
        cleanup = self._normalize_result(cleanup)
        if 'error' in cleanup:
            return cleanup

        continued = self.continue_chapters(book_id, start_chapter, count, external_context)
        return {
            'result': {
                'cleanup': cleanup.get('result', cleanup),
                'continued': continued
            }
        }

    def audit_book(self, book_id: int) -> Dict[str, Any]:
        thread_id = f"book_{book_id}_audit"
        config = self._config(thread_id)

        result = self.audit_book_workflow.invoke({'book_id': book_id}, config)
        return self._normalize_result(result).get('result', self._normalize_result(result))

    def get_checkpoint(self, thread_id: str) -> Optional[Dict[str, Any]]:
        return self.continue_chapter_workflow_instance.get_checkpoint(thread_id)

    def list_checkpoints(self, book_id: Optional[int] = None) -> List[Dict[str, Any]]:
        return self.continue_chapter_workflow_instance.list_checkpoints(book_id)

    def delete_checkpoint(self, thread_id: str) -> bool:
        return self.continue_chapter_workflow_instance.delete_checkpoint(thread_id)

    def continue_from_checkpoint(self, thread_id: str, inputs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """从 checkpoint 继续运行工作流"""
        return self.continue_chapter_workflow_instance.continue_from_checkpoint(thread_id, inputs)

    def export_workflow_diagram(self, workflow_type: str = 'continue_chapter', output_path: str = None):
        workflow_map = {
            'create_book': self.create_book_workflow,
            'continue_chapter': self.continue_chapter_workflow,
            'update_outline': self.update_outline_workflow,
            'update_chapter': self.update_chapter_workflow,
            'rewrite_from_chapter': self.rewrite_from_chapter_workflow,
            'audit_book': self.audit_book_workflow
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
    B --> C([结束])''',
                'rewrite_from_chapter': '''graph TB
    A([开始]) --> B[prepare_rewrite]
    B --> C([结束])''',
                'audit_book': '''graph TB
    A([开始]) --> B[audit_book]
    B --> C([结束])'''
            }
            return workflow_mermaid.get(workflow_type, '')

    def print_workflow_structure(self, workflow_type: str = 'continue_chapter'):
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
            },
            'rewrite_from_chapter': {
                'name': '从指定章节重写',
                'nodes': ['prepare_rewrite', 'continue_chapters'],
                'edges': ['prepare_rewrite -> continue_chapters']
            },
            'audit_book': {
                'name': '整书评估',
                'nodes': ['audit_book'],
                'edges': ['audit_book -> END']
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
