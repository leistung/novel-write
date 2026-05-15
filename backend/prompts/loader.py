"""提示词加载器 - 简化 prompts 的使用

使用示例:
    from prompts.loader import render_prompt
    
    # 渲染提示词
    system_prompt, user_prompt = render_prompt("architect/foundation", {
        "genre": "玄幻",
        "theme": "修仙"
    })
"""
import os
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

from prompts.registry.manager import PromptRegistry
from prompts.renderer.jinja_renderer import JinjaPromptRenderer, RenderContext

# 全局注册中心
_registry: Optional[PromptRegistry] = None
_renderer: Optional[JinjaPromptRenderer] = None


def get_registry() -> PromptRegistry:
    """获取全局提示词注册中心"""
    global _registry
    if _registry is None:
        _registry = PromptRegistry()
        # 自动加载 templates 目录
        templates_dir = Path(__file__).parent / "templates"
        if templates_dir.exists():
            count = _registry.load_directory(templates_dir)
            print(f"[Prompts] 已加载 {count} 个提示词模板")
    return _registry


def get_renderer() -> JinjaPromptRenderer:
    """获取全局模板渲染器"""
    global _renderer
    if _renderer is None:
        _renderer = JinjaPromptRenderer()
    return _renderer


def render_prompt(name: str, variables: Dict[str, Any], version: Optional[str] = None) -> Tuple[str, str]:
    """
    渲染提示词模板
    
    Args:
        name: 提示词名称（如 architect/foundation）
        variables: 模板变量
        version: 版本号（默认使用激活版本）
    
    Returns:
        (system_prompt, user_prompt)
    
    Raises:
        ValueError: 提示词不存在
    """
    registry = get_registry()
    renderer = get_renderer()
    
    # 获取提示词版本
    prompt_version = registry.get(name, version)
    if not prompt_version:
        raise ValueError(f"提示词不存在: {name}")
    
    # 渲染模板
    context = RenderContext(variables=variables)
    rendered = renderer.render(prompt_version.content, context)
    
    system_prompt = rendered.get("system", "")
    user_prompt = rendered.get("user", "")
    
    return system_prompt, user_prompt


def get_prompt_content(name: str, version: Optional[str] = None) -> Dict[str, str]:
    """
    获取原始提示词内容（不渲染）
    
    Args:
        name: 提示词名称
        version: 版本号
    
    Returns:
        {"system": ..., "user": ...}
    """
    registry = get_registry()
    prompt_version = registry.get(name, version)
    if not prompt_version:
        raise ValueError(f"提示词不存在: {name}")
    
    return prompt_version.content


def list_prompts(tag: Optional[str] = None) -> list:
    """列出所有可用的提示词"""
    registry = get_registry()
    return registry.list_prompts(tag)


# 便捷函数：预加载所有模板
def init_prompts():
    """初始化并预加载所有提示词模板"""
    registry = get_registry()
    return registry
