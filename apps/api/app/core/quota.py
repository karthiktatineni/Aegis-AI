"""Daily GPU request quota enforcement.

Limits requests to 5 per day to conserve GPU credits and prevent accidental overspending.
Resets automatically at midnight UTC.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import TypedDict

from app.core.config import get_settings


class QuotaStatus(TypedDict):
    limit: int
    used_today: int
    remaining: int
    is_exceeded: bool
    date_utc: str
    resets_in_seconds: int


class DailyQuotaManager:
    """Tracks daily usage per calendar day (UTC) in a local JSON storage file."""

    def __init__(self, limit: int = 5, storage_path: str | Path | None = None) -> None:
        self.limit = limit
        settings = get_settings()
        if storage_path is None:
            data_dir = Path(settings.upload_dir).parent
            data_dir.mkdir(parents=True, exist_ok=True)
            self.storage_path = data_dir / "quota_usage.json"
        else:
            self.storage_path = Path(storage_path)

    def _today_key(self) -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    def _load_data(self) -> dict[str, int]:
        if not self.storage_path.exists():
            return {}
        try:
            return json.loads(self.storage_path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _save_data(self, data: dict[str, int]) -> None:
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            self.storage_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception:
            pass

    def get_status(self) -> QuotaStatus:
        today = self._today_key()
        data = self._load_data()
        used = int(data.get(today, 0))
        remaining = max(0, self.limit - used)

        now = datetime.now(timezone.utc)
        midnight = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        resets_in = max(0, int((midnight - now).total_seconds()))

        return {
            "limit": self.limit,
            "used_today": used,
            "remaining": remaining,
            "is_exceeded": used >= self.limit,
            "date_utc": today,
            "resets_in_seconds": resets_in,
        }

    def can_consume(self) -> bool:
        return self.get_status()["remaining"] > 0

    def consume(self) -> QuotaStatus:
        """Consumes 1 request from today's quota. Returns new status.

        Raises:
            RuntimeError: If quota has already been exhausted.
        """
        today = self._today_key()
        data = self._load_data()
        used = int(data.get(today, 0))

        if used >= self.limit:
            status = self.get_status()
            raise RuntimeError(
                f"Daily GPU quota exceeded ({used}/{self.limit} requests used today). "
                f"Quota resets in {status['resets_in_seconds'] // 3600}h "
                f"{(status['resets_in_seconds'] % 3600) // 60}m UTC."
            )

        data[today] = used + 1
        self._save_data(data)
        return self.get_status()

    def reset_today(self) -> None:
        """Convenience method for testing."""
        today = self._today_key()
        data = self._load_data()
        if today in data:
            del data[today]
            self._save_data(data)


_quota_manager: DailyQuotaManager | None = None


def get_quota_manager() -> DailyQuotaManager:
    global _quota_manager
    if _quota_manager is None:
        _quota_manager = DailyQuotaManager(limit=5)
    return _quota_manager
