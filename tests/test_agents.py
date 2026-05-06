"""测试脚本 - 验证重构后的 Agent 和工作流"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import unittest
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, Any

# 真实小说测试数据
TEST_BOOK = {
    "title": "斗破苍穹",
    "genre": "玄幻",
    "platform": "起点中文网",
    "target_chapters": 100,
    "chapter_words": 3000,
    "outline": """
一、起源（1-10章）
萧炎是萧家天才少年，四岁修炼斗气，十岁达到九段斗之气，后因药尘吸走斗气沦为废物。
未婚妻纳兰嫣然退婚，萧炎受辱，发誓三年后挑战。药尘现身为师，指导修炼。

二、成长（11-50章）
萧炎在药尘指导下重修，炼药师天赋觉醒。
- 迦南学院内院找到青莲地心火
- 吞噬异火，晋升大斗师
- 云岚宗决战，击败纳兰嫣然
- 炼药师大会夺冠

三、崛起（51-80章）
- 晋升斗王，创建炎盟
- 远赴中州，组建天府联盟
- 魂殿追杀，遭遇多次生死危机

四、称帝（81-100章）
- 晋升斗帝，击败魂天帝
- 统一大陆，拯救陀舍古帝
- 最终与美杜莎、云韵结婚
    """,
    "writing_style": """
文笔特点：
- 战斗描写热血沸腾，层次分明
- 人物心理刻画细腻，代入感强
- 世界观宏大但细节丰富
- 升级体系清晰，节奏把控得当
    """
}

TEST_CHAPTER_PLAN = {
    "chapter_outline": """
本章讲述萧炎在乌坦城的修炼生活。
萧炎每天在萧家后山修炼，发现自己体内的斗气开始缓慢恢复。
药尘出现，指出萧炎的修炼问题，并开始指导他正确修炼。
纳兰嫣然派人前来试探，发现萧炎已经不是废物。
    """,
    "character_states": """
萧炎：
- 状态：斗之气三段，正在恢复
- 心理：隐忍不发，暗中积蓄力量
- 目标：三年后击败纳兰嫣然

药尘：
- 状态：灵魂体，寄居在萧炎体内
- 心理：观察萧炎品性，决定指导他
- 身份：曾经的斗帝强者

纳兰嫣然：
- 状态：云岚宗弟子
- 心理：傲慢，看不起萧炎
    """,
    "setting": """
地点：乌坦城萧家
时间：下午
氛围：修炼、隐忍
    """,
    "plot_points": [
        "萧炎在后山修炼时感受到斗气恢复",
        "药尘被萧炎的毅力打动，主动现身",
        "药尘指出萧炎修炼的问题",
        "纳兰嫣然派人试探萧炎",
        "萧炎展现出不俗实力，震惊来人"
    ]
}

TEST_CHAPTER_CONTENT = """
CHAPTER_TITLE: 第1章 陨落的天才

乌坦城，萧家后山。

午后的阳光透过树叶洒落，在地面上投下斑驳的光影。一个少年正盘腿坐在一块青石上，双目紧闭，呼吸吐纳间有着一定的节奏。

少年便是萧炎，萧家的天才少年。曾经的他，四岁修炼斗气，十岁便达到了九段斗之气的境界，是整个乌坦城最耀眼的新星。

然而，命运却对他开了一个残酷的玩笑。

三年前的那个夜晚，萧炎体内的斗气突然开始疯狂流失，仿佛有什么东西在吞噬他的力量。仅仅一夜之间，他从九段斗之气跌落到了三段，从此沦为了众人眼中的废物。

"唉……"

萧炎缓缓睁开眼睛，看着自己手掌中那淡薄的斗气，眼中闪过一丝苦涩。三年了，他的斗气一直停滞在三段，无论怎么修炼都没有进步。

在萧炎转身的那一刻，他的眼神变得锐利起来。因为只有他自己知道，他的体内正在发生着变化——那些流失的斗气，正在缓缓回归。

而在萧炎体内深处，一道苍老的灵魂正在缓缓苏醒……

"""

TEST_PREVIOUS_CHAPTER = """
第0章 序章

大千世界，无奇不有。

在这片广袤无垠的大陆上，斗气是力量的象征。修炼斗气，可以突破极限，获得超凡的力量。

萧家，乌坦城三大家族之一。

