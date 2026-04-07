#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试各个Agent的功能
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.llm.provider import LLMClient, LLMConfig
from src.agents.architect import ArchitectAgent
from src.agents.writer import WriterAgent, WriteChapterInput
from src.agents.auditor import AuditorAgent
from src.agents.detector import DetectorAgent
from src.utils.file_manager import FileManager


def test_architect_agent(llm_client):
    """测试架构师Agent"""
    print("\n测试架构师Agent...")
    try:
        architect_agent = ArchitectAgent(llm_client)
        
        # 构建测试数据
        book_dict = {
            'id': 1,
            'title': '测试小说',
            'genre': '玄幻',
            'platform': '起点中文网',
            'chapter_words': 3000,
            'target_chapters': 300,
            'language': 'zh',
            'outline': '主角是一个普通山村少年，意外获得修仙传承，开始踏上修仙之路。',
            'writing_style': '文笔流畅，情节紧凑，人物刻画鲜明，场景描写生动。'
        }
        
        external_context = ""
        
        # 调用架构师Agent生成基础设定
        output = architect_agent.generate_foundation(book_dict, external_context)
        
        print("架构师Agent测试成功！")
        print(f"故事圣经长度: {len(output.story_bible)}")
        print(f"卷纲长度: {len(output.volume_outline)}")
        print(f"书籍规则长度: {len(output.book_rules)}")
        print(f"初始状态卡长度: {len(output.current_state)}")
        print(f"初始伏笔池长度: {len(output.pending_hooks)}")
        return True
    except Exception as e:
        print(f"架构师Agent测试失败: {str(e)}")
        return False


def test_writer_agent(llm_client):
    """测试作家Agent"""
    print("\n测试作家Agent...")
    try:
        writer_agent = WriterAgent(llm_client)
        
        # 构建测试数据
        book_dict = {
            'id': 1,
            'title': '测试小说',
            'genre': '玄幻',
            'platform': '起点中文网',
            'chapter_words': 3000,
            'target_chapters': 300,
            'language': 'zh',
            'outline': '主角是一个普通山村少年，意外获得修仙传承，开始踏上修仙之路。',
            'writing_style': '文笔流畅，情节紧凑，人物刻画鲜明，场景描写生动。'
        }
        
        # 创建WriteChapterInput对象
        write_input = WriteChapterInput(
            book=book_dict,
            chapter_number=1,
            external_context="",
            word_count_override=3000
        )
        
        # 调用作家Agent生成章节
        output = writer_agent.write_chapter(write_input)
        
        print("作家Agent测试成功！")
        print(f"章节标题: {output.title}")
        print(f"章节字数: {output.word_count}")
        print(f"章节内容预览: {output.content[:500]}...")
        return True
    except Exception as e:
        print(f"作家Agent测试失败: {str(e)}")
        return False


def test_auditor_agent(llm_client):
    """测试审计Agent"""
    print("\n测试审计Agent...")
    try:
        auditor_agent = AuditorAgent(llm_client)
        
        # 构建测试数据
        book_dict = {
            'id': 1,
            'title': '测试小说',
            'genre': '玄幻',
            'platform': '起点中文网',
            'chapter_words': 3000,
            'target_chapters': 300,
            'language': 'zh'
        }
        
        # 测试内容
        test_content = "# 第1章 山村少年\n\n李小明是一个普通的山村少年，每天过着平凡的生活。直到有一天，他在山上砍柴时，发现了一个神秘的山洞。山洞里有一本古老的书籍，上面记载着修仙的方法。李小明好奇地翻开书籍，突然一道金光从书中射出，进入了他的脑海。从此，李小明的生活发生了翻天覆地的变化。他开始按照书中的方法修炼，逐渐发现自己拥有了特殊的能力。然而，修仙之路并不平坦。李小明很快就遇到了第一个挑战..."
        
        # 调用审计Agent审核内容
        audit_result = auditor_agent.run({'content': test_content, 'book': book_dict, 'chapter_num': 1})
        
        print("审计Agent测试成功！")
        print(f"审核分数: {audit_result.get('score')}")
        print(f"字数检查: {audit_result.get('word_count_check')}")
        print(f"问题: {audit_result.get('issues', [])}")
        print(f"建议: {audit_result.get('suggestions', [])}")
        return True
    except Exception as e:
        print(f"审计Agent测试失败: {str(e)}")
        return False


def test_detector_agent():
    """测试检测器Agent"""
    print("\n测试检测器Agent...")
    try:
        detector_agent = DetectorAgent()
        
        # 测试内容
        test_content = "# 第1章 山村少年\n\n李小明是一个普通的山村少年，每天过着平凡的生活。直到有一天，他在山上砍柴时，发现了一个神秘的山洞。"
        
        # 调用检测器Agent检测内容
        detection_result = detector_agent.run({'content': test_content})
        
        print("检测器Agent测试成功！")
        print(f"检测结果: {detection_result}")
        return True
    except Exception as e:
        print(f"检测器Agent测试失败: {str(e)}")
        return False


def main():
    """主函数"""
    print("开始测试各个Agent...")
    
    # 初始化LLM客户端
    config = LLMConfig()
    llm_client = LLMClient(config)
    print("LLM客户端初始化完成")
    
    # 测试各个Agent
    test_architect_agent(llm_client)
    test_writer_agent(llm_client)
    test_auditor_agent(llm_client)
    test_detector_agent()
    
    print("\n所有Agent测试完成！")


if __name__ == "__main__":
    main()
