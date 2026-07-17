"""
外形气质 — tradition_weight: 0.5。对话体。
"""
from __future__ import annotations
from typing import Any
from .base import DomainAnalyzer
from .helpers import plabel, slabel, asc_sign, chart_ruler_name, planet_sign, planets_in_house


class AppearanceAnalyzer(DomainAnalyzer):
    domain_key = "appearance"
    tradition_weight = 0.5

    def _analyze_traditional(self, chart: Any) -> dict[str, Any]:
        asc = asc_sign(chart)
        asc_l = slabel(asc)
        cr_name = chart_ruler_name(chart)
        cr_l = plabel(cr_name)
        in_1st = planets_in_house(chart, 1)

        structure = f"说到外形——你的上升在{asc_l}。{_asc_body(asc_l)}"

        if in_1st:
            planet_mentions = [plabel(p) for p in in_1st]
            structure += (
                f"\n\n你的第1宫里有{'、'.join(planet_mentions)}——"
                f"这让你的外形上会带{_planet_look(planet_mentions[0])}"
            )

        structure += (
            f"\n\n命主星{cr_l}的状态决定了你的整体气场。"
            f"外形只是第一印象——你给人的感觉才是别人记住你的原因。"
        )

        suggestion = "形体描述是倾向性的，不是定论。后天的生活方式、锻炼和健康管理会持续影响你的外在状态。"
        return {"structure": structure, "suggestion": suggestion, "theme_conditions": {}}

    def _analyze_modern(self, chart: Any) -> dict[str, Any]:
        psychology = "上升不只是外貌——它是你走进一个新环境时的本能姿态。你可能没意识到你在'扮演'你的上升，但别人看到的第一眼就是这个。"
        return {"psychology": psychology, "suggestion": ""}


def _asc_body(s: str) -> str:
    return {
        "白羊座":"你的身形偏向利落型——不太藏肉，轮廓比较分明。你可能给人一种'这人很运动'的感觉，即使你并不健身。",
        "金牛座":"你的身形偏向匀称或偏圆润——有一种'稳妥'感。你的五官通常比较柔和耐看，不是攻击性的好看，是舒服的好看。",
        "双子座":"你的身形偏瘦长或灵活型——给人感觉比较轻盈。你的表情丰富，说话的时候整个人都在动。",
        "巨蟹座":"你的身形偏圆润或柔软——有一种'让人想抱'的气质。你的眼神通常比较温柔、有亲和力。",
        "狮子座":"你的身形偏挺拔、有骨架感——走路带风。你的发型和穿搭通常会比较引人注目——你不自觉地会把自己收拾得比较'上台面'。",
        "处女座":"你的身形偏干净利落——不太会让自己看起来很邋遢。你的气质是'讲究但不张扬'——注意细节的人会看到你用心的地方。",
        "天秤座":"你的身形比例通常比较匀称——有一种天生的优雅感。你的穿搭品味不会很差——你天然知道怎么让自己看起来舒服。",
        "天蝎座":"你的身形偏结实或有力——不是肌肉多，是气场重。你的眼神最有辨识度——深、有穿透力。",
        "射手座":"你的身形偏高大或舒展——有一种'打开'的感觉。你的笑容通常很有感染力——笑起来整张脸都在发光。",
        "摩羯座":"你的身形偏骨架明显——轮廓清晰。你的气质偏成熟——可能小时候就被人说'显老'，但年纪越大越有味道。",
        "水瓶座":"你的身形偏瘦长或不对称——有一种独特的辨识度。你的穿搭不按主流走——你觉得舒服比好看重要，但往往也好看。",
        "双鱼座":"你的身形偏柔软或偏圆——有一种'没棱角'的舒服感。你的眼神是朦胧的、有故事感的——让人想多看一会儿。",
    }.get(s, "")


def _planet_look(name: str) -> str:
    return {
        "太阳":"一种存在感——你不一定五官最出众，但你就是容易被注意到。",
        "月亮":"一种柔和的气质——你给人的感觉很舒服，没有侵略性。",
        "水星":"一种机灵的感觉——你的眼神在动，整个人给人'聪明'的印象。",
        "金星":"比较出众的五官或气质——你的外形通常是好看的，或者至少让人舒服的。",
        "火星":"一种利落或有力的感觉——你的动作快、轮廓分明。如果你运动，线条会比较明显。",
        "木星":"一种大气感——你的身形可能偏大或气场偏足。你不是小鸟依人型的。",
        "土星":"一种偏瘦或偏冷的气质——你的骨架比较明显，气质偏严肃或偏成熟。",
    }.get(name, "一种独特的气质。")
