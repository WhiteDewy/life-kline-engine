"""
aspects.py - 相位系统

这个模块实现了星盘相位计算，包括：
1. 相位检测和强度计算
2. 吉凶相位判断
3. 相位特征提取
4. 相位格局检测

遵循莉莉《基督占星》体系，并提供现代扩展选项。
"""

from typing import Dict, List, Optional, Tuple, Set, Any
import math
from enum import Enum

# 导入常量和模型
from .constants import (
    Planet, Sign, AspectType, CalculationMode,
    ASPECT_CONFIG, clamp, deg_diff, get_planet_orb, normalize_to_range
)
from .models import ChartData, PlanetInfo, Aspect


# 流年相位容许度配置（比本命相位更紧的容许度，流年为快速触发事件）
TRANSIT_ASPECT_CONFIG: Dict[AspectType, Dict[str, float]] = {
    AspectType.CONJUNCTION: {"angle": 0.0, "orb": 3.0, "strength": 1.0},
    AspectType.OPPOSITION: {"angle": 180.0, "orb": 3.0, "strength": 0.8},
    AspectType.SQUARE: {"angle": 90.0, "orb": 2.5, "strength": 0.8},
    AspectType.TRINE: {"angle": 120.0, "orb": 2.5, "strength": 0.9},
    AspectType.SEXTILE: {"angle": 60.0, "orb": 2.0, "strength": 0.6},
    AspectType.QUINCUNX: {"angle": 150.0, "orb": 1.0, "strength": 0.3},
}


# ============================================================================
# 1. 相位检测函数
# ============================================================================

def detect_aspect_between(
    planet1: Planet,
    planet2: Planet,
    chart_data: ChartData,
    use_cache: bool = True
) -> Optional[Aspect]:
    """
    检测两个行星之间是否存在相位
    
    参数:
        planet1: 第一个行星
        planet2: 第二个行星
        chart_data: ChartData对象
        use_cache: 是否使用缓存
    
    返回:
        Aspect对象，如果没有相位则返回None
    
    示例:
        >>> aspect = detect_aspect_between(Planet.SUN, Planet.MOON, chart_data)
        >>> if aspect:
        >>>     print(f"太阳和月亮有{aspect.aspect_type.value}相位")
    """
    if planet1 == planet2:
        return None  # 同一行星不构成相位
    
    # 检查缓存
    if use_cache and hasattr(chart_data, 'aspect_matrix'):
        if (planet1 in chart_data.aspect_matrix and 
            planet2 in chart_data.aspect_matrix[planet1]):
            cached = chart_data.aspect_matrix[planet1][planet2]
            if isinstance(cached, Aspect):
                return cached
    
    # 获取行星信息
    info1 = chart_data.get_planet_info(planet1)
    info2 = chart_data.get_planet_info(planet2)
    
    if not info1 or not info2:
        return None
    
    # 计算绝对黄经
    long1 = info1.get_absolute_position()
    long2 = info2.get_absolute_position()
    
    # 计算角度差（考虑360°循环）
    actual_angle = deg_diff(long1, long2)
    
    # 检查所有定义的相位
    best_aspect = None
    best_orb = float('inf')  # 寻找容许度最小的相位
    
    # 计算两星的容许度半径之和的一半 (Moiety of Orbs)
    # 古典占星原则：相位容许度取决于行星而非相位类型
    orb1 = get_planet_orb(planet1)
    orb2 = get_planet_orb(planet2)
    moiety_orb = (orb1 + orb2) / 2.0
    
    for aspect_type, config in ASPECT_CONFIG.items():
        exact_angle = config['angle']
        
        # 使用 Moiety Orb 作为主要容许度
        # 但对于梅花相位(Quincunx)等次要相位，保持较小的固定容许度
        if aspect_type == AspectType.QUINCUNX:
            limit_orb = config['orb']
        else:
            limit_orb = moiety_orb
            
        # 检查是否在容许度内
        if abs(actual_angle - exact_angle) <= limit_orb:
            current_orb = abs(actual_angle - exact_angle)
            
            # 选择最精确的相位（容许度最小）
            if current_orb < best_orb:
                best_orb = current_orb
                
                # 判断是形成中还是分离中
                is_applying, is_separating = check_aspect_direction(
                    planet1, planet2, exact_angle, chart_data
                )
                
                # 计算相位强度（容许度越小，强度越大）
                # 注意：calculate_aspect_strength 内部仍使用 config['orb'] 作为归一化分母
                # 我们需要调整它，使其基于 moiety_orb
                
                # 重新实现强度计算逻辑（内联）
                if limit_orb > 0:
                    precision = 1.0 - (current_orb / limit_orb)
                    precision = clamp(precision, 0.0, 1.0)
                else:
                    precision = 1.0
                
                base_strength = config['strength']
                strength = base_strength * precision
                
                # 重要行星加成
                important_planets = {Planet.SUN, Planet.MOON}
                if planet1 in important_planets or planet2 in important_planets:
                    strength *= 1.1
                
                # 精确相位加成
                if current_orb < 1.0:
                    strength *= 1.2
                
                strength = clamp(strength, 0.0, 1.0)
                
                best_aspect = Aspect(
                    planet1=planet1,
                    planet2=planet2,
                    aspect_type=aspect_type,
                    exact_angle=exact_angle,
                    actual_angle=actual_angle,
                    orb=current_orb,
                    strength=strength,
                    is_applying=is_applying,
                    is_separating=is_separating
                )
    
    # 如果有缓存系统，存储结果
    if use_cache and best_aspect:
        if not hasattr(chart_data, 'aspect_matrix'):
            chart_data.aspect_matrix = {}
        
        if planet1 not in chart_data.aspect_matrix:
            chart_data.aspect_matrix[planet1] = {}
        if planet2 not in chart_data.aspect_matrix:
            chart_data.aspect_matrix[planet2] = {}
        
        chart_data.aspect_matrix[planet1][planet2] = best_aspect
        chart_data.aspect_matrix[planet2][planet1] = best_aspect
    
    return best_aspect


