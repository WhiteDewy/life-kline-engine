"""
today_engine.py — 今日星灵引擎

计算用户今日的指引行星（Star Spirit），基于行运相位分析。
使用三层优先级算法，覆盖精准行运到月亮星座守护。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from .constants import (
    Planet, Sign, AspectType,
    TRADITIONAL_PLANETS, ASPECT_CONFIG, deg_diff,
)
from .service import LifeKlineService, PLANET_LABELS, SIGN_LABELS, SIGN_RULERS


# 行星 Unicode 符号
PLANET_SYMBOLS: dict[Planet, str] = {
    Planet.SUN: "☉",       # ☉
    Planet.MOON: "☽",     # ☽
    Planet.MERCURY: "☿",  # ☿
    Planet.VENUS: "♀",    # ♀
    Planet.MARS: "♂",     # ♂
    Planet.JUPITER: "♃",  # ♃
    Planet.SATURN: "♄",   # ♄
    Planet.URANUS: "♅",  # ♅
    Planet.NEPTUNE: "♆", # ♆
    Planet.PLUTO: "♇",   # ♇
}


def _planet_label(planet: Planet) -> str:
    return PLANET_LABELS.get(planet, planet.value)


def _sign_label(sign: Sign) -> str:
    return SIGN_LABELS.get(sign, sign.value)


@dataclass
class TodayStarSpirit:
    """今日星灵计算结果"""
    planet: str               # Planet.value, e.g. "VENUS"
    planet_label: str         # Chinese name
    symbol: str               # Unicode symbol
    reason: str               # Human-readable explanation
    confidence: float         # 0-100
    sign: str                 # Current sign of this planet
    sign_label: str           # Chinese sign name
    transit_aspect: Optional[dict] = None  # Triggering transit detail

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "planet": self.planet,
            "planet_label": self.planet_label,
            "symbol": self.symbol,
            "reason": self.reason,
            "confidence": self.confidence,
            "sign": self.sign,
            "sign_label": self.sign_label,
        }
        if self.transit_aspect:
            result["transit_aspect"] = self.transit_aspect
        return result


class TodayStarSpiritEngine:
    """今日星灵引擎"""

    # 月球行运检测容许度（月球移动快，用较宽松的容许度）
    MOON_TRANSIT_ORB = 6.0

    def __init__(self, service: LifeKlineService):
        self.service = service

    def compute_today_star_spirit(self, chart) -> TodayStarSpirit:
        """
        计算用户今日的引路星灵。

        算法优先级：
        1. 精准行运（orb <= 1.0°），行运行星即为星灵
        2. 行运月亮触发本命行星，被触发的本命行星成为星灵
        3. 当前月亮星座的守护行星
        4. 默认回退：月亮
        """
        now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
        lat = chart.location.get("lat", 0.0) if getattr(chart, "location", None) else 0.0
        lon = chart.location.get("lon", 0.0) if getattr(chart, "location", None) else 0.0

        # 构建当前天象盘（用于获取月亮位置等）
        current_chart = self.service.engine.calculate_chart(now_utc, lat, lon)
        moon_info = current_chart.get_planet_info(Planet.MOON)

        # ── 优先级 1：精准行运 ──
        result = self._try_priority_1(chart)
        if result is not None:
            return result

        # ── 优先级 2：行运月亮触发 ──
        result = self._try_priority_2(chart, moon_info)
        if result is not None:
            return result

        # ── 优先级 3：月亮星座守护 ──
        result = self._try_priority_3(moon_info)
        if result is not None:
            return result

        # ── 默认回退：月亮 ──
        return TodayStarSpirit(
            planet=Planet.MOON.value,
            planet_label="月亮",
            symbol=PLANET_SYMBOLS.get(Planet.MOON, ""),
            reason="今日没有明显的行运指引，月亮是你的自然引路星灵",
            confidence=30.0,
            sign="UNKNOWN",
            sign_label="未知",
        )

    def _try_priority_1(self, chart) -> Optional[TodayStarSpirit]:
        """优先级 1：精准行运（orb <= 1.0°），行运行星即星灵"""
        transits = self.service.compute_transits(chart)
        exact_transits = [t for t in transits if t.get("orb", 999) <= 1.0]
        if not exact_transits:
            return None

        # 按 strength 排序，取最强
        best = max(exact_transits, key=lambda t: t.get("strength", 0))
        t_planet: Planet = best["transiting_planet"]
        n_planet: Planet = best["natal_planet"]
        aspect_type: AspectType = best["aspect_type"]
        orb: float = best.get("orb", 0)
        aspect_label: str = best.get("aspect_label", "")

        # 获取行运行星的当前星座
        now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
        lat = chart.location.get("lat", 0.0) if getattr(chart, "location", None) else 0.0
        lon = chart.location.get("lon", 0.0) if getattr(chart, "location", None) else 0.0
        current_chart = self.service.engine.calculate_chart(now_utc, lat, lon)
        t_info = current_chart.get_planet_info(t_planet)

        sign = t_info.sign.value if t_info else "UNKNOWN"
        sign_label = _sign_label(t_info.sign) if t_info else ""

        t_lbl = _planet_label(t_planet)
        n_lbl = _planet_label(n_planet)

        reason = f"行运{t_lbl}{aspect_label}你的本命{n_lbl}（orb {orb}°）——{t_lbl}今天是你最强的引路星灵"
        confidence = round(100 - orb * 20, 1)  # orb 0°=100, orb 1°=80

        return TodayStarSpirit(
            planet=t_planet.value,
            planet_label=t_lbl,
            symbol=PLANET_SYMBOLS.get(t_planet, ""),
            reason=reason,
            confidence=confidence,
            sign=sign,
            sign_label=sign_label,
            transit_aspect={
                "transiting_planet": t_planet.value,
                "natal_planet": n_planet.value,
                "aspect_type": aspect_type.value if hasattr(aspect_type, "value") else str(aspect_type),
                "aspect_label": aspect_label,
                "orb": orb,
                "strength": best.get("strength", 0),
            },
        )

    def _try_priority_2(self, chart, moon_info) -> Optional[TodayStarSpirit]:
        """优先级 2：行运月亮触发本命行星，被触发的本命行星即星灵"""
        if moon_info is None:
            return None

        moon_lon = moon_info.get_absolute_position()
        best_aspect = None
        best_orb = 999.0

        for n_planet in TRADITIONAL_PLANETS:
            n_info = chart.get_planet_info(n_planet)
            if n_info is None:
                continue
            n_lon = n_info.get_absolute_position()
            diff = deg_diff(moon_lon, n_lon)

            for aspect_type in (
                AspectType.CONJUNCTION, AspectType.SEXTILE,
                AspectType.SQUARE, AspectType.TRINE, AspectType.OPPOSITION,
            ):
                config = ASPECT_CONFIG[aspect_type]
                orb = abs(diff - config["angle"])
                if orb <= self.MOON_TRANSIT_ORB and orb < best_orb:
                    best_orb = orb
                    best_aspect = {
                        "natal_planet": n_planet,
                        "aspect_type": aspect_type,
                        "orb": orb,
                    }

        if best_aspect is None:
            return None

        n_planet: Planet = best_aspect["natal_planet"]
        n_info = chart.get_planet_info(n_planet)
        sign = n_info.sign.value if n_info else moon_info.sign.value
        sign_label = _sign_label(n_info.sign) if n_info else ""

        n_lbl = _planet_label(n_planet)
        reason = f"行运月亮触发你的本命{n_lbl}——{n_lbl}今天是你情绪的引路人"

        # confidence: 50-70，orb 越小越高
        raw_confidence = round(70 - best_orb * 3.5, 1)
        confidence = max(50.0, min(70.0, raw_confidence))

        aspect_label = best_aspect["aspect_type"].value if hasattr(best_aspect["aspect_type"], "value") else str(best_aspect["aspect_type"])

        return TodayStarSpirit(
            planet=n_planet.value,
            planet_label=n_lbl,
            symbol=PLANET_SYMBOLS.get(n_planet, ""),
            reason=reason,
            confidence=confidence,
            sign=sign,
            sign_label=sign_label,
            transit_aspect={
                "transiting_planet": Planet.MOON.value,
                "natal_planet": n_planet.value,
                "aspect_type": aspect_label,
                "orb": round(best_orb, 2),
            },
        )

    def _try_priority_3(self, moon_info) -> Optional[TodayStarSpirit]:
        """优先级 3：当前月亮星座的守护行星即星灵"""
        if moon_info is None:
            return None

        moon_sign: Sign = moon_info.sign
        ruler: Planet = SIGN_RULERS.get(moon_sign, Planet.SUN)
        moon_sign_label = _sign_label(moon_sign)

        reason = f"今日月亮在{moon_sign_label}，{_planet_label(ruler)}是你的今日引路星灵"

        return TodayStarSpirit(
            planet=ruler.value,
            planet_label=_planet_label(ruler),
            symbol=PLANET_SYMBOLS.get(ruler, ""),
            reason=reason,
            confidence=35.0,
            sign=moon_sign.value,
            sign_label=moon_sign_label,
        )
