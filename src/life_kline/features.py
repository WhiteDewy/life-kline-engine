"""
features.py - 综合特征计算系统

这个模块实现了星盘综合特征的计算，包括：
1. 资源支持特征（support_resources）
2. 压力负荷特征（load_pressure）
3. 主题一致性特征（theme_coherence）
4. 数据质量评估（data_quality）

这些特征将用于最终的运势节点评分。
"""

from typing import Dict, List, Optional, Tuple, Any, Set
import math

# 导入常量和模型
from .constants import (
    Planet, Sign, CalculationMode, clamp,
    TIME_ACCURACY_WEIGHTS, MAX_ASPECT_STRENGTH
)
from .models import ChartData, PlanetFeature

# 导入其他模块的函数
from .dignities import get_dignity_for_planet, compute_all_dignities
from .houses import get_house_power_for_planet, compute_all_house_powers, get_planets_in_house
from .aspects import compute_aspect_features_for_planet
from .receptions import compute_reception_for_planet, compute_all_receptions


# ============================================================================
# 1. 辅助函数（特征计算专用）
# ============================================================================

def has_multiple_benefics_strong(chart_data: ChartData) -> bool:
    """
    检查是否有多个吉星处于强势状态
    
    参数:
        chart_data: ChartData对象
    
    返回:
        bool: 是否有多个强势吉星
    """
    # 确保尊贵度已计算
    if not hasattr(chart_data, 'dignities_by_planet') or not chart_data.dignities_by_planet:
        compute_all_dignities(chart_data)
    
    dignities = chart_data.dignities_by_planet
    
    # 吉星列表
    benefics = [Planet.VENUS, Planet.JUPITER]
    
    # 计算强势吉星数量
    strong_count = 0
    for planet in benefics:
        if planet in dignities and dignities[planet] > 0.3:  # 尊贵度大于0.3视为强势
            strong_count += 1
    
    return strong_count >= 2


def has_multiple_malefics_afflicted(chart_data: ChartData) -> bool:
    """
    检查是否有多个凶星处于受损状态
    
    参数:
        chart_data: ChartData对象
    
    返回:
        bool: 是否有多个受损凶星
    """
    if not hasattr(chart_data, 'dignities_by_planet') or not chart_data.dignities_by_planet:
        compute_all_dignities(chart_data)
    
    dignities = chart_data.dignities_by_planet
    
    # 凶星列表
    malefics = [Planet.MARS, Planet.SATURN]
    if chart_data.mode == CalculationMode.MODERN:
        # 现代模式包含冥王星
        malefics.append(Planet.PLUTO)
    
    # 计算受损凶星数量
    afflicted_count = 0
    for planet in malefics:
        if planet in dignities and dignities[planet] < -0.3:  # 尊贵度小于-0.3视为受损
            afflicted_count += 1
    
    return afflicted_count >= 2


def detect_hard_configurations(chart_data: ChartData) -> float:
    """
    检测困难配置的压力
    
    参数:
        chart_data: ChartData对象
    
    返回:
        困难配置压力分数 [0, 1]
    """
    pressure = 0.0
    
    # 1. 检查T三角格局（较强压力）
    from .aspects import has_t_square
    if has_t_square(chart_data):
        pressure += 0.3
        print(f"调试: 检测到T三角格局，压力+0.3")
    
    # 2. 检查大十字格局（强压力）
    from .aspects import has_grand_cross
    if has_grand_cross(chart_data):
        pressure += 0.4
        print(f"调试: 检测到大十字格局，压力+0.4")
    
    # 3. 检查困难宫位的行星聚集
    difficult_houses = [6, 8, 12]  # 第6宫（健康）、第8宫（死亡）、第12宫（限制）
    
    for house in difficult_houses:
        planets_in_house = get_planets_in_house(house, chart_data)
        if len(planets_in_house) > 1:
            pressure += 0.1 * len(planets_in_house)
            print(f"调试: 第{house}宫有{len(planets_in_house)}颗行星，压力+{0.1*len(planets_in_house):.2f}")
    
    # 4. 检查凶星在角宫（加强负面影响）
    angular_houses = [1, 4, 7, 10]
    malefics = [Planet.MARS, Planet.SATURN]
    
    for planet in malefics:
        planet_info = chart_data.get_planet_info(planet)
        if planet_info and planet_info.house in angular_houses:
            pressure += 0.2
            print(f"调试: 凶星{planet.value}在角宫，压力+0.2")
    
    return clamp(pressure, 0.0, 1.0)


