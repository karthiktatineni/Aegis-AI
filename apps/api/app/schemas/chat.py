from datetime import datetime

from pydantic import BaseModel, Field


class Citation(BaseModel):
    document_id: str
    chunk_id: str
    filename: str
    score: float
    excerpt: str


class MessageRead(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    citations: list[Citation] | list[dict] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ConversationRead(BaseModel):
    id: str
    title: str
    summary: str | None = None
    pinned: bool
    archived: bool
    created_at: datetime
    updated_at: datetime
    messages: list[MessageRead] = []

    model_config = {"from_attributes": True}


class ConversationCreate(BaseModel):
    title: str = "New conversation"


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    collection_ids: list[str] = []
    use_memory: bool = True
    use_rag: bool = True


class MessageEdit(BaseModel):
    content: str = Field(min_length=1)


class ChatSearchResult(BaseModel):
    message_id: str
    conversation_id: str
    role: str
    content: str
    updated_at: datetime
