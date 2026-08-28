"""Writer 节点：首次写作 / 修改 / 段内续写 / 选中文本润色。

- intent=write:     调用 write-chapter skill，从大纲+前章摘要生成
- intent=modify:    调用 modify-chapter skill，基于当前章节内容+修改要求重写
- intent=continue:  调用 continue-writing skill，段内续写片段
- intent=polish:    调用 polish-chapter skill，选中文本润色
"""
from __future__ import annotations

import json
import logging

from .. import prompts
from .._util import ensure_paragraphs, llm_respond, stream_llm_respond, usage_payload
from ..deps import get_deps, get_stream_sink
from ..skills import describe_skill, read_skill_sections
from ..state import AgentState
from .tools import tool_loop

log = logging.getLogger("storyclaw.writer")


async def _respond_aware(state: AgentState, sys_prompt: str, user_msg: str):
    """统一应答入口：有流式 sink（SSE 请求）时逐 token 推送，否则非流式；
    无论哪种方式，最终内容都做「空行分段」后处理。"""
    sink = get_stream_sink()

    async def on_delta(piece: str):
        await sink("draft", {"delta": piece})

    if sink is not None:
        content, in_t, out_t, model_id = await stream_llm_respond(state, sys_prompt, user_msg, on_delta)
    else:
        content, in_t, out_t, model_id = await llm_respond(state, sys_prompt, user_msg)
    return ensure_paragraphs(content), in_t, out_t, model_id


def _skill_instructions(skill_name: str) -> str:
    """把 SKILL.md 的 Workflow / Constraints / Output 注入 system prompt，
    让 skill 文件真正驱动行为（DeerFlow 式 skill 加载）。"""
    sections = read_skill_sections(skill_name)
    if not sections:
        return ""
    lines = [f"<skill:{skill_name}>"]
    for key, content in sections.items():
        if content:
            lines.append(f"[{key}]\n{content}")
    lines.append("</skill>")
    return "\n\n".join(lines)


async def writer(state: AgentState) -> dict:
    intent = state.get("intent") or "write"
    if intent == "continue":
        return await _writer_continue(state)
    if intent == "polish":
        return await _writer_polish(state)
    is_modify = intent == "modify" and bool(state.get("modify_request") or state.get("current_content"))
    if is_modify:
        return await _writer_modify(state)
    return await _writer_write(state)


async def _writer_write(state: AgentState) -> dict:
    describe_skill("write-chapter")
    ctx = state.get("context") or {}
    chapter_meta = ctx.get("chapter_meta") or {}
    target_words = int(chapter_meta.get("per_chapter_words", 3000) or 3000)
    sb = (ctx.get("setting_briefs") or {})
    # Tool Use 模式：deps 注入了工具执行器时，设定/RAG 不再全量预注入，
    # 让 LLM 通过 query_setting / query_memory 等工具按需查询（省 token、更灵活）。
    use_tools = get_deps().tool_executor is not None
    if use_tools:
        char_briefs = "（写作时可用 query_setting 工具按需查询角色设定）"
        scene_briefs = "（可用 query_setting 工具查询场景设定）"
        item_briefs = "（可用 query_setting 工具查询物品设定）"
        plot_briefs = "（可用 query_setting 工具查询情节脉络）"
        rag_briefs = "（可用 query_memory 工具检索本书记忆）"
    else:
        char_briefs = sb.get("characters") or "（暂无）"
        scene_briefs = sb.get("scenes") or "（暂无）"
        item_briefs = sb.get("items") or "（暂无）"
        plot_briefs = sb.get("plots") or "（暂无）"
        rag_briefs = ctx.get("rag_briefs") or "（暂无检索结果）"
    sys_prompt = prompts.WRITER_SYSTEM.format(
        chapter_title=chapter_meta.get("title", ""),
        target_words=target_words,
        outline_node=json.dumps(ctx.get("outline_node") or {}, ensure_ascii=False),
        prev_summary=ctx.get("prev_chapter_summary", "（无前章）"),
        character_briefs=char_briefs,
        scene_briefs=scene_briefs,
        item_briefs=item_briefs,
        plot_briefs=plot_briefs,
        rag_briefs=rag_briefs,
        user_prefs=json.dumps(state.get("user_memory") or {}, ensure_ascii=False),
    ) + "\n\n" + _skill_instructions("write-chapter")
    msgs = state.get("messages") or []
    user_msg = msgs[-1]["content"] if msgs else f"请撰写《{chapter_meta.get('title', '')}》"
    # Tool Use：ReAct 收集工具结果（未注入工具时为空，直接生成）
    try:
        tool_out = await tool_loop(state, sys_prompt, user_msg)
        if tool_out:
            sys_prompt += "\n\n【工具查询结果】\n" + tool_out
    except Exception as e:
        log.warning("tool_loop failed, fallback to direct write: %s", e)
    try:
        content, in_t, out_t, model_id = await _respond_aware(state, sys_prompt, user_msg)
    except Exception as e:
        return {"draft_content": "", "error": f"Writer LLM 调用失败: {e}", "status": "error"}
    return {
        "draft_content": content, "active_skill": "write-chapter",
        "token_usage": usage_payload(model_id, in_t, out_t), "error": None,
    }


