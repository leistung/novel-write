"""P2-10 充值 API."""
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..core.deps import get_current_user
from ..database import get_db
from ..models import User, CreditsLedger
from ..services.configs import load_membership

router = APIRouter(prefix="/recharge", tags=["recharge"])


class PurchaseIn(BaseModel):
    membership_id: str


@router.get("/memberships")
async def list_memberships():
    cfg = load_membership()
    return cfg


@router.post("/purchase")
async def purchase(
    data: PurchaseIn,
    u: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cfg = load_membership()
    ms = [m for m in cfg.get("memberships", []) if m.get("id") == data.membership_id and m.get("enabled")]
    if not ms:
        raise HTTPException(400, f"未知或已下线的会员套餐: {data.membership_id}")
    m = ms[0]
    credits = int(m.get("bonus_credits", 0))
    # 占位支付：直接加积分
    u.credits_balance += credits
    ledger = CreditsLedger(user_id=u.id, delta=credits, reason=f"充值-{m['name']}", model="recharge")
    db.add(ledger)
    await db.commit()
    await db.refresh(u)
    return {"ok": True, "membership": m["name"], "credits_added": credits,
            "new_balance": u.credits_balance, "payment_status": "mock_paid"}


@router.get("/history")
async def recharge_history(
    u: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rs = await db.scalars(select(CreditsLedger).where(
        CreditsLedger.user_id == u.id, CreditsLedger.reason.like("充值%")
    ).order_by(CreditsLedger.created_at.desc()))
    return [{"id": r.id, "delta": r.delta, "reason": r.reason,
             "created_at": str(r.created_at) if r.created_at else None} for r in rs]