def detect_positive_configurations(chart_data: ChartData) -> float:
    """
    检测积极配置的支持
    
    参数:
        chart_data: ChartData对象
    
    返回:
        积极配置支持分数 [0, 1]
    """
    support = 0.0
    
    # 1. 检查大三角格局（较强支持）
    from .aspects import has_grand_trine
    if has_grand_trine(chart_data):
        support += 0.3
        print(f"调试: 检测到大三角格局，支持+0.3")
    
    # 2. 检查风筝格局（强支持）
    from .aspects import has_kite
    if has_kite(chart_data):
        support += 0.4
        print(f"调试: 检测到风筝格局，支持+0.4")
    
    # 3. 检查吉星在角宫（加强正面影响）
    angular_houses = [1, 4, 7, 10]
    benefics = [Planet.VENUS, Planet.JUPITER]
    
    for planet in benefics:
        planet_info = chart_data.get_planet_info(planet)
        if planet_info and planet_info.house in angular_houses:
            support += 0.2
            print(f"调试: 吉星{planet.value}在角宫，支持+0.2")
    
    # 4. 检查积极宫位的行星聚集
    positive_houses = [2, 5, 7, 10, 11]  # 财帛、子女、夫妻、事业、朋友宫
    
    for house in positive_houses:
        planets_in_house = get_planets_in_house(house, chart_data)
        if len(planets_in_house) > 1:
            support += 0.05 * len(planets_in_house)  # 轻微支持
            print(f"调试: 第{house}宫有{len(planets_in_house)}颗行星，支持+{0.05*len(planets_in_house):.2f}")
    
    return clamp(support, 0.0, 1.0)


# ============================================================================
# 2. 资源支持特征计算（根据PRD 6.1节）
# ============================================================================