def check_aspect_direction(
    planet1: Planet,
    planet2: Planet,
    exact_angle: float,
    chart_data: ChartData
) -> Tuple[bool, bool]:
    """
    检查相位是形成中（applying）还是分离中（separating）
    
    形成中：行星正在接近精确相位
    分离中：行星正在离开精确相位
    
    参数:
        planet1: 第一个行星
        planet2: 第二个行星
        exact_angle: 精确相位角度
        chart_data: ChartData对象
    
    返回:
        (is_applying, is_separating) 元组
    """
    info1 = chart_data.get_planet_info(planet1)
    info2 = chart_data.get_planet_info(planet2)
    
    if not info1 or not info2:
        return False, False
    
    # 获取行星的黄经和速度
    long1 = info1.get_absolute_position()
    long2 = info2.get_absolute_position()
    speed1 = info1.speed
    speed2 = info2.speed
    
    # 计算当前角度差（0-180度）
    current_diff = deg_diff(long1, long2)
    
    # 计算如果行星继续移动，角度差会如何变化
    # 这是一个简化计算，假设短时间内速度不变
    
    # 计算行星的相对位置（哪个在前面）
    # 注意：要考虑相位角度的多种可能性（如60°和300°都是六合）
    
    # 简化的方向判断：根据行星速度差和当前位置判断
    diff_to_exact = abs(current_diff - exact_angle)
    
    # 如果角度差小于1度，认为是精确相位
    if diff_to_exact < 1.0:
        return False, False
    
    # 更精确的方向判断需要考虑行星的运行方向
    # 这里简化处理：如果速度差显著且当前角度差小于精确角度，可能是在形成中
    speed_diff = speed1 - speed2
    
    # 简化的逻辑：如果内行星（速度较快）在外行星后面，可能正在形成相位
    if speed1 > speed2 and long1 < long2:
        # 内行星在外行星后面，可能会追上形成相位
        return True, False
    elif speed1 < speed2 and long1 > long2:
        # 外行星在内行星后面，可能会追上形成相位
        return True, False
    else:
        # 其他情况，暂时认为是分离中或稳定
        return False, True


def calculate_aspect_strength(
    aspect_type: AspectType,
    orb: float,
    planet1: Planet,
    planet2: Planet,
    chart_data: ChartData
) -> float:
    """
    计算相位强度
    
    强度基于：1. 容许度大小 2. 相位类型 3. 行星性质
    
    参数:
        aspect_type: 相位类型
        orb: 容许度（与精确角度的差值）
        planet1: 第一个行星
        planet2: 第二个行星
        chart_data: ChartData对象
    
    返回:
        相位强度 [0, 1]
    """
    # 获取相位配置
    config = ASPECT_CONFIG.get(aspect_type)
    if not config:
        return 0.0
    
    max_orb = config['orb']
    base_strength = config['strength']
    
    # 1. 基于容许度计算精确度分数
    if max_orb > 0:
        precision = 1.0 - (orb / max_orb)  # 容许度越小，精确度越高
        precision = clamp(precision, 0.0, 1.0)
    else:
        precision = 1.0
    
    # 2. 相位类型的基础强度
    strength = base_strength * precision
    
    # 3. 行星重要性的调整
    # 太阳和月亮的相位通常更重要
    planet_multiplier = 1.0
    
    important_planets = {Planet.SUN, Planet.MOON}
    if planet1 in important_planets or planet2 in important_planets:
        planet_multiplier = 1.1  # 重要行星相位强度增加10%
    
    # 4. 容许度很小的精确相位额外加成
    if orb < 1.0:  # 小于1度的精确相位
        planet_multiplier *= 1.2
    
    strength *= planet_multiplier
    
    return clamp(strength, 0.0, 1.0)


