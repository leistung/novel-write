import os
import json
from typing import Dict, Any, Optional

class FileManager:
    """文件管理工具类"""

    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        # 确保基础目录存在
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

    def save_chapter_summaries(self, book_id: int, content: str) -> str:
        """保存章节摘要"""
        file_path = os.path.join(self.get_book_dir(book_id), "chapter_summaries.md")
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

    def save_particle_ledger(self, book_id: int, content: str) -> str:
        """保存粒子账本"""
        file_path = os.path.join(self.get_book_dir(book_id), "particle_ledger.md")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return file_path

    def save_chapter_content(self, book_id: int, chapter_number: int, content: str) -> str:
        """保存章节内容"""
        file_path = os.path.join(self.get_chapter_dir(book_id, chapter_number), "content.md")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return file_path

    def save_chapter_metadata(self, book_id: int, chapter_number: int, metadata: Dict[str, Any]) -> str:
        """保存章节元数据"""
        file_path = os.path.join(self.get_chapter_dir(book_id, chapter_number), "metadata.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        return file_path

    def load_story_bible(self, book_id: int) -> Optional[str]:
        """加载故事圣经"""
        file_path = os.path.join(self.get_book_dir(book_id), "story_bible.md")
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        return None

    def load_volume_outline(self, book_id: int) -> Optional[str]:
        """加载卷纲"""
        file_path = os.path.join(self.get_book_dir(book_id), "volume_outline.md")
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        return None

    def load_book_rules(self, book_id: int) -> Optional[str]:
        """加载书籍规则"""
        file_path = os.path.join(self.get_book_dir(book_id), "book_rules.md")
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        return None

    def load_current_state(self, book_id: int) -> Optional[str]:
        """加载当前状态卡"""
        file_path = os.path.join(self.get_book_dir(book_id), "current_state.md")
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        return None

    def load_pending_hooks(self, book_id: int) -> Optional[str]:
        """加载伏笔池"""
        file_path = os.path.join(self.get_book_dir(book_id), "pending_hooks.md")
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        return None

    def load_chapter_summaries(self, book_id: int) -> Optional[str]:
        """加载章节摘要"""
        file_path = os.path.join(self.get_book_dir(book_id), "chapter_summaries.md")
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        return None

    def load_subplot_board(self, book_id: int) -> Optional[str]:
        """加载支线进度板"""
        file_path = os.path.join(self.get_book_dir(book_id), "subplot_board.md")
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        return None

    def load_emotional_arcs(self, book_id: int) -> Optional[str]:
        """加载情感弧线"""
        file_path = os.path.join(self.get_book_dir(book_id), "emotional_arcs.md")
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        return None

    def load_character_matrix(self, book_id: int) -> Optional[str]:
        """加载角色交互矩阵"""
        file_path = os.path.join(self.get_book_dir(book_id), "character_matrix.md")
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        return None

    def load_particle_ledger(self, book_id: int) -> Optional[str]:
        """加载粒子账本"""
        file_path = os.path.join(self.get_book_dir(book_id), "particle_ledger.md")
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        return None

    def load_chapter_content(self, book_id: int, chapter_number: int) -> Optional[str]:
        """加载章节内容"""
        file_path = os.path.join(self.get_chapter_dir(book_id, chapter_number), "content.md")
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        return None

    def load_chapter_metadata(self, book_id: int, chapter_number: int) -> Optional[Dict[str, Any]]:
        """加载章节元数据"""
        file_path = os.path.join(self.get_chapter_dir(book_id, chapter_number), "metadata.json")
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None

    def delete_book_files(self, book_id: int) -> bool:
        """删除书籍相关文件"""
        import shutil
        book_dir = self.get_book_dir(book_id)
        if os.path.exists(book_dir):
            shutil.rmtree(book_dir)
            return True
        return False

    def delete_chapter_files(self, book_id: int, chapter_number: int) -> bool:
        """删除章节相关文件"""
        import shutil
        chapter_dir = self.get_chapter_dir(book_id, chapter_number)
        if os.path.exists(chapter_dir):
            shutil.rmtree(chapter_dir)
            return True
        return False
