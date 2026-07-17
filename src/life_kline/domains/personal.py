"""
人格底色 — 接入叙事引擎。落座Base+落宫Base+尊严+宫位类型四层叠加。
"""
from __future__ import annotations
from typing import Any
from .base import DomainAnalyzer
from .helpers import slabel, planet_sign, planet_house, planet_dignity_code
from ..interpretation.narrative_engine import (
    build_sun_narrative, build_moon_narrative, build_asc_narrative,
    build_sun_house, build_moon_house,
)
from ..constants import ANGULAR_HOUSES, SUCCEDENT_HOUSES


class PersonalAnalyzer(DomainAnalyzer):
    domain_key = "personal"
    tradition_weight = 0.5

    def _analyze_traditional(self, chart: Any) -> dict[str, Any]:
        def _htype(h: int) -> str:
            return "angular" if h in ANGULAR_HOUSES else "succedent" if h in SUCCEDENT_HOUSES else "cadent"

        sun_s = slabel(planet_sign(chart, "SUN"))
        sun_h = planet_house(chart, "SUN")
        moon_s = slabel(planet_sign(chart, "MOON"))
        moon_h = planet_house(chart, "MOON")
        asc_l = slabel(planet_sign(chart, "SUN"))  # placeholder, real asc from chart

        parts = []

        # 太阳：落座 + 落宫
        sun = build_sun_narrative(
            sun_s, dignity=planet_dignity_code(chart, "SUN"), house_type=_htype(sun_h),
        )
        sun += "\n\n" + build_sun_house(sun_h)
        parts.append(sun)

        # 月亮：落座 + 落宫
        moon = build_moon_narrative(
            moon_s, dignity=planet_dignity_code(chart, "MOON"), house_type=_htype(moon_h),
        )
        moon += "\n\n" + build_moon_house(moon_h)
        parts.append(moon)

        structure = "\n\n".join(parts)

        suggestion = (
            "了解自己的优先级：先搞清楚你的月亮需要什么——因为不管外面怎么变，"
            "月亮稳了，你其他部分才有底气发挥。"
        )
        return {"structure": structure, "suggestion": suggestion, "theme_conditions": {}}

    def _analyze_modern(self, chart: Any) -> dict[str, Any]:
        moon_s = slabel(planet_sign(chart, "MOON"))
        sun_s = slabel(planet_sign(chart, "SUN"))
        psychology = (
            f"从心理层面说——你的人格不是一块石头，是三层叠在一起的。"
            f"最外面是上升（给世界看的），中间是太阳在{sun_s}（自己想成为的样子），"
            f"最里面是月亮在{moon_s}（不用跟任何人解释的真实的你）。"
            f"这三层越一致你越省力，越不一致你越容易内耗。"
        )
        return {"psychology": psychology, "suggestion": ""}