def get_all_aspects_for_planet(
    planet: Planet,
    chart_data: ChartData,
    use_cache: bool = True
) -> List[Aspect]:
    """
    获取指定行星的所有相位
    
    参数:
        planet: 行星
        chart_data: ChartData对象
        use_cache: 是否使用缓存
    
    返回:
        该行星的所有相位列表
    """
    aspects = []
    
    # 检查缓存
    if use_cache and hasattr(chart_data, 'aspect_matrix'):
        if planet in chart_data.aspect_matrix:
            for other_planet, aspect in chart_data.aspect_matrix[planet].items():
                if other_planet != planet and aspect:
                    aspects.append(aspect)
            return aspects
    
    # 如果没有缓存或不允许使用缓存，重新计算
    for other_planet in chart_data.planets.keys():
        if other_planet == planet:
            continue
        
        aspect = detect_aspect_between(planet, other_planet, chart_data, use_cache)
        if aspect:
            aspects.append(aspect)
    
    return aspects


def compute_all_aspects(chart_data: ChartData) -> Dict[Planet, Dict[Planet, Aspect]]:
    """
    计算全盘所有相位，构建相位矩阵
    
    参数:
        chart_data: ChartData对象
    
    返回:
        相位矩阵字典
    """
    if not hasattr(chart_data, 'aspect_matrix'):
        chart_data.aspect_matrix = {}
    
    planets = list(chart_data.planets.keys())
    
    print("=" * 60)
    print("开始计算全盘相位...")
    print("=" * 60)
    
    aspect_count = 0
    for i, planet1 in enumerate(planets):
        if planet1 not in chart_data.aspect_matrix:
            chart_data.aspect_matrix[planet1] = {}
        
        for planet2 in planets[i+1:]:  # 避免重复计算
            if planet2 not in chart_data.aspect_matrix:
                chart_data.aspect_matrix[planet2] = {}
            
            aspect = detect_aspect_between(planet1, planet2, chart_data, use_cache=False)
            
            if aspect:
                chart_data.aspect_matrix[planet1][planet2] = aspect
                chart_data.aspect_matrix[planet2][planet1] = aspect
                aspect_count += 1
                
                # 调试输出重要相位
                if aspect.strength > 0.7:  # 强相位
                    print(f"强相位: {planet1.value} {aspect.aspect_type.value} {planet2.value} "
                          f"(强度: {aspect.strength:.2f}, 容许度: {aspect.orb:.2f}°)")
    
    print(f"\n相位计算完成，共发现 {aspect_count} 个相位")
    print("=" * 60)
    
    return chart_data.aspect_matrix


# ============================================================================
# 2. 吉凶相位判断（根据PRD 4.2节）
# ============================================================================

def is_benefic_aspect(
    aspect: Aspect,
    is_day: bool,
    mode: CalculationMode = CalculationMode.MODERN
) -> bool:
    """
    判断相位是否为吉相位（工程优化版）
    
    根据PRD中4.2节的算法实现。
    
    参数:
        aspect: 相位对象
        is_day: 是否为日间盘
        mode: 计算模式
    
    返回:
        bool: 是否为吉相位
    
    注意：外行星处理根据模式不同
    """
    p1, p2 = aspect.planet1, aspect.planet2
    aspect_type = aspect.aspect_type
    
    # 外行星处理（根据模式）
    if mode == CalculationMode.LILLY_PURE:
        # 莉莉原版：外行星不参与吉凶分类
        if p1.is_outer or p2.is_outer:
            print(f"调试: 莉莉模式忽略外行星相位 {p1.value}-{p2.value}")
            return False
    
    # 1. 先根据相位类型判断
    # 传统吉相位：三合（120°）、六合（60°）
    # 传统凶相位：刑（90°）、冲（180°）
    # 合相（0°）：中性，取决于行星性质
    
    # 吉相位类型
    benefic_aspects = {AspectType.TRINE, AspectType.SEXTILE}
    
    # 凶相位类型
    malefic_aspects = {AspectType.SQUARE, AspectType.OPPOSITION}
    
    if aspect_type in benefic_aspects:
        # 三合和六合通常是吉相位
        return True
    
    if aspect_type in malefic_aspects:
        # 刑和冲通常是凶相位
        return False
    
    # 2. 合相的特殊处理（中性相位，取决于行星性质）
    if aspect_type == AspectType.CONJUNCTION:
        # 合相的吉凶取决于行星的组合
        
        # 吉星之间的合相：吉
        if p1.is_benefic and p2.is_benefic:
            return True
        
        # 凶星之间的合相：凶
        if p1.is_malefic and p2.is_malefic:
            return False
        
        # 吉星与中性行星的合相：偏吉
        if (p1.is_benefic and not p2.is_malefic) or (p2.is_benefic and not p1.is_malefic):
            return True
        
        # 凶星与中性行星的合相：偏凶
        if (p1.is_malefic and not p2.is_benefic) or (p2.is_malefic and not p1.is_benefic):
            return False
        
        # 太阳/月亮与其他行星的合相
        luminaries = {Planet.SUN, Planet.MOON}
        if p1 in luminaries or p2 in luminaries:
            # 发光体与吉星合相：吉
            if (p1 in luminaries and p2.is_benefic) or (p2 in luminaries and p1.is_benefic):
                return True
            # 发光体与凶星合相：凶（除非紧密合相成为Cazimi）
            if (p1 in luminaries and p2.is_malefic) or (p2 in luminaries and p1.is_malefic):
                # 检查是否为Cazimi（紧密合相）
                if aspect.orb < 0.5:  # 非常紧密的合相
                    print(f"调试: {p1.value}与{p2.value}紧密合相，可能为Cazimi")
                    return True  # Cazimi通常是吉利的
                return False
        
        # 默认情况下，合相视为中性偏吉（如果容许度小）
        return aspect.orb < 3.0  # 紧密合相视为偏吉
    
    # 3. 梅花相位（150°）的特殊处理
    if aspect_type == AspectType.QUINCUNX:
        # 梅花相位通常被视为中性偏调整性
        # 在古典占星中不常用，现代占星中视为需要调整的相位
        return False  # 通常视为轻微凶相位
    
    # 默认返回False（谨慎处理）
    return False