async def _writer_modify(state: AgentState) -> dict:
    describe_skill("modify-chapter")
    ctx = state.get("context") or {}
    chapter_meta = ctx.get("chapter_meta") or {}
    current = state.get("current_content") or ""
    modify_req = state.get("modify_request") or ""
    sys_prompt = prompts.MODIFY_SYSTEM.format(
        chapter_title=chapter_meta.get("title", ""),
        current_content=current,
        modify_request=modify_req,
        user_prefs=json.dumps(state.get("user_memory") or {}, ensure_ascii=False),
    ) + "\n\n" + _skill_instructions("modify-chapter")
    try:
        content, in_t, out_t, model_id = await _respond_aware(state, sys_prompt, f"请按要求修改本章：{modify_req}")
    except Exception as e:
        return {"draft_content": "", "error": f"Modify LLM 调用失败: {e}", "status": "error"}
    return {
        "draft_content": content, "active_skill": "modify-chapter",
        "token_usage": usage_payload(model_id, in_t, out_t), "error": None,
    }


async def _writer_continue(state: AgentState) -> dict:
    describe_skill("continue-writing")
    ctx = state.get("context") or {}
    chapter_meta = ctx.get("chapter_meta") or {}
    prefix = state.get("prefix_text") or ""
    if not prefix:
        prefix = (state.get("current_content") or "")[-1500:]
    sys_prompt = prompts.CONTINUE_SYSTEM.format(
        chapter_number=chapter_meta.get("number", "?"),
        chapter_title=chapter_meta.get("title", ""),
        outline_node=json.dumps(ctx.get("outline_node") or {}, ensure_ascii=False),
        prefix_text=prefix,
        max_words=600,
        user_prefs=json.dumps(state.get("user_memory") or {}, ensure_ascii=False),
    ) + "\n\n" + _skill_instructions("continue-writing")
    try:
        content, in_t, out_t, model_id = await _respond_aware(state, sys_prompt, "请基于上文续写片段")
    except Exception as e:
        return {"draft_content": "", "error": f"Continue LLM 调用失败: {e}", "status": "error"}
    return {
        "draft_content": content, "active_skill": "continue-writing",
        "token_usage": usage_payload(model_id, in_t, out_t), "error": None,
    }


async def _writer_polish(state: AgentState) -> dict:
    describe_skill("polish-chapter")
    selected = state.get("selected_text") or ""
    polish_goal = state.get("polish_goal") or "提升文笔与画面感"
    if not selected:
        return {"draft_content": "", "error": "未提供待润色文本", "status": "error"}
    sys_prompt = prompts.POLISH_SYSTEM.format(
        polish_goal=polish_goal,
        selected_text=selected,
        user_prefs=json.dumps(state.get("user_memory") or {}, ensure_ascii=False),
    ) + "\n\n" + _skill_instructions("polish-chapter")
    try:
        content, in_t, out_t, model_id = await _respond_aware(state, sys_prompt, "请润色这段文字")
    except Exception as e:
        return {"draft_content": "", "error": f"Polish LLM 调用失败: {e}", "status": "error"}
    return {
        "draft_content": content, "active_skill": "polish-chapter",
        "token_usage": usage_payload(model_id, in_t, out_t), "error": None,
    }
