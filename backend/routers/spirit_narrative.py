"""Rule-driven guide-spirit narrative endpoint."""
from __future__ import annotations

import logging
from typing import Any

import anyio
from fastapi import APIRouter, Header, HTTPException

from backend.services.spirit_narrative_service import (
    build_degraded_narrative,
    build_guide_spirit_narrative,
)

router = APIRouter(prefix="/api", tags=["spirit-narrative"])
logger = logging.getLogger(__name__)


@router.get("/today-star-spirit/{report_id}/narrative")
async def get_guide_spirit_narrative(
    report_id: str,
    authorization: str = Header(default=""),
) -> dict[str, Any]:
    """Return today's five-part first-person guide-spirit narrative."""
    from backend.main import load_owned_report, service

    record = load_owned_report(report_id, authorization)
    report_data = record.get("data") or {}
    if service is None:
        raise HTTPException(status_code=503, detail="Engine not initialized")

    try:
        result = await anyio.to_thread.run_sync(
            lambda: build_guide_spirit_narrative(report_data, service)
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception:
        logger.exception("guide-spirit narrative computation failed")
        result = build_degraded_narrative()

    return {
        "status": "success",
        "report_id": report_id,
        "data": result,
    }
