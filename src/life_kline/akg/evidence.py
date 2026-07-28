"""
evidence.py — AKG 证据收集与打分

从持久化 report_data 中，按 ThemeDef 抽取带权证据项。
证据风格镜像 engine_astrologer.collect_evidence 的前缀字符串
（【落宫落座】/【尊贵】/【相位】/【综合】/【宫位】/【主题相位】）。

铁律：只引用已算好的星盘事实，不重新解读、不发明判断。
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

from .theme_catalog import ThemeDef


# 行星 key ↔ 中文名（用于解析 aspect_signature / major_aspects.title）
PLANET_CN: dict[str, str] = {
    "SUN": "太阳", "MOON": "月亮", "MERCURY": "水星", "VENUS": "金星",
    "MARS": "火星", "JUPITER": "木星", "SATURN": "土星", "URANUS": "天王星",
    "NEPTUNE": "海王星", "PLUTO": "冥王星",
    "NORTH_NODE": "北交点", "SOUTH_NODE": "南交点",
}
CN_TO_KEY: dict[str, str] = {v: k for k, v in PLANET_CN.items()}


@dataclass
class EvidenceItem:
    """单条证据。"""
    source: str        # planet / house / aspect
    text: str          # 前缀字符串
    weight: float      # 0-1
    polarity: str      # support / challenge / neutral

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "text": self.text,
            "weight": round(self.weight, 3),
            "polarity": self.polarity,
        }


# ── report_data 取数辅助 ──────────────────────────────────────

def _planets(report_data: dict) -> dict:
    return report_data.get("natal_chart", {}).get("planets", {}) or {}


def _houses(report_data: dict) -> list:
    return report_data.get("natal_chart", {}).get("houses", []) or []


def _major_aspects(report_data: dict) -> list:
    return report_data.get("natal_chart", {}).get("major_aspects", []) or []


def _baselines(report_data: dict) -> dict:
    return report_data.get("_analysis_evidence", {}).get("planet_baselines", {}) or {}


# ── 尊贵度 → 权重/polarity ────────────────────────────────────

_DIGNITY_WEIGHT: dict[str, tuple[float, str]] = {
    "domicile": (1.0, "support"),
    "exaltation": (0.9, "support"),
    "detriment": (0.6, "challenge"),
    "fall": (0.6, "challenge"),
    "peregrine": (0.4, "neutral"),
}


def _dignity_weight(dignity: str) -> tuple[float, str]:
    return _DIGNITY_WEIGHT.get(dignity, (0.3, "neutral"))


# ── 收集 ──────────────────────────────────────────────────────

def collect_theme_evidence(theme: ThemeDef, report_data: dict) -> list[EvidenceItem]:
    """按 ThemeDef 从 report_data 抽取证据项。"""
    evidence: list[EvidenceItem] = []
    planets = _planets(report_data)
    baselines = _baselines(report_data)

    # 1. 主题关联行星
    for p in theme.planets:
        pinfo = planets.get(p)
        if not pinfo:
            continue
        name_zh = PLANET_CN.get(p, p)
        sign_label = pinfo.get("sign_label", "未知")
        house = pinfo.get("house", 0)
        house_title = pinfo.get("house_title", "")

        evidence.append(EvidenceItem(
            source="planet",
            text=f"【落宫落座】{name_zh}落{sign_label}座第{house}宫「{house_title}」",
            weight=0.5,
            polarity="neutral",
        ))

        dignity = pinfo.get("dignity", "")
        dignity_label = pinfo.get("dignity_label", "")
        w, pol = _dignity_weight(dignity)
        evidence.append(EvidenceItem(
            source="planet",
            text=f"【尊贵】{name_zh}{dignity_label}（{dignity}）",
            weight=w,
            polarity=pol,
        ))

        for asp in (pinfo.get("aspect_signature") or [])[:4]:
            evidence.append(EvidenceItem(
                source="aspect",
                text=f"【相位】{asp}",
                weight=0.55,
                polarity="neutral",
            ))

        baseline = baselines.get(p)
        if baseline:
            composite = baseline.get("composite", 0)
            tone = baseline.get("narrative_tone", "")
            evidence.append(EvidenceItem(
                source="planet",
                text=f"【综合】{name_zh}综合强度{composite}（{tone}）",
                weight=min(abs(composite) / 10.0, 1.0),
                polarity="support" if composite > 0 else "challenge",
            ))

    # 2. 主题关联宫位
    for h in theme.houses:
        entry = next((x for x in _houses(report_data) if x.get("house") == h), None)
        if entry:
            evidence.append(EvidenceItem(
                source="house",
                text=f"【宫位】第{h}宫「{entry.get('title', '')}」",
                weight=0.3,
                polarity="neutral",
            ))

    # 3. 主题关键相位对
    for a, b in theme.aspect_pairs:
        cn_a = PLANET_CN.get(a, a)
        cn_b = PLANET_CN.get(b, b)
        # 优先从 major_aspects 找同时含两者的条目
        hit = False
        for asp in _major_aspects(report_data):
            title = asp.get("title", "")
            if cn_a in title and cn_b in title:
                strength = asp.get("strength", 0.5)
                nature = asp.get("nature", "")
                pol = "support" if nature == "supportive" else ("challenge" if nature == "challenging" else "neutral")
                evidence.append(EvidenceItem(
                    source="aspect",
                    text=f"【主题相位】{title}（{nature}, {strength}）",
                    weight=min(strength, 1.0),
                    polarity=pol,
                ))
                hit = True
        # 兜底：扫 a 的 aspect_signature 是否提及 b
        if not hit:
            pinfo_a = planets.get(a)
            if pinfo_a:
                for asp in (pinfo_a.get("aspect_signature") or []):
                    if cn_b in asp:
                        evidence.append(EvidenceItem(
                            source="aspect",
                            text=f"【主题相位】{asp}",
                            weight=0.6,
                            polarity="neutral",
                        ))
                        break

    return evidence


# ── 打分 ──────────────────────────────────────────────────────

def score_theme(evidence: list[EvidenceItem]) -> float:
    """主题激活强度：饱和曲线，证据越多越强但不线性堆叠。

    1-exp(-sum/4)：1 条满权证据≈0.22，3 条≈0.53，6 条≈0.78，10+ 条趋近 1。
    避免真实报告里证据多就全部触顶 1.0、失去区分度。
    """
    if not evidence:
        return 0.0
    total = sum(e.weight for e in evidence)
    return 1.0 - math.exp(-total / 4.0)


def theme_confidence(evidence: list[EvidenceItem]) -> float:
    """证据融合置信度：数量 × 极性一致性。

    evidence fusion 的核心：当 support 与 challenge 证据冲突时，置信度下降
    （星盘给出矛盾信号 → 不该高置信下结论）。极性一致时置信度最高。
    """
    if not evidence:
        return 0.0
    base = min(0.3 + len(evidence) * 0.08, 0.85)
    sup = sum(1 for e in evidence if e.polarity == "support")
    chl = sum(1 for e in evidence if e.polarity == "challenge")
    polar_total = sup + chl
    if polar_total == 0:
        consistency = 1.0
    else:
        consistency = abs(sup - chl) / polar_total  # 1=一致, 0=对半冲突
    return base * (0.65 + 0.35 * consistency)
