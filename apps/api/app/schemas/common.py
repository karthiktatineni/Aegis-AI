from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    capabilities: dict[str, bool]


class ErrorResponse(BaseModel):
    detail: str
    metadata: dict[str, Any] | None = None


class Timestamped(ORMModel):
    id: str
    created_at: datetime
    updated_at: datetime
