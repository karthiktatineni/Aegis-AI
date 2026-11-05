from pathlib import Path

from app.core.config import get_settings
from app.db.base import Base
from app.db.session import engine
from app.models import entities  # noqa: F401


async def init_db() -> None:
    settings = get_settings()
    for path in settings.data_paths:
        Path(path).mkdir(parents=True, exist_ok=True)

    # Ensure parent directory for SQLite file exists
    db_url = settings.database_url
    if "sqlite" in db_url and "///" in db_url:
        db_file = db_url.split("///")[-1]
        if db_file and db_file != ":memory:":
            Path(db_file).parent.mkdir(parents=True, exist_ok=True)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
