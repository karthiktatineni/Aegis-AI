import hashlib
import shutil
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.repositories.knowledge import KnowledgeRepository
from app.models import DocumentChunk
from app.schemas.chat import Citation
from app.services.ai.reranker import rerank
from app.services.rag.chunking import chunk_text
from app.services.rag.embeddings import get_embedding_service
from app.services.rag.loaders import load_document_text
from app.services.rag.vector_store import ChromaVectorStore, VectorRecord


class RAGService:
    def __init__(self, session: AsyncSession) -> None:
        self.settings = get_settings()
        self.repository = KnowledgeRepository(session)
        self.embedding_service = get_embedding_service()
        self._vector_store: ChromaVectorStore | None = None

    @property
    def vector_store(self) -> ChromaVectorStore:
        if self._vector_store is None:
            self._vector_store = ChromaVectorStore()
        return self._vector_store

    async def ingest_upload(
        self,
        collection_id: str,
        user_id: str,
        upload: UploadFile,
        tags: list[str] | None = None,
    ) -> dict:
        collection = await self.repository.get_collection(collection_id, user_id)
        if not collection:
            raise ValueError("Collection not found")

        upload_dir = Path(self.settings.upload_dir) / user_id / collection_id
        upload_dir.mkdir(parents=True, exist_ok=True)
        storage_path = upload_dir / upload.filename
        with storage_path.open("wb") as handle:
            shutil.copyfileobj(upload.file, handle)

        checksum = hashlib.sha256(storage_path.read_bytes()).hexdigest()
        text = load_document_text(storage_path, upload.content_type)
        chunks = chunk_text(text)
        document = await self.repository.add_document(
            collection_id=collection_id,
            filename=upload.filename,
            content_type=upload.content_type,
            storage_path=str(storage_path),
            checksum=checksum,
            tags=tags,
            metadata={"chunk_count": len(chunks)},
        )

        embeddings = self.embedding_service.embed([chunk.content for chunk in chunks])
        db_chunks: list[DocumentChunk] = []
        vector_records: list[VectorRecord] = []
        for chunk, embedding in zip(chunks, embeddings, strict=False):
            embedding_id = f"{document.id}:{chunk.index}"
            db_chunk = DocumentChunk(
                document_id=document.id,
                collection_id=collection_id,
                chunk_index=chunk.index,
                content=chunk.content,
                embedding_id=embedding_id,
                metadata_json=chunk.metadata,
            )
            db_chunks.append(db_chunk)
            vector_records.append(
                VectorRecord(
                    id=embedding_id,
                    content=chunk.content,
                    embedding=embedding,
                    metadata={
                        "document_id": document.id,
                        "filename": upload.filename,
                        "collection_id": collection_id,
                        "tags": ",".join(tags or []),
                        **chunk.metadata,
                    },
                )
            )

        await self.repository.add_chunks(db_chunks)
        self.vector_store.upsert(collection_id, vector_records)
        return {"document_id": document.id, "chunks": len(chunks), "checksum": checksum}

    async def search(
        self,
        query: str,
        collection_ids: list[str],
        tags: list[str] | None = None,
        limit: int = 8,
    ) -> list[Citation]:
        if not collection_ids:
            return []
        embedding = self.embedding_service.embed([query])[0]
        citations = self.vector_store.query(collection_ids, embedding, limit=limit * 2, tags=tags)
        return rerank(query, citations, limit=limit)
