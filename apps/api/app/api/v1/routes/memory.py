from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import db_session
from app.core.security import CurrentUser, get_current_user
from app.db.repositories.memory import MemoryRepository
from app.schemas.memory import MemoryCreate, MemoryRead, PreferenceRead, PreferenceUpsert

router = APIRouter()


@router.get("", response_model=list[MemoryRead])
async def list_memories(
    scope: str | None = None,
    session: AsyncSession = Depends(db_session),
    user: CurrentUser = Depends(get_current_user),
) -> list[MemoryRead]:
    memories = await MemoryRepository(session).list_memories(user.id, scope)
    return [MemoryRead.model_validate(memory) for memory in memories]


@router.post("", response_model=MemoryRead, status_code=201)
async def create_memory(
    payload: MemoryCreate,
    session: AsyncSession = Depends(db_session),
    user: CurrentUser = Depends(get_current_user),
) -> MemoryRead:
    memory = await MemoryRepository(session).add_memory(
        user_id=user.id,
        summary=payload.summary,
        content=payload.content,
        scope=payload.scope,
        tags=payload.tags,
    )
    await session.commit()
    return MemoryRead.model_validate(memory)


@router.get("/preferences", response_model=list[PreferenceRead])
async def list_preferences(
    session: AsyncSession = Depends(db_session),
    user: CurrentUser = Depends(get_current_user),
) -> list[PreferenceRead]:
    preferences = await MemoryRepository(session).list_preferences(user.id)
    return [PreferenceRead.model_validate(preference) for preference in preferences]


@router.put("/preferences", response_model=PreferenceRead)
async def upsert_preference(
    payload: PreferenceUpsert,
    session: AsyncSession = Depends(db_session),
    user: CurrentUser = Depends(get_current_user),
) -> PreferenceRead:
    preference = await MemoryRepository(session).upsert_preference(user.id, payload.key, payload.value)
    await session.commit()
    return PreferenceRead.model_validate(preference)
