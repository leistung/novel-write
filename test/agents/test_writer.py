import unittest
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.agents.writer import WriterAgent, WriteChapterInput
from src.llm.provider import llm_client

class TestWriterAgent(unittest.TestCase):
    """测试写手Agent的功能"""
    
    def setUp(self):
        """设置测试环境"""
        self.agent = WriterAgent(llm_client)
        self.test_book = {
            'id': 1,
            'title': '测试小说',
            'genre': '都市',
            'platform': '起点中文网',
            'chapter_words': 2000,
            'target_chapters': 20,
            'outline': '这是一个测试大纲'
        }
    
    def test_write_chapter(self):
        """测试写章节内容"""
        print("\n=== 测试写章节内容 ===")
        
        # 创建测试输入
        write_input = WriteChapterInput(
            book=self.test_book,
            chapter_number=1,
            chapter_plan={
                'chapter_outline': '这是测试章节大纲',
                'character_states': '这是测试角色状态',
                'setting': '这是测试场景',
                'plot_points': '这是测试情节点'
            },
            external_context="这是测试外部上下文",
            word_count_override=1000,
            book_dir=None
        )
        
        result = self.agent.write_chapter(write_input)
        
        # 验证返回值结构
        self.assertIsNotNone(result)
        self.assertTrue(hasattr(result, 'title'))
        self.assertTrue(hasattr(result, 'content'))
        self.assertTrue(hasattr(result, 'word_count'))
        self.assertTrue(hasattr(result, 'updated_state'))
        self.assertTrue(hasattr(result, 'updated_hooks'))
        self.assertTrue(hasattr(result, 'chapter_summary'))
        self.assertTrue(hasattr(result, 'updated_ledger'))
        self.assertTrue(hasattr(result, 'updated_subplots'))
        self.assertTrue(hasattr(result, 'updated_emotional_arcs'))
        self.assertTrue(hasattr(result, 'updated_character_matrix'))
        
        # 验证内容不为空
        self.assertNotEmpty(result.title)
        self.assertNotEmpty(result.content)
        self.assertGreater(result.word_count, 0)
        self.assertNotEmpty(result.updated_state)
        self.assertNotEmpty(result.updated_hooks)
        self.assertNotEmpty(result.chapter_summary)
        
        print("✅ 测试写章节内容通过")
    
    def assertNotEmpty(self, value):
        """断言值不为空"""
        self.assertIsNotNone(value)
        if isinstance(value, str):
            self.assertTrue(len(value.strip()) > 0)

if __name__ == '__main__':
    unittest.main()