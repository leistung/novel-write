"""日志管理器"""
import logging
import os
from datetime import datetime
from typing import Optional, Dict, Any

class LogManager:
    """日志管理器"""
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, base_dir: str = None):
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        if base_dir is None:
            base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")
        
        self.base_dir = base_dir
        self.log_dir = base_dir
        os.makedirs(self.log_dir, exist_ok=True)
        
        self._setup_logger()
        self._initialized = True
    
    def _setup_logger(self):
        """配置日志记录器"""
        self.logger = logging.getLogger("novel-write")
        self.logger.setLevel(logging.DEBUG)
        
        if self.logger.handlers:
            return
        
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(console_handler)
    
    def _get_log_file(self, log_type: str) -> str:
        """获取日志文件路径"""
        today = datetime.now().strftime("%Y-%m-%d")
        return os.path.join(self.log_dir, f"{log_type}_{today}.log")
    
    def log_agent(self, agent: str, message: str, details: Optional[Dict[str, Any]] = None):
        """记录Agent日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{agent.upper()}] {message}"
        
        if details:
            for key, value in details.items():
                log_entry += f"\n  {key}: {value}"
        
        log_entry += "\n"
        
        log_file = self._get_log_file("agent")
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
        
        if details:
            details_str = "".join([f"\n  {key}: {value}" for key, value in details.items()])
            self.logger.info(f"[{agent}] {message}{details_str}")
        else:
            self.logger.info(f"[{agent}] {message}")
    
    def log_workflow(self, workflow: str, message: str, details: Optional[Dict[str, Any]] = None):
        """记录工作流日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{workflow.upper()}] {message}"
        
        if details:
            for key, value in details.items():
                log_entry += f"\n  {key}: {value}"
        
        log_entry += "\n"
        
        log_file = self._get_log_file("workflow")
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
        
        if details:
            details_str = "".join([f"\n  {key}: {value}" for key, value in details.items()])
            self.logger.info(f"[{workflow}] {message}{details_str}")
        else:
            self.logger.info(f"[{workflow}] {message}")
    
    def log_operation(self, operation: str, message: str, details: Optional[Dict[str, Any]] = None):
        """记录操作日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{operation.upper()}] {message}"
        
        if details:
            for key, value in details.items():
                log_entry += f"\n  {key}: {value}"
        
        log_entry += "\n"
        
        log_file = self._get_log_file("operation")
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
        
        self.logger.info(f"[{operation}] {message}")
    
    def get_recent_logs(self, log_type: str = "agent", limit: int = 100) -> str:
        """获取最近的日志"""
        log_file = self._get_log_file(log_type)
        
        if not os.path.exists(log_file):
            return ""
        
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            return "".join(lines[-limit:])