def is_malefic_aspect(
    aspect: Aspect,
    is_day: bool,
    mode: CalculationMode = CalculationMode.MODERN
) -> bool:
    """
    判断相位是否为凶相位
    
    参数:
        aspect: 相位对象
        is_day: 是否为日间盘
        mode: 计算模式
    
    返回:
        bool: 是否为凶相位
    """
    # 吉凶是互斥的，但可能有中性相位
    # 这里简单处理：不是吉相位就是凶相位（实际可能有中性相位）
    
    # 先检查是否为吉相位
    if is_benefic_aspect(aspect, is_day, mode):
        return False
    
    # 对于某些明确是凶相位的情况
    p1, p2 = aspect.planet1, aspect.planet2
    aspect_type = aspect.aspect_type
    
    # 明确的凶相位类型
    if aspect_type in {AspectType.SQUARE, AspectType.OPPOSITION}:
        return True
    
    # 合相的特殊情况
    if aspect_type == AspectType.CONJUNCTION:
        # 凶星之间的合相
        if p1.is_malefic and p2.is_malefic:
            return True
        
        # 发光体与凶星的合相（除非是Cazimi）
        luminaries = {Planet.SUN, Planet.MOON}
        if ((p1 in luminaries and p2.is_malefic) or 
            (p2 in luminaries and p1.is_malefic)):
            if aspect.orb >= 0.5:  # 不是紧密的Cazimi
                return True
    
    # 梅花相位通常视为轻微凶相位
    if aspect_type == AspectType.QUINCUNX:
        return True
    
    return True  # 默认视为凶相位（简化处理）


def get_aspect_nature_description(
    aspect: Aspect,
    is_day: bool,
    mode: CalculationMode = CalculationMode.MODERN
) -> str:
    """
    获取相位的性质描述
    
    参数:
        aspect: 相位对象
        is_day: 是否为日间盘
        mode: 计算模式
    
    返回:
        相位性质描述字符串
    """
    if is_benefic_aspect(aspect, is_day, mode):
        return "吉相位"
    elif is_malefic_aspect(aspect, is_day, mode):
        return "凶相位"
    else:
        return "中性相位"


# ============================================================================
# 3. 相位特征计算（根据PRD 4.1节）
# ============================================================================

