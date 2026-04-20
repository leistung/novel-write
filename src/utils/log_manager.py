import logging
import os
from datetime import datetime
from typing import Optional, Dict, Any


class LogManager:
    """日志管理器"""
    
    def __init__(self, base_dir: str = "logs"):
        self.base_dir = base_dir
        # 如果base_dir为空，使用当前工作目录
        if not base_dir:
            self.log_dir = os.path.join(os.getcwd(), "logs")
        else:
            self.log_dir = base_dir
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
        
        # 控制台handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 格式化
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(console_handler)
    
    def _get_log_file(self, log_type: str) -> str:
        """获取日志文件路径
        
        Args:
            log_type: 日志类型 (agent, workflow)
            
        Returns:
            日志文件路径
        """
        today = datetime.now().strftime("%Y-%m-%d")
        return os.path.join(self.log_dir, f"{log_type}_{today}.log")
    
    def log_agent(self, agent: str, message: str, details: Optional[Dict[str, Any]] = None):
        """记录Agent日志
        
        Args:
            agent: Agent名称
            message: 日志消息
            details: 详细信息
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{agent.upper()}] {message}"
        
        if details:
            for key, value in details.items():
                log_entry += f"\n  {key}: {value}"
        
        log_entry += "\n"
        
        log_file = self._get_log_file("agent")
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
        
        # 控制台输出也包含详细信息
        if details:
            details_str = "".join([f"\n  {key}: {value}" for key, value in details.items()])
            self.logger.info(f"[{agent}] {message}{details_str}")
        else:
            self.logger.info(f"[{agent}] {message}")
    
    def log_workflow(self, workflow: str, message: str, details: Optional[Dict[str, Any]] = None):
        """记录工作流日志
        
        Args:
            workflow: 工作流名称
            message: 日志消息
            details: 详细信息
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{workflow.upper()}] {message}"
        
        if details:
            for key, value in details.items():
                log_entry += f"\n  {key}: {value}"
        
        log_entry += "\n"
        
        log_file = self._get_log_file("workflow")
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
        
        # 控制台输出也包含详细信息
        if details:
            details_str = "".join([f"\n  {key}: {value}" for key, value in details.items()])
            self.logger.info(f"[{workflow}] {message}{details_str}")
        else:
            self.logger.info(f"[{workflow}] {message}")
