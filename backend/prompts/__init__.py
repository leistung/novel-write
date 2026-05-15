"""提示词工程模块 - 企业级提示词管理

完整功能清单:
1. Prompt Registry - 提示词注册中心
2. Security Sanitizer - 输入净化和安全防护
3. Output Validation - 输出验证和JSON Schema
4. Jinja Renderer - Jinja2模板渲染
5. Model Adapters - OpenAI/Claude模型适配
6. Cache Optimization - 缓存和Token优化
7. BaseAgent - 企业级Agent基类

使用示例:
    from prompts import get_registry, PromptSanitizer, BaseAgentV2
    
    # 加载提示词
    registry = get_registry()
    registry.load_directory(Path("./templates"))
    
    # 创建Agent
    agent = MyAgent(prompt_name="architect/foundation")
    result = await agent.execute(genre="科幻", theme="AI")
"""
from prompts.registry.manager import PromptRegistry, PromptVersion, PromptMetadata
from prompts.security.sanitizer import PromptSanitizer, SanitizationResult, RiskLevel
from prompts.schemas.validation import OutputValidator, ValidationResult
from prompts.schemas.novel_schemas import (
    FoundationOutput,
    ChapterOutlineOutput,
    AuditResultOutput,
    RewriteOutput,
    StyleAnalysisOutput,
)
from prompts.renderer.jinja_renderer import JinjaPromptRenderer, RenderContext
from prompts.adapters.base import ModelAdapter, AdapterConfig
from prompts.adapters.openai_adapter import OpenAIAdapter
from prompts.adapters.anthropic_adapter import AnthropicAdapter
from prompts.optimization.cache import PromptCache, CacheConfig
from prompts.optimization.token_optimizer import TokenOptimizer, TokenStats
from prompts.agent.base import BaseAgentV2, AgentConfig, AgentResult

__version__ = "2.0.0"

__all__ = [
    # Registry
    "PromptRegistry",
    "PromptVersion",
    "PromptMetadata",
    # Security
    "PromptSanitizer",
    "SanitizationResult",
    "RiskLevel",
    # Validation
    "OutputValidator",
    "ValidationResult",
    # Schemas
    "FoundationOutput",
    "ChapterOutlineOutput",
    "AuditResultOutput",
    "RewriteOutput",
    "StyleAnalysisOutput",
    # Renderer
    "JinjaPromptRenderer",
    "RenderContext",
    # Adapters
    "ModelAdapter",
    "AdapterConfig",
    "OpenAIAdapter",
    "AnthropicAdapter",
    # Optimization
    "PromptCache",
    "CacheConfig",
    "TokenOptimizer",
    "TokenStats",
    # Agent
    "BaseAgentV2",
    "AgentConfig",
    "AgentResult",
]

# 全局注册中心实例
_registry = None


def get_registry() -> PromptRegistry:
    """获取全局提示词注册中心"""
    global _registry
    if _registry is None:
        _registry = PromptRegistry()
    return _registry


def init_registry(templates_dir: str = "./templates") -> PromptRegistry:
    """初始化注册中心并加载模板
    
    Args:
        templates_dir: YAML模板目录路径
        
    Returns:
        初始化后的注册中心
    """
    from pathlib import Path
    
    registry = get_registry()
    templates_path = Path(templates_dir)
    
    if templates_path.exists():
        count = registry.load_directory(templates_path)
        print(f"Loaded {count} prompts from {templates_dir}")
    
    return registry
