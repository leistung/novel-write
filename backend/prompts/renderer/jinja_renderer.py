"""Jinja2提示词模板渲染器"""
import re
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Callable
from pathlib import Path

try:
    from jinja2 import Environment, BaseLoader, Template, TemplateError
    JINJA_AVAILABLE = True
except ImportError:
    JINJA_AVAILABLE = False


@dataclass
class RenderContext:
    """渲染上下文"""
    variables: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    history: List[Dict] = field(default_factory=list)
    
    def add_variable(self, name: str, value: Any):
        """添加变量"""
        self.variables[name] = value
    
    def add_history(self, role: str, content: str):
        """添加历史记录"""
        self.history.append({"role": role, "content": content})


class JinjaPromptRenderer:
    """Jinja2提示词渲染器
    
    功能:
    1. 模板变量替换
    2. 条件渲染
    3. 循环渲染
    4. 过滤器链
    5. 宏定义和复用
    """
    
    # 内置过滤器
    BUILTIN_FILTERS = {
        'truncate': lambda s, n: (s[:n-3] + '...') if len(s) > n else s,
        'wordcount': lambda s: len(s.split()),
        'json': lambda o: str(o).replace("'", '"'),
        'upper': str.upper,
        'lower': str.lower,
        'title': str.title,
        'trim': str.strip,
        'indent': lambda s, n=4: '\n'.join(' ' * n + line for line in s.split('\n')),
    }
    
    def __init__(self, enable_jinja: bool = True):
        self.enable_jinja = enable_jinja and JINJA_AVAILABLE
        self._custom_filters: Dict[str, Callable] = {}
        self._template_cache: Dict[str, Any] = {}
        
        if self.enable_jinja:
            self._env = Environment(loader=BaseLoader(), trim_blocks=True, lstrip_blocks=True)
            self._register_builtin_filters()
    
    def _register_builtin_filters(self):
        """注册内置过滤器"""
        for name, func in self.BUILTIN_FILTERS.items():
            self._env.filters[name] = func
    
    def register_filter(self, name: str, func: Callable):
        """注册自定义过滤器"""
        self._custom_filters[name] = func
        if self.enable_jinja:
            self._env.filters[name] = func
    
    def render(
        self,
        template: str,
        context: RenderContext,
        validate_vars: bool = True
    ) -> Dict[str, str]:
        """渲染模板
        
        Args:
            template: 模板内容 {system: ..., user: ...}
            context: 渲染上下文
            validate_vars: 是否验证变量
            
        Returns:
            渲染后的 {system: ..., user: ...}
        """
        result = {}
        
        for key in ['system', 'user']:
            if key in template:
                template_str = template[key]
                
                if self.enable_jinja:
                    rendered = self._render_jinja(template_str, context)
                else:
                    rendered = self._render_simple(template_str, context)
                
                result[key] = rendered
        
        return result
    
    def _render_jinja(self, template_str: str, context: RenderContext) -> str:
        """使用Jinja2渲染"""
        try:
            # 使用缓存
            cache_key = hash(template_str)
            if cache_key not in self._template_cache:
                self._template_cache[cache_key] = self._env.from_string(template_str)
            
            template = self._template_cache[cache_key]
            
            # 合并上下文
            render_ctx = {
                **context.variables,
                '_meta': context.metadata,
                '_history': context.history,
            }
            
            return template.render(**render_ctx)
            
        except TemplateError as e:
            # 回退到简单渲染
            return self._render_simple(template_str, context)
    
    def _render_simple(self, template_str: str, context: RenderContext) -> str:
        """简单变量替换（无Jinja2时回退）"""
        result = template_str
        
        # 替换 {{ variable }}
        pattern = r'\{\{\s*(\w+)\s*\}\}'
        
        def replace_var(match):
            var_name = match.group(1)
            if var_name in context.variables:
                value = context.variables[var_name]
                return str(value)
            return match.group(0)  # 保留原样
        
        result = re.sub(pattern, replace_var, result)
        
        return result
    
    def extract_variables(self, template: str) -> List[str]:
        """提取模板中的变量名"""
        variables = set()
        
        for key in ['system', 'user']:
            if key in template:
                template_str = template[key]
                
                # 匹配 {{ variable }} 和 {% for x in variable %}
                patterns = [
                    r'\{\{\s*(\w+)\s*\}\}',
                    r'\{%\s*for\s+\w+\s+in\s+(\w+)\s*%\}',
                    r'\{%\s*if\s+(\w+)\s*%\}',
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, template_str)
                    variables.update(matches)
        
        return list(variables)
    
    def validate_template(self, template: str) -> tuple[bool, Optional[str]]:
        """验证模板语法"""
        if not self.enable_jinja:
            return True, None
        
        for key in ['system', 'user']:
            if key in template:
                try:
                    self._env.from_string(template[key])
                except TemplateError as e:
                    return False, f"{key} template error: {str(e)}"
        
        return True, None
    
    def estimate_tokens(self, template: str, context: RenderContext) -> int:
        """估算token数量（粗略估计）"""
        rendered = self.render(template, context)
        total_text = ' '.join(rendered.values())
        
        # 粗略估算：英文约4字符/token，中文约1.5字符/token
        english_chars = len(re.findall(r'[a-zA-Z]', total_text))
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', total_text))
        other_chars = len(total_text) - english_chars - chinese_chars
        
        estimated_tokens = (
            english_chars / 4 +
            chinese_chars / 1.5 +
            other_chars / 6
        )
        
        return int(estimated_tokens)
    
    def create_partial(self, name: str, template_str: str):
        """创建可复用的模板片段"""
        if self.enable_jinja:
            self._env.globals[name] = self._env.from_string(template_str)
    
    def clear_cache(self):
        """清除模板缓存"""
        self._template_cache.clear()
