"""Engine data enrichment functions for dossier building.

Every engine-computed fact that lives in the report JSON is harvested here
and added as structured ChartEvidence to the dossier.
"""
from __future__ import annotations

from typing import Any

from .models import ChartEvidence, EvidenceSource, stable_evidence_id


def _evidence(
    source: EvidenceSource,
    title: str,
    fact: str,
    payload: dict[str, Any],
    *,
    importance: int,
    current: bool = False,
    supportive: bool | None = None,
) -> ChartEvidence:
    return ChartEvidence(
        evidence_id=stable_evidence_id(source, payload),
        source=source,
        title=title,
        fact=fact,
        payload=payload,
        importance=importance,
        current=current,
        supportive=supportive,
    )


_DIGNITY_DEEP_LABELS: dict[str, str] = {
    "triplicity_lord": "三分主星",
    "term_lord": "界主星",
    "face_lord": "面主星",
    "combust": "燃烧",
    "cazimi": "日核",
    "oriental": "东出",
    "occidental": "西入",
    "hayz": "喜乐",
    "in_joy": "喜乐宫",
}

_ASPECT_PATTERN_LABELS: dict[str, str] = {
    "grand_trine": "大三角",
    "t_square": "T三角",
    "grand_cross": "大十字",
    "kite": "风筝",
}

_ENCLOSURE_LABELS: dict[str, str] = {
    "benefic_enclosure": "吉星夹辅",
    "malefic_siege": "凶星夹制",
    "mixed_enclosure": "吉凶夹",
}

_FLYSTAR_DIMENSIONS: dict[str, str] = {
    "dignity_score": "尊贵",
    "aspect_score": "相位",
    "reception_score": "接纳",
    "house_score": "宫位",
    "special_score": "特殊",
}


def _planet_cn(report_data: dict[str, Any], planet: str) -> str:
    chars = report_data.get("planet_characters", {}).get("planet_characters", {})
    profile = chars.get(planet, {})
    persona = profile.get("persona", {})
    return str(persona.get("name_zh", planet))


def enrich_dignity_deep(
    report_data: dict[str, Any], planet: str, evidence: list[ChartEvidence]
) -> list[ChartEvidence]:
    """古占尊贵细分：三分主星、界主、面主、燃烧、日核、东出、喜乐。"""
    breakdown = (
        report_data.get("_analysis_evidence", {})
        .get("dignity_breakdown", {})
        .get(planet, {})
    )
    if not breakdown:
        return evidence
    for key, label in _DIGNITY_DEEP_LABELS.items():
        val = breakdown.get(key)
        if val is None:
            continue
        if isinstance(val, bool) and not val:
            continue
        if isinstance(val, str) and not val:
            continue
        fact = label if isinstance(val, bool) else f"{label}: {val}"
        evidence.append(_evidence(
            EvidenceSource.NATAL_DIGNITY, "尊贵细分", fact,
            {"planet": planet, "field": key, "value": val},
            importance=55, supportive=True if isinstance(val, bool) else None,
        ))
    return evidence


def enrich_aspect_patterns(
    report_data: dict[str, Any], planet: str, evidence: list[ChartEvidence]
) -> list[ChartEvidence]:
    """相位格局：大三角、T三角、大十字、风筝——仅涉及当前行星的格局。"""
    patterns = (
        report_data.get("advanced_patterns", {}).get("aspect_patterns", []) or []
    )
    name_cn = _planet_cn(report_data, planet)
    for pat in patterns:
        if not isinstance(pat, dict):
            continue
        ptype = pat.get("pattern_type", "")
        planets_in = [str(p) for p in pat.get("planets", [])]
        label = _ASPECT_PATTERN_LABELS.get(ptype, ptype)
        if name_cn not in planets_in and planet not in planets_in:
            continue
        severity = pat.get("severity", "")
        interp = pat.get("interpretation", "")[:120]
        fact = (
            f"{label}（{'、'.join(planets_in)}）"
            f"{'·' + severity if severity else ''}: {interp}"
        )
        evidence.append(_evidence(
            EvidenceSource.NATAL_ASPECT, "格局", fact,
            {"planet": planet, "pattern_type": ptype, "planets": planets_in},
            importance=70, supportive=None,
        ))
    return evidence


def enrich_enclosures(
    report_data: dict[str, Any], planet: str, evidence: list[ChartEvidence]
) -> list[ChartEvidence]:
    """夹辅/夹制格局——仅涉及当前行星的夹制。"""
    enclosures = (
        report_data.get("advanced_patterns", {}).get("enclosure_patterns", []) or []
    )
    name_cn = _planet_cn(report_data, planet)
    for enc in enclosures:
        if not isinstance(enc, dict):
            continue
        enclosed = enc.get("enclosed_planet", "")
        if enclosed != name_cn and enclosed != planet:
            continue
        ptype = enc.get("pattern_type", "")
        label = _ENCLOSURE_LABELS.get(ptype, ptype)
        desc = enc.get("description", "")[:100]
        supportive = ptype == "benefic_enclosure"
        evidence.append(_evidence(
            EvidenceSource.NATAL_RECEPTION, "夹辅夹制", f"{label}: {desc}",
            {"planet": planet, **enc},
            importance=68, supportive=supportive,
        ))
    return evidence


