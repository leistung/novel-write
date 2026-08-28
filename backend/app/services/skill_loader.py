"""Context Loader（backend 数据层）：为 write-chapter skill 构造写作上下文。

纯工具（字数 / 摘要 / 大纲定位）统一在 packages/storyclaw/src/storyclaw/context.py；
本模块只负责从 DB 读取章节 / 书籍 / 大纲，组装 context dict 后交给 agent 包。
"""
from __future__ import annotations

import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from storyclaw.context import find_outline_node, summarize_prev  # noqa: F401（agent 包内纯工具）

from ..models import Book, Chapter, ConfigEntity, Outline


def _entity_brief(rows, limit: int = 12) -> str:
    """把配置实体压缩成可注入 prompt 的摘要文本。"""
    if not rows:
        return ""
    parts = []
    for r in rows:
        extra = ""
        if r.extra_json:
            try:
                extra = "，" + "、".join(f"{k}:{v}" for k, v in (r.extra_json.items() if isinstance(r.extra_json, dict) else []))[:200]
            except Exception:
                extra = ""
        desc = (r.description or "").strip()
        line = f"- {r.name}"
        if r.category:
            line += f"（{r.category}）"
        if desc:
            line += f"：{desc[:200]}"
        line += extra
        parts.append(line)
    return "\n".join(parts[:limit])


async def build_write_context(user_id: int, book_id: int, chapter_id: int, db: AsyncSession) -> dict[str, Any]:
    """构造 write-chapter skill 的 context 字典。

    返回 {"chapter_meta":..., "outline_node":..., "prev_chapter_summary":...,
           "setting_briefs": {characters,scenes,items,plots}, "rag_briefs": "..."}
    """
    chapter = await db.get(Chapter, chapter_id)
    if not chapter or chapter.book_id != book_id:
        return {}
    book = await db.get(Book, book_id)
    if not book:
        return {}

    # 大纲
    outline_row = await db.scalar(select(Outline).where(Outline.book_id == book_id))
    outline_content: dict = {}
    if outline_row and outline_row.content:
        try:
            outline_content = json.loads(outline_row.content)
        except Exception:
            outline_content = {}
    outline_node = find_outline_node(outline_content, chapter.number)

    # 本书设定：角色 / 场景 / 物品 / 情节（供 writer 保持一致性与呼应）
    setting_rows = {
        et: list(await db.scalars(select(ConfigEntity).where(
            ConfigEntity.book_id == book_id, ConfigEntity.entity_type == et
        ).order_by(ConfigEntity.sort_order, ConfigEntity.id)))
        for et in ("character", "scene", "item", "plot")
    }
    setting_briefs = {
        "characters": _entity_brief(setting_rows["character"]),
        "scenes": _entity_brief(setting_rows["scene"]),
        "items": _entity_brief(setting_rows["item"]),
        "plots": _entity_brief(setting_rows["plot"]),
    }

    # 前章摘要（复用 agent 包纯工具）
    prev_summary = ""
    if chapter.number > 1:
        prev = await db.scalar(select(Chapter).where(
            Chapter.book_id == book_id, Chapter.number == chapter.number - 1
        ))
        if prev:
            prev_summary = summarize_prev(prev.content or "")

    chapter_meta = {
        "id": chapter.id,
        "number": chapter.number,
        "title": chapter.title,
        "per_chapter_words": book.per_chapter_words,
    }

    # 本书记忆检索（向量 + 图谱）：以本章大纲节点 + 章节标题为查询，召回相关切片与实体关系。
    # RAG 不可用时降级为空串，不影响写作。
    rag_briefs = ""
    try:
        from storyclaw.rag.service import query_context
        q_parts = []
        if outline_node.get("title"):
            q_parts.append(outline_node["title"])
        if outline_node.get("summary"):
            q_parts.append(str(outline_node["summary"])[:200])
        q_parts.append(chapter.title)
        query = " ".join(x for x in q_parts if x)[:300] or chapter.title
        rag = await query_context(user_id, book_id, query, top_k=5)
        if not rag.get("error"):
            chunks = rag.get("chunks") or []
            ents = rag.get("entities") or []
            rels = rag.get("relations") or []
            parts = []
            if chunks:
                parts.append("【相关片段】")
                for c in chunks[:4]:
                    t = (c.get("text") or "").strip().replace("\n", " ")
                    if t:
                        parts.append(f"- 第{c.get('chapter_id','?')}章: {t[:300]}")
            if ents:
                parts.append("【相关实体】")
                parts.append("、".join(
                    f"{e.get('name','')}({e.get('type','')})" for e in ents[:12]
                ))
            if rels:
                parts.append("【实体关系】")
                for r in rels[:10]:
                    parts.append(f"- {r.get('from','')} {r.get('type','')} {r.get('to','')}")
            rag_briefs = "\n".join(parts)
    except Exception:
        rag_briefs = ""

    return {
        "chapter_meta": chapter_meta,
        "outline_node": outline_node,
        "prev_chapter_summary": prev_summary,
        "setting_briefs": setting_briefs,
        "rag_briefs": rag_briefs,
    }
