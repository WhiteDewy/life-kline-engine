"""
事业方向 — tradition_weight: 0.7。对话体叙事 + 飞星增强。
"""
from __future__ import annotations
from typing import Any
from .base import DomainAnalyzer
from .helpers import plabel, slabel, house_ruler_name, planet_sign, planet_house, planet_dignity_code, house_title, chart_ruler_name


def _flystar_bridge(ruler: str, from_house: int, to_house: int) -> str:
    """复用 composer 的飞星短句库做领域增强。"""
    from ..composer import _FLYSTAR_SHORT, _flystar_meaning
    return _flystar_meaning(ruler, from_house, to_house)


class CareerAnalyzer(DomainAnalyzer):
    domain_key = "career"
    tradition_weight = 0.7

    def _analyze_traditional(self, chart: Any) -> dict[str, Any]:
        r10 = house_ruler_name(chart, 10)
        r10l = plabel(r10)
        r10s = planet_sign(chart, r10)
        r10h = planet_house(chart, r10)
        r10d = planet_dignity_code(chart, r10)
        r1 = chart_ruler_name(chart)
        r1l = plabel(r1)

        structure = (
            f"事业方面，你的10宫主星是{r10l}，落在{slabel(r10s)}——"
        )
        if r10d in ("domicile", "exaltation"):
            structure += (
                f"这是个好信号。{r10l}庙旺说明你的事业有结构性支撑——"
                f"你不需要靠运气。你靠的是持续积累出来的不可替代性。"
                f"但也因为如此，你的事业不是爆发型的，是稳步往上走的。"
                f"你可能偶尔羡慕那些'一下就冲上去'的人——"
                f"但说实话，你的配置更稳，不容易栽。"
            )
        elif r10d in ("detriment", "fall"):
            structure += (
                f"{r10l}落陷不是说你会失败——是说常规路径对你不太友好。"
                f"你可能试过跟着别人走的路，结果发现走不通或者走得很累。"
                f"这不是能力问题。是你的路径需要自己设计——"
                f"别人靠复制粘贴就能成的路，你不行。但你自己摸索出来的，别人也抄不走。"
                f"很多大器晚成的人就是这种配置——早走弯路的代价，换来晚到的底气。"
            )
        else:
            structure += (
                f"配置不算极强也不算弱——你可以理解为，你的职业发展不靠天赋碾压，"
                f"但可以通过选对赛道和长期积累做到很好。"
            )

        # ── 飞星增强：10宫主飞入 → 社会成就的具象化路径 ──
        if r10h and r10h != 10:
            flystar_text = _flystar_bridge(r10, 10, r10h)
            structure += (
                f"\n\n10宫主星飞到了第{r10h}宫——{house_title(r10h)}。"
                f"{flystar_text}。"
            )
        else:
            structure += (
                f"\n\n你的命主星{r1l}和10宫主星{r10l}的关系，决定了'自我'和'事业'的绑定程度。"
                f"10宫主星飞到了第{r10h}宫——"
                f"你的社会成就更容易通过'{house_title(r10h)}'这个领域来实现。"
                f"说得具体点：你不是在所有事情上都发光，你在{house_title(r10h)}这个领域里是有天分的。"
                f"找到这个领域，比你换十个方向都有用。"
            )

        suggestion = (
            "别拿自己的事业节奏跟别人比。你的10宫主星已经告诉你了——"
            "你的路径是定制的，不是量产的。"
        )
        return {"structure": structure, "suggestion": suggestion, "theme_conditions": {}}

    def _analyze_modern(self, chart: Any) -> dict[str, Any]:
        mc_sign = slabel(planet_sign(chart, "SUN"))  # fallback
        try:
            r10 = house_ruler_name(chart, 10)
            r10s = slabel(planet_sign(chart, r10))
        except Exception:
            r10s = mc_sign
        psychology = (
            f"从心理上说——你对'成功'的定义，很大程度上是由你10宫主星在{r10s}的需求决定的。"
            f"如果你做的事情和这颗星的需求对不上，即使外界觉得你很好，你自己会觉得不对。"
            f"那个'不对'不是你在矫情——是你的星盘在提醒你：这不是你的路。"
        )
        return {"psychology": psychology, "suggestion": ""}
