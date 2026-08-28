"""Agent 运行时统一入口（供 backend 薄网关调用）。

backend 只做：鉴权 / 计费 / 落库 / SSE 格式；真正的 agent 执行全部走这里。
"""
from __future__ import annotations

import json
from typing import Any, AsyncGenerator

from . import graph as graph_mod


def get_graph():
    return graph_mod.graph


def get_outline_graph():
    return graph_mod.outline_graph


async def run_agent(input_state: dict, thread_id: str) -> dict:
    """非流式调用 agent，返回最终 state（合并所有节点 diff）。"""
    config = {"configurable": {"thread_id": thread_id}}
    final: dict = {}
    async for chunk in get_graph().astream(input_state, config=config, stream_mode="updates"):
        for node, diff in (chunk or {}).items():
            if isinstance(diff, dict):
                final.update(diff)
    return final


async def stream_agent(input_state: dict, thread_id: str) -> AsyncGenerator[tuple[str, dict], None]:
    """流式调用 agent，逐个节点 yield (node_name, state_diff)。"""
    config = {"configurable": {"thread_id": thread_id}}
    async for chunk in get_graph().astream(input_state, config=config, stream_mode="updates"):
        for node, diff in (chunk or {}).items():
            if isinstance(diff, dict):
                yield node, diff


def sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
