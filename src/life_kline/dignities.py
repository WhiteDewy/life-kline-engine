"""
dignities.py - 尊贵度计算系统

这个模块实现了古典占星学中的尊贵度计算，包括：
1. 本质尊贵（Essential Dignity）：庙、旺、三分、界、面等
2. 意外尊贵（Accidental Dignity）：宫位、特殊状态、速度等
3. 尊贵度归一化和缓存管理。
"""

from typing import Dict, List, Optional, Tuple, Any
import math

# 导入常量和模型
from .constants import (
    Planet,
    Sign,
    CalculationMode,
    DOMICILE_SIGNS,
    EXALTATION_SIGNS,
    EXALTATION_DEGREES,
    DETRIMENT_SIGNS,
    FALL_SIGNS,
    ANGULAR_HOUSES,
    SUCCEDENT_HOUSES,
    CADENT_HOUSES,
    clamp,
    normalize_to_range,
    deg_diff,
)
from .models import ChartData, PlanetInfo


# ============================================================================
# 1. 辅助函数（尊贵度计算专用）
# ============================================================================


def get_term_lord(sign: Sign, degree: float) -> Optional[Planet]:
    """
    获取界的宫主星（根据埃及界表 Egyptian Terms）

    注意：本系统遵循 Dorotheus 体系，使用埃及界（Egyptian Terms），
    而非托勒密界（Ptolemaic Terms）。
    数据来源: Dorotheus of Sidon (Carmen Astrologicum)

    参数:
        sign: 星座
        degree: 度数（0-29.999）

    返回:
        界的宫主星，如果没有则返回None
    """
    # 埃及界表 (Egyptian Terms - Dorotheus System)
    # 格式：[(起始度, 结束度, 守护星), ...]
    egyptian_terms: Dict[Sign, List[Tuple[float, float, Planet]]] = {
        Sign.ARIES: [
            (0, 6, Planet.JUPITER),   # 0-6° 木
            (6, 12, Planet.VENUS),    # 6-12° 金
            (12, 20, Planet.MERCURY), # 12-20° 水
            (20, 25, Planet.MARS),    # 20-25° 火
            (25, 30, Planet.SATURN),  # 25-30° 土
        ],
        Sign.TAURUS: [
            (0, 8, Planet.VENUS),     # 0-8° 金
            (8, 14, Planet.MERCURY),  # 8-14° 水
            (14, 22, Planet.JUPITER), # 14-22° 木
            (22, 27, Planet.SATURN),  # 22-27° 土
            (27, 30, Planet.MARS),    # 27-30° 火
        ],
        Sign.GEMINI: [
            (0, 6, Planet.MERCURY),   # 0-6° 水
            (6, 12, Planet.VENUS),    # 6-12° 金
            (12, 17, Planet.JUPITER), # 12-17° 木
            (17, 24, Planet.MARS),    # 17-24° 火
            (24, 30, Planet.SATURN),  # 24-30° 土
        ],
        Sign.CANCER: [
            (0, 6, Planet.MARS),      # 0-6° 火
            (6, 12, Planet.VENUS),    # 6-12° 金
            (12, 19, Planet.MERCURY), # 12-19° 水
            (19, 26, Planet.JUPITER), # 19-26° 木
            (26, 30, Planet.SATURN),  # 26-30° 土
        ],
        Sign.LEO: [
            (0, 6, Planet.JUPITER),   # 0-6° 木
            (6, 11, Planet.VENUS),    # 6-11° 金
            (11, 18, Planet.SATURN),  # 11-18° 土
            (18, 24, Planet.MERCURY), # 18-24° 水
            (24, 30, Planet.MARS),    # 24-30° 火
        ],
        Sign.VIRGO: [
            (0, 7, Planet.MERCURY),   # 0-7° 水
            (7, 17, Planet.VENUS),    # 7-17° 金
            (17, 21, Planet.JUPITER), # 17-21° 木
            (21, 28, Planet.MARS),    # 21-28° 火
            (28, 30, Planet.SATURN),  # 28-30° 土
        ],
        Sign.LIBRA: [
            (0, 6, Planet.SATURN),    # 0-6° 土
            (6, 14, Planet.MERCURY),  # 6-14° 水
            (14, 21, Planet.JUPITER), # 14-21° 木
            (21, 28, Planet.VENUS),   # 21-28° 金
            (28, 30, Planet.MARS),    # 28-30° 火
        ],
        Sign.SCORPIO: [
            (0, 7, Planet.MARS),      # 0-7° 火
            (7, 11, Planet.VENUS),    # 7-11° 金
            (11, 19, Planet.MERCURY), # 11-19° 水
            (19, 24, Planet.JUPITER), # 19-24° 木
            (24, 30, Planet.SATURN),  # 24-30° 土
        ],
        Sign.SAGITTARIUS: [
            (0, 12, Planet.JUPITER),  # 0-12° 木
            (12, 17, Planet.VENUS),   # 12-17° 金
            (17, 21, Planet.MERCURY), # 17-21° 水
            (21, 26, Planet.SATURN),  # 21-26° 土
            (26, 30, Planet.MARS),    # 26-30° 火
        ],
        Sign.CAPRICORN: [
            (0, 7, Planet.MERCURY),   # 0-7° 水
            (7, 14, Planet.JUPITER),  # 7-14° 木
            (14, 22, Planet.VENUS),   # 14-22° 金
            (22, 26, Planet.SATURN),  # 22-26° 土
            (26, 30, Planet.MARS),    # 26-30° 火
        ],
        Sign.AQUARIUS: [
            (0, 7, Planet.MERCURY),   # 0-7° 水
            (7, 13, Planet.VENUS),    # 7-13° 金
            (13, 20, Planet.JUPITER), # 13-20° 木
            (20, 25, Planet.MARS),    # 20-25° 火
            (25, 30, Planet.SATURN),  # 25-30° 土
        ],
        Sign.PISCES: [
            (0, 12, Planet.VENUS),    # 0-12° 金
            (12, 16, Planet.JUPITER), # 12-16° 木
            (16, 19, Planet.MERCURY), # 16-19° 水
            (19, 28, Planet.MARS),    # 19-28° 火
            (28, 30, Planet.SATURN),  # 28-30° 土
        ],
    }

    if sign not in egyptian_terms:
        return None

    for start, end, lord in egyptian_terms[sign]:
        if start <= degree < end:
            return lord
            
    # 处理 29.999... 的边界情况
    if 29.0 <= degree < 30.0:
        return egyptian_terms[sign][-1][2]

    return None


