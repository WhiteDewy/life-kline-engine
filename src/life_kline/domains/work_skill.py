"""
工作技能 — tradition_weight: 0.5。对话体。6宫=日常工作方式。
"""
from __future__ import annotations
from typing import Any
from .base import DomainAnalyzer
from .helpers import plabel, slabel, house_ruler_name, planet_sign, planet_house, planet_dignity_code, house_title


class WorkSkillAnalyzer(DomainAnalyzer):
    domain_key = "work_skill"
    tradition_weight = 0.5

    def _analyze_traditional(self, chart: Any) -> dict[str, Any]:
        r6 = house_ruler_name(chart, 6)
        r6l = plabel(r6)
        r6s = planet_sign(chart, r6)
        r6h = planet_house(chart, r6)
        r6d = planet_dignity_code(chart, r6)
        mercury_sign = planet_sign(chart, "MERCURY")
        merc_l = slabel(mercury_sign)

        structure = (
            f"说到你怎么做事——6宫主星是{r6l}，落在{slabel(r6s)}。"
        )
        if r6d in ("domicile", "exaltation"):
            structure += (
                f"你的执行力是靠谱的。你能把事情做细、做到位——"
                f"你是那种'交给你就不用再担心'的人。"
                f"但你也要留意——做得太好了，别人会什么都丢给你。"
            )
        elif r6d in ("detriment", "fall"):
            structure += (
                f"你不太适合高强度、重复性的执行类工作——不是说做不了，"
                f"而是这种工作方式消耗你比别人快。"
                f"你需要找到更省力的方式——聪明的流程比蛮力更适合你。"
            )
        else:
            structure += "工作能力中等——选对节奏比选对行业对你的影响更大。"

        structure += (
            f"\n\n你怎么学东西——水星在{merc_l}。{_mercury_work(merc_l)}"
        )

        structure += (
            f"\n\n6宫主星飞到第{r6h}宫——你的日常工作最可能和'{house_title(r6h)}'"
            f"相关。你最容易在这个领域找到上手快、做得顺的工作。"
        )

        suggestion = "日常工作不是事业理想——是你每天花时间在做什么。找到对的节奏比找到高的位置对你的幸福感更重要。"
        return {"structure": structure, "suggestion": suggestion, "theme_conditions": {}}

    def _analyze_modern(self, chart: Any) -> dict[str, Any]:
        psychology = "6宫不只是工作——也是你怎么照顾自己。当你的工作方式对的时候，身体会告诉你；当你一直在消耗的时候，身体也会提醒你。听听身体的信号。"
        return {"psychology": psychology, "suggestion": ""}


def _mercury_work(s: str) -> str:
    return {
        "白羊座":"你学东西喜欢马上实践——看说明书不如直接上手。快，但也容易跳过重要的细节。",
        "金牛座":"你学得慢但记得牢——一旦掌握了就是肌肉记忆。适合需要积累和耐心的技能。",
        "双子座":"你是多线程学习者——能同时学好几样东西。适合需要信息整合和快速切换的工作。",
        "巨蟹座":"你通过'感受'来学习——有情感连接的技能你学得快。适合和人有关的工作。",
        "狮子座":"你学东西需要'被看见'——有观众的时候你效率更高。适合需要表现力的工作。",
        "处女座":"你学东西的过程是系统性的——先拆解再组装。适合需要精度和流程的工作。",
        "天秤座":"你喜欢在讨论中学——一个人看不如两个人聊。适合需要协作和沟通的工作。",
        "天蝎座":"你学东西是往深了钻——不满足于表面。适合需要深度研究和分析的工作。",
        "射手座":"你通过'去经历'来学习——坐在教室里不如走出去。适合需要见识和阅历的工作。",
        "摩羯座":"你学习有计划和纪律——不追求速度追求扎实。适合需要长期积累的专业技能。",
        "水瓶座":"你学东西的方式不太按常规——会自己发明方法论。适合需要创新和独立思考的工作。",
        "双鱼座":"你学东西靠'感觉'——有灵感的时候效率惊人。适合创意和直觉驱动的工作。",
    }.get(s, "你有自己的学习方式。")
