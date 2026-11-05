import pytest
from app.core.quota import DailyQuotaManager


def test_daily_quota_lifecycle(tmp_path):
    storage_file = tmp_path / "test_quota.json"
    mgr = DailyQuotaManager(limit=5, storage_path=storage_file)

    status = mgr.get_status()
    assert status["limit"] == 5
    assert status["used_today"] == 0
    assert status["remaining"] == 5
    assert status["is_exceeded"] is False

    # Consume 4 requests
    for i in range(4):
        assert mgr.can_consume() is True
        res = mgr.consume()
        assert res["used_today"] == i + 1

    assert mgr.get_status()["remaining"] == 1

    # Consume 5th request
    mgr.consume()
    assert mgr.get_status()["remaining"] == 0
    assert mgr.get_status()["is_exceeded"] is True
    assert mgr.can_consume() is False

    # 6th request must raise RuntimeError
    with pytest.raises(RuntimeError) as exc_info:
        mgr.consume()
    assert "Daily GPU quota exceeded" in str(exc_info.value)
