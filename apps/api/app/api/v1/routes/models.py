from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter()


@router.get("")
async def model_status() -> dict:
    settings = get_settings()
    return {
        "provider": settings.llm_provider,
        "local_model_id": settings.local_model_id,
        "embedding_model": settings.local_embedding_model,
        "device": settings.model_device,
        "supported": [
            "mistralai/Mistral-7B-Instruct-v0.3",
            "Qwen/Qwen2.5-7B-Instruct",
            "meta-llama/Meta-Llama-3-8B-Instruct",
            "google/gemma-7b-it",
        ],
    }