def compute_support_resources(
    feat: PlanetFeature,
    chart_data: ChartData,
    focus_planet: Planet
) -> float:
    """
    计算资源支持特征（修正参数签名）
    
    根据PRD中6.1节的算法实现。
    
    参数:
        feat: PlanetFeature对象（会被修改）
        chart_data: ChartData对象（包含全盘尊贵数据）
        focus_planet: 焦点行星ID
    
    返回:
        计算后的特征值 [0, 1]
    
    示例:
        >>> feat = PlanetFeature()
        >>> support = compute_support_resources(feat, chart_data, Planet.SUN)
        >>> print(f"资源支持特征值: {support:.3f}")
    """
    print(f"\n计算 {focus_planet.value} 的资源支持特征:")
    print("=" * 40)
    
    # 获取全盘尊贵度数据
    dignities = chart_data.dignities_by_planet
    if not dignities:
        print("提示: 尊贵度未计算，先计算全盘尊贵度...")
        dignities = compute_all_dignities(chart_data)
    
    # 1. 吉相位支持（从feat获取或重新计算）
    if feat.aspect_benefic == 0.0:  # 如果还没计算相位特征
        print("提示: 相位特征未计算，计算相位特征...")
        benefic_score, malefic_score = compute_aspect_features_for_planet(focus_planet, chart_data)
        feat.aspect_benefic = benefic_score
        feat.aspect_malefic = malefic_score
    
    phase_support = feat.aspect_benefic
    print(f"吉相位支持: {phase_support:.3f}")
    
    # 2. 接纳互容支持
    reception_support = compute_reception_for_planet(focus_planet, chart_data)
    feat.reception = reception_support  # 设置到feat对象
    print(f"接纳支持: {reception_support:.3f}")
    
    # 3. 吉星自身状态（从全盘数据获取）
    venus_dignity = max(0, dignities.get(Planet.VENUS, 0))
    jupiter_dignity = max(0, dignities.get(Planet.JUPITER, 0))
    
    print(f"金星尊贵度: {venus_dignity:+.3f} (取正: {max(0, venus_dignity):.3f})")
    print(f"木星尊贵度: {jupiter_dignity:+.3f} (取正: {max(0, jupiter_dignity):.3f})")
    
    # 双吉星加权和（根据PRD）
    benefic_dignity = venus_dignity + jupiter_dignity * 0.8
    benefic_dignity = clamp(benefic_dignity, 0.0, 1.0)
    print(f"吉星加权和: {benefic_dignity:.3f} (金星×1.0 + 木星×0.8)")
    
    # 4. 宫位支持（从全盘数据获取）
    house_power = get_house_power_for_planet(focus_planet, chart_data)
    feat.house_power = house_power  # 设置到feat对象
    house_support = max(0, house_power)  # 只取正向部分
    print(f"宫位力量: {house_power:+.3f}, 宫位支持: {house_support:.3f}")
    
    # 5. 积极配置额外支持
    config_support = detect_positive_configurations(chart_data)
    print(f"积极配置支持: {config_support:.3f}")
    
    # 加权聚合（根据PRD的权重）
    support_raw = (
        0.40 * phase_support +
        0.25 * reception_support +
        0.20 * benefic_dignity +
        0.15 * house_support
    )
    
    # 加上配置支持（额外加成）
    support_with_config = support_raw + 0.1 * config_support
    support_final = clamp(support_with_config, 0.0, 1.0)
    
    feat.support_resources = support_final
    
    print(f"\n加权计算:")
    print(f"  0.40 × 吉相位支持({phase_support:.3f}) = {0.40 * phase_support:.3f}")
    print(f"  0.25 × 接纳支持({reception_support:.3f}) = {0.25 * reception_support:.3f}")
    print(f"  0.20 × 吉星状态({benefic_dignity:.3f}) = {0.20 * benefic_dignity:.3f}")
    print(f"  0.15 × 宫位支持({house_support:.3f}) = {0.15 * house_support:.3f}")
    print(f"  小计: {support_raw:.3f}")
    print(f"  + 配置加成(0.1×{config_support:.3f}): {0.1 * config_support:.3f}")
    print(f"  最终资源支持: {support_final:.3f}")
    
    # 调试信息
    feat.debug['support_calculation'] = {
        'phase_support': phase_support,
        'reception_support': reception_support,
        'venus_dignity': venus_dignity,
        'jupiter_dignity': jupiter_dignity,
        'benefic_dignity': benefic_dignity,
        'house_power': house_power,
        'house_support': house_support,
        'config_support': config_support,
        'support_raw': support_raw,
        'support_final': support_final
    }
    
    return support_final


# ============================================================================
# 3. 压力负荷特征计算（根据PRD 6.2节）
# ============================================================================

