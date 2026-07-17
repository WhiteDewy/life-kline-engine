"""
婚姻画像 — tradition_weight: 0.7。对话体。
"""
from __future__ import annotations
from typing import Any
from .base import DomainAnalyzer
from .helpers import plabel, slabel, house_ruler_name, planet_sign, planet_house, planet_dignity_code, house_title, chart_ruler_name


class MarriageAnalyzer(DomainAnalyzer):
    domain_key = "marriage"
    tradition_weight = 0.7

    def _analyze_traditional(self, chart: Any) -> dict[str, Any]:
        r7 = house_ruler_name(chart, 7)
        r7l = plabel(r7)
        r7s = planet_sign(chart, r7)
        r7h = planet_house(chart, r7)
        r7d = planet_dignity_code(chart, r7)

        structure = f"婚姻方面，你的7宫主星是{r7l}，落在{slabel(r7s)}。"
        if r7d in ("domicile", "exaltation"):
            structure += (
                f"{r7l}庙旺——你的婚姻有结构性支撑。这意味着你遇到的人整体素质不会差，"
                f"你的婚姻质量是有保障的。你不一定早婚，但你的婚运不差。"
            )
        elif r7d in ("detriment", "fall"):
            structure += (
                f"{r7l}落陷——婚姻是你人生中需要认真学习的课题。不是说你不会幸福，"
                f"而是说'选对人'对你来说比大多数人都重要。你选错了代价很大。"
                f"好的一面是，一旦你选对了，你的婚姻会比那些轻轻松松就结婚的人更清醒、更有边界。"
            )
        else:
            structure += "婚姻质量中等——好的婚姻需要你主动经营，不是顺其自然就能好的。"

        structure += (
            f"\n\n你的7宫主飞到了第{r7h}宫。你的伴侣最可能通过'{house_title(r7h)}'"
            f"这个领域进入你的生活。说得具体点——"
            f"你在{house_title(r7h)}相关的事情上遇到的人，比你在"
            f"相亲软件上滑到的人更有可能成为你的长期伴侣。"
        )

        suggestion = (
            "选伴侣之前先想清楚：你需要的不是'让你心动的人'——"
            "你需要的是'让你的7宫主星感到舒服的人'。心动是金星的活儿，长期是7宫的活儿。"
        )
        return {"structure": structure, "suggestion": suggestion, "theme_conditions": {}}

    def _analyze_modern(self, chart: Any) -> dict[str, Any]:
        psychology = "下降点是你潜意识里渴望的特质——你在伴侣身上寻找的，往往是你自己不敢承认的那一面。你的伴侣某种程度上是你的镜子。"
        return {"psychology": psychology, "suggestion": ""}
