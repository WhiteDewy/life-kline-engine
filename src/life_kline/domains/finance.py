"""
财务格局 — tradition_weight: 0.8。对话体。
"""
from __future__ import annotations
from typing import Any
from .base import DomainAnalyzer
from .helpers import plabel, house_ruler_name, planet_sign, planet_house, planet_dignity_code


class FinanceAnalyzer(DomainAnalyzer):
    domain_key = "finance"
    tradition_weight = 0.8

    def _analyze_traditional(self, chart: Any) -> dict[str, Any]:
        r2 = house_ruler_name(chart, 2)
        r2l = plabel(r2)
        r2_dig = planet_dignity_code(chart, r2)
        r8 = house_ruler_name(chart, 8)
        r8l = plabel(r8)
        r8_dig = planet_dignity_code(chart, r8)
        r5 = house_ruler_name(chart, 5)
        r5l = plabel(r5)

        structure = (
            f"聊钱之前先说一句：你的财富模式不是'每个月稳定存一笔'的那种——"
            f"你的星盘里的财富结构比你想象的复杂一点。"
        )

        structure += f"\n\n你的正财运看{r2l}。"
        if r2_dig in ("domicile", "exaltation"):
            structure += (
                f"{r2l}庙旺——正财是你的优势通道。你靠主业赚钱的能力是稳的，"
                f"工资、劳动收入、储蓄积累是你的基本盘。"
                f"你不会轻易缺钱，但你也别轻易放弃主业去做'风口'。"
            )
        elif r2_dig in ("detriment", "fall"):
            structure += (
                f"{r2l}落陷——正财不是你的舒适区。你可能试过只靠一份工资生活，"
                f"结果发现不太够或者不太稳。这不是你的问题，是你的配置需要多元收入来分摊风险。"
                f"单一收入对你来说像一条腿走路——不是不行，是容易摔。"
            )
        else:
            structure += (
                f"正财中等——你的收入靠经营，不是等着涨薪的那种。"
                f"你需要主动规划收入结构。"
            )

        structure += f"\n\n偏财运看{r8l}。"
        if r8_dig in ("domicile", "exaltation"):
            structure += (
                f"{r8l}庙旺——偏财嗅觉是你的隐藏技能。投资、合伙分红、资源整合——"
                f"这些'让别人钱为你工作'的方式你是有天赋的。"
            )
            if r2_dig in ("detriment", "fall"):
                structure += "你的偏财运明显强于正财。主业保底，偏财发力的结构对你最合理。"
        elif r8_dig in ("detriment", "fall"):
            structure += (
                f"{r8l}落陷——偏财不是你的菜。投资、借贷、风险资产——"
                f"这些领域你要格外谨慎。不是不能碰，是不要碰大的。"
                f"有一个靠谱的理财顾问或者只用'亏了也不影响生活'的钱去试——这两条对你会很有用。"
            )
        else:
            structure += "偏财中等——可以配置，但不要押重注。"

        structure += (
            f"\n\n你的投机运（5宫{r5l}）和群体财（11宫）也是财富拼图的一部分。"
            f"你可以回想一下——你在哪些年龄段觉得赚钱特别顺？又在哪些时候特别紧？"
            f"这不是运气好坏的随机波动，是你的四财宫周期在起作用。"
        )

        suggestion = (
            "理财的核心——把自己最强的财宫当成主力，弱的那条不要硬押。"
            "你只需要做对一次关键选择，比做对十次小动作值钱。"
        )
        return {"structure": structure, "suggestion": suggestion, "theme_conditions": {}}

    def _analyze_modern(self, chart: Any) -> dict[str, Any]:
        psychology = "心理层面说一句——你和钱的关系，很大程度是由你2宫主星的状态决定的。不只是'能赚多少'，更是'你觉得自己值多少'。这个底层信念会影响你谈薪资、定价、投资决策的每一个环节。"
        return {"psychology": psychology, "suggestion": ""}
