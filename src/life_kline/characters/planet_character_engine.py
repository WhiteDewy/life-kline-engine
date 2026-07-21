"""
planet_character_engine.py — 行星角色个性化引擎

从用户的星盘数据计算10颗行星的个性化角色状态：
- core_strength: 该行星在此人生命中的综合表达强度 (0-100)
- sign_flavor: 该行星落入星座的风格修饰
- house_context: 该行星落入宫位的领域语境
- role_tag: 天赋维度 / 人生课题 / 核心表达 / 背景影响
- personalized_greeting: 三层融合的个性化开场白

对标万象有灵的十神人格维度模型：
太阳 = 主人格（主角，始终在线）
月亮/水星/金星/火星/木星/土星/天王星/海王星/冥王星 = 次人格
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..constants import (
    ANGULAR_HOUSES,
    SUCCEDENT_HOUSES,
    CADENT_HOUSES,
    DOMICILE_SIGNS,
    DETRIMENT_SIGNS,
    EXALTATION_SIGNS,
    FALL_SIGNS,
    JOY_HOUSES,
    Planet,
    Sign,
    SIGN_ELEMENT,
    SIGN_MODALITY,
    get_sign_element,
    get_sign_modality,
    get_house_type,
    clamp,
)
from .sign_personas import SIGN_PERSONAS, get_persona
from .planet_personas import PlanetPersona, PLANET_PERSONAS, get_planet_persona


# ── 尊贵评分映射 ─────────────────────────────────────────

_DIGNITY_SCORE: dict[str, float] = {
    "domicile": 1.0,
    "exaltation": 0.8,
    "peregrine": 0.0,
    "detriment": -0.7,
    "fall": -0.9,
}

# 宫位类型强度系数
_HOUSE_TYPE_STRENGTH: dict[str, float] = {
    "angular": 20.0,
    "succedent": 10.0,
    "cadent": 5.0,
}


# ═══════════════════════════════════════════════════════════════
# 角色画像数据类
# ═══════════════════════════════════════════════════════════════

@dataclass
class PlanetCharacterProfile:
    """一颗行星的完整个性化角色画像——与具体用户星盘绑定"""
    planet: Planet
    persona: PlanetPersona                         # 固定原型
    core_strength: float                           # 综合强度 0-100
    sign: Sign                                     # 落入的星座
    sign_label: str                                # 星座中文名
    house: int                                     # 落入的宫位
    house_label: str                               # 宫位中文标签
    dignity_code: str                              # domicile/exaltation/peregrine/detriment/fall
    dignity_label: str                             # 尊贵状态中文标签
    role_tag: str                                  # 天赋维度 / 人生课题 / 核心表达 / 背景影响
    sign_flavor: dict[str, Any] = field(default_factory=dict)   # 星座风格层
    house_context: dict[str, Any] = field(default_factory=dict) # 宫位语境层
    is_chart_ruler: bool = False                   # 是否为命主星
    personalized_greeting: str = ""                # 个性化开场白
    linked_domains: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "planet": self.planet.value,
            "persona": self.persona.to_dict(),
            "core_strength": round(self.core_strength, 1),
            "sign": self.sign.value,
            "sign_label": self.sign_label,
            "house": self.house,
            "house_label": self.house_label,
            "dignity_code": self.dignity_code,
            "dignity_label": self.dignity_label,
            "role_tag": self.role_tag,
            "sign_flavor": self.sign_flavor,
            "house_context": self.house_context,
            "is_chart_ruler": self.is_chart_ruler,
            "personalized_greeting": self.personalized_greeting,
            "linked_domains": self.linked_domains,
        }


# ═══════════════════════════════════════════════════════════════
# 行星角色引擎
# ═══════════════════════════════════════════════════════════════

class PlanetCharacterEngine:
    """从星盘数据生成10行星个性化角色画像的引擎。

    所有计算完全由规则驱动——无硬编码、无 LLM。

    对标万象有灵十神模型：
    - 太阳 = 主人格（主角）
    - 月亮/水星/金星/火星/木星/土星/天王星/海王星/冥王星 = 次人格
    """

    # 10 颗行星（传统 7 + 外行星 3）
    PERSONAL_PLANETS = [
        Planet.SUN, Planet.MOON, Planet.MERCURY, Planet.VENUS,
        Planet.MARS, Planet.JUPITER, Planet.SATURN,
        Planet.URANUS, Planet.NEPTUNE, Planet.PLUTO,
    ]

    def __init__(self, chart: Any):
        self.chart = chart
        self._planet_signs: dict[Planet, Sign] = {}
        self._planet_houses: dict[Planet, int] = {}
        self._planet_dignities: dict[Planet, str] = {}
        self._asc_sign: Sign | None = None
        self._chart_ruler: Planet | None = None
        self._parse_chart()

    # ── 解析星盘 ──────────────────────────────────────────

    def _parse_chart(self) -> None:
        planets = getattr(self.chart, "planets", {})
        for planet, info in planets.items():
            if hasattr(info, "sign"):
                self._planet_signs[planet] = info.sign
            if hasattr(info, "house"):
                self._planet_houses[planet] = info.house

        houses = getattr(self.chart, "houses", [])
        if houses:
            for i, (sign, _) in enumerate(houses[:12]):
                if i == 0:
                    self._asc_sign = sign

        if self._asc_sign:
            self._chart_ruler = self._get_sign_ruler(self._asc_sign)

        for planet in self.PERSONAL_PLANETS:
            sign = self._planet_signs.get(planet)
            if sign:
                self._planet_dignities[planet] = self._compute_dignity_code(planet, sign)
            else:
                self._planet_dignities[planet] = "peregrine"

    @staticmethod
    def _get_sign_ruler(sign: Sign) -> Planet:
        for planet, signs in DOMICILE_SIGNS.items():
            if sign in signs and planet in (
                Planet.SUN, Planet.MOON, Planet.MERCURY, Planet.VENUS,
                Planet.MARS, Planet.JUPITER, Planet.SATURN,
            ):
                return planet
        return Planet.SUN

    @staticmethod
    def _compute_dignity_code(planet: Planet, sign: Sign) -> str:
        if sign in DOMICILE_SIGNS.get(planet, []):
            return "domicile"
        if sign in EXALTATION_SIGNS.get(planet, []):
            return "exaltation"
        if sign in DETRIMENT_SIGNS.get(planet, []):
            return "detriment"
        if sign in FALL_SIGNS.get(planet, []):
            return "fall"
        return "peregrine"

    # ── 尊贵中文标签 ──────────────────────────────────────

    DIGNITY_LABELS: dict[str, str] = {
        "domicile": "入庙",
        "exaltation": "旺相",
        "peregrine": "平",
        "detriment": "失势",
        "fall": "落陷",
    }

    # ── 核心强度计算 ──────────────────────────────────────

    def compute_core_strength(self, planet: Planet) -> float:
        """计算单颗行星的综合强度 (0-100)。

        算法：
        - 尊贵加成 (40%): 入庙+40, 旺相+30, 平+10, 失势-20, 落陷-30
        - 宫位力量 (30%): 角宫+20, 续宫+10, 果宫+5
        - 命主星 (15%): 是命主+15
        - 发光体加成 (15%): 太阳/月亮+15
        """
        score = 0.0

        # 1. 尊贵状态 (40%)
        dignity = self._planet_dignities.get(planet, "peregrine")
        dignity_map = {"domicile": 40, "exaltation": 30, "peregrine": 10, "detriment": -20, "fall": -30}
        score += dignity_map.get(dignity, 0) * 0.4

        # 2. 宫位类型 (30%)
        house = self._planet_houses.get(planet)
        if house in ANGULAR_HOUSES:
            score += 20 * 0.3
        elif house in SUCCEDENT_HOUSES:
            score += 10 * 0.3
        elif house in CADENT_HOUSES:
            score += 5 * 0.3

        # 3. 命主星 (15%)
        if planet == self._chart_ruler:
            score += 15 * 0.15

        # 4. 发光体加成 (15%)
        if planet in (Planet.SUN, Planet.MOON):
            score += 15 * 0.15

        # 5. 喜乐宫加分 (宫位系统内的)
        joy_house = JOY_HOUSES.get(planet)
        if joy_house and house == joy_house:
            score += 8

        return clamp(score + 30, 0, 100)  # 偏移 +30 使大部分行星在 20-80 区间

    def compute_all_strengths(self) -> dict[Planet, float]:
        """计算全部10颗行星的核心强度"""
        return {p: self.compute_core_strength(p) for p in self.PERSONAL_PLANETS}

    # ── 星座风格层 ────────────────────────────────────────

    def get_sign_flavor(self, planet: Planet) -> dict[str, Any]:
        """获取行星落入星座的风格修饰层。

        从 SIGN_PERSONAS 中提取该星座的 element, modality, voice_tone
        等属性，作为行星表达的「风格滤镜」。
        """
        sign = self._planet_signs.get(planet)
        if sign is None:
            return {}

        persona = get_persona(sign)
        return {
            "sign": sign.value,
            "sign_name": persona.name,
            "element": persona.element,
            "modality": persona.modality,
            "polarity": persona.polarity,
            "voice_tone": persona.voice_tone,
            "personality_snippet": persona.personality[:120] if persona.personality else "",
            "visual_color": persona.visual_color,
            "keywords": persona.keywords[:5],
        }

    # ── 宫位语境层 ────────────────────────────────────────

    @staticmethod
    def get_house_context(house_num: int) -> dict[str, Any]:
        """获取宫位的领域语境。"""
        from ..interpretation.house_rules import get_house_profile

        hp = get_house_profile(house_num)
        return {
            "house": house_num,
            "title": hp.title,
            "domain": hp.domain_key,
            "topic": hp.keywords[0] if hp.keywords else "",
        }

    # ── 领域关联 ──────────────────────────────────────────

    _HOUSE_DOMAIN_MAP: dict[int, str] = {
        1: "personal", 2: "finance", 3: "education",
        4: "family", 5: "romance", 6: "work_skill",
        7: "marriage", 8: "finance", 9: "education",
        10: "career", 11: "partnership", 12: "health",
    }

    def _get_linked_domains(self, planet: Planet) -> list[str]:
        """根据行星落入宫位 + 行星天然领域，生成关联领域列表"""
        domains: list[str] = []

        house = self._planet_houses.get(planet)
        if house and house in self._HOUSE_DOMAIN_MAP:
            domain = self._HOUSE_DOMAIN_MAP[house]
            if domain not in domains:
                domains.append(domain)

        persona = get_planet_persona(planet)
        for d in persona.expertise_domains:
            if d not in domains:
                domains.append(d)

        return domains[:4]

    # ── 角色标签 ──────────────────────────────────────────

    def _determine_role_tag(self, planet: Planet, strength: float) -> str:
        """根据强度 + 尊贵状态确定角色标签"""
        dignity = self._planet_dignities.get(planet, "peregrine")

        if strength >= 60 and dignity in ("domicile", "exaltation"):
            return "天赋维度"
        if strength >= 40 and dignity in ("detriment", "fall"):
            return "人生课题"
        if strength >= 50:
            return "核心表达"
        if strength >= 25:
            return "活跃影响"
        return "背景影响"

    # ── 个性化开场白 ──────────────────────────────────────

    def _build_greeting(self, profile: PlanetCharacterProfile) -> str:
        """三层融合开场白：行星本性 + 星座风格 + 宫位语境"""
        p = profile.persona
        sign = self._planet_signs.get(profile.planet)
        house = self._planet_houses.get(profile.planet)
        dignity = self._planet_dignities.get(profile.planet, "peregrine")

        parts: list[str] = []

        # 第一层：行星自介
        parts.append(f"我是你的{p.name_zh}——{p.archetype_zh}。{p.essence}")

        # 第二层：星座风格
        if sign and sign in SIGN_PERSONAS:
            sp = SIGN_PERSONAS[sign]
            element_word = {"火": "热烈地", "土": "踏实地", "风": "灵活地", "水": "敏感地"}.get(sp.element, "")
            parts.append(f"我在{sp.name}，所以我的表达方式是{element_word}、{sp.modality}的——{sp.voice_tone[:60]}。")

        # 第三层：宫位语境
        if house:
            hc = self.get_house_context(house)
            title = hc.get("title", f"第{house}宫")
            parts.append(f"我在你的第{house}宫「{title}」运作——这是我在你生命中主要发挥影响的领域。")

        # 尊贵注脚
        dignity_notes = {
            "domicile": "在这里我很自在——这是我最舒服的位置，你可以放心依靠我。",
            "exaltation": "这个位置让我发挥得特别好——你在这方面有超出常人的天赋。",
            "peregrine": "在这里我没有特别的加持——但也没有阻力。一切看你后天怎么用我。",
            "detriment": "老实说，这个位置让我不太舒服。但这不代表你做不到——只是需要更努力、更有意识。",
            "fall": "这是我最难发挥的位置。但好消息是——你最难的功课，往往也是你成长最多的地方。",
        }
        note = dignity_notes.get(dignity, "")
        if note:
            parts.append(note)

        return "".join(parts)

    # ── 公共方法 ──────────────────────────────────────────

    def get_planet_profile(self, planet: Planet) -> PlanetCharacterProfile | None:
        """获取单颗行星的完整个性化角色画像"""
        if planet not in self.PERSONAL_PLANETS:
            return None

        persona = get_planet_persona(planet)
        sign = self._planet_signs.get(planet)
        house = self._planet_houses.get(planet) or 1
        dignity = self._planet_dignities.get(planet, "peregrine")
        strength = self.compute_core_strength(planet)

        profile = PlanetCharacterProfile(
            planet=planet,
            persona=persona,
            core_strength=strength,
            sign=sign or Sign.ARIES,
            sign_label=SIGN_PERSONAS[sign].name if sign else "未知",
            house=house,
            house_label=self.get_house_context(house).get("title", f"第{house}宫"),
            dignity_code=dignity,
            dignity_label=self.DIGNITY_LABELS.get(dignity, "平"),
            role_tag=self._determine_role_tag(planet, strength),
            sign_flavor=self.get_sign_flavor(planet),
            house_context=self.get_house_context(house),
            is_chart_ruler=(planet == self._chart_ruler),
            linked_domains=self._get_linked_domains(planet),
        )
        profile.personalized_greeting = self._build_greeting(profile)
        return profile

    def get_all_profiles(self) -> dict[Planet, PlanetCharacterProfile]:
        """获取 10 颗行星的完整画像"""
        result: dict[Planet, PlanetCharacterProfile] = {}
        for p in self.PERSONAL_PLANETS:
            profile = self.get_planet_profile(p)
            if profile:
                result[p] = profile
        return result

    def get_main_character(self) -> PlanetCharacterProfile:
        """获取主人格（太阳）"""
        return self.get_planet_profile(Planet.SUN)  # type: ignore

    def get_sub_personalities(self) -> list[PlanetCharacterProfile]:
        """获取 9 颗次人格行星，按强度降序"""
        profiles = [
            self.get_planet_profile(p)
            for p in self.PERSONAL_PLANETS
            if p != Planet.SUN
        ]
        valid = [p for p in profiles if p is not None]
        valid.sort(key=lambda p: p.core_strength, reverse=True)
        return valid

    def get_profiles_by_strength(self) -> list[PlanetCharacterProfile]:
        """所有 10 颗行星按强度降序"""
        profiles = [self.get_planet_profile(p) for p in self.PERSONAL_PLANETS]
        valid = [p for p in profiles if p is not None]
        valid.sort(key=lambda p: p.core_strength, reverse=True)
        return valid

    def get_core_planets(self, threshold: float = 50.0) -> list[PlanetCharacterProfile]:
        """强度 >= threshold 的核心行星"""
        return [p for p in self.get_profiles_by_strength() if p.core_strength >= threshold]
