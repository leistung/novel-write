"""BaseAgent V2 - 企业级Agent基类

整合所有提示词工程最佳实践:
- Prompt Registry
- 输入净化
- 输出验证
- 模板渲染
- 模型适配
- 缓存优化
"""
import time
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Type, Callable
from datetime import datetime

from prompts.registry.manager import PromptRegistry
from prompts.security.sanitizer import PromptSanitizer, RiskLevel
from prompts.schemas.validation import OutputValidator, ValidationResult
from prompts.renderer.jinja_renderer import JinjaPromptRenderer, RenderContext
from prompts.adapters.base import ModelAdapter, AdapterConfig
from prompts.adapters.openai_adapter import OpenAIAdapter
from prompts.adapters.anthropic_adapter import AnthropicAdapter
from prompts.optimization.cache import PromptCache, CacheConfig
from prompts.optimization.token_optimizer import TokenOptimizer


@dataclass
class AgentConfig:
    """Agent配置"""
    # 模型配置
    model_name: str = "gpt-4o"
    temperature: float = 0.7
    max_tokens: int = 4096
    
    # 功能开关
    enable_sanitization: bool = True
    enable_validation: bool = True
    enable_caching: bool = True
    enable_token_optimization: bool = False
    
    # 安全设置
    strict_mode: bool = False  # 严格模式：拒绝任何可疑输入
    max_input_length: int = 10000
    
    # 缓存配置
    cache_ttl: int = 3600
    
    # 重试配置
    max_retries: int = 3
    retry_delay: float = 1.0


@dataclass
class AgentResult:
    """Agent执行结果"""
    success: bool
    data: Optional[Any]
    raw_response: Optional[str]
    
    # 元数据
    prompt_name: str
    version: str
    model: str
    
    # 性能指标
    latency_ms: float
    tokens_used: Optional[int]
    
    # 处理信息
    sanitized: bool
    validation_passed: bool
    cache_hit: bool
    
    # 错误信息
    error: Optional[str] = None
    validation_errors: List[str] = field(default_factory=list)
    
    # 时间戳
    created_at: datetime = field(default_factory=datetime.utcnow)


