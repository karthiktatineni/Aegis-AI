from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.base import Repository
from app.models import Memory, UserPreference


class MemoryRepository(Repository[Memory]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Memory)

    async def list_memories(self, user_id: str, scope: str | None = None) -> Sequence[Memory]:
        statement = select(Memory).where(Memory.user_id == user_id).order_by(Memory.updated_at.desc())
        if scope:
            statement = statement.where(Memory.scope == scope)
        result = await self.session.scalars(statement)
        return result.all()

    async def add_memory(
        self,
        user_id: str,
        summary: str,
        content: str,
        scope: str = "long_term",
        embedding_id: str | None = None,
        tags: list[str] | None = None,
        metadata: dict | None = None,
    ) -> Memory:
        memory = Memory(
            user_id=user_id,
            summary=summary,
            content=content,
            scope=scope,
            embedding_id=embedding_id,
            tags=tags or [],
            metadata_json=metadata or {},
        )
        self.session.add(memory)
        await self.session.flush()
        return memory

    async def upsert_preference(self, user_id: str, key: str, value: str) -> UserPreference:
        statement = select(UserPreference).where(
            UserPreference.user_id == user_id, UserPreference.key == key
        )
        preference = await self.session.scalar(statement)
        if preference:
            preference.value = value
        else:
            preference = UserPreference(user_id=user_id, key=key, value=value)
            self.session.add(preference)
        await self.session.flush()
        return preference

    async def list_preferences(self, user_id: str) -> Sequence[UserPreference]:
        statement = select(UserPreference).where(UserPreference.user_id == user_id).order_by(
            UserPreference.key
        )
        result = await self.session.scalars(statement)
        return result.all()
