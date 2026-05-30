from fastapi import APIRouter

from app.api.v1.routes import agents, chat, health, knowledge, memory, models, tools

router = APIRouter()
router.include_router(health.router, tags=["health"])
router.include_router(chat.router, prefix="/chat", tags=["chat"])
router.include_router(memory.router, prefix="/memory", tags=["memory"])
router.include_router(knowledge.router, prefix="/knowledge", tags=["knowledge"])
router.include_router(agents.router, prefix="/agents", tags=["agents"])
router.include_router(tools.router, prefix="/tools", tags=["tools"])
router.include_router(models.router, prefix="/models", tags=["models"])
