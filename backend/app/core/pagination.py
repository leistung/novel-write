"""统一分页约定。

- 请求侧：?page=1&page_size=20（page 从 1 开始，page_size 上限 100）
- 响应侧：{"items": [...], "total": N, "page": P, "page_size": S}

配合 SQLAlchemy 异步查询使用：

    async def list_x(page: PageParams = Depends(PageParams)):
        q = select(X).where(...).order_by(...)
        total = await db.scalar(select(func.count()).select_from(q.subquery())) or 0
        rows = await db.scalars(q.offset(page.offset()).limit(page.page_size))
        return page_payload(rows.all(), total, page)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from fastapi import Query


@dataclass
class PageParams:
    page: int
    page_size: int

    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    def __init__(
        self,
        page: int = Query(1, ge=1, description="页码，从 1 开始"),
        page_size: int = Query(20, ge=1, le=100, description="每页条数，最大 100"),
    ) -> None:
        self.page = page
        self.page_size = page_size


def page_payload(items: list[Any], total: int, page: PageParams) -> dict:
    return {
        "items": items,
        "total": int(total),
        "page": page.page,
        "page_size": page.page_size,
    }
