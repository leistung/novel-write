"""写章节后的设定动态同步：从本章正文提取并更新 角色/场景/物品/情节。

在章节生成落库后由后台任务触发，用 LLM 分析本章出现/变更的设定实体，
按 (book_id, entity_type, name) 唯一 upsert 到 ConfigEntity，使「一边写一边跟进设定」。
"""
from __future__ import annotations

import asyncio
import json
import logging
import re

from sqlalchemy import select

from storyclaw._util import llm_respond

from ..database import AsyncSessionLocal
from ..models import Chapter, ConfigEntity, User

log = logging.getLogger("storyclaw.setting_sync")

_SYNC_SYSTEM = """你是网文设定同步员。阅读本章正文，从中提取本章「新出现或发生重大变化」的角色、场景、物品、情节，输出严格 JSON：
{{"characters":[{{"name":"","category":"主角|配角|反派","description":"100字内概述","extra":{{"identity":"身份","personality":"性格特点","relation":"与其他角色关系"}}}}],"scenes":[{{"name":"","category":"室内|室外|幻想","description":"场景描写要点"}}],"items":[{{"name":"","category":"武器|道具|信物","description":"物品作用"}}],"plots":[{{"name":"","category":"主线|支线|伏笔","description":"本章情节推进或新埋设的伏笔"}}]}}

规则：
- 只提取本章明确出现或推进的实体，已存在但未变化的不要重复
- 描述聚焦本章新增信息，保持与既有设定一致
- 没有某类时给空数组
- 只输出 JSON，不带任何其他文字

【既有设定】
{existing}

【本章正文】
{chapter_text}
"""


def launch(book_id: int, chapter_id: int, user_id: int, model_choice: dict) -> None:
    """后台触发（幂等保护：仅当书里已有设定或本章有内容时执行）。"""
    asyncio.get_event_loop().create_task(_run(book_id, chapter_id, user_id, model_choice))


async def _run(book_id: int, chapter_id: int, user_id: int, model_choice: dict) -> None:
    try:
        await _sync(book_id, chapter_id, user_id, model_choice)
    except Exception as e:  # noqa: BLE001
        log.warning("setting sync failed book=%s ch=%s: %s", book_id, chapter_id, e)


async def _sync(book_id: int, chapter_id: int, user_id: int, model_choice: dict) -> None:
    async with AsyncSessionLocal() as db:
        chapter = await db.get(Chapter, chapter_id)
        user = await db.get(User, user_id)
        if not chapter or not chapter.content or not user:
            return
        # 章节纯文本
        text = re.sub(r"<[^>]+>", "", chapter.content)
        text = re.sub(r"\s+", " ", text).strip()
        if len(text) < 50:
            return
        # 既有设定
        existing_rows = list(await db.scalars(select(ConfigEntity).where(
            ConfigEntity.book_id == book_id
        ).order_by(ConfigEntity.entity_type)))
        existing_map: dict[str, list[str]] = {}
        for r in existing_rows:
            existing_map.setdefault(r.entity_type, []).append(
                f"{r.name}（{r.category}）：{(r.description or '')[:80]}"
            )
        existing = "\n".join(
            f"[{k}]\n" + "\n".join(v) for k, v in existing_map.items() if v
        ) or "（暂无设定）"

    mc = model_choice or {"kind": "local", "user_id": user_id}
    sys_prompt = _SYNC_SYSTEM.format(existing=existing[:3000], chapter_text=text[:4000])
    content, _, _, _ = await llm_respond({"model_choice": mc}, sys_prompt, "请提取本章设定变更")

    data = _parse_json(content)
    if not isinstance(data, dict):
        return

    async with AsyncSessionLocal() as db:
        for entity_type in ("characters", "scenes", "items", "plots"):
            type_key = {
                "characters": "character", "scenes": "scene",
                "items": "item", "plots": "plot",
            }[entity_type]
            for item in (data.get(entity_type) or []):
                if not isinstance(item, dict):
                    continue
                name = (item.get("name") or "").strip()
                if not name:
                    continue
                desc = (item.get("description") or "").strip()
                category = (item.get("category") or "").strip()
                extra = item.get("extra") or {}
                if not desc and not extra:
                    continue
                existing = await db.scalar(select(ConfigEntity).where(
                    ConfigEntity.book_id == book_id,
                    ConfigEntity.entity_type == type_key,
                    ConfigEntity.name == name,
                ))
                if existing:
                    # 追加新信息（不覆盖既有 description，避免丢失细节）
                    if desc:
                        existing.description = (existing.description + "\n" + desc).strip()[:2000]
                    if category:
                        existing.category = category
                    if isinstance(existing.extra_json, dict) and isinstance(extra, dict):
                        merged = {**existing.extra_json, **extra}
                        existing.extra_json = merged
                    elif extra:
                        existing.extra_json = extra
                else:
                    db.add(ConfigEntity(
                        book_id=book_id, entity_type=type_key, name=name,
                        category=category, description=desc, extra_json=extra or None,
                    ))
        await db.commit()
    log.info("setting sync ok book=%s ch=%s", book_id, chapter_id)


def _parse_json(text: str) -> dict | None:
    t = text.strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    if t.startswith("{"):
        try:
            return json.loads(t[: t.rindex("}") + 1])
        except Exception:
            pass
    m = re.search(r"\{.*\}", t, re.S)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            return None
    return None
