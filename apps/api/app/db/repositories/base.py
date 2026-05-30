from collections.abc import Sequence
from typing import Generic, TypeVar

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class Repository(Generic[ModelT]):
    def __init__(self, session: AsyncSession, model: type[ModelT]) -> None:
        self.session = session
        self.model = model

    async def get(self, item_id: str) -> ModelT | None:
        return await self.session.get(self.model, item_id)

    async def list(self, statement: Select[tuple[ModelT]] | None = None) -> Sequence[ModelT]:
        result = await self.session.scalars(statement or select(self.model))
        return result.all()

    async def add(self, instance: ModelT) -> ModelT:
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def delete(self, instance: ModelT) -> None:
        await self.session.delete(instance)
        await self.session.flush()
