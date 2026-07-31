"""Tests for the consultation state infrastructure layer."""
from __future__ import annotations

import asyncio
import os

import pytest

from backend.infrastructure.redis_store import RedisStore


def test_redis_store_degrades_when_unconfigured() -> None:
    os.environ.pop("LIFE_KLINE_REDIS_URL", None)
    store = RedisStore()
    asyncio.run(store.connect())
    assert store.available is False

    asyncio.run(store.set_json("k", {"a": 1}))
    loaded = asyncio.run(store.get_json("k"))
    assert loaded == {"a": 1}
    asyncio.run(store.delete("k"))
    assert asyncio.run(store.get_json("k")) is None


def test_redis_store_token_cap_respects_limit() -> None:
    store = RedisStore()
    asyncio.run(store.connect())
    asyncio.run(store.delete("cap_key"))
    value1, ok1 = asyncio.run(
        store.increment_with_cap("cap_key", limit=2, ttl=60)
    )
    value2, ok2 = asyncio.run(
        store.increment_with_cap("cap_key", limit=2, ttl=60)
    )
    value3, ok3 = asyncio.run(
        store.increment_with_cap("cap_key", limit=2, ttl=60)
    )
    assert (value1, ok1) == (1, True)
    assert (value2, ok2) == (2, True)
    assert ok3 is False
    asyncio.run(store.delete("cap_key"))


def test_migrations_are_idempotent() -> None:
    from backend.migrations import apply_migrations

    applied_first = apply_migrations()
    applied_second = apply_migrations()
    # Second run must not re-apply anything and must not raise.
    assert applied_second == []
    assert applied_first is not None


def test_consultation_insight_round_trip(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("LIFE_KLINE_DB_PATH_OVERRIDE", str(tmp_path / "test.db"))
    from backend import database as db_module

    monkeypatch.setattr(db_module, "DB_PATH", str(tmp_path / "test.db"))
    db_module.init_db()
    from backend.migrations import apply_migrations

    apply_migrations()
    from backend.repositories import consultation_repository as repo

    insight = {
        "insight_id": "ins_test_1",
        "session_id": "ses_test",
        "planet": "VENUS",
        "topic_key": "placement",
        "hypothesis_id": "hyp_test",
        "evidence_ids": ["ev_1", "ev_2"],
        "user_quote": "我经常在关系里先在脑内演完一整部剧",
        "summary": "在关系里，你倾向于先在心里预演再行动",
        "domain_tags": ["romance"],
        "growth_action": "下次先留意身体反应再决定",
        "validation_status": "confirmed",
    }
    repo.upsert_insight(insight, report_id="rep_test", user_id="user_test")
    rows = repo.list_insights("rep_test", user_id="user_test")
    assert len(rows) == 1
    assert rows[0]["planet"] == "VENUS"
    assert rows[0]["validation_status"] == "confirmed"
    assert rows[0]["evidence_ids"] == ["ev_1", "ev_2"]

    overlay = repo.overlay_by_planet("rep_test", user_id="user_test")
    assert "VENUS" in overlay
