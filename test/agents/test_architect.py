import unittest
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.agents.architect import ArchitectAgent
from src.llm.provider import llm_client

class TestArchitectAgent(unittest.TestCase):
    """测试架构师Agent的功能"""
    
    def setUp(self):
        """设置测试环境"""
        self.agent = ArchitectAgent(llm_client)
        self.test_book = {
            'id': 1,
            'title': '测试小说',
            'genre': '都市',
            'platform': '起点中文网',
            'chapter_words': 2000,
            'target_chapters': 20,
            'outline': '这是一个测试大纲'
        }
    
    def test_generate_foundation(self):
        """测试生成基础设定"""
        print("\n=== 测试生成基础设定 ===")
        result = self.agent.generate_foundation(self.test_book, "这是测试外部上下文")
        
        # 验证返回值结构
        self.assertIsNotNone(result)
        self.assertTrue(hasattr(result, 'story_bible'))
        self.assertTrue(hasattr(result, 'volume_outline'))
        self.assertTrue(hasattr(result, 'book_rules'))
        self.assertTrue(hasattr(result, 'current_state'))
        self.assertTrue(hasattr(result, 'pending_hooks'))
        
        # 验证内容不为空
        self.assertNotEmpty(result.story_bible)
        self.assertNotEmpty(result.volume_outline)
        self.assertNotEmpty(result.book_rules)
        self.assertNotEmpty(result.current_state)
        self.assertNotEmpty(result.pending_hooks)
        
        print("✅ 测试生成基础设定通过")
    
    def test_plan_chapter(self):
        """测试规划章节内容"""
        print("\n=== 测试规划章节内容 ===")
        result = self.agent.plan_chapter(
            book=self.test_book,
            chapter_num=1,
            current_state="初始状态",
            previous_chapter_summary="",
            external_context="这是测试外部上下文"
        )
        
        # 验证返回值结构
        self.assertIsNotNone(result)
        self.assertTrue(hasattr(result, 'chapter_outline'))
        self.assertTrue(hasattr(result, 'character_states'))
        self.assertTrue(hasattr(result, 'setting'))
        self.assertTrue(hasattr(result, 'plot_points'))
        
        # 验证内容不为空
        self.assertNotEmpty(result.chapter_outline)
        self.assertNotEmpty(result.character_states)
        self.assertNotEmpty(result.setting)
        self.assertNotEmpty(result.plot_points)
        
        print("✅ 测试规划章节内容通过")
    
    def test_analyze_outline_impact(self):
        """测试分析大纲影响"""
        print("\n=== 测试分析大纲影响 ===")
        result = self.agent.analyze_outline_impact(
            old_outline="旧大纲",
            new_outline="新大纲",
            book=self.test_book,
            outline_context="这是测试大纲上下文"
        )
        
        # 验证返回值结构
        self.assertIsNotNone(result)
        self.assertIn('major_impact', result)
        self.assertIn('minor_impact', result)
        self.assertIn('affected_chapters', result)
        self.assertIn('suggestions', result)
        self.assertIn('analysis', result)
        
        print("✅ 测试分析大纲影响通过")
    
    def test_update_book_state(self):
        """测试更新书籍状态"""
        print("\n=== 测试更新书籍状态 ===")
        result = self.agent.update_book_state(
            book=self.test_book,
            chapter_num=1,
            chapter_content="这是测试章节内容",
            chapter_summary="这是测试章节摘要",
            current_state="当前状态",
            pending_hooks="当前伏笔",
            book_dir=None
        )
        
        # 验证返回值结构
        self.assertIsNotNone(result)
        self.assertIn('updated_state', result)
        self.assertIn('updated_hooks', result)
        self.assertIn('updated_ledger', result)
        self.assertIn('updated_subplots', result)
        self.assertIn('updated_emotional_arcs', result)
        self.assertIn('updated_character_matrix', result)
        
        # 验证内容不为空
        self.assertNotEmpty(result['updated_state'])
        self.assertNotEmpty(result['updated_hooks'])
        self.assertNotEmpty(result['updated_ledger'])
        self.assertNotEmpty(result['updated_subplots'])
        self.assertNotEmpty(result['updated_emotional_arcs'])
        self.assertNotEmpty(result['updated_character_matrix'])
        
        print("✅ 测试更新书籍状态通过")
    
    def assertNotEmpty(self, value):
        """断言值不为空"""
        self.assertIsNotNone(value)
        if isinstance(value, str):
            self.assertTrue(len(value.strip()) > 0)

if __name__ == '__main__':
    unittest.main()