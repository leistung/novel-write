"""Store存储管理器 - 按书分文件夹"""
import json
import aiofiles
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from config.settings import get_settings

settings = get_settings()


class StoreManager:
    """存储管理器"""
    
    def __init__(self):
        self.base_path = settings.STORE_PATH
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def _get_book_path(self, book_id: int) -> Path:
        """获取书籍存储路径"""
        return self.base_path / f"book_{book_id}"
    
    def _ensure_book_dir(self, book_id: int) -> Path:
        """确保书籍目录存在"""
        book_path = self._get_book_path(book_id)
        book_path.mkdir(parents=True, exist_ok=True)
        
        # 创建子目录
        (book_path / "outline").mkdir(exist_ok=True)
        (book_path / "chapters").mkdir(exist_ok=True)
        (book_path / "state").mkdir(exist_ok=True)
        (book_path / "workflow_logs").mkdir(exist_ok=True)
        (book_path / "locks").mkdir(exist_ok=True)
        
        return book_path
    
    async def save_outline_file(
        self,
        book_id: int,
        filename: str,
        content: str
    ) -> Path:
        """保存大纲文件"""
        book_path = self._ensure_book_dir(book_id)
        file_path = book_path / "outline" / filename
        
        async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
            await f.write(content)
        
        return file_path
    
    async def load_outline_file(
        self,
        book_id: int,
        filename: str
    ) -> Optional[str]:
        """加载大纲文件"""
        file_path = self._get_book_path(book_id) / "outline" / filename
        
        if not file_path.exists():
            return None
        
        async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
            return await f.read()
    
    async def save_chapter_file(
        self,
        book_id: int,
        chapter_num: int,
        title: str,
        content: str
    ) -> Path:
        """保存章节文件"""
        book_path = self._ensure_book_dir(book_id)
        file_path = book_path / "chapters" / f"chapter_{chapter_num:03d}.md"
        
        # 添加YAML frontmatter
        file_content = f"""---
chapter_number: {chapter_num}
title: {title}
word_count: {len(content)}
created_at: {datetime.utcnow().isoformat()}
---

{content}
"""
        
        async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
            await f.write(file_content)
        
        return file_path
    
    async def load_chapter_file(
        self,
        book_id: int,
        chapter_num: int
    ) -> Optional[Dict[str, Any]]:
        """加载章节文件"""
        file_path = self._get_book_path(book_id) / "chapters" / f"chapter_{chapter_num:03d}.md"
        
        if not file_path.exists():
            return None
        
        async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
            content = await f.read()
        
        # 解析YAML frontmatter
        import re
        match = re.match(r'^---\n(.*?)\n---\n\n(.*)$', content, re.DOTALL)
        if match:
            # 简单解析frontmatter
            frontmatter = match.group(1)
            body = match.group(2)
            
            return {
                "chapter_number": chapter_num,
                "content": body,
                "frontmatter": frontmatter
            }
        
        return {"chapter_number": chapter_num, "content": content}
    
    async def save_state_file(
        self,
        book_id: int,
        state_type: str,
        content: str
    ) -> Path:
        """保存状态文件"""
        book_path = self._ensure_book_dir(book_id)
        file_path = book_path / "state" / f"{state_type}.md"
        
        async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
            await f.write(content)
        
        return file_path
    
    async def load_state_file(
        self,
        book_id: int,
        state_type: str
    ) -> Optional[str]:
        """加载状态文件"""
        file_path = self._get_book_path(book_id) / "state" / f"{state_type}.md"
        
        if not file_path.exists():
            return None
        
        async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
            return await f.read()
    
    async def create_lock(
        self,
        book_id: int,
        lock_type: str,
        metadata: Dict[str, Any] = None
    ) -> Path:
        """创建锁文件"""
        book_path = self._ensure_book_dir(book_id)
        lock_path = book_path / "locks" / f"{lock_type}.lock"
        
        lock_data = {
            "created_at": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }
        
        async with aiofiles.open(lock_path, "w", encoding="utf-8") as f:
            await f.write(json.dumps(lock_data, ensure_ascii=False, indent=2))
        
        return lock_path
    
    async def remove_lock(self, book_id: int, lock_type: str) -> bool:
        """移除锁文件"""
        lock_path = self._get_book_path(book_id) / "locks" / f"{lock_type}.lock"
        
        if lock_path.exists():
            lock_path.unlink()
            return True
        return False
    
    def check_lock(self, book_id: int, lock_type: str) -> Optional[Dict[str, Any]]:
        """检查锁文件"""
        lock_path = self._get_book_path(book_id) / "locks" / f"{lock_type}.lock"
        
        if not lock_path.exists():
            return None
        
        try:
            with open(lock_path, "r", encoding="utf-8") as f:
                return json.loads(f.read())
        except Exception:
            return None
    
    async def save_workflow_log(
        self,
        book_id: int,
        workflow_id: str,
        log_data: Dict[str, Any]
    ) -> Path:
        """保存工作流日志"""
        book_path = self._ensure_book_dir(book_id)
        log_path = book_path / "workflow_logs" / f"{workflow_id}.json"
        
        async with aiofiles.open(log_path, "w", encoding="utf-8") as f:
            await f.write(json.dumps(log_data, ensure_ascii=False, indent=2))
        
        return log_path
    
    async def load_workflow_log(
        self,
        book_id: int,
        workflow_id: str
    ) -> Optional[Dict[str, Any]]:
        """加载工作流日志"""
        log_path = self._get_book_path(book_id) / "workflow_logs" / f"{workflow_id}.json"
        
        if not log_path.exists():
            return None
        
        async with aiofiles.open(log_path, "r", encoding="utf-8") as f:
            content = await f.read()
            return json.loads(content)
    
    def get_book_structure(self, book_id: int) -> Dict[str, Any]:
        """获取书籍目录结构"""
        book_path = self._get_book_path(book_id)
        
        if not book_path.exists():
            return {"exists": False}
        
        structure = {
            "exists": True,
            "book_id": book_id,
            "path": str(book_path),
            "outline_files": [],
            "chapter_files": [],
            "state_files": [],
            "locks": []
        }
        
        # 扫描大纲文件
        outline_dir = book_path / "outline"
        if outline_dir.exists():
            structure["outline_files"] = [f.name for f in outline_dir.glob("*.md")]
        
        # 扫描章节文件
        chapters_dir = book_path / "chapters"
        if chapters_dir.exists():
            structure["chapter_files"] = sorted([f.name for f in chapters_dir.glob("*.md")])
        
        # 扫描状态文件
        state_dir = book_path / "state"
        if state_dir.exists():
            structure["state_files"] = [f.name for f in state_dir.glob("*.md")]
        
        # 扫描锁文件
        locks_dir = book_path / "locks"
        if locks_dir.exists():
            structure["locks"] = [f.stem for f in locks_dir.glob("*.lock")]
        
        return structure


# 全局存储管理器
store_manager = StoreManager()
