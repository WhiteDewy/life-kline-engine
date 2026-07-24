"""
桃花感情 — tradition_weight: 0.4。对话体。
"""
from __future__ import annotations
from typing import Any
from .base import DomainAnalyzer
from .helpers import plabel, slabel, house_ruler_name, planet_sign, planet_dignity_code


class RomanceAnalyzer(DomainAnalyzer):
    domain_key = "romance"
    tradition_weight = 0.4

    def _analyze_traditional(self, chart: Any) -> dict[str, Any]:
        r5 = house_ruler_name(chart, 5)
        r5l = plabel(r5)
        r5_dig = planet_dignity_code(chart, r5)
        venus_sign = planet_sign(chart, "VENUS")
        venus_l = slabel(venus_sign)
        moon_sign = planet_sign(chart, "MOON")
        moon_l = slabel(moon_sign)

        structure = (
            f"你的恋爱模式是由5宫主星{r5l}和金星在{venus_l}共同决定的——"
        )
        if r5_dig in ("domicile", "exaltation"):
            structure += (
                f"你在这个领域是有天赋的。你在恋爱中比较容易放松、享受——"
                f"你知道怎么制造好的氛围，也知道怎么让自己和对方都开心。"
            )
        elif r5_dig in ("detriment", "fall"):
            structure += (
                f"说实话——恋爱不是你的主场。不是说你不会爱，而是说你的恋爱模式"
                f"需要学习。你可能经历过几次不太顺利的感情，回头看会发现——"
                f"每次都是同一个问题，换了一个人而已。这不是运气不好，是模式在重复。"
            )
        else:
            structure += "你的恋爱模式比较灵活，没有很强的先天倾向——好或不好主要看你遇到谁。"

        structure += (
            f"\n\n金星在{venus_l}——你在感情里最容易被人注意到的特质是{_venus_trait(venus_l)}"
            f"但这也意味着{_venus_blind_spot(venus_l)}"
        )

        structure += (
            f"\n\n有一个需要提醒自己的地方：你的金星让你容易被{_venus_attract(venus_l)}吸引，"
            f"但你的月亮在{moon_l}——你真正需要的是{_moon_need(moon_l)}。"
            f"这两个有时候是矛盾的人。你一开始被吸引的和让你长期安心的，"
            f"不一定是同一种类型的。你可能要经历过几次'心动但不对'之后，"
            f"才能分辨出'心动而且对'长什么样。"
        )

        suggestion = (
            "在感情里——先看清你的模式，再选人。"
            "你容易被某种类型吸引这件事本身，就值得你花时间去理解。"
        )
        return {"structure": structure, "suggestion": suggestion, "theme_conditions": {}}

    def _analyze_modern(self, chart: Any) -> dict[str, Any]:
        psychology = "感情里最能让你成长的，不是'找到对的人'——是看清你为什么总是被不对的人吸引。这个答案不在对方身上，在你自己的星盘里。"
        return {"psychology": psychology, "suggestion": ""}

    def _analyze_question(self, chart: Any, question_key: str) -> dict[str, Any] | None:
        """针对 7 个感情抓手问题的差异化分析"""
        handlers = {
            "love_pattern": self._q_love_pattern,
            "when_meet": self._q_when_meet,
            "does_he_like_me": self._q_does_he_like_me,
            "compatibility": self._q_compatibility,
            "letting_go": self._q_letting_go,
            "peach_blossom": self._q_peach_blossom,
            "true_love": self._q_true_love,
        }
        handler = handlers.get(question_key)
        if not handler:
            return None
        return handler(chart)

    # ── 各问题差异化分析 ──

    def _q_love_pattern(self, chart: Any) -> dict[str, Any]:
        """感情模式重复 — 聚焦 5H/7H 主 + Venus + 全盘结构"""
        r5 = house_ruler_name(chart, 5)
        r7 = house_ruler_name(chart, 7)
        venus_sign = planet_sign(chart, "VENUS")
        moon_sign = planet_sign(chart, "MOON")

        structure = (
            f"你的感情模式是由三个部分共同编织的：\n\n"
            f"1）{plabel(r5)}（5宫主）掌管你的恋爱方式——你怎么开始一段感情、你在恋爱中扮演什么角色。"
        )
        r5_dig = planet_dignity_code(chart, r5)
        if r5_dig in ("domicile", "exaltation"):
            structure += f" {plabel(r5)}的状态很好，意味着你的恋爱本能是顺畅的——你知道怎么让自己和对方开心。"
        elif r5_dig in ("detriment", "fall"):
            structure += f" {plabel(r5)}在这里不太舒服——你的恋爱方式需要后天学习，可能走了几次弯路。"
        else:
            structure += f" {plabel(r5)}比较中性——你的恋爱方式受具体处境的影响比较大。"

        structure += (
            f"\n\n2）{plabel(r7)}（7宫主）掌管你的伴侣关系——你需要什么样的长期伴侣、你在关系里的角色期待。"
            f"如果5宫是'怎么开始'，7宫就是'怎么走下去'。当5宫和7宫的能量不协调时，"
            f"就会出现'在一起了才发现不对'的反复模式。"
        )

        structure += (
            f"\n\n3）金星在{slabel(venus_sign)}决定了你被什么吸引——"
            f"{_venus_attract(venus_sign)}。"
            f"而月亮在{slabel(moon_sign)}决定了你需要什么——{_moon_need(moon_sign)}。"
            f"\n\n如果你吸引来的人总是满足金星的需求但满足不了月亮，你的感情就会不断重复"
            f"'心动→不安→分开→再心动'的循环。打破循环的关键是：在最初被吸引的时候，"
            f"就问自己——这个人给我的感觉，是我的金星在点头，还是我的月亮也在点头？"
        )

        suggestion = "下一次对一个人心动的时候，先别问'我是不是喜欢TA'，先问'我的月亮觉得安全吗'。"
        return {"traditional": {"structure": structure, "suggestion": suggestion}, "modern": {}}

    def _q_when_meet(self, chart: Any) -> dict[str, Any]:
        """何时遇到对的人 — 聚焦法达周期 + 行运 Jupiter"""
        r7 = house_ruler_name(chart, 7)
        venus_sign = planet_sign(chart, "VENUS")
        jupiter_sign = planet_sign(chart, "JUPITER")

        structure = (
            f"关于'什么时候遇到对的人'——在古典占星里，这个问题要看三个时钟：\n\n"
            f"第一时钟：7宫主星{plabel(r7)}的法达周期。当你的法达大运或子运走到{plabel(r7)}时，"
            f"关系议题会被推到台前——你会更关注感情，也更容易遇到关键的人。\n\n"
            f"第二时钟：行运木星。木星在{slabel(jupiter_sign)}——当行运木星经过你的7宫、"
            f"5宫，或与你的金星/7宫主产生和谐相位时，是桃花和正缘的高概率窗口。\n\n"
            f"第三时钟：你自己。金星在{slabel(venus_sign)}意味着你需要在{slabel(venus_sign)}的状态里"
            f"才能真正释放吸引力——不是刻意社交，而是做自己。\n\n"
            f"时机不只是天时，也是你的状态。当你和你的金星处于同一频道时，"
            f"宇宙的时钟才真正开始为你倒计时。"
        )

        suggestion = "与其等待对的人出现，不如先让自己处于'对的状态'。关注你的法达周期和行运，同时关注你的内心时钟。"
        return {"traditional": {"structure": structure, "suggestion": suggestion}, "modern": {}}

    def _q_does_he_like_me(self, chart: Any) -> dict[str, Any]:
        """TA 喜欢我吗 — 聚焦下降点 + Venus + 比较盘思维"""
        venus_sign = planet_sign(chart, "VENUS")
        mars_sign = planet_sign(chart, "MARS")

        structure = (
            f"关于'TA喜不喜欢我'——没有TA的星盘，我不能直接回答。但我可以告诉你一件事：\n\n"
            f"这个问题本身，可能比你想要的答案更重要。\n\n"
            f"你的金星在{slabel(venus_sign)}——它决定了你如何发出'喜欢'的信号。"
            f"而你的火星在{slabel(mars_sign)}——它决定了你如何主动出击（或不主动）。"
            f"\n\n如果你的金星在{slabel(venus_sign)}意味着你表达好感的方式比较"
            f"{'直接明确' if venus_sign in ('ARIES','LEO','SAGITTARIUS') else '含蓄内敛' if venus_sign in ('TAURUS','VIRGO','CAPRICORN') else '灵活多变' if venus_sign in ('GEMINI','LIBRA','AQUARIUS') else '细腻深沉'}，"
            f"而TA的表达方式和你不一样——那么你感觉到的'不确定'，也许是信号的错位，不是心意的问题。\n\n"
            f"如果你真的想知道答案——最快的办法不是猜，是问。你的星盘里最需要被释放的勇气，"
            f"可能就在你的火星{slabel(mars_sign)}里。"
        )

        suggestion = "在不确定TA喜不喜欢你的时候，先确定你喜欢TA什么。不是为了TA——是为了看清自己的信号。"
        return {"traditional": {"structure": structure, "suggestion": suggestion},
                "modern": {"psychology": "你对'不被喜欢'的恐惧，可能比TA对你的态度更值得你关注。"}}

    def _q_compatibility(self, chart: Any) -> dict[str, Any]:
        """契合度 — 聚焦日/月互动 + 下降点"""
        r7 = house_ruler_name(chart, 7)
        venus_sign = planet_sign(chart, "VENUS")
        moon_sign = planet_sign(chart, "MOON")
        sun_sign = planet_sign(chart, "SUN")

        structure = (
            f"契合度（在没有对方星盘的情况下）可以反过来看：\n\n"
            f"你的7宫是{plabel(r7)}在掌管——这意味着你真正需要的伴侣类型是{plabel(r7)}式的人。"
            f"注意：这不等于你被吸引的类型。你的金星在{slabel(venus_sign)}决定吸引，"
            f"你的7宫决定匹配。\n\n"
            f"真正契合的关系需要两个层面的匹配：\n"
            f"• 月亮层面的情绪安全感——你的月亮在{slabel(moon_sign)}，需要一个{_moon_need(moon_sign)}\n"
            f"• 太阳层面的身份认同——你的太阳在{slabel(sun_sign)}，需要一个不会让你觉得自己'太过了'的人\n\n"
            f"如果一段关系让你长期感觉安全（月亮）又能做自己（太阳），契合度就是高的。"
            f"反之，如果只有火花没有安心——那不是契合，是吸引。"
        )

        suggestion = "下次评估一段关系的时候，用两个问题替代'TA对我好不好'：1）我在这里能做自己吗？2）我的月亮在这里是放松的还是绷着的？"
        return {"traditional": {"structure": structure, "suggestion": suggestion}, "modern": {}}

    def _q_letting_go(self, chart: Any) -> dict[str, Any]:
        """如何放下 — 聚焦 8H/12H + 冥王星 + 土星"""
        venus_sign = planet_sign(chart, "VENUS")
        moon_sign = planet_sign(chart, "MOON")
        saturn_sign = planet_sign(chart, "SATURN")

        structure = (
            f"放下一个人最难的部分，不是'不联系'——是你的星盘里有一些东西在帮你抓住不放。\n\n"
            f"你的金星在{slabel(venus_sign)}——你爱一个人的方式就是{slabel(venus_sign)}的方式，"
            f"分手后最难放下的不是那个人本身，是你在那段感情里活出来的那个自己。"
            f"\n\n你的月亮在{slabel(moon_sign)}——你的情绪安全感建立在什么上面，"
            f"失去之后什么就会最痛。如果那段关系曾经是你的'安全区'，那么失去它就像失去了锚。"
            f"\n\n你的土星在{slabel(saturn_sign)}——土星掌管时间。它能给你的礼物是："
            f"够久之后，回头看，你会感谢那段经历教会你的东西。但这个礼物需要时间。"
            f"\n\n所以'放下'不是一个动作，是一个过程。你的星盘没有'遗忘'的快捷键——"
            f"但它有'转化'的路径。把痛苦放进你的创造性活动里（5宫），或者放进你愿意帮别人疗愈的能力里，"
            f"它会变成你的一部分。不是债务，是你携带过的东西——但不再沉重。"
        )

        suggestion = "写一封信给你自己——不是给TA——告诉那个在痛苦中的你：'我看见你了，我陪你熬过去'。这是你月亮最需要的疗愈。"
        return {"traditional": {"structure": structure, "suggestion": suggestion},
                "modern": {"psychology": "放下不是删除记忆，是把那段经历从'我的故事'变成'我经历过的一个篇章'。你的人生还有很长的篇幅。"}}

    def _q_peach_blossom(self, chart: Any) -> dict[str, Any]:
        """桃花运 — 聚焦 5H + Venus + Jupiter + 11H"""
        r5 = house_ruler_name(chart, 5)
        venus_sign = planet_sign(chart, "VENUS")
        jupiter_sign = planet_sign(chart, "JUPITER")

        r5_dig = planet_dignity_code(chart, r5)
        structure = (
            f"你的桃花运取决于三个因素：\n\n"
            f"1）5宫主{plabel(r5)}——你的桃花是{plabel(r5)}式的。"
        )
        if r5_dig in ("domicile", "exaltation"):
            structure += f" {plabel(r5)}状态很强——你的桃花运本质上是通畅的，你散发魅力不需要太费力。"
        elif r5_dig in ("detriment", "fall"):
            structure += f" {plabel(r5)}在这里不太自在——你的桃花不是没有，是出现的方式比较拐弯，或者你自己不容易识别。"
        else:
            structure += f"状态平稳——桃花运受你自己心境的影响很大。"

        structure += (
            f"\n\n2）金星在{slabel(venus_sign)}——你展示魅力的方式。"
            f"当你在{slabel(venus_sign)}的频道里时——做{slabel(venus_sign)}喜欢的事、"
            f"待在{slabel(venus_sign)}风格的环境里——你的吸引力会自动打开。"
            f"\n\n3）木星在{slabel(jupiter_sign)}——你的运气放大器。"
            f"当行运木星经过你的5宫或7宫时，是桃花最旺的窗口。"
            f"\n\n另外——11宫也不容忽略。你的桃花不只是从私密关系里来，"
            f"也可能从社群、朋友圈、共同兴趣里长出来。你认识的人越多，桃花出现的概率越高——"
            f"这是简单的数学，也是木星的运作方式。"
        )

        suggestion = "与其等桃花，不如去{slabel(venus_sign)}喜欢的地方做你喜欢的事。桃花往往是在你不刻意找的时候，自己撞上来的。"
        return {"traditional": {"structure": structure, "suggestion": suggestion}, "modern": {}}

    def _q_true_love(self, chart: Any) -> dict[str, Any]:
        """正缘画像 — 聚焦 7H 主 + 下降点 + 金星/木星相位"""
        r7 = house_ruler_name(chart, 7)
        venus_sign = planet_sign(chart, "VENUS")
        moon_sign = planet_sign(chart, "MOON")

        structure = (
            f"正缘不是一个具体的人——是一类人。你的星盘里藏着这类人的画像：\n\n"
            f"• 你的7宫主是{plabel(r7)}——你的正缘会带有{plabel(r7)}的气质。"
            f" {plabel(r7)}型的人可能是：有主见、行动力强、不太拐弯抹角。\n\n"
            f"• 你的金星在{slabel(venus_sign)}——你被什么样的人吸引，从星盘来看：{_venus_attract(venus_sign)}。"
            f"但注意——有吸引力的不一定是正缘。正缘是你既被吸引、又能长久相处的人。\n\n"
            f"• 你的月亮在{slabel(moon_sign)}——正缘必须能让你的月亮安全。{_moon_need(moon_sign)}。"
            f"\n\n所以你的正缘大概是这样的人：有{plabel(r7)}的存在方式，让你感觉{slabel(venus_sign)}式的心动，"
            f"同时给你的月亮{slabel(moon_sign)}式的安全感。\n\n"
            f"这三者同时满足并不容易——所以正缘不是'等'来的，是你逐渐了解自己之后'识别'出来的。"
        )

        suggestion = "列一个清单：左边写'我被什么样的人吸引'（金星），中间写'我需要什么样的关系'（7宫），右边写'什么样的相处让我安心'（月亮）。三者的交集，就是你的正缘画像。"
        return {"traditional": {"structure": structure, "suggestion": suggestion}, "modern": {}}