def compute_load_pressure(
    feat: PlanetFeature,
    chart_data: ChartData,
    focus_planet: Planet
) -> float:
    """
    计算压力负荷特征（修正参数签名）
    
    根据PRD中6.2节的算法实现。
    
    参数:
        feat: PlanetFeature对象（会被修改）
        chart_data: ChartData对象
        focus_planet: 焦点行星ID
    
    返回:
        计算后的特征值 [0, 1]
    """
    print(f"\n计算 {focus_planet.value} 的压力负荷特征:")
    print("=" * 40)
    
    # 获取全盘尊贵度数据
    dignities = chart_data.dignities_by_planet
    if not dignities:
        print("提示: 尊贵度未计算，先计算全盘尊贵度...")
        dignities = compute_all_dignities(chart_data)
    
    # 1. 凶相位压力
    if feat.aspect_malefic == 0.0:  # 如果还没计算相位特征
        print("提示: 相位特征未计算，计算相位特征...")
        benefic_score, malefic_score = compute_aspect_features_for_planet(focus_planet, chart_data)
        feat.aspect_benefic = benefic_score
        feat.aspect_malefic = malefic_score
    
    phase_pressure = feat.aspect_malefic
    print(f"凶相位压力: {phase_pressure:.3f}")
    
    # 2. 凶星状态（从全盘数据获取）
    saturn_pressure = abs(min(0, dignities.get(Planet.SATURN, 0)))
    mars_pressure = abs(min(0, dignities.get(Planet.MARS, 0)))
    
    print(f"土星尊贵度: {dignities.get(Planet.SATURN, 0):+.3f}, 压力值: {saturn_pressure:.3f}")
    print(f"火星尊贵度: {dignities.get(Planet.MARS, 0):+.3f}, 压力值: {mars_pressure:.3f}")
    
    # 冥王星压力（现代模式）
    pluto_pressure = 0.0
    if chart_data.mode == CalculationMode.MODERN:
        pluto_pressure = abs(min(0, dignities.get(Planet.PLUTO, 0))) * 0.7
        print(f"冥王星尊贵度: {dignities.get(Planet.PLUTO, 0):+.3f}, 压力值: {pluto_pressure:.3f} (权重0.7)")
    
    # 多凶星叠加
    malefic_factor = saturn_pressure + mars_pressure * 0.8 + pluto_pressure
    malefic_factor = clamp(malefic_factor, 0.0, 1.0)
    print(f"凶星叠加因子: {malefic_factor:.3f} (土星×1.0 + 火星×0.8 + 冥王星×0.7)")
    
    # 3. 困难宫位负担
    difficult_houses = [6, 8, 12]
    house_burden = 0.0
    for house in difficult_houses:
        planets_in_house = get_planets_in_house(house, chart_data)
        if len(planets_in_house) > 0:
            house_burden += 0.2 * len(planets_in_house)
            print(f"第{house}宫有{len(planets_in_house)}颗行星，负担+{0.2 * len(planets_in_house):.2f}")
    
    house_burden = clamp(house_burden, 0.0, 0.6)
    print(f"困难宫位总负担: {house_burden:.3f} (上限0.6)")
    
    # 4. 困难配置压力
    config_pressure = detect_hard_configurations(chart_data)
    print(f"困难配置压力: {config_pressure:.3f}")
    
    # 加权聚合（根据PRD的权重）
    load_raw = (
        0.50 * phase_pressure +
        0.25 * malefic_factor +
        0.15 * house_burden +
        0.10 * config_pressure
    )
    
    load_final = clamp(load_raw, 0.0, 1.0)
    feat.load_pressure = load_final
    
    print(f"\n加权计算:")
    print(f"  0.50 × 凶相位压力({phase_pressure:.3f}) = {0.50 * phase_pressure:.3f}")
    print(f"  0.25 × 凶星因子({malefic_factor:.3f}) = {0.25 * malefic_factor:.3f}")
    print(f"  0.15 × 宫位负担({house_burden:.3f}) = {0.15 * house_burden:.3f}")
    print(f"  0.10 × 配置压力({config_pressure:.3f}) = {0.10 * config_pressure:.3f}")
    print(f"  最终压力负荷: {load_final:.3f}")
    
    # 调试信息
    feat.debug['pressure_calculation'] = {
        'phase_pressure': phase_pressure,
        'saturn_pressure': saturn_pressure,
        'mars_pressure': mars_pressure,
        'pluto_pressure': pluto_pressure,
        'malefic_factor': malefic_factor,
        'house_burden': house_burden,
        'config_pressure': config_pressure,
        'load_raw': load_raw,
        'load_final': load_final
    }
    
    return load_final


# ============================================================================
# 4. 主题一致性计算（根据PRD 6.3节）
# ============================================================================

