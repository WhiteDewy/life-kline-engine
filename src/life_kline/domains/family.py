"""
原生家庭 — tradition_weight: 0.7。古占唯一标准：4宫主=父亲，10宫主=母亲。
"""
from __future__ import annotations
from typing import Any
from .base import DomainAnalyzer
from .helpers import plabel, slabel, house_ruler_name, planet_sign, planet_dignity_code


class FamilyAnalyzer(DomainAnalyzer):
    domain_key = "family"
    tradition_weight = 0.7

    def _analyze_traditional(self, chart: Any) -> dict[str, Any]:
        r4 = house_ruler_name(chart, 4)
        r4l = plabel(r4)
        r4s = planet_sign(chart, r4)
        r4d = planet_dignity_code(chart, r4)
        r10 = house_ruler_name(chart, 10)
        r10l = plabel(r10)
        r10s = planet_sign(chart, r10)
        r10d = planet_dignity_code(chart, r10)

        structure = "聊家庭之前先说明——古典占星里，4宫主星就是父亲，10宫主星就是母亲。和现代占星不一样，我们不混着看。\n\n"

        structure += f"你的父亲——4宫主星{r4l}落在{slabel(r4s)}。"
        if r4d in ("domicile", "exaltation"):
            structure += "父亲在你的成长中是正向的角色。他大概率是有能力的、有担当的——不管他本人是什么性格，他在你人生中起到的是'支撑'的作用。"
        elif r4d in ("detriment", "fall"):
            structure += "父亲在你的成长中可能遇到了一些客观困难——事业、健康或个人状态的问题。这不代表他不爱你——但他在你的人生里可能更像'你需要去理解的人'，而不是'能给你支撑的人'。"
        else:
            structure += "父亲的角色在你生命中的影响是存在的，只是方式不那么直接。他可能不是那种'什么事都管'的家长，但他在关键时刻的态度会影响你很多年。"

        structure += f"\n\n你的母亲——10宫主星{r10l}落在{slabel(r10s)}。"
        if r10d in ("domicile", "exaltation"):
            structure += "母亲是你在童年里看到的最有力量的形象之一。她独立、有主见——你从她身上学会了什么叫'在社会中站住'。"
        elif r10d in ("detriment", "fall"):
            structure += "母亲可能在自己的社会角色或人生方向上经历过一些困境——这对你会有无形的影响。你成年后对'权威'和'照顾'的理解，很大程度上是被她塑造的。"
        else:
            structure += "母亲的角色对你来说是重要的——她的养育方式会在你成年后的关系中持续回响。你可能不会马上意识到，但你对'被照顾'的期待和她有很大关系。"

        suggestion = (
            "理解父母，不是要你原谅谁或者怪谁——是让你看清楚："
            "你现在的某些模式不是凭空来的。看见了，你才有选择权。"
        )
        return {"structure": structure, "suggestion": suggestion, "theme_conditions": {}}

    def _analyze_modern(self, chart: Any) -> dict[str, Any]:
        psychology = "4宫也是你内心安全感的来源——你童年住过的房子、对'家'的定义。这些情感残留会持续影响你成年后的选择——即使你早就搬出去了。"
        return {"psychology": psychology, "suggestion": ""}
