"""Integration tests for the consultation service layer (LLM + Redis mocked)."""
from __future__ import annotations

import asyncio
from typing import Any

import pytest

from backend.infrastructure.redis_store import RedisStore
from backend.services.spirit_consultation_service import (
    QuotaExceeded,
    SpiritConsultationService,
)
from tests.test_spirit_consultation_engine import _report_data


class _FakeLLM:
    def __init__(self, tokens: list[str] | None = None, *, configured: bool = True):
        self._tokens = tokens or ["我", "在", "听", "你", "说。"]
        self._configured = configured
        self.calls: list[list[dict[str, str]]] = []

    @property
    def is_configured(self) -> bool:
        return self._configured

    async def chat_stream(self, messages, *, timeout_seconds=None):
        self.calls.append(messages)
        for token in self._tokens:
            yield token


def _store() -> RedisStore:
    store = RedisStore()
    asyncio.run(store.connect())
    return store


@pytest.fixture
def service() -> SpiritConsultationService:
    return SpiritConsultationService(_store(), llm_client=_FakeLLM())


def test_start_session_returns_dossier_and_opening(service: SpiritConsultationService) -> None:
    data = _report_data()
    result = asyncio.run(
        service.start_session(
            report_data=data,
            report_id="rep_test",
            user_id="user_test",
            planet="VENUS",
        )
    )
    assert result["session_id"].startswith("ses_")
    assert result["dossier"]["planet"] == "VENUS"
    assert "topic_order" in result["dossier"]
    assert result["opening_text"]


def test_turn_streams_text_and_evidence(service: SpiritConsultationService) -> None:
    data = _report_data()
    start = asyncio.run(
        service.start_session(
            report_data=data, report_id="rep_test", user_id="user_test", planet="VENUS"
        )
    )
    session_id = start["session_id"]
    state, dossier, plan, crisis = asyncio.run(
        service.plan_turn(
            report_data=data,
            report_id="rep_test",
            session_id=session_id,
            user_id="user_test",
            message="我们先聊聊落宫吧",
        )
    )
    assert crisis is None
    events = []
    asyncio.run(
        _collect(
            service.stream_turn(
                dossier=dossier, plan=plan, state=state, history=[]
            ),
            events,
        )
    )
    types = [e["type"] for e in events]
    assert "evidence" in types
    assert "text_delta" in types
    assert "done" in types


def test_crisis_short_circuits(service: SpiritConsultationService) -> None:
    data = _report_data()
    start = asyncio.run(
        service.start_session(
            report_data=data, report_id="rep_test", user_id="user_test", planet="VENUS"
        )
    )
    state, dossier, plan, crisis = asyncio.run(
        service.plan_turn(
            report_data=data,
            report_id="rep_test",
            session_id=start["session_id"],
            user_id="user_test",
            message="我不想活了，我想结束一切",
        )
    )
    assert crisis is not None
    assert crisis["type"] == "crisis"


def test_decide_insight_persists_confirmed(service: SpiritConsultationService, tmp_path, monkeypatch) -> None:
    from backend import database as db_module

    monkeypatch.setattr(db_module, "DB_PATH", str(tmp_path / "test.db"))
    db_module.init_db()
    from backend.migrations import apply_migrations

    apply_migrations()

    data = _report_data()
    start = asyncio.run(
        service.start_session(
            report_data=data, report_id="rep_test", user_id="user_test", planet="VENUS"
        )
    )
    session_id = start["session_id"]
    # Drive a full micro-cycle: explain -> (open hypothesis) -> confirm
    asyncio.run(
        service.plan_turn(
            report_data=data, report_id="rep_test", session_id=session_id,
            user_id="user_test", message="我们先聊聊落宫吧",
        )
    )
    asyncio.run(
        service.plan_turn(
            report_data=data, report_id="rep_test", session_id=session_id,
            user_id="user_test", message="上周和伴侣在餐厅起冲突",
        )
    )
    confirm = asyncio.run(
        service.plan_turn(
            report_data=data, report_id="rep_test", session_id=session_id,
            user_id="user_test", message="对，我就是这样",
        )
    )
    state, dossier, plan, _ = confirm
    assert plan.insight_draft is not None
    insight_id = plan.insight_draft.insight_id
    result = asyncio.run(
        service.decide_insight(
            report_id="rep_test", user_id="user_test", session_id=session_id,
            insight_id=insight_id, decision="confirmed",
            edited_user_quote="我经常先在心里演完一整部剧",
            request_id="req_1",
        )
    )
    assert result["persisted"] is True

    overlay = asyncio.run(
        service.report_overlay(report_id="rep_test", user_id="user_test")
    )
    assert "VENUS" in overlay


def test_token_budget_enforced(service: SpiritConsultationService, monkeypatch) -> None:
    import backend.services.spirit_consultation_service as svc_mod

    monkeypatch.setattr(svc_mod, "_TOKEN_DAILY", 1)
    data = _report_data()
    start = asyncio.run(
        service.start_session(
            report_data=data, report_id="rep_test", user_id="user_test", planet="VENUS"
        )
    )
    # The budget check increments the per-user token counter; with a daily
    # cap of 1 the second turn's check must raise.
    asyncio.run(
        service.plan_turn(
            report_data=data, report_id="rep_test", session_id=start["session_id"],
            user_id="user_test", message="我们先聊聊落宫吧",
        )
    )
    with pytest.raises(QuotaExceeded):
        asyncio.run(
            service.plan_turn(
                report_data=data, report_id="rep_test", session_id=start["session_id"],
                user_id="user_test", message="继续聊聊",
            )
        )


async def _collect(gen: Any, sink: list[Any]) -> None:
    async for event in gen:
        sink.append(event)
