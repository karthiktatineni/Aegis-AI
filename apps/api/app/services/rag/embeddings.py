import hashlib
import math
from typing import Protocol

from app.core.config import Settings, get_settings


class EmbeddingService(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]:
        ...


class HashEmbeddingService:
    """Small deterministic fallback for tests and first-run development."""

    dimensions = 384

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in texts:
            values = [0.0] * self.dimensions
            for token in text.lower().split():
                digest = hashlib.sha256(token.encode("utf-8")).digest()
                index = int.from_bytes(digest[:2], "big") % self.dimensions
                values[index] += 1.0
            norm = math.sqrt(sum(value * value for value in values)) or 1.0
            vectors.append([value / norm for value in values])
        return vectors


class SentenceTransformerEmbeddingService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._model = None

    def _ensure_loaded(self) -> None:
        if self._model is not None:
            return
        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer(self.settings.local_embedding_model)

    def embed(self, texts: list[str]) -> list[list[float]]:
        self._ensure_loaded()
        assert self._model is not None
        return self._model.encode(texts, normalize_embeddings=True).tolist()


def get_embedding_service() -> EmbeddingService:
    settings = get_settings()
    if settings.llm_provider.lower() == "mock":
        return HashEmbeddingService()
    return SentenceTransformerEmbeddingService(settings)
