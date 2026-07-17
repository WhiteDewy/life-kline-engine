"""
事业合伙 — tradition_weight: 0.8。对话体。
"""
from __future__ import annotations
from typing import Any
from .base import DomainAnalyzer
from .helpers import plabel, slabel, house_ruler_name, planet_sign, planet_house, planet_dignity_code, chart_ruler_name, house_title


class PartnershipAnalyzer(DomainAnalyzer):
    domain_key = "partnership"
    tradition_weight = 0.8

    def _analyze_traditional(self, chart: Any) -> dict[str, Any]:
        r7 = house_ruler_name(chart, 7)
        r7l = plabel(r7)
        r7s = planet_sign(chart, r7)
        r7h = planet_house(chart, r7)
        r7d = planet_dignity_code(chart, r7)
        r10 = house_ruler_name(chart, 10)
        r10l = plabel(r10)

        structure = (
            f"合伙这件事和婚姻看的是同一个7宫——但角度不太一样。"
            f"你的7宫主星是{r7l}，落在{slabel(r7s)}。"
        )
        if r7d in ("domicile", "exaltation"):
            structure += (
                "你是适合合伙的——你能找到能力强、互补你的人。"
                "合作对你来说是乘法，不是加法。"
            )
        elif r7d in ("detriment", "fall"):
            structure += (
                "合伙不是你的舒适区。你不是不能合伙——"
                "但你需要比别人更谨慎地选人。选错一个合伙人对你的损害，"
                "比单独做事犯的错大多了。"
            )
        else:
            structure += "合伙可以，但不能看感觉。你需要靠制度和契约来保障，而不是靠信任。"

        structure += (
            f"\n\n你的7宫主星飞到了第{r7h}宫——你最容易在'{house_title(r7h)}'"
            f"这个领域遇到你的合伙人。不是说你只能在这个领域找——"
            f"而是说这个领域的人跟你天然更合拍。"
        )

        structure += (
            f"\n\n有一个值得关注的点：你的10宫主星是{r10l}——"
            f"合伙能不能推动你的事业，主要看7宫主和10宫主之间的相位关系。"
            f"这两个如果搭得好，合伙是你事业的加速器；搭得不好，合伙反而会消耗你的精力。"
        )

        suggestion = "好的合伙人是你互补的人——不是你喜欢的。签合同之前，先把利益分配谈清楚。好的关系也需要好的边界。"
        return {"structure": structure, "suggestion": suggestion, "theme_conditions": {}}

    def _analyze_modern(self, chart: Any) -> dict[str, Any]:
        psychology = "合伙关系不只是契约——它也是你'如何跟人分享权力'的心理投射。你在合作中是控制型还是放手型——这个模式在你自己意识到之前就已经定型了。"
        return {"psychology": psychology, "suggestion": ""}
