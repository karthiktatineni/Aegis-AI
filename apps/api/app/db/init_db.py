from pathlib import Path

from app.core.config import get_settings
from app.db.base import Base
from app.db.session import engine
from app.models import entities  # noqa: F401


async def init_db() -> None:
    settings = get_settings()
    for path in settings.data_paths:
        Path(path).mkdir(parents=True, exist_ok=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
