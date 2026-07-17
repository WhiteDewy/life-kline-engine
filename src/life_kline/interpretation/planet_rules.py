"""
行星规则 — 四维基准线计算 + 五级先天尊贵评分（PRD v1.3 §4）

四维基准线公式：
  综合 = 先天尊贵×1.0 + 接纳互溶×1.0 + 相位叠加×0.7 + 落宫类型×0.5

所有数值保留在引擎内部。对外通过 narrative_tone 映射为叙事语调。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..constants import (
    Planet,
    Sign,
    DOMICILE_SIGNS,
    EXALTATION_SIGNS,
    DETRIMENT_SIGNS,
    FALL_SIGNS,
    DIGNITY_SCORE_DOMICILE,
    DIGNITY_SCORE_EXALTATION,
    DIGNITY_SCORE_PEREGRINE,
    DIGNITY_SCORE_FALL,
    DIGNITY_SCORE_DETRIMENT,
    DIGNITY_SCORE_TRIPLICITY,
    DIGNITY_SCORE_TERM,
    DIGNITY_SCORE_FACE,
    BASELINE_WEIGHT_DIGNITY,
    BASELINE_WEIGHT_RECEPTION,
    BASELINE_WEIGHT_ASPECT,
    BASELINE_WEIGHT_HOUSE_TYPE,
    DIGNITY_MODIFIER_MULTIPLIER_STRONG,
    DIGNITY_MODIFIER_MULTIPLIER_WEAK,
    get_term_ruler,
    get_face_ruler,
    is_sign_triplicity_ruler,
    get_reception_score,
    get_house_type_score,
    get_aspect_orb_coefficient,
)


# ── 叙事语调映射 ─────────────────────────────────────────
NARRATIVE_TONE_MAP = [
    (6, "天然优势，放手去做"),
    (3, "底子好，注意不要浪费"),
    (-1, "借力可成，不要单打独斗"),
    (-3, "需要迂回策略，正面硬推不划算"),
    (float("-inf"), "先天不足，找替代路径或用接纳补救"),
]


def composite_to_tone(composite: float) -> str:
    for threshold, tone in NARRATIVE_TONE_MAP:
        if composite >= threshold:
            return tone
    return NARRATIVE_TONE_MAP[-1][1]


# ── 数据结构 ──────────────────────────────────────────────

@dataclass
class DignityBreakdown:
    domicile: int = 0
    exaltation: int = 0
    detriment: int = 0
    fall: int = 0
    triplicity: int = 0
    term: int = 0
    face: int = 0
    total: int = 0

    def to_dict(self) -> dict[str, int]:
        return {
            "domicile": self.domicile,
            "exaltation": self.exaltation,
            "detriment": self.detriment,
            "fall": self.fall,
            "triplicity": self.triplicity,
            "term": self.term,
            "face": self.face,
            "total": self.total,
        }


@dataclass
class PlanetBaseline:
    planet: Planet
    sign: Sign
    degree: float
    house: int
    dignity_breakdown: DignityBreakdown = field(default_factory=DignityBreakdown)
    dignity_total: float = 0.0
    house_type_score: float = 0.0
    aspect_overlay_total: float = 0.0
    reception_total: float = 0.0
    composite: float = 0.0
    narrative_tone: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "planet": self.planet.value,
            "sign": self.sign.value,
            "degree": self.degree,
            "house": self.house,
            "dignity_breakdown": self.dignity_breakdown.to_dict(),
            "dignity_total": round(self.dignity_total, 2),
            "house_type_score": round(self.house_type_score, 2),
            "aspect_overlay_total": round(self.aspect_overlay_total, 2),
            "reception_total": round(self.reception_total, 2),
            "composite": round(self.composite, 2),
            "narrative_tone": self.narrative_tone,
        }


# ── 维度一：先天尊贵五级评分 ──────────────────────────────

def compute_essential_dignity(planet: Planet, sign: Sign, degree: float) -> DignityBreakdown:
    bd = DignityBreakdown()
    sign_name = sign.value
    planet_name = planet.value

    domicile_signs = DOMICILE_SIGNS.get(planet, [])
    exaltation_signs = EXALTATION_SIGNS.get(planet, [])
    detriment_signs = DETRIMENT_SIGNS.get(planet, [])
    fall_signs = FALL_SIGNS.get(planet, [])

    if sign in domicile_signs:
        bd.domicile = DIGNITY_SCORE_DOMICILE
    elif sign in exaltation_signs:
        bd.exaltation = DIGNITY_SCORE_EXALTATION
    elif sign in detriment_signs:
        bd.detriment = DIGNITY_SCORE_DETRIMENT
    elif sign in fall_signs:
        bd.fall = DIGNITY_SCORE_FALL

    if is_sign_triplicity_ruler(sign_name, planet_name):
        bd.triplicity = DIGNITY_SCORE_TRIPLICITY

    if get_term_ruler(sign_name, degree) == planet_name:
        bd.term = DIGNITY_SCORE_TERM

    if get_face_ruler(sign_name, degree) == planet_name:
        bd.face = DIGNITY_SCORE_FACE

    bd.total = (
        bd.domicile + bd.exaltation + bd.detriment + bd.fall
        + bd.triplicity + bd.term + bd.face
    )
    return bd


# ── 维度二：落宫类型 ─────────────────────────────────────

def compute_house_type_score(house: int) -> float:
    return get_house_type_score(house)


# ── 维度三：相位叠加 ──────────────────────────────────────

def compute_aspect_overlay(
    aspects: list[dict[str, Any]],
    focus_planet: Planet,
    chart_ruler: Planet | None = None,
    dignity_total: float = 0.0,
) -> float:
    total = 0.0
    for asp in aspects:
        other_planet = asp.get("planet2") if asp.get("planet1") == focus_planet else asp.get("planet1")
        if other_planet is None:
            continue

        base = _aspect_base_score(asp, focus_planet, other_planet, chart_ruler)
        if base == 0.0:
            continue

        orb = float(asp.get("orb", 5))
        coeff = get_aspect_orb_coefficient(orb)
        score = base * coeff

        # 行星状态调节
        if base < 0:
            if dignity_total >= 3:
                score *= DIGNITY_MODIFIER_MULTIPLIER_STRONG
            elif dignity_total <= -3:
                score *= DIGNITY_MODIFIER_MULTIPLIER_WEAK

        total += score
    return total


def _aspect_base_score(
    asp: dict[str, Any],
    focus_planet: Planet,
    other_planet_str: str,
    chart_ruler: Planet | None,
) -> float:
    from ..constants import ASPECT_OVERLAY_BASE_SCORES, Planet as P

    try:
        other = P(other_planet_str)
    except ValueError:
        return 0.0

    nature = asp.get("nature", "")
    aspect_type = asp.get("type", "")

    if aspect_type in ("CONJUNCTION", "conjunction"):
        if other.is_benefic or focus_planet.is_benefic:
            return ASPECT_OVERLAY_BASE_SCORES.get("luminary_conjunction", 0.5)
        if other in (P.SUN, P.MOON) or focus_planet in (P.SUN, P.MOON):
            return ASPECT_OVERLAY_BASE_SCORES["luminary_conjunction"]
        return 0.3

    is_harmonious = nature in ("supportive",)
    is_challenging = nature in ("challenging",)
    other_is_benefic = other.is_benefic
    other_is_malefic = other.is_malefic

    score = 0.0
    if is_harmonious and other_is_benefic:
        score = ASPECT_OVERLAY_BASE_SCORES["benefic_harmonious"]
    elif is_harmonious and other_is_malefic:
        score = ASPECT_OVERLAY_BASE_SCORES["malefic_harmonious"]
    elif is_challenging and other_is_benefic:
        score = ASPECT_OVERLAY_BASE_SCORES["benefic_hard"]
    elif is_challenging and other_is_malefic:
        score = ASPECT_OVERLAY_BASE_SCORES["malefic_hard"]

    if chart_ruler and other == chart_ruler:
        score += ASPECT_OVERLAY_BASE_SCORES["chart_ruler_aspect"]

    return score


# ── 维度四：接纳互溶 ──────────────────────────────────────

def compute_reception_score(
    receptions: list[dict[str, Any]],
    chart_ruler: Planet | None = None,
) -> float:
    total = 0.0
    for rec in receptions:
        receptor = rec.get("receptor", "")
        if not receptor:
            continue
        is_cr = chart_ruler is not None and receptor.upper() == chart_ruler.value
        total += get_reception_score(receptor, is_chart_ruler=is_cr)

        if rec.get("mutual"):
            total += 2.0

    return total


# ── 综合计算 ──────────────────────────────────────────────

def compute_planet_baseline(
    planet: Planet,
    sign: Sign,
    degree: float,
    house: int,
    aspects: list[dict[str, Any]] | None = None,
    receptions: list[dict[str, Any]] | None = None,
    chart_ruler: Planet | None = None,
) -> PlanetBaseline:
    dignity = compute_essential_dignity(planet, sign, degree)
    dignity_total = float(dignity.total)

    house_score = compute_house_type_score(house)

    aspect_total = compute_aspect_overlay(
        aspects or [], planet, chart_ruler, dignity_total,
    )

    reception_total = compute_reception_score(receptions or [], chart_ruler)

    composite = (
        dignity_total * BASELINE_WEIGHT_DIGNITY
        + reception_total * BASELINE_WEIGHT_RECEPTION
        + aspect_total * BASELINE_WEIGHT_ASPECT
        + house_score * BASELINE_WEIGHT_HOUSE_TYPE
    )

    return PlanetBaseline(
        planet=planet,
        sign=sign,
        degree=degree,
        house=house,
        dignity_breakdown=dignity,
        dignity_total=dignity_total,
        house_type_score=house_score,
        aspect_overlay_total=aspect_total,
        reception_total=reception_total,
        composite=composite,
        narrative_tone=composite_to_tone(composite),
    )
