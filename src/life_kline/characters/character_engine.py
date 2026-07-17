"""
character_engine.py — 角色个性化引擎

从用户的星盘数据计算12星座角色的个性化状态：
- 存在感 (presence): 该星座在此人生命中的表达强度
- 舒适度 (comfort): 落此星座的行星状态是否舒适
- 角色标签 (role_tag): 天赋/课题/背景
- 个性化叙事 (personalized_greeting, storylines)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..constants import (
    ANGULAR_HOUSES,
    DOMICILE_SIGNS,
    DETRIMENT_SIGNS,
    EXALTATION_SIGNS,
    FALL_SIGNS,
    Planet,
    Sign,
    SIGN_ELEMENT,
    SIGN_MODALITY,
    get_sign_element,
    get_sign_modality,
    clamp,
)
from .sign_personas import SignPersona, SIGN_PERSONAS, get_persona


# ── 行星权重（用于存在感计算）─────────────────────────────

_PLANET_PRESENCE_WEIGHTS: dict[Planet, float] = {
    Planet.SUN: 2.5,
    Planet.MOON: 2.0,
    Planet.MERCURY: 1.0,
    Planet.VENUS: 1.0,
    Planet.MARS: 1.0,
    Planet.JUPITER: 1.0,
    Planet.SATURN: 1.0,
    Planet.URANUS: 0.5,
    Planet.NEPTUNE: 0.5,
    Planet.PLUTO: 0.5,
}

# 宫头星座权重
_HOUSE_CUSP_WEIGHTS: dict[int, float] = {
    1: 1.5,   # ASC
    4: 0.8,   # IC
    7: 0.8,   # DSC
    10: 1.5,  # MC
    2: 0.5, 3: 0.5, 5: 0.5, 6: 0.5,
    8: 0.5, 9: 0.5, 11: 0.5, 12: 0.5,
}

# 尊贵评分映射
_DIGNITY_COMFORT: dict[str, float] = {
    "domicile": 2.0,
    "exaltation": 1.5,
    "triplicity": 0.8,
    "term": 0.5,
    "face": 0.3,
    "peregrine": 0.0,
    "detriment": -1.5,
    "fall": -2.0,
}


# ═══════════════════════════════════════════════════════════════
# 角色画像数据类
# ═══════════════════════════════════════════════════════════════

@dataclass
class CharacterProfile:
    """一个星座角色的完整个性化画像——与具体用户星盘绑定"""
    sign: Sign
    persona: SignPersona                    # 固定原型（来自 sign_personas.py）
    presence_score: float                   # 存在感 0-100
    comfort_score: float                    # 舒适度 -100 ~ +100
    role_tag: str                           # "天赋角色" / "课题角色" / "背景角色"
    planets_here: list[str]                 # 落此星座的行星名称（中文）
    planets_dignity: dict[str, str]         # 行星 → 尊贵状态
    house_cusps_here: list[int]             # 宫头落此星座的宫位
    is_ascendant: bool                      # 是否是上升星座
    is_midheaven: bool                      # 是否是 MC 星座
    storylines: list[str]                   # 飞星故事线（中文叙事）
    linked_domains: list[str]               # 关联的生命领域
    personalized_greeting: str              # 个性化开场白

    def to_dict(self) -> dict[str, Any]:
        return {
            "sign": self.sign.value,
            "persona": self.persona.to_dict(),
            "presence_score": round(self.presence_score, 1),
            "comfort_score": round(self.comfort_score, 1),
            "role_tag": self.role_tag,
            "planets_here": self.planets_here,
            "planets_dignity": self.planets_dignity,
            "house_cusps_here": self.house_cusps_here,
            "is_ascendant": self.is_ascendant,
            "is_midheaven": self.is_midheaven,
            "storylines": self.storylines,
            "linked_domains": self.linked_domains,
            "personalized_greeting": self.personalized_greeting,
        }


# ═══════════════════════════════════════════════════════════════
# 角色引擎
# ═══════════════════════════════════════════════════════════════

class CharacterEngine:
    """从星盘数据生成12星座个性化角色画像的引擎。

    所有计算完全由规则驱动——无硬编码、无 LLM。
    """

    def __init__(self, chart: Any):
        """
        Args:
            chart: ChartData 或兼容对象。需提供:
                   - chart.planets: Dict[Planet, PlanetInfo]
                   - chart.houses: List[Tuple[Sign, float]] (12宫头)
                   - 兼容 getattr(chart, 'planets', {}) 的对象均可
        """
        self.chart = chart
        self._planet_signs: dict[Planet, Sign] = {}
        self._planet_houses: dict[Planet, int] = {}
        self._planet_dignities: dict[Planet, str] = {}
        self._house_cusp_signs: dict[int, Sign] = {}
        self._asc_sign: Sign | None = None
        self._mc_sign: Sign | None = None
        self._chart_ruler: Planet | None = None
        self._parse_chart()

    # ── 解析星盘 ──────────────────────────────────────────

    def _parse_chart(self) -> None:
        """从 chart 对象解析行星位置和宫头信息。兼容 ChartData 和 dict-like 对象。"""
        # 解析行星
        planets = getattr(self.chart, "planets", {})
        for planet, info in planets.items():
            if hasattr(info, "sign"):
                self._planet_signs[planet] = info.sign
            if hasattr(info, "house"):
                self._planet_houses[planet] = info.house

        # 解析宫头
        houses = getattr(self.chart, "houses", [])
        if houses:
            for i, (sign, _) in enumerate(houses[:12]):
                house_num = i + 1
                self._house_cusp_signs[house_num] = sign
                if house_num == 1:
                    self._asc_sign = sign
                if house_num == 10:
                    self._mc_sign = sign

        # 计算命主星
        if self._asc_sign:
            self._chart_ruler = self._get_sign_ruler(self._asc_sign)

        # 计算行星尊贵度
        for planet, sign in self._planet_signs.items():
            self._planet_dignities[planet] = self._compute_dignity_code(planet, sign)

    @staticmethod
    def _get_sign_ruler(sign: Sign) -> Planet:
        """获取星座的传统守护星"""
        from ..constants import DOMICILE_SIGNS
        for planet, signs in DOMICILE_SIGNS.items():
            if sign in signs and planet in (
                Planet.SUN, Planet.MOON, Planet.MERCURY, Planet.VENUS,
                Planet.MARS, Planet.JUPITER, Planet.SATURN,
            ):
                return planet
        return Planet.SUN

    @staticmethod
    def _compute_dignity_code(planet: Planet, sign: Sign) -> str:
        """计算行星在星座中的尊贵状态"""
        if sign in DOMICILE_SIGNS.get(planet, []):
            return "domicile"
        if sign in EXALTATION_SIGNS.get(planet, []):
            return "exaltation"
        if sign in DETRIMENT_SIGNS.get(planet, []):
            return "detriment"
        if sign in FALL_SIGNS.get(planet, []):
            return "fall"
        return "peregrine"

    # ── 存在感计算 ────────────────────────────────────────

    def compute_sign_presence(self) -> dict[Sign, float]:
        """计算12星座在此人星盘中的存在感分数 (0-100)。

        算法：
        - 上升星座: +15
        - MC星座: +10
        - 太阳星座: +12
        - 月亮星座: +10
        - 每颗行星落此星座: 权重 * 1.5 (传统) 或 权重 * 0.8 (外行星)
        - 每个宫头落此星座: 宫位权重 * 1.0
        - 星群 (>=3颗传统行星): +8
        - 命主星所在星座: +5
        - 归一化到 0-100
        """
        raw: dict[Sign, float] = {s: 0.0 for s in Sign}

        # ASC + MC
        if self._asc_sign:
            raw[self._asc_sign] += 15.0
        if self._mc_sign:
            raw[self._mc_sign] += 10.0

        # 行星落点
        planet_count_per_sign: dict[Sign, int] = {s: 0 for s in Sign}
        traditional_planets = {
            Planet.SUN, Planet.MOON, Planet.MERCURY, Planet.VENUS,
            Planet.MARS, Planet.JUPITER, Planet.SATURN,
        }

        for planet, sign in self._planet_signs.items():
            weight = _PLANET_PRESENCE_WEIGHTS.get(planet, 0.5)
            raw[sign] += weight * 1.5
            if planet in traditional_planets:
                planet_count_per_sign[sign] += 1

        # 宫头
        for house_num, sign in self._house_cusp_signs.items():
            weight = _HOUSE_CUSP_WEIGHTS.get(house_num, 0.5)
            raw[sign] += weight * 1.0

        # 星群 bonus
        for sign, count in planet_count_per_sign.items():
            if count >= 3:
                raw[sign] += 8.0

        # 命主星
        if self._chart_ruler and self._chart_ruler in self._planet_signs:
            ruler_sign = self._planet_signs[self._chart_ruler]
            raw[ruler_sign] += 5.0

        # 归一化到 0-100
        max_raw = max(raw.values()) if raw else 1.0
        if max_raw > 0:
            return {s: round(v / max_raw * 100, 1) for s, v in raw.items()}
        return {s: 0.0 for s in Sign}

    # ── 舒适度计算 ────────────────────────────────────────

    def compute_sign_comfort(self) -> dict[Sign, float]:
        """计算每个星座的舒适度 (-100 ~ +100)。

        庙旺行星多 = 舒适（角色是'天赋'）
        失势落陷行星多 = 不适（角色是'课题'）
        没有行星 = 0（中性）
        """
        comfort: dict[Sign, float] = {s: 0.0 for s in Sign}

        for planet, sign in self._planet_signs.items():
            dignity = self._planet_dignities.get(planet, "peregrine")
            score = _DIGNITY_COMFORT.get(dignity, 0.0)
            # 传统行星权重更高
            if planet in (Planet.SUN, Planet.MOON):
                score *= 1.5
            comfort[sign] += score

        # 钳制到 -100 ~ +100
        return {s: round(clamp(v, -100.0, 100.0), 1) for s, v in comfort.items()}

    # ── 角色标签 ──────────────────────────────────────────

    @staticmethod
    def _determine_role_tag(presence: float, comfort: float) -> str:
        """根据存在感和舒适度确定角色标签"""
        if presence >= 50:
            if comfort >= 10:
                return "天赋角色"
            elif comfort <= -10:
                return "课题角色"
            return "核心角色"
        elif presence >= 20:
            if comfort >= 10:
                return "辅助角色"
            elif comfort <= -10:
                return "挑战角色"
            return "活跃角色"
        else:
            return "背景角色"

    # ── 故事线 ────────────────────────────────────────────

    def _build_storylines(self, sign: Sign) -> list[str]:
        """构建该星座在此人星盘中的飞星故事线。

        检查：命主星是否落此星座？是否有宫主星飞入？
        """
        lines: list[str] = []

        # 命主星故事线
        if self._chart_ruler and self._planet_signs.get(self._chart_ruler) == sign:
            ruler_house = self._planet_houses.get(self._chart_ruler, 0)
            ruler_label = _PLANET_LABELS_CN.get(self._chart_ruler, "命主星")
            lines.append(f"命主星{ruler_label}落在这里——你的人生起点和核心身份通过{sign}的方式展开")

        # 宫主星飞入
        for house_num in range(1, 13):
            cusp_sign = self._house_cusp_signs.get(house_num)
            if cusp_sign is None:
                continue
            ruler = CharacterEngine._get_sign_ruler(cusp_sign)
            if ruler in self._planet_signs and self._planet_signs[ruler] == sign:
                ruler_label = _PLANET_LABELS_CN.get(ruler, "宫主星")
                house_label = _HOUSE_TITLES_CN.get(house_num, f"第{house_num}宫")
                lines.append(f"{house_label}的宫主星{ruler_label}飞入这里——{house_label}的故事线由{sign}来演绎")

        return lines

    # ── 领域关联 ──────────────────────────────────────────

    @staticmethod
    def _get_linked_domains(sign: Sign, house_cusps: list[int]) -> list[str]:
        """获取该星座关联的生命领域"""
        domains: set[str] = set()

        # 宫头映射
        for h in house_cusps:
            domain = _HOUSE_TO_DOMAIN.get(h)
            if domain:
                domains.add(domain)

        # 从角色原型补充
        persona = SIGN_PERSONAS.get(sign)
        if persona:
            for d in persona.expertise_domains:
                domains.add(d)

        return sorted(domains)

    # ── 个性化开场白 ──────────────────────────────────────

    def _build_greeting(self, profile: CharacterProfile) -> str:
        """生成个性化开场白"""
        persona = profile.persona
        parts: list[str] = []

        # 角色自我介绍
        parts.append(f"我是你的{persona.name}角色——{persona.archetype}。")

        # 行星线索
        if profile.planets_here:
            planet_list = "、".join(profile.planets_here)
            parts.append(f"你的{planet_list}都在我这里。")

        # 角色标签
        if profile.role_tag == "天赋角色":
            parts.append("在这个维度上，你有天然的优势——就像鱼在水里。")
        elif profile.role_tag == "课题角色":
            parts.append("说实话，这个维度不是你的舒适区——但正是因为它难，它才值得聊。")
        elif profile.role_tag == "核心角色":
            parts.append("这是你星盘里最重要的一条线——你的人生很多故事都从这里开始。")

        # 上升
        if profile.is_ascendant:
            parts.append("而且我是你的上升星座——你出门面对世界时戴的面具，就是我的样子。")

        return "".join(parts)

    # ── 主入口 ────────────────────────────────────────────

    def get_character_profile(self, sign: Sign) -> CharacterProfile:
        """生成一个角色的完整个性化画像"""
        persona = get_persona(sign)
        presence = self.compute_sign_presence()
        comfort = self.compute_sign_comfort()

        presence_score = presence.get(sign, 0.0)
        comfort_score = comfort.get(sign, 0.0)
        role_tag = self._determine_role_tag(presence_score, comfort_score)

        # 收集落此星座的行星
        planets_here: list[str] = []
        planets_dignity: dict[str, str] = {}
        for planet, p_sign in self._planet_signs.items():
            if p_sign == sign:
                label = _PLANET_LABELS_CN.get(planet, planet.value)
                planets_here.append(label)
                planets_dignity[label] = self._planet_dignities.get(planet, "peregrine")

        # 收集宫头
        house_cusps_here: list[int] = [
            h for h, s in self._house_cusp_signs.items() if s == sign
        ]

        # 故事线
        storylines = self._build_storylines(sign)

        # 领域
        linked_domains = self._get_linked_domains(sign, house_cusps_here)

        is_asc = self._asc_sign == sign
        is_mc = self._mc_sign == sign

        profile = CharacterProfile(
            sign=sign,
            persona=persona,
            presence_score=presence_score,
            comfort_score=comfort_score,
            role_tag=role_tag,
            planets_here=planets_here,
            planets_dignity=planets_dignity,
            house_cusps_here=sorted(house_cusps_here),
            is_ascendant=is_asc,
            is_midheaven=is_mc,
            storylines=storylines,
            linked_domains=linked_domains,
            personalized_greeting="",  # 先占位
        )
        profile.personalized_greeting = self._build_greeting(profile)
        return profile

    def get_all_profiles(self) -> dict[Sign, CharacterProfile]:
        """生成全部12个角色画像"""
        return {sign: self.get_character_profile(sign) for sign in Sign}

    def get_sorted_profiles(self) -> list[CharacterProfile]:
        """按存在感降序排列的角色画像"""
        profiles = list(self.get_all_profiles().values())
        profiles.sort(key=lambda p: p.presence_score, reverse=True)
        return profiles

    def get_core_characters(self, threshold: float = 50.0) -> list[CharacterProfile]:
        """获取核心角色（存在感高于阈值）"""
        return [p for p in self.get_sorted_profiles() if p.presence_score >= threshold]


# ═══════════════════════════════════════════════════════════════
# 辅助映射表
# ═══════════════════════════════════════════════════════════════

_PLANET_LABELS_CN: dict[Planet, str] = {
    Planet.SUN: "太阳",
    Planet.MOON: "月亮",
    Planet.MERCURY: "水星",
    Planet.VENUS: "金星",
    Planet.MARS: "火星",
    Planet.JUPITER: "木星",
    Planet.SATURN: "土星",
    Planet.URANUS: "天王星",
    Planet.NEPTUNE: "海王星",
    Planet.PLUTO: "冥王星",
    Planet.NORTH_NODE: "北交点",
    Planet.SOUTH_NODE: "南交点",
}

_HOUSE_TITLES_CN: dict[int, str] = {
    1: "自我宫", 2: "财帛宫", 3: "兄弟宫", 4: "田宅宫",
    5: "子女宫", 6: "奴仆宫", 7: "夫妻宫", 8: "疾厄宫",
    9: "迁移宫", 10: "官禄宫", 11: "福德宫", 12: "玄秘宫",
}

_HOUSE_TO_DOMAIN: dict[int, str] = {
    1: "personal", 2: "finance", 3: "education",
    4: "family", 5: "romance", 6: "work_skill",
    7: "marriage", 8: "finance", 9: "education",
    10: "career", 11: "partnership", 12: "health",
}
