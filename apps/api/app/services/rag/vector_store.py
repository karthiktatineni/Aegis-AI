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
        # Chroma collection names must be 3-63 characters alphanumeric, underscore or hyphen
        clean_name = f"kb_{collection_id.replace('-', '_')}"[:63]
        return self.client.get_or_create_collection(name=clean_name)

    def upsert(self, collection_id: str, records: list[VectorRecord]) -> None:
        if not records:
            return
        collection = self._collection(collection_id)
        # Ensure metadata values are flat and primitive (string, int, float, bool)
        clean_metadatas = []
        for r in records:
            clean_meta = {}
            for k, v in r.metadata.items():
                if isinstance(v, (str, int, float, bool)):
                    clean_meta[k] = v
                elif v is None:
                    clean_meta[k] = ""
                else:
                    clean_meta[k] = str(v)
            clean_metadatas.append(clean_meta)

        collection.upsert(
            ids=[record.id for record in records],
            documents=[record.content for record in records],
            embeddings=[record.embedding for record in records],
            metadatas=clean_metadatas,
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
            if collection.count() == 0:
                continue
            effective_limit = min(limit, collection.count())
            result = collection.query(
                query_embeddings=[query_embedding],
                n_results=effective_limit,
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
                distance = float(distances[index] if index < len(distances) else 0.0)
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
