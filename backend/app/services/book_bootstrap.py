"""创建书后的后台初始化生成：大纲 / 情节 / 角色。

在 create_book 后由 asyncio.create_task 触发，使用独立 DB session，
不阻塞创建接口响应。每个生成项独立 try/except，单项失败不影响其余。
"""
from __future__ import annotations

import asyncio
import json
import logging

from sqlalchemy import select

from storyclaw._util import llm_respond
from storyclaw.prompts import ANALYST_PLOT_SYSTEM

from ..database import AsyncSessionLocal
from ..models import Book, ConfigEntity, Outline, User

log = logging.getLogger("storyclaw.bootstrap")

_BOOTSTRAP_CHARACTER_SYSTEM = """你是网文角色设定师。基于书籍信息为主角、核心配角、关键反派生成角色卡。
输出严格 JSON 数组，每个元素：
{{"name":"角色名","category":"主角|配角|反派","description":"80-150字角色概述","extra":{{"identity":"身份","personality":"性格特点","background":"背景身世","relation":"与其他角色关系"}}}}
规则：
- 主角必须包含，其余角色 3-6 个
- 角色名字与提供的保持一致，不重复
- 只输出 JSON 数组，不带任何其他文字

【书名】{title}
【类型】{genre}
【简介】{intro}
【主角】{protagonist_name}
【主角介绍】{protagonist_intro}
"""


def _model_choice_for(user: User) -> dict:
    if user.version == "business":
        return {"kind": "business", "model_id": "gpt-4o-mini"}
    return {"kind": "local", "user_id": user.id}


def launch(book_id: int, user_id: int, flags: dict) -> None:
    """后台启动（幂等：只跑勾选项）。"""
    if not any([flags.get("generate_outline"), flags.get("generate_plots"), flags.get("generate_characters")]):
        return
    asyncio.get_event_loop().create_task(_run(book_id, user_id, flags))


async def _run(book_id: int, user_id: int, flags: dict) -> None:
    if flags.get("generate_outline"):
        try:
            await _gen_outline(book_id, user_id)
        except Exception as e:  # noqa: BLE001
            log.warning("bootstrap outline failed book=%s: %s", book_id, e)
    if flags.get("generate_plots"):
        try:
            await _gen_plots(book_id, user_id)
        except Exception as e:  # noqa: BLE001
            log.warning("bootstrap plots failed book=%s: %s", book_id, e)
    if flags.get("generate_characters"):
        try:
            await _gen_characters(book_id, user_id)
        except Exception as e:  # noqa: BLE001
            log.warning("bootstrap characters failed book=%s: %s", book_id, e)


async def _load(book_id: int, user_id: int):
    """返回 (book, user, model_choice)。"""
    async with AsyncSessionLocal() as db:
        book = await db.get(Book, book_id)
        user = await db.get(User, user_id)
        return book, user


async def _gen_outline(book_id: int, user_id: int) -> None:
    """复用大纲工作流生成大纲（与 /outline/generate 同逻辑）。"""
    from storyclaw.graph import outline_graph
    async with AsyncSessionLocal() as db:
        book = await db.get(Book, book_id)
        if not book:
            return
        meta = {
            "title": book.title, "intro": book.intro or "", "genre": book.genre,
            "protagonist_name": book.protagonist_name or "",
            "protagonist_intro": book.protagonist_intro or "",
            "target_chapters": book.target_chapters, "target_words": book.target_words,
            "per_chapter_words": book.per_chapter_words,
        }
    result = await outline_graph.ainvoke({"book_meta": meta})
    outline = result.get("outline") or {}
    if not outline:
        return
    async with AsyncSessionLocal() as db:
        existing = await db.scalar(select(Outline).where(Outline.book_id == book_id))
        if existing:
            existing.content = json.dumps(outline, ensure_ascii=False)
        else:
            db.add(Outline(book_id=book_id, content=json.dumps(outline, ensure_ascii=False)))
        await db.commit()
    log.info("bootstrap outline ok book=%s", book_id)


