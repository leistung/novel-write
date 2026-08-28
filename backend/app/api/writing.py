"""P1-6 写作 Skill 全集 API（薄网关）。

Agent 执行统一走 packages/storyclaw/runtime.run_agent，
本模块只负责：鉴权 / 落库 / 积分计费 / 上下文组装。
- POST /chapters/{cid}/polish     选中文本润色
- POST /chapters/{cid}/continue   段内续写
- POST /books/{bid}/multi-write   批量生成多章
- POST /books/{bid}/analyze        分析 skill（情节/角色/一致性/前情/大纲）
- POST /assist/*                   辅助 skill（头脑风暴/标题/场景/对话/阅读配置）
"""
from __future__ import annotations

import json
import re
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from storyclaw.context import count_words
from storyclaw.runtime import run_agent

from ..core.deps import get_current_user
from ..database import get_db
from ..models import Book, Chapter, CreditsLedger, Message, Outline, User
from ..schemas import (
    AnalyzeIn, AnalyzeOut, AssistOut, BrainstormIn, ContinueIn, ContinueOut,
    DialoguePolishIn, MultiWriteIn, MultiWriteItem, MultiWriteOut,
    PolishIn, PolishOut, ReadingConfigGenIn, SceneEnhanceIn, TitleGenIn,
)
from ..services import pricing as pricing_svc
from ..services.memory import load_user_memory
from ..services.skill_loader import build_write_context

router = APIRouter(prefix="", tags=["writing-skills"])


# ============ 公共辅助 ============

def _model_choice(u: User, choice: dict | None) -> dict:
    if u.version == "local":
        return {"kind": "local", "config_id": (choice or {}).get("config_id"), "user_id": u.id}
    return {"kind": "business", "model_id": (choice or {}).get("model_id") or "gpt-4o-mini"}


async def _save_assistant_msg(db: AsyncSession, u: User, thread_id: str,
                              content: str, model_id: str, in_t: int, out_t: int,
                              ref_user_msg_id: int | None = None) -> tuple[Message, int]:
    """保存 assistant 消息 + 扣积分。返回 (message, credits_cost)。"""
    u2 = await db.get(User, u.id)
    cost = 0
    if u2.version == "business":
        cost = pricing_svc.compute_cost(model_id, in_t, out_t)
        u2.credits_balance -= cost
        db.add(CreditsLedger(user_id=u2.id, delta=-cost, reason="consume", model=model_id,
                             in_tokens=in_t, out_tokens=out_t, ref_msg_id=ref_user_msg_id))
    am = Message(user_id=u2.id, thread_id=thread_id, role="assistant", content=content,
                 model=model_id, in_tokens=in_t, out_tokens=out_t, credits_cost=cost)
    db.add(am)
    await db.commit()
    await db.refresh(am)
    await db.refresh(u2)
    return am, cost


async def _load_outline(db: AsyncSession, book_id: int) -> dict:
    row = await db.scalar(select(Outline).where(Outline.book_id == book_id))
    if row and row.content:
        try:
            return json.loads(row.content) if isinstance(row.content, str) else row.content
        except Exception:
            return {}
    return {}


async def _load_book_meta(db: AsyncSession, book_id: int, u: User) -> dict:
    b = await db.get(Book, book_id)
    if not b or b.user_id != u.id:
        raise HTTPException(404, "书籍不存在")
    return {
        "id": b.id, "title": b.title, "genre": b.genre or "",
        "intro": b.intro or "", "protagonist_name": b.protagonist_name or "",
        "protagonist_intro": b.protagonist_intro or "",
        "target_chapters": b.target_chapters, "target_words": b.target_words,
        "per_chapter_words": b.per_chapter_words,
    }


# ============ 1. 选中文本润色 ============