萧炎的出生，曾让整个萧家欣喜若狂。因为萧炎在修炼上展现出了惊人的天赋，四岁开始修炼斗气，十岁便达到了九段斗之气的境界。

然而，命运弄人……

"""


def create_mock_response(content: str):
    """创建模拟 LLM 响应"""
    mock_response = Mock()
    mock_response.content = content
    mock_response.usage_metadata = {"prompt_tokens": 100, "completion_tokens": 50}
    return mock_response


class TestSkillLoader(unittest.TestCase):
    """测试技能加载器"""

    def test_skill_loader_initialization(self):
        """测试技能加载器初始化"""
        from src.skills.loader import SkillLoader, get_skill_loader

        loader = SkillLoader()
        self.assertIsInstance(loader, SkillLoader)

        loader2 = get_skill_loader()
        self.assertIs(loader2, get_skill_loader())

    def test_list_skills_and_genres(self):
        """测试列出技能和题材"""
        from src.skills.loader import get_skill_loader

        loader = get_skill_loader()
        skills = loader.list_skills()
        genres = loader.list_genres()

        self.assertIsInstance(skills, list)
        self.assertIsInstance(genres, list)

    def test_generate_prompt_enhancement(self):
        """测试生成提示词增强"""
        from src.skills.loader import get_skill_loader

        loader = get_skill_loader()

        enhancement = loader.generate_prompt_enhancement("玄幻")
        self.assertIsInstance(enhancement, str)


class TestBaseAgent(unittest.TestCase):
    """测试基础 Agent"""

    def test_agent_context(self):
        """测试 AgentContext"""
        from src.agents.base import AgentContext

        context = AgentContext(chapter_num=1, book=TEST_BOOK)

        self.assertEqual(context.chapter_num, 1)
        self.assertEqual(context.get('book')['title'], "斗破苍穹")
        self.assertEqual(context.get('book')['genre'], "玄幻")


class TestArchitectAgent(unittest.TestCase):
    """测试架构师 Agent"""

    def test_architect_initialization(self):
        """测试架构师实例化"""
        from src.agents.architect import ArchitectAgent

        mock_llm = Mock()
        agent = ArchitectAgent(mock_llm)
        self.assertIsInstance(agent, ArchitectAgent)

    def test_plan_chapter_returns_correct_structure(self):
        """测试章节规划返回正确结构"""
        from src.agents.architect import ArchitectAgent

        mock_llm = Mock()
        mock_response = create_mock_response("""=== SECTION: story_bible ===
# 故事圣经
这是一个讲述废物逆袭的玄幻故事。

=== SECTION: volume_outline ===
# 卷纲
萧炎在药尘指导下重修，最终击败纳兰嫣然。

=== SECTION: book_rules ===
# 书籍规则
- 主角不得轻易死亡

=== SECTION: current_state ===
# 当前状态
萧炎：斗之气三段

=== SECTION: pending_hooks ===
# 伏笔池
- 药尘的身份
        """)

        with patch.object(ArchitectAgent, 'run_chain', return_value={'content': mock_response.content}):
            agent = ArchitectAgent(mock_llm)
            result = agent.plan_chapter(
                TEST_BOOK, 1, "萧炎：斗之气三段", "上一章讲述萧家的背景"
            )

            self.assertTrue(hasattr(result, 'chapter_outline'))
            self.assertTrue(hasattr(result, 'character_states'))
            self.assertTrue(hasattr(result, 'setting'))
            self.assertTrue(hasattr(result, 'plot_points'))

    def test_execute_plan_chapter(self):
        """测试执行章节规划任务"""
        from src.agents.architect import ArchitectAgent
        from src.agents.base import AgentContext

        mock_llm = Mock()
        mock_response = create_mock_response("""=== SECTION: story_bible ===
# 故事圣经
测试

=== SECTION: volume_outline ===
# 卷纲
测试

=== SECTION: book_rules ===
# 书籍规则

=== SECTION: current_state ===
# 当前状态

