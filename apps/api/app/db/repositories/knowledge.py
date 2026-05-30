from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.repositories.base import Repository
from app.models import Document, DocumentChunk, KnowledgeCollection


class KnowledgeRepository(Repository[KnowledgeCollection]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, KnowledgeCollection)

    async def list_collections(self, user_id: str) -> Sequence[KnowledgeCollection]:
        statement = (
            select(KnowledgeCollection)
            .where(KnowledgeCollection.user_id == user_id)
            .options(selectinload(KnowledgeCollection.documents))
            .order_by(KnowledgeCollection.updated_at.desc())
        )
        result = await self.session.scalars(statement)
        return result.unique().all()

    async def get_collection(self, collection_id: str, user_id: str) -> KnowledgeCollection | None:
        statement = select(KnowledgeCollection).where(
            KnowledgeCollection.id == collection_id, KnowledgeCollection.user_id == user_id
        )
        return await self.session.scalar(statement)

    async def create_collection(
        self, user_id: str, name: str, description: str | None = None, tags: list[str] | None = None
    ) -> KnowledgeCollection:
        collection = KnowledgeCollection(
            user_id=user_id,
            name=name,
            description=description,
            tags=tags or [],
        )
        self.session.add(collection)
        await self.session.flush()
        return collection

    async def add_document(
        self,
        collection_id: str,
        filename: str,
        content_type: str | None,
        storage_path: str,
        checksum: str,
        tags: list[str] | None = None,
        metadata: dict | None = None,
    ) -> Document:
        document = Document(
            collection_id=collection_id,
            filename=filename,
            content_type=content_type,
            storage_path=storage_path,
            checksum=checksum,
            tags=tags or [],
            metadata_json=metadata or {},
        )
        self.session.add(document)
        await self.session.flush()
        return document

    async def add_chunks(self, chunks: list[DocumentChunk]) -> list[DocumentChunk]:
        self.session.add_all(chunks)
        await self.session.flush()
        return chunks