def get_face_lord(sign: Sign, degree: float) -> Optional[Planet]:
    """
    获取面的宫主星（Chaldean Decans）

    面（Face或Decan）是将每个星座平分成3个10度的区间，
    每个区间由不同的行星守护，顺序是：火星-太阳-金星-水星-月亮-土星-木星。

    参数:
        sign: 星座
        degree: 度数（0-29.999）

    返回:
        面的宫主星，如果没有则返回None
    """
    # Chaldean Decans顺序：火星、太阳、金星、水星、月亮、土星、木星...
    # 每10度一个面，每个星座3个面
    decan_planets = [
        Planet.MARS,  # 第1个10度
        Planet.SUN,  # 第2个10度
        Planet.VENUS,  # 第3个10度
        Planet.MERCURY,  # 第4个10度
        Planet.MOON,  # 第5个10度
        Planet.SATURN,  # 第6个10度
        Planet.JUPITER,  # 第7个10度（然后循环）
    ]

    # 计算星座的面索引
    sign_index = list(Sign).index(sign)
    decan_index = int(degree // 10)  # 0, 1, 2

    # 面的守护行星序列（从白羊座开始）
    # 每个星座的面从不同的行星开始
    start_index = (sign_index * 3) % len(decan_planets)

    # 获取面的守护行星
    planet_index = (start_index + decan_index) % len(decan_planets)
    return decan_planets[planet_index]


def is_any_triplicity_lord(planet: Planet, sign: Sign) -> bool:
    """
    判断行星是否为该星座的三分宫主星之一（Dorotheus体系）

    三分（Triplicity）有三种主星：日主星、夜主星、共同主星。
    只要是其中任意一个，即返回True。

    参数:
        planet: 行星
        sign: 星座

    返回:
        bool: 是否为三分宫主星之一
    """
    # 三分宫主星表（根据Dorotheus系统）
    # 格式：{星座: (日主星, 夜主星, 共同主星)}
    triplicity_lords: Dict[Sign, Tuple[Planet, Planet, Planet]] = {
        # 🔥 火三分：白羊 / 狮子 / 射手
        Sign.ARIES: (Planet.SUN, Planet.JUPITER, Planet.SATURN),
        Sign.LEO: (Planet.SUN, Planet.JUPITER, Planet.SATURN),
        Sign.SAGITTARIUS: (Planet.SUN, Planet.JUPITER, Planet.SATURN),
        # 🌱 土三分：金牛 / 处女 / 摩羯
        Sign.TAURUS: (Planet.VENUS, Planet.MOON, Planet.MARS),
        Sign.VIRGO: (Planet.VENUS, Planet.MOON, Planet.MARS),
        Sign.CAPRICORN: (Planet.VENUS, Planet.MOON, Planet.MARS),
        # 🌬 风三分：双子 / 天秤 / 水瓶
        Sign.GEMINI: (Planet.SATURN, Planet.MERCURY, Planet.JUPITER),
        Sign.LIBRA: (Planet.SATURN, Planet.MERCURY, Planet.JUPITER),
        Sign.AQUARIUS: (Planet.SATURN, Planet.MERCURY, Planet.JUPITER),
        # 🌊 水三分：巨蟹 / 天蝎 / 双鱼
        Sign.CANCER: (Planet.VENUS, Planet.MARS, Planet.MOON),
        Sign.SCORPIO: (Planet.VENUS, Planet.MARS, Planet.MOON),
        Sign.PISCES: (Planet.VENUS, Planet.MARS, Planet.MOON),
    }

    if sign not in triplicity_lords:
        return False

    day_lord, night_lord, particip_lord = triplicity_lords[sign]

    # 只要是任意一个主星，即返回True（不可叠加）
    return planet in (day_lord, night_lord, particip_lord)


def is_peregrine(planet: Planet, sign: Sign, degree: float, is_day: bool) -> bool:
    """
    判断行星是否处于游走状态（Peregrine）

    游走是指行星不在自己的庙、旺、三分、界、面中，
    即没有任何尊贵。

    参数:
        planet: 行星
        sign: 星座
        degree: 度数
        is_day: 是否为日间盘

    返回:
        bool: 是否游走
    """
    # 检查庙宫
    if sign in DOMICILE_SIGNS.get(planet, []):
        return False

    # 检查旺宫
    if sign in EXALTATION_SIGNS.get(planet, []):
        return False

    # 检查三分宫主星
    if is_any_triplicity_lord(planet, sign):
        return False

    # 检查界
    term_lord = get_term_lord(sign, degree)
    if term_lord == planet:
        return False

    # 检查面
    face_lord = get_face_lord(sign, degree)
    if face_lord == planet:
        return False

    # 如果以上都没有，则为游走
    return True


def is_cazimi(planet: Planet, sun_longitude: float, planet_longitude: float) -> bool:
    """
    判断行星是否在太阳心脏（Cazimi）

    Cazimi是指行星与太阳合相在0°17'（约0.283度）以内，
    被认为是极其有力的状态。

    参数:
        planet: 行星（太阳自身不可能是Cazimi）
        sun_longitude: 太阳黄经
        planet_longitude: 行星黄经

    返回:
        bool: 是否为Cazimi
    """
    if planet == Planet.SUN:
        return False  # 太阳自身不可能是Cazimi

    # Cazimi的容许度通常是0°17'（约0.283度）
    cazimi_orb = 0.283

    # 计算与太阳的角度差
    diff = deg_diff(planet_longitude, sun_longitude)

    return diff <= cazimi_orb


def is_combust(planet: Planet, sun_longitude: float, planet_longitude: float) -> bool:
    """
    判断行星是否被燃烧（Combust）

    燃烧是指行星与太阳合相在8°30'（古典标准）以内，
    被认为是非常不利的状态。

    参数:
        planet: 行星（太阳自身不可能被燃烧）
        sun_longitude: 太阳黄经
        planet_longitude: 行星黄经

    返回:
        bool: 是否被燃烧
    """
    if planet == Planet.SUN:
        return False  # 太阳自身不可能被燃烧

    # 燃烧的容许度通常是8°30'（约8.5度）
    combust_orb = 8.5

    # 计算与太阳的角度差
    diff = deg_diff(planet_longitude, sun_longitude)

    return 0 < diff <= combust_orb  # 大于0度但小于等于8.5度


def is_under_sun_beams(
    planet: Planet, sun_longitude: float, planet_longitude: float
) -> bool:
    """
    判断行星是否在日光下（Under Sun Beams）

    日光下是指行星与太阳合相在8°30'到17°之间，
    被认为是轻微不利的状态。

    参数:
        planet: 行星
        sun_longitude: 太阳黄经
        planet_longitude: 行星黄经

    返回:
        bool: 是否在日光下
    """
    if planet == Planet.SUN:
        return False

    # 计算与太阳的角度差
    diff = deg_diff(planet_longitude, sun_longitude)

    # 日光下的范围：大于燃烧容许度，小于17度
    return 8.5 < diff <= 17.0


def is_oriental(
    planet: Planet, sun_longitude: float, planet_longitude: float
) -> bool:
    """
    判断行星是否为东方行星（Oriental，即先于太阳升起）

    定义：
    东方行星（Oriental）：在黄道上位于太阳“后面”（度数更小），
    即 (Sun - Planet) % 360 < 180。
    它们在日出前升起。

    西方行星（Occidental）：在黄道上位于太阳“前面”（度数更大），
    即 (Planet - Sun) % 360 < 180。
    它们在日落后落下。

    参数:
        planet: 行星
        sun_longitude: 太阳黄经
        planet_longitude: 行星黄经

    返回:
        bool: 是否为东方行星
    """
    if planet == Planet.SUN:
        return False

    # 计算 Sun - Planet 的角度差
    # 如果差值在 0-180 之间，说明 Planet 在 Sun 的“顺时针”方向（升起更早）
    diff = (sun_longitude - planet_longitude) % 360.0

    return diff < 180.0


def is_east_of_sun(
    planet: Planet, sun_longitude: float, planet_longitude: float
) -> bool:
    """
    (已废弃，请使用 is_oriental) 判断行星是否在太阳东边
    """
    return is_oriental(planet, sun_longitude, planet_longitude)


def get_average_speed(planet: Planet) -> float:
    """
    获取行星的平均运行速度（度/天）

    这是古典占星学中的参考值，用于判断行星速度的快慢。

    参数:
        planet: 行星

    返回:
        平均速度（度/天）
    """
    # 行星平均速度表（近似值）
    average_speeds: Dict[Planet, float] = {
        Planet.SUN: 0.9856,  # 太阳
        Planet.MOON: 13.176,  # 月亮
        Planet.MERCURY: 1.383,  # 水星
        Planet.VENUS: 1.175,  # 金星
        Planet.MARS: 0.524,  # 火星
        Planet.JUPITER: 0.083,  # 木星
        Planet.SATURN: 0.034,  # 土星
        Planet.URANUS: 0.012,  # 天王星
        Planet.NEPTUNE: 0.006,  # 海王星
        Planet.PLUTO: 0.004,  # 冥王星
    }

    return average_speeds.get(planet, 1.0)


def get_joy_house(planet: Planet) -> Optional[int]:
    """
    获取行星的喜乐宫（Joy House）

    喜乐宫是行星感到舒适和发挥正面影响的宫位。

    参数:
        planet: 行星

    返回:
        喜乐宫编号（1-12），如果没有则返回None
    """
    joy_houses: Dict[Planet, int] = {
        Planet.MERCURY: 1,  # 水星喜乐第1宫
        Planet.MOON: 3,  # 月亮喜乐第3宫
        Planet.VENUS: 5,  # 金星喜乐第5宫
        Planet.MARS: 6,  # 火星喜乐第6宫
        Planet.SUN: 9,  # 太阳喜乐第9宫
        Planet.JUPITER: 11,  # 木星喜乐第11宫
        Planet.SATURN: 12,  # 土星喜乐第12宫
    }

    return joy_houses.get(planet)


# ============================================================================
# 2. 本质尊贵计算（根据PRD）
# ============================================================================


def compute_essential_dignity_raw(
    planet: Planet,
    sign: Sign,
    degree: float,
    is_day: bool,
    mode: CalculationMode = CalculationMode.MODERN,
    chart_data: Optional[ChartData] = None,
) -> float:
    """
    计算本质尊贵原始分（庙旺三分界面/失势落陷/游走）

    根据PRD中2.1节的算法实现。

    参数:
        planet: 行星ID
        sign: 星座
        degree: 度数（0-29.999）
        is_day: 是否为日间盘
        mode: 计算模式，'LILLY_PURE'或'MODERN'
        chart_data: 星盘数据（用于互容和相位检测，可选）

    返回:
        本质尊贵原始分数

    示例:
        >>> compute_essential_dignity_raw(Planet.SUN, Sign.LEO, 10.5, True, CalculationMode.MODERN)
        5.0  # 太阳在狮子座（庙宫）
    """
    # 外行星处理（根据模式）
    if mode == CalculationMode.LILLY_PURE and planet.is_outer:
        # 莉莉原版：外行星不参与尊贵评分
        return 0.0

    score = 0.0

    # 1. 庙宫（Domicile）：行星守护的星座 +5分
    if sign in DOMICILE_SIGNS.get(planet, []):
        score += 5.0
        # 调试信息可以记录
        if planet == Planet.SUN and sign == Sign.LEO:
            print(f"调试: {planet.value}在庙宫{sign.value} +5.0分")

    # 2. 旺宫（Exaltation）：行星擢升的星座 +4分
    if sign in EXALTATION_SIGNS.get(planet, []):
        score += 4.0
        print(f"调试: {planet.value}在旺宫{sign.value} +4.0分")

    # 3. 失势（Detriment）：庙宫的对宫 -4分
    if sign in DETRIMENT_SIGNS.get(planet, []):
        score -= 4.0
        print(f"调试: {planet.value}在失势{sign.value} -4.0分")

    # 4. 落陷（Fall）：旺宫的对宫 -3分
    if sign in FALL_SIGNS.get(planet, []):
        score -= 3.0
        print(f"调试: {planet.value}在落陷{sign.value} -3.0分")

    # 5. 三分宫主星（Triplicity）：+3分
    # 只要是任意一个三分主星，即获得+3分（不叠加）
    if is_any_triplicity_lord(planet, sign):
        score += 3.0
        print(f"调试: {planet.value}是三分宫主星之一 +3.0分")

    # 6. 界（Term）：+1.5分
    # 使用埃及界 (Egyptian Terms)
    term_lord = get_term_lord(sign, degree)
    if term_lord == planet:
        score += 1.5
        print(f"调试: {planet.value}是界主星 +1.5分")

    # 7. 面（Face）：+0.5分
    face_lord = get_face_lord(sign, degree)
    if face_lord == planet:
        score += 0.5
        print(f"调试: {planet.value}是面主星 +0.5分")

    # 8. 游走（Peregrine）：-5.0分 或 -2.0分（缓解）
    # 如果以上尊贵都没有（庙旺三分界面），则为游走
    if is_peregrine(planet, sign, degree, is_day):
        # 检查是否可以缓解
        mitigated = False
        
        if chart_data:
            # 动态导入避免循环依赖
            from .receptions import check_mutual_reception
            from .aspects import detect_aspect_between
            
            # 获取定位星（Dispositor）
            dispositor = None
            for p, signs in DOMICILE_SIGNS.items():
                if sign in signs:
                    dispositor = p
                    break
            
            if dispositor and dispositor != planet:
                # 1. 检查互容 (Mutual Reception)
                mutual_rec = check_mutual_reception(planet, dispositor, chart_data)
                
                # 2. 检查接纳+相位 (Reception by Domicile + Aspect)
                # 行星在定位星的星座中，即已被接纳。只要有相位即可。
                has_aspect = detect_aspect_between(planet, dispositor, chart_data) is not None
                
                if mutual_rec or has_aspect:
                    mitigated = True
                    print(f"调试: {planet.value}游走但获得救赎 (互容或有相位接纳)")
        
        if mitigated:
            score -= 2.0
            print(f"调试: {planet.value}缓解的游走 -2.0分")
        else:
            score -= 5.0
            print(f"调试: {planet.value}游走 -5.0分")

    return score


def compute_essential_dignity_for_planet(
    planet: Planet, chart_data: ChartData
) -> float:
    """
    包装函数：为指定行星计算本质尊贵

    参数:
        planet: 行星
        chart_data: ChartData对象

    返回:
        本质尊贵原始分数

    示例:
        >>> chart = ChartData()
        >>> chart.planets[Planet.SUN] = PlanetInfo(Sign.LEO, 10.5, 10)
        >>> chart.is_day_chart = True
        >>> compute_essential_dignity_for_planet(Planet.SUN, chart)
        5.0
    """
    # 获取行星信息
    planet_info = chart_data.get_planet_info(planet)
    if not planet_info:
        print(f"警告: 行星 {planet.value} 不在星盘中")
        return 0.0

    # 调用原始计算函数
    return compute_essential_dignity_raw(
        planet=planet,
        sign=planet_info.sign,
        degree=planet_info.degree,
        is_day=chart_data.is_day_chart,
        mode=chart_data.mode,
    )


# ============================================================================
# 3. 意外尊贵计算（根据PRD）
# ============================================================================


def compute_accidental_dignity_raw(
    planet_info: PlanetInfo, chart_info: Dict[str, Any]
) -> float:
    """
    计算意外尊贵原始分（角续果宫+状态等）

    根据PRD中2.2节的算法实现。

    参数:
        planet_info: 行星信息对象
        chart_info: 盘信息字典（包含sun_longitude, is_day等）

    返回:
        意外尊贵原始分数

    示例:
        >>> planet_info = PlanetInfo(Sign.ARIES, 10.0, 1, is_retrograde=False)
        >>> chart_info = {'sun_longitude': 120.0, 'is_day': True}
        >>> compute_accidental_dignity_raw(planet_info, chart_info)
        2.0  # 角宫+2分
    """
    score = 0.0
    house = planet_info.house
    sun_long = chart_info.get("sun_longitude", 0.0)

    # 获取行星黄经（从度数和星座计算）
    # 每个星座30度，从白羊座0°开始
    sign_index = list(Sign).index(planet_info.sign)
    planet_long = sign_index * 30.0 + planet_info.degree

    # 1. 宫位角续果（重要：宫位力量计算不包含此项）
    if house in ANGULAR_HOUSES:
        score += 2.0  # 角宫 +2
        print(f"调试: 行星在角宫第{house}宫 +2.0分")
    elif house in SUCCEDENT_HOUSES:
        score += 1.0  # 续宫 +1
        print(f"调试: 行星在续宫第{house}宫 +1.0分")
    elif house in CADENT_HOUSES:
        score -= 1.0  # 果宫 -1
        print(f"调试: 行星在果宫第{house}宫 -1.0分")

    # 2. 特殊状态（Cazimi优先）
    # 获取行星枚举
    planet_enum = None
    for planet in Planet:
        if planet_info.sign.name.lower() in planet.value.lower():
            planet_enum = planet
            break

    # 如果无法确定行星枚举，尝试使用行星名称
    if planet_enum is None and hasattr(planet_info, "name") and planet_info.name:
        for planet in Planet:
            if planet_info.name.lower() in planet.value.lower():
                planet_enum = planet
                break

    # 对于非太阳的行星，检查太阳相关状态
    if planet_enum and planet_enum != Planet.SUN:
        # 检查Cazimi
        if is_cazimi(planet_enum, sun_long, planet_long):
            score += 3.0  # Cazimi +3
            print(f"调试: 行星在太阳心脏 +3.0分")
        else:
            # 非Cazimi情况下检查燃烧/日光下
            if is_combust(planet_enum, sun_long, planet_long):
                score -= 3.0  # 燃烧 -3
                print(f"调试: 行星被燃烧 -3.0分")
            elif is_under_sun_beams(planet_enum, sun_long, planet_long):
                score -= 1.0  # 日光下 -1
                print(f"调试: 行星在日光下 -1.0分")

    # 3. 逆行、速度等
    if planet_info.is_retrograde:
        score -= 1.5  # 逆行 -1.5
        print(f"调试: 行星逆行 -1.5分")

    # 速度判断（快慢）
    speed = planet_info.speed
    if planet_enum:
        avg_speed = get_average_speed(planet_enum)

        # 计算速度比例
        if avg_speed > 0:
            speed_ratio = speed / avg_speed

            if speed_ratio > 1.2:
                score += 0.5  # 速度快 +0.5
                print(f"调试: 行星速度快 +0.5分 (速度比: {speed_ratio:.2f})")
            elif speed_ratio < 0.8:
                score -= 0.5  # 速度慢 -0.5
                print(f"调试: 行星速度慢 -0.5分 (速度比: {speed_ratio:.2f})")

    # 4. 东方/西方（相对于太阳）
    # 古典规则：
    # 上位行星（火木土）东方更有力
    # 下位行星（水金）西方更有力（作为长庚星）
    # 但根据用户统一要求：东方 +0.5, 西方 -0.5
    if planet_enum and planet_enum != Planet.SUN:
        # 使用 is_oriental 判断
        is_ori = is_oriental(planet_enum, sun_long, planet_long)
        
        # 修正逻辑：
        # 如果是上位行星(火木土)，东方为吉
        # 如果是下位行星(水金)，西方为吉
        # 但遵循用户指令 "东方 +0.5 西方 -0.5" 
        # 我们这里先严格执行用户指令，但添加注释说明古典区别
        
        if is_ori:
            score += 0.5  # 东方 +0.5
            print(f"调试: 行星为东方行星(Oriental) +0.5分")
        else:
            score -= 0.5  # 西方 -0.5
            print(f"调试: 行星为西方行星(Occidental) -0.5分")

    # 5. 纬度判断
    latitude = getattr(planet_info, "latitude", 0.0)
    if latitude > 0:
        score += 0.5  # 北纬有利
        print(f"调试: 行星在北纬 +0.5分")
    elif latitude < 0:
        score -= 0.5  # 南纬不利
        print(f"调试: 行星在南纬 -0.5分")

    # 6. 喜乐宫
    if planet_enum:
        joy_house = get_joy_house(planet_enum)
        if joy_house is not None and house == joy_house:
            score += 0.5  # 在喜乐宫 +0.5
            print(f"调试: 行星在喜乐宫 +0.5分")

    # 7. 限制总分范围（意外尊贵整体不允许超过 ±5）
    original_score = score
    score = clamp(score, -5.0, 5.0)
    if score != original_score:
        print(f"调试: 意外尊贵总分从 {original_score:.2f} 限制为 {score:.2f}")

    return score


def compute_accidental_dignity_for_planet(
    planet: Planet, chart_data: ChartData
) -> float:
    """
    包装函数：为指定行星计算意外尊贵

    参数:
        planet: 行星
        chart_data: ChartData对象

    返回:
        意外尊贵原始分数

    示例:
        >>> chart = ChartData()
        >>> chart.planets[Planet.SUN] = PlanetInfo(Sign.LEO, 10.5, 10)
        >>> chart.sun_longitude = 120.0
        >>> compute_accidental_dignity_for_planet(Planet.SUN, chart)
        2.0  # 假设是角宫
    """
    # 获取行星信息
    planet_info = chart_data.get_planet_info(planet)
    if not planet_info:
        print(f"警告: 行星 {planet.value} 不在星盘中")
        return 0.0

    # 准备盘信息
    chart_info = {
        "sun_longitude": chart_data.sun_longitude,
        "is_day": chart_data.is_day_chart,
    }

    # 调用原始计算函数
    return compute_accidental_dignity_raw(planet_info, chart_info)


# ============================================================================
# 4. 全盘尊贵度计算（核心函数，根据PRD）
# ============================================================================


def compute_all_dignities(chart_data: ChartData) -> Dict[Planet, float]:
    """
    计算所有行星的尊贵度，存储到chart_data.dignities_by_planet

    根据PRD中2.3节的算法实现。

    参数:
        chart_data: ChartData对象（会修改其dignities_by_planet属性）

    返回:
        尊贵度字典 {行星: 归一化尊贵度}

    示例:
        >>> chart = ChartData()
        >>> # 添加行星数据...
        >>> dignities = compute_all_dignities(chart)
        >>> print(chart.dignities_by_planet[Planet.SUN])
        0.8  # 太阳的尊贵度
    """
    dignities = {}

    print("=" * 60)
    print("开始计算全盘尊贵度...")
    print("=" * 60)

    for planet in chart_data.planets.keys():
        print(f"\n计算 {planet.value} 的尊贵度:")
        print("-" * 40)

        # 获取行星信息
        planet_info = chart_data.get_planet_info(planet)
        if not planet_info:
            print(f"警告: 跳过缺失的行星 {planet.value}")
            continue

        # 1. 计算本质尊贵
        essential_raw = compute_essential_dignity_raw(
            planet=planet,
            sign=planet_info.sign,
            degree=planet_info.degree,
            is_day=chart_data.is_day_chart,
            mode=chart_data.mode,
            chart_data=chart_data,  # 传递 chart_data 用于互容检查
        )
        print(f"本质尊贵原始分: {essential_raw:.2f}")

        # 2. 计算意外尊贵
        chart_info = {
            "sun_longitude": chart_data.sun_longitude,
            "is_day": chart_data.is_day_chart,
        }
        accidental_raw = compute_accidental_dignity_raw(planet_info, chart_info)
        print(f"意外尊贵原始分: {accidental_raw:.2f}")

        # 3. 合并原始分数
        total_raw = essential_raw + accidental_raw
        print(f"尊贵原始总分: {total_raw:.2f}")

        # 4. 归一化到[-1, 1]范围
        MAX_RAW = 15.0  # 理论最大值（根据PRD）
        MIN_RAW = -15.0  # 理论最小值（根据PRD）

        normalized = normalize_to_range(total_raw, MIN_RAW, MAX_RAW, -1.0, 1.0)
        normalized = clamp(normalized, -1.0, 1.0)

        print(f"归一化尊贵度: {normalized:.3f}")

        # 存储结果
        dignities[planet] = normalized

        # 5. 记录调试信息
        if not hasattr(chart_data, "debug"):
            chart_data.debug = {}

        chart_data.debug[planet.value] = chart_data.debug.get(planet.value, {})
        chart_data.debug[planet.value]["dignity"] = {
            "essential_raw": essential_raw,
            "accidental_raw": accidental_raw,
            "total_raw": total_raw,
            "normalized": normalized,
        }

        # 记录计算日志
        if "calculation_log" not in chart_data.debug:
            chart_data.debug["calculation_log"] = []

        chart_data.debug["calculation_log"].append(
            {
                "timestamp": "now",  # 实际应使用datetime
                "action": "compute_dignity",
                "planet": planet.value,
                "result": normalized,
            }
        )

    # 存储到chart_data
    chart_data.dignities_by_planet = dignities

    print("\n" + "=" * 60)
    print("全盘尊贵度计算完成!")
    print("=" * 60)

    # 打印摘要
    print("\n尊贵度摘要:")
    for planet, dignity in sorted(dignities.items(), key=lambda x: x[1], reverse=True):
        status = "强势" if dignity > 0.3 else "弱势" if dignity < -0.3 else "平衡"
        print(f"  {planet.value}: {dignity:+.3f} ({status})")

    return dignities


def get_dignity_for_planet(planet: Planet, chart_data: ChartData) -> float:
    """
    获取单个行星的尊贵度（如果未计算则先计算全盘）

    参数:
        planet: 行星
        chart_data: ChartData对象

    返回:
        归一化后的尊贵度值（[-1, 1]）

    示例:
        >>> dignity = get_dignity_for_planet(Planet.SUN, chart_data)
        >>> print(f"太阳尊贵度: {dignity:.3f}")
    """
    # 检查是否已经计算过
    if (
        not hasattr(chart_data, "dignities_by_planet")
        or not chart_data.dignities_by_planet
    ):
        print(f"提示: 尊贵度未计算，先计算全盘尊贵度...")
        compute_all_dignities(chart_data)

    # 返回尊贵度，如果行星不存在则返回0.0
    return chart_data.dignities_by_planet.get(planet, 0.0)


# ============================================================================
# 5. 尊贵度分析工具
# ============================================================================


def analyze_dignity_distribution(chart_data: ChartData) -> Dict[str, Any]:
    """
    分析尊贵度分布情况

    参数:
        chart_data: ChartData对象

    返回:
        尊贵度分布分析结果
    """
    if (
        not hasattr(chart_data, "dignities_by_planet")
        or not chart_data.dignities_by_planet
    ):
        compute_all_dignities(chart_data)

    dignities = chart_data.dignities_by_planet

    # 计算统计数据
    values = list(dignities.values())

    analysis = {
        "count": len(values),
        "mean": sum(values) / len(values) if values else 0.0,
        "max": max(values) if values else 0.0,
        "min": min(values) if values else 0.0,
        "positive_count": sum(1 for v in values if v > 0),
        "negative_count": sum(1 for v in values if v < 0),
        "neutral_count": sum(1 for v in values if abs(v) <= 0.1),
    }

    # 最强和最弱行星
    if dignities:
        strongest = max(dignities.items(), key=lambda x: x[1])
        weakest = min(dignities.items(), key=lambda x: x[1])

        analysis["strongest_planet"] = {
            "planet": strongest[0].value,
            "dignity": strongest[1],
        }
        analysis["weakest_planet"] = {"planet": weakest[0].value, "dignity": weakest[1]}

    # 行星分组统计
    traditional_dignities = {}
    outer_dignities = {}

    for planet, dignity in dignities.items():
        if planet.is_traditional:
            traditional_dignities[planet.value] = dignity
        if planet.is_outer:
            outer_dignities[planet.value] = dignity

    analysis["traditional_planets"] = traditional_dignities
    analysis["outer_planets"] = outer_dignities

    return analysis


def print_dignity_report(chart_data: ChartData) -> None:
    """
    打印尊贵度详细报告

    参数:
        chart_data: ChartData对象
    """
    if (
        not hasattr(chart_data, "dignities_by_planet")
        or not chart_data.dignities_by_planet
    ):
        compute_all_dignities(chart_data)

    dignities = chart_data.dignities_by_planet

    print("\n" + "=" * 60)
    print("尊贵度详细报告")
    print("=" * 60)

    # 按尊贵度排序
    sorted_dignities = sorted(dignities.items(), key=lambda x: x[1], reverse=True)

    for planet, dignity in sorted_dignities:
        planet_info = chart_data.get_planet_info(planet)

        if planet_info:
            # 获取尊贵度描述
            if dignity > 0.7:
                desc = "极其强势"
            elif dignity > 0.4:
                desc = "非常强势"
            elif dignity > 0.1:
                desc = "略微强势"
            elif dignity > -0.1:
                desc = "基本平衡"
            elif dignity > -0.4:
                desc = "略微弱势"
            elif dignity > -0.7:
                desc = "非常弱势"
            else:
                desc = "极其弱势"

            # 打印行星信息
            print(f"\n{planet.value}:")
            print(f"  位置: {planet_info.sign.value} {planet_info.degree:.1f}°")
            print(f"  宫位: 第{planet_info.house}宫")
            print(f"  逆行: {'是' if planet_info.is_retrograde else '否'}")
            print(f"  尊贵度: {dignity:+.3f} ({desc})")

            # 打印调试信息（如果存在）
            if planet.value in chart_data.debug:
                debug_info = chart_data.debug[planet.value].get("dignity", {})
                if debug_info:
                    print(f"  本质尊贵: {debug_info.get('essential_raw', 0):.2f}")
                    print(f"  意外尊贵: {debug_info.get('accidental_raw', 0):.2f}")

    print("\n" + "=" * 60)
    print("报告结束")
    print("=" * 60)


# ============================================================================
# 6. 导出函数
# ============================================================================

__all__ = [
    # 本质尊贵计算
    "compute_essential_dignity_raw",
    "compute_essential_dignity_for_planet",
    # 意外尊贵计算
    "compute_accidental_dignity_raw",
    "compute_accidental_dignity_for_planet",
    # 全盘尊贵计算
    "compute_all_dignities",
    "get_dignity_for_planet",
    # 辅助函数
    "get_term_lord",
    "get_face_lord",
    "is_triplicity_lord_current",
    "is_peregrine",
    "is_cazimi",
    "is_combust",
    "is_under_sun_beams",
    "is_east_of_sun",
    "get_average_speed",
    "get_joy_house",
    # 分析工具
    "analyze_dignity_distribution",
    "print_dignity_report",
]
