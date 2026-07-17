"""
学业方向 — tradition_weight: 0.5。对话体。3宫+9宫+水星+木星。
"""
from __future__ import annotations
from typing import Any
from .base import DomainAnalyzer
from .helpers import plabel, slabel, house_ruler_name, planet_sign, planet_house, planet_dignity_code, house_title


class EducationAnalyzer(DomainAnalyzer):
    domain_key = "education"
    tradition_weight = 0.5

    def _analyze_traditional(self, chart: Any) -> dict[str, Any]:
        r3 = house_ruler_name(chart, 3)
        r3l = plabel(r3)
        r3s = planet_sign(chart, r3)
        r3d = planet_dignity_code(chart, r3)
        r9 = house_ruler_name(chart, 9)
        r9l = plabel(r9)
        r9s = planet_sign(chart, r9)
        r9d = planet_dignity_code(chart, r9)
        merc_s = planet_sign(chart, "MERCURY")
        merc_l = slabel(merc_s)

        structure = (
            f"学习这件事分两块——早期的底子和后来的方向。"
        )

        structure += f"\n\n你小时候的学习环境——3宫主星{r3l}在{slabel(r3s)}。"
        if r3d in ("domicile", "exaltation"):
            structure += "你早期的学习经历整体是顺的——你小时候应该不讨厌上学，或者遇到过让你觉得自己'还可以'的老师。"
        elif r3d in ("detriment", "fall"):
            structure += "早期学习可能不是一帆风顺——也许学校的教学方式不太适合你，也许你小时候觉得自己'不够聪明'。但这不是真的——你只是需要和大多数人不一样的学习方法。"
        else:
            structure += "早期学习经历中等——有好的有不好的，看运气碰到的老师和环境。"

        structure += f"\n\n你适合深造吗——9宫主星{r9l}在{slabel(r9s)}。"
        if r9d in ("domicile", "exaltation"):
            structure += "适合。大学以上的学习能直接带给你机会和社会认可。学术、法律、出版、跨国相关你是有天赋的。"
        elif r9d in ("detriment", "fall"):
            structure += "高等学术路线不是你最舒适的方向——但这绝对不代表你不聪明。你的智慧不一定要在课堂里获取——实践、旅行、和人打交道也是学习。"
        else:
            structure += "是否深造取决于你选的专业和时机——不是必须也不是不适合。"

        structure += (
            f"\n\n你最适合的学习方式是水星在{merc_l}的那种——{_mercury_study(merc_l)}"
        )

        suggestion = "别用别人的学习方法来折磨自己。找到你自己吸收信息最舒服的方式——效率是其次的，先让自己愿意学。"
        return {"structure": structure, "suggestion": suggestion, "theme_conditions": {}}

    def _analyze_modern(self, chart: Any) -> dict[str, Any]:
        psychology = "3宫是你的好奇心引擎——9宫是你寻找意义的雷达。你学什么、怎么学、学到什么深度——不是能力问题，是你内在的'想知道'和'想相信'在驱动你。"
        return {"psychology": psychology, "suggestion": ""}


def _mercury_study(s: str) -> str:
    return {
        "白羊座":"快节奏、有挑战、能动手的——坐着听讲是你最难受的。",
        "金牛座":"有结构、有重复、能慢慢消化的——赶进度对你没用。",
        "双子座":"多样化、能切换、能一边学一边聊的——单一科目会让你无聊到走神。",
        "巨蟹座":"有情感连接、有安全氛围的——在让你舒服的环境里你学得最好。",
        "狮子座":"有表现机会、能被认可的——你的成果需要被看到。",
        "处女座":"有清晰步骤、能拆分细化的——模糊的框架会逼疯你。",
        "天秤座":"能讨论、能分享、有同行者的——一个人啃书不是你的最佳方式。",
        "天蝎座":"能深入、能挖透、有秘密武器感的——肤浅的概览你学不进去。",
        "射手座":"能拓展视野、有远方的——把你关在教室里是对你的惩罚。",
        "摩羯座":"有目标、有计划、有阶梯的——你需要看到'学了这个能干嘛'。",
        "水瓶座":"能创新、能质疑、能自己设计路线的——跟着教材走你会觉得无聊。",
        "双鱼座":"有灵感、有画面、能沉浸的——你靠'感觉对'来学，不是靠死记。",
    }.get(s, "适合你自己的那种。")