def compute_aspect_features_for_planet(
    planet: Planet,
    chart_data: ChartData,
    transits: Optional[Dict[Planet, PlanetInfo]] = None
) -> Tuple[float, float]:
    """
    计算行星的相位特征（返回数值，不修改feat对象）
    
    根据PRD中4.1节的算法实现。
    
    参数:
        planet: 行星ID
        chart_data: ChartData对象
        transits: 流年行星数据（可选）
    
    返回:
        (benefic_score, malefic_score) 元组，范围都是[0, 1]
    
    示例:
        >>> benefic, malefic = compute_aspect_features_for_planet(Planet.SUN, chart_data)
        >>> print(f"吉相位强度: {benefic:.3f}, 凶相位强度: {malefic:.3f}")
    """
    # 获取所有相位
    natal_aspects = get_all_aspects_for_planet(planet, chart_data)
    
    benefic_total = 0.0
    malefic_total = 0.0

    print(f"\n计算 {planet.value} 的相位特征:")
    print("-" * 40)

    # 处理本命相位
    for aspect in natal_aspects:
        strength = aspect.strength

        # 判断吉凶
        if is_benefic_aspect(aspect, chart_data.is_day_chart, chart_data.mode):
            benefic_total += strength
            nature = "吉"
        elif is_malefic_aspect(aspect, chart_data.is_day_chart, chart_data.mode):
            malefic_total += strength
            nature = "凶"
        else:
            nature = "中"
            # 中性相位不计入总分

        # 调试输出
        other_planet = aspect.planet2 if aspect.planet1 == planet else aspect.planet1
        print(f"  {nature}相位: {planet.value} {aspect.aspect_type.value} {other_planet.value} "
              f"(强度: {strength:.2f}, 容许度: {aspect.orb:.2f}°)")

    # 如果有流年行星，也计算流年相位
    transit_aspects = []
    if transits:
        natal_info = chart_data.get_planet_info(planet)
        if natal_info:
            for t_planet, t_info in transits.items():
                if t_planet == planet:
                    continue  # 跳过自身

                # 直接计算流年行星与本命行星之间的角度差
                angle = deg_diff(t_info.longitude, natal_info.longitude)

                # 检查所有流年相位类型（使用更紧的容许度）
                best_aspect = None
                best_orb = float('inf')

                for aspect_type, config in TRANSIT_ASPECT_CONFIG.items():
                    current_orb = abs(angle - config["angle"])
                    if current_orb <= config["orb"] and current_orb < best_orb:
                        best_orb = current_orb
                        best_aspect = (aspect_type, config, current_orb)

                if best_aspect:
                    aspect_type, config, current_orb = best_aspect
                    # 简化的形成/分离判断：比较运行速度
                    is_applying = (t_info.speed or 0) > (natal_info.speed or 0)

                    # 计算相位强度（容许度越小，强度越大）
                    if config["orb"] > 0:
                        precision = 1.0 - (current_orb / config["orb"])
                        precision = clamp(precision, 0.0, 1.0)
                    else:
                        precision = 1.0

                    strength = config["strength"] * precision
                    strength = clamp(strength, 0.0, 1.0)

                    transit_aspects.append(Aspect(
                        planet1=t_planet,
                        planet2=planet,
                        aspect_type=aspect_type,
                        exact_angle=config["angle"],
                        actual_angle=angle,
                        orb=round(current_orb, 2),
                        strength=round(strength, 2),
                        is_applying=is_applying,
                        is_separating=not is_applying,
                    ))

        # 处理流年相位（权重为本命相位的0.6倍）
        TRANSIT_WEIGHT = 0.6
        for aspect in transit_aspects:
            strength = aspect.strength * TRANSIT_WEIGHT

            if is_benefic_aspect(aspect, chart_data.is_day_chart, chart_data.mode):
                benefic_total += strength
                nature = "吉"
            elif is_malefic_aspect(aspect, chart_data.is_day_chart, chart_data.mode):
                malefic_total += strength
                nature = "凶"
            else:
                nature = "中"

            print(f"  流年{nature}相位: {aspect.planet1.value} {aspect.aspect_type.value} "
                  f"{aspect.planet2.value} (强度: {strength:.2f}, 容许度: {aspect.orb:.2f}°)")

        print(f"  流年相位合计: {len(transit_aspects)} 个")

    # 归一化（根据PRD，达到4视为极强）
    MAX_STRENGTH = 4.0
    benefic_norm = clamp(benefic_total / MAX_STRENGTH, 0.0, 1.0)
    malefic_norm = clamp(malefic_total / MAX_STRENGTH, 0.0, 1.0)

    print(f"吉相位原始总分: {benefic_total:.2f}, 归一化: {benefic_norm:.3f}")
    print(f"凶相位原始总分: {malefic_total:.2f}, 归一化: {malefic_norm:.3f}")

    return benefic_norm, malefic_norm


# ============================================================================
# 4. 相位格局检测
# ============================================================================

