import unittest
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.agents.continuity import ContinuityAuditor
from src.llm.provider import llm_client

class TestContinuityAuditor(unittest.TestCase):
    """测试连续性检查器Agent的功能"""
    
    def setUp(self):
        """设置测试环境"""
        self.agent = ContinuityAuditor(llm_client)
    
    def test_check_continuity(self):
        """测试检查连续性"""
        print("\n=== 测试检查连续性 ===")
        
        result = self.agent.check_continuity(
            book_title="测试小说",
            chapter_num=2,
            chapter_content="这是第二章内容，主角继续他的冒险。",
            previous_summary="第一章：主角开始了他的冒险。",
            current_state="主角在森林中"
        )
        
        # 验证返回值结构
        self.assertIsNotNone(result)
        self.assertIn('passed', result)
        self.assertIn('score', result)
        self.assertIn('issues', result)
        self.assertIn('suggestions', result)
        
        # 验证分数范围
        self.assertGreaterEqual(result['score'], 0)
        self.assertLessEqual(result['score'], 100)
        
        print("✅ 测试检查连续性通过")

if __name__ == '__main__':
    unittest.main()