class BaseAgentV2(ABC):
    """企业级Agent基类 V2
    
    使用示例:
        class ArchitectAgent(BaseAgentV2):
            def __init__(self):
                super().__init__(
                    prompt_name="architect/foundation",
                    output_schema="foundation",
                    config=AgentConfig(model_name="gpt-4o")
                )
            
            async def execute(self, genre: str, theme: str) -> AgentResult:
                return await self._call_llm({
                    "genre": genre,
                    "theme": theme
                })
    """
    
    def __init__(
        self,
        prompt_name: str,
        output_schema: Optional[str] = None,
        config: Optional[AgentConfig] = None,
        registry: Optional[PromptRegistry] = None
    ):
        self.prompt_name = prompt_name
        self.output_schema = output_schema
        self.config = config or AgentConfig()
        
        # 初始化组件
        self._registry = registry or get_registry()
        self._sanitizer = PromptSanitizer(max_length=self.config.max_input_length)
        self._validator = OutputValidator()
        self._renderer = JinjaPromptRenderer()
        self._adapter = self._create_adapter()
        self._cache = PromptCache(CacheConfig(
            ttl_seconds=self.config.cache_ttl
        )) if self.config.enable_caching else None
        self._optimizer = TokenOptimizer() if self.config.enable_token_optimization else None
        
        # 注册输出模式
        if output_schema:
            self._register_schema(output_schema)
    
    def _create_adapter(self) -> ModelAdapter:
        """创建模型适配器"""
        adapter_config = AdapterConfig(
            model_name=self.config.model_name,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens
        )
        
        if self.config.model_name.startswith(("gpt-", "text-")):
            return OpenAIAdapter(adapter_config)
        elif self.config.model_name.startswith("claude-"):
            return AnthropicAdapter(adapter_config)
        else:
            # 默认使用OpenAI适配器
            return OpenAIAdapter(adapter_config)
    
    def _register_schema(self, schema_name: str):
        """注册输出验证模式"""
        # 动态导入模式类
        from prompts.schemas.novel_schemas import (
            FoundationOutput,
            ChapterOutlineOutput,
            AuditResultOutput,
            RewriteOutput,
            StyleAnalysisOutput,
        )
        
        schemas = {
            "foundation": FoundationOutput,
            "chapter_outline": ChapterOutlineOutput,
            "audit": AuditResultOutput,
            "rewrite": RewriteOutput,
            "style_analysis": StyleAnalysisOutput,
        }
        
        if schema_name in schemas:
            self._validator.register_schema(schema_name, schemas[schema_name])
    
    async def _call_llm(
        self,
        variables: Dict[str, Any],
        version: Optional[str] = None,
        history: Optional[List[Dict]] = None
    ) -> AgentResult:
        """调用LLM的完整流程
        
        流程:
        1. 获取提示词模板
        2. 净化输入变量
        3. 渲染模板
        4. 检查缓存
        5. 调用LLM
        6. 验证输出
        7. 更新缓存
        """
        start_time = time.time()
        
        try:
            # 1. 获取提示词
            prompt_version = self._registry.get(self.prompt_name, version)
            if not prompt_version:
                return self._error_result(
                    f"Prompt not found: {self.prompt_name}",
                    start_time
                )
            
            # 2. 净化输入
            sanitized_vars, sanitization_info = self._sanitize_variables(variables)
            if not sanitization_info["is_safe"] and self.config.strict_mode:
                return self._error_result(
                    f"Input validation failed: {sanitization_info['issues']}",
                    start_time
                )
            
            # 3. 检查缓存
            cache_hit = False
            cached_result = None
            if self._cache and self.config.enable_caching:
                cached_result = self._cache.get(
                    self.prompt_name,
                    sanitized_vars,
                    self.config.model_name,
                    prompt_version.version
                )
                if cached_result:
                    cache_hit = True
                    return self._success_result(
                        data=cached_result.get("data"),
                        raw_response=cached_result.get("raw_response"),
                        start_time=start_time,
                        prompt_version=prompt_version,
                        sanitized=True,
                        validation_passed=True,
                        cache_hit=True
                    )
            
            # 4. 渲染模板
            render_context = RenderContext(variables=sanitized_vars)
            if history:
                for msg in history:
                    render_context.add_history(msg.get("role"), msg.get("content"))
            
            rendered = self._renderer.render(
                prompt_version.content,
                render_context
            )
            
            system_prompt = rendered.get("system")
            user_prompt = rendered.get("user", "")
            
            # 5. Token优化
            if self._optimizer:
                system_prompt, user_prompt, _ = self._optimizer.optimize_prompt(
                    system_prompt, user_prompt
                )
            
            # 6. 模型适配
            system_prompt, user_prompt = self._adapter.optimize_for_model(
                system_prompt or "", user_prompt
            )
            
            # 7. 调用LLM (由子类实现具体调用)
            raw_response = await self._execute_llm_call(
                system_prompt, user_prompt, history
            )
            
            if raw_response is None:
                return self._error_result(
                    "LLM call failed",
                    start_time
                )
            
            # 8. 验证输出
            validation_passed = True
            validation_errors = []
            parsed_data = None
            
            if self.config.enable_validation and self.output_schema:
                validation_result = self._validator.validate(
                    raw_response,
                    self.output_schema,
                    strict=True
                )
                validation_passed = validation_result.is_valid
                validation_errors = validation_result.errors
                parsed_data = validation_result.data
            else:
                # 尝试解析JSON
                try:
                    parsed_data = json.loads(raw_response)
                except:
                    parsed_data = {"raw": raw_response}
            
            # 9. 更新缓存
            if self._cache and not cache_hit:
                self._cache.set(
                    self.prompt_name,
                    sanitized_vars,
                    self.config.model_name,
                    {
                        "data": parsed_data,
                        "raw_response": raw_response
                    },
                    version=prompt_version.version,
                    metadata={
                        "prompt_name": self.prompt_name,
                        "version": prompt_version.version
                    }
                )
            
            return self._success_result(
                data=parsed_data,
                raw_response=raw_response,
                start_time=start_time,
                prompt_version=prompt_version,
                sanitized=sanitization_info["is_safe"],
                validation_passed=validation_passed,
                cache_hit=cache_hit,
                validation_errors=validation_errors
            )
            
        except Exception as e:
            return self._error_result(str(e), start_time)
    
    @abstractmethod
    async def _execute_llm_call(
        self,
        system: Optional[str],
        user: str,
        history: Optional[List[Dict]]
    ) -> Optional[str]:
        """执行实际的LLM调用 - 子类必须实现"""
        pass
    
    def _sanitize_variables(
        self,
        variables: Dict[str, Any]
    ) -> tuple[Dict, Dict]:
        """净化变量"""
        if not self.config.enable_sanitization:
            return variables, {"is_safe": True, "issues": []}
        
        sanitized = {}
        all_issues = []
        is_safe = True
        
        for key, value in variables.items():
            if isinstance(value, str):
                result = self._sanitizer.sanitize(
                    value,
                    context=key,
                    strict_mode=self.config.strict_mode
                )
                sanitized[key] = result.sanitized
                all_issues.extend(result.issues)
                if not result.is_safe:
                    is_safe = False
            else:
                sanitized[key] = value
        
        return sanitized, {
            "is_safe": is_safe,
            "issues": all_issues
        }
    
    def _success_result(
        self,
        data: Any,
        raw_response: str,
        start_time: float,
        prompt_version: Any,
        sanitized: bool,
        validation_passed: bool,
        cache_hit: bool,
        validation_errors: Optional[List[str]] = None
    ) -> AgentResult:
        """创建成功结果"""
        latency = (time.time() - start_time) * 1000
        
        return AgentResult(
            success=True,
            data=data,
            raw_response=raw_response,
            prompt_name=self.prompt_name,
            version=prompt_version.version,
            model=self.config.model_name,
            latency_ms=round(latency, 2),
            tokens_used=None,  # 由子类填充
            sanitized=sanitized,
            validation_passed=validation_passed,
            cache_hit=cache_hit,
            validation_errors=validation_errors or []
        )
    
    def _error_result(
        self,
        error: str,
        start_time: float
    ) -> AgentResult:
        """创建错误结果"""
        latency = (time.time() - start_time) * 1000
        
        return AgentResult(
            success=False,
            data=None,
            raw_response=None,
            prompt_name=self.prompt_name,
            version="unknown",
            model=self.config.model_name,
            latency_ms=round(latency, 2),
            tokens_used=None,
            sanitized=False,
            validation_passed=False,
            cache_hit=False,
            error=error
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """获取Agent统计信息"""
        stats = {
            "prompt_name": self.prompt_name,
            "config": {
                "model": self.config.model_name,
                "enable_sanitization": self.config.enable_sanitization,
                "enable_validation": self.config.enable_validation,
                "enable_caching": self.config.enable_caching,
            }
        }
        
        if self._cache:
            stats["cache"] = self._cache.get_stats()
        
        return stats