def enrich_flystar_details(
    report_data: dict[str, Any], planet: str, evidence: list[ChartEvidence]
) -> list[ChartEvidence]:
    """飞星吉凶分维得分（尊贵/相位/接纳/宫位/特殊五维）。"""
    fortunes = (
        report_data.get("advanced_patterns", {}).get("flystar_fortunes", {}) or {}
    )
    for key, fortune in fortunes.items():
        if not isinstance(fortune, dict):
            continue
        if not key.startswith(planet) and planet not in key:
            continue
        dims = []
        for fk, flabel in _FLYSTAR_DIMENSIONS.items():
            score = fortune.get(fk, 0)
            if score:
                dims.append(f"{flabel}={score}")
        if dims:
            summary = fortune.get("summary", "")[:80]
            rec = fortune.get("recommendation", "")[:80]
            fact = (
                f"飞星{key}: {'，'.join(dims)} | {summary}"
                + (f" → {rec}" if rec else "")
            )
            evidence.append(_evidence(
                EvidenceSource.NATAL_FLYSTAR, "飞星吉凶", fact,
                {"planet": planet, "flystar_key": key, **fortune},
                importance=62,
                supportive=fortune.get("fortune_level") == "fortunate",
            ))
    return evidence


def enrich_transits(
    report_data: dict[str, Any], planet: str, evidence: list[ChartEvidence]
) -> list[ChartEvidence]:
    """每日行运分层注入：哪些行运触发了这颗行星。"""
    transits = report_data.get("_transits", []) or []
    if not transits:
        return evidence
    name_cn = _planet_cn(report_data, planet)
    relevant = [
        t for t in transits if isinstance(t, dict) and (
            t.get("natal_planet") == planet
            or t.get("transiting_planet") == planet
            or name_cn in str(t.get("highlight", ""))
            or name_cn in str(t.get("natal_label", ""))
        )
    ]
    for t in relevant[:5]:
        fact = (
            t.get("highlight", "")
            or f"行运{t.get('transiting_label','')}{t.get('aspect_label','')}"
               f"本命{t.get('natal_label','')}"
        )
        evidence.append(_evidence(
            EvidenceSource.TODAY_ACTIVATION, "今日行运", fact,
            {"planet": planet, **t},
            importance=85 if t.get("orb", 99) <= 3 else 60,
            current=True,
        ))
    return evidence


def enrich_interceptions(
    report_data: dict[str, Any], planet: str, evidence: list[ChartEvidence]
) -> list[ChartEvidence]:
    """截夺星座检测。"""
    info = (
        report_data.get("advanced_patterns", {}).get("interception_info", {}) or {}
    )
    intercepted = info.get("intercepted_signs", {}) or {}
    expanded = info.get("expanded_rulers", {}) or {}
    if not intercepted and not expanded:
        return evidence
    for house, sign in intercepted.items():
        evidence.append(_evidence(
            EvidenceSource.NATAL_PLACEMENT, "截夺",
            f"第{house}宫截夺{sign}",
            {"planet": planet, "house": house, "intercepted_sign": sign},
            importance=50, supportive=False,
        ))
    for ruler, houses in expanded.items():
        evidence.append(_evidence(
            EvidenceSource.NATAL_RULERSHIP, "截夺扩展",
            f"{ruler}因截夺扩展至{'、'.join(str(h)+'宫' for h in houses)}",
            {"planet": planet, "ruler": ruler, "expanded_houses": houses},
            importance=50,
        ))
    return evidence


def enrich_hero_context(
    report_data: dict[str, Any], planet: str, evidence: list[ChartEvidence]
) -> list[ChartEvidence]:
    """命盘基调：上升、命主星、核心叙事。"""
    hero = report_data.get("hero", {}) or {}
    if not hero:
        return evidence
    asc_label = hero.get("asc_label", "")
    chart_ruler_label = hero.get("chart_ruler_label", "")
    core_theme = hero.get("core_theme", "")[:200]
    if asc_label and chart_ruler_label:
        evidence.append(_evidence(
            EvidenceSource.NATAL_PLACEMENT, "命盘基调",
            f"上升{asc_label}，命主星{chart_ruler_label}。{core_theme}",
            {"planet": planet, **hero},
            importance=60,
        ))
    return evidence
