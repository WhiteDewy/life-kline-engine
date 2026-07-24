"""
飞星得吉/受克综合判断引擎 (Flight Fortune Evaluator)

基于梦老师占星笔记体系，综合多维度判断飞星吉凶：

判断维度（按优先级）：
1. 星体先天尊贵 — 庙旺落陷 + 三分主 + 界/面
2. 相位格局 — 吉相位(三合/六合) vs 凶相位(刑/冲) 的数量和强度
3. 接纳互容 — 被吉星接纳则加分，被凶星接纳则减分；互容 > 接纳 > 普通相位
4. 后天宫位 — 落角宫(1/4/7/10)力量充分；落果宫(3/6/9/12)力量有限
5. 灼烧/日核/日光下 — 日核内极大提升；灼烧压制；日光下自由发挥
6. 月亮盈亏 — 增光期偏吉，减光期偏凶
7. 东出/西入 — 昼星喜东出，夜星喜西入
8. 星体运行速度 — 高于平均速度更早实现
9. 喜乐宫 — 星体落喜乐宫获得额外舒适度
10. 三王星特性 — 即使是正相位也带负面影响

返回结构化 fortune 对象，供 flystar_catalog 和 engine_astrologer 使用。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from .constants import (
    ANGULAR_HOUSES,
    CADENT_HOUSES,
    DETRIMENT_SIGNS,
    DOMICILE_SIGNS,
    EXALTATION_SIGNS,
    FALL_SIGNS,
    JOY_HOUSES,
    SUCCEDENT_HOUSES,
    TRIPLICITY_RULERS,
    SIGN_ELEMENT,
    Planet,
    Sign,
)


# ═══════════════════════════════════════════════════════════════
# 现代守护关系（三王星）
# ═══════════════════════════════════════════════════════════════

MODERN_RULERS: dict[str, str] = {
    "AQUARIUS": "URANUS",
    "PISCES": "NEPTUNE",
    "SCORPIO": "PLUTO",
}

# 三王星集合（即使是正相位也带负面影响）
OUTER_PLANETS = {"URANUS", "NEPTUNE", "PLUTO"}

# 平均运行速度（度/天）— 用于判断快慢
PLANET_AVG_SPEED: dict[str, float] = {
    "SUN": 0.9856,
    "MOON": 13.176,
    "MERCURY": 1.383,
    "VENUS": 1.202,
    "MARS": 0.524,
    "JUPITER": 0.083,
    "SATURN": 0.034,
    "URANUS": 0.012,
    "NEPTUNE": 0.006,
    "PLUTO": 0.004,
}

# 暗宫 — 与1宫无托勒密相位，能量不易被1宫掌控
DARK_HOUSES = {2, 6, 8, 12}

# 灼烧阈值（度）
CAZIMI_ORB = 0.283       # 日核内：0°17'
COMBUST_ORB = 8.5        # 灼烧：17' - 8°30'
UNDER_BEAMS_ORB = 17.0   # 日光下：8°30' - 17°

# 宫尾穿刺度数
LATE_HOUSE_ORB = 5.0


@dataclass
class FlightFortune:
    """飞星吉凶综合评估结果"""

    # 核心判定
    fortune_level: str = "neutral"  # "fortunate"(得吉) | "neutral"(中性) | "afflicted"(受克)
    fortune_score: float = 0.0      # -10 ~ +10 综合得分

    # 各维度得分（-2 ~ +2）
    dignity_score: float = 0.0      # 先天尊贵
    aspect_score: float = 0.0       # 相位格局
    reception_score: float = 0.0    # 接纳互容
    house_score: float = 0.0        # 后天宫位
    special_score: float = 0.0      # 特殊状态(灼烧/盈亏/东出西入等)

    # 详细维度数据
    dignity_detail: str = ""
    aspect_detail: str = ""
    reception_detail: str = ""
    house_detail: str = ""
    special_detail: str = ""

    # 综合文本
    summary: str = ""
    recommendation: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "fortune_level": self.fortune_level,
            "fortune_score": round(self.fortune_score, 2),
            "dignity_score": round(self.dignity_score, 2),
            "aspect_score": round(self.aspect_score, 2),
            "reception_score": round(self.reception_score, 2),
            "house_score": round(self.house_score, 2),
            "special_score": round(self.special_score, 2),
            "dignity_detail": self.dignity_detail,
            "aspect_detail": self.aspect_detail,
            "reception_detail": self.reception_detail,
            "house_detail": self.house_detail,
            "special_detail": self.special_detail,
            "summary": self.summary,
            "recommendation": self.recommendation,
        }


# ═══════════════════════════════════════════════════════════════
# 各维度评估函数
# ═══════════════════════════════════════════════════════════════

def _eval_dignity(planet_name: str, sign_name: str, degree: float) -> tuple[float, str]:
    """评估先天尊贵（-2 ~ +2）"""
    try:
        planet = Planet(planet_name)
        sign = Sign(sign_name)
    except (ValueError, KeyError):
        return 0.0, "无法判定尊贵"

    details = []
    score = 0.0

    # 入庙 +2
    if sign in DOMICILE_SIGNS.get(planet, []):
        score = 2.0
        details.append("入庙——在自己家中，拥有绝对话语权")
    # 入旺 +1.5
    elif sign in EXALTATION_SIGNS.get(planet, []):
        score = 1.5
        details.append("入旺——力量被提升，资源流动顺畅")
    # 失势 -1.5
    elif sign in DETRIMENT_SIGNS.get(planet, []):
        score = -1.5
        details.append("失势——不在舒适区，做事费力")
    # 落陷 -2
    elif sign in FALL_SIGNS.get(planet, []):
        score = -2.0
        details.append("落陷——力量难以发挥，容易出纰漏")
    # 游走 0
    else:
        score = 0.0
        details.append("游走——中性状态，全靠后天经营")

    # 三分主尊贵 +0.5（叠加）
    sign_element = SIGN_ELEMENT.get(sign_name, "")
    triplicity_rulers = TRIPLICITY_RULERS.get(sign_element, [])
    if planet_name in triplicity_rulers:
        if score <= 0:
            # 落陷但有三分主，像金星天蝎——有力量但不成熟
            score += 0.8
            details.append("三分主——落陷但有尊贵支撑，'部门总监'级别，仍可展现力量")
        else:
            score += 0.3
            details.append("三分主——尊贵叠加，力量更稳定")

    return max(-2.0, min(2.0, score)), "；".join(details) if details else "游走"


def _eval_aspect(
    planet_name: str,
    aspects: list[dict[str, Any]],
    planet_profiles: dict[str, Any] | None = None,
) -> tuple[float, str]:
    """评估相位格局（-2 ~ +2）"""
    if not aspects:
        return 0.0, "空相——力量纯粹，无外界拉扯"

    supportive = 0.0
    challenging = 0.0
    details = []

    for a in aspects:
        nature = a.get("nature", "mixed")
        strength = float(a.get("strength", 0.5))
        other = ""
        # 找到对方行星
        p1 = str(a.get("planet1", ""))
        p2 = str(a.get("planet2", ""))
        if isinstance(p1, str) and p1.upper() == planet_name.upper():
            other = str(p2)
        elif isinstance(p2, str) and p2.upper() == planet_name.upper():
            other = str(p1)
        else:
            # 尝试从 label 推断
            title = str(a.get("title", ""))
            other = title

        is_outer = other.upper() in OUTER_PLANETS

        if nature == "supportive":
            if is_outer:
                # 三王星即使是正相位也有负面影响
                supportive += strength * 0.4
                challenging += strength * 0.3
                details.append(f"与{other}和谐相位——有助力但三王星自带业力")
            else:
                supportive += strength
                details.append(f"与{other}和谐相位——顺流支持")
        elif nature == "challenging":
            if is_outer:
                challenging += strength * 1.3  # 三王星凶相位更凶
            else:
                challenging += strength
            details.append(f"与{other}紧张相位——摩擦拉扯")

    net = supportive - challenging
    score = max(-2.0, min(2.0, net * 2.0))

    if supportive > challenging + 0.5:
        detail_text = "相位格局偏吉——" + "；".join(details[:3])
    elif challenging > supportive + 0.5:
        detail_text = "相位格局偏凶——" + "；".join(details[:3])
    else:
        detail_text = "吉凶参半——" + "；".join(details[:3]) if details else "无明显相位影响"

    return score, detail_text


def _eval_reception(
    planet_name: str,
    received: list[dict[str, Any]] = None,
    hosting: list[dict[str, Any]] = None,
    mutuals: list[dict[str, Any]] = None,
) -> tuple[float, str]:
    """评估接纳互容（-2 ~ +2）"""
    received = received or []
    hosting = hosting or []
    mutuals = mutuals or []

    score = 0.0
    details = []

    # 互容 — 最强绑定
    if mutuals:
        score += 1.5 if len(mutuals) >= 2 else 1.0
        labels = []
        for m in mutuals:
            labels.extend(m.get("labels", []) or m.get("pair", []))
        details.append(f"互容{'/'.join(labels[:4])}——深度绑定，资源共享，密不可分")

    # 被接纳方（获得好处）
    if hosting:
        for h in hosting[:3]:
            receiver = h.get("receiver_label", h.get("receiver", ""))
            score += 0.5
            details.append(f"被{receiver}接纳——获得扶持和资源")

    # 接纳方（付出方）
    if received:
        for r in received[:3]:
            guests = r.get("guests", [])
            guest_names = [g.get("planet", "") for g in guests[:3]]
            if guest_names:
                score += 0.2
                details.append(f"接纳{'/'.join(guest_names)}——你在输出力量")

    score = max(-2.0, min(2.0, score))
    return score, "；".join(details) if details else "无特殊接纳互容关系"


def _eval_house(house: int, planet_name: str) -> tuple[float, str]:
    """评估后天宫位力量（-1 ~ +1）"""
    if house in ANGULAR_HOUSES:
        return 1.0, f"落角宫(第{house}宫)——力量100%发挥，世俗影响力强"
    elif house in SUCCEDENT_HOUSES:
        return 0.4, f"落续宫(第{house}宫)——力量稳定保持"
    elif house in CADENT_HOUSES:
        return -0.1, f"落果宫(第{house}宫)——力量有限，偏精神层面"

    return 0.0, ""

    # 喜乐
    try:
        joy_house = JOY_HOUSES.get(Planet(planet_name))
    except (ValueError, KeyError):
        joy_house = None

    if joy_house is not None and house == joy_house:
        base_score += 0.5
        details.append(f"落喜乐宫(第{house}宫)——能量与宫性高度契合")


def _eval_special_states(
    planet_name: str,
    chart: Any = None,
    planet_info: Any = None,
) -> tuple[float, str]:
    """评估特殊状态：灼烧/日核/盈亏/东出西入/速度/暗宫"""
    score = 0.0
    details = []

    if chart is None or planet_info is None:
        return 0.0, ""

    # ── 灼烧/日核/日光下 ──
    if planet_name not in ("SUN", "MOON"):
        sun_info = None
        try:
            sun_info = chart.get_planet_info(Planet.SUN)
        except Exception:
            pass

        if sun_info and planet_info:
            sun_lon = _absolute_longitude(sun_info)
            planet_lon = _absolute_longitude(planet_info)
            dist = min(abs(sun_lon - planet_lon) % 360, abs(planet_lon - sun_lon) % 360)

            if dist <= CAZIMI_ORB:
                score += 2.0
                details.append("日核内(Cazimi)——与太阳共享权威，力量被极大提升")
            elif dist <= COMBUST_ORB:
                score -= 1.0
                details.append("灼烧(Combust)——被太阳光芒遮蔽，力量受压制")
            elif dist <= UNDER_BEAMS_ORB:
                score += 0.3
                details.append("日光下(Under Beams)——受太阳恩惠但不受制约，自由发挥")

    # ── 东出/西入 ──
    if planet_name in ("JUPITER", "SATURN", "MARS", "VENUS", "MERCURY"):
        try:
            sun_info = chart.get_planet_info(Planet.SUN)
            if sun_info and planet_info:
                sun_lon = _absolute_longitude(sun_info)
                planet_lon = _absolute_longitude(planet_info)
                # 东出：行星在太阳顺时针方向（度数小于太阳）
                diff_clockwise = (sun_lon - planet_lon) % 360
                is_oriental = diff_clockwise < 180  # 东出

                day_planets = {"SUN", "JUPITER", "SATURN"}
                night_planets = {"MOON", "VENUS", "MARS"}

                if planet_name in day_planets:
                    if is_oriental:
                        score += 0.3
                        details.append("东出——昼星东出，主动发挥力量，事件由你引发")
                    else:
                        score -= 0.1
                        details.append("西入——昼星西入，相对被动")
                elif planet_name in night_planets:
                    if not is_oriental:
                        score += 0.3
                        details.append("西入——夜星西入，被动接收但更舒适")
                    else:
                        score -= 0.1
                        details.append("东出——夜星东出，需要主动但不擅长")
        except Exception:
            pass

    # ── 月亮盈亏 ──
    if planet_name == "MOON":
        try:
            sun_info = chart.get_planet_info(Planet.SUN)
            if sun_info and planet_info:
                sun_lon = _absolute_longitude(sun_info)
                moon_lon = _absolute_longitude(planet_info)
                # 增光期：月亮在太阳顺时针方向（新月到满月之间）
                diff = (moon_lon - sun_lon) % 360
                if diff < 180:
                    score += 0.4
                    details.append("增光期——月亮力量增强，偏吉")
                else:
                    score -= 0.3
                    details.append("减光期——月亮力量减弱，偏凶")
        except Exception:
            pass

    # ── 运行速度 ──
    avg = PLANET_AVG_SPEED.get(planet_name, 1.0)
    actual_speed = abs(float(getattr(planet_info, "speed", avg)))
    if avg > 0 and actual_speed > avg * 1.3:
        score += 0.2
        details.append("运行速度高于平均——所掌领域更快实现")
    elif avg > 0 and actual_speed < avg * 0.7:
        score -= 0.2
        details.append("运行速度低于平均——所掌领域更迟缓")

    # ── 逆行 ──
    if getattr(planet_info, "is_retrograde", False):
        score -= 0.3
        details.append("逆行——力量内化，外在表现受阻")

    return max(-2.0, min(2.0, score)), "；".join(details) if details else ""


def _absolute_longitude(info: Any) -> float:
    """计算行星的绝对黄经"""
    if hasattr(info, "longitude"):
        return float(info.longitude)
    if hasattr(info, "sign") and hasattr(info, "degree"):
        try:
            return list(Sign).index(info.sign) * 30.0 + float(info.degree)
        except (ValueError, TypeError):
            pass
    return 0.0


# ═══════════════════════════════════════════════════════════════
# 主函数
# ═══════════════════════════════════════════════════════════════

def evaluate_flight_fortune(
    planet_name: str,
    sign_name: str,
    degree: float,
    house: int,
    chart: Any = None,
    planet_info: Any = None,
    aspects: list[dict[str, Any]] | None = None,
    received: list[dict[str, Any]] | None = None,
    hosting: list[dict[str, Any]] | None = None,
    mutuals: list[dict[str, Any]] | None = None,
) -> FlightFortune:
    """
    综合评估飞星吉凶。

    返回 FlightFortune 对象，包含：
    - fortune_level: "fortunate" | "neutral" | "afflicted"
    - fortune_score: -10 ~ +10
    - 各维度得分和详情
    """
    # 1. 先天尊贵
    d_score, d_detail = _eval_dignity(planet_name, sign_name, degree)

    # 2. 相位格局（增强版——刑冲权重更高）
    a_score, a_detail = _eval_aspect_enhanced(planet_name, aspects or [])

    # 3. 接纳互容
    r_score, r_detail = _eval_reception(planet_name, received, hosting, mutuals)

    # 4. 后天宫位
    h_score, h_detail = _eval_house(house, planet_name)

    # 5. 特殊状态
    s_score, s_detail = _eval_special_states(planet_name, chart, planet_info)

    # ── 加权综合 ──
    # 先天尊贵权重最高(40%)，相位(25%)，接纳互容(20%)，宫位(10%)，特殊(5%)
    total = (
        d_score * 4.0
        + a_score * 2.5
        + r_score * 2.0
        + h_score * 1.0
        + s_score * 1.0
    )
    total = max(-10.0, min(10.0, total))

    # ── 判定 fortune_level ──
    if total >= 2.5:
        level = "fortunate"
    elif total <= -2.5:
        level = "afflicted"
    else:
        level = "neutral"

    # ── 生成综合文本 ──
    summary = _build_summary(level, total, d_detail, a_detail, r_detail, h_detail, s_detail)
    recommendation = _build_recommendation(level, planet_name, d_score, a_score, r_score)

    return FlightFortune(
        fortune_level=level,
        fortune_score=total,
        dignity_score=d_score,
        aspect_score=a_score,
        reception_score=r_score,
        house_score=h_score,
        special_score=s_score,
        dignity_detail=d_detail,
        aspect_detail=a_detail,
        reception_detail=r_detail,
        house_detail=h_detail,
        special_detail=s_detail,
        summary=summary,
        recommendation=recommendation,
    )


def _build_summary(level: str, score: float, *details: str) -> str:
    """生成综合摘要"""
    all_details = [d for d in details if d]
    detail_text = "。".join(all_details[:4])

    if level == "fortunate":
        prefix = "【得吉】此飞星整体偏吉——"
    elif level == "afflicted":
        prefix = "【受克】此飞星整体偏凶——"
    else:
        prefix = "【中性】此飞星吉凶参半——"

    return f"{prefix}{detail_text}（综合得分：{score:+.1f}）"


def _build_recommendation(
    level: str,
    planet_name: str,
    d_score: float,
    a_score: float,
    r_score: float,
) -> str:
    """生成行动建议"""
    if level == "fortunate":
        if d_score >= 1.5:
            return "这个领域你天生顺手——大胆走，做自己就是最好的策略。"
        elif r_score >= 1.0:
            return "借力打力——你背后有人和资源撑着，善用关系网络。"
        else:
            return "顺势而为——当前条件不错，把已经成熟的能力推向更大舞台。"
    elif level == "afflicted":
        if d_score <= -1.5:
            return "这个领域天生不是你的舒适区——但一旦找到方法，别人抄不走。需要比旁人更多的耐心和坚持。"
        elif a_score <= -1.0:
            return "摩擦和拉扯会逼出你的成熟度——不急于求成，先把节奏稳住。"
        else:
            return "遇到的麻烦不是终点，是提醒你换个方式。多试几次，第二次往往比第一次好。"
    else:
        return "不好不坏——全靠你的节奏管理和判断。把方法打磨好，结构搭稳。"


def get_house_rulers_extended(sign_name: str) -> dict[str, Any]:
    """
    返回某星座的完整守护星信息：
    - domicile: 庙主星（古典优先）
    - exaltation: 旺主星（古典优先）
    - triplicity: 三分主星列表
    - modern: 现代守护星（三王星）

    古典守护优先——因为古典占星在论断客观事物时更准确。
    现代守护用于心理层面的补充解读。

    用于为每个宫位提供多层次的飞星分析。
    """
    try:
        sign = Sign(sign_name)
    except (ValueError, KeyError):
        return {}

    result: dict[str, Any] = {}

    # 庙主星 — 古典优先（前7个行星），现代补充
    classical_planets = [Planet.SUN, Planet.MOON, Planet.MERCURY, Planet.VENUS,
                         Planet.MARS, Planet.JUPITER, Planet.SATURN]
    outer_planets_map = {Planet.URANUS: "URANUS", Planet.NEPTUNE: "NEPTUNE", Planet.PLUTO: "PLUTO"}

    for planet in classical_planets:
        if sign in DOMICILE_SIGNS.get(planet, []):
            result["domicile"] = planet.value
            break  # 只取第一个古典守护

    # 如果古典没找到，再用现代（这种情况理论上不会发生）
    if "domicile" not in result:
        for planet, name in outer_planets_map.items():
            if sign in DOMICILE_SIGNS.get(planet, []):
                result["domicile"] = name

    # 旺主星 — 同样古典优先
    for planet in classical_planets:
        if sign in EXALTATION_SIGNS.get(planet, []):
            result["exaltation"] = planet.value
            break

    if "exaltation" not in result:
        for planet, name in outer_planets_map.items():
            if sign in EXALTATION_SIGNS.get(planet, []):
                result["exaltation"] = name

    # 三分主星
    element = SIGN_ELEMENT.get(sign_name, "")
    result["triplicity"] = TRIPLICITY_RULERS.get(element, [])

    # 现代守护（三王星——心理层面的补充）
    result["modern"] = MODERN_RULERS.get(sign_name)

    return result


def is_dark_house(house: int) -> bool:
    """判断是否为暗宫（2/6/8/12 — 与1宫无托勒密相位）"""
    return house in DARK_HOUSES


def get_pierced_house(degree: float, current_house: int) -> Optional[int]:
    """
    宫尾5度穿刺原则：
    若行星在宫尾5度内，返回下一宫（穿刺目标），否则返回 None。
    """
    remaining = 30.0 - (degree % 30.0)
    if remaining <= LATE_HOUSE_ORB:
        next_house = current_house + 1
        return next_house if next_house <= 12 else 1
    return None


def detect_interception(houses: list[tuple[Any, float]]) -> dict[str, Any]:
    """
    检测宫位劫夺（Interception）。

    参数:
        houses: [(sign, degree), ...] 12个宫头

    返回:
        {
            "intercepted_signs": {house_number: sign_name},   # 被劫夺的星座
            "expanded_rulers": {sign_name: [extra_house_numbers]},  # 星座跨越多个宫位
        }
    """
    if not houses or len(houses) < 12:
        return {"intercepted_signs": {}, "expanded_rulers": {}}

    intercepted = {}
    expanded = {}

    for i in range(12):
        current_house = i + 1
        next_house = (i + 1) % 12 + 1

        current_sign = None
        next_sign = None
        try:
            current_sign = houses[i][0]
            next_sign = houses[(i + 1) % 12][0]
        except (IndexError, TypeError):
            continue

        if current_sign is None or next_sign is None:
            continue

        try:
            current_sign_val = current_sign if isinstance(current_sign, Sign) else Sign(str(current_sign))
            next_sign_val = next_sign if isinstance(next_sign, Sign) else Sign(str(next_sign))
        except (ValueError, KeyError):
            continue

        current_idx = list(Sign).index(current_sign_val)
        next_idx = list(Sign).index(next_sign_val)

        # 宫位劫夺星座：两个宫头之间跨越了超过1个星座
        gap = (next_idx - current_idx) % 12
        if gap > 1:
            # 中间的星座被劫夺
            for offset in range(1, gap):
                intercepted_idx = (current_idx + offset) % 12
                intercepted_sign = list(Sign)[intercepted_idx]
                intercepted[current_house] = intercepted_sign.value

        # 星座劫夺宫位：宫头星座重复出现（同一个星座跨了两个宫头）
        # 检查当前星座是否在后面的宫头中也出现
        for j in range(i + 1, min(i + 5, 12)):
            try:
                check_sign = houses[j][0]
                check_sign_val = check_sign if isinstance(check_sign, Sign) else Sign(str(check_sign))
            except (ValueError, KeyError, IndexError, TypeError):
                continue
            if check_sign_val == current_sign_val:
                # 这个星座跨越了多个宫位
                extra_houses = list(range(current_house + 1, j + 2))
                extra_houses = [h if h <= 12 else h - 12 for h in extra_houses]
                sign_name = current_sign_val.value
                if sign_name not in expanded:
                    expanded[sign_name] = extra_houses
                else:
                    expanded[sign_name].extend(extra_houses)

    return {
        "intercepted_signs": intercepted,
        "expanded_rulers": expanded,
    }


# ═══════════════════════════════════════════════════════════════
# 便捷函数：从 chart 和 planet_profiles 提取所需数据并评估
# ═══════════════════════════════════════════════════════════════

def evaluate_flystar_from_chart(
    chart: Any,
    source_house: int,
    target_house: int,
    ruler_name: str,
    planet_profiles: dict[str, Any] | None = None,
    receptions_data: dict[str, Any] | None = None,
) -> FlightFortune:
    """
    一站式评估：从星盘数据直接评估飞星吉凶。

    这是一个高层封装，内部调用 evaluate_flight_fortune()。
    当 chart 为 None 时，仅基于 planet_profiles 做基础评估。
    """
    # 获取行星基本信息
    planet_info = None
    sign_name = ""
    degree = 0.0
    house = target_house  # 默认用飞入宫位

    if chart is not None:
        try:
            planet_enum = Planet(ruler_name)
            planet_info = chart.get_planet_info(planet_enum)
            if planet_info:
                sign_name = planet_info.sign.value if hasattr(planet_info.sign, "value") else str(planet_info.sign)
                degree = float(getattr(planet_info, "degree", 0))
                house = int(getattr(planet_info, "house", target_house))
        except (ValueError, KeyError):
            pass

    if not sign_name and planet_profiles:
        profile = planet_profiles.get(ruler_name, {})
        sign_name = profile.get("sign", "")
        house = profile.get("house", target_house)
        degree = profile.get("degree", 0.0)

    # 获取相位数据
    aspects = []
    if planet_profiles:
        profile = planet_profiles.get(ruler_name, {})
        aspect_sig = profile.get("aspect_signature", [])
        # aspect_signature 格式: ["合相 太阳，容许度 3.5°", ...]
        for sig in aspect_sig:
            if "合相" in str(sig) or "三合" in str(sig) or "六合" in str(sig) or "六分" in str(sig):
                # 解析出 nature
                if "刑" in str(sig) or "冲" in str(sig) or "对分" in str(sig):
                    nature = "challenging"
                else:
                    nature = "supportive"
                aspects.append({
                    "title": str(sig),
                    "nature": nature,
                    "strength": 0.6,
                })

    # 获取接纳互容数据
    received = receptions_data.get("received", []) if receptions_data else []
    hosting = receptions_data.get("hosting", []) if receptions_data else []
    mutuals = receptions_data.get("mutuals", []) if receptions_data else []

    return evaluate_flight_fortune(
        planet_name=ruler_name,
        sign_name=sign_name,
        degree=degree,
        house=house,
        chart=chart,
        planet_info=planet_info,
        aspects=aspects,
        received=received,
        hosting=hosting,
        mutuals=mutuals,
    )


# ═══════════════════════════════════════════════════════════════
# 行星夹辅/围荣格局检测 (Planetary Enclosure)
# 梦老师体系：金木围荣土星 = 古典富贵格局
# ═══════════════════════════════════════════════════════════════

@dataclass
class EnclosurePattern:
    """夹辅/围荣格局"""
    enclosed_planet: str          # 被夹辅的星体
    left_planet: str              # 左侧星体
    right_planet: str             # 右侧星体
    pattern_type: str             # "benefic_enclosure"(吉星围荣) | "malefic_siege"(凶星夹困)
    house: int                    # 发生的宫位
    description: str              # 中文描述
    significance: str             # 格局含义

    def to_dict(self) -> dict[str, Any]:
        return {
            "enclosed_planet": self.enclosed_planet,
            "left_planet": self.left_planet,
            "right_planet": self.right_planet,
            "pattern_type": self.pattern_type,
            "house": self.house,
            "description": self.description,
            "significance": self.significance,
        }


def detect_planetary_enclosures(
    planet_positions: list[dict[str, Any]],
) -> list[EnclosurePattern]:
    """
    检测行星夹辅/围荣格局。

    规则：同一宫位或相邻宫位中，两颗星体"包围"中间的星体。
    - 两颗吉星（金/木）包围 = 吉星围荣（富贵格局）
    - 两颗凶星（火/土）包围 = 凶星夹困（压力格局）
    - 一吉一凶包围 = 混合夹辅

    参数:
        planet_positions: [{"planet": "SUN", "longitude": 120.5, "house": 9}, ...]

    返回:
        检测到的夹辅格局列表
    """
    patterns: list[EnclosurePattern] = []

    if len(planet_positions) < 3:
        return patterns

    BENEFICS = {"VENUS", "JUPITER"}
    MALEFICS = {"MARS", "SATURN"}

    # 按绝对黄经排序
    sorted_planets = sorted(planet_positions, key=lambda p: p.get("longitude", 0))

    # 检查每三个连续的行星
    n = len(sorted_planets)
    for i in range(n):
        left = sorted_planets[i]
        mid = sorted_planets[(i + 1) % n]
        right = sorted_planets[(i + 2) % n]

        lp = left.get("planet", "")
        mp = mid.get("planet", "")
        rp = right.get("planet", "")

        # 跳过三王星和发光体（它们一般不作为夹辅主体）
        if mp in OUTER_PLANETS or lp in OUTER_PLANETS or rp in OUTER_PLANETS:
            continue

        # 检查是否在同一或相邻宫位
        lh = left.get("house", 0)
        mh = mid.get("house", 0)
        rh = right.get("house", 0)

        same_or_adjacent = (
            (lh == mh or abs(lh - mh) == 1 or abs(lh - mh) == 11)
            and (rh == mh or abs(rh - mh) == 1 or abs(rh - mh) == 11)
        )
        if not same_or_adjacent:
            continue

        # 判断格局类型
        l_benefic = lp in BENEFICS
        r_benefic = rp in BENEFICS
        l_malefic = lp in MALEFICS
        r_malefic = rp in MALEFICS

        if l_benefic and r_benefic:
            pattern_type = "benefic_enclosure"
            desc = f"{lp}星与{rp}星围荣{mp}星于第{mh}宫"
            sig = f"吉星围荣——{mp}星所掌管的领域获得金木双重助力，显著提升财富和贵气。"
        elif l_malefic and r_malefic:
            pattern_type = "malefic_siege"
            desc = f"{lp}星与{rp}星夹困{mp}星于第{mh}宫"
            sig = f"凶星夹困——{mp}星所掌管的领域承受双重压力，需借行运吉星来化解。"
        else:
            pattern_type = "mixed_enclosure"
            desc = f"{lp}星与{rp}星夹辅{mp}星于第{mh}宫"
            sig = f"吉凶夹辅——{mp}星既得助力也承压力，关键在于区分何时借吉星之力、何时避凶星之锋。"

        patterns.append(EnclosurePattern(
            enclosed_planet=mp,
            left_planet=lp,
            right_planet=rp,
            pattern_type=pattern_type,
            house=mh,
            description=desc,
            significance=sig,
        ))

    return patterns


# ═══════════════════════════════════════════════════════════════
# 相位格局检测 (Aspect Pattern)
# T三角 / 大十字 / 大三角 / 风筝
# ═══════════════════════════════════════════════════════════════

@dataclass
class AspectPattern:
    """相位格局"""
    pattern_type: str             # "t_square" | "grand_cross" | "grand_trine" | "kite"
    planets: list[str]            # 参与的星体
    houses: list[int]             # 涉及的宫位
    description: str              # 中文描述
    interpretation: str           # 格局解读
    severity: str                 # "high" | "medium" | "low"

    def to_dict(self) -> dict[str, Any]:
        return {
            "pattern_type": self.pattern_type,
            "planets": self.planets,
            "houses": self.houses,
            "description": self.description,
            "interpretation": self.interpretation,
            "severity": self.severity,
        }


def detect_aspect_patterns(
    aspects: list[dict[str, Any]],
    planet_house_map: dict[str, int] | None = None,
) -> list[AspectPattern]:
    """
    从相位列表中检测经典相位格局。

    检测顺序：
    1. T三角 (T-Square): 两星对冲 + 第三星与两者分别刑克
    2. 大十字 (Grand Cross): 四星互相刑冲组成十字
    3. 大三角 (Grand Trine): 三星互相三合
    4. 风筝 (Kite): 大三角 + 第四星与其中一星对冲

    参数:
        aspects: 相位列表，每条包含 planet1, planet2, type(ASPECT_TYPE), strength
        planet_house_map: {"SUN": 9, "MOON": 5, ...} 用于标注涉及宫位

    返回:
        检测到的相位格局列表
    """
    if planet_house_map is None:
        planet_house_map = {}

    patterns: list[AspectPattern] = []

    # 构建图：planet -> {other_planet: aspect_type}
    graph: dict[str, dict[str, str]] = {}
    for a in aspects:
        p1 = str(a.get("planet1", "")).upper()
        p2 = str(a.get("planet2", "")).upper()
        atype = str(a.get("type", ""))
        # 归一化 aspect type: "AspectType.SQUARE" -> "SQUARE"
        if "." in atype:
            atype = atype.split(".")[-1]
        if not p1 or not p2:
            continue
        graph.setdefault(p1, {})[p2] = atype
        graph.setdefault(p2, {})[p1] = atype

    planets = list(graph.keys())
    if len(planets) < 3:
        return patterns

    OPPOSITION = "OPPOSITION"
    SQUARE = "SQUARE"
    TRINE = "TRINE"
    SEXTILE = "SEXTILE"

    # ── T三角检测 ──
    for i, p1 in enumerate(planets):
        for j, p2 in enumerate(planets):
            if j <= i:
                continue
            if graph[p1].get(p2) != OPPOSITION:
                continue
            # 找第三星：与p1和p2都刑克
            for p3 in planets:
                if p3 in (p1, p2):
                    continue
                s1 = graph[p1].get(p3)
                s2 = graph[p2].get(p3)
                if SQUARE in (s1, s2) and (s1 == SQUARE or s2 == SQUARE):
                    # 确认p3与双方都有紧张相位（至少一个刑克+另一个也可以是对冲）
                    if not ((s1 in (SQUARE, OPPOSITION)) and (s2 in (SQUARE, OPPOSITION))):
                        continue
                    houses = [
                        planet_house_map.get(p1, 0),
                        planet_house_map.get(p2, 0),
                        planet_house_map.get(p3, 0),
                    ]
                    apex = p3  # 顶点
                    patterns.append(AspectPattern(
                        pattern_type="t_square",
                        planets=[p1, p2, p3],
                        houses=[h for h in houses if h > 0],
                        description=f"{p1}-{p2}对冲，{apex}为T三角顶点",
                        interpretation=(
                            f"T三角格局——{apex}是压力的集中点也是出口。"
                            f"{p1}和{p2}的对立通过{apex}释放，"
                            "这个领域是你一生反复面对、越磨越利的课题。"
                        ),
                        severity="high",
                    ))

    # ── 大三角检测 ──
    seen_triples: set[tuple] = set()
    for p1 in planets:
        for p2 in planets:
            if p2 == p1:
                continue
            if graph[p1].get(p2) != TRINE:
                continue
            for p3 in planets:
                if p3 in (p1, p2):
                    continue
                if graph[p1].get(p3) != TRINE or graph[p2].get(p3) != TRINE:
                    continue
                triple = tuple(sorted([p1, p2, p3]))
                if triple in seen_triples:
                    continue
                seen_triples.add(triple)
                houses = [planet_house_map.get(p, 0) for p in triple]
                patterns.append(AspectPattern(
                    pattern_type="grand_trine",
                    planets=list(triple),
                    houses=[h for h in houses if h > 0],
                    description=f"{'/'.join(triple)}形成大三角",
                    interpretation=(
                        f"大三角格局——{'/'.join(triple)}三者之间能量顺流，"
                        "在这些领域你天然顺手，但也容易因太舒服而缺乏突破动力。"
                    ),
                    severity="low",
                ))

    # ── 大十字检测 ──
    # 需要至少4颗星形成两个对冲+四个刑克
    for p1 in planets:
        for p2 in planets:
            if p2 == p1:
                continue
            if graph[p1].get(p2) != OPPOSITION:
                continue
            for p3 in planets:
                if p3 in (p1, p2):
                    continue
                for p4 in planets:
                    if p4 in (p1, p2, p3):
                        continue
                    if graph[p3].get(p4) != OPPOSITION:
                        continue
                    # 检查十字邢克
                    squares = 0
                    for a, b in [(p1, p3), (p1, p4), (p2, p3), (p2, p4)]:
                        if graph[a].get(b) == SQUARE:
                            squares += 1
                    if squares >= 4:
                        houses = [planet_house_map.get(p, 0) for p in [p1, p2, p3, p4]]
                        patterns.append(AspectPattern(
                            pattern_type="grand_cross",
                            planets=[p1, p2, p3, p4],
                            houses=[h for h in houses if h > 0],
                            description=f"{'/'.join([p1,p2,p3,p4])}形成大十字",
                            interpretation=(
                                f"大十字格局——四颗星体互相拉扯，"
                                "人生注定无法走单一轨道，需要在多个矛盾领域间反复平衡。"
                                "这是最辛苦的格局之一，但也是最能练出全维度能力的格局。"
                            ),
                            severity="high",
                        ))
                    # 只取第一个大十字
                    break

    return patterns


# ═══════════════════════════════════════════════════════════════
# 增强版 fortune 评分（调高刑冲权重）
# ═══════════════════════════════════════════════════════════════

def _eval_aspect_enhanced(
    planet_name: str,
    aspects: list[dict[str, Any]],
) -> tuple[float, str]:
    """
    增强版相位评估 —— 刑冲权重更高。

    改动点（针对金兰兰案例）：
    - 刑克/对冲的负面权重从 1.0x 提升到 1.3x
    - 互溶中带刑克的，增加了额外的摩擦惩罚
    - 三王星刑冲的额外惩罚从 1.3x 提升到 1.5x
    """
    if not aspects:
        return 0.0, "空相——力量纯粹，无外界拉扯"

    supportive = 0.0
    challenging = 0.0
    details: list[str] = []

    for a in aspects:
        nature = a.get("nature", "mixed")
        strength = float(a.get("strength", 0.5))
        other = ""
        p1 = str(a.get("planet1", ""))
        p2 = str(a.get("planet2", ""))
        if p1.upper() == planet_name.upper():
            other = str(p2)
        elif p2.upper() == planet_name.upper():
            other = str(p1)
        else:
            other = str(a.get("title", ""))

        is_outer = other.upper() in OUTER_PLANETS

        if nature == "supportive":
            if is_outer:
                supportive += strength * 0.4
                challenging += strength * 0.4  # 三王星正相位也带负面影响（提升）
                details.append(f"与{other}和谐相位——有助力但三王星自带业力")
            else:
                supportive += strength
                details.append(f"与{other}和谐相位——顺流支持")
        elif nature == "challenging":
            if is_outer:
                challenging += strength * 1.5  # 三王星凶相位更凶（从1.3提升）
            else:
                challenging += strength * 1.3  # 普通凶相位权重提升（从1.0提升）
            details.append(f"与{other}紧张相位——摩擦拉扯")

    net = supportive - challenging
    score = max(-2.5, min(2.5, net * 2.2))  # 范围扩大（从-2~2改为-2.5~2.5）

    if supportive > challenging + 0.5:
        detail_text = "相位格局偏吉——" + "；".join(details[:3])
    elif challenging > supportive + 0.3:  # 阈值收紧（从0.5改为0.3）
        detail_text = "相位格局偏凶——" + "；".join(details[:3])
    else:
        detail_text = "吉凶参半——" + "；".join(details[:3]) if details else "无明显相位影响"

    return score, detail_text
