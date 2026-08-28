"""Embedding 配置解析（backend 数据层）：按「当前请求用户」的默认 LLM 配置解析。

配置优先级（resolve_embedding_config）：
  1. 用户默认 UserLLMConfig 的 embedding 三元组（embedding_base_url / api_key / model）
  2. 用户默认 UserLLMConfig 的对话 LLM 三元组（base_url / api_key / model）——同一端点通常也提供 embeddings
  3. 无 → None（storyclaw 层继续走环境变量 / 内置兜底）

user_id 通过 contextvar 透传：get_current_user 鉴权成功后调用 set_embedding_user()。
"""
from __future__ import annotations

import os
from contextvars import ContextVar

_current_user_id: ContextVar[int | None] = ContextVar("sc_embedding_user_id", default=None)


def set_embedding_user(user_id: int | None) -> None:
    """在请求作用域内标记当前用户（供 embedding 配置解析使用）。"""
    _current_user_id.set(user_id)


async def resolve_embedding_config() -> dict | None:
    """解析当前请求用户的 embedding 配置；无则返回 None（走环境变量）。"""
    user_id = _current_user_id.get()
    if not user_id:
        return None
    try:
        from sqlalchemy import select
        from ..core.security import decrypt_api_key
        from ..database import AsyncSessionLocal
        from ..models import UserLLMConfig
        async with AsyncSessionLocal() as db:
            c = await db.scalar(select(UserLLMConfig).where(
                UserLLMConfig.user_id == user_id,
                UserLLMConfig.is_default == True,  # noqa: E712
            ).order_by(UserLLMConfig.id.desc()))
            if not c:
                return None
            # 用户显式配置的 embedding 三元组；未单独配置时复用对话 LLM 的 base_url / api_key
            emb_model = (c.embedding_model or "").strip()
            emb_url = (c.embedding_base_url or c.base_url or "").strip()
            emb_key = decrypt_api_key(c.embedding_api_key_enc) or decrypt_api_key(c.api_key_enc) or ""
            if emb_model and emb_url and emb_key:
                return {"base_url": emb_url.rstrip("/"), "api_key": emb_key, "model": emb_model}
            # 未配置向量模型 → 无可用 embedding 配置（上层走 hash 兜底或报错）
            return None
    except Exception:
        return None
