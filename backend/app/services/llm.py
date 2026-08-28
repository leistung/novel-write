"""LLM 工厂（backend 数据层）：把 DB 配置解析成 agent 可用的 chat client。

client 构建（三种格式适配：openai_chat / anthropic / openai_responses）
统一在 packages/storyclaw/src/storyclaw/llm.py；
本模块只负责：解密 key / 查库 / 版本路由 → 调 storyclaw.llm.build_chat_client。
"""
from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from ..config import settings
from ..core.security import decrypt_api_key
from ..database import AsyncSessionLocal
from ..models import UserLLMConfig
from .configs import load_models

SYSTEM_PROMPT = "你是 StoryClaw 助手，帮助用户进行小说创作相关的问答。回答简洁。"


def build_chat_client(*, format: str, model: str, api_key: str = "", base_url: str = "",
                      temperature: float = 0.7, max_tokens: int = 8192):
    """委托 storyclaw.llm.build_chat_client（格式适配统一在 agent 包）。"""
    from storyclaw.llm import build_chat_client as _build
    return _build(format=format, model=model, api_key=api_key, base_url=base_url,
                  temperature=temperature, max_tokens=max_tokens)


async def invoke_llm(user_msg: str, *, model_cfg: UserLLMConfig | None = None, business_model_id: str | None = None) -> dict:
    """调用 LLM 返回 {content, in_tokens, out_tokens, model_id}。"""
    if business_model_id:
        chat, model_id = _build_business(business_model_id)
    else:
        if model_cfg is None:
            raise ValueError("本地版本需提供 model_cfg")
        chat, model_id = _build_local(model_cfg)
    resp = await chat.ainvoke([SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=user_msg)])
    content = resp.content if isinstance(resp.content, str) else str(resp.content)
    usage = getattr(resp, "usage_metadata", None) or {}
    in_t = int(usage.get("input_tokens", 0) or 0)
    out_t = int(usage.get("output_tokens", 0) or 0)
    return {"content": content, "in_tokens": in_t, "out_tokens": out_t, "model_id": model_id}


def _build_local(cfg: UserLLMConfig):
    key = decrypt_api_key(cfg.api_key_enc) or ""
    chat = build_chat_client(
        format=cfg.format or "openai_chat", model=cfg.model, api_key=key,
        base_url=cfg.base_url or "", temperature=cfg.temperature, max_tokens=cfg.max_tokens,
    )
    return chat, cfg.model


def _build_business(model_id: str):
    m = next((x for x in load_models().get("models", []) if x.get("id") == model_id), None)
    if not m:
        raise ValueError(f"未知模型 {model_id}")
    if m["format"] == "anthropic":
        return build_chat_client(format="anthropic", model=model_id, api_key=settings.anthropic_api_key), model_id
    return build_chat_client(
        format=m.get("format", "openai_chat"), model=model_id,
        api_key=settings.openai_api_key, base_url=m.get("base_url", ""),
    ), model_id


# ===== P0-4: LLM 工厂（供 storyclaw 包注入） =====

async def build_llm_from_choice(model_choice: dict) -> tuple:
    """供 storyclaw.configure(llm_factory=...) 注入的异步工厂。

    model_choice:
      - {"kind":"business","model_id":"gpt-4o-mini"}
      - {"kind":"local","config_id":1,"user_id":12}
      - {"kind":"local","config_id":None,"user_id":12}  # 取该用户的默认配置

    返回 (chat_model, model_id)。
    """
    kind = model_choice.get("kind") or "business"
    if kind == "business":
        model_id = model_choice.get("model_id") or "gpt-4o-mini"
        return _build_business(model_id)
    # local: 需查 DB
    config_id = model_choice.get("config_id")
    user_id = model_choice.get("user_id")
    async with AsyncSessionLocal() as db:
        cfg = await _resolve_local_cfg_by_id(config_id, db, user_id=user_id)
        return _build_local(cfg)


async def _resolve_local_cfg_by_id(config_id, db, user_id=None) -> UserLLMConfig:
    from sqlalchemy import select
    if config_id:
        c = await db.get(UserLLMConfig, int(config_id))
        if not c:
            raise ValueError(f"LLM 配置不存在: {config_id}")
        return c
    # 默认配置：优先按 user_id 过滤，避免取到其他用户的残留配置
    q = select(UserLLMConfig).where(UserLLMConfig.is_default == True)  # noqa: E712
    if user_id:
        q = q.where(UserLLMConfig.user_id == user_id)
    c = await db.scalar(q)
    if c:
        return c
    # 回退：该用户任意一条配置
    if user_id:
        c = await db.scalar(select(UserLLMConfig).where(
            UserLLMConfig.user_id == user_id).order_by(UserLLMConfig.id))
        if c:
            return c
    # 最终回退：全表任意一条
    c = await db.scalar(select(UserLLMConfig).order_by(UserLLMConfig.id))
    if not c:
        raise ValueError("未配置任何 LLM")
    return c
