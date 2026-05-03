import os
from typing import Dict, Any, Optional

class FileManager:
    """文件管理工具类"""

    def __init__(self, base_dir: str = None):
        if base_dir is None:
            base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
        self.base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)

    def get_book_dir(self, book_id: int) -> str:
        """获取书籍目录"""
        book_dir = os.path.join(self.base_dir, f"book_{book_id}")
        os.makedirs(book_dir, exist_ok=True)
        return book_dir

    def get_chapter_dir(self, book_id: int, chapter_number: int) -> str:
        """获取章节目录"""
        chapter_dir = os.path.join(self.get_book_dir(book_id), f"chapter_{chapter_number}")
        os.makedirs(chapter_dir, exist_ok=True)
        return chapter_dir

    def save_story_bible(self, book_id: int, content: str) -> str:
        """保存故事圣经"""
        file_path = os.path.join(self.get_book_dir(book_id), "story_bible.md")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return file_path

    def save_volume_outline(self, book_id: int, content: str) -> str:
        """保存卷纲"""
        file_path = os.path.join(self.get_book_dir(book_id), "volume_outline.md")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return file_path

    def save_book_rules(self, book_id: int, content: str) -> str:
        """保存书籍规则"""
        file_path = os.path.join(self.get_book_dir(book_id), "book_rules.md")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return file_path

    def save_current_state(self, book_id: int, content: str) -> str:
        """保存当前状态卡"""
        file_path = os.path.join(self.get_book_dir(book_id), "current_state.md")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return file_path

    def save_pending_hooks(self, book_id: int, content: str) -> str:
        """保存伏笔池"""
        file_path = os.path.join(self.get_book_dir(book_id), "pending_hooks.md")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return file_path

    def save_subplot_board(self, book_id: int, content: str) -> str:
        """保存支线进度板"""
        file_path = os.path.join(self.get_book_dir(book_id), "subplot_board.md")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return file_path

    def save_emotional_arcs(self, book_id: int, content: str) -> str:
        """保存情感弧线"""
        file_path = os.path.join(self.get_book_dir(book_id), "emotional_arcs.md")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return file_path

    def save_character_matrix(self, book_id: int, content: str) -> str:
        """保存角色交互矩阵"""
        file_path = os.path.join(self.get_book_dir(book_id), "character_matrix.md")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return file_path

    def save_chapter_content(self, book_id: int, chapter_number: int, content: str) -> str:
        """保存章节内容"""
        file_path = os.path.join(self.get_chapter_dir(book_id, chapter_number), "content.md")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return file_path
