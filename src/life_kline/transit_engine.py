"""
transit_engine.py -- Layered Daily Transit System

Provides a multi-layer transit analysis that mirrors how professional astrologers
write daily horoscopes. Layers:
  1. Moon (changes daily -- the engine of daily variety)
  2. Fast planets (Mercury/Venus/Mars -- changes weekly)
  3. Retrogrades (conditional -- only when active)
  4. Slow background (Jupiter through Pluto -- long-term context)

The old compute_transits() in service.py is preserved for TodayStarSpirit
backward compatibility.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Optional

from .constants import (
    Planet, Sign, AspectType,
    TRADITIONAL_PLANETS, ASPECT_CONFIG, deg_diff, clamp,
)
from .ephemeris import EphemerisEngine
from .models import ChartData


# ============================================================================
# Chinese labels (mirrors service.py so transit_engine can stand alone)
# ============================================================================

PLANET_LABELS: dict[Planet, str] = {
    Planet.SUN: "太阳", Planet.MOON: "月亮", Planet.MERCURY: "水星",
    Planet.VENUS: "金星", Planet.MARS: "火星", Planet.JUPITER: "木星",
    Planet.SATURN: "土星", Planet.URANUS: "天王星", Planet.NEPTUNE: "海王星",
    Planet.PLUTO: "冥王星",
}

ASPECT_LABELS: dict[AspectType, str] = {
    AspectType.CONJUNCTION: "合相",
    AspectType.OPPOSITION: "对冲",
    AspectType.SQUARE: "刑相",
    AspectType.TRINE: "三合",
    AspectType.SEXTILE: "六合",
}

SIGN_LABELS: dict[Sign, str] = {
    Sign.ARIES: "白羊座", Sign.TAURUS: "金牛座", Sign.GEMINI: "双子座",
    Sign.CANCER: "巨蟹座", Sign.LEO: "狮子座", Sign.VIRGO: "处女座",
    Sign.LIBRA: "天秤座", Sign.SCORPIO: "天蝎座", Sign.SAGITTARIUS: "射手座",
    Sign.CAPRICORN: "摩羯座", Sign.AQUARIUS: "水瓶座", Sign.PISCES: "双鱼座",
}

TRANSIT_ASPECT_CONFIG_EXTENDED = {
    AspectType.CONJUNCTION: {"angle": 0.0},
    AspectType.OPPOSITION: {"angle": 180.0},
    AspectType.SQUARE: {"angle": 90.0},
    AspectType.TRINE: {"angle": 120.0},
    AspectType.SEXTILE: {"angle": 60.0},
}

# Outer planets that are meaningful to track for retrograde
CHECK_RETROGRADE_PLANETS = [
    Planet.MERCURY, Planet.VENUS, Planet.MARS,
    Planet.JUPITER, Planet.SATURN,
]

HOUSE_TITLES: dict[int, str] = {
    1: "第1宫（自我）", 2: "第2宫（财帛）", 3: "第3宫（学习）",
    4: "第4宫（家庭）", 5: "第5宫（恋爱）", 6: "第6宫（工作）",
    7: "第7宫（伴侣）", 8: "第8宫（疾厄）", 9: "第9宫（迁移）",
    10: "第10宫（事业）", 11: "第11宫（交友）", 12: "第12宫（玄秘）",
}


# ============================================================================
# Layer 0: Moon Phase
# ============================================================================

def compute_moon_phase(sun_longitude: float, moon_longitude: float) -> dict:
    """Calculate current moon phase based on sun-moon angular separation."""
    angle = deg_diff(moon_longitude, sun_longitude)
    if angle < 45:
        phase = "新月"
    elif angle < 90:
        phase = "蛾眉月"
    elif angle < 135:
        phase = "上弦月"
    elif angle < 180:
        phase = "盈凸月"
    elif angle < 225:
        phase = "满月"
    elif angle < 270:
        phase = "亏凸月"
    elif angle < 315:
        phase = "下弦月"
    else:
        phase = "残月"

    return {
        "phase": phase,
        "angle": round(angle, 1),
        "is_waxing": angle < 180,
    }


# ============================================================================
# Layer 3: Retrograde Detection
# ============================================================================

@dataclass
class RetrogradeInfo:
    planet: str
    planet_label: str
    is_retrograde: bool
    in_house: int | None
    in_house_label: str | None


def detect_retrogrades(current_chart: ChartData, natal_chart: ChartData) -> list[RetrogradeInfo]:
    """Detect which planets are currently retrograde and which natal house they affect."""
    retrogrades: list[RetrogradeInfo] = []
    for p in CHECK_RETROGRADE_PLANETS:
        t_info = current_chart.planets.get(p)
        if t_info and t_info.is_retrograde:
            n_info = natal_chart.planets.get(p)
            house = n_info.house if n_info else None
            house_label = _get_house_title(house) if house else None
            retrogrades.append(RetrogradeInfo(
                planet=p.value,
                planet_label=PLANET_LABELS.get(p, p.value),
                is_retrograde=True,
                in_house=house,
                in_house_label=house_label,
            ))
    return retrogrades


# ============================================================================
# Transit Data Structures
# ============================================================================

@dataclass
class TransitAspectItem:
    transiting_planet: str
    transiting_label: str
    natal_planet: str
    natal_label: str
    aspect_type: str
    aspect_label: str
    orb: float
    is_applying: bool
    strength: float
    highlight: str


@dataclass
class DailyTransitReport:
    # Layer 1: Moon (changes DAILY)
    moon_sign: str
    moon_sign_label: str
    moon_phase: dict
    moon_house: int | None
    moon_house_label: str | None
    moon_aspects: list[TransitAspectItem]

    # Layer 2: Fast planets (Mercury/Venus/Mars -- changes weekly)
    fast_transits: list[TransitAspectItem]

    # Layer 3: Retrogrades (conditional)
    active_retrogrades: list[RetrogradeInfo]

    # Layer 4: Slow background (Jupiter through Pluto)
    slow_background: list[TransitAspectItem]


# ============================================================================
# Daily Transit Engine
# ============================================================================

class DailyTransitEngine:
    """Layered daily transit analysis engine.

    Computes a structured report organised by astrological time-scale,
    from the fast-moving Moon down to the slow background planets.
    """

    # Orbs by layer
    MOON_ORB = 6.0       # Wide orb for the fast-moving Moon
    FAST_ORB = 3.0       # Mercury / Venus / Mars
    SLOW_ORB = 3.0       # Jupiter through Pluto

    _FAST_TRANSIT_PLANETS = [Planet.MERCURY, Planet.VENUS, Planet.MARS]
    _SLOW_TRANSIT_PLANETS = [
        Planet.JUPITER, Planet.SATURN, Planet.URANUS,
        Planet.NEPTUNE, Planet.PLUTO,
    ]

    def __init__(self, ephemeris_engine: EphemerisEngine):
        self.ephemeris = ephemeris_engine

    def compute_daily_transits(self, natal_chart: ChartData) -> DailyTransitReport:
        """Compute the layered daily transit report from a natal chart."""
        # -- 1. Get current sky positions ----------------------------------
        now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
        lat = natal_chart.location.get("lat", 0) if natal_chart.location else 0
        lon = natal_chart.location.get("lon", 0) if natal_chart.location else 0
        current = self.ephemeris.calculate_chart(now_utc, lat, lon)

        # -- 2. Moon layer (changes daily) --------------------------------
        moon = current.planets.get(Planet.MOON)
        sun = current.planets.get(Planet.SUN)

        moon_sign_str = ""
        moon_sign_label_str = ""
        moon_natal_house: int | None = None
        moon_natal_house_label: str | None = None
        moon_aspects_list: list[TransitAspectItem] = []
        moon_phase_dict: dict = {"phase": "未知", "angle": 0.0, "is_waxing": True}

        if moon is not None:
            moon_sign_str = moon.sign.value if moon.sign else ""
            moon_sign_label_str = SIGN_LABELS.get(moon.sign, "")
            house_result = self._find_house(moon.longitude, natal_chart)
            if house_result is not None:
                moon_natal_house, moon_natal_house_label = house_result
            moon_aspects_list = self._detect_planet_transits(
                Planet.MOON, moon, natal_chart,
                orb=self.MOON_ORB,
                check_planets=TRADITIONAL_PLANETS,
            )
            if sun is not None:
                moon_phase_dict = compute_moon_phase(sun.longitude, moon.longitude)

        moon_aspects_list.sort(key=lambda x: x.orb)
        moon_aspects_final = moon_aspects_list[:4]

        # -- 3. Fast layer (Mercury / Venus / Mars) -----------------------
        fast_transits_list: list[TransitAspectItem] = []
        for tp in self._FAST_TRANSIT_PLANETS:
            t_info = current.planets.get(tp)
            if t_info is None:
                continue
            aspects = self._detect_planet_transits(
                tp, t_info, natal_chart,
                orb=self.FAST_ORB,
                check_planets=TRADITIONAL_PLANETS,
            )
            fast_transits_list.extend(aspects)

        fast_transits_list.sort(key=lambda x: x.orb)
        fast_transits_final = fast_transits_list[:6]

        # -- 4. Retrograde layer -----------------------------------------
        retrogrades = detect_retrogrades(current, natal_chart)

        # -- 5. Slow background (Jupiter through Pluto) -------------------
        slow_bg_list: list[TransitAspectItem] = []
        for tp in self._SLOW_TRANSIT_PLANETS:
            t_info = current.planets.get(tp)
            if t_info is None:
                continue
            aspects = self._detect_planet_transits(
                tp, t_info, natal_chart,
                orb=self.SLOW_ORB,
                check_planets=TRADITIONAL_PLANETS,
            )
            slow_bg_list.extend(aspects)

        slow_bg_list.sort(key=lambda x: (x.transiting_planet, x.orb))
        slow_bg_final = slow_bg_list[:6]

        return DailyTransitReport(
            moon_sign=moon_sign_str,
            moon_sign_label=moon_sign_label_str,
            moon_phase=moon_phase_dict,
            moon_house=moon_natal_house,
            moon_house_label=moon_natal_house_label,
            moon_aspects=moon_aspects_final,
            fast_transits=fast_transits_final,
            active_retrogrades=retrogrades,
            slow_background=slow_bg_final,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _detect_planet_transits(
        self,
        t_planet: Planet,
        t_info: Any,
        natal_chart: ChartData,
        orb: float,
        check_planets: list[Planet],
    ) -> list[TransitAspectItem]:
        """Detect aspects between a transiting planet and a set of natal planets."""
        results: list[TransitAspectItem] = []
        t_lon = self._absolute_longitude(t_info)

        for np in check_planets:
            n_info = natal_chart.planets.get(np)
            if n_info is None:
                continue
            n_lon = self._absolute_longitude(n_info)
            angle = deg_diff(t_lon, n_lon)

            for aspect_type, cfg in TRANSIT_ASPECT_CONFIG_EXTENDED.items():
                orb_diff = abs(angle - cfg["angle"])
                if orb_diff > orb:
                    continue

                results.append(TransitAspectItem(
                    transiting_planet=t_planet.value,
                    transiting_label=PLANET_LABELS.get(t_planet, ""),
                    natal_planet=np.value,
                    natal_label=PLANET_LABELS.get(np, ""),
                    aspect_type=aspect_type.value,
                    aspect_label=ASPECT_LABELS.get(aspect_type, ""),
                    orb=round(orb_diff, 2),
                    is_applying=(getattr(t_info, "speed", 0) or 0) > 0,
                    strength=round(1.0 - orb_diff / max(orb, 0.1), 2),
                    highlight=self._build_highlight(t_planet, np, aspect_type),
                ))
                # Only the strongest aspect per planet pair
                break

        return results

    def _find_house(
        self,
        longitude: float,
        chart: ChartData,
    ) -> tuple[int, str] | None:
        """Find which natal house a given absolute longitude falls in."""
        houses = getattr(chart, "houses", [])
        if not houses or len(houses) < 12:
            return None

        # Build ordered cusp longitudes
        cusps: list[float] = []
        prev = -1.0
        for sign_val, deg_val in houses[:12]:
            cusp_lon = self._longitude_from_sign(sign_val, deg_val)
            while cusp_lon <= prev:
                cusp_lon += 360.0
            cusps.append(cusp_lon)
            prev = cusp_lon

        target = float(longitude) % 360.0
        while target < cusps[0]:
            target += 360.0

        for idx, start in enumerate(cusps):
            end = cusps[idx + 1] if idx < len(cusps) - 1 else cusps[0] + 360.0
            if start <= target < end:
                house_num = idx + 1
                return house_num, _get_house_title(house_num)

        return 12, _get_house_title(12)

    def _absolute_longitude(self, info: Any) -> float:
        """Get absolute longitude (0-360) from a planet-info-like object."""
        # PlanetInfo.get_absolute_position()
        if hasattr(info, "get_absolute_position"):
            return info.get_absolute_position()
        # .longitude attribute (absolute, 0-360)
        if hasattr(info, "longitude") and info.longitude is not None:
            return float(info.longitude) % 360.0
        # Fallback: sign index * 30 + degree
        sign_idx = list(Sign).index(info.sign) if hasattr(info, "sign") else 0
        deg = float(getattr(info, "degree", 0))
        return (sign_idx * 30 + deg) % 360.0

    def _longitude_from_sign(self, sign: Sign | str, degree: float) -> float:
        """Convert (Sign, degree) to absolute longitude 0-360."""
        try:
            sign_enum = sign if isinstance(sign, Sign) else Sign(sign)
        except Exception:
            return float(degree or 0.0)
        return list(Sign).index(sign_enum) * 30.0 + float(degree or 0.0)

    def _build_highlight(self, t_planet: Planet, n_planet: Planet, aspect_type: AspectType) -> str:
        """Chinese transit highlight sentence."""
        tl = PLANET_LABELS.get(t_planet, str(t_planet))
        nl = PLANET_LABELS.get(n_planet, str(n_planet))
        al = ASPECT_LABELS.get(aspect_type, "")

        transit_roles = {
            "太阳": "自我表达和活力",
            "月亮": "情绪和直觉",
            "水星": "沟通和思绪",
            "金星": "关系和价值",
            "火星": "行动力和冲突",
            "木星": "扩张和机会",
            "土星": "压力和责任",
            "天王星": "意外和突破",
            "海王星": "迷茫和灵感",
            "冥王星": "深层的转化",
        }
        natal_domains = {
            "太阳": "你的自我认同和生活方向",
            "月亮": "你的情绪和安全感",
            "水星": "你的思考和沟通方式",
            "金星": "你的感情和价值观",
            "火星": "你的行动力和脾气",
            "木星": "你的信念和成长",
            "土星": "你的责任和底线",
        }
        aspect_verbs = {
            "合相": "正在激活",
            "对冲": "正在拉扯",
            "刑相": "正在施压",
            "三合": "正在顺流推动",
            "六合": "正在给你开一扇小窗",
        }

        role = transit_roles.get(tl, "变化")
        domain = natal_domains.get(nl, "你的一个重要部分")
        verb = aspect_verbs.get(al, "正在影响")

        return f"{tl}{al}{nl}——{verb}{domain}。{role}的能量在放大——留意它。"


# ============================================================================
# Module-level helper
# ============================================================================

def _get_house_title(house: int) -> str:
    return HOUSE_TITLES.get(house, f"第{house}宫")
