import unittest
import sys
import os
import shutil

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.pipeline.runner import PipelineRunner, PipelineConfig
from src.llm.provider import llm_client

class TestPipelineRunner(unittest.TestCase):
    """测试Pipeline工作流的功能"""
    
    def setUp(self):
        """设置测试环境"""
        self.runner = PipelineRunner(llm_client)
        self.test_book = {
            'id': 1,
            'title': '测试小说',
            'genre': '都市',
            'platform': '起点中文网',
            'chapter_words': 2000,
            'target_chapters': 20,
            'outline': '这是一个测试大纲'
        }
        # 创建临时测试目录
        self.test_book_dir = os.path.join('data', 'test_book')
        os.makedirs(self.test_book_dir, exist_ok=True)
    
    def tearDown(self):
        """清理测试环境"""
        # 删除临时测试目录
        if os.path.exists(self.test_book_dir):
            shutil.rmtree(self.test_book_dir)
    
    def test_create_book_foundation(self):
        """测试创建书籍基础设定"""
        print("\n=== 测试创建书籍基础设定 ===")
        result = self.runner.create_book_foundation(self.test_book, "这是测试外部上下文")
        
        # 验证返回值结构
        self.assertIsNotNone(result)
        self.assertIn('story_bible', result)
        self.assertIn('volume_outline', result)
        self.assertIn('book_rules', result)
        self.assertIn('current_state', result)
        self.assertIn('pending_hooks', result)
        
        # 验证内容不为空
        self.assertNotEmpty(result['story_bible'])
        self.assertNotEmpty(result['volume_outline'])
        self.assertNotEmpty(result['book_rules'])
        self.assertNotEmpty(result['current_state'])
        self.assertNotEmpty(result['pending_hooks'])
        
        print("✅ 测试创建书籍基础设定通过")
    
    def test_continue_next_chapter(self):
        """测试续写下一章"""
        print("\n=== 测试续写下一章 ===")
        
        # 首先创建基础设定
        self.runner.create_book_foundation(self.test_book, "这是测试外部上下文")
        
        # 测试续写下一章
        result = self.runner.continue_next_chapter(
            book=self.test_book,
            chapter_num=1,
            external_context="这是测试外部上下文",
            word_count_override=1000,
            book_dir=self.test_book_dir
        )
        
        # 验证返回值结构
        self.assertIsNotNone(result)
        self.assertIn('chapter_num', result)
        self.assertIn('title', result)
        self.assertIn('content', result)
        self.assertIn('word_count', result)
        self.assertIn('audit_score', result)
        self.assertIn('continuity_score', result)
        self.assertIn('revisions', result)
        self.assertIn('updated_state', result)
        self.assertIn('updated_hooks', result)
        self.assertIn('chapter_summary', result)
        self.assertIn('state_update', result)
        
        # 验证内容不为空
        self.assertNotEmpty(result['title'])
        self.assertNotEmpty(result['content'])
        self.assertGreater(result['word_count'], 0)
        self.assertGreater(result['audit_score'], 0)
        self.assertGreater(result['continuity_score'], 0)
        self.assertNotEmpty(result['updated_state'])
        self.assertNotEmpty(result['updated_hooks'])
        self.assertNotEmpty(result['chapter_summary'])
        
        print("✅ 测试续写下一章通过")
    
    def test_rewrite_chapter(self):
        """测试重写章节"""
        print("\n=== 测试重写章节 ===")
        
        # 首先创建基础设定
        self.runner.create_book_foundation(self.test_book, "这是测试外部上下文")
        
        # 测试重写章节
        result = self.runner.rewrite_chapter(
            book=self.test_book,
            chapter_num=1,
            external_context="这是测试外部上下文",
            word_count_override=1000,
            book_dir=self.test_book_dir
        )
        
        # 验证返回值结构
        self.assertIsNotNone(result)
        self.assertIn('chapter_num', result)
        self.assertIn('title', result)
        self.assertIn('content', result)
        self.assertIn('word_count', result)
        self.assertIn('audit_score', result)
        self.assertIn('continuity_score', result)
        
        # 验证内容不为空
        self.assertNotEmpty(result['title'])
        self.assertNotEmpty(result['content'])
        self.assertGreater(result['word_count'], 0)
        self.assertGreater(result['audit_score'], 0)
        self.assertGreater(result['continuity_score'], 0)
        
        print("✅ 测试重写章节通过")
    
    def test_rewrite_from_chapter(self):
        """测试从指定章节开始重写"""
        print("\n=== 测试从指定章节开始重写 ===")
        
        # 首先创建基础设定
        self.runner.create_book_foundation(self.test_book, "这是测试外部上下文")
        
        # 测试从指定章节开始重写
        result = self.runner.rewrite_from_chapter(
            book=self.test_book,
            chapter_num=2,
            external_context="这是测试外部上下文",
            word_count_override=1000,
            book_dir=self.test_book_dir
        )
        
        # 验证返回值结构
        self.assertIsNotNone(result)
        self.assertIn('chapter_num', result)
        self.assertIn('title', result)
        self.assertIn('content', result)
        self.assertIn('word_count', result)
        self.assertIn('audit_score', result)
        self.assertIn('continuity_score', result)
        
        # 验证内容不为空
        self.assertNotEmpty(result['title'])
        self.assertNotEmpty(result['content'])
        self.assertGreater(result['word_count'], 0)
        self.assertGreater(result['audit_score'], 0)
        self.assertGreater(result['continuity_score'], 0)
        
        print("✅ 测试从指定章节开始重写通过")
    
    def test_update_story_outline(self):
        """测试修改故事大纲"""
        print("\n=== 测试修改故事大纲 ===")
        
        result = self.runner.update_story_outline(
            book=self.test_book,
            new_outline="这是新的测试大纲",
            outline_context="这是测试大纲上下文",
            book_dir=self.test_book_dir
        )
        
        # 验证返回值结构
        self.assertIsNotNone(result)
        self.assertIn('backup_dir', result)
        self.assertIn('outline_change_ratio', result)
        self.assertIn('impact_analysis', result)
        self.assertIn('recommendation', result)
        
        # 验证内容不为空
        self.assertIn('major_impact', result['impact_analysis'])
        self.assertIn('minor_impact', result['impact_analysis'])
        self.assertIn('affected_chapters', result['impact_analysis'])
        self.assertIn('suggestions', result['impact_analysis'])
        self.assertIn('analysis', result['impact_analysis'])
        self.assertNotEmpty(result['recommendation'])
        
        print("✅ 测试修改故事大纲通过")
    
    def assertNotEmpty(self, value):
        """断言值不为空"""
        self.assertIsNotNone(value)
        if isinstance(value, str):
            self.assertTrue(len(value.strip()) > 0)

if __name__ == '__main__':
    unittest.main()