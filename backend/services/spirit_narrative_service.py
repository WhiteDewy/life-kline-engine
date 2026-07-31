"""Application service for the rule-driven guide-spirit narrative."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from life_kline.ephemeris import EphemerisEngine
from life_kline.firdaria import calculate_firdaria_periods
from life_kline.guide_spirit_narrative import compute_guide_narrative
from life_kline.service import LifeKlineService
from life_kline.today_engine import TodayStarSpiritEngine


def extract_current_firdaria(
    report_data: dict[str, Any],
    user_info: dict[str, Any],
    *,
    now: datetime | None = None,
) -> Any:
    """Return the current Firdaria period, or ``None`` when unavailable."""
    del report_data  # Reserved for a future persisted-period fast path.
    birth_value = user_info.get("birth_time_local") or user_info.get("birth_time_utc")
    if not birth_value:
        return None

    try:
        birth_dt = datetime.fromisoformat(str(birth_value))
    except (TypeError, ValueError):
        return None

    current = now or datetime.now(timezone.utc)
    if birth_dt.tzinfo is None:
        current = current.replace(tzinfo=None)
    else:
        current = current.astimezone(birth_dt.tzinfo)

    current_age = max(0.0, (current - birth_dt).total_seconds() / (365.2422 * 86400))
    try:
        periods = calculate_firdaria_periods(
            bool(user_info.get("is_day_chart", True)),
            max_age=max(100.0, current_age + 1.0),
        )
    except Exception:
        return None

    return next(
        (
            period
            for period in periods
            if period.start_age <= current_age < period.end_age
        ),
        None,
    )


def reconstruct_chart_from_user_info(user_info: dict[str, Any]):
    """Rebuild the natal chart required by today's transit engine."""
    birth_value = user_info.get("birth_time_utc") or user_info.get("birth_time_local")
    if not birth_value:
        raise ValueError("报告缺少出生时间")

    birth_time = datetime.fromisoformat(str(birth_value))
    lat = float(user_info.get("lat", 0.0))
    lon = float(user_info.get("lon", 0.0))
    chart = EphemerisEngine().calculate_chart(birth_time, lat, lon)
    chart.location = {"lat": lat, "lon": lon}
    return chart


def build_guide_spirit_narrative(
    report_data: dict[str, Any],
    life_service: LifeKlineService,
) -> dict[str, Any]:
    """Compute today's guide-spirit narrative from engine-owned facts."""
    user_info = report_data.get("user_info") or {}
    natal_chart = report_data.get("natal_chart") or {}
    character_payload = report_data.get("planet_characters") or {}
    planet_characters = character_payload.get("planet_characters") or {}
    if not user_info:
        raise ValueError("报告缺少用户信息")
    if not natal_chart or not planet_characters:
        raise ValueError("报告缺少星盘数据或行星角色数据")

    firdaria_period = extract_current_firdaria(report_data, user_info)
    chart = reconstruct_chart_from_user_info(user_info)
    today_spirit = TodayStarSpiritEngine(life_service).compute_today_star_spirit(
        chart,
        firdaria_period,
    )
    narrative = compute_guide_narrative(
        today_spirit=today_spirit,
        natal_chart=natal_chart,
        planet_characters=planet_characters,
        firdaria_period=firdaria_period,
    )
    return narrative.to_dict()


def build_degraded_narrative() -> dict[str, Any]:
    """Return a safe fallback without exposing internal exception details."""
    return {
        "spirit_planet": "MOON",
        "spirit_name": "月亮",
        "spirit_symbol": "☽",
        "trigger_type": "default",
        "confidence": 20.0,
        "ruled_houses": [],
        "located_house": 0,
        "located_sign": "",
        "dignity_code": "peregrine",
        "dignity_label": "平常",
        "is_chart_ruler": False,
        "segments": {
            "who_am_i": "我是月亮，也是你内在感受与安全感的一部分。",
            "where_i_work": "",
            "flystar_chain": "",
            "why_me_today": "今天的星图暂时看不清，但我仍会陪你留意此刻的感受。",
            "guidance": "先回到呼吸和身体里，不急着替今天下结论。——月亮",
        },
        "full_introduction": (
            "你好，我是月亮，也是你内在感受与安全感的一部分。\n\n"
            "今天的星图暂时看不清，但我仍会陪你留意此刻的感受。\n\n"
            "先回到呼吸和身体里，不急着替今天下结论。——月亮"
        ),
        "evidence": [],
        "persona_snapshot": {
            "name_zh": "月亮",
            "archetype_zh": "照料者",
            "voice_tone": "温柔",
            "advice_approach": "先照顾此刻的你",
        },
        "degraded": True,
    }
