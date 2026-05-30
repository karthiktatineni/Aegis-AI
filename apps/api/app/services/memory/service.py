from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.memory import MemoryRepository
from app.models import Message
from app.services.rag.embeddings import get_embedding_service


class MemoryService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = MemoryRepository(session)
        self.embedding_service = get_embedding_service()

    async def summarize_conversation(self, messages: list[Message]) -> str:
        meaningful = [message.content.strip() for message in messages if message.role != "system"]
        if not meaningful:
            return ""
        joined = " ".join(meaningful)
        return joined[:800] + ("..." if len(joined) > 800 else "")

    async def remember_conversation(self, user_id: str, messages: list[Message]) -> None:
        summary = await self.summarize_conversation(messages)
        if not summary:
            return
        embedding = self.embedding_service.embed([summary])[0]
        embedding_id = f"memory:{user_id}:{abs(hash(tuple(round(v, 4) for v in embedding[:8])))}"
        await self.repository.add_memory(
            user_id=user_id,
            summary=summary[:160],
            content=summary,
            scope="long_term",
            embedding_id=embedding_id,
            tags=["conversation"],
        )

    async def retrieve_relevant(self, user_id: str, query: str, limit: int = 5) -> list[str]:
        memories = await self.repository.list_memories(user_id, scope="long_term")
        if not memories:
            return []
        query_tokens = set(query.lower().split())
        scored = []
        for index, memory in enumerate(memories):
            tokens = set((memory.content + " " + memory.summary).lower().split())
            score = len(query_tokens.intersection(tokens))
            scored.append((score, index, memory))
        ranked = sorted(scored, key=lambda item: (item[0], -item[1]), reverse=True)
        return [memory.summary for score, _, memory in ranked[:limit] if score > 0]