def has_grand_trine(chart_data: ChartData) -> bool:
    """
    检测是否有大三角格局
    
    大三角：三颗行星互相形成120度相位
    
    参数:
        chart_data: ChartData对象
    
    返回:
        bool: 是否有大三角格局
    """
    if not hasattr(chart_data, 'aspect_matrix') or not chart_data.aspect_matrix:
        compute_all_aspects(chart_data)
    
    planets = list(chart_data.planets.keys())
    n = len(planets)
    
    # 检查所有三元组
    for i in range(n):
        for j in range(i+1, n):
            for k in range(j+1, n):
                p1, p2, p3 = planets[i], planets[j], planets[k]
                
                # 检查是否两两都有三合相位
                aspect12 = detect_aspect_between(p1, p2, chart_data)
                aspect23 = detect_aspect_between(p2, p3, chart_data)
                aspect31 = detect_aspect_between(p3, p1, chart_data)
                
                if (aspect12 and aspect12.aspect_type == AspectType.TRINE and
                    aspect23 and aspect23.aspect_type == AspectType.TRINE and
                    aspect31 and aspect31.aspect_type == AspectType.TRINE):
                    
                    # 检查是否形成等边三角形（三个相位都较强）
                    if (aspect12.strength > 0.6 and 
                        aspect23.strength > 0.6 and 
                        aspect31.strength > 0.6):
                        
                        print(f"发现大三角格局: {p1.value}, {p2.value}, {p3.value}")
                        return True
    
    return False


def has_t_square(chart_data: ChartData) -> bool:
    """
    检测是否有T三角格局
    
    T三角：两颗行星对冲，第三颗行星与这两颗行星都成刑相位
    
    参数:
        chart_data: ChartData对象
    
    返回:
        bool: 是否有T三角格局
    """
    if not hasattr(chart_data, 'aspect_matrix') or not chart_data.aspect_matrix:
        compute_all_aspects(chart_data)
    
    planets = list(chart_data.planets.keys())
    n = len(planets)
    
    # 首先找到所有对冲相位
    oppositions = []
    for i in range(n):
        for j in range(i+1, n):
            aspect = detect_aspect_between(planets[i], planets[j], chart_data)
            if aspect and aspect.aspect_type == AspectType.OPPOSITION:
                oppositions.append((planets[i], planets[j], aspect))
    
    # 对于每个对冲相位，寻找T三角的顶点
    for p1, p2, opp_aspect in oppositions:
        for p3 in planets:
            if p3 == p1 or p3 == p2:
                continue
            
            aspect13 = detect_aspect_between(p1, p3, chart_data)
            aspect23 = detect_aspect_between(p2, p3, chart_data)
            
            # 检查p3是否同时与p1和p2成刑相位
            if (aspect13 and aspect13.aspect_type == AspectType.SQUARE and
                aspect23 and aspect23.aspect_type == AspectType.SQUARE):
                
                # 检查相位强度
                if (opp_aspect.strength > 0.6 and 
                    aspect13.strength > 0.6 and 
                    aspect23.strength > 0.6):
                    
                    print(f"发现T三角格局:")
                    print(f"  对冲: {p1.value} - {p2.value}")
                    print(f"  顶点: {p3.value}")
                    return True
    
    return False


def has_grand_cross(chart_data: ChartData) -> bool:
    """
    检测是否有大十字格局
    
    大十字：四颗行星形成两个对冲和四个刑相位
    
    参数:
        chart_data: ChartData对象
    
    返回:
        bool: 是否有大十字格局
    """
    if not hasattr(chart_data, 'aspect_matrix') or not chart_data.aspect_matrix:
        compute_all_aspects(chart_data)
    
    planets = list(chart_data.planets.keys())
    n = len(planets)
    
    # 检查所有四元组
    for i in range(n):
        for j in range(i+1, n):
            for k in range(j+1, n):
                for l in range(k+1, n):
                    p1, p2, p3, p4 = planets[i], planets[j], planets[k], planets[l]
                    
                    # 检查必要的相位
                    aspects = [
                        detect_aspect_between(p1, p2, chart_data),
                        detect_aspect_between(p2, p3, chart_data),
                        detect_aspect_between(p3, p4, chart_data),
                        detect_aspect_between(p4, p1, chart_data),
                        detect_aspect_between(p1, p3, chart_data),
                        detect_aspect_between(p2, p4, chart_data),
                    ]
                    
                    # 检查是否形成大十字（两个对冲，四个刑相位）
                    # 这里简化检查：至少有两个对冲和四个强相位
                    opposition_count = 0
                    square_count = 0
                    
                    for aspect in aspects:
                        if aspect:
                            if aspect.aspect_type == AspectType.OPPOSITION:
                                opposition_count += 1
                            elif aspect.aspect_type == AspectType.SQUARE:
                                square_count += 1
                    
                    if opposition_count >= 2 and square_count >= 4:
                        # 检查相位强度
                        strong_aspects = [a for a in aspects if a and a.strength > 0.6]
                        if len(strong_aspects) >= 4:
                            print(f"发现大十字格局: {p1.value}, {p2.value}, {p3.value}, {p4.value}")
                            return True
    
    return False


