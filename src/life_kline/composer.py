"""
组合引擎 — 编排 + Hero叙事 + 证据快照。
接入叙事引擎：每颗行星 = 落座Base + 落宫Base + 尊严修饰 + 宫位类型修饰。
"""
from __future__ import annotations
from typing import Any

from .domains.personal import PersonalAnalyzer
from .domains.finance import FinanceAnalyzer
from .domains.family import FamilyAnalyzer
from .domains.romance import RomanceAnalyzer
from .domains.marriage import MarriageAnalyzer
from .domains.partnership import PartnershipAnalyzer
from .domains.children import ChildrenAnalyzer
from .domains.work_skill import WorkSkillAnalyzer
from .domains.career import CareerAnalyzer
from .domains.education import EducationAnalyzer
from .domains.appearance import AppearanceAnalyzer
from .domains.health import HealthAnalyzer
from .characters.character_engine import CharacterEngine

DOMAIN_ANALYZER_CLASSES: dict[str, type] = {
    "personal": PersonalAnalyzer, "finance": FinanceAnalyzer,
    "family": FamilyAnalyzer, "romance": RomanceAnalyzer,
    "marriage": MarriageAnalyzer, "partnership": PartnershipAnalyzer,
    "children": ChildrenAnalyzer, "work_skill": WorkSkillAnalyzer,
    "career": CareerAnalyzer, "education": EducationAnalyzer,
    "appearance": AppearanceAnalyzer, "health": HealthAnalyzer,
}


