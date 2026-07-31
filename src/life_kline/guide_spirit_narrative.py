"""
guide_spirit_narrative.py — 引路星灵自述引擎

宫性优先、星性修饰。输出5段第一人称自述：
  1. 我是你的谁 — 宫主星 → 结果（我替你管哪些人生领域）
  2. 我在哪里干活 — 宫内星 → 过程（我通过什么经历来训练你）
  3. 飞星链路 — 过程 → 结果的完整叙事
  4. 今天为什么是我 — 行运触发 + 宫位激活
  5. 给你的方向 — 基于宫性链的可行动建议

纯规则驱动，不依赖 LLM。所有占星事实来自引擎计算。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from .constants import Planet
from .domains.helpers import (
    SIGN_RULER_MAP,
    PLANET_LABEL_CN,
    SIGN_LABEL_CN,
    HOUSE_TITLES as _HOUSE_TITLES_SHORT,
)
from .interpretation.house_rules import HOUSE_DATA
from .characters.planet_personas import (
    PLANET_PERSONAS,
    PlanetPersona,
    get_planet_persona,
)
from .today_engine import TodayStarSpirit


# ═══════════════════════════════════════════════════════════════
# 常量
# ═══════════════════════════════════════════════════════════════

# 参与宫主星计算的传统行星（三王星无传统守护星座）
_TRADITIONAL_RULERS = {"SUN", "MOON", "MERCURY", "VENUS", "MARS", "JUPITER", "SATURN"}

# 触发类型 → 中文标签
_TRIGGER_TYPE_LABELS: dict[str, str] = {
    "exact_transit": "精准行运",
    "moon_trigger": "月亮触动",
    "moon_ruler": "月亮指引",
    "firdaria": "法达大运",
    "default": "自然守护",
}

# 尊贵状态 → 叙事语气修饰
_DIGNITY_TONE: dict[str, dict[str, str]] = {
    "domicile": {
        "label": "入庙",
        "strength_phrase": "这里是我的主场——我做主",
        "process_phrase": "我不绕路，直接在{house}宫就把事办了",
    },
    "exaltation": {
        "label": "擢升",
        "strength_phrase": "我在这里被放大——比平时更有力",
        "process_phrase": "通过{house}宫的经历，你能拿到超出预期的成长",
    },
    "peregrine": {
        "label": "平常",
        "strength_phrase": "我在这里不强势，但也不受伤——正常发挥",
        "process_phrase": "在{house}宫的经历里慢慢磨，不急",
    },
    "detriment": {
        "label": "失势",
        "strength_phrase": "我在这里不太舒服——不是我做不了事，是做事的方式要拐弯",
        "process_phrase": "你在{house}宫吃的亏，恰恰是我在训练你的方式",
    },
    "fall": {
        "label": "落陷",
        "strength_phrase": "我在这里最弱——但这不代表你不成长，只是成长的方式比较痛",
        "process_phrase": "{house}宫是你反复摔跤的地方，也是你最后站得最稳的地方",
    },
}

# 行运相位 → 触发叙事片段
_ASPECT_NARRATIVE_FRAGMENTS: dict[str, str] = {
    "合相": "正在激活",
    "对冲": "正在两端拉扯",
    "刑相": "正在施压、逼你做选择",
    "三合": "正在顺流推你一把",
    "六合": "正在侧面敲你一下",
}


# ═══════════════════════════════════════════════════════════════
# 辅助函数
# ═══════════════════════════════════════════════════════════════

def _planet_cn(planet_str: str) -> str:
    """行星英文 → 中文名"""
    return PLANET_LABEL_CN.get(planet_str, planet_str)


def _sign_cn(sign_str: str) -> str:
    """星座英文 → 中文名"""
    return SIGN_LABEL_CN.get(sign_str, sign_str)


def _house_title(house_num: int) -> str:
    """宫位号 → 中文名（短版）"""
    return _HOUSE_TITLES_SHORT.get(house_num, f"第{house_num}宫")


def _house_full_title(house_num: int) -> str:
    """宫位号 → 完整中文名"""
    data = HOUSE_DATA.get(house_num, {})
    return str(data.get("title", f"第{house_num}宫"))


def _house_ruler_meaning(house_num: int) -> str:
    """获取某宫的宫主星含义文本"""
    data = HOUSE_DATA.get(house_num, {})
    return str(data.get("ruler_meaning", ""))


def _house_planet_in_meaning(house_num: int) -> str:
    """获取某宫的宫内星含义文本"""
    data = HOUSE_DATA.get(house_num, {})
    return str(data.get("planet_in_meaning", ""))


def _houses_list_cn(house_nums: list[int]) -> str:
    """宫位号列表 → 中文拼接，如 '第2宫和第9宫'"""
    if not house_nums:
        return ""
    parts = [f"第{h}宫（{_house_full_title(h)}）" for h in house_nums]
    if len(parts) == 1:
        return parts[0]
    return "和".join(["、".join(parts[:-1]), parts[-1]]) if len(parts) > 2 else f"{parts[0]}和{parts[1]}"


def compute_planet_rulerships(houses: list) -> dict[str, list[int]]:
    """从12宫头数据计算每颗传统行星掌管哪些宫。

    Args:
        houses: 12个元素的列表，每个是 (sign_str, degree) 或类似结构。
                sign_str 如 "ARIES", "TAURUS"。

    Returns:
        {"SUN": [5], "MOON": [4], "MERCURY": [3, 6], ...}
    """
    result: dict[str, list[int]] = {p: [] for p in _TRADITIONAL_RULERS}
    for i, cusp in enumerate(houses):
        house_num = i + 1
        # 兼容多种数据格式：tuple/list/dict/对象
        sign_str = _extract_sign_str(cusp)
        ruler = SIGN_RULER_MAP.get(sign_str)
        if ruler and ruler in result:
            result[ruler].append(house_num)
    return result


def _extract_sign_str(cusp: Any) -> str:
    """从宫头数据的多种格式中提取星座字符串（如 'ARIES'）。"""
    if isinstance(cusp, dict):
        # 报告中的 dict 格式: {'house': 1, 'sign': 'GEMINI', ...}
        return str(cusp.get("sign", ""))
    if isinstance(cusp, (list, tuple)):
        return str(cusp[0]) if len(cusp) > 0 else ""
    if hasattr(cusp, "value"):
        return str(cusp.value)
    return str(cusp)


def _dignity_tone_for(dignity_code: str) -> dict[str, str]:
    """获取尊贵状态对应的叙事语气"""
    return _DIGNITY_TONE.get(
        dignity_code,
        {"label": dignity_code, "strength_phrase": "", "process_phrase": ""},
    )


# ═══════════════════════════════════════════════════════════════
# 数据类
# ═══════════════════════════════════════════════════════════════

@dataclass
class GuideSpiritNarrative:
    """引路星灵完整自述"""

    spirit_planet: str
    spirit_name: str
    spirit_symbol: str
    trigger_type: str
    confidence: float

    # 宫性数据
    ruled_houses: list[int]              # 该行星是哪些宫的宫主星
    located_house: int                   # 该行星落在哪个宫
    located_sign: str                    # 该行星落在哪个星座
    dignity_code: str                    # 尊贵状态
    dignity_label: str
    is_chart_ruler: bool                 # 是否为命主星

    # 五段自述
    segment_who_am_i: str                # 1. 我是你的谁（宫主星 → 结果）
    segment_where_i_work: str            # 2. 我在哪里干活（宫内星 → 过程）
    segment_flystar_chain: str           # 3. 飞星链路（过程 → 结果）
    segment_why_me_today: str            # 4. 今天为什么是我（行运触发）
    segment_guidance: str                # 5. 给你的方向

    # 组合输出
    full_introduction: str               # 完整自述文本

    # 元数据
    evidence: list[str] = field(default_factory=list)
    persona_snapshot: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "spirit_planet": self.spirit_planet,
            "spirit_name": self.spirit_name,
            "spirit_symbol": self.spirit_symbol,
            "trigger_type": self.trigger_type,
            "confidence": self.confidence,
            "ruled_houses": self.ruled_houses,
            "located_house": self.located_house,
            "located_sign": self.located_sign,
            "dignity_code": self.dignity_code,
            "dignity_label": self.dignity_label,
            "is_chart_ruler": self.is_chart_ruler,
            "segments": {
                "who_am_i": self.segment_who_am_i,
                "where_i_work": self.segment_where_i_work,
                "flystar_chain": self.segment_flystar_chain,
                "why_me_today": self.segment_why_me_today,
                "guidance": self.segment_guidance,
            },
            "full_introduction": self.full_introduction,
            "evidence": self.evidence,
            "persona_snapshot": self.persona_snapshot,
        }


# ═══════════════════════════════════════════════════════════════
# 引路星灵自述引擎
# ═══════════════════════════════════════════════════════════════

class GuideSpiritNarrativeEngine:
    """引路星灵自述引擎 — 宫性优先，纯规则驱动。

    用法:
        engine = GuideSpiritNarrativeEngine()
        narrative = engine.compute(today_spirit, natal_chart, planet_characters)
    """

    def compute(
        self,
        today_spirit: TodayStarSpirit,
        natal_chart: dict[str, Any],
        planet_characters: dict[str, dict[str, Any]],
        firdaria_period: Any = None,
    ) -> GuideSpiritNarrative:
        """计算完整引路星灵自述。

        Args:
            today_spirit: TodayStarSpiritEngine 的输出
            natal_chart: report_data["natal_chart"]，需含 "houses" 键
            planet_characters: report_data["planet_characters"]["planet_characters"]
            firdaria_period: 可选的法达周期对象

        Returns:
            GuideSpiritNarrative 完整自述
        """
        planet_str = today_spirit.planet
        persona = self._safe_get_persona(planet_str)
        houses = natal_chart.get("houses", [])

        # ── 宫性数据提取 ──
        all_rulerships = compute_planet_rulerships(houses)
        ruled_houses_all = all_rulerships.get(planet_str, [])

        planet_char = planet_characters.get(planet_str, {})
        located_house = planet_char.get("house", 0)
        located_sign = planet_char.get("sign", "")
        located_sign_label = planet_char.get("sign_label", "")
        dignity_code = planet_char.get("dignity_code", "peregrine")
        dignity_label = planet_char.get("dignity_label", "平常")
        is_chart_ruler = planet_char.get("is_chart_ruler", False)

        # 宫内星自守：行星在它自己掌管的宫里 → 拆分处理
        # ruled_houses_all 包含所有宫位（含自守宫），用于段1身份声明
        # ruled_houses_other 不含自守宫，用于段3飞星链路避免 7→7 自循环
        is_in_own_house = located_house in ruled_houses_all
        ruled_houses_other = [h for h in ruled_houses_all if h != located_house]

        # ── 触发类型判定 ──
        trigger_type = today_spirit.trigger_type or "default"
        transit_aspect = today_spirit.transit_aspect

        # ── 证据收集 ──
        evidence = self._collect_evidence(
            planet_str, ruled_houses_all, located_house, dignity_code, trigger_type
        )

        # ── 渲染五段 ──
        seg1 = self._render_who_am_i(
            planet_str, persona, ruled_houses_all, located_house,
            dignity_code, is_chart_ruler, is_in_own_house,
        )
        seg2 = self._render_where_i_work(
            planet_str, persona, located_house, located_sign_label,
            dignity_code, is_in_own_house,
        )
        seg3 = self._render_flystar_chain(
            planet_str, persona, ruled_houses_other, located_house,
            dignity_code, is_in_own_house,
        )
        seg4 = self._render_why_me_today(
            planet_str, persona, trigger_type, transit_aspect,
            located_house, ruled_houses_all, firdaria_period,
        )
        seg5 = self._render_guidance(
            planet_str, persona, ruled_houses_other, located_house, trigger_type,
        )

        # ── 组合完整文本 ──
        full = self._assemble_full(
            persona, seg1, seg2, seg3, seg4, seg5,
        )

        return GuideSpiritNarrative(
            spirit_planet=planet_str,
            spirit_name=_planet_cn(planet_str),
            spirit_symbol=today_spirit.symbol,
            trigger_type=trigger_type,
            confidence=today_spirit.confidence,
            ruled_houses=ruled_houses_all,
            located_house=located_house,
            located_sign=located_sign,
            dignity_code=dignity_code,
            dignity_label=dignity_label,
            is_chart_ruler=is_chart_ruler,
            segment_who_am_i=seg1,
            segment_where_i_work=seg2,
            segment_flystar_chain=seg3,
            segment_why_me_today=seg4,
            segment_guidance=seg5,
            full_introduction=full,
            evidence=evidence,
            persona_snapshot={
                "name_zh": persona.name_zh,
                "archetype_zh": persona.archetype_zh,
                "voice_tone": persona.voice_tone,
                "advice_approach": persona.advice_approach,
            },
        )

    # ── 证据收集 ────────────────────────────────────────────

    @staticmethod
    def _collect_evidence(
        planet_str: str,
        ruled_houses: list[int],
        located_house: int,
        dignity_code: str,
        trigger_type: str,
    ) -> list[str]:
        """收集用于自述的星盘证据清单"""
        evidence = [
            f"引路行星: {_planet_cn(planet_str)}",
            f"触发类型: {_TRIGGER_TYPE_LABELS.get(trigger_type, trigger_type)}",
        ]
        if ruled_houses:
            evidence.append(
                f"宫主星掌管: {', '.join(_house_full_title(h) for h in ruled_houses)}"
            )
        else:
            evidence.append("宫主星: 无传统守护宫位（三王星）")
        if located_house:
            evidence.append(f"宫内星落: {_house_full_title(located_house)}")
        evidence.append(f"尊贵状态: {_DIGNITY_TONE.get(dignity_code, {}).get('label', dignity_code)}")
        return evidence

    # ── 段1: 我是你的谁（宫主星 → 结果）────────────────────

    @staticmethod
    def _render_who_am_i(
        planet_str: str,
        persona: PlanetPersona,
        ruled_houses: list[int],
        located_house: int,
        dignity_code: str,
        is_chart_ruler: bool,
        is_in_own_house: bool = False,
    ) -> str:
        """渲染第一段：宫主星身份声明"""
        name = persona.name_zh

        # 外行星无传统守护 → 不同的开场
        if not ruled_houses:
            if is_chart_ruler:
                return (
                    f"我是{name}。在传统守护体系里我不掌管任何一宫——"
                    f"但你的上升星座落在我的星座上，我是你的命主星。"
                    f"你整个人生的基调，都染着我的颜色。"
                )
            return (
                f"我是{name}。在传统守护体系里我不掌管具体宫位——"
                f"我不是你的哪个领域的'地主'。但我落在你的"
                f"第{located_house}宫（{_house_full_title(located_house)}），"
                f"这是我在你生命里最直接的力量所在。"
            )

        # 有宫主星身份
        houses_cn = _houses_list_cn(ruled_houses)
        chart_ruler_suffix = ""
        if is_chart_ruler:
            chart_ruler_suffix = "。同时你的上升星座落在我的星座上——我是你的命主星，整张盘的基调由我定"

        count = len(ruled_houses)
        prefix = "这两个领域" if count == 2 else "这个领域" if count == 1 else "这些领域"

        return (
            f"我是{name}。在你的星盘里，{houses_cn}的宫头落在我的星座上——"
            f"{prefix}的最终收成，归我管。"
            f"{chart_ruler_suffix}。"
        )

    # ── 段2: 我在哪里干活（宫内星 → 过程）─────────────────

    @staticmethod
    def _render_where_i_work(
        planet_str: str,
        persona: PlanetPersona,
        located_house: int,
        located_sign_label: str,
        dignity_code: str,
        is_in_own_house: bool = False,
    ) -> str:
        """渲染第二段：宫内星过程描述"""
        if located_house <= 0:
            return ""

        name = persona.name_zh
        house_title = _house_full_title(located_house)
        dignity_info = _dignity_tone_for(dignity_code)
        strength = dignity_info["strength_phrase"]

        # 宫内星自守：行星在自己掌管的宫里
        own_house_note = ""
        if is_in_own_house:
            own_house_note = (
                f"而且——{house_title}的宫头就落在我的星座上，我是这宫的主人。"
                f"我不需要通过别的领域绕路——我直接在{house_title}就把事办了。"
            )

        return (
            f"但我不住在我管的那些宫里——我住在你的第{located_house}宫"
            f"（{house_title}），落在{located_sign_label}。"
            f"{strength}。"
            f"{own_house_note}"
            f"你正通过{house_title}的经历，来学习我负责的功课。"
        )

    # ── 段3: 飞星链路（过程 → 结果）────────────────────────

    @staticmethod
    def _render_flystar_chain(
        planet_str: str,
        persona: PlanetPersona,
        ruled_houses_other: list[int],
        located_house: int,
        dignity_code: str,
        is_in_own_house: bool = False,
    ) -> str:
        """渲染第三段：宫性链 —— 过程如何连接到结果"""
        if located_house <= 0:
            return ""

        name = persona.name_zh
        process_house_title = _house_full_title(located_house)
        dignity_info = _dignity_tone_for(dignity_code)
        process_phrase = dignity_info["process_phrase"].format(
            house=process_house_title
        )

        # 宫内星自守 + 无其他宫主星身份 → 纯粹的自守叙事
        if is_in_own_house and not ruled_houses_other:
            return (
                f"所以你在{process_house_title}里经历的一切，就在这里开花结果——"
                f"不需要绕路去别的领域。"
                f"{process_phrase}。"
                f"这是最直接的配置：你的{name}既是这个领域的主人，也在这里干活——"
                f"意味着你在{process_house_title}上的成长，每一步都直接算数。"
            )

        # 外行星无宫主星身份 → 聚焦过程本身
        if not ruled_houses_other and not is_in_own_house:
            return (
                f"所以你在{process_house_title}里经历的事，不是孤立的。"
                f"{process_phrase}——{name}的方式是让你在这个领域里反复碰撞，"
                f"直到你摸到更深的东西。"
            )

        # 有宫主星 → 完整飞星链
        result_houses_cn = _houses_list_cn(ruled_houses_other)

        return (
            f"这就意味着：你在{process_house_title}经历的所有事——"
            f"那些磨合、那些起伏、那些反复出现的模式——不是在{process_house_title}宫结束的。"
            f"它们最终会落到{result_houses_cn}的收成上。"
            f"{process_phrase}。"
        )

    # ── 段4: 今天为什么是我（行运触发）─────────────────────

    @staticmethod
    def _render_why_me_today(
        planet_str: str,
        persona: PlanetPersona,
        trigger_type: str,
        transit_aspect: Optional[dict],
        located_house: int,
        ruled_houses: list[int],
        firdaria_period: Any,
    ) -> str:
        """渲染第四段：今天为什么是这颗星灵引路"""
        name = persona.name_zh

        if trigger_type == "exact_transit" and transit_aspect:
            return _render_exact_transit_trigger(
                name, transit_aspect, located_house, ruled_houses
            )
        elif trigger_type == "moon_trigger" and transit_aspect:
            return _render_moon_trigger(name, located_house, ruled_houses)
        elif trigger_type == "moon_ruler":
            return _render_moon_ruler_trigger(name, located_house, ruled_houses)
        elif trigger_type == "firdaria":
            return _render_firdaria_trigger(name, firdaria_period, located_house, ruled_houses)
        else:
            return _render_default_trigger(name, located_house, ruled_houses)

    # ── 段5: 给你的方向 ─────────────────────────────────────

    @staticmethod
    def _render_guidance(
        planet_str: str,
        persona: PlanetPersona,
        ruled_houses_other: list[int],
        located_house: int,
        trigger_type: str,
    ) -> str:
        """渲染第五段：基于宫性链的可行动建议"""
        name = persona.name_zh

        if located_house <= 0:
            return f"今天，听听{name}怎么说：{persona.gift_to_user}"

        process_house = _house_full_title(located_house)

        if not ruled_houses_other:
            return (
                f"所以今天——你在{process_house}里感受到的任何波动，"
                f"不用急着去别的地方找答案。答案就在{process_house}本身。"
                f"{name}说：{persona.gift_to_user}"
            )

        result_first = _house_full_title(ruled_houses_other[0])
        return (
            f"所以今天——你在{process_house}里感受到的不舒服，"
            f"别只把它当成{process_house}的问题。"
            f"它很可能在替你的{result_first}敲门——让你重新看它。"
            f"{persona.gift_to_user}"
        )

    # ── 组合──────────────────────────────────────────────────

    @staticmethod
    def _assemble_full(
        persona: PlanetPersona,
        seg1: str,
        seg2: str,
        seg3: str,
        seg4: str,
        seg5: str,
    ) -> str:
        """将五段组合成完整自述文本"""
        name = persona.name_zh
        parts = [
            f"你好，我是{name}——你今天的引路星灵。",
            "",
            seg1,
            "",
            seg2,
            "",
            seg3,
            "",
            seg4,
            "",
            seg5,
        ]
        return "\n".join(p for p in parts if p)

    # ── 辅助 ─────────────────────────────────────────────────

    @staticmethod
    def _safe_get_persona(planet_str: str) -> PlanetPersona:
        """安全获取行星 persona，未知行星回退到月亮"""
        try:
            planet_enum = Planet(planet_str)
            return get_planet_persona(planet_enum)
        except (ValueError, KeyError):
            return get_planet_persona(Planet.MOON)


# ═══════════════════════════════════════════════════════════════
# 触发类型渲染函数
# ═══════════════════════════════════════════════════════════════

def _render_exact_transit_trigger(
    name: str,
    transit_aspect: dict,
    located_house: int,
    ruled_houses: list[int],
) -> str:
    """精准行运触发叙事"""
    t_planet = _planet_cn(transit_aspect.get("transiting_planet", ""))
    n_planet = _planet_cn(transit_aspect.get("natal_planet", ""))
    aspect_label = transit_aspect.get("aspect_label", "触发")
    orb = transit_aspect.get("orb", 0)

    verb = _ASPECT_NARRATIVE_FRAGMENTS.get(aspect_label, "正在影响")

    base = (
        f"今天行运{t_planet}正{verb}你的本命{n_planet}"
        f"（容许度 {orb}°）——这是今天最紧的相位。"
    )

    if located_house > 0:
        house_title = _house_full_title(located_house)
        base += f"这个触发点恰好落在你的{house_title}。"

    if ruled_houses:
        ruled_str = _houses_list_cn(ruled_houses)
        base += (
            f"它在撬动你整条'{house_title if located_house > 0 else ''}"
            f"→ {ruled_str}'的轴线——"
            f"今天你在这个领域里会格外敏感。"
        )

    return base


def _render_moon_trigger(
    name: str,
    located_house: int,
    ruled_houses: list[int],
) -> str:
    """月亮触发叙事"""
    base = "今天行运月亮触动了你——月亮走得太快，它的触动往往是情绪的、一闪而过的，但也正是因为它快，它能照到你平时注意不到的地方。"

    if located_house > 0:
        house_title = _house_full_title(located_house)
        base += f"今天月亮撩动了你的{house_title}——注意那些突然涌上来的情绪，它们不是无缘无故的。"

    if ruled_houses:
        ruled_str = _houses_list_cn(ruled_houses)
        base += f"这些情绪的方向盘最终指向{ruled_str}——情绪只是信使。"

    return base


def _render_moon_ruler_trigger(
    name: str,
    located_house: int,
    ruled_houses: list[int],
) -> str:
    """月亮星座守护触发叙事"""
    base = "今天的月亮落在一个需要我出面的星座——月亮走到哪里，情绪的聚光灯就打到哪里。"

    if located_house > 0:
        house_title = _house_full_title(located_house)
        base += f"而我在你的{house_title}等着——今天你的情绪雷达会自然往这个方向转。"

    if ruled_houses:
        ruled_str = _houses_list_cn(ruled_houses)
        base += f"留意{house_title if located_house > 0 else '情绪'}跟{ruled_str}的关联——月亮不会无缘无故照一个地方。"

    return base


def _render_firdaria_trigger(
    name: str,
    firdaria_period: Any,
    located_house: int,
    ruled_houses: list[int],
) -> str:
    """法达大运触发叙事"""
    base = f"你正处在{name}的大运里——这不是一天两天的事，是几年的主旋律。"

    if located_house > 0:
        house_title = _house_full_title(located_house)
        base += f"这段大运选在你的{house_title}展开——不是随机选的。"

    if ruled_houses:
        ruled_str = _houses_list_cn(ruled_houses)
        base += (
            f"这几年的所有经历，最终都在雕刻你的{ruled_str}。"
            f"今天也不例外——只是这几年的一个缩影。"
        )

    return base


def _render_default_trigger(
    name: str,
    located_house: int,
    ruled_houses: list[int],
) -> str:
    """默认/月亮回退触发叙事"""
    base = "今天没有特别紧的相位——但不代表没有指引。"

    if located_house > 0:
        house_title = _house_full_title(located_house)
        base += f"安静的日子，最适合回到你的{house_title}——看看有什么被你忽略的信号。"

    if ruled_houses:
        ruled_str = _houses_list_cn(ruled_houses)
        base += f"{ruled_str}不会因为今天安静就停止运作——它们只是在后台跑。"

    return base


# ═══════════════════════════════════════════════════════════════
# 便捷函数
# ═══════════════════════════════════════════════════════════════

def compute_guide_narrative(
    today_spirit: TodayStarSpirit,
    natal_chart: dict[str, Any],
    planet_characters: dict[str, dict[str, Any]],
    firdaria_period: Any = None,
) -> GuideSpiritNarrative:
    """便捷函数：计算引路星灵完整自述。

    Args:
        today_spirit: TodayStarSpiritEngine 的输出
        natal_chart: report_data["natal_chart"]
        planet_characters: report_data["planet_characters"]["planet_characters"]
        firdaria_period: 可选的法达周期
    """
    engine = GuideSpiritNarrativeEngine()
    return engine.compute(
        today_spirit, natal_chart, planet_characters, firdaria_period
    )
