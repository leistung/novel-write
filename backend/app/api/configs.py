from fastapi import APIRouter, Depends

from ..core.deps import get_current_user
from ..models import User
from ..services.configs import load_models, load_pricing

router = APIRouter(prefix="", tags=["configs"])


@router.get("/models")
async def list_models(u: User = Depends(get_current_user)):
    data = load_models()
    return [m for m in data.get("models", []) if m.get("enabled")]


@router.get("/pricing")
async def get_pricing(u: User = Depends(get_current_user)):
    return load_pricing()