def compute_theme_coherence(
    feat: PlanetFeature,
    chart_data: ChartData
) -> float:
    """
    计算主题一致性（考虑相位格局）
    
    根据PRD中6.3节的算法实现。
    
    参数:
        feat: PlanetFeature对象（会被修改）
        chart_data: ChartData对象
    
    返回:
        计算后的特征值 [0, 1]
    
    注意：需要support_resources和load_pressure已计算
    """
    print(f"\n计算主题一致性特征:")
    print("=" * 40)
    
    S = feat.support_resources
    L = feat.load_pressure
    
    print(f"资源支持(S): {S:.3f}")
    print(f"压力负荷(L): {L:.3f}")
    print(f"差异绝对值: {abs(S - L):.3f}")
    
    # 基础一致性计算
    diff = abs(S - L)
    
    if diff < 0.15:
        # 平衡状态（差距小）
        base_coherence = 0.7
        print(f"状态: 平衡 (差异<0.15)，基础一致性: {base_coherence}")
    elif diff < 0.3:
        # 略不平衡
        base_coherence = 0.5
        print(f"状态: 略不平衡 (差异<0.3)，基础一致性: {base_coherence}")
    else:
        # 明显不平衡
        base_coherence = 0.3
        print(f"状态: 明显不平衡 (差异≥0.3)，基础一致性: {base_coherence}")
    
    # 相位格局修正
    pattern_adjustment = 0.0
    
    from .aspects import (
        has_grand_trine, has_kite,
        has_t_square, has_grand_cross
    )
    
    # 和谐格局增加一致性
    if has_grand_trine(chart_data):
        pattern_adjustment += 0.15
        print(f"检测到大三角格局，一致性+0.15")
    
    if has_kite(chart_data):
        pattern_adjustment += 0.15
        print(f"检测到风筝格局，一致性+0.15")
    
    # 紧张格局减少一致性
    if has_t_square(chart_data):
        pattern_adjustment -= 0.15
        print(f"检测到T三角格局，一致性-0.15")
    
    if has_grand_cross(chart_data):
        pattern_adjustment -= 0.15
        print(f"检测到大十字格局，一致性-0.15")
    
    # 行星状态修正
    planet_adjustment = 0.0
    
    if has_multiple_benefics_strong(chart_data):
        planet_adjustment += 0.10  # 多吉星强增加和谐
        print(f"多个吉星强势，一致性+0.10")
    
    if has_multiple_malefics_afflicted(chart_data):
        planet_adjustment -= 0.10  # 多凶星受损增加矛盾
        print(f"多个凶星受损，一致性-0.10")
    
    # 计算最终一致性
    coherence_with_patterns = base_coherence + pattern_adjustment + planet_adjustment
    final_coherence = clamp(coherence_with_patterns, 0.0, 1.0)
    
    feat.theme_coherence = final_coherence
    
    print(f"\n最终计算:")
    print(f"  基础一致性: {base_coherence:.3f}")
    print(f"  格局修正: {pattern_adjustment:+.3f}")
    print(f"  行星修正: {planet_adjustment:+.3f}")
    print(f"  小计: {coherence_with_patterns:.3f}")
    print(f"  最终主题一致性: {final_coherence:.3f}")
    
    # 调试信息
    feat.debug['coherence_calculation'] = {
        'support': S,
        'pressure': L,
        'diff': diff,
        'base_coherence': base_coherence,
        'pattern_adjustment': pattern_adjustment,
        'planet_adjustment': planet_adjustment,
        'coherence_with_patterns': coherence_with_patterns,
        'final_coherence': final_coherence
    }
    
    return final_coherence


# ============================================================================
# 5. 数据质量评估（根据PRD 6.4节）
# ============================================================================