class ReportComposer:
    def __init__(self) -> None:
        self._analyzers = {k: cls() for k, cls in DOMAIN_ANALYZER_CLASSES.items()}

    def compose_domains(self, chart: Any, hero_context: str = "") -> dict[str, dict[str, Any]]:
        results = {}
        for k, a in self._analyzers.items():
            report = a.analyze(chart)
            d = report.to_dict()
            if hero_context:
                d["hero_bridge"] = _build_hero_bridge(k, hero_context)
            results[k] = d
        return results

    def compose_hero(self, chart: Any, phase_info: dict[str, Any] | None = None, transits: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        """三段深度观察——咨询式对话，千人千面。"""
        return _build_hero_observations(chart, phase_info=phase_info, transits=transits)

    def compose_evidence(self, chart: Any) -> dict[str, Any]:
        from .interpretation.planet_rules import compute_planet_baseline, compute_essential_dignity
        pb, db = {}, {}
        for pn, info in getattr(chart, "planets", {}).items():
            if not hasattr(pn, "value"): continue
            db[str(pn.value)] = compute_essential_dignity(pn, info.sign, float(getattr(info,"degree",0))).to_dict()
            pb[str(pn.value)] = compute_planet_baseline(pn, info.sign, float(getattr(info,"degree",0)), int(getattr(info,"house",0))).to_dict()
        return {"planet_baselines": pb, "dignity_breakdown": db, "house_infos": {str(i): {"title": _ht(i)} for i in range(1,13)}}

    def compose_character_profiles(self, chart: Any) -> dict[str, Any]:
        """生成12星座个性化角色画像（v1.5 旧系统，保留兼容）。

        返回:
            characters: 12个角色画像 (dict[sign.value, CharacterProfile.to_dict()])
            sorted_by_presence: 按存在感降序的角色列表
            core_characters: 存在感 >= 50 的核心角色
            dormant_characters: 存在感 < 20 的沉睡角色
        """
        engine = CharacterEngine(chart)
        all_profiles = engine.get_all_profiles()
        sorted_profiles = engine.get_sorted_profiles()

        return {
            "characters": {s.value: p.to_dict() for s, p in all_profiles.items()},
            "sorted_by_presence": [
                {"sign": p.sign.value, "name": p.persona.name,
                 "archetype": p.persona.archetype, "presence_score": p.presence_score,
                 "role_tag": p.role_tag}
                for p in sorted_profiles
            ],
            "core_characters": [
                {"sign": p.sign.value, "name": p.persona.name,
                 "presence_score": p.presence_score, "role_tag": p.role_tag}
                for p in sorted_profiles if p.presence_score >= 50
            ],
            "dormant_characters": [
                {"sign": p.sign.value, "name": p.persona.name}
                for p in sorted_profiles if p.presence_score < 20
            ],
        }

    def compose_planet_profiles(self, chart: Any) -> dict[str, Any]:
        """生成10行星个性化角色画像（v2.0 新系统，对标万象有灵十神模型）。

        返回:
            planet_characters: 10个行星角色 (dict[planet.value, PlanetCharacterProfile.to_dict()])
            main_character: 太阳（主人格）画像
            sorted_by_strength: 按强度降序
            core_planets: 强度 >= 50 的核心行星
        """
        from .characters.planet_character_engine import PlanetCharacterEngine

        engine = PlanetCharacterEngine(chart)
        all_profiles = engine.get_all_profiles()
        sorted_profiles = engine.get_profiles_by_strength()

        return {
            "planet_characters": {p.value: prof.to_dict() for p, prof in all_profiles.items()},
            "main_character": engine.get_main_character().to_dict(),
            "sorted_by_strength": [
                {"planet": p.planet.value, "name_zh": p.persona.name_zh,
                 "archetype_zh": p.persona.archetype_zh, "core_strength": p.core_strength,
                 "role_tag": p.role_tag, "symbol": p.persona.symbol}
                for p in sorted_profiles
            ],
            "core_planets": [
                {"planet": p.planet.value, "name_zh": p.persona.name_zh,
                 "core_strength": p.core_strength, "role_tag": p.role_tag}
                for p in sorted_profiles if p.core_strength >= 50
            ],
        }


def _ht(h: int) -> str:
    try:
        from .interpretation.house_rules import get_house_profile
        return get_house_profile(h).title
    except: return f"第{h}宫"


def enrich_report(chart: Any, phase_info: dict[str, Any] | None = None, transits: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    c = ReportComposer()
    hero = c.compose_hero(chart, phase_info=phase_info, transits=transits)
    domains = c.compose_domains(chart, hero_context=hero.get("narrative", ""))
    evidence = c.compose_evidence(chart)
    characters = c.compose_character_profiles(chart)
    planet_characters = c.compose_planet_profiles(chart)
    return {
        "hero": hero,
        "domains": domains,
        "_analysis_evidence": evidence,
        "characters": characters,
        "planet_characters": planet_characters,
    }


_DOMAIN_HERO_LINKS: dict[str, str] = {
    "personal": "刚才说的你的性格底色——",
    "career": "你刚才看到了你是一个什么样的人。在事业上——",
    "finance": "你的性格决定了你怎么做选择。在钱这件事上——",
    "romance": "你了解了自己的模式。在感情里——",
    "marriage": "你看到了你是什么样的人。在长期关系里——",
    "family": "你的原生家庭模式，和你刚才看到的性格底色——",
    "partnership": "你在合伙关系中的模式，和你前面看到的——",
    "children": "你刚才看到的你的性格和感情模式，在亲子关系里——",
    "work_skill": "你的做事方式，和刚才说的——",
    "education": "你的学习方式，和你前面看到的——",
    "appearance": "你的性格底色会体现在你的外形和气质上——",
    "health": "你的性格和情绪模式，会在身体上留下痕迹——",
}


def _build_hero_bridge(domain_key: str, _hero_text: str) -> str:
    return _DOMAIN_HERO_LINKS.get(domain_key, "前面聊到的——")


# ═══════════════════════════════════════════════════════════════
# Hero 三段观察构建器 —— 咨询式对话，千人千面
# ═══════════════════════════════════════════════════════════════

def _build_phase_anchor(phase_info: dict[str, Any], chart_ruler_label: str) -> str:
    """法达时间锚点——告诉用户当前在哪个大运、还剩多久。"""
    major = phase_info.get("major_label", "")
    sub = phase_info.get("sub_label", "")
    remaining = phase_info.get("remaining_years")
    trend = phase_info.get("trend_type", "")
    is_ruler = phase_info.get("is_chart_ruler_phase", False)

    if not major:
        return ""

    # 核心句：当前阶段
    if sub and sub != major:
        core = f"你现在正处于{ major }主运、{ sub }子运的阶段"
    else:
        core = f"你现在正处于{ major }主运的阶段"

    # 命主星关联——如果大运星是命主星，这句话极其重要
    if is_ruler:
        core += f"。{ major }是你的命主星——这个阶段不是在'经历'什么，是在'成为'什么"

    # 剩余时间
    if remaining is not None and remaining > 0:
        if remaining < 1:
            time_note = f"。离下一个阶段切换不到一年——是时候做收尾和准备了"
        elif remaining < 3:
            time_note = f"。距离下一个大阶段还有大约{remaining:.1f}年——好好用"
        else:
            time_note = f"。这个阶段还有{remaining:.1f}年——时间够你做一次认真的调整"
        core += time_note

    # 趋势提示
    if trend == "bull":
        core += "。整体是扩张窗口——适合把已经成熟的能力推向更大的舞台"
    elif trend == "bear":
        core += "。整体偏收缩——更适合整顿结构、清理负担，而不是冒进"
    else:
        core += "。节奏偏平稳——重点在于打磨方法、搭好结构、耐心推进"

    return core


def _build_transit_highlight(transits: list[dict]) -> str:
    """行运高亮——从活跃行运中挑1条最强的，翻译成'此刻'人话。"""
    if not transits:
        return ""

    # 优先挑慢行星（木星/土星）+ 合相/对冲 + 高强度的
    best = transits[0]  # already sorted

    tl = best.get("transiting_label", "")
    nl = best.get("natal_label", "")
    al = best.get("aspect_label", "")
    is_applying = best.get("is_applying", False)

    # 根据行星+相位生成不同的自然语言
    transit_voice: dict[tuple[str, str], str] = {
        ("木星", "合相"): f"而且现在——行运木星正合你的本命{nl}。这是一个扩张和信心的窗口。接下来的几周，和{nl}相关的事情会更容易、更顺、更被看到。不是运气——是时机对了。",
        ("木星", "三合"): f"而且现在——行运木星正和你的本命{nl}形成三合。这是一个顺流期。和{nl}相关的事情不用太用力——顺势推一把就有反馈。",
        ("木星", "对冲"): f"而且现在——行运木星正对你的本命{nl}。你可能会觉得和{nl}相关的事被放大了——好的更好，坏的也更明显。这段时间适合重新校准：你要的到底是什么。",
        ("土星", "合相"): f"而且现在——行运土星正压在你的本命{nl}上。这不是轻松的时期。你会觉得和{nl}有关的事情变重了、变慢了、变难了。但说实话——土星压过的地方，就是你接下来几年最扎实的地基。现在的'难'，是在逼你认真。",
        ("土星", "对冲"): f"而且现在——行运土星正对你的本命{nl}。你可能会在和{nl}相关的领域感到一种拉扯——外部有压力，内部有疑问。这不是要你马上解决，是要你重新定义什么才是重要的。",
        ("土星", "刑相"): f"而且现在——行运土星正和你的本命{nl}形成刑相位。{nl}相关的领域最近会有一些摩擦和障碍。不是你做得不好——是这个阶段在逼你换一种方式做。",
        ("天王星", "合相"): f"而且现在——行运天王星正合你的本命{nl}。准备好迎接变化——和{nl}相关的事可能会以你没想到的方式出现转折。不一定是坏事——但一定不是按你计划来的。",
        ("天王星", "对冲"): f"而且现在——行运天王星正对你的本命{nl}。和{nl}相关的领域正在经历一场'突然的清醒'。某个人或某件事会逼你跳出惯性——一开始不舒服，但回头看你会感谢。",
        ("冥王星", "合相"): f"而且现在——行运冥王星正缓慢压过你的本命{nl}。这不是一个'这几天'的变化——是几年的深层转化。和{nl}相关的领域在经历一次彻底的翻新。旧的会被拿走，新的需要你主动去选。",
        ("海王星", "合相"): f"而且现在——行运海王星正合你的本命{nl}。和{nl}相关的领域最近可能有点模糊——看不清、想不明、不知道自己在干嘛。这不一定是坏事——有时候'迷失'是找到新方向的必经之路。但注意别自己骗自己。",
        ("火星", "合相"): f"而且现在——行运火星正点燃你的本命{nl}。和{nl}相关的事这几天会加速——你可能会比较冲、比较急、想马上做点什么。行动力是好事——但先想好打哪里。",
        ("火星", "对冲"): f"而且现在——行运火星正对你的本命{nl}。这几天和{nl}有关的事容易起冲突——别人说的话、做的事可能会踩到你。不是对方故意——是你的火星被激活了，耐心变短了。",
        ("金星", "合相"): f"而且现在——行运金星正合你的本命{nl}。和{nl}有关的事这几天会变舒服——人际关系、审美、金钱决策都会顺一些。适合谈合作、做重要的消费决策。",
    }

    key = (tl, al)
    if key in transit_voice:
        return transit_voice[key]

    # fallback: 组合生成
    aspect_voice: dict[str, str] = {
        "合相": f"正在激活你的{nl}",
        "对冲": f"正在拉扯你的{nl}",
        "刑相": f"正在给你的{nl}施压",
        "三合": f"正在顺流推动你的{nl}",
        "六合": f"正在给你的{nl}开一扇小窗",
    }
    voice = aspect_voice.get(al, f"正在影响你的{nl}")
    direction = "接下来一段时间" if is_applying else "这段时间"

    return f"而且现在——行运{tl}{al}——{voice}。{direction}，留意和{nl}有关的事。"


def _build_suspense_hook(obs: list[dict]) -> str:
    """悬念钩子——制造翻页动机。"""
    hooks = [
        "刚才说了你的性格底色和时间节奏。往下翻——你的事业、感情和钱，星盘里有更具体的答案。",
        "上面这些只是'你是什么样的人'。但你可能更想知道：你适合做什么、你的感情模式、你的钱从哪来。往下翻。",
        "性格这件事你大概心里有数了。但星盘能告诉你的远不止这些——你和钱的关系、你和爱的关系、你和你自己的关系，都在下面。",
        "刚才这三点，是你星盘最外面的那层。往下的内容更具体——关于你的事业方向、财务格局、感情模式——每一块都值得你花几分钟看看。",
    ]
    seed = sum(ord(c) for c in (obs[0].get("sign", "") + obs[0].get("planet", ""))) if obs else 0
    return hooks[seed % len(hooks)]


def _build_hero_observations(chart: Any, phase_info: dict[str, Any] | None = None, transits: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    from .domains.helpers import (
        asc_sign, plabel, slabel, planet_sign, planet_house,
        planet_dignity_code, chart_ruler_name,
    )
    from .interpretation.narrative_engine import (
        build_sun_narrative, build_moon_narrative, build_venus_narrative,
        build_mars_narrative, build_mercury_narrative, build_asc_narrative,
        build_sun_house, build_moon_house, build_venus_house, build_mars_house,
    )
    from .constants import ANGULAR_HOUSES, SUCCEDENT_HOUSES

    def _ht(h: int) -> str: return "angular" if h in ANGULAR_HOUSES else "succedent" if h in SUCCEDENT_HOUSES else "cadent"

    asc_l = slabel(asc_sign(chart))
    sun_s = slabel(planet_sign(chart, "SUN")); sun_h = planet_house(chart, "SUN")
    moon_s = slabel(planet_sign(chart, "MOON")); moon_h = planet_house(chart, "MOON")
    venus_s = slabel(planet_sign(chart, "VENUS")); venus_h = planet_house(chart, "VENUS")
    mars_s = slabel(planet_sign(chart, "MARS")); mars_h = planet_house(chart, "MARS")
    merc_s = slabel(planet_sign(chart, "MERCURY"))
    cr_l = plabel(chart_ruler_name(chart))

    # 收集 3 段观察
    obs = []

    # 获取相位和接纳信息（简化：从planet_baselines推断）
    sun_dig = planet_dignity_code(chart, "SUN")
    moon_dig = planet_dignity_code(chart, "MOON")
    venus_dig = planet_dignity_code(chart, "VENUS")

    # 飞星工具
    from .flystar_catalog import get_house_ruler_flight_entry

    def _flystar_note(planet_name: str, house: int) -> str:
        ruler_name = _house_ruler(chart, house)
        if not ruler_name:
            return ""
        ruler_house = planet_house(chart, ruler_name)
        if ruler_house <= 0 or ruler_house == house:
            return ""
        meaning = _flystar_meaning(ruler_name, house, ruler_house)
        if not meaning:
            return ""
        return f"而且有意思的是——{meaning}"

    # —— 观察1：太阳 ——
    sun_core = _pick_sun_core(sun_s)
    sun_house_note = _pick_house_note("SUN", sun_h)
    sun_flystar = _flystar_note("SUN", sun_h)
    obs.append({
        "planet": "太阳", "core": sun_core, "dignity": sun_dig,
        "sign": sun_s, "house": sun_h, "house_note": sun_house_note,
        "house_type": _ht(sun_h), "flystar": sun_flystar,
    })

    # —— 观察2：月亮 ——
    moon_core = _pick_moon_core(moon_s)
    moon_house_note = _pick_house_note("MOON", moon_h)
    moon_flystar = _flystar_note("MOON", moon_h)
    obs.append({
        "planet": "月亮", "core": moon_core, "dignity": moon_dig,
        "sign": moon_s, "house": moon_h, "house_note": moon_house_note,
        "house_type": _ht(moon_h), "flystar": moon_flystar,
    })

    # —— 观察3：金星 ——
    venus_core = _pick_venus_core(venus_s)
    venus_house_note = _pick_house_note("VENUS", venus_h)
    venus_flystar = _flystar_note("VENUS", venus_h)
    obs.append({
        "planet": "金星", "core": venus_core, "dignity": venus_dig,
        "sign": venus_s, "house": venus_h, "house_note": venus_house_note,
        "house_type": _ht(venus_h), "venus_12h": venus_h == 12, "flystar": venus_flystar,
    })

    # 为每人选择不同开门句式
    import random
    random.seed(sum(ord(c) for c in sun_s + moon_s + venus_s))
    openers = random.sample(_OPENERS, 3)

    # 组装
    parts = []
    for i, o in enumerate(obs):
        opener = openers[i]
        para = _build_observation(opener, o)
        parts.append(para)

    narrative = "\n\n".join(parts)

    # ── 行运高亮：此刻正在发生的 ──
    if transits:
        transit_text = _build_transit_highlight(transits)
        if transit_text:
            narrative = narrative + "\n\n" + transit_text

    # ── 时间锚点：当前法达阶段 ──
    if phase_info:
        anchor = _build_phase_anchor(phase_info, cr_l)
        if anchor:
            narrative = narrative + "\n\n" + anchor

    # ── 悬念钩子：驱动用户往下翻 ──
    narrative = narrative + "\n\n" + _build_suspense_hook(obs)

    return {"narrative": narrative, "asc_label": asc_l, "chart_ruler_label": cr_l}


_OPENERS = [
    "你有没有发现——",
    "我看你的星盘，第一眼就看到——",
    "你身上有一个挺有意思的特点——",
    "说起来你可能不信，你的盘里有一条很清晰的线——",
    "如果我猜得没错的话，你——",
    "很多人不知道的是，你这个配置的人——",
    "你的星盘有一个你自己可能都没意识到的东西——",
    "让我直接说吧——",
    "聊你的盘之前，我先说一个直觉——",
    "外面的人看到的你，和真实的你，有一个挺大的差别——",
    "你星盘里最让我在意的是——",
    "有一个东西，你的星盘反复在说——",
]


def _pick_sun_core(sign: str) -> str:
    return {
        "白羊座":"是一个想赢的人——你心里有自己的标准，达不到你会烦躁，达到了你马上找下一个目标",
        "金牛座":"做事有自己的节奏。你不在乎的东西很多，但在乎的一样都不会放",
        "双子座":"脑子很难停下来。你对无聊过敏，需要新鲜的信息和有趣的人来充电",
        "巨蟹座":"对自己人和外人天差地别。你在乎的人你什么都愿意做，不在乎的连敷衍都懒",
        "狮子座":"需要被看见。不是虚荣——是你需要确认自己的存在有意义",
        "处女座":"对自己挺狠的。事情没做好你先怪自己。你的标准是自律也是压力",
        "天秤座":"讲体面。你能看到所有人的角度，但轮到自己的事反而容易犹豫",
        "天蝎座":"信任门槛很高。过了你是最忠诚的人，没过你会一直观察",
        "射手座":"对被困住有生理性反感。你需要前面有路可走，需要自由和空间",
        "摩羯座":"是扛事的人。不想多说只想多做。你对结果负责——但对自己太苛刻",
        "水瓶座":"和别人不太一样。不是刻意的——你对主流本能地审视，需要自己的空间",
        "双鱼座":"感受世界的方式和大多数人不一样。细腻、敏感、容易共情也容易累",
    }.get(sign, "有自己独特的方式")


def _pick_moon_core(sign: str) -> str:
    return {
        "白羊座":"情绪来得快去得也快。最受不了的是等着——不确定让人焦躁",
        "金牛座":"关起门来最需要稳。看起来好商量，安全感底线触到了比谁都硬",
        "双子座":"真正的需求是有人跟你说话。孤独不是没人陪，是没人听得懂",
        "巨蟹座":"最大的开关是被需要。被忽略被敷衍会记很久——但不一定会说出来",
        "狮子座":"私底下需要一个认真的观众。不是拍马屁——是真心觉得你不错",
        "处女座":"关起门来最大的消耗是想太多。脑子停不下来——需要有人让你不想事",
        "天秤座":"独处时容易纠结。理解太全面了，反而不知道自己要什么",
        "天蝎座":"情绪很深，不轻易给人看。需要的是'这个人不会背叛我'的安全感",
        "射手座":"最怕无聊。需要前面有东西在等你——不然会萎",
        "摩羯座":"关起门来比外面柔软得多——只有极少数人知道",
        "水瓶座":"需要被理解成合理的不同。一个人待着是充电不是孤独",
        "双鱼座":"情绪像海——涨潮汹涌退潮安静。需要帮你落地的人",
    }.get(sign, "有自己的情绪节奏")


def _pick_venus_core(sign: str) -> str:
    return {
        "白羊座":"在感情里是主动的——喜欢就追，不浪费时间。但上头快下头也可能快",
        "金牛座":"慢热但投入。要时间确认，但一旦确认了是长期经营的",
        "双子座":"最看重聊得来。好看是加分，聊不来再好看也无聊",
        "巨蟹座":"会照顾人。记得对方一切的细节——你付出的是最柔软的那部分",
        "狮子座":"大方热烈的。需要被重视——被怠慢是你最难接受的",
        "处女座":"付出型——会为对方做很多。但需要被看见，不是工具人",
        "天秤座":"照顾氛围第一。不想吵架——但为了和谐委屈自己的次数太多了",
        "天蝎座":"要全部不是一部分。信任建立慢，但一旦建立是最忠诚的",
        "射手座":"需要空间。不是不爱——是对被限制太敏感",
        "摩羯座":"审慎长期主义。一开始就在评估能不能走远。爱用行动不是嘴",
        "水瓶座":"审美跟别人不一样。被控制最受不了。需要独立空间",
        "双鱼座":"浪漫包容的。容易给对对方加滤镜——需要学会问自己愿不愿意",
    }.get(sign, "有自己独特的感情模式")


def _pick_house_note(planet: str, house: int) -> str:
    notes = {
        ("SUN", 1):"所以你的自我和你要走的路是同一件事——你不是那种犹豫太久的人",
        ("SUN", 4):"所以家庭和根基是你人生绕不开的主题——你需要在外面闯，但内心需要一个基地",
        ("SUN", 5):"所以你在创作、表达和被欣赏的时候最觉得自己活着",
        ("SUN", 7):"所以你需要通过关系来确认自己——一个人待着的时候你会不太确定自己是谁",
        ("SUN", 10):"所以你在社会中需要有一个位置——你的存在感和你的成就绑在一起",
        ("SUN", 12):"所以你的光芒在幕后——你不是那种站在台前喊'看我'的人，但你的影响力在暗处",
        ("MOON", 1):"所以你的情绪都写在脸上——开心不开心都藏不住",
        ("MOON", 4):"所以你最需要的是一个家——不是房子，是那种有人等你的感觉",
        ("MOON", 7):"所以你的情绪会和伴侣绑在一起——对方开心你就安心，对方不开心你秒知",
        ("MOON", 8):"所以你的情绪是暗流涌动的——不是没有情绪，是不轻易给人看",
        ("MOON", 10):"所以你的情绪和事业绑在一起——工作顺你整个人都对，不顺你整个人都不对",
        ("MOON", 12):"所以你需要大量独处充电——不是孤僻，是情绪需要通过安静来消化",
        ("VENUS", 7):"所以你在关系中天然有吸引力——你能吸引到条件不错的对象",
        ("VENUS", 8):"所以你对感情的深度要求很高——表面的甜言蜜语打动不了你",
        ("VENUS", 10):"所以你的公众形象是有魅力的——不只是长相，是你整个人的气质让人舒服",
        ("VENUS", 12):"所以你的感情容易在'不被看见'的地方——不是你的错，但这个模式你需要注意",
    }
    return notes.get((planet, house), "")


def _build_observation(opener: str, o: dict) -> str:
    parts = [f"{opener}{o['core']}。"]
    # 宫位落点（过程）
    if o.get("house_note"):
        parts.append(o["house_note"] + "。")
    # 尊贵度（痛点/爽点）
    dignity_text = _dignity_pain_pleasure(o.get("dignity", "peregrine"), o.get("planet", ""))
    if dignity_text:
        parts.append(dignity_text + "。")
    # 飞星（过程→结果）
    if o.get("flystar"):
        parts.append(o["flystar"] + "。")
    # 金星12宫特殊提醒
    if o.get("venus_12h"):
        parts.append("你的金星在12宫——这个配置的人容易经历不被公开的感情。不是你的错，但你需要知道：你值得一段站在阳光下的关系。")
    return "".join(parts)


def _house_ruler(chart: Any, house: int) -> str:
    from .domains.helpers import house_ruler_name
    return house_ruler_name(chart, house)


def _house_title(h: int) -> str:
    from .domains.helpers import house_title
    return house_title(h)


_FLYSTAR_SHORT: dict[tuple[int, int], str] = {
    # ── 1宫主（自我）飞入各宫 ──
    (1, 2): "你搞清楚自己是谁的最好方式，不是照镜子——是看你的银行账户和你在创造什么价值",
    (1, 3): "你是通过说出去、写下来、跟人聊——才慢慢搞清楚自己",
    (1, 4): "你绕了一大圈才发现，最开始的那些事——家、根基、安全感——才是答案",
    (1, 5): "你在创作、表达和被欣赏的时候，才最像你自己",
    (1, 6): "你不是在空想中确认自己——是在每天的日常、工作和节奏里，一点一点拼出来的",
    (1, 7): "你最终是通过和另一个人站在一起，才真正搞清楚自己是谁",
    (1, 8): "你需要经历几次大的转变、甚至是危机——每一次'死去活来'都让你更接近自己",
    (1, 9): "你需要在路上确认自己——旅行、读书、接触更大的世界，而不是坐在家里想",
    (1, 10): "你的自我确认最终要靠事业和社会角色来完成——不是在镜子前面想通的",
    (1, 11): "你一个人搞不定自己。你需要一群对的人，在他们中间你才像自己",
    (1, 12): "你越不去想'我是谁'，你反而越接近答案——在独处、安静和不被打扰的时候",
    # ── 2宫主（财富）飞入各宫 ──
    (2, 1): "你的钱和你是谁绑在一起——你的个人品牌、你的存在方式，就是你的收入来源",
    (2, 6): "你的钱是通过日常工作和持续交付赚出来的——不是投机，是积累",
    (2, 8): "你的钱不只是靠赚——更靠你怎么处理别人的钱、怎么处理信任",
    (2, 10): "你的收入和你的事业地位直接挂钩——往上走，钱自然来",
    # ── 3宫主（沟通/学习）飞入 ──
    (3, 9): "你早期的学习经历，最终会把你引向更大的知识和远方的世界",
    (3, 10): "你说的话、写的东西、表达的方式——这些是你事业的隐形阶梯",
    # ── 4宫主（家庭/根基）飞入各宫 ──
    (4, 1): "你的原生家庭给你的东西，最后变成了你这个人最核心的底色",
    (4, 7): "你原生家庭里没解决的东西，会在伴侣关系里重新出现——这是你的功课",
    (4, 9): "你的根扎得越深，你走得越远。家庭给你的东西，是你探索世界的出发点",
    (4, 10): "你的家庭和根基，最终会成为你事业最大的支撑——不是负担",
    (4, 11): "你通过家庭和根基连接到的圈子和人脉，比你想象的更广",
    # ── 5宫主（创造/恋爱）飞入各宫 ──
    (5, 1): "恋爱和创造不是你人生的'副业'——它们就是你这个人最重要的组成部分",
    (5, 7): "你的桃花和你的婚姻是连在一起的——没有'随便谈谈'这回事",
    (5, 9): "你在创作和恋爱中学到的东西，最终会变成你的人生信念和世界观",
    (5, 10): "你的创造力和恋爱，会影响你的事业高度——这两个不是分开的",
    # ── 6宫主（工作/健康）飞入 ──
    (6, 1): "你的日常工作和身体状态，直接塑造了你这个人——你不是'想'出来的，是'做'出来的",
    (6, 10): "把日常的事做得比别人好一百倍——这就是你事业的真正跳板",
    # ── 7宫主（伴侣/合作）飞入各宫 ──
    (7, 1): "你的关系最终是帮你完成自我的——不是为了别人牺牲自己",
    (7, 4): "你的伴侣会让你重新面对家庭和根基的课题——ta不是你原生家庭的解药，是镜子",
    (7, 9): "你的伴侣或合伙人，最可能和'远方'有关——地理上的、文化上的、或者是视野上的",
    (7, 10): "你的伴侣或合伙人是你事业的关键推手——选对了人，事半功倍",
    # ── 8宫主（偏财/转化）飞入 ──
    (8, 2): "你的偏财运和投资直觉，会直接转化成你的正财收入——不是靠死工资",
    (8, 6): "你在危机和高压中学到的东西，在日常工作中反复帮你——那些'太难了'的时刻是你的隐藏简历",
    (8, 12): "你在金钱和信任上的功课，最终要到独处和内省里消化",
    # ── 9宫主（远见/学业）飞入 ──
    (9, 1): "你学的东西、你相信的理念——不是身外之物，是你这个人最核心的组成",
    (9, 10): "你的学识和远见，直接转换成你的社会地位——你是靠头脑上位的",
    # ── 10宫主（事业）飞入各宫 ──
    (10, 1): "你的事业就是你自己——你的个人品牌、你的存在方式，就是你的职业",
    (10, 4): "不管你在外面爬得多高，你的根基和家庭一直是你的底盘——别忽视它",
    (10, 5): "你的事业需要你的创造力和个人魅力——不是苦干，是发光",
    (10, 6): "你的事业不是冲在一线，是把日常的事做得比别人好一百倍",
    (10, 7): "事业这条路，你一个人走不远——你需要一个搭档、伴侣或合伙人",
    (10, 9): "你的事业需要通过学识、远见和传播来放大——不是苦干，是巧干",
    # ── 11宫主（社群/愿景）飞入 ──
    (11, 1): "你的圈子和人脉不是身外的——它们是你自我认同的一部分",
    (11, 3): "你的人脉圈子最终是靠你的表达和传播来扩大的——不是社交，是输出",
    (11, 10): "你的人脉和社群，是你事业上最重要的杠杆——朋友介绍的机会比你面试来的好",
    # ── 12宫主（潜意识/隐退）飞入 ──
    (12, 1): "那些你自己都不太清楚的东西，最后会变成你最独特的个人标签",
    (12, 3): "你没说出来的那些话、你在独处时想的事——写下来，你会吓到自己",
    (12, 6): "你的隐性压力和潜意识，会在身体和日常节奏上留下痕迹——照顾好自己不是矫情",
}


def _flystar_meaning(ruler: str, from_house: int, to_house: int) -> str:
    short = _FLYSTAR_SHORT.get((from_house, to_house))
    if short:
        return short
    from .domains.helpers import plabel
    ruler_label = plabel(ruler) if ruler else "一颗星"
    to_title = _house_title(to_house)
    return (
        f"{ruler_label}把这个领域的故事带到了{to_title}。"
        f"这意味着你的答案不在原地——要去{to_title}那个方向找"
    )


_DIGNITY_PAIN_PLEASURE: dict[str, str] = {
    "domicile": "这是你的天赋位——你在这方面不需要太费劲，做自己就是对的。别人要学的东西你天生就有",
    "exaltation": "这个位置是你星盘里的一个高点——在这一块你比别人更容易被认可、被看见",
    "detriment": "说实话，这个领域不是你的舒适区。你可能会觉得别人轻松做到的你得花更多力气——但一旦找到方法，别人抄不走",
    "fall": "这是你星盘里需要最多耐心的地方。这个领域的课题来得早——但过了之后你的韧性是没人能比的",
}


def _dignity_pain_pleasure(dignity: str, planet: str) -> str:
    return _DIGNITY_PAIN_PLEASURE.get(dignity, "")

