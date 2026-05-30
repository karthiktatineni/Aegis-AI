from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

API_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = API_DIR.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(PROJECT_ROOT / ".env", API_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Aegis AI"
    environment: str = Field(default="development", alias="AEGIS_ENV")
    api_v1_prefix: str = "/api/v1"
    backend_cors_origins: Annotated[list[str], NoDecode] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    database_url: str = "sqlite+aiosqlite:///./data/aegis.db"
    chroma_path: str = "./data/chroma"
    upload_dir: str = "./data/uploads"
    workspace_root: str = "./workspace"

    llm_provider: str = "mock"
    local_model_id: str = "mistralai/Mistral-7B-Instruct-v0.3"
    local_embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    model_device: str = "auto"
    model_dtype: str = "auto"
    max_new_tokens: int = 768
    temperature: float = 0.7
    top_p: float = 0.9

    command_sandbox_enabled: bool = True
    command_timeout_seconds: int = 20
    web_search_provider: str = "disabled"
    mqtt_broker_url: str | None = None

    @field_validator("backend_cors_origins", mode="before")
    @classmethod
    def parse_cors(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @property
    def data_paths(self) -> list[Path]:
        return [Path(self.upload_dir), Path(self.chroma_path), Path(self.workspace_root)]


@lru_cache
def get_settings() -> Settings:
    return Settings()