def compute_data_quality(chart_data: ChartData) -> float:
    """
    计算数据质量（独立函数，返回数值）
    
    根据PRD中6.4节的算法实现。
    
    参数:
        chart_data: ChartData对象
    
    返回:
        [0, 1] 范围内的质量分数
    
    示例:
        >>> quality = compute_data_quality(chart_data)
        >>> print(f"数据质量: {quality:.3f}")
    """
    print(f"\n计算数据质量:")
    print("=" * 40)
    
    # 1. 出生时间精度
    time_accuracy = chart_data.time_accuracy
    time_weight = TIME_ACCURACY_WEIGHTS.get(time_accuracy, 0.3)
    print(f"时间精度 '{time_accuracy}': 权重 {time_weight:.2f}")
    
    # 2. 行星覆盖度
    traditional_planets = [Planet.SUN, Planet.MOON, Planet.MERCURY, Planet.VENUS, 
                          Planet.MARS, Planet.JUPITER, Planet.SATURN]
    outer_planets = [Planet.URANUS, Planet.NEPTUNE, Planet.PLUTO]
    
    # 统计存在的行星
    trad_count = sum(1 for p in traditional_planets if p in chart_data.planets)
    outer_count = sum(1 for p in outer_planets if p in chart_data.planets)
    
    print(f"传统行星: {trad_count}/7 存在")
    print(f"外行星: {outer_count}/3 存在")
    
    # 计算覆盖率
    trad_coverage = (trad_count / 7.0) * 0.8
    outer_coverage = (outer_count / 3.0) * 0.2
    planet_coverage = trad_coverage + outer_coverage
    
    print(f"行星覆盖度: {planet_coverage:.3f} (传统×0.8 + 外行星×0.2)")
    
    # 3. 技术覆盖度
    techniques = ['dignities', 'aspects', 'receptions', 'houses']
    
    # 检查是否计算了这些技术指标
    covered = 0
    for tech in techniques:
        # 检查是否有对应的计算属性
        if tech == 'dignities' and hasattr(chart_data, 'dignities_by_planet') and chart_data.dignities_by_planet:
            covered += 1
        elif tech == 'aspects' and hasattr(chart_data, 'aspect_matrix') and chart_data.aspect_matrix:
            covered += 1
        elif tech == 'receptions' and hasattr(chart_data, 'reception_matrix') and chart_data.reception_matrix:
            covered += 1
        elif tech == 'houses' and hasattr(chart_data, 'house_powers') and chart_data.house_powers:
            covered += 1
    
    technique_coverage = covered / len(techniques) if techniques else 0.0
    print(f"技术覆盖度: {technique_coverage:.3f} ({covered}/{len(techniques)}项已计算)")
    
    # 4. 特殊数据
    special_score = 1.0  # 基础分数
    
    if chart_data.has_fixed_stars:
        special_score += 0.2
        print(f"有恒星数据，特殊分+0.2")
    
    if chart_data.has_arabic_parts:
        special_score += 0.15
        print(f"有阿拉伯点，特殊分+0.15")
    
    if chart_data.has_antiscia:
        special_score += 0.1
        print(f"有映点，特殊分+0.1")
    
    if chart_data.has_parallels:
        special_score += 0.05
        print(f"有赤纬平行，特殊分+0.05")
    
    special_score = clamp(special_score, 1.0, 2.0)  # 限制在1.0-2.0范围
    special_factor = (special_score - 1.0)  # 转换为0-1范围
    print(f"特殊数据总分: {special_score:.2f}, 因子: {special_factor:.3f}")
    
    # 加权平均（根据PRD权重）
    data_quality = (
        0.35 * time_weight +
        0.25 * planet_coverage +
        0.20 * technique_coverage +
        0.20 * special_factor
    )
    
    final_quality = clamp(data_quality, 0.0, 1.0)
    
    print(f"\n加权计算:")
    print(f"  0.35 × 时间精度({time_weight:.3f}) = {0.35 * time_weight:.3f}")
    print(f"  0.25 × 行星覆盖({planet_coverage:.3f}) = {0.25 * planet_coverage:.3f}")
    print(f"  0.20 × 技术覆盖({technique_coverage:.3f}) = {0.20 * technique_coverage:.3f}")
    print(f"  0.20 × 特殊数据({special_factor:.3f}) = {0.20 * special_factor:.3f}")
    print(f"  最终数据质量: {final_quality:.3f}")
    
    return final_quality


# ============================================================================
# 6. 行星特征主函数（根据PRD 7.1节）
# ============================================================================

