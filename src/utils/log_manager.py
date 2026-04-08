import logging
import os
from datetime import datetime
from typing import Optional, Dict, Any


class LogManager:
    """日志管理器"""
    
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.log_dir = os.path.join(base_dir, "log")
        os.makedirs(self.log_dir, exist_ok=True)
        
        # 配置日志
        self._setup_logger()
        
        # 操作日志文件
        self.operation_log_file = os.path.join(self.log_dir, "operations.log")
        
    def _setup_logger(self):
        """配置日志记录器"""
        self.logger = logging.getLogger("novel-write")
        self.logger.setLevel(logging.DEBUG)
        
        # 避免重复添加handler
        if self.logger.handlers:
            return
        
        # 文件handler - 完整日志
        today = datetime.now().strftime("%Y-%m-%d")
        file_handler = logging.FileHandler(
            os.path.join(self.log_dir, f"novel-write_{today}.log"),
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        
        # 控制台handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 格式化
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def log_operation(self, operation: str, details: Optional[Dict[str, Any]] = None, 
                      status: str = "success"):
        """记录操作日志
        
        Args:
            operation: 操作名称
            details: 操作详情
            status: 操作状态 (success, failed, in_progress)
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{status.upper()}] {operation}"
        
        if details:
            for key, value in details.items():
                log_entry += f"\n  {key}: {value}"
        
        log_entry += "\n"
        
        with open(self.operation_log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
        
        self.logger.info(f"操作记录: {operation} - {status}")
    
    def log_book_creation(self, book_id: int, title: str):
        """记录书籍创建"""
        self.log_operation(
            "创建书籍",
            {"书籍ID": book_id, "标题": title}
        )
    
    def log_chapter_generation(self, book_id: int, chapter_num: int, title: str, word_count: int):
        """记录章节生成"""
        self.log_operation(
            "生成章节",
            {"书籍ID": book_id, "章节": chapter_num, "标题": title, "字数": word_count}
        )
    
    def log_chapter_rewrite(self, book_id: int, chapter_num: int, title: str):
        """记录章节重写"""
        self.log_operation(
            "重写章节",
            {"书籍ID": book_id, "章节": chapter_num, "标题": title}
        )
    
    def log_settings_generation(self, book_id: int, title: str):
        """记录基础设定生成"""
        self.log_operation(
            "生成基础设定",
            {"书籍ID": book_id, "标题": title}
        )
    
    def log_state_update(self, book_id: int, chapter_num: int):
        """记录状态更新"""
        self.log_operation(
            "更新状态文件",
            {"书籍ID": book_id, "章节": chapter_num}
        )
    
    def log_error(self, operation: str, error: Exception, details: Optional[Dict[str, Any]] = None):
        """记录错误"""
        error_details = {"错误": str(error)}
        if details:
            error_details.update(details)
        
        self.log_operation(
            operation,
            error_details,
            status="failed"
        )
        self.logger.error(f"{operation} 失败: {str(error)}")
    
    def get_recent_operations(self, limit: int = 20) -> str:
        """获取最近的操作日志
        
        Args:
            limit: 返回的日志条数
            
        Returns:
            操作日志内容
        """
        if not os.path.exists(self.operation_log_file):
            return "暂无操作记录"
        
        with open(self.operation_log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 返回最近的limit条记录
        if len(lines) > limit * 2:
            lines = lines[-(limit * 2):]
        
        return "".join(lines)
    
    def debug(self, message: str):
        """调试日志"""
        self.logger.debug(message)
    
    def info(self, message: str):
        """信息日志"""
        self.logger.info(message)
    
    def warning(self, message: str):
        """警告日志"""
        self.logger.warning(message)
    
    def error(self, message: str):
        """错误日志"""
        self.logger.error(message)