def _venus_trait(s: str) -> str:
    return {"白羊座":"主动、直接、不扭捏——你喜欢就看得出来。",
            "金牛座":"质感——不只是外表的，也包括相处时的那种安稳和舒服。",
            "双子座":"有趣、会聊天——聊不来的人再好看也没用。",
            "巨蟹座":"温柔、有家人感——你让另一半觉得'回家真好'。",
            "狮子座":"热情、大方、让人觉得自己被重视。",
            "处女座":"靠谱、细心——你会用行动让对方觉得'这个人真的很在乎我'。",
            "天秤座":"得体、照顾氛围——跟你在一起是舒服的。",
            "天蝎座":"深度——你不是随便玩玩的人，你要的是全部。",
            "射手座":"自由、不粘人——让对方觉得有空间。",
            "摩羯座":"认真、长期主义——你不是玩玩的人，你从一开始就在评估'能不能走远的'。",
            "水瓶座":"独立、有自己的想法——你不是会围着对方转的人。",
            "双鱼座":"浪漫、包容、有想象力——让对方觉得被无条件接纳。"}.get(s, "独特的气质。")


def _venus_blind_spot(s: str) -> str:
    return {"白羊座":"你容易太快投入——上头快，下头也可能很快。",
            "金牛座":"你太稳了，对方可能觉得你不够浪漫——但其实你只是表达方式不花哨。",
            "双子座":"你容易被新鲜感吸引——但当新鲜感消退，你可能也不确定自己还爱不爱。",
            "巨蟹座":"你容易过度付出，然后用'我对你这么好'来期待回报——这种期待会让自己失望。",
            "狮子座":"你太要面子了——明明在意，却装不在意，最后自己难受。",
            "处女座":"你容易对对方太好——帮ta做太多，久了对方习惯了，你开始觉得'我变成工具人了'。",
            "天秤座":"你容易为了关系和谐委屈自己——短期没事，长期下来你会找不到自己。",
            "天蝎座":"你容易在信任和不信任之间反复——一旦被辜负，很难再给出第二次信任。",
            "射手座":"新鲜感消退后你容易想逃——不是不爱，是觉得被困住了。",
            "摩羯座":"你容易把感情当成项目管理——认真是好事，但忘了感情也需要'没用的浪漫'。",
            "水瓶座":"你不觉得自己冷——但对方可能觉得跟你有距离。",
            "双鱼座":"你边界感弱——太能理解对方了，以至于忘了问自己'我想要什么'。"}.get(s,"")


