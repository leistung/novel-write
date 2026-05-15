"""OpenAI模型适配器"""
import re
from typing import Dict, List, Optional
from prompts.adapters.base import ModelAdapter, AdapterConfig, FormattedPrompt


class OpenAIAdapter(ModelAdapter):
    """OpenAI GPT模型适配器
    
    支持模型:
    - gpt-4o, gpt-4o-mini
    - gpt-4-turbo
    - gpt-3.5-turbo
    """
    
    # 模型特定参数
    MODEL_CONFIGS = {
        "gpt-4o": {"context_window": 128000, "max_output": 4096},
        "gpt-4o-mini": {"context_window": 128000, "max_output": 4096},
        "gpt-4-turbo": {"context_window": 128000, "max_output": 4096},
        "gpt-4": {"context_window": 8192, "max_output": 4096},
        "gpt-3.5-turbo": {"context_window": 16385, "max_output": 4096},
    }
    
    def __init__(self, config: AdapterConfig):
        super().__init__(config)
        self.model_config = self.MODEL_CONFIGS.get(
            config.model_name, 
            {"context_window": 128000, "max_output": 4096}
        )
    
    def format_prompt(
        self,
        system: Optional[str],
        user: str,
        history: Optional[List[Dict]] = None
    ) -> FormattedPrompt:
        """格式化为OpenAI消息格式"""
        messages = []
        
        # 系统消息
        if system:
            messages.append({
                "role": "system",
                "content": system
            })
        
        # 历史消息
        if history:
            for msg in history:
                messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                })
        
        # 用户消息
        messages.append({
            "role": "user",
            "content": user
        })
        
        return FormattedPrompt(
            messages=messages,
            system=system,
            config=self.config
        )
    
    def get_token_count(self, text: str) -> int:
        """估算OpenAI token数量
        
        使用粗略估算:
        - 英文: ~4字符/token
        - 中文: ~1.5字符/token
        """
        english_chars = len(re.findall(r'[a-zA-Z]', text))
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        other_chars = len(text) - english_chars - chinese_chars
        
        return int(english_chars / 4 + chinese_chars / 1.5 + other_chars / 6)
    
    def supports_system_message(self) -> bool:
        """OpenAI支持system消息"""
        return True
    
    def supports_json_mode(self) -> bool:
        """gpt-4o及更新版本支持JSON模式"""
        return self.config.model_name in [
            "gpt-4o", "gpt-4o-mini", "gpt-4-turbo"
        ]
    
    def optimize_for_model(self, system: str, user: str) -> tuple[str, str]:
        """OpenAI特定优化"""
        # 对于较新模型，可以简化系统提示词
        if self.config.model_name in ["gpt-4o", "gpt-4o-mini"]:
            # 这些模型对指令理解更好，可以适当简化
            system = self._simplify_system_prompt(system)
        
        # 如果启用JSON模式，添加指令
        if self.config.response_format and self.supports_json_mode():
            user = self.add_json_instruction(user)
        
        return system, user
    
    def _simplify_system_prompt(self, system: str) -> str:
        """简化系统提示词（针对新模型）"""
        # 移除冗余的格式说明
        redundant_patterns = [
            r"你必须",
            r"请确保",
            r"重要的是",
        ]
        
        result = system
        for pattern in redundant_patterns:
            result = re.sub(pattern, "", result)
        
        return result.strip()
    
    def get_api_params(self, formatted: FormattedPrompt) -> Dict:
        """获取API调用参数"""
        params = {
            "model": self.config.model_name,
            "messages": formatted.messages,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "top_p": self.config.top_p,
            "frequency_penalty": self.config.frequency_penalty,
            "presence_penalty": self.config.presence_penalty,
        }
        
        if self.config.stop_sequences:
            params["stop"] = self.config.stop_sequences
        
        if self.config.response_format:
            params["response_format"] = self.config.response_format
        
        return params