=== SECTION: pending_hooks ===
# 伏笔池
        """)

        with patch.object(ArchitectAgent, 'run_chain', return_value={'content': mock_response.content}):
            agent = ArchitectAgent(mock_llm)

            context = AgentContext(
                chapter_num=1,
                task_type='plan_chapter',
                book=TEST_BOOK,
                current_state="萧炎：斗之气三段",
                previous_chapter_summary="上一章讲述萧家的背景"
            )

            result = agent.execute(context)

            self.assertIsInstance(result, dict)
            self.assertIn('chapter_outline', result)


class TestWriterAgent(unittest.TestCase):
    """测试写手 Agent"""

    def test_writer_initialization(self):
        """测试写手实例化"""
        from src.agents.writer import WriterAgent

        mock_llm = Mock()
        agent = WriterAgent(mock_llm)
        self.assertIsInstance(agent, WriterAgent)

    def test_validate_chapter_outline(self):
        """测试大纲验证"""
        from src.agents.writer import WriterAgent

        mock_llm = Mock()
        mock_response = create_mock_response("大纲合理，可以继续写作。")

        with patch.object(WriterAgent, 'run_chain', return_value={'content': mock_response.content}):
            agent = WriterAgent(mock_llm)

            result = agent.validate_chapter_outline(
                TEST_CHAPTER_PLAN["chapter_outline"],
                TEST_BOOK
            )

            self.assertIsInstance(result, dict)
            self.assertIn('is_valid', result)
            self.assertIn('suggestions', result)

    def test_execute_write_chapter(self):
        """测试执行写章节任务"""
        from src.agents.writer import WriterAgent
        from src.agents.base import AgentContext

        mock_llm = Mock()

        mock_write_response = create_mock_response("""PRE_WRITE_CHECK: 本章符合卷纲要求，字数3000字

CHAPTER_TITLE: 第1章 陨落的天才

CHAPTER_CONTENT:
这是测试章节内容，萧炎在后山修炼，感受到斗气开始恢复。药尘出现，决定指导他修炼。
    """)

        def mock_run_chain(prompt, **kwargs):
            return {'content': mock_write_response.content}

        with patch.object(WriterAgent, 'run_chain', side_effect=mock_run_chain):
            agent = WriterAgent(mock_llm)

            context = AgentContext(
                chapter_num=1,
                task_type='write_chapter',
                book=TEST_BOOK,
                chapter_plan=TEST_CHAPTER_PLAN
            )

            result = agent.execute(context)

            self.assertIsInstance(result, dict)
            self.assertIn('content', result)
            self.assertIn('summary', result)
            self.assertIn('title', result)


class TestContinuityAuditor(unittest.TestCase):
    """测试连续性审核 Agent"""

    def test_auditor_initialization(self):
        """测试连续性审核实例化"""
        from src.agents.continuity_auditor import ContinuityAuditor

        mock_llm = Mock()
        agent = ContinuityAuditor(mock_llm)
        self.assertIsInstance(agent, ContinuityAuditor)

    def test_check_chapter_consistency(self):
        """测试章节连续性检查"""
        from src.agents.continuity_auditor import ContinuityAuditor

        mock_llm = Mock()
        mock_response = create_mock_response("""分数：85

## 检查报告
连续性检查通过，没有发现明显问题。

## 建议
可以继续下一阶段。
""")

        with patch.object(ContinuityAuditor, 'run_chain', return_value={'content': mock_response.content}):
            agent = ContinuityAuditor(mock_llm)

            result = agent.check_chapter_consistency(
                TEST_BOOK, 1,
                TEST_CHAPTER_CONTENT,
                TEST_PREVIOUS_CHAPTER
            )

            self.assertIsNotNone(result)
            self.assertTrue(hasattr(result, 'is_consistent'))
            self.assertTrue(hasattr(result, 'score'))
            self.assertTrue(hasattr(result, 'suggestions'))

    def test_execute_check_consistency(self):
        """测试执行连续性检查任务"""
        from src.agents.continuity_auditor import ContinuityAuditor
        from src.agents.base import AgentContext

        mock_llm = Mock()
        mock_response = create_mock_response("""分数：85

## 检查报告
连续性检查通过，没有发现明显问题。

## 建议
可以继续下一阶段。
""")

        with patch.object(ContinuityAuditor, 'run_chain', return_value={'content': mock_response.content}):
            agent = ContinuityAuditor(mock_llm)

            context = AgentContext(
                chapter_num=1,
                task_type='check_chapter_consistency',
                book=TEST_BOOK,
                chapter_content=TEST_CHAPTER_CONTENT,
                previous_chapter=TEST_PREVIOUS_CHAPTER
            )

            result = agent.execute(context)

            self.assertIsInstance(result, dict)
            self.assertIn('is_consistent', result)
            self.assertIn('score', result)


class TestAuditorAgent(unittest.TestCase):
    """测试评分审核 Agent"""

    def test_auditor_initialization(self):
        """测试评分审核实例化"""
        from src.agents.auditor import AuditorAgent

        mock_llm = Mock()
        agent = AuditorAgent(mock_llm)
        self.assertIsInstance(agent, AuditorAgent)

    def test_score_chapter(self):
        """测试章节评分"""
        from src.agents.auditor import AuditorAgent

        mock_llm = Mock()
        mock_response = create_mock_response("""总分：82

