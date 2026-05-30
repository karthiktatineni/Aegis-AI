from dataclasses import dataclass
from pathlib import Path

from app.core.config import get_settings
from app.schemas.chat import Citation


@dataclass(frozen=True)
class VectorRecord:
    id: str
    content: str
    embedding: list[float]
    metadata: dict


class ChromaVectorStore:
    def __init__(self) -> None:
        self.settings = get_settings()
        Path(self.settings.chroma_path).mkdir(parents=True, exist_ok=True)
        import chromadb

        self.client = chromadb.PersistentClient(path=self.settings.chroma_path)

    def _collection(self, collection_id: str):
        return self.client.get_or_create_collection(name=f"kb_{collection_id}")

    def upsert(self, collection_id: str, records: list[VectorRecord]) -> None:
        if not records:
            return
        collection = self._collection(collection_id)
        collection.upsert(
            ids=[record.id for record in records],
            documents=[record.content for record in records],
            embeddings=[record.embedding for record in records],
            metadatas=[record.metadata for record in records],
        )

    def query(
        self,
        collection_ids: list[str],
        query_embedding: list[float],
        limit: int = 8,
        tags: list[str] | None = None,
    ) -> list[Citation]:
        citations: list[Citation] = []
        for collection_id in collection_ids:
            collection = self._collection(collection_id)
            result = collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                include=["documents", "metadatas", "distances"],
            )
            ids = result.get("ids", [[]])[0]
            documents = result.get("documents", [[]])[0]
            metadatas = result.get("metadatas", [[]])[0]
            distances = result.get("distances", [[]])[0]
            for index, chunk_id in enumerate(ids):
                metadata = metadatas[index] or {}
                metadata_tags = str(metadata.get("tags", "")).split(",")
                if tags and not set(tags).intersection(set(metadata_tags)):
                    continue
                distance = float(distances[index] or 0.0)
                citations.append(
                    Citation(
                        document_id=str(metadata.get("document_id", "")),
                        chunk_id=str(chunk_id),
                        filename=str(metadata.get("filename", "unknown")),
                        score=max(0.0, 1.0 - distance),
                        excerpt=(documents[index] or "")[:500],
                    )
                )
        return sorted(citations, key=lambda item: item.score, reverse=True)[:limit]
