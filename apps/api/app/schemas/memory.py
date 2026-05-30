from datetime import datetime

from pydantic import BaseModel, Field


class MemoryRead(BaseModel):
    id: str
    scope: str
    summary: str
    content: str
    importance: int
    tags: list[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MemoryCreate(BaseModel):
    summary: str = Field(min_length=1)
    content: str = Field(min_length=1)
    scope: str = "long_term"
    tags: list[str] = []


class PreferenceUpsert(BaseModel):
    key: str = Field(min_length=1, max_length=128)
    value: str = Field(min_length=1)


class PreferenceRead(BaseModel):
    id: str
    key: str
    value: str
    source: str
    updated_at: datetime

    model_config = {"from_attributes": True}
