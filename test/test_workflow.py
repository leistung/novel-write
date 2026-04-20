"""测试工作流功能"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.db.init_db import init_db
from src.workflow.workflow import NovelWriteWorkflow

def test_create_book():
    """测试创建新书"""
    print("=== 测试创建新书 ===")
    
    # 初始化数据库
    init_db()
    print("数据库初始化完成")
    
    # 创建工作流实例
    workflow = NovelWriteWorkflow()
    print("工作流初始化完成")
    
    # 测试数据
    book_data = {
        "title": "测试小说",
        "genre": "玄幻",
        "platform": "起点",
        "chapter_words": 3000,
        "target_chapters": 20,
        "outline": "这是小说大纲",
        "story_bible": "这是故事圣经",
        "volume_outline": "这是卷纲",
        "book_rules": "这是书籍规则"
    }
    
    # 调用创建书籍方法
    result = workflow.create_book(book_data)
    print(f"创建书籍结果类型: {type(result)}")
    print(f"创建书籍结果: {result}")
    
    # 检查是否创建成功
    if isinstance(result, dict):
        # 打印字典的所有键
        print(f"字典键: {list(result.keys())}")
        # 尝试从不同的键中获取book_id
        book_id = result.get('book_id') or result.get('id')
        if book_id:
            print(f"✓ 书籍创建成功，ID: {book_id}")
            return book_id
    
    # 检查是否是数据库对象
    if hasattr(result, 'id'):
        print(f"✓ 书籍创建成功，ID: {result.id}")
        return result.id
    
    # 检查是否是LangGraph的输出结构
    if hasattr(result, 'values'):
        print(f"LangGraph输出值: {result.values()}")
    
    print("✗ 书籍创建失败")
    return None

def test_continue_chapter(book_id):
    """测试续写下一个章节"""
    print(f"\n=== 测试续写下一个章节 (书籍ID: {book_id}) ===")
    
    # 创建工作流实例
    workflow = NovelWriteWorkflow()
    
    # 计算下一章的章节号
    from src.db.crud import get_chapters_by_book
    from src.db.config import get_db
    db = next(get_db())
    chapters = get_chapters_by_book(db, book_id)
    next_chapter = len(chapters) + 1
    print(f"下一章章节号: {next_chapter}")
    
    # 外部指令（可选）
    external_context = "请写一个精彩的章节，展示主角的成长"
    
    # 调用续写下一章方法
    print("开始续写下一章...")
    result = workflow.continue_chapter(book_id, next_chapter, external_context)
    print(f"续写下一章结果: {result}")
    
    # 检查是否续写成功
    if result.get('result', {}).get('chapter_id'):
        print(f"✓ 章节续写成功，ID: {result['result']['chapter_id']}")
        return True
    else:
        print("✗ 章节续写失败")
        return False

if __name__ == "__main__":
    print("开始测试工作流功能...")
    
    # 测试创建新书
    book_id = test_create_book()
    
    if book_id:
        # 测试续写下一个章节
        test_continue_chapter(book_id)
    
    print("\n测试完成！")