情节一致性：80
文本一致性：85
人物表现：82
文笔质量：80

## 评语
本章情节推进自然，人物性格鲜明。

## 建议
可以继续写作。
""")

        with patch.object(AuditorAgent, 'run_chain', return_value={'content': mock_response.content}):
            agent = AuditorAgent(mock_llm)

            result = agent.score_chapter(
                TEST_BOOK, 1,
                TEST_CHAPTER_CONTENT,
                "第0章讲述萧家的背景和萧炎曾经的天赋"
            )

            self.assertIsNotNone(result)
            self.assertTrue(hasattr(result, 'score'))
            self.assertTrue(hasattr(result, 'detailed_scores'))
            self.assertTrue(hasattr(result, 'passed'))

    def test_execute_score_chapter(self):
        """测试执行评分任务"""
        from src.agents.auditor import AuditorAgent
        from src.agents.base import AgentContext

        mock_llm = Mock()
        mock_response = create_mock_response("""总分：82

情节一致性：80
文本一致性：85
人物表现：82
文笔质量：80

## 评语
本章情节推进自然，人物性格鲜明。

## 建议
可以继续写作。
""")

        with patch.object(AuditorAgent, 'run_chain', return_value={'content': mock_response.content}):
            agent = AuditorAgent(mock_llm)

            context = AgentContext(
                chapter_num=1,
                task_type='score_chapter',
                book=TEST_BOOK,
                chapter_content=TEST_CHAPTER_CONTENT,
                chapter_summary="第0章讲述萧家的背景和萧炎曾经的天赋"
            )

            result = agent.execute(context)

            self.assertIsInstance(result, dict)
            self.assertIn('score', result)
            self.assertIn('passed', result)


class TestWorkflowIntegration(unittest.TestCase):
    """测试工作流集成"""

    def test_all_agents_available(self):
        """测试所有 Agent 都能正常导入"""
        from src.agents import (
            BaseAgent,
            AgentContext,
            ArchitectAgent,
            WriterAgent,
            ContinuityAuditor,
            AuditorAgent
        )

        self.assertTrue(callable(ArchitectAgent))
        self.assertTrue(callable(WriterAgent))
        self.assertTrue(callable(ContinuityAuditor))
        self.assertTrue(callable(AuditorAgent))

    def test_skill_loader_integration(self):
        """测试技能加载器集成"""
        from src.skills.loader import get_skill_loader

        loader = get_skill_loader()
        self.assertTrue(hasattr(loader, 'generate_prompt_enhancement'))

    def test_genre_enhancement_in_all_agents(self):
        """测试所有 Agent 都能获取题材增强"""
        mock_llm = Mock()

        from src.agents.architect import ArchitectAgent
        from src.agents.writer import WriterAgent
        from src.agents.continuity_auditor import ContinuityAuditor
        from src.agents.auditor import AuditorAgent

        architect = ArchitectAgent(mock_llm)
        writer = WriterAgent(mock_llm)
        continuity = ContinuityAuditor(mock_llm)
        auditor = AuditorAgent(mock_llm)

        self.assertTrue(hasattr(architect, 'get_genre_enhancement'))
        self.assertTrue(hasattr(writer, 'get_genre_enhancement'))
        self.assertTrue(hasattr(continuity, 'get_genre_enhancement'))
        self.assertTrue(hasattr(auditor, 'get_genre_enhancement'))

        result = architect.get_genre_enhancement("玄幻")
        self.assertIsInstance(result, str)


def run_tests():
    """运行所有测试"""
    print("=" * 60)
    print("《斗破苍穹》- Agent 和工作流测试")
    print("=" * 60)
    print()

    suite = unittest.TestSuite()

    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestSkillLoader))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestBaseAgent))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestArchitectAgent))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestWriterAgent))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestContinuityAuditor))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestAuditorAgent))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestWorkflowIntegration))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print()
    print("=" * 60)
    print(f"测试完成: {result.testsRun} 个测试")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    print("=" * 60)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)