def compute_planet_features(
    focus_planet: Planet,
    chart_data: ChartData,
    transits: Optional[Dict[Planet, PlanetInfo]] = None
) -> PlanetFeature:
    """
    计算焦点行星的所有特征（主入口函数）
    
    根据PRD中7.1节的算法实现。
    
    参数:
        focus_planet: 焦点行星ID
        chart_data: ChartData对象
        transits: 流年行星数据（可选）
    
    返回:
        PlanetFeature对象
    
    示例:
        >>> feat = compute_planet_features(Planet.SUN, chart_data)
        >>> print(f"太阳特征: {feat.summary()}")
    """
    print("\n" + "=" * 60)
    print(f"开始计算 {focus_planet.value} 的所有特征")
    print("=" * 60)
    
    feat = PlanetFeature()
    
    # 1. 尊贵度（从全盘数据获取）
    feat.dignity = get_dignity_for_planet(focus_planet, chart_data)
    print(f"\n1. 尊贵度: {feat.dignity:+.3f}")
    
    # 2. 相位特征
    print(f"\n2. 相位特征:")
    feat.aspect_benefic, feat.aspect_malefic = compute_aspect_features_for_planet(
        focus_planet, chart_data, transits
    )
    print(f"  吉相位强度: {feat.aspect_benefic:.3f}")
    print(f"  凶相位强度: {feat.aspect_malefic:.3f}")
    
    # 3. 计算综合特征（这些函数会设置feat的其他属性）
    print(f"\n3. 综合特征计算:")
    compute_support_resources(feat, chart_data, focus_planet)
    compute_load_pressure(feat, chart_data, focus_planet)
    
    # 4. 主题一致性（需要support和pressure已计算）
    print(f"\n4. 主题一致性:")
    compute_theme_coherence(feat, chart_data)
    
    # 5. 数据质量（独立计算，但存储到feat）
    print(f"\n5. 数据质量:")
    feat.data_quality = compute_data_quality(chart_data)
    
    print("\n" + "=" * 60)
    print(f"{focus_planet.value} 的所有特征计算完成!")
    print("=" * 60)
    
    # 打印特征摘要
    print(feat.summary())
    
    # 验证特征值
    if not feat.validate():
        print("警告: 部分特征值超出有效范围!")
    
    return feat


def compute_features_for_multiple_planets(
    planet_list: List[Planet],
    chart_data: ChartData,
    transits: Optional[Dict[Planet, PlanetInfo]] = None
) -> Dict[Planet, PlanetFeature]:
    """
    批量计算多个行星的特征
    
    参数:
        planet_list: 行星列表
        chart_data: ChartData对象
        transits: 流年行星数据（可选）
    
    返回:
        行星特征字典
    
    示例:
        >>> features = compute_features_for_multiple_planets(
        >>>     [Planet.SUN, Planet.MOON], chart_data
        >>> )
        >>> for planet, feat in features.items():
        >>>     print(f"{planet.value}的支持资源: {feat.support_resources:.3f}")
    """
    results = {}
    
    print(f"\n批量计算 {len(planet_list)} 个行星的特征...")
    
    for planet in planet_list:
        print(f"\n--- 计算 {planet.value} ---")
        feat = compute_planet_features(planet, chart_data, transits)
        results[planet] = feat
    
    print(f"\n批量计算完成，共计算了 {len(results)} 个行星的特征")
    
    return results


# ============================================================================
# 7. 特征分析工具
# ============================================================================

