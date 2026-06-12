"""
High-level report service for the Life K-Line product.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from itertools import combinations
from statistics import mean
from typing import Any, Dict, Iterable, Optional

from .constants import (
    ANGULAR_HOUSES,
    ASPECT_CONFIG,
    CADENT_HOUSES,
    DOMICILE_SIGNS,
    DETRIMENT_SIGNS,
    EXALTATION_SIGNS,
    FALL_SIGNS,
    JOY_HOUSES,
    SUCCEDENT_HOUSES,
    AspectType,
    Planet,
    Sign,
)
from .ephemeris import EphemerisEngine
from .firdaria import FirdariaPeriod, calculate_firdaria_periods


PLANET_LABELS: Dict[Planet, str] = {
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

SIGN_LABELS: Dict[Sign, str] = {
    Sign.ARIES: "白羊座",
    Sign.TAURUS: "金牛座",
    Sign.GEMINI: "双子座",
    Sign.CANCER: "巨蟹座",
    Sign.LEO: "狮子座",
    Sign.VIRGO: "处女座",
    Sign.LIBRA: "天秤座",
    Sign.SCORPIO: "天蝎座",
    Sign.SAGITTARIUS: "射手座",
    Sign.CAPRICORN: "摩羯座",
    Sign.AQUARIUS: "水瓶座",
    Sign.PISCES: "双鱼座",
}

SIGN_ELEMENT_LABELS: Dict[Sign, str] = {
    Sign.ARIES: "火",
    Sign.LEO: "火",
    Sign.SAGITTARIUS: "火",
    Sign.TAURUS: "土",
    Sign.VIRGO: "土",
    Sign.CAPRICORN: "土",
    Sign.GEMINI: "风",
    Sign.LIBRA: "风",
    Sign.AQUARIUS: "风",
    Sign.CANCER: "水",
    Sign.SCORPIO: "水",
    Sign.PISCES: "水",
}

SIGN_MODALITY_LABELS: Dict[Sign, str] = {
    Sign.ARIES: "本位",
    Sign.CANCER: "本位",
    Sign.LIBRA: "本位",
    Sign.CAPRICORN: "本位",
    Sign.TAURUS: "固定",
    Sign.LEO: "固定",
    Sign.SCORPIO: "固定",
    Sign.AQUARIUS: "固定",
    Sign.GEMINI: "变动",
    Sign.VIRGO: "变动",
    Sign.SAGITTARIUS: "变动",
    Sign.PISCES: "变动",
}

SIGN_RULERS: Dict[Sign, Planet] = {
    Sign.ARIES: Planet.MARS,
    Sign.TAURUS: Planet.VENUS,
    Sign.GEMINI: Planet.MERCURY,
    Sign.CANCER: Planet.MOON,
    Sign.LEO: Planet.SUN,
    Sign.VIRGO: Planet.MERCURY,
    Sign.LIBRA: Planet.VENUS,
    Sign.SCORPIO: Planet.MARS,
    Sign.SAGITTARIUS: Planet.JUPITER,
    Sign.CAPRICORN: Planet.SATURN,
    Sign.AQUARIUS: Planet.SATURN,
    Sign.PISCES: Planet.JUPITER,
}

DIGNITY_LABELS = {
    "domicile": "入庙",
    "exaltation": "旺相",
    "detriment": "失势",
    "fall": "落陷",
    "peregrine": "平常",
}

PLANET_ARCHETYPES: Dict[Planet, Dict[str, str]] = {
    Planet.SUN: {
        "gift": "自我定义与主导能力",
        "shadow": "过度自尊或只按意志推进",
        "strategy": "把注意力放在长期目标、名望与作品沉淀上。",
    },
    Planet.MOON: {
        "gift": "情绪感知、照料与安全需求的把握",
        "shadow": "情绪卷入、节奏被环境牵动",
        "strategy": "先稳定作息与关系边界，再谈效率和决策。",
    },
    Planet.MERCURY: {
        "gift": "信息整合、表达、交易与学习能力",
        "shadow": "犹疑、分心、过度比较",
        "strategy": "把复杂问题拆成流程，建立可复用的认知框架。",
    },
    Planet.VENUS: {
        "gift": "关系经营、审美、合作与资源协调",
        "shadow": "讨好、依赖外部认可、享乐分散",
        "strategy": "通过关系与价值交换打开局面，但不要牺牲底线。",
    },
    Planet.MARS: {
        "gift": "行动力、竞争性、突破与执行",
        "shadow": "急躁、对抗、提前消耗",
        "strategy": "把火力聚焦在关键战役，而不是到处起冲突。",
    },
    Planet.JUPITER: {
        "gift": "扩张、信念、机会识别与贵人运",
        "shadow": "过度乐观、承诺过量、理想化",
        "strategy": "扩张时保留边界与节奏，把好运落到制度上。",
    },
    Planet.SATURN: {
        "gift": "结构、耐力、长期主义与责任",
        "shadow": "压抑、迟滞、过度保守",
        "strategy": "用时间换确定性，先筑底盘再谈跃迁。",
    },
    Planet.NORTH_NODE: {
        "gift": "增长方向、未来牵引",
        "shadow": "急于跳向新阶段而失去根基",
        "strategy": "把陌生感当作成长入口，但别抛弃原有能力。",
    },
    Planet.SOUTH_NODE: {
        "gift": "熟练、旧天赋、天然顺手的惯性",
        "shadow": "停在舒适区、消耗旧模式",
        "strategy": "保留经验，但要主动更新做事逻辑。",
    },
}

HOUSE_TOPICS: Dict[int, Dict[str, Any]] = {
    1: {"title": "自我与身体", "keywords": ["自我定位", "身体状态", "个人意志"]},
    2: {"title": "收入与资源", "keywords": ["现金流", "价值感", "可支配资源"]},
    3: {"title": "学习与表达", "keywords": ["沟通", "技能", "短途连接"]},
    4: {"title": "家庭与根基", "keywords": ["原生家庭", "居所", "情绪根基"]},
    5: {"title": "创造与恋爱", "keywords": ["创作", "恋爱", "个人表达"]},
    6: {"title": "工作与健康", "keywords": ["执行", "习惯", "健康管理"]},
    7: {"title": "伴侣与合作", "keywords": ["伴侣", "合作", "契约关系"]},
    8: {"title": "风险与转化", "keywords": ["风险", "共享资源", "深层转变"]},
    9: {"title": "远方与意义", "keywords": ["高阶学习", "远行", "世界观"]},
    10: {"title": "事业与名望", "keywords": ["事业地位", "公众形象", "成就"]},
    11: {"title": "社群与愿景", "keywords": ["人脉", "社群", "长期愿景"]},
    12: {"title": "潜意识与退隐", "keywords": ["隐性压力", "疗愈", "收尾"]},
}

HOUSE_ADULT_MEANINGS: Dict[int, Dict[str, str]] = {
    1: {
        "adult": "个人姿态、身体存在感、出面方式",
        "power": "决定你是以什么样的姿态让他人记住你。",
    },
    2: {
        "adult": "现金流、资源控制、利益分配、可变现能力",
        "power": "决定你如何把资源、欲望和实际收益绑定成钱。",
    },
    3: {
        "adult": "信息网络、线报、传播、谈判、地面关系、组织口径",
        "power": "决定你如何通过消息、人脉、名单和传播形成影响力。",
    },
    4: {
        "adult": "家族根基、地盘、安全盘、退路",
        "power": "决定你是否有足够稳的根基去承受外部扩张。",
    },
    5: {
        "adult": "创作表达、名色、娱乐场、个人招牌",
        "power": "决定你如何把个人魅力与舞台感变成影响力。",
    },
    6: {
        "adult": "执行系统、差事、日常工序、用人管理",
        "power": "决定你能否把复杂事务做成持续运转的流程。",
    },
    7: {
        "adult": "联盟、客户、对手、契约、师徒、保护关系",
        "power": "决定你如何通过他人进入更大的系统并借力扩张。",
    },
    8: {
        "adult": "风险共担、利益绑定、债务与筹码",
        "power": "决定你如何处理权力背后的代价、筹码和深度绑定。",
    },
    9: {
        "adult": "理念、旗号、远方资源、合法性",
        "power": "决定你如何给自己的路径找到更大的叙事和正当性。",
    },
    10: {
        "adult": "公开地位、制度名望、社会抬头",
        "power": "决定你如何被公众看见，以及以什么身份被承认。",
    },
    11: {
        "adult": "人脉团体、门生网络、长期势力",
        "power": "决定你能否把个人关系做成成规模的势力网络。",
    },
    12: {
        "adult": "幕后运作、监禁清算、隐形敌人、收尾代价",
        "power": "决定你如何处理台面下的力量，以及后期如何被回收。",
    },
}

HOUSE_DOMAIN_WEIGHTS: Dict[int, Dict[str, float]] = {
    1: {"career": 0.20, "wealth": 0.10, "relationship": 0.15, "health": 0.45, "family": 0.10},
    2: {"career": 0.20, "wealth": 0.55, "relationship": 0.05, "health": 0.05, "family": 0.15},
    3: {"career": 0.25, "wealth": 0.10, "relationship": 0.10, "health": 0.10, "family": 0.30},
    4: {"career": 0.10, "wealth": 0.10, "relationship": 0.20, "health": 0.10, "family": 0.50},
    5: {"career": 0.15, "wealth": 0.10, "relationship": 0.45, "health": 0.10, "family": 0.20},
    6: {"career": 0.35, "wealth": 0.10, "relationship": 0.05, "health": 0.40, "family": 0.10},
    7: {"career": 0.15, "wealth": 0.10, "relationship": 0.55, "health": 0.05, "family": 0.15},
    8: {"career": 0.10, "wealth": 0.45, "relationship": 0.10, "health": 0.25, "family": 0.10},
    9: {"career": 0.25, "wealth": 0.10, "relationship": 0.10, "health": 0.05, "family": 0.10},
    10: {"career": 0.55, "wealth": 0.15, "relationship": 0.05, "health": 0.05, "family": 0.05},
    11: {"career": 0.25, "wealth": 0.25, "relationship": 0.25, "health": 0.05, "family": 0.05},
    12: {"career": 0.05, "wealth": 0.05, "relationship": 0.10, "health": 0.40, "family": 0.20},
}

PLANET_DOMAIN_WEIGHTS: Dict[Planet, Dict[str, float]] = {
    Planet.SUN: {"career": 0.40, "wealth": 0.15, "relationship": 0.10, "health": 0.10, "family": 0.05},
    Planet.MOON: {"career": 0.05, "wealth": 0.10, "relationship": 0.25, "health": 0.25, "family": 0.30},
    Planet.MERCURY: {"career": 0.30, "wealth": 0.20, "relationship": 0.10, "health": 0.05, "family": 0.05},
    Planet.VENUS: {"career": 0.10, "wealth": 0.15, "relationship": 0.40, "health": 0.05, "family": 0.15},
    Planet.MARS: {"career": 0.35, "wealth": 0.15, "relationship": 0.05, "health": 0.20, "family": 0.05},
    Planet.JUPITER: {"career": 0.20, "wealth": 0.35, "relationship": 0.15, "health": 0.05, "family": 0.10},
    Planet.SATURN: {"career": 0.35, "wealth": 0.15, "relationship": 0.05, "health": 0.15, "family": 0.10},
    Planet.NORTH_NODE: {"career": 0.20, "wealth": 0.20, "relationship": 0.20, "health": 0.10, "family": 0.10},
    Planet.SOUTH_NODE: {"career": 0.10, "wealth": 0.10, "relationship": 0.10, "health": 0.20, "family": 0.20},
}

ASPECT_LABELS = {
    AspectType.CONJUNCTION: "合相",
    AspectType.SEXTILE: "六合",
    AspectType.SQUARE: "刑相",
    AspectType.TRINE: "三合",
    AspectType.OPPOSITION: "对冲",
    AspectType.QUINCUNX: "梅花相",
}

TRADITIONAL_PLANETS = [
    Planet.SUN,
    Planet.MOON,
    Planet.MERCURY,
    Planet.VENUS,
    Planet.MARS,
    Planet.JUPITER,
    Planet.SATURN,
]

SECT_DAY_PLANETS = {Planet.SUN, Planet.JUPITER, Planet.SATURN}
SECT_NIGHT_PLANETS = {Planet.MOON, Planet.VENUS, Planet.MARS}
PLANET_ORBS: Dict[Planet, float] = {
    Planet.SUN: 8.0,
    Planet.MOON: 7.0,
    Planet.MERCURY: 5.5,
    Planet.VENUS: 5.5,
    Planet.MARS: 6.0,
    Planet.JUPITER: 6.0,
    Planet.SATURN: 6.0,
}


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def planet_label(planet: Planet | str) -> str:
    if isinstance(planet, Planet):
        return PLANET_LABELS.get(planet, planet.value)
    try:
        return PLANET_LABELS[Planet(planet)]
    except Exception:
        return str(planet)


def sign_label(sign: Sign | str) -> str:
    if isinstance(sign, Sign):
        return SIGN_LABELS.get(sign, sign.value)
    try:
        return SIGN_LABELS[Sign(sign)]
    except Exception:
        return str(sign)


def get_planet_orb(planet: Planet) -> float:
    return PLANET_ORBS.get(planet, 5.5)


class LifeKlineService:
    def __init__(self) -> None:
        self.engine = EphemerisEngine()

    def generate_report(
        self,
        birth_time_iso: str,
        lat: float,
        lon: float,
        timezone_offset: float = 8.0,
    ) -> Dict[str, Any]:
        birth_time_local, birth_time_utc = self._parse_birth_time(birth_time_iso, timezone_offset)
        chart = self.engine.calculate_chart(birth_time_utc, lat, lon)
        aspect_cache = self._build_aspect_cache(chart)
        planet_profiles = self._build_planet_profiles(chart, aspect_cache)
        periods = calculate_firdaria_periods(chart.is_day_chart)

        output_data: Dict[str, Any] = {
            "meta": {
                "generated_at": datetime.now().isoformat(),
                "engine_version": "2.3.0",
            },
            "user_info": {
                "birth_time_local": birth_time_local.isoformat(),
                "birth_time_utc": birth_time_utc.isoformat(),
                "lat": lat,
                "lon": lon,
                "timezone": f"GMT{timezone_offset:+.1f}",
                "is_day_chart": chart.is_day_chart,
            },
            "kline_data": {"periods": []},
        }

        periods_data = self._build_periods_data(
            periods=periods,
            birth_time_local=birth_time_local,
            chart=chart,
            planet_profiles=planet_profiles,
            aspect_cache=aspect_cache,
        )
        output_data["kline_data"]["periods"] = periods_data

        natal_chart = self._build_natal_chart(chart, planet_profiles, aspect_cache)
        current_phase = self._build_current_phase(periods_data, birth_time_local)
        life_model = self._build_life_model(
            chart=chart,
            natal_chart=natal_chart,
            periods_data=periods_data,
            current_phase=current_phase,
        )
        natal_blueprint = self._build_natal_blueprint(
            birth_time_iso=birth_time_iso,
            lat=lat,
            lon=lon,
            natal_chart=natal_chart,
            planet_profiles=planet_profiles,
        )
        advanced_patterns = self._build_advanced_patterns(
            birth_time_iso=birth_time_iso,
            lat=lat,
            lon=lon,
            natal_chart=natal_chart,
            planet_profiles=planet_profiles,
        )
        timeline_validation = self._build_timeline_validation(
            birth_time_iso=birth_time_iso,
            birth_time_local=birth_time_local,
            lat=lat,
            lon=lon,
            periods_data=periods_data,
        )

        output_data["natal_chart"] = natal_chart
        output_data["current_phase"] = current_phase
        output_data["life_model"] = life_model
        output_data["natal_blueprint"] = natal_blueprint
        output_data["advanced_patterns"] = advanced_patterns
        output_data["timeline_validation"] = timeline_validation
        return output_data

    def _parse_birth_time(self, birth_time_iso: str, timezone_offset: float) -> tuple[datetime, datetime]:
        try:
            parsed_birth_time = datetime.fromisoformat(birth_time_iso)
        except ValueError as exc:
            raise ValueError(
                f"Invalid date format: {birth_time_iso}. Expected ISO 8601."
            ) from exc

        if parsed_birth_time.tzinfo is not None:
            birth_time_utc = parsed_birth_time.astimezone(timezone.utc).replace(tzinfo=None)
            birth_time_local = birth_time_utc + timedelta(hours=timezone_offset)
        else:
            birth_time_local = parsed_birth_time
            birth_time_utc = birth_time_local - timedelta(hours=timezone_offset)
        return birth_time_local, birth_time_utc

    def _build_aspect_cache(self, chart: Any) -> Dict[Planet, list[Dict[str, Any]]]:
        cache: Dict[Planet, list[Dict[str, Any]]] = {planet: [] for planet in TRADITIONAL_PLANETS}
        for planet_a, planet_b in combinations(TRADITIONAL_PLANETS, 2):
            info_a = chart.get_planet_info(planet_a)
            info_b = chart.get_planet_info(planet_b)
            if not info_a or not info_b:
                continue

            aspect = self._detect_aspect(planet_a, info_a, planet_b, info_b)
            if not aspect:
                continue

            cache[planet_a].append(aspect)
            cache[planet_b].append(aspect)
        return cache

    def _detect_aspect(self, planet_a: Planet, info_a: Any, planet_b: Planet, info_b: Any) -> Optional[Dict[str, Any]]:
        longitude_a = self._absolute_longitude(info_a)
        longitude_b = self._absolute_longitude(info_b)
        diff = abs(longitude_a - longitude_b) % 360
        diff = min(diff, 360 - diff)

        best: Optional[Dict[str, Any]] = None
        best_orb = 999.0
        pair_orb = (get_planet_orb(planet_a) + get_planet_orb(planet_b)) / 2.0

        for aspect_type in (
            AspectType.CONJUNCTION,
            AspectType.SEXTILE,
            AspectType.SQUARE,
            AspectType.TRINE,
            AspectType.OPPOSITION,
        ):
            config = ASPECT_CONFIG[aspect_type]
            aspect_orb = min(config["orb"], pair_orb)
            orb = abs(diff - config["angle"])
            if orb > aspect_orb or orb >= best_orb:
                continue

            strength = clamp(config["strength"] * (1.0 - orb / aspect_orb), 0.1, 1.0)
            best_orb = orb
            best = {
                "planet1": planet_a,
                "planet2": planet_b,
                "type": aspect_type,
                "orb": round(orb, 2),
                "strength": round(strength, 3),
                "nature": self._aspect_nature(aspect_type, planet_a, planet_b),
                "label": ASPECT_LABELS[aspect_type],
                "summary": self._aspect_summary(aspect_type, planet_a, planet_b),
            }

        return best

    def _aspect_nature(self, aspect_type: AspectType, planet_a: Planet, planet_b: Planet) -> str:
        if aspect_type in (AspectType.TRINE, AspectType.SEXTILE):
            return "supportive"
        if aspect_type in (AspectType.SQUARE, AspectType.OPPOSITION):
            return "challenging"
        if aspect_type == AspectType.CONJUNCTION:
            if planet_a.is_benefic or planet_b.is_benefic:
                return "supportive"
            if planet_a.is_malefic or planet_b.is_malefic:
                return "challenging"
        return "mixed"

    def _aspect_summary(self, aspect_type: AspectType, planet_a: Planet, planet_b: Planet) -> str:
        label_a = planet_label(planet_a)
        label_b = planet_label(planet_b)
        if aspect_type == AspectType.CONJUNCTION:
            return f"{label_a}与{label_b}合流，主题会被放大。"
        if aspect_type == AspectType.TRINE:
            return f"{label_a}与{label_b}形成顺流，推进更自然。"
        if aspect_type == AspectType.SEXTILE:
            return f"{label_a}与{label_b}互相配合，适合主动争取。"
        if aspect_type == AspectType.SQUARE:
            return f"{label_a}与{label_b}存在张力，逼你调整方法。"
        if aspect_type == AspectType.OPPOSITION:
            return f"{label_a}与{label_b}拉扯明显，需要在两端寻找平衡。"
        return f"{label_a}与{label_b}形成复杂联动。"

    def _build_planet_profiles(
        self,
        chart: Any,
        aspect_cache: Dict[Planet, list[Dict[str, Any]]],
    ) -> Dict[Planet, Dict[str, Any]]:
        profiles: Dict[Planet, Dict[str, Any]] = {}
        asc_sign = chart.houses[0][0] if hasattr(chart, "houses") and chart.houses else None
        chart_ruler = SIGN_RULERS.get(asc_sign) if asc_sign else None

        for planet in TRADITIONAL_PLANETS:
            info = chart.get_planet_info(planet)
            if not info:
                continue

            dignity_code, dignity_score = self._dignity_state(planet, info.sign)
            aspects = sorted(
                aspect_cache.get(planet, []),
                key=lambda item: item["strength"],
                reverse=True,
            )
            supportive = sum(a["strength"] for a in aspects if a["nature"] == "supportive")
            challenging = sum(a["strength"] for a in aspects if a["nature"] == "challenging")
            mixed = sum(a["strength"] for a in aspects if a["nature"] == "mixed")
            house_score = self._house_strength(info.house)
            joy_score = 0.35 if JOY_HOUSES.get(planet) == info.house else 0.0
            sect_score = self._sect_modifier(planet, chart.is_day_chart)
            retrograde_penalty = -0.3 if getattr(info, "is_retrograde", False) else 0.0
            ruler_bonus = 0.25 if chart_ruler == planet else 0.0

            score = (
                dignity_score
                + house_score
                + joy_score
                + sect_score
                + supportive * 0.55
                - challenging * 0.65
                - mixed * 0.10
                + retrograde_penalty
                + ruler_bonus
            )
            score = clamp(score, -3.2, 3.2)

            house_title = HOUSE_TOPICS[info.house]["title"]
            keywords = [
                PLANET_ARCHETYPES[planet]["gift"],
                *HOUSE_TOPICS[info.house]["keywords"][:2],
            ]
            profiles[planet] = {
                "planet": planet,
                "label": planet_label(planet),
                "sign": info.sign.value,
                "sign_label": sign_label(info.sign),
                "house": info.house,
                "house_title": house_title,
                "degree": round(info.degree, 1),
                "retrograde": bool(getattr(info, "is_retrograde", False)),
                "dignity": dignity_code,
                "dignity_label": DIGNITY_LABELS[dignity_code],
                "score": round(score, 3),
                "supportive_aspects": round(supportive, 3),
                "challenging_aspects": round(challenging, 3),
                "aspect_signature": [self._format_aspect_line(planet, item) for item in aspects[:3]],
                "aspect_count": len(aspects),
                "keywords": keywords,
                "gift": PLANET_ARCHETYPES[planet]["gift"],
                "shadow": PLANET_ARCHETYPES[planet]["shadow"],
                "strategy": PLANET_ARCHETYPES[planet]["strategy"],
                "reason": self._planet_reason(
                    planet=planet,
                    dignity_label=DIGNITY_LABELS[dignity_code],
                    house_title=house_title,
                    supportive=supportive,
                    challenging=challenging,
                    chart_ruler=chart_ruler,
                ),
            }
        return profiles

    def _planet_reason(
        self,
        planet: Planet,
        dignity_label: str,
        house_title: str,
        supportive: float,
        challenging: float,
        chart_ruler: Optional[Planet],
    ) -> str:
        reason = f"{planet_label(planet)}落在{house_title}，先天状态为{dignity_label}。"
        if supportive > challenging + 0.35:
            reason += " 相位支持较多，能把天赋顺着结构用出来。"
        elif challenging > supportive + 0.35:
            reason += " 相位拉扯偏重，人生会通过摩擦逼出成熟度。"
        else:
            reason += " 支持与压力并存，需要靠节奏管理来定胜负。"
        if chart_ruler == planet:
            reason += " 这也是整张命盘的命主星，权重更高。"
        return reason

    def _format_aspect_line(self, focus_planet: Planet, aspect: Dict[str, Any]) -> str:
        other = aspect["planet2"] if aspect["planet1"] == focus_planet else aspect["planet1"]
        return f"{aspect['label']} {planet_label(other)}，容许度 {aspect['orb']}°"

    def _dignity_state(self, planet: Planet, sign: Sign) -> tuple[str, float]:
        if sign in DOMICILE_SIGNS.get(planet, []):
            return "domicile", 1.8
        if sign in EXALTATION_SIGNS.get(planet, []):
            return "exaltation", 1.35
        if sign in DETRIMENT_SIGNS.get(planet, []):
            return "detriment", -1.35
        if sign in FALL_SIGNS.get(planet, []):
            return "fall", -1.75
        return "peregrine", 0.0

    def _house_strength(self, house: int) -> float:
        if house in ANGULAR_HOUSES:
            return 0.95
        if house in SUCCEDENT_HOUSES:
            return 0.45
        if house in CADENT_HOUSES:
            return 0.1
        return 0.0

    def _sect_modifier(self, planet: Planet, is_day_chart: bool) -> float:
        if planet == Planet.MERCURY:
            return 0.1
        if is_day_chart and planet in SECT_DAY_PLANETS:
            return 0.25
        if (not is_day_chart) and planet in SECT_NIGHT_PLANETS:
            return 0.25
        if is_day_chart and planet == Planet.MARS:
            return -0.2
        if (not is_day_chart) and planet == Planet.SATURN:
            return -0.2
        return 0.0

    def _build_periods_data(
        self,
        periods: Iterable[FirdariaPeriod],
        birth_time_local: datetime,
        chart: Any,
        planet_profiles: Dict[Planet, Dict[str, Any]],
        aspect_cache: Dict[Planet, list[Dict[str, Any]]],
    ) -> list[Dict[str, Any]]:
        data: list[Dict[str, Any]] = []
        for index, period in enumerate(periods):
            major_profile = planet_profiles.get(period.major_lord)
            if not major_profile:
                continue

            sub_profile = planet_profiles.get(period.sub_lord) if period.sub_lord else None
            major_score = major_profile["score"]
            sub_score = sub_profile["score"] if sub_profile else major_score * 0.6
            bonus = clamp((major_score * 0.72 + sub_score * 0.28) / 4.5, -0.75, 0.75)

            trend_type = "stable"
            if bonus >= 0.16:
                trend_type = "bull"
            elif bonus <= -0.16:
                trend_type = "bear"

            start_date = birth_time_local + timedelta(days=period.start_age * 365.242199)
            end_date = birth_time_local + timedelta(days=period.end_age * 365.242199)
            domains = self._build_domain_scores(period, major_profile, sub_profile, bonus)
            summary_pack = self._build_period_summary(
                period=period,
                major_profile=major_profile,
                sub_profile=sub_profile,
                bonus=bonus,
                trend_type=trend_type,
                domains=domains,
                aspect_cache=aspect_cache,
            )

            data.append(
                {
                    "index": index,
                    "timing": {
                        "start_age": round(period.start_age, 2),
                        "end_age": round(period.end_age, 2),
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat(),
                        "duration_years": round(period.duration, 2),
                    },
                    "lords": {
                        "major": period.major_lord.value,
                        "sub": period.sub_lord.value if period.sub_lord else None,
                    },
                    "trend": {
                        "bonus_coefficient": round(bonus, 3),
                        "type": trend_type,
                    },
                    "domains": domains,
                    "astrology": {
                        "sign": major_profile["sign"],
                        "sign_label": major_profile["sign_label"],
                        "house": major_profile["house"],
                        "house_title": major_profile["house_title"],
                        "dignity": major_profile["dignity"],
                        "dignity_label": major_profile["dignity_label"],
                        "major_score": round(major_score, 2),
                        "sub_score": round(sub_score, 2),
                        "aspect_signature": major_profile["aspect_signature"][:2],
                    },
                    "title": summary_pack["title"],
                    "summary": summary_pack["summary"],
                    "themes": summary_pack["themes"],
                    "opportunities": summary_pack["opportunities"],
                    "cautions": summary_pack["cautions"],
                    "action_focus": summary_pack["action_focus"],
                    "type": "major",
                }
            )
        return data

    def _build_domain_scores(
        self,
        period: FirdariaPeriod,
        major_profile: Dict[str, Any],
        sub_profile: Optional[Dict[str, Any]],
        bonus: float,
    ) -> Dict[str, float]:
        house_weights = HOUSE_DOMAIN_WEIGHTS[major_profile["house"]]
        planet_weights = PLANET_DOMAIN_WEIGHTS.get(period.major_lord, HOUSE_DOMAIN_WEIGHTS[major_profile["house"]])
        sub_weights = (
            PLANET_DOMAIN_WEIGHTS.get(period.sub_lord, planet_weights) if period.sub_lord else planet_weights
        )

        base = 50 + bonus * 22
        result: Dict[str, float] = {}
        for domain in ("career", "wealth", "relationship", "health", "family"):
            score = (
                base
                + house_weights[domain] * 22
                + planet_weights.get(domain, 0.1) * 18
                + sub_weights.get(domain, 0.1) * 8
                + major_profile["supportive_aspects"] * 4
                - major_profile["challenging_aspects"] * 5
            )
            result[domain] = round(clamp(score, 18, 92), 1)
        return result

    def _build_period_summary(
        self,
        period: FirdariaPeriod,
        major_profile: Dict[str, Any],
        sub_profile: Optional[Dict[str, Any]],
        bonus: float,
        trend_type: str,
        domains: Dict[str, float],
        aspect_cache: Dict[Planet, list[Dict[str, Any]]],
    ) -> Dict[str, Any]:
        house_topic = major_profile["house_title"]
        major_label = major_profile["label"]
        sub_label = sub_profile["label"] if sub_profile else "无子运"
        top_domains = self._top_domains(domains)
        themes = [
            f"{major_label}主题被放大",
            f"重点落在{house_topic}",
            f"{top_domains[0]['label']}是阶段主轴",
        ]
        opportunities = [
            self._phase_opportunity_line(major_profile, top_domains[0]["label"], trend_type),
            self._phase_opportunity_line(
                sub_profile or major_profile,
                top_domains[1]["label"] if len(top_domains) > 1 else top_domains[0]["label"],
                trend_type,
            ),
        ]
        cautions = [
            self._phase_caution_line(major_profile, trend_type),
            self._phase_caution_line(sub_profile or major_profile, "mixed"),
        ]
        action_focus = [
            f"把时间优先给{top_domains[0]['label']}和{top_domains[1]['label'] if len(top_domains) > 1 else top_domains[0]['label']}。",
            major_profile["strategy"],
            self._house_action_line(major_profile["house"]),
        ]
        summary = (
            f"{major_label}主运、{sub_label}辅运。主星落在{major_profile['house_title']}，"
            f"先天状态为{major_profile['dignity_label']}，"
            f"因此这段时间的人生重心会围绕{top_domains[0]['label']}与{top_domains[1]['label'] if len(top_domains) > 1 else top_domains[0]['label']}展开。"
        )
        title = f"{major_label} - {sub_label} 阶段"

        if trend_type == "bull":
            summary += " 整体是扩张窗口，适合把已经成熟的能力推向更大舞台。"
        elif trend_type == "bear":
            summary += " 整体偏收缩与校准，更适合整顿结构、清理负担、避免高杠杆。"
        else:
            summary += " 整体偏平稳，重点在于打磨方法、搭好结构、耐心推进。"

        return {
            "title": title,
            "summary": summary,
            "themes": themes,
            "opportunities": opportunities,
            "cautions": cautions,
            "action_focus": action_focus,
        }

    def _phase_opportunity_line(self, profile: Dict[str, Any], domain_label: str, trend_type: str) -> str:
        prefix = "放大" if trend_type == "bull" else "稳住" if trend_type == "stable" else "修复"
        return f"{prefix}{profile['label']}在{domain_label}上的能力，优先做可复用、可沉淀的成果。"

    def _phase_caution_line(self, profile: Dict[str, Any], trend_type: str) -> str:
        if trend_type == "bull":
            return f"别让{profile['label']}的顺风感演变成过度承诺，{profile['shadow']}是这段的代价点。"
        if trend_type == "bear":
            return f"这段容易放大{profile['shadow']}，不要在不稳定时做过于激进的押注。"
        return f"即使局面平稳，也要注意{profile['shadow']}，别被惯性牵着走。"

    def _house_action_line(self, house: int) -> str:
        house_title = HOUSE_TOPICS[house]["title"]
        if house == 10:
            return "把资源押在能形成社会可见度、职位抬升或作品背书的事项上。"
        if house == 7:
            return "关键突破来自合作关系，谈规则比谈感觉更重要。"
        if house == 4:
            return "先稳根基，家庭、居住、心理安全感会直接影响外部发挥。"
        if house == 6:
            return "你的胜负点不在灵感，而在习惯、流程和执行耐力。"
        if house == 11:
            return "扩大人脉池、社群协作与长期愿景，比单打独斗更高效。"
        if house == 12:
            return "控制外部噪音，预留退场与修复时间，隐性损耗要先止血。"
        return f"围绕{house_title}做结构化经营，而不是被情绪和偶然性牵着走。"

    def _top_domains(self, domains: Dict[str, float]) -> list[Dict[str, Any]]:
        label_map = {
            "career": "事业",
            "wealth": "财富",
            "relationship": "关系",
            "health": "健康",
            "family": "家庭",
        }
        ranked = sorted(domains.items(), key=lambda item: item[1], reverse=True)
        return [{"key": key, "label": label_map[key], "score": score} for key, score in ranked]

    def _build_natal_chart(
        self,
        chart: Any,
        planet_profiles: Dict[Planet, Dict[str, Any]],
        aspect_cache: Dict[Planet, list[Dict[str, Any]]],
    ) -> Dict[str, Any]:
        asc_sign = chart.houses[0][0] if hasattr(chart, "houses") and chart.houses else Sign.ARIES
        asc_degree = chart.houses[0][1] if hasattr(chart, "houses") and chart.houses else 0.0
        chart_ruler = SIGN_RULERS.get(asc_sign, Planet.SUN)

        dominant_planets = sorted(
            planet_profiles.values(),
            key=lambda item: item["score"],
            reverse=True,
        )[:3]
        weakest_planets = sorted(
            planet_profiles.values(),
            key=lambda item: item["score"],
        )[:2]

        major_aspects = self._build_major_aspects(aspect_cache)
        house_emphasis = self._build_house_emphasis(chart)
        signature = self._build_signature_text(chart, planet_profiles, chart_ruler, dominant_planets)

        planets_payload: Dict[str, Any] = {}
        for planet, profile in planet_profiles.items():
            planets_payload[planet.value] = {
                "sign": profile["sign"],
                "sign_label": profile["sign_label"],
                "house": profile["house"],
                "house_title": profile["house_title"],
                "dignity": profile["dignity"],
                "dignity_label": profile["dignity_label"],
                "degree": profile["degree"],
                "retrograde": profile["retrograde"],
                "score": round(profile["score"], 2),
                "keywords": profile["keywords"],
                "gift": profile["gift"],
                "shadow": profile["shadow"],
                "strategy": profile["strategy"],
                "aspect_signature": profile["aspect_signature"],
                "reason": profile["reason"],
            }

        return {
            "ascendant": {
                "sign": asc_sign.value,
                "sign_label": sign_label(asc_sign),
                "degree": round(asc_degree, 1),
            },
            "houses": [
                {
                    "house": index + 1,
                    "sign": sign.value,
                    "sign_label": sign_label(sign),
                    "degree": round(degree, 1),
                    "title": HOUSE_TOPICS[index + 1]["title"],
                }
                for index, (sign, degree) in enumerate(getattr(chart, "houses", [])[:12])
            ],
            "sect": "day" if chart.is_day_chart else "night",
            "sect_label": "日盘" if chart.is_day_chart else "夜盘",
            "chart_ruler": chart_ruler.value,
            "chart_ruler_label": planet_label(chart_ruler),
            "signature": signature,
            "planets": planets_payload,
            "dominant_planets": [
                {
                    "planet": p["planet"].value,
                    "label": p["label"],
                    "score": round(p["score"], 2),
                    "reason": p["reason"],
                }
                for p in dominant_planets
            ],
            "pressure_points": [
                {
                    "planet": p["planet"].value,
                    "label": p["label"],
                    "score": round(p["score"], 2),
                    "reason": p["reason"],
                }
                for p in weakest_planets
            ],
            "house_emphasis": house_emphasis,
            "major_aspects": major_aspects,
        }

    def _build_house_emphasis(self, chart: Any) -> list[Dict[str, Any]]:
        weights: Dict[int, float] = {house: 0.0 for house in range(1, 13)}
        for planet in TRADITIONAL_PLANETS:
            info = chart.get_planet_info(planet)
            if not info:
                continue
            weights[info.house] += 1.2 if planet in (Planet.SUN, Planet.MOON) else 1.0
        ranked = sorted(weights.items(), key=lambda item: item[1], reverse=True)[:4]
        return [
            {
                "house": house,
                "title": HOUSE_TOPICS[house]["title"],
                "keywords": HOUSE_TOPICS[house]["keywords"],
                "weight": round(weight, 2),
            }
            for house, weight in ranked
            if weight > 0
        ]

    def _build_major_aspects(self, aspect_cache: Dict[Planet, list[Dict[str, Any]]]) -> list[Dict[str, Any]]:
        seen: set[tuple[str, str, str]] = set()
        aspects: list[Dict[str, Any]] = []
        for items in aspect_cache.values():
            for aspect in items:
                key = (
                    aspect["planet1"].value,
                    aspect["planet2"].value,
                    aspect["type"].value,
                )
                reverse_key = (
                    aspect["planet2"].value,
                    aspect["planet1"].value,
                    aspect["type"].value,
                )
                if key in seen or reverse_key in seen:
                    continue
                seen.add(key)
                aspects.append(
                    {
                        "title": f"{planet_label(aspect['planet1'])} {aspect['label']} {planet_label(aspect['planet2'])}",
                        "strength": aspect["strength"],
                        "nature": aspect["nature"],
                        "summary": aspect["summary"],
                    }
                )
        aspects.sort(key=lambda item: item["strength"], reverse=True)
        return aspects[:6]

    def _build_signature_text(
        self,
        chart: Any,
        planet_profiles: Dict[Planet, Dict[str, Any]],
        chart_ruler: Planet,
        dominant_planets: list[Dict[str, Any]],
    ) -> str:
        sun_sign = sign_label(chart.get_planet_info(Planet.SUN).sign) if chart.get_planet_info(Planet.SUN) else "未知"
        moon_sign = sign_label(chart.get_planet_info(Planet.MOON).sign) if chart.get_planet_info(Planet.MOON) else "未知"
        asc_sign = sign_label(chart.houses[0][0]) if hasattr(chart, "houses") and chart.houses else "未知"
        dominant_labels = "、".join(item["label"] for item in dominant_planets[:2])
        return (
            f"这是一个以{asc_sign}上升起盘、太阳落在{sun_sign}、月亮落在{moon_sign}的命盘。"
            f"命主星是{planet_label(chart_ruler)}，主导力量偏向{dominant_labels}。"
            "整体不是靠单一高光取胜，而是靠把人生关键主题做成长期结构。"
        )

    def _build_current_phase(
        self,
        periods_data: list[Dict[str, Any]],
        birth_time_local: datetime,
    ) -> Optional[Dict[str, Any]]:
        current_age = (datetime.now() - birth_time_local).days / 365.2422
        for period in periods_data:
            start_age = period["timing"]["start_age"]
            end_age = period["timing"]["end_age"]
            if not (start_age <= current_age < end_age):
                continue

            domains_ranked = self._top_domains(period["domains"])
            bonus = period["trend"]["bonus_coefficient"]
            trend_type = period["trend"]["type"]
            feeling = self._current_feeling(period["astrology"]["house_title"], trend_type)
            description = self._trend_display_text(trend_type, bonus)
            return {
                "age_range": f"{int(start_age)} - {int(end_age)} 岁",
                "start_date": period["timing"]["start_date"],
                "end_date": period["timing"]["end_date"],
                "major_lord": period["lords"]["major"],
                "sub_lord": period["lords"]["sub"] or "",
                "trend_type": trend_type,
                "score": round(50 + bonus * 40, 1),
                "keywords": period["themes"][:3],
                "feeling": feeling,
                "description": description,
                "summary": period["summary"],
                "opportunities": period["opportunities"],
                "cautions": period["cautions"],
                "action_focus": period["action_focus"],
                "dominant_domains": domains_ranked[:3],
                "why_now": (
                    f"主运星落在{period['astrology']['house_title']}，"
                    f"且先天状态为{period['astrology']['dignity_label']}，"
                    "所以这几年的人生议题会更集中、更具体。"
                ),
            }
        return None

    def _current_feeling(self, house_title: str, trend_type: str) -> str:
        if trend_type == "bull":
            return f"你会明显感觉到，围绕{house_title}的事情更容易出现推力和窗口。"
        if trend_type == "bear":
            return f"你会感到，{house_title}相关的课题在逼你收缩、修正和重新排优先级。"
        return f"当前阶段不会剧烈翻盘，但{house_title}会成为你持续经营的主线。"

    def _trend_display_text(self, trend_type: str, bonus: float) -> str:
        if trend_type == "bull":
            return f"扩张段（基准提升 {bonus:.0%}）"
        if trend_type == "bear":
            return f"收缩段（基准回落 {abs(bonus):.0%}）"
        return "平稳段"

    def _build_natal_blueprint(
        self,
        birth_time_iso: str,
        lat: float,
        lon: float,
        natal_chart: Dict[str, Any],
        planet_profiles: Dict[Planet, Dict[str, Any]],
    ) -> Dict[str, Any]:
        is_historical_sample = self._is_huang_jinrong_sample(birth_time_iso, lat, lon)
        dominant = natal_chart.get("dominant_planets", [])
        pressure_points = natal_chart.get("pressure_points", [])
        houses = natal_chart.get("house_emphasis", [])
        top_house = houses[0] if houses else None
        second_house = houses[1] if len(houses) > 1 else None
        chart_ruler_value = natal_chart.get("chart_ruler")
        chart_ruler_label = natal_chart.get("chart_ruler_label", "命主星")

        chart_ruler_profile: Optional[Dict[str, Any]] = None
        if chart_ruler_value:
            try:
                chart_ruler_profile = planet_profiles.get(Planet(chart_ruler_value))
            except Exception:
                chart_ruler_profile = None

        role_title = self._build_role_title(natal_chart, planet_profiles, is_historical_sample)
        role_keywords = self._build_role_keywords(natal_chart)
        structure_summary = (
            "这张盘的底层不是靠单点爆发取胜，而是靠把核心议题做成长期结构。"
            if not is_historical_sample
            else "这张盘的底层不是天然高位，而是通过信息、关系、资源与隐性控制一步步做大。"
        )
        power_summary = (
            "真正影响人生走向的，不只是性格，而是你如何获得资源、进入系统并形成控制力。"
        )
        role_summary = (
            "本命蓝图不只回答“你像什么人”，还要回答“你在社会中更像哪一种角色”。"
        )
        cost_summary = (
            "每种强项都有对应的代价。越能成事的结构，越需要知道它会从哪里反噬。"
        )

        structure_points = [
            (
                f"上升在{natal_chart['ascendant']['sign_label']}，命主星是{chart_ruler_label}。"
                f"这说明你的人生入口更依赖{chart_ruler_profile['gift'] if chart_ruler_profile else '长期经营能力'}。"
            ),
            (
                f"主导力量偏向{'、'.join(item['label'] for item in dominant[:2]) or chart_ruler_label}，"
                "真正能带来跃迁的，往往不是单个高光，而是持续放大的主轴。"
            ),
            (
                f"最强宫位集中在{self._format_house_titles(houses[:3])}，"
                "它们不是零散主题，而是会反复塑造人生路径的主结构。"
            ),
        ]

        power_points = []
        if top_house:
            power_points.append(
                f"第一权力入口在第{top_house['house']}宫：{HOUSE_ADULT_MEANINGS[top_house['house']]['adult']}。"
            )
            power_points.append(HOUSE_ADULT_MEANINGS[top_house["house"]]["power"])
        if second_house:
            power_points.append(
                f"第二杠杆在第{second_house['house']}宫：{HOUSE_ADULT_MEANINGS[second_house['house']]['adult']}。"
            )
        if is_historical_sample:
            power_points = [
                "3宫过强，说明真正的上位方式不是抽象的“表达”，而是线报、传播、谈判与地面关系。",
                "7宫木星让扩张更多通过联盟、门生、保护关系与更大的制度平台完成。",
                "2宫金星与12宫火星把资源经营和幕后控制绑在一起，钱与权不会完全分开。",
            ]

        role_points = [
            f"这张盘更像“{role_title}”，而不是单纯的性格标签。",
            (
                f"命主星{chart_ruler_label}"
                f"{'落在第' + str(chart_ruler_profile['house']) + '宫' if chart_ruler_profile else ''}，"
                "说明你的核心能力会通过特定社会场景显形，而不是停留在抽象潜能。"
            ),
            f"重点宫位的成人社会义分别落在：{self._format_house_adult_meanings(houses[:4])}。",
        ]
        if is_historical_sample:
            role_points = [
                "这张盘更像“信息操盘型权力人物”，不是温和的表达型人格。",
                "它的核心不是正面高光，而是把名单、关系、口径、制度缝隙变成控制力。",
                "同样的结构放在现代语境里，也常见于组织操盘者、关系整合者、规则边缘高手。",
            ]

        cost_points = []
        if pressure_points:
            cost_points.append(
                f"首要代价点在{pressure_points[0]['label']}：{pressure_points[0]['reason']}"
            )
        if len(pressure_points) > 1:
            cost_points.append(
                f"第二代价点在{pressure_points[1]['label']}：{pressure_points[1]['reason']}"
            )
        if houses:
            cost_points.append(
                f"当第{houses[0]['house']}宫议题失衡时，最容易把优势变成负担。"
            )
        if is_historical_sample:
            cost_points = [
                "水星失势又合土星，意味着信息优势会越来越带上冷硬、规训与控制色彩。",
                "金星失势落2宫，说明资源与享乐一旦绑定，后期就容易把欲望变成结构性代价。",
                "12宫火星不是简单的内耗，而是幕后冲突、清算与晚年回收机制。",
            ]

        return {
            "role_title": role_title,
            "summary": natal_chart.get("signature"),
            "keywords": role_keywords,
            "layers": [
                {
                    "key": "structure",
                    "title": "结构层",
                    "headline": f"{natal_chart['ascendant']['sign_label']}上升 · {chart_ruler_label}命主",
                    "summary": structure_summary,
                    "points": structure_points,
                },
                {
                    "key": "power",
                    "title": "权力层",
                    "headline": "资源、关系与控制如何运作",
                    "summary": power_summary,
                    "points": power_points,
                },
                {
                    "key": "role",
                    "title": "角色层",
                    "headline": role_title,
                    "summary": role_summary,
                    "points": role_points,
                },
                {
                    "key": "cost",
                    "title": "代价层",
                    "headline": "能力的反噬点与收束方式",
                    "summary": cost_summary,
                    "points": cost_points,
                },
            ],
        }

    def _build_timeline_validation(
        self,
        birth_time_iso: str,
        birth_time_local: datetime,
        lat: float,
        lon: float,
        periods_data: list[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        if not self._is_huang_jinrong_sample(birth_time_iso, lat, lon):
            return None

        event_specs = [
            {
                "date": "1873-07-01T12:00:00",
                "date_label": "1873年",
                "title": "举家迁往上海",
                "category": "家庭迁移",
                "validation": "家庭、迁移与生存感成为早年主轴，适合用月亮主题来校验早期命运塑形。",
            },
            {
                "date": "1892-07-01T12:00:00",
                "date_label": "1892年",
                "title": "考入法租界巡捕房",
                "category": "进入制度平台",
                "validation": "通过关系、制度入口与更大的平台完成上升，正是这张盘最典型的扩张方式。",
            },
            {
                "date": "1924-07-01T12:00:00",
                "date_label": "1924年",
                "title": "升任督察长",
                "category": "公开地位抬升",
                "validation": "这一步不只是职位变化，而是社会可见度、资源调动权与公共身份同步抬升。",
            },
            {
                "date": "1927-04-12T12:00:00",
                "date_label": "1927年4月12日",
                "title": "参与四一二政变",
                "category": "组织与口径合流",
                "validation": "真正危险的地方不是单纯暴力，而是名单、口径、组织调度与政治站队合流。",
            },
            {
                "date": "1951-05-20T12:00:00",
                "date_label": "1951年5月20日",
                "title": "发表自白并扫街改造",
                "category": "晚年清算",
                "validation": "旧有结构进入回收期，幕后权力被公众评价和新秩序反向处理，代价层彻底显形。",
            },
        ]

        events: list[Dict[str, Any]] = []
        for spec in event_specs:
            event_dt = datetime.fromisoformat(spec["date"])
            age = (event_dt - birth_time_local).days / 365.2422
            period = self._find_period_for_age(periods_data, age)
            if not period:
                continue

            phase_range = f"{int(period['timing']['start_age'])}-{int(period['timing']['end_age'])}岁"
            lords = (
                f"{planet_label(period['lords']['major'])}/"
                f"{planet_label(period['lords']['sub']) if period['lords']['sub'] else '无'}"
            )
            events.append(
                {
                    "date_label": spec["date_label"],
                    "title": spec["title"],
                    "category": spec["category"],
                    "age_label": f"{int(age)}岁左右",
                    "phase_title": period["title"],
                    "phase_range": phase_range,
                    "phase_lords": lords,
                    "phase_summary": period["summary"],
                    "validation": spec["validation"],
                    "reading": (
                        f"对应阶段是{period['title']}，重心落在{period['astrology']['house_title']}，"
                        f"这和“{spec['category']}”形成了直接映射。"
                    ),
                }
            )

        return {
            "mode": "historical_validation",
            "title": "人生节点校验",
            "summary": "这个案例不看“你现在在哪一段”，而是用已知人生事件反推命盘结构和阶段逻辑是否成立。",
            "events": events,
        }

    def _build_advanced_patterns(
        self,
        birth_time_iso: str,
        lat: float,
        lon: float,
        natal_chart: Dict[str, Any],
        planet_profiles: Dict[Planet, Dict[str, Any]],
    ) -> Dict[str, Any]:
        house_rulers = self._build_house_ruler_map(natal_chart, planet_profiles)
        ruler_groups = self._build_ruler_groups(house_rulers, planet_profiles)
        core_threads = self._build_core_threads(house_rulers)
        reception_groups = self._build_reception_groups(planet_profiles)
        mutual_receptions = self._build_mutual_receptions(planet_profiles)
        derived_houses = self._build_derived_house_profiles(house_rulers)
        pattern_readings = self._build_pattern_readings(
            house_rulers=house_rulers,
            ruler_groups=ruler_groups,
            reception_groups=reception_groups,
            mutual_receptions=mutual_receptions,
            derived_houses=derived_houses,
            planet_profiles=planet_profiles,
        )
        case_themes: list[Dict[str, Any]] = []

        if self._is_huang_jinrong_sample(birth_time_iso, lat, lon):
            case_themes = self._build_huang_jinrong_case_themes(
                natal_chart=natal_chart,
                planet_profiles=planet_profiles,
                house_rulers=house_rulers,
                ruler_groups=ruler_groups,
                reception_groups=reception_groups,
                derived_houses=derived_houses,
            )

        return {
            "summary": "把几宫主飞几宫、同一行星统领哪些宫位，先拆成规则层，再进入现实语言解释。",
            "house_rulers": house_rulers,
            "ruler_groups": ruler_groups,
            "reception_groups": reception_groups,
            "mutual_receptions": mutual_receptions,
            "derived_houses": derived_houses,
            "core_threads": core_threads,
            "pattern_readings": pattern_readings,
            "case_themes": case_themes,
        }

    def _build_house_ruler_map(
        self,
        natal_chart: Dict[str, Any],
        planet_profiles: Dict[Planet, Dict[str, Any]],
    ) -> list[Dict[str, Any]]:
        houses = natal_chart.get("houses", [])
        results: list[Dict[str, Any]] = []

        for item in houses:
            try:
                sign = Sign(item["sign"])
                ruler = SIGN_RULERS[sign]
            except Exception:
                continue

            profile = planet_profiles.get(ruler)
            if not profile:
                continue

            results.append(
                {
                    "house": item["house"],
                    "title": item["title"],
                    "sign": item["sign"],
                    "sign_label": item.get("sign_label") or sign_label(sign),
                    "ruler": ruler.value,
                    "ruler_label": planet_label(ruler),
                    "ruler_house": profile["house"],
                    "ruler_house_title": profile["house_title"],
                    "ruler_sign": profile["sign"],
                    "ruler_sign_label": profile["sign_label"],
                    "dignity": profile["dignity"],
                    "dignity_label": profile["dignity_label"],
                    "adult_meaning": HOUSE_ADULT_MEANINGS.get(item["house"], {}).get("adult", item["title"]),
                    "notation": f"{item['house']}R",
                    "line": f"{item['house']}R {planet_label(ruler)}飞{profile['house']}宫",
                }
            )
        return results

    def _build_ruler_groups(
        self,
        house_rulers: list[Dict[str, Any]],
        planet_profiles: Dict[Planet, Dict[str, Any]],
    ) -> list[Dict[str, Any]]:
        grouped: Dict[str, list[Dict[str, Any]]] = {}
        for item in house_rulers:
            grouped.setdefault(item["ruler"], []).append(item)

        results: list[Dict[str, Any]] = []
        for ruler_value, items in grouped.items():
            items.sort(key=lambda value: value["house"])
            try:
                profile = planet_profiles.get(Planet(ruler_value))
            except Exception:
                profile = None
            if not profile:
                continue

            house_numbers = [item["house"] for item in items]
            notation = "/".join(f"{house}R" for house in house_numbers)
            results.append(
                {
                    "ruler": ruler_value,
                    "ruler_label": items[0]["ruler_label"],
                    "houses": house_numbers,
                    "house_titles": [item["title"] for item in items],
                    "notation": notation,
                    "line": f"{notation} {items[0]['ruler_label']}飞{profile['house']}宫",
                    "ruler_house": profile["house"],
                    "ruler_house_title": profile["house_title"],
                    "ruler_sign": profile["sign"],
                    "ruler_sign_label": profile["sign_label"],
                    "dignity": profile["dignity"],
                    "dignity_label": profile["dignity_label"],
                }
            )

        results.sort(key=lambda value: min(value["houses"]) if value["houses"] else 99)
        return results

    def _build_core_threads(self, house_rulers: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
        selected_houses = [1, 2, 3, 7, 10, 12]
        selected_map = {item["house"]: item for item in house_rulers}
        threads: list[Dict[str, Any]] = []

        for house in selected_houses:
            item = selected_map.get(house)
            if not item:
                continue

            threads.append(
                {
                    "house": house,
                    "title": f"{item['notation']} {item['ruler_label']}飞{item['ruler_house']}宫",
                    "summary": (
                        f"{item['title']}不会停留在抽象层，而会通过{item['ruler_house_title']}显形。"
                    ),
                    "points": [
                        f"{item['title']}的成人社会义是：{item['adult_meaning']}。",
                        f"宫主{item['ruler_label']}落在第{item['ruler_house']}宫 {item['ruler_house_title']}，所以这条线会通过具体场景运作。",
                        f"先天状态为{item['dignity_label']}，这会影响这条线是顺手放大，还是带着代价运作。",
                    ],
                }
            )
        return threads

    def _build_reception_groups(
        self,
        planet_profiles: Dict[Planet, Dict[str, Any]],
    ) -> list[Dict[str, Any]]:
        grouped: Dict[Planet, list[Dict[str, Any]]] = {}

        for planet, profile in planet_profiles.items():
            try:
                guest_sign = Sign(profile["sign"])
                receiver = SIGN_RULERS[guest_sign]
            except Exception:
                continue

            if receiver == planet:
                continue

            grouped.setdefault(receiver, []).append(
                {
                    "planet": planet.value,
                    "label": profile["label"],
                    "house": profile["house"],
                    "house_title": profile["house_title"],
                    "sign": profile["sign"],
                    "sign_label": profile["sign_label"],
                }
            )

        results: list[Dict[str, Any]] = []
        for receiver, guests in grouped.items():
            receiver_profile = planet_profiles.get(receiver)
            if not receiver_profile:
                continue

            guest_labels = [item["label"] for item in guests]
            results.append(
                {
                    "receiver": receiver.value,
                    "receiver_label": planet_label(receiver),
                    "receiver_house": receiver_profile["house"],
                    "receiver_house_title": receiver_profile["house_title"],
                    "receiver_sign": receiver_profile["sign"],
                    "receiver_sign_label": receiver_profile["sign_label"],
                    "guests": guests,
                    "line": f"{planet_label(receiver)}接纳{'/'.join(guest_labels)}",
                    "summary": (
                        f"{planet_label(receiver)}会接住落在其守护星座内的议题，"
                        f"并把它们带到第{receiver_profile['house']}宫 {receiver_profile['house_title']}去运作。"
                    ),
                }
            )

        results.sort(key=lambda item: (-len(item["guests"]), item["receiver_label"]))
        return results

    def _build_mutual_receptions(
        self,
        planet_profiles: Dict[Planet, Dict[str, Any]],
    ) -> list[Dict[str, Any]]:
        results: list[Dict[str, Any]] = []
        seen: set[tuple[str, str]] = set()
        planets = list(planet_profiles.keys())

        for planet_a in planets:
            profile_a = planet_profiles.get(planet_a)
            if not profile_a:
                continue
            try:
                ruler_of_a = SIGN_RULERS[Sign(profile_a["sign"])]
            except Exception:
                continue

            for planet_b in planets:
                if planet_a == planet_b:
                    continue
                profile_b = planet_profiles.get(planet_b)
                if not profile_b:
                    continue
                try:
                    ruler_of_b = SIGN_RULERS[Sign(profile_b["sign"])]
                except Exception:
                    continue

                if ruler_of_a != planet_b or ruler_of_b != planet_a:
                    continue

                key = tuple(sorted([planet_a.value, planet_b.value]))
                if key in seen:
                    continue
                seen.add(key)

                results.append(
                    {
                        "pair": [planet_a.value, planet_b.value],
                        "labels": [planet_label(planet_a), planet_label(planet_b)],
                        "line": f"{planet_label(planet_a)} 与 {planet_label(planet_b)} 互溶",
                        "summary": (
                            f"{planet_label(planet_a)}与{planet_label(planet_b)}互相进入对方守护的星座，"
                            "意味着这两条线会互相借力。"
                        ),
                    }
                )

        return results

    def _build_derived_house_profiles(
        self,
        house_rulers: list[Dict[str, Any]],
    ) -> list[Dict[str, Any]]:
        house_map = {item["house"]: item for item in house_rulers}
        configs = [
            {
                "base_house": 7,
                "base_label": "伴侣",
                "checks": [
                    (1, "伴侣本人"),
                    (2, "伴侣的钱财"),
                    (9, "伴侣的信念"),
                    (10, "伴侣的事业"),
                    (12, "伴侣的隐藏代价"),
                ],
            },
            {
                "base_house": 10,
                "base_label": "事业",
                "checks": [
                    (1, "事业本身"),
                    (2, "事业的钱"),
                    (7, "事业的合作/对手"),
                    (12, "事业的隐性代价"),
                ],
            },
            {
                "base_house": 2,
                "base_label": "财富",
                "checks": [
                    (1, "财富本身"),
                    (5, "财富的投机与扩张"),
                    (7, "财富的合作绑定"),
                    (12, "财富的隐形代价"),
                ],
            },
        ]

        results: list[Dict[str, Any]] = []
        for config in configs:
            links: list[Dict[str, Any]] = []
            for derived_house, label in config["checks"]:
                radical_house = self._turned_house(config["base_house"], derived_house)
                target = house_map.get(radical_house)
                if not target:
                    continue

                links.append(
                    {
                        "label": label,
                        "derived_house": derived_house,
                        "radical_house": radical_house,
                        "title": target["title"],
                        "adult_meaning": target["adult_meaning"],
                        "line": f"{label}看本盘第{radical_house}宫",
                        "ruler_line": target["line"],
                    }
                )

            results.append(
                {
                    "base_house": config["base_house"],
                    "base_label": config["base_label"],
                    "summary": (
                        f"转宫不是单看{config['base_label']}宫位本身，"
                        f"还要看围绕{config['base_label']}展开的信念、事业、资源与隐藏代价。"
                    ),
                    "links": links,
                }
            )

        return results

    def _turned_house(self, base_house: int, derived_house: int) -> int:
        return ((base_house + derived_house - 2) % 12) + 1

    def _build_pattern_readings(
        self,
        house_rulers: list[Dict[str, Any]],
        ruler_groups: list[Dict[str, Any]],
        reception_groups: list[Dict[str, Any]],
        mutual_receptions: list[Dict[str, Any]],
        derived_houses: list[Dict[str, Any]],
        planet_profiles: Dict[Planet, Dict[str, Any]],
    ) -> list[Dict[str, Any]]:
        house_map = {item["house"]: item for item in house_rulers}
        group_map = {item["ruler"]: item for item in ruler_groups}
        reception_map = {item["receiver"]: item for item in reception_groups}
        derived_map = {item["base_house"]: item for item in derived_houses}
        cards: list[Dict[str, Any]] = []

        identity = house_map.get(1)
        career = house_map.get(10)
        if identity and career:
            identity_profile = self._planet_profile_by_value(planet_profiles, identity["ruler"])
            same_ruler = identity["ruler"] == career["ruler"]
            identity_reception = reception_map.get(identity["ruler"])

            evidence = [identity["line"], career["line"]]
            if same_ruler:
                group = group_map.get(identity["ruler"])
                if group:
                    evidence.append(group["line"])
            if identity_reception:
                evidence.append(identity_reception["line"])
            if identity_profile:
                evidence.append(f"{identity['ruler_label']}{identity_profile['dignity_label']}")

            points = [
                f"1宫主 {identity['ruler_label']} 落在第{identity['ruler_house']}宫 {identity['ruler_house_title']}，说明你本人会通过这类现实场景被定义。",
                f"10宫主 {career['ruler_label']} 落在第{career['ruler_house']}宫 {career['ruler_house_title']}，事业和公开位置会顺着这条线被社会看见。",
                (
                    "1宫和10宫由同一颗星统领，个人风格、职业路径与社会身份天然绑在一起。"
                    if same_ruler
                    else "1宫和10宫分属不同主星，说明“你是谁”和“你如何成事”需要两套方法协同。"
                ),
            ]
            if identity_profile:
                points.append(
                    f"{identity['ruler_label']}先天状态为{identity_profile['dignity_label']}，"
                    f"{self._dignity_flow_text(identity_profile['dignity'])}"
                )
            if identity_reception:
                guest_topics = self._format_reception_topics(identity_reception, group_map)
                points.append(
                    f"{identity['ruler_label']}还接住了{guest_topics}这些课题，命主线不会只处理自我，还会把更多宫位议题一起卷进现实。"
                )

            cards.append(
                {
                    "key": "core_axis",
                    "title": "命主线与事业线",
                    "summary": (
                        "这张盘先看 1宫主 怎么落地，再看 10宫主 怎么显化。"
                        "它决定了命主是把自己活成事业，还是需要先分清人设与职业。"
                    ),
                    "evidence": self._unique_strings(evidence),
                    "points": points,
                }
            )

        alliance = house_map.get(7)
        spouse_profile = derived_map.get(7)
        if alliance:
            alliance_profile = self._planet_profile_by_value(planet_profiles, alliance["ruler"])
            alliance_reception = reception_map.get(alliance["ruler"])
            spouse_links = {item["derived_house"]: item for item in spouse_profile.get("links", [])} if spouse_profile else {}

            evidence = [alliance["line"]]
            if alliance_reception:
                evidence.append(alliance_reception["line"])
            for derived_house in (1, 9, 10):
                link = spouse_links.get(derived_house)
                if link:
                    evidence.append(link["line"])

            points = [
                f"7宫主 {alliance['ruler_label']} 落在第{alliance['ruler_house']}宫 {alliance['ruler_house_title']}，伴侣、合作、贵人和公开对手会通过这类场景进入命运。",
                "7宫不只讲婚姻，也讲你会通过哪类人进入更大的系统、平台和资源网络。",
            ]
            if alliance_profile:
                points.append(
                    f"7宫主先天状态为{alliance_profile['dignity_label']}，"
                    f"{self._dignity_flow_text(alliance_profile['dignity'])}"
                )
            if alliance_reception:
                guest_topics = self._format_reception_topics(alliance_reception, group_map)
                points.append(
                    f"{alliance['ruler_label']}接纳了{guest_topics}，说明联盟关系不会只带来感情或合约，也会连带更多资源和任务一起进场。"
                )
            if spouse_links:
                partner_self = spouse_links.get(1)
                partner_belief = spouse_links.get(9)
                partner_career = spouse_links.get(10)
                details: list[str] = []
                if partner_self:
                    details.append(f"伴侣本人看本盘第{partner_self['radical_house']}宫")
                if partner_belief:
                    details.append(f"伴侣的信念看本盘第{partner_belief['radical_house']}宫")
                if partner_career:
                    details.append(f"伴侣的事业看本盘第{partner_career['radical_house']}宫")
                if details:
                    points.append(f"转宫继续展开时，{'；'.join(details)}，所以这类关系会深度卷入你的现实结构。")

            cards.append(
                {
                    "key": "alliance_axis",
                    "title": "7宫助力与联盟入口",
                    "summary": "7宫决定你如何借别人上桌。对很多盘来说，真正的抬升并不来自单打独斗，而来自伴侣、合作、贵人和对手。",
                    "evidence": self._unique_strings(evidence),
                    "points": points,
                }
            )

        wealth = house_map.get(2)
        speculative = house_map.get(5)
        shared = house_map.get(8)
        wealth_profile = derived_map.get(2)
        if wealth and speculative and shared:
            wealth_planet = self._planet_profile_by_value(planet_profiles, wealth["ruler"])
            evidence = [wealth["line"], speculative["line"], shared["line"]]
            if wealth_planet:
                evidence.append(f"{wealth['ruler_label']}{wealth_planet['dignity_label']}")
            if wealth_profile:
                wealth_links = {item["derived_house"]: item for item in wealth_profile.get("links", [])}
                for derived_house in (5, 7, 12):
                    link = wealth_links.get(derived_house)
                    if link:
                        evidence.append(link["line"])

            points = [
                f"2宫主 {wealth['ruler_label']} 落在第{wealth['ruler_house']}宫 {wealth['ruler_house_title']}，说明你的钱会通过这类场景进入和流动。",
                f"5宫主 {speculative['ruler_label']} 落在第{speculative['ruler_house']}宫 {speculative['ruler_house_title']}，投机、创作、名气或让人上头的东西怎么参与财富，会看这条线。",
                f"8宫主 {shared['ruler_label']} 落在第{shared['ruler_house']}宫 {shared['ruler_house_title']}，共享资源、债务、利益绑定与灰度成本也会从这里进入。",
            ]
            if wealth_planet:
                points.append(
                    f"2宫主先天状态为{wealth_planet['dignity_label']}，"
                    f"{self._dignity_flow_text(wealth_planet['dignity'])}"
                )
            if alliance and wealth["ruler"] == alliance["ruler"]:
                points.append("2宫与7宫同主，钱和伴侣、合作、客户、契约的绑定度通常比较高。")
            if career and wealth["ruler"] == career["ruler"]:
                points.append("2宫与10宫同主，财富和事业往往是同一条路，能不能赚到钱取决于能不能把职业位置做成资源入口。")

            cards.append(
                {
                    "key": "wealth_axis",
                    "title": "财富结构",
                    "summary": "财路不只看 2宫。真正的财富结构要同时看 2宫的变现能力、5宫的扩张方式、8宫的绑定与代价。",
                    "evidence": self._unique_strings(evidence),
                    "points": points,
                }
            )

        if spouse_profile and alliance:
            spouse_links = {item["derived_house"]: item for item in spouse_profile.get("links", [])}
            evidence = [alliance["line"]]
            for derived_house in (1, 2, 9, 10, 12):
                link = spouse_links.get(derived_house)
                if link:
                    evidence.append(link["line"])

            points = []
            for derived_house in (1, 2, 9, 10, 12):
                link = spouse_links.get(derived_house)
                if not link:
                    continue
                points.append(
                    f"{link['label']}看本盘第{link['radical_house']}宫 {link['title']}，说明这段关系会把“{link['adult_meaning']}”这类现实议题带进来。"
                )
            points.append("所以 7宫不是单看对象性格，而是看你最容易通过哪类人形成稳定的借力、绑定与代价。")

            cards.append(
                {
                    "key": "partner_profile",
                    "title": "伴侣/合作方画像",
                    "summary": "转宫的价值，在于把“对象本人、对象的钱、对象的信念、对象的事业、对象的隐性代价”拆开看，而不是把7宫压扁成单一情感标签。",
                    "evidence": self._unique_strings(evidence),
                    "points": points,
                }
            )

        hidden = house_map.get(12)
        if hidden:
            hidden_profile = self._planet_profile_by_value(planet_profiles, hidden["ruler"])
            hidden_reception = reception_map.get(hidden["ruler"])
            related_mutuals = [
                item["line"]
                for item in mutual_receptions
                if hidden["ruler"] in item.get("pair", [])
            ]
            evidence = [hidden["line"]]
            if shared:
                evidence.append(shared["line"])
            if hidden_reception:
                evidence.append(hidden_reception["line"])
            evidence.extend(related_mutuals[:2])

            shared_axes: list[str] = []
            for house in (1, 7, 10):
                item = house_map.get(house)
                if item and item["ruler"] == hidden["ruler"] and house != 12:
                    shared_axes.append(f"{house}宫")

            points = [
                f"12宫主 {hidden['ruler_label']} 落在第{hidden['ruler_house']}宫 {hidden['ruler_house_title']}，幕后运作、隐线压力、清算与收束会通过这里出现。",
            ]
            if hidden_profile:
                points.append(
                    f"12宫主先天状态为{hidden_profile['dignity_label']}，"
                    f"{self._dignity_flow_text(hidden_profile['dignity'])}"
                )
            if shared_axes:
                points.append(f"12宫主同时还统领{self._format_house_number_list(shared_axes)}，说明明线课题和幕后代价是绑在一起的。")
            if hidden_reception:
                guest_topics = self._format_reception_topics(hidden_reception, group_map)
                points.append(f"{hidden['ruler_label']}还接纳了{guest_topics}，所以台面下的问题不会孤立存在，而会和更多生活领域连成系统。")
            if related_mutuals:
                points.append("一旦12宫主参与互溶，往往代表明线与暗线会互相借力，也意味着后期更难完全切割代价。")

            cards.append(
                {
                    "key": "hidden_cost",
                    "title": "幕后结构与后期代价",
                    "summary": "12宫不是一句“潜意识”就能带过。它更像台面下的系统、收尾机制、隐形敌人，以及后期要被回收的代价。",
                    "evidence": self._unique_strings(evidence),
                    "points": points,
                }
            )

        return cards

    def _planet_profile_by_value(
        self,
        planet_profiles: Dict[Planet, Dict[str, Any]],
        planet_value: str,
    ) -> Optional[Dict[str, Any]]:
        try:
            return planet_profiles.get(Planet(planet_value))
        except Exception:
            return None

    def _format_reception_topics(
        self,
        reception_group: Dict[str, Any],
        group_map: Dict[str, Dict[str, Any]],
    ) -> str:
        topics: list[str] = []
        for guest in reception_group.get("guests", []):
            group = group_map.get(guest["planet"])
            topics.append(group["notation"] if group else guest["label"])
        unique_topics = self._unique_strings(topics)
        return "、".join(unique_topics[:4]) if unique_topics else "其他宫位课题"

    def _dignity_flow_text(self, dignity_code: str) -> str:
        mapping = {
            "domicile": "这条线比较稳，做起来更像顺手放大。",
            "exaltation": "这条线容易被放大和看见，但也更容易被寄予高期待。",
            "peregrine": "这条线更依赖后天环境、方法和所处平台来定胜负。",
            "detriment": "这条线能成事，但常常要靠失衡、代价或绕路来推进。",
            "fall": "这条线先天吃力，往往需要托举、补位或付出明显代价。",
        }
        return mapping.get(dignity_code, "这条线需要放回具体环境里判断。")

    def _unique_strings(self, values: Iterable[str]) -> list[str]:
        results: list[str] = []
        seen: set[str] = set()
        for item in values:
            if not item or item in seen:
                continue
            seen.add(item)
            results.append(item)
        return results

    def _format_house_number_list(self, values: Iterable[str]) -> str:
        items = [item for item in values if item]
        if not items:
            return ""
        if len(items) == 1:
            return items[0]
        return "、".join(items[:-1]) + "和" + items[-1]

    def _build_huang_jinrong_case_themes(
        self,
        natal_chart: Dict[str, Any],
        planet_profiles: Dict[Planet, Dict[str, Any]],
        house_rulers: list[Dict[str, Any]],
        ruler_groups: list[Dict[str, Any]],
        reception_groups: list[Dict[str, Any]],
        derived_houses: list[Dict[str, Any]],
    ) -> list[Dict[str, Any]]:
        group_map = {item["ruler"]: item for item in ruler_groups}
        reception_map = {item["receiver"]: item for item in reception_groups}
        spouse_profile = derived_houses[0] if derived_houses else None

        mercury_group = group_map.get(Planet.MERCURY.value)
        jupiter_group = group_map.get(Planet.JUPITER.value)
        venus_group = group_map.get(Planet.VENUS.value)
        saturn_group = group_map.get(Planet.SATURN.value)
        mars_group = group_map.get(Planet.MARS.value)
        moon_group = group_map.get(Planet.MOON.value)
        sun_group = group_map.get(Planet.SUN.value)

        mercury_profile = planet_profiles.get(Planet.MERCURY, {})
        venus_profile = planet_profiles.get(Planet.VENUS, {})
        mars_profile = planet_profiles.get(Planet.MARS, {})

        return [
            {
                "key": "nobility",
                "title": "得贵格局",
                "summary": "先天不是轻松命，后天靠7宫木星与联盟结构托举上位，属于典型的后天得贵。",
                "evidence": [
                    mercury_group["line"] if mercury_group else "1R/10R 水星飞3宫",
                    jupiter_group["line"] if jupiter_group else "4R/7R 木星飞7宫",
                    sun_group["line"] if sun_group else "12R 太阳飞3宫",
                    reception_map.get(Planet.JUPITER.value, {}).get("line", "木星接纳太阳/水星/土星"),
                    f"水星{mercury_profile.get('dignity_label', '失势')}" if mercury_profile else "水星失势",
                ],
                "points": [
                    "命主水星既主1宫也主10宫，却落在3宫且先天失势，说明不是门第型、清望型的轻松贵命。",
                    "真正的抬升点来自7宫木星：贵气不是自己天然带来的，而是通过贵人、伴侣、联盟和更大的制度平台后天形成。",
                    "木星把落在自己星座里的太阳、水星、土星接住，再把这些议题带去7宫运作，所以得贵不是空话，而是有人托、有人带、有人接。",
                    "这类贵不是清贵，而是势贵：先借人、借系统、借关系，后把借来的势做成自己的位置。",
                ],
            },
            {
                "key": "seventh_house_support",
                "title": "7宫助力",
                "summary": "7宫不是单纯婚姻，而是最强的托举口。伴侣、贵人、兄弟网络都会从这里进来。",
                "evidence": [
                    jupiter_group["line"] if jupiter_group else "4R/7R 木星飞7宫",
                    saturn_group["line"] if saturn_group else "5R/6R 土星飞3宫",
                    moon_group["line"] if moon_group else "11R 月亮飞3宫",
                    mercury_group["line"] if mercury_group else "10R 水星飞3宫",
                    spouse_profile["links"][2]["line"] if spouse_profile and len(spouse_profile["links"]) > 2 else "伴侣的信念看本盘第3宫",
                ],
                "points": [
                    "7R 木星飞7，本身就说明伴侣、盟友、保护关系、门生网络是成事入口，不只是情感配置。",
                    "7宫木星不只接住命主，也间接带动事业宫，所以伴侣和联盟对事业抬升有实质帮助。",
                    "11宫月亮飞3宫，朋友、团队、兄弟感和信息网络连在一起，容易形成讲义气、重关系的帮会式结构。",
                ],
            },
            {
                "key": "wealth",
                "title": "财富格局",
                "summary": "有挣钱格局，也有大进大出的格局。能把资源做成钱，但守财和留财不强。",
                "evidence": [
                    venus_group["line"] if venus_group else "2R/9R 金星飞2宫",
                    saturn_group["line"] if saturn_group else "5R/6R 土星飞3宫",
                    mars_group["line"] if mars_group else "3R/8R 火星飞12宫",
                    f"金星{venus_profile.get('dignity_label', '失势')}" if venus_profile else "金星失势",
                ],
                "points": [
                    "2R/9R 金星飞2宫，说明他有财富嗅觉，也懂得把关系、欲望、资源和现实收益绑成钱。",
                    "但金星先天失势，财富不是干净稳态的累积，更像大进大出、能挣但不容易真正留下。",
                    "5R/6R 土星和 3R/8R 火星把投机财、辛苦财、暗财、灰度财连在一起，所以财路往往和技能、跑动、娱乐、地下资源有关。",
                ],
            },
            {
                "key": "dual_system",
                "title": "黑白通吃",
                "summary": "这张盘最大的本事，不是单一权威，而是在台面上和台面下都能运作。",
                "evidence": [
                    mercury_group["line"] if mercury_group else "1R/10R 水星飞3宫",
                    mars_group["line"] if mars_group else "3R/8R 火星飞12宫",
                    sun_group["line"] if sun_group else "12R 太阳飞3宫",
                    "水星合土星",
                ],
                "points": [
                    "1R/10R 水星飞3宫，身份与事业都靠消息、口才、名单、交通、传递、组织网络运作。",
                    "3R/8R 火星飞12宫，说明沟通、风险、暗财、暴力和幕后操作天然有链路，不是完全分开的系统。",
                    "12R 太阳飞3宫又让幕后资源、隐性保护和台面上的说法绑在一起，所以能同时打通黑白两面。",
                ],
            },
            {
                "key": "career",
                "title": "事业暗线",
                "summary": "事业不是常规体制型上升，而是信息、差事、规则边缘和联盟关系推动出来的。",
                "evidence": [
                    mercury_group["line"] if mercury_group else "10R 水星飞3宫",
                    jupiter_group["line"] if jupiter_group else "7R 木星飞7宫",
                    saturn_group["line"] if saturn_group else "6R 土星飞3宫",
                    "木星拱土星",
                ],
                "points": [
                    "10R 水星飞3宫，事业抬升不是靠纯名望，而是靠能跑、能说、能接线、能调度人和规则。",
                    "6R 土星飞3宫说明技能、学徒、劳苦、执行力都和事业底盘绑在一起，先苦后抬升。",
                    "7宫木星再把事业接进联盟和贵人系统，所以职业线经常不是单兵突破，而是被带着往上走。",
                ],
            },
            {
                "key": "marriage",
                "title": "婚姻与外缘",
                "summary": "正宫关系是托举型的，但外缘不会少，婚姻里容易出现隐藏人物与台面下关系。",
                "evidence": [
                    jupiter_group["line"] if jupiter_group else "7R 木星飞7宫",
                    sun_group["line"] if sun_group else "12R 太阳飞3宫",
                    saturn_group["line"] if saturn_group else "5R 土星飞3宫",
                    mars_group["line"] if mars_group else "8R 火星飞12宫",
                    spouse_profile["links"][3]["line"] if spouse_profile and len(spouse_profile["links"]) > 3 else "伴侣的事业看本盘第4宫",
                ],
                "points": [
                    "7R 木星飞7先说明正宫本身有托举、包容和带平台的力量，婚姻不是完全失序的。",
                    "但12宫不断被带进婚姻与社交链路，说明关系里会有隐藏人、暗线、看不见的外部因素。",
                    "5宫和8宫又都牵到12宫，所以短桃花、露水关系、外面有人这类题目更像盘主自己带出来的结构性问题。",
                ],
            },
            {
                "key": "spouse_profile",
                "title": "伴侣画像",
                "summary": "伴侣不是弱角色，更像托举型、包容型、有理想感的人。",
                "evidence": [
                    jupiter_group["line"] if jupiter_group else "7R 木星飞7宫",
                    spouse_profile["links"][0]["line"] if spouse_profile and spouse_profile["links"] else "伴侣本人看本盘第7宫",
                    spouse_profile["links"][2]["line"] if spouse_profile and len(spouse_profile["links"]) > 2 else "伴侣的信念看本盘第3宫",
                    spouse_profile["links"][3]["line"] if spouse_profile and len(spouse_profile["links"]) > 3 else "伴侣的事业看本盘第4宫",
                ],
                "points": [
                    "7宫自己就很强，说明伴侣不是边缘人物，而是能独立成事、能提供平台的人。",
                    "伴侣的信念看本盘第3宫，那里群星集中，说明她身上带着强烈的理念感、讲法、信念与价值判断。",
                    "伴侣的事业与外部位置再看转宫，也能看到她并不是单纯依附型，而是具备实际托举和资源调动能力的人。",
                ],
            },
            {
                "key": "reckoning",
                "title": "晚年清算",
                "summary": "前半生靠幕后、暗线和制度缝隙成事，后半生也容易被这些东西反向回收。",
                "evidence": [
                    mars_group["line"] if mars_group else "8R 火星飞12宫",
                    sun_group["line"] if sun_group else "12R 太阳飞3宫",
                    mercury_group["line"] if mercury_group else "1R/10R 水星飞3宫",
                    f"火星落{mars_profile.get('house_title', '12宫')}" if mars_profile else "火星落12宫",
                ],
                "points": [
                    "12宫在这张盘里不是纯隐退，而是幕后运作、清算、监禁、隐形敌人与回收机制。",
                    "前面那些台面下的助力，在得势时叫保护伞和资源；失势时就会变成公众评价、名单、羞辱和清算。",
                    "所以这是典型的前半生借势，后半生回收的结构盘，晚年很难完全脱离前面留下的因果。",
                ],
            },
        ]

    def _find_period_for_age(
        self,
        periods_data: list[Dict[str, Any]],
        age: float,
    ) -> Optional[Dict[str, Any]]:
        for period in periods_data:
            start_age = period["timing"]["start_age"]
            end_age = period["timing"]["end_age"]
            if start_age <= age < end_age:
                return period
        return None

    def _is_huang_jinrong_sample(self, birth_time_iso: str, lat: float, lon: float) -> bool:
        normalized_time = birth_time_iso.strip()
        return (
            normalized_time.startswith("1868-12-14T00:01")
            and abs(lat - 30.05) < 0.02
            and abs(lon - 121.1667) < 0.02
        )

    def _build_role_title(
        self,
        natal_chart: Dict[str, Any],
        planet_profiles: Dict[Planet, Dict[str, Any]],
        is_historical_sample: bool = False,
    ) -> str:
        if is_historical_sample:
            return "信息操盘型权力人物"

        top_houses = [item["house"] for item in natal_chart.get("house_emphasis", [])]
        chart_ruler = natal_chart.get("chart_ruler")
        if 3 in top_houses and chart_ruler == Planet.MERCURY.value:
            if 7 in top_houses or any(profile["house"] == 7 for profile in planet_profiles.values()):
                return "关系网络型操盘者"
            if 12 in top_houses or any(profile["house"] == 12 for profile in planet_profiles.values()):
                return "隐性控制型组织者"
            return "信息整合型推进者"
        if 7 in top_houses:
            return "联盟扩张型整合者"
        if 10 in top_houses:
            return "公开角色型推进者"
        return f"{natal_chart['chart_ruler_label']}主导型人生角色"

    def _build_role_keywords(self, natal_chart: Dict[str, Any]) -> list[str]:
        keywords: list[str] = []
        for item in natal_chart.get("house_emphasis", [])[:4]:
            meaning = HOUSE_ADULT_MEANINGS.get(item["house"], {}).get("adult")
            if meaning:
                keywords.append(meaning)
        return keywords[:4]

    def _format_house_titles(self, houses: list[Dict[str, Any]]) -> str:
        if not houses:
            return "关键宫位"
        return "、".join(item["title"] for item in houses)

    def _format_house_adult_meanings(self, houses: list[Dict[str, Any]]) -> str:
        if not houses:
            return "基础社会议题"
        items = []
        for item in houses:
            meaning = HOUSE_ADULT_MEANINGS.get(item["house"], {}).get("adult", item["title"])
            items.append(f"{item['title']}（{meaning}）")
        return "；".join(items)

    def _build_life_model(
        self,
        chart: Any,
        natal_chart: Dict[str, Any],
        periods_data: list[Dict[str, Any]],
        current_phase: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        dominant = natal_chart.get("dominant_planets", [])
        houses = natal_chart.get("house_emphasis", [])
        strongest = dominant[:2]
        pressure_points = natal_chart.get("pressure_points", [])
        best_periods = sorted(periods_data, key=lambda item: item["trend"]["bonus_coefficient"], reverse=True)[:3]
        reset_periods = sorted(periods_data, key=lambda item: item["trend"]["bonus_coefficient"])[:2]

        title = self._life_model_title(dominant, natal_chart)
        core_themes = [
            f"{item['title']}是人生主轴" for item in houses[:3]
        ]
        strengths = [item["reason"] for item in strongest]
        challenges = [item["reason"] for item in pressure_points]
        growth_path = self._growth_path_lines(natal_chart, houses, pressure_points)
        strategy = self._strategy_lines(current_phase, strongest)

        return {
            "title": title,
            "summary": natal_chart["signature"],
            "core_themes": core_themes,
            "strengths": strengths,
            "challenges": challenges,
            "growth_path": growth_path,
            "strategy": strategy,
            "peak_windows": [
                {
                    "age_range": f"{int(item['timing']['start_age'])}-{int(item['timing']['end_age'])}岁",
                    "lords": f"{planet_label(item['lords']['major'])}/{planet_label(item['lords']['sub']) if item['lords']['sub'] else '无'}",
                    "summary": item["summary"],
                }
                for item in best_periods
            ],
            "reset_windows": [
                {
                    "age_range": f"{int(item['timing']['start_age'])}-{int(item['timing']['end_age'])}岁",
                    "lords": f"{planet_label(item['lords']['major'])}/{planet_label(item['lords']['sub']) if item['lords']['sub'] else '无'}",
                    "summary": item["summary"],
                }
                for item in reset_periods
            ],
        }

    def _life_model_title(self, dominant: list[Dict[str, Any]], natal_chart: Dict[str, Any]) -> str:
        asc_label = natal_chart["ascendant"]["sign_label"]
        ruler_label = natal_chart["chart_ruler_label"]
        dominant_labels = " / ".join(item["label"] for item in dominant[:2]) if dominant else ruler_label
        return f"{asc_label}上升 · {dominant_labels} 主导型人生模型"

    def _growth_path_lines(
        self,
        natal_chart: Dict[str, Any],
        houses: list[Dict[str, Any]],
        pressure_points: list[Dict[str, Any]],
    ) -> list[str]:
        lines = []
        if houses:
            lines.append(
                f"先把{houses[0]['title']}做成稳定结构，再去追求更大的舞台和结果。"
            )
        if pressure_points:
            lines.append(
                f"对{pressure_points[0]['label']}的课题，不能只靠天赋，应建立规则、边界与复盘机制。"
            )
        lines.append(
            f"命主星是{natal_chart['chart_ruler_label']}，真正的跃迁来自持续经营而不是偶发爆发。"
        )
        return lines

    def _strategy_lines(
        self,
        current_phase: Optional[Dict[str, Any]],
        strongest: list[Dict[str, Any]],
    ) -> list[str]:
        lines: list[str] = []
        if current_phase:
            lines.append(
                f"当前阶段优先处理{current_phase['dominant_domains'][0]['label']}，这是此刻最能带动全局的入口。"
            )
            lines.extend(current_phase["action_focus"][:2])
        if strongest:
            lines.append(
                f"长期来看，要让{strongest[0]['label']}的优势变成可复制的方法，而不是只在状态好时才出现。"
            )
        return lines[:4]

    def _absolute_longitude(self, info: Any) -> float:
        longitude = getattr(info, "longitude", 0.0)
        if longitude:
            return float(longitude) % 360.0
        sign = getattr(info, "sign")
        degree = getattr(info, "degree", 0.0)
        sign_index = list(Sign).index(sign)
        return sign_index * 30.0 + degree
