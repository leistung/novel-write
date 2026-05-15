"""Anthropic Claude模型适配器"""
import re
from typing import Dict, List, Optional
from prompts.adapters.base import ModelAdapter, AdapterConfig, FormattedPrompt


class AnthropicAdapter(ModelAdapter):
    """Anthropic Claude模型适配器
    
    支持模型:
    - claude-3-5-sonnet-20241022
    - claude-3-opus-20240229
    - claude-3-sonnet-20240229
    - claude-3-haiku-20240307
    """
    
    MODEL_CONFIGS = {
        "claude-3-5-sonnet-20241022": {
            "context_window": 200000,
            "max_output": 8192,
        },
        "claude-3-opus-20240229": {
            "context_window": 200000,
            "max_output": 4096,
        },
        "claude-3-sonnet-20240229": {
            "context_window": 200000,
            "max_output": 4096,
        },
        "claude-3-haiku-20240307": {
            "context_window": 200000,
            "max_output": 4096,
        },
    }
    
    def __init__(self, config: AdapterConfig):
        super().__init__(config)
        self.model_config = self.MODEL_CONFIGS.get(
            config.model_name,
            {"context_window": 200000, "max_output": 4096}
        )
    
    def format_prompt(
        self,
        system: Optional[str],
        user: str,
        history: Optional[List[Dict]] = None
    ) -> FormattedPrompt:
        """格式化为Claude消息格式
        
        Claude使用分离的system参数和messages数组
        """
        messages = []
        
        # 历史消息
        if history:
            for msg in history:
                role = msg.get("role", "user")
                # Claude只接受 user 和 assistant
                if role == "system":
                    continue
                messages.append({
                    "role": role,
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
        """估算Claude token数量
        
        Claude使用与GPT类似的tokenizer
        """
        english_chars = len(re.findall(r'[a-zA-Z]', text))
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        other_chars = len(text) - english_chars - chinese_chars
        
        return int(english_chars / 4 + chinese_chars / 1.5 + other_chars / 6)
    
    def supports_system_message(self) -> bool:
        """Claude支持system参数（但不在messages中）"""
        return True
    
    def supports_json_mode(self) -> bool:
        """Claude通过提示词实现JSON输出，无原生JSON模式"""
        return False
    
    def optimize_for_model(self, system: str, user: str) -> tuple[str, str]:
        """Claude特定优化"""
        # Claude对XML标签响应良好
        system = self._add_xml_structure(system)
        
        # 添加JSON指令（Claude需要显式指令）
        if "json" in user.lower() or "json" in system.lower():
            user = self._enhance_json_instruction(user)
        
        return system, user
    
    def _add_xml_structure(self, system: str) -> str:
        """添加XML结构帮助Claude理解"""
        # 如果已经有XML结构，不再添加
        if "<instructions>" in system:
            return system
        
        # 包装系统提示词
        structured = f"""<instructions>
{system}
</instructions>

请严格遵循以上指令。"""
        
        return structured
    
    def _enhance_json_instruction(self, user: str) -> str:
        """增强JSON指令（Claude特定）"""
        if "<output_format>" in user:
            return user
        
        enhanced = f"""{user}

<output_format>
请严格按以下要求输出:
1. 只输出有效的JSON格式
2. 不要包含任何解释性文字
3. 确保JSON完整且可解析
4. 使用双引号包裹所有字符串
</output_format>"""
        
        return enhanced
    
    def get_api_params(self, formatted: FormattedPrompt) -> Dict:
        """获取API调用参数"""
        params = {
            "model": self.config.model_name,
            "messages": formatted.messages,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "top_p": self.config.top_p,
        }
        
        # Claude使用顶层system参数
        if formatted.system:
            params["system"] = formatted.system
        
        if self.config.stop_sequences:
            params["stop_sequences"] = self.config.stop_sequences
        
        # 扩展思考模式（仅Claude 3.5 Sonnet支持）
        if self.config.thinking and "claude-3-5-sonnet" in self.config.model_name:
            params["thinking"] = self.config.thinking
        
        return params
    
    def extract_thinking(self, response: Dict) -> Optional[str]:
        """提取思考过程（如果启用thinking模式）"""
        content = response.get("content", [])
        for block in content:
            if block.get("type") == "thinking":
                return block.get("thinking", "")
        return None
