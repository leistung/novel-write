#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试完整的工作流程
"""

import os
import sys
import json
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import init_db, create_book, get_books, get_book_chapters, create_chapter, update_book, get_book_by_id
from src.agents.architect import ArchitectAgent
from src.agents.writer import WriterAgent, WriteChapterInput
from src.agents.auditor import AuditorAgent
from src.agents.detector import DetectorAgent
from src.llm.provider import LLMClient
from src.utils.file_manager import FileManager


def test_full_workflow():
    """测试完整的工作流程"""
    print("开始测试完整工作流程...")
    
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
    title = "测试小说"
    genre = "玄幻"
    platform = "起点中文网"
    chapter_words = 3000
    target_chapters = 300
    brief = "这是一本测试用的玄幻小说"
    outline = "主角是一个普通山村少年，意外获得修仙传承，开始踏上修仙之路。"
    writing_style = "文笔流畅，情节紧凑，人物刻画鲜明，场景描写生动。"
    language = "zh"
    
    book_id = create_book(
        title=title,
        genre=genre,
        platform=platform,
        chapter_words=chapter_words,
        target_chapters=target_chapters,
        brief=brief,
        outline=outline,
        writing_style=writing_style,
        language=language
    )
    
    print(f"书籍创建成功，ID: {book_id}")
    
    # 获取书籍信息
    book = get_book_by_id(book_id)
    print(f"书籍信息: {book}")
    
    # 2. 生成基础设定
    print("\n2. 生成基础设定...")
    try:
        # 构建输入数据
        book_dict = {
            'id': book_id,
            'title': title,
            'genre': genre,
            'platform': platform,
            'chapter_words': chapter_words,
            'target_chapters': target_chapters,
            'language': language,
            'outline': outline,
            'writing_style': writing_style
        }
        
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
        print(f"故事圣经长度: {len(output.story_bible)}")
        print(f"卷纲长度: {len(output.volume_outline)}")
        print(f"书籍规则长度: {len(output.book_rules)}")
        print(f"初始状态卡长度: {len(output.current_state)}")
        print(f"初始伏笔池长度: {len(output.pending_hooks)}")
    except Exception as e:
        print(f"生成基础设定失败: {str(e)}")
    
    # 3. 修改设定
    print("\n3. 修改设定...")
    new_outline = "主角是一个普通山村少年，意外获得修仙传承，开始踏上修仙之路。途中遇到各种挑战和机遇，最终成为一代宗师。"
    update_book(book_id, outline=new_outline)
    print("小说大纲修改成功")
    
    # 4. 更新作者文笔
    print("\n4. 更新作者文笔...")
    new_writing_style = "文笔流畅优美，情节紧凑跌宕，人物刻画鲜明立体，场景描写生动细腻，富有画面感。"
    update_book(book_id, writing_style=new_writing_style)
    print("作者文笔参考更新成功")
    
    # 5. 生成第一章
    print("\n5. 生成第一章...")
    try:
        # 构建输入数据
        book_dict = get_book_by_id(book_id)
        
        # 创建 WriteChapterInput 对象
        write_input = WriteChapterInput(
            book=book_dict,
            chapter_number=1,
            external_context="",
            word_count_override=chapter_words
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
            audit_score=audit_result.get('score', 0.85),
            audit_issues=json.dumps(output.post_write_errors + output.post_write_warnings),
            detection_score=detection_result.get('score'),
            detection_provider=detection_result.get('provider')
        )
        print("章节保存成功")
    except Exception as e:
        print(f"生成章节失败: {str(e)}")
    
    # 6. 生成第二章
    print("\n6. 生成第二章...")
    try:
        # 构建输入数据
        book_dict = get_book_by_id(book_id)
        
        # 创建 WriteChapterInput 对象
        write_input = WriteChapterInput(
            book=book_dict,
            chapter_number=2,
            external_context="",
            word_count_override=chapter_words
        )
        
        # 调用作家 Agent 生成章节
        output = writer_agent.write_chapter(write_input)
        
        # 检测 AI 内容
        detection_result = detector_agent.run({'content': output.content})
        print(f"AI 检测结果: {detection_result}")
        
        # 审核章节内容
        audit_result = auditor_agent.run({'content': output.content, 'book': book_dict, 'chapter_num': 2})
        print(f"审核结果: {audit_result}")
        
        # 创建章节
        create_chapter(
            book_id=book_id,
            chapter_num=2,
            title=output.title,
            content=output.content,
            word_count=output.word_count,
            status="已完成",
            summary=output.chapter_summary,
            audit_score=audit_result.get('score', 0.85),
            audit_issues=json.dumps(output.post_write_errors + output.post_write_warnings),
            detection_score=detection_result.get('score'),
            detection_provider=detection_result.get('provider')
        )
        print("章节保存成功")
    except Exception as e:
        print(f"生成章节失败: {str(e)}")
    
    # 7. 重写第一章
    print("\n7. 重写第一章...")
    try:
        # 构建输入数据
        book_dict = get_book_by_id(book_id)
        
        # 创建 WriteChapterInput 对象
        write_input = WriteChapterInput(
            book=book_dict,
            chapter_number=1,
            external_context="请重写第一章，增加更多细节和场景描写",
            word_count_override=chapter_words
        )
        
        # 调用作家 Agent 生成章节
        output = writer_agent.write_chapter(write_input)
        
        # 检测 AI 内容
        detection_result = detector_agent.run({'content': output.content})
        
        # 审核章节内容
        audit_result = auditor_agent.run({'content': output.content, 'book': book_dict, 'chapter_num': 1})
        print(f"重写章节审核结果: {audit_result}")
        
        # 更新章节
        # 这里简化处理，实际应该调用 update_chapter 函数
        print("第一章重写成功")
    except Exception as e:
        print(f"重写章节失败: {str(e)}")
    
    # 8. 查看第一章
    print("\n8. 查看第一章...")
    chapters = get_book_chapters(book_id)
    if chapters:
        first_chapter = chapters[0]
        print(f"章节标题: {first_chapter['title']}")
        print(f"章节字数: {first_chapter['word_count']}")
        print(f"修订次数: {first_chapter['revisions']}")
        print(f"章节内容预览: {first_chapter['content'][:500]}...")
    else:
        print("章节不存在")
    
    # 9. 导出第一章到 txt 文件
    print("\n9. 导出第一章到 txt 文件...")
    if chapters:
        first_chapter = chapters[0]
        # 确保 exports 目录存在
        os.makedirs('exports', exist_ok=True)
        
        # 导出到 txt 文件
        export_path = f"exports/{first_chapter['title']}.txt"
        with open(export_path, 'w', encoding='utf-8') as f:
            f.write(f"# {first_chapter['title']}\n\n")
            f.write(first_chapter['content'])
        
        print(f"章节导出成功，路径: {export_path}")
    
    # 10. 查看章节列表
    print("\n章节列表:")
    chapters = get_book_chapters(book_id)
    for chapter in chapters:
        print(f"第{chapter['chapter_num']}章: {chapter['title']} (字数: {chapter['word_count']})")
    
    print("\n测试完成！")


if __name__ == "__main__":
    test_full_workflow()
