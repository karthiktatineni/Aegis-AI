from fastapi import APIRouter

from app.core.config import get_settings
from app.schemas.common import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        version="0.1.0",
        capabilities={
            "streaming": True,
            "rag": True,
            "memory": True,
            "agents": True,
            "local_llm": settings.llm_provider.lower() == "transformers",
        },
    )
