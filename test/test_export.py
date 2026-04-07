#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试导出功能
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import init_db, create_book, create_chapter, get_book_chapters


def test_export_functions():
    """测试导出功能"""
    print("开始测试导出功能...")
    
    # 初始化数据库
    init_db()
    print("数据库初始化完成")
    
    # 创建测试书籍
    print("\n1. 创建测试书籍...")
    book_id = create_book(
        title="测试书籍",
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
    
    # 创建测试章节
    print("\n2. 创建测试章节...")
    chapter_id = create_chapter(
        book_id=book_id,
        chapter_num=1,
        title="第1章 山村少年",
        content="# 第1章 山村少年\n\n李小明是一个普通的山村少年，每天过着平凡的生活。直到有一天，他在山上砍柴时，发现了一个神秘的山洞。山洞里有一本古老的书籍，上面记载着修仙的方法。李小明好奇地翻开书籍，突然一道金光从书中射出，进入了他的脑海。从此，李小明的生活发生了翻天覆地的变化。他开始按照书中的方法修炼，逐渐发现自己拥有了特殊的能力。然而，修仙之路并不平坦。李小明很快就遇到了第一个挑战...",
        word_count=500,
        status="已完成",
        summary="李小明发现神秘山洞，获得修仙传承。"
    )
    print(f"章节创建成功，ID: {chapter_id}")
    
    # 测试导出到 txt 文件
    print("\n3. 测试导出到 txt 文件...")
    chapters = get_book_chapters(book_id)
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
        
        # 验证文件是否存在
        if os.path.exists(export_path):
            print("文件导出验证成功")
        else:
            print("文件导出验证失败")
    else:
        print("章节不存在，无法导出")
    
    # 测试导出整本书
    print("\n4. 测试导出整本书...")
    chapters = get_book_chapters(book_id)
    if chapters:
        # 确保 exports 目录存在
        os.makedirs('exports', exist_ok=True)
        
        # 导出整本书
        export_path = f"exports/{'测试书籍'}.txt"
        with open(export_path, 'w', encoding='utf-8') as f:
            f.write(f"# {'测试书籍'}\n\n")
            for chapter in chapters:
                f.write(f"## {chapter['title']}\n\n")
                f.write(chapter['content'])
                f.write("\n\n")
        
        print(f"整本书导出成功，路径: {export_path}")
        
        # 验证文件是否存在
        if os.path.exists(export_path):
            print("整本书导出验证成功")
        else:
            print("整本书导出验证失败")
    else:
        print("章节不存在，无法导出整本书")
    
    print("\n导出功能测试完成！")


if __name__ == "__main__":
    test_export_functions()