def analyze_feature_distribution(
    features_dict: Dict[Planet, PlanetFeature]
) -> Dict[str, Any]:
    """
    分析特征分布情况
    
    参数:
        features_dict: 行星特征字典
    
    返回:
        特征分布分析结果
    """
    if not features_dict:
        return {}
    
    analysis = {
        'count': len(features_dict),
        'by_feature': {},
        'strongest_by_feature': {},
        'weakest_by_feature': {},
        'correlations': {}
    }
    
    # 收集所有特征值
    all_features = ['dignity', 'house_power', 'aspect_benefic', 'aspect_malefic',
                   'reception', 'support_resources', 'load_pressure',
                   'theme_coherence', 'data_quality']
    
    for feature_name in all_features:
        values = []
        for planet, feat in features_dict.items():
            value = getattr(feat, feature_name, 0.0)
            values.append((planet.value, value))
        
        if values:
            # 统计
            just_values = [v for _, v in values]
            analysis['by_feature'][feature_name] = {
                'mean': sum(just_values) / len(just_values),
                'max': max(just_values),
                'min': min(just_values),
                'std': (sum((v - sum(just_values)/len(just_values))**2 for v in just_values) / len(just_values))**0.5 if len(just_values) > 1 else 0.0
            }
            
            # 最强和最弱
            strongest = max(values, key=lambda x: x[1])
            weakest = min(values, key=lambda x: x[1])
            
            analysis['strongest_by_feature'][feature_name] = {
                'planet': strongest[0],
                'value': strongest[1]
            }
            analysis['weakest_by_feature'][feature_name] = {
                'planet': weakest[0],
                'value': weakest[1]
            }
    
    # 计算相关性（简化的相关性分析）
    # 这里可以添加特征间的相关性计算
    # 例如：支持资源和压力负荷通常负相关
    
    return analysis


def print_feature_comparison(features_dict: Dict[Planet, PlanetFeature]) -> None:
    """
    打印特征对比报告
    
    参数:
        features_dict: 行星特征字典
    """
    if not features_dict:
        print("无特征数据")
        return
    
    print("\n" + "=" * 80)
    print("行星特征对比报告")
    print("=" * 80)
    
    # 表头
    headers = ["行星", "尊贵度", "宫位力", "吉相位", "凶相位", "接纳", "支持", "压力", "一致性", "数据质量"]
    header_format = "{:<8} {:>8} {:>8} {:>8} {:>8} {:>8} {:>8} {:>8} {:>8} {:>8}"
    
    print(header_format.format(*headers))
    print("-" * 80)
    
    # 数据行
    for planet, feat in sorted(features_dict.items(), key=lambda x: x[0].value):
        row = [
            planet.value,
            f"{feat.dignity:+.3f}",
            f"{feat.house_power:+.3f}",
            f"{feat.aspect_benefic:.3f}",
            f"{feat.aspect_malefic:.3f}",
            f"{feat.reception:.3f}",
            f"{feat.support_resources:.3f}",
            f"{feat.load_pressure:.3f}",
            f"{feat.theme_coherence:.3f}",
            f"{feat.data_quality:.3f}"
        ]
        print(header_format.format(*row))
    
    print("=" * 80)
    
    # 摘要统计
    analysis = analyze_feature_distribution(features_dict)
    
    print("\n特征统计摘要:")
    for feature_name, stats in analysis['by_feature'].items():
        print(f"  {feature_name:15s}: 平均={stats['mean']:.3f}, 范围=[{stats['min']:.3f}, {stats['max']:.3f}]")
    
    print("\n最强特征:")
    for feature_name, strongest in analysis['strongest_by_feature'].items():
        print(f"  {feature_name:15s}: {strongest['planet']} ({strongest['value']:.3f})")
    
    print("\n最弱特征:")
    for feature_name, weakest in analysis['weakest_by_feature'].items():
        print(f"  {feature_name:15s}: {weakest['planet']} ({weakest['value']:.3f})")


# ============================================================================
# 8. 导出函数
# ============================================================================

__all__ = [
    # 辅助函数
    "has_multiple_benefics_strong",
    "has_multiple_malefics_afflicted",
    "detect_hard_configurations",
    "detect_positive_configurations",
    
    # 综合特征计算
    "compute_support_resources",
    "compute_load_pressure",
    "compute_theme_coherence",
    "compute_data_quality",
    
    # 行星特征主函数
    "compute_planet_features",
    "compute_features_for_multiple_planets",
    
    # 分析工具
    "analyze_feature_distribution",
    "print_feature_comparison",
]