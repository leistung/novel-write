"""Reviewer 节点：字数自检 + 修改要求满足度检查。"""
from __future__ import annotations

import json

from .._util import llm_respond
from ..context import count_words
from ..state import AgentState


async def reviewer(state: AgentState) -> dict:
    draft = state.get("draft_content") or ""
    ctx = state.get("context") or {}
    chapter_meta = ctx.get("chapter_meta") or {}
    target = int(chapter_meta.get("per_chapter_words", 3000) or 3000)
    actual = count_words(draft)
    round_n = int(state.get("review_round") or 0) + 1
    modify_req = state.get("modify_request") or ""
    active_skill = state.get("active_skill") or ""

    # modify 模式：用 LLM 检查修改要求是否满足
    if modify_req and active_skill == "modify-chapter" and round_n < 2:
        try:
            satisfied = await _llm_check_modify(draft, modify_req, state)
            if not satisfied["pass"]:
                return {"review_feedback": f"修改未达标：{satisfied['reason']}，请按要求重写",
                        "review_round": round_n, "status": "review_retry"}
            return {
                "review_feedback": f"修改通过：{satisfied['reason']}（{actual}字）",
                "review_round": round_n,
                "messages": [{"role": "assistant", "content": draft[:200] + "...(章节已修改)"}],
                "status": "finished",
            }
        except Exception:
            pass  # LLM 检查失败，降级为字数检查

    # 字数自检
    if actual < target * 0.8 and round_n < 2:
        return {"review_feedback": f"字数不足：当前 {actual} 字，目标 {target} 字，请扩写",
                "review_round": round_n, "status": "review_retry"}
    return {
        "review_feedback": f"通过（{actual}/{target} 字）",
        "review_round": round_n,
        "messages": [{"role": "assistant", "content": draft[:200] + "...(章节已生成)"}],
        "status": "finished",
    }


async def _llm_check_modify(draft: str, modify_req: str, state: AgentState) -> dict:
    try:
        content, _, _, _ = await llm_respond(
            state,
            '判断草稿是否满足用户的修改要求。只输出严格 JSON：{"pass":true|false,"reason":"简短说明"}\n不要任何其他文字。',
            f"【修改要求】{modify_req}\n\n【草稿前1000字】{draft[:1000]}",
        )
    except Exception:
        return {"pass": True, "reason": "LLM 不可用，跳过修改检查"}
    content = content.strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    try:
        result = json.loads(content)
        return {"pass": bool(result.get("pass", True)), "reason": str(result.get("reason", ""))}
    except Exception:
        return {"pass": True, "reason": "解析失败，默认通过"}
