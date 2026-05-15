"""LLM客户端"""
import asyncio
from typing import AsyncGenerator, Dict, Any, Optional, List
from dataclasses import dataclass

import httpx
from openai import AsyncOpenAI
import anthropic

from config.settings import get_settings


@dataclass
class LLMResponse:
    """LLM响应"""
    content: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    model: str = ""
    finish_reason: str = ""


class LLMClient:
    """LLM客户端"""
    
    def __init__(self):
        self.settings = get_settings()
        self._openai_client: Optional[AsyncOpenAI] = None
        self._anthropic_client: Optional[anthropic.AsyncAnthropic] = None
    
    @property
    def openai_client(self) -> AsyncOpenAI:
        """获取OpenAI客户端"""
        if self._openai_client is None:
            api_key = self.settings.OPENAI_API_KEY
            self._openai_client = AsyncOpenAI(
                api_key=api_key.get_secret_value() if api_key else None,
                base_url=self.settings.OPENAI_BASE_URL
            )
        return self._openai_client
    
    @property
    def anthropic_client(self) -> anthropic.AsyncAnthropic:
        """获取Anthropic客户端"""
        if self._anthropic_client is None:
            api_key = self.settings.ANTHROPIC_API_KEY
            self._anthropic_client = anthropic.AsyncAnthropic(
                api_key=api_key.get_secret_value() if api_key else None
            )
        return self._anthropic_client
    
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        provider: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        **kwargs
    ) -> LLMResponse:
        """生成文本"""
        provider = provider or self.settings.DEFAULT_LLM_PROVIDER
        
        if provider == "openai":
            return await self._generate_openai(
                system_prompt, user_prompt, temperature, max_tokens, **kwargs
            )
        elif provider == "anthropic":
            return await self._generate_anthropic(
                system_prompt, user_prompt, temperature, max_tokens, **kwargs
            )
        else:
            raise ValueError(f"Unknown provider: {provider}")
    
    async def generate_stream(
        self,
        system_prompt: str,
        user_prompt: str,
        provider: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """流式生成文本"""
        provider = provider or self.settings.DEFAULT_LLM_PROVIDER
        
        if provider == "openai":
            async for chunk in self._generate_stream_openai(
                system_prompt, user_prompt, temperature, max_tokens, **kwargs
            ):
                yield chunk
        elif provider == "anthropic":
            async for chunk in self._generate_stream_anthropic(
                system_prompt, user_prompt, temperature, max_tokens, **kwargs
            ):
                yield chunk
        else:
            raise ValueError(f"Unknown provider: {provider}")
    
    async def _generate_openai(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int,
        **kwargs
    ) -> LLMResponse:
        """使用OpenAI生成"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = await self.openai_client.chat.completions.create(
            model=self.settings.OPENAI_MODEL,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        
        return LLMResponse(
            content=response.choices[0].message.content,
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
            total_tokens=response.usage.total_tokens,
            model=response.model,
            finish_reason=response.choices[0].finish_reason
        )
    
    async def _generate_stream_openai(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """使用OpenAI流式生成"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        stream = await self.openai_client.chat.completions.create(
            model=self.settings.OPENAI_MODEL,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
            **kwargs
        )
        
        async for chunk in stream:
            if chunk.choices and len(chunk.choices) > 0 and chunk.choices[0].delta and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
    async def _generate_anthropic(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int,
        **kwargs
    ) -> LLMResponse:
        """使用Anthropic生成"""
        response = await self.anthropic_client.messages.create(
            model=self.settings.ANTHROPIC_MODEL,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            **kwargs
        )
        
        return LLMResponse(
            content=response.content[0].text,
            prompt_tokens=response.usage.input_tokens,
            completion_tokens=response.usage.output_tokens,
            total_tokens=response.usage.input_tokens + response.usage.output_tokens,
            model=response.model,
            finish_reason=response.stop_reason
        )
    
    async def _generate_stream_anthropic(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """使用Anthropic流式生成"""
        async with self.anthropic_client.messages.stream(
            model=self.settings.ANTHROPIC_MODEL,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            **kwargs
        ) as stream:
            async for text in stream.text_stream:
                yield text


# 全局LLM客户端实例
llm_client = LLMClient()