async def _gen_plots(book_id: int, user_id: int) -> None:
    """用 analyst plot skill 生成每章情节节点，存为 plot ConfigEntity。"""
    async with AsyncSessionLocal() as db:
        book = await db.get(Book, book_id)
        user = await db.get(User, user_id)
        if not book or not user:
            return
        outline_row = await db.scalar(select(Outline).where(Outline.book_id == book_id))
        outline = {}
        if outline_row and outline_row.content:
            try:
                outline = json.loads(outline_row.content)
            except Exception:
                outline = {}
        mc = _model_choice_for(user)
        book_meta = {
            "title": book.title, "genre": book.genre, "intro": book.intro or "",
            "target_chapters": book.target_chapters, "target_words": book.target_words,
        }
    if not outline:
        log.info("bootstrap plots skip (no outline) book=%s", book_id)
        return
    sys_prompt = ANALYST_PLOT_SYSTEM.format(
        outline=json.dumps(outline, ensure_ascii=False),
        book_meta=json.dumps(book_meta, ensure_ascii=False),
    )
    content, _, _, _ = await llm_respond(
        {"model_choice": mc}, sys_prompt, "请根据大纲为每章规划情节节点"
    )
    data = _parse_json(content)
    if not data:
        return
    plots = []
    for ch in (data.get("chapters") or []):
        num = ch.get("number")
        for beat in (ch.get("beats") or []):
            name = beat.get("name") or f"第{num}章情节点"
            plots.append({
                "name": f"第{num}章·{name}",
                "category": "主线" if ch.get("main_line") else "支线",
                "description": beat.get("content", ""),
                "extra": {"chapter": num, "main_line": ch.get("main_line", ""),
                          "sub_lines": ch.get("sub_lines", [])},
            })
    # 伏笔也作为情节实体
    for f in (data.get("foreshadowing") or []):
        plots.append({
            "name": f"伏笔·{f.get('id', '')}",
            "category": "伏笔",
            "description": f.get("description", ""),
            "extra": {"planted_at": f.get("planted_at"), "resolved_at": f.get("resolved_at")},
        })
    await _upsert_entities(book_id, "plot", plots)


async def _gen_characters(book_id: int, user_id: int) -> None:
    async with AsyncSessionLocal() as db:
        book = await db.get(Book, book_id)
        user = await db.get(User, user_id)
        if not book or not user:
            return
        mc = _model_choice_for(user)
        sys_prompt = _BOOTSTRAP_CHARACTER_SYSTEM.format(
            title=book.title, genre=book.genre, intro=book.intro or "",
            protagonist_name=book.protagonist_name or "（未指定）",
            protagonist_intro=book.protagonist_intro or "（未提供）",
        )
    content, _, _, _ = await llm_respond(
        {"model_choice": mc}, sys_prompt, "请生成该书的角色卡"
    )
    data = _parse_json(content)
    if not isinstance(data, list):
        log.warning("bootstrap characters parse fail book=%s content=%s", book_id, (content or "")[:300])
        return
    chars = []
    for c in data:
        if not isinstance(c, dict) or not c.get("name"):
            continue
        chars.append({
            "name": c["name"],
            "category": c.get("category", "配角"),
            "description": c.get("description", ""),
            "extra": c.get("extra") or {},
        })
    await _upsert_entities(book_id, "character", chars)


async def _upsert_entities(book_id: int, entity_type: str, items: list[dict]) -> None:
    """按 (book_id, entity_type, name) 唯一 upsert ConfigEntity。"""
    async with AsyncSessionLocal() as db:
        for it in items:
            name = (it.get("name") or "").strip()
            if not name:
                continue
            existing = await db.scalar(select(ConfigEntity).where(
                ConfigEntity.book_id == book_id,
                ConfigEntity.entity_type == entity_type,
                ConfigEntity.name == name,
            ))
            if existing:
                existing.description = it.get("description", existing.description)
                existing.category = it.get("category", existing.category)
                existing.extra_json = it.get("extra") or existing.extra_json
            else:
                db.add(ConfigEntity(
                    book_id=book_id, entity_type=entity_type,
                    name=name, category=it.get("category", ""),
                    description=it.get("description", ""),
                    extra_json=it.get("extra") or None,
                ))
        await db.commit()
    log.info("bootstrap upsert %s x%d book=%s", entity_type, len(items), book_id)


def _parse_json(text: str) -> dict | list | None:
    t = text.strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    try:
        return json.loads(t)
    except Exception:
        # 尝试截取 [] 或 {} 块
        import re
        for ch in ("[", "{"):
            if ch in t:
                try:
                    s = t[t.index(ch):]
                    # 平衡括号截取
                    depth = 0
                    for i, cc in enumerate(s):
                        if cc in "[{":
                            depth += 1
                        elif cc in "]}":
                            depth -= 1
                            if depth == 0:
                                return json.loads(s[:i + 1])
                except Exception:
                    continue
    return None
