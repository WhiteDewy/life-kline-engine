"""
领域分析器辅助工具 — 从星盘提取特定数据 + 生成个性化叙事片段。
"""
from __future__ import annotations

from typing import Any

from ..constants import Planet, Sign, DOMICILE_SIGNS, EXALTATION_SIGNS, DETRIMENT_SIGNS, FALL_SIGNS


# ── 基础查询 ──────────────────────────────────────────────

SIGN_RULER_MAP: dict[str, str] = {
    "ARIES": "MARS", "TAURUS": "VENUS", "GEMINI": "MERCURY",
    "CANCER": "MOON", "LEO": "SUN", "VIRGO": "MERCURY",
    "LIBRA": "VENUS", "SCORPIO": "MARS", "SAGITTARIUS": "JUPITER",
    "CAPRICORN": "SATURN", "AQUARIUS": "SATURN", "PISCES": "JUPITER",
}

PLANET_LABEL_CN: dict[str, str] = {
    "SUN": "太阳", "MOON": "月亮", "MERCURY": "水星", "VENUS": "金星",
    "MARS": "火星", "JUPITER": "木星", "SATURN": "土星",
    "URANUS": "天王星", "NEPTUNE": "海王星", "PLUTO": "冥王星",
    "NORTH_NODE": "北交点", "SOUTH_NODE": "南交点",
}

SIGN_LABEL_CN: dict[str, str] = {
    "ARIES": "白羊座", "TAURUS": "金牛座", "GEMINI": "双子座", "CANCER": "巨蟹座",
    "LEO": "狮子座", "VIRGO": "处女座", "LIBRA": "天秤座", "SCORPIO": "天蝎座",
    "SAGITTARIUS": "射手座", "CAPRICORN": "摩羯座", "AQUARIUS": "水瓶座", "PISCES": "双鱼座",
}

HOUSE_TITLES: dict[int, str] = {
    1: "自我与身体", 2: "收入与资源", 3: "学习与表达", 4: "家庭与根基",
    5: "创造与恋爱", 6: "工作与健康", 7: "伴侣与合作", 8: "风险与转化",
    9: "远方与意义", 10: "事业与名望", 11: "社群与愿景", 12: "潜意识与退隐",
}

DIGNITY_LABEL_CN: dict[str, str] = {
    "domicile": "入庙", "exaltation": "擢升", "detriment": "失势",
    "fall": "落陷", "peregrine": "平常",
}


def plabel(p: Planet | str) -> str:
    n = p.value if isinstance(p, Planet) else str(p)
    return PLANET_LABEL_CN.get(n, n)


def slabel(s: Sign | str) -> str:
    n = s.value if isinstance(s, Sign) else str(s)
    return SIGN_LABEL_CN.get(n, n)


def dlabel(code: str) -> str:
    return DIGNITY_LABEL_CN.get(code, code)


def house_title(h: int) -> str:
    return HOUSE_TITLES.get(h, f"第{h}宫")


def asc_sign(chart: Any) -> str:
    try:
        if hasattr(chart, "houses") and chart.houses:
            return chart.houses[0][0].value
    except Exception:
        pass
    return "未知"


def chart_ruler_name(chart: Any) -> str:
    asc = asc_sign(chart)
    return SIGN_RULER_MAP.get(asc, "SUN")


def house_cusp_sign(chart: Any, house: int) -> str:
    try:
        if hasattr(chart, "houses") and len(chart.houses) >= house:
            s = chart.houses[house - 1][0]
            return s.value if hasattr(s, "value") else str(s)
    except Exception:
        pass
    return "未知"


def house_ruler_name(chart: Any, house: int) -> str:
    sign = house_cusp_sign(chart, house)
    return SIGN_RULER_MAP.get(sign, "SUN")


def planet_by_name(chart: Any, name: str) -> Any:
    try:
        for p, info in chart.planets.items():
            if p.value == name:
                return info
    except Exception:
        pass
    return None


def planet_sign(chart: Any, name: str) -> str:
    info = planet_by_name(chart, name)
    return info.sign.value if info and hasattr(info, "sign") else "未知"


def planet_house(chart: Any, name: str) -> int:
    info = planet_by_name(chart, name)
    return info.house if info and hasattr(info, "house") else 0


def planet_dignity_code(chart: Any, name: str) -> str:
    info = planet_by_name(chart, name)
    if not info:
        return "peregrine"
    sign = info.sign
    planet = _resolve_planet(name)
    if not planet:
        return "peregrine"
    if sign in DOMICILE_SIGNS.get(planet, []):
        return "domicile"
    if sign in EXALTATION_SIGNS.get(planet, []):
        return "exaltation"
    if sign in DETRIMENT_SIGNS.get(planet, []):
        return "detriment"
    if sign in FALL_SIGNS.get(planet, []):
        return "fall"
    return "peregrine"


def _resolve_planet(name: str) -> Planet | None:
    try:
        return Planet(name)
    except ValueError:
        return None


def planets_in_house(chart: Any, house: int) -> list[str]:
    result: list[str] = []
    try:
        for p, info in chart.planets.items():
            if getattr(info, "house", 0) == house:
                result.append(p.value)
    except Exception:
        pass
    return result