def has_kite(chart_data: ChartData) -> bool:
    """
    检测是否有风筝格局
    
    风筝格局：一个大三角加上一个对冲顶点
    
    参数:
        chart_data: ChartData对象
    
    返回:
        bool: 是否有风筝格局
    """
    if not hasattr(chart_data, 'aspect_matrix') or not chart_data.aspect_matrix:
        compute_all_aspects(chart_data)
    
    planets = list(chart_data.planets.keys())
    
    # 先检查大三角
    for i in range(len(planets)):
        for j in range(i+1, len(planets)):
            for k in range(j+1, len(planets)):
                p1, p2, p3 = planets[i], planets[j], planets[k]
                
                # 检查是否形成大三角
                aspect12 = detect_aspect_between(p1, p2, chart_data)
                aspect23 = detect_aspect_between(p2, p3, chart_data)
                aspect31 = detect_aspect_between(p3, p1, chart_data)
                
                if (aspect12 and aspect12.aspect_type == AspectType.TRINE and
                    aspect23 and aspect23.aspect_type == AspectType.TRINE and
                    aspect31 and aspect31.aspect_type == AspectType.TRINE):
                    
                    # 大三角成立，现在检查是否有风筝的"尾巴"
                    # 风筝：大三角的一个顶点与另一颗行星对冲
                    triangle_planets = {p1, p2, p3}
                    
                    for p4 in planets:
                        if p4 in triangle_planets:
                            continue
                        
                        # 检查p4是否与某个顶点对冲
                        for vertex in triangle_planets:
                            aspect = detect_aspect_between(vertex, p4, chart_data)
                            if aspect and aspect.aspect_type == AspectType.OPPOSITION:
                                # 还需要p4与其他两个顶点成六合相位（风筝的翅膀）
                                other_vertices = [p for p in triangle_planets if p != vertex]
                                aspect1 = detect_aspect_between(p4, other_vertices[0], chart_data)
                                aspect2 = detect_aspect_between(p4, other_vertices[1], chart_data)
                                
                                if (aspect1 and aspect1.aspect_type == AspectType.SEXTILE and
                                    aspect2 and aspect2.aspect_type == AspectType.SEXTILE):
                                    
                                    print(f"发现风筝格局:")
                                    print(f"  大三角: {p1.value}, {p2.value}, {p3.value}")
                                    print(f"  顶点: {vertex.value} (与{p4.value}对冲)")
                                    return True
    
    return False


def detect_aspect_patterns(chart_data: ChartData) -> Dict[str, Any]:
    """
    检测所有相位格局
    
    参数:
        chart_data: ChartData对象
    
    返回:
        相位格局检测结果
    """
    patterns = {
        'grand_trine': has_grand_trine(chart_data),
        't_square': has_t_square(chart_data),
        'grand_cross': has_grand_cross(chart_data),
        'kite': has_kite(chart_data),
    }
    
    # 其他格局检测可以在这里添加
    patterns['has_major_pattern'] = any(patterns.values())
    
    return patterns


# ============================================================================
# 5. 相位分析工具
# ============================================================================

def analyze_aspect_distribution(chart_data: ChartData) -> Dict[str, Any]:
    """
    分析相位分布情况
    
    参数:
        chart_data: ChartData对象
    
    返回:
        相位分布分析结果
    """
    if not hasattr(chart_data, 'aspect_matrix') or not chart_data.aspect_matrix:
        compute_all_aspects(chart_data)
    
    aspect_matrix = chart_data.aspect_matrix
    
    # 统计各类相位数量
    aspect_counts = {atype: 0 for atype in AspectType}
    benefic_count = 0
    malefic_count = 0
    
    all_aspects = []
    
    # 收集所有相位
    for p1 in aspect_matrix:
        for p2, aspect in aspect_matrix[p1].items():
            if p1.value < p2.value and aspect:  # 避免重复计数
                all_aspects.append(aspect)
                
                # 统计相位类型
                aspect_counts[aspect.aspect_type] += 1
                
                # 统计吉凶
                if is_benefic_aspect(aspect, chart_data.is_day_chart, chart_data.mode):
                    benefic_count += 1
                else:
                    malefic_count += 1
    
    # 计算平均强度
    strengths = [a.strength for a in all_aspects]
    avg_strength = sum(strengths) / len(strengths) if strengths else 0.0
    
    # 最强和最弱相位
    strongest = max(all_aspects, key=lambda x: x.strength) if all_aspects else None
    weakest = min(all_aspects, key=lambda x: x.strength) if all_aspects else None
    
    analysis = {
        'total_aspects': len(all_aspects),
        'benefic_aspects': benefic_count,
        'malefic_aspects': malefic_count,
        'benefic_ratio': benefic_count / len(all_aspects) if all_aspects else 0.0,
        'aspect_type_counts': {k.value: v for k, v in aspect_counts.items()},
        'avg_strength': avg_strength,
        'max_strength': max(strengths) if strengths else 0.0,
        'min_strength': min(strengths) if strengths else 0.0,
        'strongest_aspect': str(strongest) if strongest else None,
        'weakest_aspect': str(weakest) if weakest else None,
        'aspect_patterns': detect_aspect_patterns(chart_data),
    }
    
    return analysis