@router.post("/chapters/{cid}/polish", response_model=PolishOut)
async def polish_chapter(
    cid: int, data: PolishIn,
    u: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """polish-chapter skill：对选中文本做文笔润色。"""
    c = await db.get(Chapter, cid)
    if not c:
        raise HTTPException(404, "章节不存在")
    b = await db.get(Book, c.book_id)
    if not b or b.user_id != u.id:
        raise HTTPException(404, "章节不存在")
    if not data.selected_text.strip():
        raise HTTPException(400, "待润色文本不能为空")

    thread_id = data.thread_id or uuid.uuid4().hex
    um = Message(user_id=u.id, thread_id=thread_id, role="user",
                 content=f"[润色] {data.polish_goal or '提升文笔'}：{data.selected_text[:100]}...")
    db.add(um)
    await db.commit()
    await db.refresh(um)

    mc = _model_choice(u, data.llm_choice)
    user_mem = await load_user_memory(u.id, db)
    ctx = await build_write_context(u.id, c.book_id, cid, db)

    input_state = {
        "user_id": u.id, "book_id": c.book_id, "chapter_id": cid,
        "thread_id": thread_id,
        "messages": [{"role": "user", "content": data.selected_text}],
        "model_choice": mc, "user_memory": user_mem, "context": ctx,
        "selected_text": data.selected_text,
        "polish_goal": data.polish_goal or "提升文笔与画面感",
        "current_content": c.content or "",
    }
    final = await run_agent(input_state, thread_id)

    content = final.get("draft_content", "") or ""
    if not content:
        raise HTTPException(500, f"润色失败：{final.get('error', '未返回内容')}")
    tu = final.get("token_usage") or {}
    in_t, out_t = int(tu.get("in_tokens", 0)), int(tu.get("out_tokens", 0))
    model_id = tu.get("model_id", "") or ""

    am, cost = await _save_assistant_msg(db, u, thread_id, content, model_id, in_t, out_t, um.id)
    return PolishOut(content=content, word_count=count_words(content), model=model_id,
                     in_tokens=in_t, out_tokens=out_t, credits_cost=cost,
                     thread_id=thread_id, message_id=am.id)


# ============ 2. 段内续写 ============

@router.post("/chapters/{cid}/continue", response_model=ContinueOut)
async def continue_writing(
    cid: int, data: ContinueIn,
    u: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """continue-writing skill：基于光标前文续写片段。"""
    c = await db.get(Chapter, cid)
    if not c:
        raise HTTPException(404, "章节不存在")
    b = await db.get(Book, c.book_id)
    if not b or b.user_id != u.id:
        raise HTTPException(404, "章节不存在")

    prefix = data.prefix_text or ""
    if not prefix and c.content:
        prefix = c.content[-1500:]

    thread_id = data.thread_id or uuid.uuid4().hex
    um = Message(user_id=u.id, thread_id=thread_id, role="user",
                 content=f"[续写片段] 光标前：{prefix[-80:]}...")
    db.add(um)
    await db.commit()
    await db.refresh(um)

    mc = _model_choice(u, data.llm_choice)
    user_mem = await load_user_memory(u.id, db)
    ctx = await build_write_context(u.id, c.book_id, cid, db)

    input_state = {
        "user_id": u.id, "book_id": c.book_id, "chapter_id": cid,
        "thread_id": thread_id,
        "messages": [{"role": "user", "content": "请基于上文续写片段"}],
        "model_choice": mc, "user_memory": user_mem, "context": ctx,
        "prefix_text": prefix,
        "current_content": c.content or "",
    }
    final = await run_agent(input_state, thread_id)

    content = final.get("draft_content", "") or ""
    if not content:
        raise HTTPException(500, f"续写失败：{final.get('error', '未返回内容')}")
    tu = final.get("token_usage") or {}
    in_t, out_t = int(tu.get("in_tokens", 0)), int(tu.get("out_tokens", 0))
    model_id = tu.get("model_id", "") or ""

    am, cost = await _save_assistant_msg(db, u, thread_id, content, model_id, in_t, out_t, um.id)
    return ContinueOut(content=content, word_count=count_words(content), model=model_id,
                       in_tokens=in_t, out_tokens=out_t, credits_cost=cost,
                       thread_id=thread_id, message_id=am.id)


# ============ 3. 批量生成多章 ============

@router.post("/books/{bid}/multi-write", response_model=MultiWriteOut)
async def multi_write(
    bid: int, data: MultiWriteIn,
    u: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """write-multi-chapters skill：批量生成多章正文。"""
    b = await db.get(Book, bid)
    if not b or b.user_id != u.id:
        raise HTTPException(404, "书籍不存在")

    start = data.start_number
    if data.end_number:
        end = data.end_number
    elif data.count:
        end = start + data.count - 1
    else:
        end = start
    if end < start:
        raise HTTPException(400, "end_number 不能小于 start_number")
    if end - start > 20:
        raise HTTPException(400, "单次批量不超过 20 章")

    thread_id = data.thread_id or uuid.uuid4().hex
    mc = _model_choice(u, data.llm_choice)
    user_mem = await load_user_memory(u.id, db)
    outline = await _load_outline(db, bid)

    items: list[MultiWriteItem] = []
    total_in, total_out, total_cost = 0, 0, 0
    model_id = ""

    # 加载范围内章节
    rs = await db.scalars(select(Chapter).where(
        Chapter.book_id == bid, Chapter.number >= start, Chapter.number <= end
    ).order_by(Chapter.number))
    chapters_by_num = {c.number: c for c in rs}

    # 若章节不存在，自动创建
    for num in range(start, end + 1):
        if num not in chapters_by_num:
            nc = Chapter(book_id=bid, number=num, title=f"第{num}章 待定", content="", word_count=0)
            db.add(nc)
            await db.commit()
            await db.refresh(nc)
            chapters_by_num[num] = nc

    prev_summary = ""
    for num in range(start, end + 1):
        ch = chapters_by_num[num]
        if data.skip_existing and ch.content:
            items.append(MultiWriteItem(chapter_id=ch.id, number=num, title=ch.title,
                                        word_count=ch.word_count, status="skipped"))
            prev_summary = (ch.content or "")[-600:]
            continue

        outline_node = {}
        for vol in outline.get("volumes", []) or []:
            for c in vol.get("chapters", []) or []:
                if int(c.get("number", 0)) == num:
                    outline_node = c
                    break

        # 复用 build_write_context：注入 设定(角色/场景/物品/情节) + RAG 记忆检索
        ctx = await build_write_context(u.id, bid, ch.id, db)
        ctx["chapter_meta"] = {
            "id": ch.id, "number": num, "title": ch.title,
            "per_chapter_words": b.per_chapter_words,
        }
        ctx["outline_node"] = outline_node
        ctx["prev_chapter_summary"] = prev_summary
        input_state = {
            "user_id": u.id, "book_id": bid, "chapter_id": ch.id,
            "thread_id": thread_id,
            "messages": [{"role": "user", "content": f"请撰写第{num}章 {ch.title}"}],
            "model_choice": mc, "user_memory": user_mem,
            "context": ctx,
            "current_content": "",
        }
        try:
            final = await run_agent(input_state, thread_id)
            content = final.get("draft_content", "") or ""
            if not content:
                items.append(MultiWriteItem(chapter_id=ch.id, number=num, title=ch.title,
                                            word_count=0, status="error",
                                            error=final.get("error", "未返回内容")))
                continue
            wc = count_words(content)
            ch.content = content
            ch.word_count = wc
            if ch.title.endswith("待定") and outline_node.get("title"):
                ch.title = outline_node["title"]
            await db.commit()
            # 后台同步：从本章内容提取并更新 角色/场景/物品/情节 设定
            from ..services.setting_sync import launch as launch_setting_sync
            launch_setting_sync(bid, ch.id, u.id, mc)
            prev_summary = content[-600:]
            tu = final.get("token_usage") or {}
            ti, to = int(tu.get("in_tokens", 0)), int(tu.get("out_tokens", 0))
            model_id = tu.get("model_id", "") or model_id
            total_in += ti
            total_out += to
            items.append(MultiWriteItem(chapter_id=ch.id, number=num, title=ch.title,
                                        word_count=wc, status="generated"))
        except Exception as e:
            items.append(MultiWriteItem(chapter_id=ch.id, number=num, title=ch.title,
                                        word_count=0, status="error", error=str(e)))

    # 批量积分扣减
    u2 = await db.get(User, u.id)
    cost = 0
    if u2.version == "business" and model_id:
        cost = pricing_svc.compute_cost(model_id, total_in, total_out)
        u2.credits_balance -= cost
        db.add(CreditsLedger(user_id=u2.id, delta=-cost, reason="multi-write", model=model_id,
                             in_tokens=total_in, out_tokens=total_out))
    summary = f"[批量生成] 第{start}-{end}章：" + ", ".join(
        f"第{it.number}章{it.status}" for it in items)
    am = Message(user_id=u2.id, thread_id=thread_id, role="assistant", content=summary,
                 model=model_id, in_tokens=total_in, out_tokens=total_out, credits_cost=cost)
    db.add(am)
    await db.commit()
    await db.refresh(am)

    return MultiWriteOut(
        book_id=bid, chapters=items, model=model_id,
        total_in_tokens=total_in, total_out_tokens=total_out,
        total_credits_cost=cost, thread_id=thread_id,
    )


# ============ 4. 分析 skill ============

@router.post("/books/{bid}/analyze", response_model=AnalyzeOut)
async def analyze_book(
    bid: int, data: AnalyzeIn,
    u: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """分析 skill 统一入口：plot/character/consistency/summary/outline。"""
    b = await db.get(Book, bid)
    if not b or b.user_id != u.id:
        raise HTTPException(404, "书籍不存在")

    valid_skills = {"plot-planning", "character-development", "consistency-check",
                    "book-summary", "outline-planning"}
    if data.skill not in valid_skills:
        raise HTTPException(400, f"未知分析 skill: {data.skill}，可选：{valid_skills}")

    thread_id = data.thread_id or uuid.uuid4().hex
    um = Message(user_id=u.id, thread_id=thread_id, role="user",
                 content=f"[{data.skill}] 书籍 {bid}" +
                         (f" 角色：{data.character_name}" if data.character_name else "") +
                         (f" 范围：{data.chapter_range}" if data.chapter_range else ""))
    db.add(um)
    await db.commit()
    await db.refresh(um)

    mc = _model_choice(u, data.llm_choice)
    user_mem = await load_user_memory(u.id, db)
    book_meta = await _load_book_meta(db, bid, u)
    outline = await _load_outline(db, bid)

    # 加载章节内容摘要（consistency-check / book-summary 需要）
    chapters_brief = ""
    if data.skill in {"consistency-check", "book-summary"}:
        cr = data.chapter_range or {"start": 1, "end": 10}
        rs = await db.scalars(select(Chapter).where(
            Chapter.book_id == bid,
            Chapter.number >= int(cr.get("start", 1)),
            Chapter.number <= int(cr.get("end", 10)),
        ).order_by(Chapter.number))
        parts = []
        for c in rs:
            if c.content:
                txt = re.sub(r"<[^>]+>", "", c.content)
                txt = re.sub(r"\s+", "", txt)
                parts.append(f"第{c.number}章 {c.title}：{txt[:300]}")
        chapters_brief = "\n\n".join(parts)[:4000] or "（无章节内容）"

    input_state = {
        "user_id": u.id, "book_id": bid, "chapter_id": None,
        "thread_id": thread_id,
        "messages": [{"role": "user", "content": um.content}],
        "model_choice": mc, "user_memory": user_mem,
        "context": {
            "book_meta": book_meta,
            "outline": outline,
            "chapters_brief": chapters_brief,
            "character_name": data.character_name or book_meta.get("protagonist_name", ""),
            "character_intro": book_meta.get("protagonist_intro", ""),
            "chapter_range": data.chapter_range or {},
        },
        "active_skill": data.skill,
        "chapter_range": data.chapter_range or {},
        "intent": "analyze",
    }
    final = await run_agent(input_state, thread_id)

    report = final.get("analysis_report", "") or ""
    if not report:
        raise HTTPException(500, f"分析失败：{final.get('error', '未返回报告')}")
    tu = final.get("token_usage") or {}
    in_t, out_t = int(tu.get("in_tokens", 0)), int(tu.get("out_tokens", 0))
    model_id = tu.get("model_id", "") or ""

    am, cost = await _save_assistant_msg(db, u, thread_id, report, model_id, in_t, out_t, um.id)
    return AnalyzeOut(report=report, model=model_id, in_tokens=in_t, out_tokens=out_t,
                      credits_cost=cost, thread_id=thread_id, message_id=am.id)


# ============ P1-8 辅助 skill ============

@router.post("/assist/brainstorm", response_model=AssistOut)
async def assist_brainstorm(
    data: BrainstormIn,
    u: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """brainstorm skill：头脑风暴生成创意建议。"""
    thread_id = data.thread_id or uuid.uuid4().hex
    um = Message(user_id=u.id, thread_id=thread_id, role="user",
                 content=f"[头脑风暴] {data.topic}")
    db.add(um)
    await db.commit()
    await db.refresh(um)

    mc = _model_choice(u, data.llm_choice)
    user_mem = await load_user_memory(u.id, db)

    input_state = {
        "user_id": u.id, "book_id": None, "chapter_id": None,
        "thread_id": thread_id,
        "messages": [{"role": "user", "content": f"主题：{data.topic}\n方向：{data.direction or '不限'}"}],
        "model_choice": mc, "user_memory": user_mem,
        "context": {"count": data.count, "genre": data.genre, "direction": data.direction},
        "active_skill": "brainstorm", "intent": "assist",
    }
    final = await run_agent(input_state, thread_id)
    content = final.get("draft_content", "") or ""
    if not content:
        raise HTTPException(500, f"头脑风暴失败：{final.get('error', '未返回内容')}")
    tu = final.get("token_usage") or {}
    in_t, out_t = int(tu.get("in_tokens", 0)), int(tu.get("out_tokens", 0))
    model_id = tu.get("model_id", "") or ""
    am, cost = await _save_assistant_msg(db, u, thread_id, content, model_id, in_t, out_t, um.id)
    return AssistOut(content=content, model=model_id, in_tokens=in_t, out_tokens=out_t,
                     credits_cost=cost, thread_id=thread_id, message_id=am.id)


@router.post("/assist/title-generation", response_model=AssistOut)
async def assist_title_generation(
    data: TitleGenIn,
    u: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """title-generation skill：生成候选标题列表。"""
    thread_id = data.thread_id or uuid.uuid4().hex
    um = Message(user_id=u.id, thread_id=thread_id, role="user",
                 content=f"[标题生成] {data.target} 风格={data.style}")
    db.add(um)
    await db.commit()
    await db.refresh(um)

    mc = _model_choice(u, data.llm_choice)
    user_mem = await load_user_memory(u.id, db)
    user_msg = f"请生成{data.count}个{data.style}风格{data.target}标题"
    if data.content:
        user_msg += f"\n内容摘要：{data.content[:500]}"
    if data.keywords:
        user_msg += f"\n关键词：{', '.join(data.keywords)}"

    input_state = {
        "user_id": u.id, "book_id": None, "chapter_id": None,
        "thread_id": thread_id,
        "messages": [{"role": "user", "content": user_msg}],
        "model_choice": mc, "user_memory": user_mem,
        "context": {"count": data.count, "style": data.style, "target": data.target},
        "active_skill": "title-generation", "intent": "assist",
    }
    final = await run_agent(input_state, thread_id)
    content = final.get("draft_content", "") or ""
    if not content:
        raise HTTPException(500, f"标题生成失败：{final.get('error', '未返回内容')}")
    tu = final.get("token_usage") or {}
    in_t, out_t = int(tu.get("in_tokens", 0)), int(tu.get("out_tokens", 0))
    model_id = tu.get("model_id", "") or ""
    am, cost = await _save_assistant_msg(db, u, thread_id, content, model_id, in_t, out_t, um.id)
    return AssistOut(content=content, model=model_id, in_tokens=in_t, out_tokens=out_t,
                     credits_cost=cost, thread_id=thread_id, message_id=am.id)


@router.post("/assist/scene-enhance", response_model=AssistOut)
async def assist_scene_enhance(
    data: SceneEnhanceIn,
    u: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """scene-enhance skill：场景增强。"""
    if not data.scene_text.strip():
        raise HTTPException(400, "场景文本不能为空")
    thread_id = data.thread_id or uuid.uuid4().hex
    um = Message(user_id=u.id, thread_id=thread_id, role="user",
                 content=f"[场景增强] {data.scene_text[:80]}...")
    db.add(um)
    await db.commit()
    await db.refresh(um)

    mc = _model_choice(u, data.llm_choice)
    user_mem = await load_user_memory(u.id, db)

    input_state = {
        "user_id": u.id, "book_id": None, "chapter_id": None,
        "thread_id": thread_id,
        "messages": [{"role": "user", "content": "请增强以下场景"}],
        "model_choice": mc, "user_memory": user_mem,
        "context": {"senses": data.senses, "mood": data.mood, "pov": data.pov,
                    "preserve_length": data.preserve_length},
        "scene_text": data.scene_text,
        "active_skill": "scene-enhance", "intent": "assist",
    }
    final = await run_agent(input_state, thread_id)
    content = final.get("draft_content", "") or ""
    if not content:
        raise HTTPException(500, f"场景增强失败：{final.get('error', '未返回内容')}")
    tu = final.get("token_usage") or {}
    in_t, out_t = int(tu.get("in_tokens", 0)), int(tu.get("out_tokens", 0))
    model_id = tu.get("model_id", "") or ""
    am, cost = await _save_assistant_msg(db, u, thread_id, content, model_id, in_t, out_t, um.id)
    return AssistOut(content=content, model=model_id, in_tokens=in_t, out_tokens=out_t,
                     credits_cost=cost, thread_id=thread_id, message_id=am.id)


@router.post("/assist/dialogue-polish", response_model=AssistOut)
async def assist_dialogue_polish(
    data: DialoguePolishIn,
    u: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """dialogue-polish skill：对话润色。"""
    if not data.dialogue_text.strip():
        raise HTTPException(400, "对话文本不能为空")
    thread_id = data.thread_id or uuid.uuid4().hex
    um = Message(user_id=u.id, thread_id=thread_id, role="user",
                 content=f"[对话润色] goal={data.goal} {data.dialogue_text[:80]}...")
    db.add(um)
    await db.commit()
    await db.refresh(um)

    mc = _model_choice(u, data.llm_choice)
    user_mem = await load_user_memory(u.id, db)

    input_state = {
        "user_id": u.id, "book_id": None, "chapter_id": None,
        "thread_id": thread_id,
        "messages": [{"role": "user", "content": "请润色以下对话"}],
        "model_choice": mc, "user_memory": user_mem,
        "context": {"characters": data.characters, "goal": data.goal, "preserve_info": data.preserve_info},
        "dialogue_text": data.dialogue_text,
        "active_skill": "dialogue-polish", "intent": "assist",
    }
    final = await run_agent(input_state, thread_id)
    content = final.get("draft_content", "") or ""
    if not content:
        raise HTTPException(500, f"对话润色失败：{final.get('error', '未返回内容')}")
    tu = final.get("token_usage") or {}
    in_t, out_t = int(tu.get("in_tokens", 0)), int(tu.get("out_tokens", 0))
    model_id = tu.get("model_id", "") or ""
    am, cost = await _save_assistant_msg(db, u, thread_id, content, model_id, in_t, out_t, um.id)
    return AssistOut(content=content, model=model_id, in_tokens=in_t, out_tokens=out_t,
                     credits_cost=cost, thread_id=thread_id, message_id=am.id)


@router.post("/assist/reading-config-gen", response_model=AssistOut)
async def assist_reading_config_gen(
    data: ReadingConfigGenIn,
    u: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """reading-config-gen skill：生成阅读配置JSON。"""
    thread_id = data.thread_id or uuid.uuid4().hex
    um = Message(user_id=u.id, thread_id=thread_id, role="user",
                 content=f"[阅读配置生成] scene={data.scene}")
    db.add(um)
    await db.commit()
    await db.refresh(um)

    mc = _model_choice(u, data.llm_choice)
    user_mem = await load_user_memory(u.id, db)

    input_state = {
        "user_id": u.id, "book_id": None, "chapter_id": None,
        "thread_id": thread_id,
        "messages": [{"role": "user", "content": f"场景：{data.scene}"}],
        "model_choice": mc, "user_memory": user_mem,
        "context": {"scene": data.scene, "user_prefs": data.user_prefs, "book_genre": data.book_genre},
        "active_skill": "reading-config-gen", "intent": "assist",
    }
    final = await run_agent(input_state, thread_id)
    content = final.get("draft_content", "") or ""
    if not content:
        raise HTTPException(500, f"阅读配置生成失败：{final.get('error', '未返回内容')}")
    tu = final.get("token_usage") or {}
    in_t, out_t = int(tu.get("in_tokens", 0)), int(tu.get("out_tokens", 0))
    model_id = tu.get("model_id", "") or ""
    am, cost = await _save_assistant_msg(db, u, thread_id, content, model_id, in_t, out_t, um.id)
    return AssistOut(content=content, model=model_id, in_tokens=in_t, out_tokens=out_t,
                     credits_cost=cost, thread_id=thread_id, message_id=am.id)
