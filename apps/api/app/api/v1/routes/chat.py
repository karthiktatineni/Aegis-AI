from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import db_session
from app.core.security import CurrentUser, get_current_user
from app.db.repositories.conversations import ConversationRepository
from app.schemas.chat import (
    ChatRequest,
    ChatSearchResult,
    ConversationCreate,
    ConversationRead,
    MessageEdit,
    MessageRead,
)
from app.services.ai.llm import ModelNotReadyError, get_llm_provider
from app.services.ai.prompts import build_chat_prompt
from app.services.memory.service import MemoryService
from app.services.rag.service import RAGService
from app.utils.sse import sse_event

router = APIRouter()


@router.get("/conversations", response_model=list[ConversationRead])
async def list_conversations(
    q: str | None = Query(default=None),
    session: AsyncSession = Depends(db_session),
    user: CurrentUser = Depends(get_current_user),
) -> list[ConversationRead]:
    repository = ConversationRepository(session)
    await repository.ensure_user(user.id, user.email)
    conversations = await repository.list_for_user(user.id, q)
    return [ConversationRead.model_validate(conversation) for conversation in conversations]


@router.post("/conversations", response_model=ConversationRead, status_code=201)
async def create_conversation(
    payload: ConversationCreate,
    session: AsyncSession = Depends(db_session),
    user: CurrentUser = Depends(get_current_user),
) -> ConversationRead:
    repository = ConversationRepository(session)
    await repository.ensure_user(user.id, user.email)
    conversation = await repository.create(user.id, payload.title)
    await session.commit()
    return ConversationRead.model_validate(conversation)


@router.get("/conversations/{conversation_id}", response_model=ConversationRead)
async def get_conversation(
    conversation_id: str,
    session: AsyncSession = Depends(db_session),
    user: CurrentUser = Depends(get_current_user),
) -> ConversationRead:
    repository = ConversationRepository(session)
    conversation = await repository.get_for_user(conversation_id, user.id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return ConversationRead.model_validate(conversation)


@router.get("/search", response_model=list[ChatSearchResult])
async def search_chat(
    q: str = Query(min_length=1),
    session: AsyncSession = Depends(db_session),
    user: CurrentUser = Depends(get_current_user),
) -> list[ChatSearchResult]:
    repository = ConversationRepository(session)
    messages = await repository.search_messages(user.id, q)
    return [
        ChatSearchResult(
            message_id=message.id,
            conversation_id=message.conversation_id,
            role=message.role,
            content=message.content,
            updated_at=message.updated_at,
        )
        for message in messages
    ]


@router.patch("/messages/{message_id}", response_model=MessageRead)
async def edit_message(
    message_id: str,
    payload: MessageEdit,
    session: AsyncSession = Depends(db_session),
    user: CurrentUser = Depends(get_current_user),
) -> MessageRead:
    repository = ConversationRepository(session)
    message = await repository.edit_message(message_id, user.id, payload.content)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    await session.commit()
    return MessageRead.model_validate(message)


@router.post("/conversations/{conversation_id}/messages", response_model=MessageRead)
async def send_message(
    conversation_id: str,
    payload: ChatRequest,
    session: AsyncSession = Depends(db_session),
    user: CurrentUser = Depends(get_current_user),
) -> MessageRead:
    repository = ConversationRepository(session)
    conversation = await repository.get_for_user(conversation_id, user.id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    await repository.add_message(conversation.id, "user", payload.message)
    rag = RAGService(session)
    memory = MemoryService(session)
    citations = await rag.search(payload.message, payload.collection_ids) if payload.use_rag else []
    memories = await memory.retrieve_relevant(user.id, payload.message) if payload.use_memory else []
    prompt = build_chat_prompt(conversation.messages, payload.message, memories, citations)
    response = await get_llm_provider().complete(prompt)
    assistant_message = await repository.add_message(
        conversation.id,
        "assistant",
        response,
        citations=[citation.model_dump() for citation in citations],
    )
    await session.commit()
    return MessageRead.model_validate(assistant_message)


@router.post("/conversations/{conversation_id}/stream")
async def stream_message(
    conversation_id: str,
    payload: ChatRequest,
    session: AsyncSession = Depends(db_session),
    user: CurrentUser = Depends(get_current_user),
) -> StreamingResponse:
    repository = ConversationRepository(session)
    conversation = await repository.get_for_user(conversation_id, user.id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    async def events() -> AsyncIterator[str]:
        await repository.add_message(conversation.id, "user", payload.message)
        rag = RAGService(session)
        memory = MemoryService(session)
        citations = await rag.search(payload.message, payload.collection_ids) if payload.use_rag else []
        memories = await memory.retrieve_relevant(user.id, payload.message) if payload.use_memory else []
        prompt = build_chat_prompt(conversation.messages, payload.message, memories, citations)
        yield sse_event("citations", {"citations": [citation.model_dump() for citation in citations]})
        chunks: list[str] = []
        try:
            async for chunk in get_llm_provider().stream_chat(prompt):
                chunks.append(chunk)
                yield sse_event("token", {"text": chunk})
        except ModelNotReadyError as exc:
            await session.rollback()
            yield sse_event("error", {"message": str(exc)})
            return
        except Exception as exc:
            await session.rollback()
            yield sse_event(
                "error",
                {"message": f"Local model generation failed: {type(exc).__name__}: {exc}"},
            )
            return
        assistant_message = await repository.add_message(
            conversation.id,
            "assistant",
            "".join(chunks),
            citations=[citation.model_dump() for citation in citations],
        )
        await memory.remember_conversation(user.id, conversation.messages + [assistant_message])
        await session.commit()
        yield sse_event(
            "done",
            {
                "message_id": assistant_message.id,
                "conversation_id": conversation.id,
            },
        )

    return StreamingResponse(events(), media_type="text/event-stream")
