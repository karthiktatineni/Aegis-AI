from fastapi import APIRouter

from app.core.quota import QuotaStatus, get_quota_manager

router = APIRouter()


@router.get("", response_model=QuotaStatus)
async def get_quota() -> QuotaStatus:
    """Return the current daily request quota and usage for today."""
    return get_quota_manager().get_status()
