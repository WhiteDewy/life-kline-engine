"""
daily_engine.py — 每日唤醒引擎

根据时间律动计算12星座角色的每日激活度。
决定"今天哪些角色登场"以及"它们想对用户说什么"。

时间律动来源：
- 法达 (Firdaria): 主运星 + 子运星所在星座
- 行运 (Transits): 当前行星位置触发本命行星
- 月亮周期: 当前月亮星座
- 太阳季节: 当前太阳星座
- 月返: 月返盘强调的星座
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from ..constants import Planet, Sign, ASPECT_CONFIG, AspectType
from ..ephemeris import EphemerisEngine
from ..firdaria import FirdariaPeriod
from ..characters.character_engine import CharacterEngine, CharacterProfile
from ..characters.sign_personas import SIGN_PERSONAS


# ═══════════════════════════════════════════════════════════════
# 激活权重配置
# ═══════════════════════════════════════════════════════════════

_ACTIVATION_WEIGHTS = {
    "firdaria_major": 30.0,     # 法达主运星所在星座
    "firdaria_sub": 15.0,       # 法达子运星所在星座
    "moon_current": 25.0,       # 当前月亮星座
    "sun_current": 20.0,        # 当前太阳星座
    "transit_conjunction": 12.0,  # 行运合相
    "transit_opposition": 10.0,   # 行运对冲
    "transit_square": 8.0,        # 行运刑相
    "transit_trine": 6.0,         # 行运拱相
    "transit_sextile": 4.0,       # 行运六合
    "lunar_return_asc": 10.0,     # 月返上升星座
    "lunar_return_moon": 8.0,     # 月返月亮星座
    "natal_presence_bonus": 5.0,  # 本命存在感加成
}

# 行运检测容许度
_TRANSIT_ORBS = {
    AspectType.CONJUNCTION: 3.0,
    AspectType.OPPOSITION: 3.0,
    AspectType.SQUARE: 2.5,
    AspectType.TRINE: 3.0,
    AspectType.SEXTILE: 2.0,
}

# 参与行运计算的行星
_TRANSITING_PLANETS = [
    Planet.SUN, Planet.MOON, Planet.MERCURY, Planet.VENUS, Planet.MARS,
    Planet.JUPITER, Planet.SATURN, Planet.URANUS, Planet.NEPTUNE, Planet.PLUTO,
]


# ═══════════════════════════════════════════════════════════════
# 数据类
# ═══════════════════════════════════════════════════════════════

@dataclass
class FeaturedCharacter:
    """今日登场角色"""
    sign: str                # Sign.value
    name: str                # 中文名
    archetype: str           # 角色原型
    activation_score: float  # 激活度
    reason: str              # 为什么今天被激活
    daily_message: str       # 今天想对用户说的话
    suggested_topic: str     # 建议聊什么
    visual_color: str        # 视觉色

    def to_dict(self) -> dict[str, Any]:
        return {
            "sign": self.sign,
            "name": self.name,
            "archetype": self.archetype,
            "activation_score": round(self.activation_score, 1),
            "reason": self.reason,
            "daily_message": self.daily_message,
            "suggested_topic": self.suggested_topic,
            "visual_color": self.visual_color,
        }


@dataclass
class DailyActivation:
    """每日激活结果"""
    date: str                                    # ISO 日期
    activation_scores: dict[str, float]           # 12 星座激活度
    featured_characters: list[FeaturedCharacter]  # 前 3 名
    lunar_note: str                              # 月亮提示
    firdaria_note: str                           # 法达提示
    daily_theme: str                             # 今日主题

    def to_dict(self) -> dict[str, Any]:
        return {
            "date": self.date,
            "activation_scores": {
                k: round(v, 1) for k, v in self.activation_scores.items()
            },
            "featured_characters": [f.to_dict() for f in self.featured_characters],
            "lunar_note": self.lunar_note,
            "firdaria_note": self.firdaria_note,
            "daily_theme": self.daily_theme,
        }


# ═══════════════════════════════════════════════════════════════
# 每日唤醒引擎
# ═══════════════════════════════════════════════════════════════

class DailyAwakeningEngine:
    """计算每日12角色激活度的引擎。"""

    def __init__(
        self,
        chart: Any,
        character_engine: CharacterEngine | None = None,
        firdaria_period: FirdariaPeriod | None = None,
        current_chart: Any = None,
    ):
        """
        Args:
            chart: 本命盘 ChartData
            character_engine: 角色引擎（可选，自动创建）
            firdaria_period: 当前法达周期（可选，需外部传入）
            current_chart: 当天行运盘（可选，自动计算）
        """
        self.chart = chart
        self.character_engine = character_engine or CharacterEngine(chart)
        self.firdaria_period = firdaria_period
        self._current_chart = current_chart
        self._ephemeris = EphemerisEngine()
        self._presence_cache: dict[Sign, float] | None = None

    @property
    def presence_scores(self) -> dict[Sign, float]:
        if self._presence_cache is None:
            self._presence_cache = self.character_engine.compute_sign_presence()
        return self._presence_cache

    def _ensure_current_chart(self) -> Any:
        """确保有当前行运盘数据"""
        if self._current_chart is not None:
            return self._current_chart

        now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
        location = getattr(self.chart, "location", None)
        lat = location.get("lat", 0.0) if location else 0.0
        lon = location.get("lon", 0.0) if location else 0.0

        self._current_chart = self._ephemeris.calculate_chart(now_utc, lat, lon)
        return self._current_chart

    def _get_planet_sign(self, chart: Any, planet: Planet) -> Sign | None:
        """从星盘获取行星所在星座"""
        planets = getattr(chart, "planets", {})
        info = planets.get(planet)
        if info and hasattr(info, "sign"):
            return info.sign
        return None

    def _get_house_sign(self, chart: Any, house_num: int) -> Sign | None:
        """从星盘获取宫头星座"""
        houses = getattr(chart, "houses", [])
        if len(houses) >= house_num:
            return houses[house_num - 1][0]
        return None

    # ── 主入口 ────────────────────────────────────────────

    def compute_daily_activation(
        self,
        date: datetime | None = None,
    ) -> DailyActivation:
        """计算当日12角色激活度。

        Args:
            date: 目标日期，默认今天

        Returns:
            DailyActivation 包含全部激活数据
        """
        if date is None:
            date = datetime.now(timezone.utc).replace(tzinfo=None)

        current = self._ensure_current_chart()

        # 初始化原始分数
        raw: dict[Sign, float] = {s: 0.0 for s in Sign}

        # 1. 法达激活
        firdaria_note = ""
        if self.firdaria_period:
            major_sign = self._get_planet_sign(self.chart, self.firdaria_period.major_lord)
            if major_sign:
                raw[major_sign] += _ACTIVATION_WEIGHTS["firdaria_major"]
                firdaria_note = f"当前法达主运星在{major_sign.value}，人生主旋律经由这个星座展开"

            if self.firdaria_period.sub_lord:
                sub_sign = self._get_planet_sign(self.chart, self.firdaria_period.sub_lord)
                if sub_sign:
                    raw[sub_sign] += _ACTIVATION_WEIGHTS["firdaria_sub"]

        # 2. 当前月亮星座
        moon_sign = self._get_planet_sign(current, Planet.MOON)
        lunar_note = ""
        if moon_sign:
            raw[moon_sign] += _ACTIVATION_WEIGHTS["moon_current"]
            persona = SIGN_PERSONAS.get(moon_sign)
            lunar_note = f"今天月亮在{persona.name if persona else moon_sign.value}——情绪和注意力自然往这个方向流"

        # 3. 当前太阳星座
        sun_sign = self._get_planet_sign(current, Planet.SUN)
        if sun_sign:
            raw[sun_sign] += _ACTIVATION_WEIGHTS["sun_current"]

        # 4. 行运激活
        self._add_transit_activations(raw, current)

        # 5. 本命存在感加成
        for sign in Sign:
            presence = self.presence_scores.get(sign, 0.0)
            if presence >= 50:
                raw[sign] += _ACTIVATION_WEIGHTS["natal_presence_bonus"]

        # 归一化到 0-100
        max_raw = max(raw.values()) if raw else 1.0
        if max_raw > 0:
            scores = {s: round(v / max_raw * 100, 1) for s, v in raw.items()}
        else:
            scores = {s: 0.0 for s in Sign}

        # 选出前 3 名
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        featured = self._build_featured(ranked[:3], scores)

        # 每日主题
        daily_theme = self._synthesize_theme(featured, moon_sign)

        return DailyActivation(
            date=date.date().isoformat(),
            activation_scores={s.value: v for s, v in scores.items()},
            featured_characters=featured,
            lunar_note=lunar_note,
            firdaria_note=firdaria_note,
            daily_theme=daily_theme,
        )

    # ── 行运激活 ──────────────────────────────────────────

    def _add_transit_activations(self, raw: dict[Sign, float], current: Any) -> None:
        """检测行运行星与本命行星的相位，累加激活度"""
        natal_planets = getattr(self.chart, "planets", {})
        current_planets = getattr(current, "planets", {})

        for t_planet in _TRANSITING_PLANETS:
            t_info = current_planets.get(t_planet)
            if not t_info:
                continue
            t_lon = self._absolute_longitude(t_info)

            for n_planet, n_info in natal_planets.items():
                n_lon = self._absolute_longitude(n_info)
                diff = abs(t_lon - n_lon) % 360
                diff = min(diff, 360 - diff)

                for aspect_type, max_orb in _TRANSIT_ORBS.items():
                    config = ASPECT_CONFIG.get(aspect_type, {})
                    target_angle = config.get("angle", 0.0)
                    orb = abs(diff - target_angle)
                    if orb > max_orb:
                        continue

                    # 找到匹配的相位，累加到行运行星所在星座
                    t_sign = getattr(t_info, "sign", None)
                    if t_sign:
                        weight_key = f"transit_{aspect_type.value.lower()}"
                        weight = _ACTIVATION_WEIGHTS.get(weight_key, 4.0)
                        raw[t_sign] += weight
                    break  # 只取最佳相位

    @staticmethod
    def _absolute_longitude(info: Any) -> float:
        """获取行星的绝对黄经"""
        if hasattr(info, "longitude") and info.longitude:
            return float(info.longitude)
        if hasattr(info, "sign") and hasattr(info, "degree"):
            sign_index = list(Sign).index(info.sign) if isinstance(info.sign, Sign) else 0
            return sign_index * 30.0 + float(info.degree or 0.0)
        return 0.0

    # ── 登场角色 ──────────────────────────────────────────

    def _build_featured(
        self,
        top3: list[tuple[Sign, float]],
        all_scores: dict[Sign, float],
    ) -> list[FeaturedCharacter]:
        """构建前3名登场角色"""
        featured: list[FeaturedCharacter] = []
        for sign, score in top3:
            persona = SIGN_PERSONAS.get(sign)
            if persona is None:
                continue

            reason = self._activation_reason(sign, all_scores)
            daily_message = self._generate_daily_message(sign, persona)
            suggested_topic = persona.expertise_domains[0] if persona.expertise_domains else "personal"

            featured.append(FeaturedCharacter(
                sign=sign.value,
                name=persona.name,
                archetype=persona.archetype,
                activation_score=score,
                reason=reason,
                daily_message=daily_message,
                suggested_topic=suggested_topic,
                visual_color=persona.visual_color,
            ))
        return featured

    def _activation_reason(self, sign: Sign, scores: dict[Sign, float]) -> str:
        """解释为什么这个角色今天被激活"""
        score = scores.get(sign, 0.0)
        if score >= 80:
            return "今天这个角色全面激活——时间律动和你的本命配置都在往这个方向推"
        elif score >= 60:
            return "今天这个角色比较活跃，有几个天体正在触发这个维度的议题"
        elif score >= 40:
            return "今天这个角色在背景中存在——不是主角，但有话要说"
        else:
            return "今天这个角色比较安静，但如果你主动找它聊聊，它会在"

    def _generate_daily_message(self, sign: Sign, persona) -> str:
        """生成登场角色的每日一句话"""
        presence = self.presence_scores.get(sign, 0.0)

        if presence >= 70:
            return f"今天我的声音会比较大——你的星盘里我本来就是一个重要角色，今天的节奏又在推我出来。有什么想聊的？"

        if self.firdaria_period:
            major_sign = self._get_planet_sign(self.chart, self.firdaria_period.major_lord)
            if major_sign == sign:
                return f"你当前的人生阶段正好经过我这里——这几年你经历的事情，很多都是我在背后推动的。今天尤其明显。"

        current = self._ensure_current_chart()
        moon_sign = self._get_planet_sign(current, Planet.MOON)
        if moon_sign == sign:
            return f"今天的月亮在我这里——你的情绪和注意力会自然往这个方向流。是个适合感受和整理的日子。"

        return f"嘿，今天想聊聊{persona.expertise_domains[0] if persona.expertise_domains else '你'}的事吗？我一直在。"

    # ── 每日主题 ──────────────────────────────────────────

    @staticmethod
    def _synthesize_theme(featured: list[FeaturedCharacter], moon_sign: Sign | None) -> str:
        """合成每日主题文本"""
        if not featured:
            return "今天所有角色都比较安静——适合回顾和整理，而不是主动冲刺。"

        top = featured[0]
        persona = SIGN_PERSONAS.get(Sign(top.sign)) if top.sign else None

        theme_prefixes = {
            "火": "今天是行动力主导的一天——",
            "土": "今天是务实和积累主导的一天——",
            "风": "今天是思考和连接主导的一天——",
            "水": "今天是感受和内省主导的一天——",
        }

        element = persona.element if persona else "火"
        prefix = theme_prefixes.get(element, "今天是特别的一天——")

        names = "、".join(f.name for f in featured[:2])
        suffix = f"{names}是你今天最值得倾听的声音。"

        return prefix + suffix
