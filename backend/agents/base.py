"""Agent基类"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple, AsyncGenerator
from enum import Enum

from llm.client import llm_client, LLMResponse
from prompts.loader import render_prompt


class AgentStatus(Enum):
    """Agent状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AgentResult:
    """Agent执行结果"""
    ok: bool
    task: str
    data: Dict[str, Any] = field(default_factory=dict)
    score: Optional[float] = None
    feedback: str = ""
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    token_usage: Dict[str, int] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "ok": self.ok,
            "task": self.task,
            "data": self.data,
            "score": self.score,
            "feedback": self.feedback,
            "errors": self.errors,
            "warnings": self.warnings,
            "token_usage": self.token_usage
        }


class BaseAgent(ABC):
    """Agent基类 - 支持 prompts 模板系统 + 流式输出"""
    
    def __init__(self, name: str):
        self.name = name
        self.llm = llm_client
        self.status = AgentStatus.PENDING
        self.current_task: Optional[str] = None
    
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        **kwargs
    ) -> LLMResponse:
        """调用LLM生成内容（非流式，内部自动拼接）"""
        content_parts = []
        async for chunk in self.llm.generate_stream(
            system_prompt, user_prompt,
            temperature=temperature, max_tokens=max_tokens, **kwargs
        ):
            content_parts.append(chunk)
        full_content = "".join(content_parts)
        return LLMResponse(content=full_content)
    
    async def generate_stream(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        流式调用LLM，逐块yield文本。
        
        所有Agent方法内部统一走这个方法，
        上层SSE端点通过它拿到实时文本块。
        """
        async for chunk in self.llm.generate_stream(
            system_prompt, user_prompt,
            temperature=temperature, max_tokens=max_tokens, **kwargs
        ):
            yield chunk
    
    def result(
        self,
        task: str,
        ok: bool = True,
        data: Dict[str, Any] = None,
        score: Optional[float] = None,
        feedback: str = "",
        errors: List[str] = None,
        warnings: List[str] = None,
        token_usage: Dict[str, int] = None
    ) -> AgentResult:
        """创建执行结果"""
        return AgentResult(
            ok=ok,
            task=task,
            data=data or {},
            score=score,
            feedback=feedback,
            errors=errors or [],
            warnings=warnings or [],
            token_usage=token_usage or {}
        )
    
    def success(
        self,
        task: str,
        data: Dict[str, Any] = None,
        feedback: str = "",
        token_usage: Dict[str, int] = None
    ) -> AgentResult:
        """创建成功结果"""
        return self.result(
            task=task,
            ok=True,
            data=data,
            feedback=feedback,
            token_usage=token_usage
        )
    
    def failure(
        self,
        task: str,
        error: str,
        data: Dict[str, Any] = None
    ) -> AgentResult:
        """创建失败结果"""
        return self.result(
            task=task,
            ok=False,
            errors=[error],
            data=data or {}
        )
    
    def _render_prompt(self, prompt_name: str, variables: Dict[str, Any]) -> Tuple[str, str]:
        """
        使用 prompts 渲染提示词模板
        
        Args:
            prompt_name: 提示词名称（如 architect/foundation）
            variables: 模板变量
        
        Returns:
            (system_prompt, user_prompt)
        """
        return render_prompt(prompt_name, variables)
    
    def _build_system_prompt(self, base_prompt: str, genre: str = None) -> str:
        """构建系统提示词，如果指定genre则附加skill内容"""
        if not genre:
            return base_prompt
        from skills.loader import skill_loader
        suffix = skill_loader.get_skill_prompt_suffix(genre)
        if suffix:
            return base_prompt + "\n\n## 题材专家知识库\n" + suffix
        return base_prompt

    @abstractmethod
    async def execute(self, task: str, **kwargs) -> AgentResult:
        """执行Agent核心逻辑（子类必须实现）"""
        pass
    
    def get_public_methods(self) -> List[str]:
        """获取所有public方法名"""
        public_methods = []
        for attr_name in dir(self):
            if not attr_name.startswith("_") and attr_name != "execute":
                attr = getattr(self, attr_name)
                if callable(attr) and attr_name not in ["generate", "generate_stream", "result", "success", "failure", "get_public_methods"]:
                    public_methods.append(attr_name)
        return public_methods