def _venus_attract(s: str) -> str:
    return {"白羊座":"有冲劲、有棱角的人","金牛座":"稳重大方、让人觉得踏实的人",
            "双子座":"聪明有趣、会聊天的人","巨蟹座":"温柔体贴、有家人感的人",
            "狮子座":"有自信、有光芒的人","处女座":"靠谱细心、能做对事的人",
            "天秤座":"得体优雅、让人舒服的人","天蝎座":"有深度、有秘密的人",
            "射手座":"自由洒脱、有故事的人","摩羯座":"认真有实力、让人佩服的人",
            "水瓶座":"有独立思考、不跟风的人","双鱼座":"有灵性、让人产生幻想的人"}.get(s,"某种类型的人")


def _moon_need(s: str) -> str:
    return {"白羊座":"一个能跟你并肩作战的搭档——不是依附你，是跟你一起冲",
            "金牛座":"一个不会突然离开的人——不是天天浪漫，是一直在",
            "双子座":"一个能跟你聊到天亮的人——精神连接比什么都重要",
            "巨蟹座":"一个让你觉得'有家'的人——不是房子，是心安",
            "狮子座":"一个真心欣赏你的人——不是客套，是真的看见你的光芒",
            "处女座":"一个让你可以放松的人——你对自己已经够严格了",
            "天秤座":"一个帮你做决定的人——不是替你做，是陪你一起想",
            "天蝎座":"一个让你不设防的人——能放下控制、放下试探",
            "射手座":"一个给你空间的人——不是不关心你，是不绑着你",
            "摩羯座":"一个说到做到的人——让你觉得可以一起规划未来",
            "水瓶座":"一个尊重你独立性的人——不需要你解释为什么你想一个人待着",
            "双鱼座":"一个帮你建立边界的人——既懂你的柔软，也保护你不被打散"}.get(s,"一个真正懂你的人")
