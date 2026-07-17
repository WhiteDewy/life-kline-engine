"""
相位规则（PRD v1.3 §9）

相位是星盘的"语法"，贯穿并修饰所有层面。
提供古占/现占双轨判断 + 容许度系数 + 行星状态调节。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..constants import AspectType


ASPECT_NARRATIVE: dict[str, dict[str, str]] = {
    "CONJUNCTION": {
        "nature": "能量合并放大，不分好坏，看谁合谁",
        "social": "{a}与{b}合流——这两个主题在人生中被绑定在一起，互相放大",
    },
    "TRINE": {
        "nature": "自然顺流，能力轻松配合",
        "risk": "可能缺乏张力，让优势睡过去",
        "social": "{a}与{b}形成顺流——这两个领域天生互相成全，做起来不费力",
    },
    "SEXTILE": {
        "nature": "有机会但需主动争取",
        "social": "{a}与{b}互相配合——有机会，但需要你主动伸手才能拿到",
    },
    "SQUARE": {
        "nature": "内在张力，成长的发动机",
        "risk": "内耗和反复",
        "social": "{a}与{b}存在内在张力——逼你调整方法、升级自己",
    },
    "OPPOSITION": {
        "nature": "外在拉扯，需在两端找平衡",
        "risk": "容易投射到他人身上",
        "social": "{a}与{b}在两端拉扯——需要在两个极端之间找到属于你的位置",
    },
    "QUINCUNX": {
        "nature": "需要适应的不协调",
        "social": "{a}与{b}不兼容但必须共存——需要学会适应而不是对抗",
    },
}


@dataclass
class AspectJudgment:
    aspect_type: str
    nature: str
    risk: str
    traditional: str     # 古占判断
    modern: str          # 现占描述
    social: str          # 现实语境


def judge_aspect(
    aspect_type: str,
    planet_a_label: str,
    planet_b_label: str,
    planet_a_dignified: bool = False,
    planet_b_dignified: bool = False,
) -> AspectJudgment:
    narrative = ASPECT_NARRATIVE.get(aspect_type, ASPECT_NARRATIVE["CONJUNCTION"])
    nature = narrative.get("nature", "")
    risk = narrative.get("risk", "")
    social_template = narrative.get("social", "{a}与{b}形成联动")

    # 古占判断：考虑双方的庙旺状态
    both_strong = planet_a_dignified and planet_b_dignified
    one_strong = planet_a_dignified or planet_b_dignified

    if aspect_type in ("TRINE", "SEXTILE"):
        if both_strong:
            traditional = "吉。两个领域都根基好，顺流助力稳而强。"
        elif one_strong:
            traditional = "偏吉。有一方根基好，顺流中带着一些不确定性。"
        else:
            traditional = "中性偏吉。有顺流的机会，但需要后天努力来承接。"
    elif aspect_type in ("SQUARE", "OPPOSITION"):
        if both_strong:
            traditional = "中性。双方都有实力，冲突是高手过招，能逼出更高水平。"
        elif one_strong:
            traditional = "偏凶。一方根基弱，在张力中容易吃亏，但也是成长的必经之路。"
        else:
            traditional = "凶。双方根基都不稳，需要先夯实自己再面对外部拉扯。"
    elif aspect_type == "CONJUNCTION":
        if both_strong:
            traditional = "强吉。两股力量都强，合并后的人生主题会被放大和强化。"
        elif one_strong:
            traditional = "偏吉。合流中有一股主导力量，另一股需要适应。"
        else:
            traditional = "中性。合在一起的能量需要借力才能发挥。"
    else:
        traditional = "中性。需要适应期，之后才能找到节奏。"

    modern = social_template.format(a=planet_a_label, b=planet_b_label)
    social = modern

    return AspectJudgment(
        aspect_type=aspect_type,
        nature=nature,
        risk=risk,
        traditional=traditional,
        modern=modern,
        social=social,
    )


def get_aspect_strength_modifiers(
    orb: float,
    involves_angular: bool = False,
    involves_chart_ruler: bool = False,
) -> dict[str, float]:
    """获取相位强度修饰因子"""
    return {
        "orb_tightness": min(1.5, max(0.4, 1.0 / max(orb, 0.1))),
        "angular_bonus": 1.2 if involves_angular else 1.0,
        "chart_ruler_bonus": 1.3 if involves_chart_ruler else 1.0,
    }
