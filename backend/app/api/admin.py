"""P2-10 后台管理 API."""
from __future__ import annotations
import yaml
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from ..core.admin import get_admin_user
from ..database import get_db
from ..models import User, CreditsLedger
from ..config import settings

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users")
async def list_users(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    rs = await db.scalars(select(User).order_by(User.id))
    return [{"id": u.id, "username": u.username, "version": u.version,
             "credits_balance": u.credits_balance, "is_admin": u.is_admin,
             "created_at": str(u.created_at) if u.created_at else None} for u in rs]


@router.get("/credits-report")
async def credits_report(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    # 按用户聚合
    by_user = await db.execute(
        select(CreditsLedger.user_id,
               func.sum(CreditsLedger.delta).label("total_delta"),
               func.count().label("tx_count"))
        .group_by(CreditsLedger.user_id).order_by(func.sum(CreditsLedger.delta)))
    # 按模型聚合
    by_model = await db.execute(
        select(CreditsLedger.model,
               func.sum(CreditsLedger.delta).label("total_delta"),
               func.count().label("tx_count"))
        .group_by(CreditsLedger.model))
    return {
        "by_user": [{"user_id": r[0], "total_delta": r[1], "tx_count": r[2]} for r in by_user],
        "by_model": [{"model": r[0] or "N/A", "total_delta": r[1], "tx_count": r[2]} for r in by_model],
    }


@router.get("/pricing")
async def get_pricing(admin: User = Depends(get_admin_user)):
    p = Path(settings.configs_dir) / "pricing.yaml"
    if not p.exists():
        raise HTTPException(404, "pricing.yaml 不存在")
    return yaml.safe_load(p.read_text("utf-8"))


@router.put("/pricing")
async def update_pricing(data: dict, admin: User = Depends(get_admin_user)):
    p = Path(settings.configs_dir) / "pricing.yaml"
    p.write_text(yaml.dump(data, allow_unicode=True, default_flow_style=False), "utf-8")
    return {"ok": True}


@router.get("/membership")
async def get_membership(admin: User = Depends(get_admin_user)):
    p = Path(settings.configs_dir) / "membership.yaml"
    if not p.exists():
        raise HTTPException(404, "membership.yaml 不存在")
    return yaml.safe_load(p.read_text("utf-8"))


@router.put("/membership")
async def update_membership(data: dict, admin: User = Depends(get_admin_user)):
    p = Path(settings.configs_dir) / "membership.yaml"
    p.write_text(yaml.dump(data, allow_unicode=True, default_flow_style=False), "utf-8")
    return {"ok": True}
