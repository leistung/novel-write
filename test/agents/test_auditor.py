import unittest
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.agents.auditor import AuditorAgent
from src.llm.provider import llm_client

class TestAuditorAgent(unittest.TestCase):
    """测试审核Agent的功能"""
    
    def setUp(self):
        """设置测试环境"""
        self.agent = AuditorAgent(llm_client)
        self.test_book = {
            'id': 1,
            'title': '测试小说',
            'genre': '都市',
            'platform': '起点中文网',
            'chapter_words': 2000,
            'target_chapters': 20,
            'outline': '这是一个测试大纲'
        }
    
    def test_score_chapter(self):
        """测试评分章节"""
        print("\n=== 测试评分章节 ===")
        
        result = self.agent.score_chapter(
            content="这是测试章节内容。主角在城市中漫步，思考着人生的意义。突然，他遇到了一个神秘的陌生人...",
            book=self.test_book,
            chapter_num=1
        )
        
        # 验证返回值结构
        self.assertIsNotNone(result)
        self.assertIn('score', result)
        self.assertIn('breakdown', result)
        self.assertIn('issues', result)
        self.assertIn('suggestions', result)
        
        # 验证分数范围
        self.assertGreaterEqual(result['score'], 0)
        self.assertLessEqual(result['score'], 100)
        
        print("✅ 测试评分章节通过")

if __name__ == '__main__':
    unittest.main()