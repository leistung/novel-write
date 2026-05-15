"""模型适配器基类"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from enum import Enum


class MessageRole(Enum):
    """消息角色"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class AdapterConfig:
    """适配器配置"""
    model_name: str
    max_tokens: int = 4096
    temperature: float = 0.7
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop_sequences: Optional[List[str]] = None
    
    # 特定模型参数
    response_format: Optional[Dict] = None  # OpenAI JSON mode
    thinking: Optional[Dict] = None  # Claude thinking mode


@dataclass
class FormattedPrompt:
    """格式化后的提示词"""
    messages: List[Dict[str, str]]
    system: Optional[str] = None
    config: Optional[AdapterConfig] = None


class ModelAdapter(ABC):
    """模型适配器基类
    
    统一不同LLM的提示词格式:
    - OpenAI: [{role, content}]
    - Claude: system + messages
    - 其他: 自定义格式
    """
    
    def __init__(self, config: AdapterConfig):
        self.config = config
    
    @abstractmethod
    def format_prompt(
        self,
        system: Optional[str],
        user: str,
        history: Optional[List[Dict]] = None
    ) -> FormattedPrompt:
        """格式化提示词为模型特定格式"""
        pass
    
    @abstractmethod
    def get_token_count(self, text: str) -> int:
        """估算token数量"""
        pass
    
    @abstractmethod
    def supports_system_message(self) -> bool:
        """是否支持system消息"""
        pass
    
    @abstractmethod
    def supports_json_mode(self) -> bool:
        """是否支持JSON模式"""
        pass
    
    def optimize_for_model(self, system: str, user: str) -> tuple[str, str]:
        """针对特定模型优化提示词
        
        例如:
        - 添加模型特定的指令格式
        - 调整token分布
        - 优化系统提示词位置
        """
        return system, user
    
    def add_json_instruction(self, text: str, schema: Optional[Dict] = None) -> str:
        """添加JSON输出指令"""
        instruction = "\n\n请严格按JSON格式输出，不要包含任何其他文本。"
        if schema:
            instruction += f"\n输出应符合以下结构: {schema}"
        return text + instruction
