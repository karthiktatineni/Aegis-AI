from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.chat import Citation


class CollectionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    tags: list[str] = []


class DocumentRead(BaseModel):
    id: str
    filename: str
    content_type: str | None
    checksum: str
    tags: list[str]
    metadata_json: dict[str, Any]
    created_at: datetime

    model_config = {"from_attributes": True}


class CollectionRead(BaseModel):
    id: str
    name: str
    description: str | None
    tags: list[str]
    created_at: datetime
    updated_at: datetime
    documents: list[DocumentRead] = []

    model_config = {"from_attributes": True}


class KnowledgeSearchRequest(BaseModel):
    query: str = Field(min_length=1)
    collection_ids: list[str] = []
    tags: list[str] = []
    limit: int = Field(default=8, ge=1, le=30)


class KnowledgeSearchResponse(BaseModel):
    results: list[Citation]
