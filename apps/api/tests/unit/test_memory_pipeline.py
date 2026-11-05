import pytest
from unittest.mock import AsyncMock, MagicMock

from app.models import Message
from app.services.memory.service import MemoryService


@pytest.mark.asyncio
async def test_memory_summarization():
    service = MemoryService(session=AsyncMock())
    messages = [
        Message(id="1", conversation_id="c1", role="user", content="I prefer Python and fast APIs."),
        Message(id="2", conversation_id="c1", role="assistant", content="FastAPI with async SQLAlchemy is recommended."),
        Message(id="3", conversation_id="c1", role="user", content="Deploy on Modal with GPU."),
    ]
    summary = await service.summarize_conversation(messages)
    assert "Python" in summary or "FastAPI" in summary
    assert len(summary) <= 800


@pytest.mark.asyncio
async def test_memory_retrieval_relevance():
    mock_session = AsyncMock()
    service = MemoryService(session=mock_session)

    # Mock memories in repository
    m1 = MagicMock()
    m1.summary = "User prefers Python, FastAPI, and ChromaDB"
    m1.content = "User prefers Python, FastAPI, and ChromaDB vector store"

    m2 = MagicMock()
    m2.summary = "User asked about baking sourdough bread"
    m2.content = "Discussion on flour and fermentation"

    service.repository.list_memories = AsyncMock(return_value=[m1, m2])

    relevant = await service.retrieve_relevant("user1", "Tell me about Python FastAPI setup", limit=2)
    assert len(relevant) >= 1
    assert "FastAPI" in relevant[0]
