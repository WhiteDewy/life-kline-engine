"""v2 star-spirit consultation routes (SSE + REST, additive)."""
from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from backend.infrastructure.redis_store import get_redis_store
from backend.services.spirit_consultation_service import (
    ConsultationUnavailable,
    QuotaExceeded,
    SpiritConsultationService,
)
from backend.services.spirit_narrative_service import (
    extract_current_firdaria,
    reconstruct_chart_from_user_info,
)

router = APIRouter(prefix="/api/v2", tags=["spirit-consultation"])
logger = logging.getLogger(__name__)


class StartConsultationInput(BaseModel):
    planet: str = Field(default="MOON")
    entry_context: dict[str, Any] | None = None


class TurnInput(BaseModel):
    message: str = Field(default="", max_length=4000)
    intent_hint: str = Field(default="", max_length=40)
    history: list[dict[str, str]] = Field(default_factory=list)


class InsightDecisionInput(BaseModel):
    decision: str
    edited_user_quote: str = ""
    request_id: str = ""


def _service() -> SpiritConsultationService:
    return SpiritConsultationService(get_redis_store())


def _auth_and_report(report_id: str, authorization: str) -> tuple[str, dict[str, Any]]:
    from backend.main import load_owned_report

    record = load_owned_report(report_id, authorization)
    data = record.get("data") or {}
    from backend.main import require_report_owner

    user_id = require_report_owner(report_id, authorization)
    return user_id, data


@router.post("/spirit-consultations/{report_id}")
async def start_consultation(
    report_id: str,
    body: StartConsultationInput,
    authorization: str = Header(default=""),
) -> dict[str, Any]:
    user_id, report_data = _auth_and_report(report_id, authorization)
    user_info = report_data.get("user_info") or {}
    today_spirit = None
    firdaria_period = None
    try:
        firdaria_period = extract_current_firdaria(report_data, user_info)
        chart = reconstruct_chart_from_user_info(user_info)
        from life_kline.today_engine import TodayStarSpiritEngine
        from backend.main import service as life_service

        if life_service is not None:
            today_spirit = TodayStarSpiritEngine(life_service).compute_today_star_spirit(
                chart, firdaria_period
            )
    except Exception:
        logger.exception("today spirit/firdaria 计算失败，按普通星灵开场")

    result = await _service().start_session(
        report_data=report_data,
        report_id=report_id,
        user_id=user_id,
        planet=body.planet,
        entry_context=body.entry_context,
        today_spirit=today_spirit,
        firdaria_period=firdaria_period,
    )
    return {"status": "success", "report_id": report_id, "data": result}


@router.get("/spirit-consultations/{report_id}/{session_id}")
async def resume_consultation(
    report_id: str,
    session_id: str,
    authorization: str = Header(default=""),
) -> dict[str, Any]:
    user_id, report_data = _auth_and_report(report_id, authorization)
    result = await _service().resume_session(
        report_data=report_data,
        report_id=report_id,
        user_id=user_id,
        session_id=session_id,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="咨询会话不存在或已过期")
    return {"status": "success", "report_id": report_id, "data": result}


@router.post("/spirit-consultations/{report_id}/{session_id}/turn")
async def consultation_turn(
    report_id: str,
    session_id: str,
    body: TurnInput,
    request: Request,
    authorization: str = Header(default=""),
) -> StreamingResponse:
    user_id, report_data = _auth_and_report(report_id, authorization)
    service = _service()

    try:
        state, dossier, plan, crisis = await service.plan_turn(
            report_data=report_data,
            report_id=report_id,
            session_id=session_id,
            user_id=user_id,
            message=body.message,
            intent_hint=body.intent_hint,
        )
    except ConsultationUnavailable as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except QuotaExceeded as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc

    async def generate() -> Any:
        if crisis is not None:
            yield _sse("crisis", crisis)
            yield _sse("done", "")
            return
        async for event in service.stream_turn(
            dossier=dossier,
            plan=plan,
            state=state,
            history=body.history,
            report_id=report_id,
            user_id=user_id,
            user_message=body.message,
        ):
            yield _sse(event.get("type", "event"), event)
        yield _sse("done", "")

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post(
    "/spirit-consultations/{report_id}/{session_id}/insights/{insight_id}/decision"
)
async def decide_insight(
    report_id: str,
    session_id: str,
    insight_id: str,
    body: InsightDecisionInput,
    authorization: str = Header(default=""),
) -> dict[str, Any]:
    user_id, _ = _auth_and_report(report_id, authorization)
    try:
        result = await _service().decide_insight(
            report_id=report_id,
            user_id=user_id,
            session_id=session_id,
            insight_id=insight_id,
            decision=body.decision,
            edited_user_quote=body.edited_user_quote,
            request_id=body.request_id,
        )
    except ConsultationUnavailable as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"status": "success", "report_id": report_id, "data": result}


@router.get("/reports/{report_id}/consultation-overlay")
async def consultation_overlay(
    report_id: str,
    authorization: str = Header(default=""),
) -> dict[str, Any]:
    user_id, _ = _auth_and_report(report_id, authorization)
    overlay = await _service().report_overlay(report_id=report_id, user_id=user_id)
    return {"status": "success", "report_id": report_id, "data": overlay}


def _sse(kind: str, payload: Any) -> str:
    """Pass the event dict through as-is; the frontend parses event.type directly."""
    if isinstance(payload, dict) and "type" in payload:
        return f"data: {json.dumps(payload, ensure_ascii=False, default=str)}\n\n"
    # fallback: wrap scalar payloads
    return f"data: {json.dumps({'type': kind, 'text': str(payload)}, ensure_ascii=False)}\n\n"