def print_aspect_report(chart_data: ChartData) -> None:
    """
    打印相位详细报告
    
    参数:
        chart_data: ChartData对象
    """
    if not hasattr(chart_data, 'aspect_matrix') or not chart_data.aspect_matrix:
        compute_all_aspects(chart_data)
    
    aspect_matrix = chart_data.aspect_matrix
    
    print("\n" + "=" * 70)
    print("相位详细报告")
    print("=" * 70)
    
    # 收集所有相位
    all_aspects = []
    for p1 in aspect_matrix:
        for p2, aspect in aspect_matrix[p1].items():
            if p1.value < p2.value and aspect:  # 避免重复
                all_aspects.append(aspect)
    
    # 按强度排序
    all_aspects.sort(key=lambda x: x.strength, reverse=True)
    
    print(f"\n总共发现 {len(all_aspects)} 个相位:")
    print("-" * 70)
    
    for aspect in all_aspects:
        nature = get_aspect_nature_description(
            aspect, chart_data.is_day_chart, chart_data.mode
        )
        
        direction = ""
        if aspect.is_applying:
            direction = " (形成中)"
        elif aspect.is_separating:
            direction = " (分离中)"
        
        exactness = ""
        if aspect.orb < 1.0:
            exactness = " [精确]"
        elif aspect.orb < 3.0:
            exactness = " [较精确]"
        
        print(f"{nature:6s} | {aspect.planet1.value:8s} {aspect.aspect_type.value:12s} "
              f"{aspect.planet2.value:8s} | 强度: {aspect.strength:.2f} "
              f"(差{aspect.orb:.2f}°){direction}{exactness}")
    
    # 相位格局报告
    print("\n" + "=" * 70)
    print("相位格局检测:")
    print("-" * 70)
    
    patterns = detect_aspect_patterns(chart_data)
    
    if patterns['has_major_pattern']:
        print("发现以下重要相位格局:")
        for pattern_name, detected in patterns.items():
            if pattern_name != 'has_major_pattern' and detected:
                print(f"  ✓ {pattern_name.replace('_', ' ').title()}")
    else:
        print("未发现重要相位格局")
    
    print("\n" + "=" * 70)
    print("报告结束")
    print("=" * 70)


def get_planets_with_strong_aspects(
    chart_data: ChartData, 
    min_strength: float = 0.7
) -> List[Dict[str, Any]]:
    """
    获取有强相位的行星
    
    参数:
        chart_data: ChartData对象
        min_strength: 最小强度阈值
    
    返回:
        有强相位的行星信息列表
    """
    if not hasattr(chart_data, 'aspect_matrix') or not chart_data.aspect_matrix:
        compute_all_aspects(chart_data)
    
    result = []
    
    for planet in chart_data.planets.keys():
        aspects = get_all_aspects_for_planet(planet, chart_data)
        
        # 统计强相位
        strong_aspects = [a for a in aspects if a.strength >= min_strength]
        
        if strong_aspects:
            # 计算平均强度
            avg_strength = sum(a.strength for a in strong_aspects) / len(strong_aspects)
            
            # 统计吉凶相位
            benefic_aspects = [a for a in strong_aspects if 
                              is_benefic_aspect(a, chart_data.is_day_chart, chart_data.mode)]
            malefic_aspects = [a for a in strong_aspects if 
                              is_malefic_aspect(a, chart_data.is_day_chart, chart_data.mode)]
            
            result.append({
                'planet': planet.value,
                'total_strong_aspects': len(strong_aspects),
                'benefic_aspects': len(benefic_aspects),
                'malefic_aspects': len(malefic_aspects),
                'avg_strength': avg_strength,
                'aspect_partners': [
                    (a.planet2.value if a.planet1 == planet else a.planet1.value, 
                     a.aspect_type.value, a.strength)
                    for a in strong_aspects
                ]
            })
    
    # 按强相位数量排序
    result.sort(key=lambda x: x['total_strong_aspects'], reverse=True)
    
    return result


# ============================================================================
# 6. 导出函数
# ============================================================================

__all__ = [
    # 相位检测
    "detect_aspect_between",
    "get_all_aspects_for_planet",
    "compute_all_aspects",
    
    # 相位性质判断
    "is_benefic_aspect",
    "is_malefic_aspect",
    "get_aspect_nature_description",
    
    # 相位特征计算
    "compute_aspect_features_for_planet",
    
    # 相位格局检测
    "has_grand_trine",
    "has_t_square",
    "has_grand_cross",
    "has_kite",
    "detect_aspect_patterns",
    
    # 分析工具
    "analyze_aspect_distribution",
    "print_aspect_report",
    "get_planets_with_strong_aspects",
]
