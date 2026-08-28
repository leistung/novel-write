"""大纲规划子图：LLM 生成 + 模板兜底。

独立成模块，避免 graph.py 与 analyst.py 循环引用。
"""
from __future__ import annotations

from typing import Any

from ._util import llm_respond
from .prompts import SYSTEM_OUTLINE, build_outline_user_prompt


def mock_outline(meta: dict) -> dict:
    total = int(meta.get("target_chapters", 20) or 20)
    per_vol = 7
    volumes: list[dict[str, Any]] = []
    ch = 1
    vn = 0
    while ch <= total:
        vn += 1
        end = min(ch + per_vol - 1, total)
        chapters = [
            {"number": n, "title": f"第{n}章 待定", "summary": "（待生成梗概）"}
            for n in range(ch, end + 1)
        ]
        volumes.append({"name": f"第{vn}卷", "chapters": chapters})
        ch = end + 1
    return {"volumes": volumes}


async def plan_outline(state: dict[str, Any]) -> dict:
    """大纲规划节点：优先 LLM 生成，失败回退模板。"""
    meta = state.get("book_meta", {})
    try:
        content, _, _, _ = await llm_respond(
            {"model_choice": None}, SYSTEM_OUTLINE, build_outline_user_prompt(meta)
        )
        content = content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        outline = __import__("json").loads(content)
        return {"outline": outline, "error": None}
    except Exception as e:
        return {"outline": mock_outline(meta), "error": f"LLM 不可用，使用模板大纲: {e}"}
