from __future__ import annotations

import math
import re
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.memory import MemoryRepository
from app.models import Message
from app.services.rag.embeddings import get_embedding_service


def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2, strict=False))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)


class MemoryService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = MemoryRepository(session)
        self.embedding_service = get_embedding_service()

    async def summarize_conversation(self, messages: list[Message]) -> str:
        meaningful = [
            f"{message.role.capitalize()}: {message.content.strip()}"
            for message in messages
            if message.role != "system" and message.content.strip()
        ]
        if not meaningful:
            return ""

        # Build structured memory summary preserving key insights
        recent = meaningful[-6:]  # Focus on key conversation exchange
        summary_text = " | ".join(recent)
        if len(summary_text) > 800:
            summary_text = summary_text[:797] + "..."
        return summary_text

    async def remember_conversation(self, user_id: str, messages: list[Message]) -> None:
        summary = await self.summarize_conversation(messages)
        if not summary:
            return
        embeddings = self.embedding_service.embed([summary])
        embedding = embeddings[0] if embeddings else []
        embedding_id = f"memory:{user_id}:{abs(hash(summary[:64]))}"

        # Clean short summary for prompt injection
        short_summary = summary[:160].replace("\n", " ").strip()
        await self.repository.add_memory(
            user_id=user_id,
            summary=short_summary,
            content=summary,
            scope="long_term",
            embedding_id=embedding_id,
            tags=["conversation", "auto_summary"],
        )

    async def retrieve_relevant(self, user_id: str, query: str, limit: int = 5) -> list[str]:
        memories = await self.repository.list_memories(user_id, scope="long_term")
        if not memories:
            return []

        query_tokens = set(re.findall(r"\w+", query.lower()))
        query_embeddings = self.embedding_service.embed([query])
        query_vector = query_embeddings[0] if query_embeddings else []

        scored: list[tuple[float, int, str]] = []
        for index, memory in enumerate(memories):
            combined_text = f"{memory.summary} {memory.content}".lower()
            tokens = set(re.findall(r"\w+", combined_text))
            token_overlap = len(query_tokens.intersection(tokens))

            # Combine token overlap with embedding semantic similarity
            score = float(token_overlap)
            if query_vector:
                mem_embeddings = self.embedding_service.embed([memory.content[:500]])
                if mem_embeddings:
                    similarity = cosine_similarity(query_vector, mem_embeddings[0])
                    score += max(0.0, similarity) * 2.0

            if score > 0.1:
                scored.append((score, index, memory.summary))

        ranked = sorted(scored, key=lambda item: (item[0], -item[1]), reverse=True)
        return [summary for _, _, summary in ranked[:limit]]
