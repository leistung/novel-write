#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试完整的pipeline
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import init_db, create_book, get_book_by_id, create_chapter
from src.agents.architect import ArchitectAgent
from src.agents.writer import WriterAgent, WriteChapterInput
from src.agents.auditor import AuditorAgent
from src.agents.detector import DetectorAgent
from src.llm.provider import LLMClient
from src.utils.file_manager import FileManager


def test_pipeline():
    """测试完整的pipeline"""
    print("开始测试完整的pipeline...")
    
    # 初始化数据库
    init_db()
    print("数据库初始化完成")
    
    # 初始化 LLM 客户端
    from src.llm.provider import LLMConfig
    config = LLMConfig()
    llm_client = LLMClient(config)
    
    # 初始化 Agent
    architect_agent = ArchitectAgent(llm_client)
    writer_agent = WriterAgent(llm_client)
    auditor_agent = AuditorAgent(llm_client)
    detector_agent = DetectorAgent()
    file_manager = FileManager(base_dir="data")
    
    print("Agent 初始化完成")
    
    # 1. 创建小说
    print("\n1. 创建小说...")
    book_id = create_book(
        title="测试小说",
        genre="玄幻",
        platform="起点中文网",
        chapter_words=3000,
        target_chapters=300,
        brief="这是一本测试用的玄幻小说",
        outline="主角是一个普通山村少年，意外获得修仙传承，开始踏上修仙之路。",
        writing_style="文笔流畅，情节紧凑，人物刻画鲜明，场景描写生动。",
        language="zh"
    )
    print(f"书籍创建成功，ID: {book_id}")
    
    # 2. 生成基础设定
    print("\n2. 生成基础设定...")
    try:
        # 构建输入数据
        book_dict = get_book_by_id(book_id)
        
        external_context = ""
        
        # 调用架构师 Agent 生成基础设定
        output = architect_agent.generate_foundation(book_dict, external_context)
        
        # 保存到文件
        file_manager.save_story_bible(book_id, output.story_bible)
        file_manager.save_volume_outline(book_id, output.volume_outline)
        file_manager.save_book_rules(book_id, output.book_rules)
        file_manager.save_current_state(book_id, output.current_state)
        file_manager.save_pending_hooks(book_id, output.pending_hooks)
        
        print("基础设定生成成功")
    except Exception as e:
        print(f"生成基础设定失败: {str(e)}")
    
    # 3. 生成章节
    print("\n3. 生成章节...")
    try:
        # 构建输入数据
        book_dict = get_book_by_id(book_id)
        
        # 创建 WriteChapterInput 对象
        write_input = WriteChapterInput(
            book=book_dict,
            chapter_number=1,
            external_context="",
            word_count_override=book_dict['chapter_words']
        )
        
        # 调用作家 Agent 生成章节
        output = writer_agent.write_chapter(write_input)
        
        # 检测 AI 内容
        detection_result = detector_agent.run({'content': output.content})
        print(f"AI 检测结果: {detection_result}")
        
        # 审核章节内容
        audit_result = auditor_agent.run({'content': output.content, 'book': book_dict, 'chapter_num': 1})
        print(f"审核结果: {audit_result}")
        
        # 创建章节
        create_chapter(
            book_id=book_id,
            chapter_num=1,
            title=output.title,
            content=output.content,
            word_count=output.word_count,
            status="已完成",
            summary=output.chapter_summary,
            audit_score=audit_result.get('score', 0.85)
        )
        print("章节生成成功")
    except Exception as e:
        print(f"生成章节失败: {str(e)}")
    
    print("\n完整pipeline测试完成！")


if __name__ == "__main__":
    test_pipeline()
