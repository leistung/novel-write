"""模型适配模块"""
from prompts.adapters.base import ModelAdapter, AdapterConfig
from prompts.adapters.openai_adapter import OpenAIAdapter
from prompts.adapters.anthropic_adapter import AnthropicAdapter

__all__ = [
    "ModelAdapter",
    "AdapterConfig",
    "OpenAIAdapter",
    "AnthropicAdapter",
]
