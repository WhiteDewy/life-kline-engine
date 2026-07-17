"""
亲子关系 — tradition_weight: 0.5。对话体。
"""
from __future__ import annotations
from typing import Any
from .base import DomainAnalyzer
from .helpers import plabel, slabel, house_ruler_name, planet_sign, planet_house, planet_dignity_code, house_title


class ChildrenAnalyzer(DomainAnalyzer):
    domain_key = "children"
    tradition_weight = 0.5

    def _analyze_traditional(self, chart: Any) -> dict[str, Any]:
        r5 = house_ruler_name(chart, 5)
        r5l = plabel(r5)
        r5s = planet_sign(chart, r5)
        r5h = planet_house(chart, r5)
        r5d = planet_dignity_code(chart, r5)
        moon_sign = planet_sign(chart, "MOON")
        moon_l = slabel(moon_sign)

        structure = f"亲子关系看5宫——你的5宫主星是{r5l}，落在{slabel(r5s)}。"
        if r5d in ("domicile", "exaltation"):
            structure += (
                "这是个好信号。你和孩子的关系天然比较顺畅——"
                "你身上有一种让孩子感到安全的特质。不是你会不会教——"
                "是你本身就是孩子会信任的那种大人。"
            )
        elif r5d in ("detriment", "fall"):
            structure += (
                "亲子关系可能是你需要学习的课题。这不代表你不会是好家长——"
                "而是说这个领域不会'自动就好'，需要你主动投入和调整。"
                "你可能会发现自己的养育方式和预想的不太一样——这很正常。"
            )
        else:
            structure += "亲子关系的发展取决于你后天的用心程度。好消息是——5宫是可以经营的。"

        structure += (
            f"\n\n你的养育方式看月亮——月亮在{moon_l}。"
            f"你给孩子的爱是通过{_moon_parent_style(moon_l)}来传递的。"
            f"你的孩子可能不一定会说'你好温柔'——"
            f"但ta会从{_moon_child_feels(moon_l)}中感受到你的爱。"
        )

        structure += (
            f"\n\n5宫主星飞到了第{r5h}宫——孩子最可能在你人生的'{house_title(r5h)}'"
            f"领域对你有重大的影响。孩子不是你的附属——ta们是来让你成长的。"
        )

        suggestion = "亲子的核心不是'教好孩子'——是用孩子照见你自己。孩子呈现的特质，往往是你自己未被活出来的那面。"
        return {"structure": structure, "suggestion": suggestion, "theme_conditions": {}}

    def _analyze_modern(self, chart: Any) -> dict[str, Any]:
        psychology = "你对孩子的期待和担忧——往往是你自己童年的延续。你的内在小孩会在你对待自己孩子的时候重新冒出来。这是功课，也是礼物。"
        return {"psychology": psychology, "suggestion": ""}


def _moon_parent_style(s: str) -> str:
    return {"白羊座":"鼓励和行动——你会带孩子去尝试、去挑战、去'别怕'",
            "金牛座":"稳定的陪伴和实实在在的照顾——吃好、穿暖、有人在",
            "双子座":"聊天和分享——你会跟孩子讲道理、讲世界、讲所有有趣的事",
            "巨蟹座":"最传统的'家'的感觉——温暖的庇护所，无条件的接纳",
            "狮子座":"欣赏和骄傲——你会让孩子觉得'我在你眼里是特别的'",
            "处女座":"用心和细节——你记得孩子的每一个习惯、每一个需要",
            "天秤座":"公平和尊重——你是一个会蹲下来跟孩子讲道理的大人",
            "天蝎座":"保护和忠诚——你是孩子最坚硬的盾，但可能不太会说'我爱你'",
            "射手座":"自由和空间——你会带孩子去看世界，让ta自己去探索",
            "摩羯座":"责任和示范——你不是嘴上教，是活给孩子看",
            "水瓶座":"尊重和独立——你会把孩子当独立的个体，而不是'我的孩子'",
            "双鱼座":"共情和包容——你能感受到孩子说不出来的那些情绪"}.get(s, "你自己独特的方式")


def _moon_child_feels(s: str) -> str:
    return {"白羊座":"你从不扫兴的鼓励","金牛座":"你一直都在的陪伴",
            "双子座":"你认真听ta说话的专注","巨蟹座":"你无条件站在ta这边",
            "狮子座":"你为ta骄傲的眼神","处女座":"你把ta每一件事都放在心上",
            "天秤座":"你把ta当大人尊重的态度","天蝎座":"你绝不会让任何人伤害ta",
            "射手座":"你带ta见过的那个更大的世界","摩羯座":"你从未说出口但ta能感受到的在乎",
            "水瓶座":"你从来不强迫ta成为别人","双鱼座":"你比任何人都懂ta的感受"}.get(s, "那些细微的瞬间")
