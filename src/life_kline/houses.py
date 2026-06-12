"""
houses.py - 宫位力量计算系统

这个模块实现了星盘宫位力量的计算，包括：
1. 宫主星的本质尊贵
2. 宫内行星的影响
3. 宫位特殊配置
4. 宫位主题修正

注意：宫位力量计算不包含角续果宫（已在意外尊贵中计算）
"""

from typing import Dict, List, Optional, Set, Any, Tuple
import math

# 导入常量和模型
from .constants import (
    Planet, Sign, clamp,
    ANGULAR_HOUSES, SUCCEDENT_HOUSES, CADENT_HOUSES
)
from .models import ChartData, PlanetInfo
from .dignities import compute_essential_dignity_for_planet, get_dignity_for_planet


# ============================================================================
# 1. 辅助函数（宫位计算专用）
# ============================================================================

def get_house_lord(house_num: int, chart_data: ChartData) -> Optional[Planet]:
    """
    获取宫位的宫主星（行星守护该宫头星座）
    
    宫主星是守护宫头星座的行星，对宫位有重要影响。
    
    参数:
        house_num: 宫位编号（1-12）
        chart_data: ChartData对象
    
    返回:
        宫主星，如果无法确定则返回None
    
    示例:
        >>> get_house_lord(1, chart_data)  # 如果第1宫宫头是白羊座
        Planet.MARS  # 火星守护白羊座
    """
    # 这里需要星盘数据中有宫头星座信息
    # 由于ChartData目前没有直接存储宫头星座，我们需要假设这个信息存在
    
    # 在实际实现中，应该从chart_data中获取宫头星座
    # 这里我们先实现一个简化版本
    
    # 宫位与星座的对应关系（简化：假设第1宫是白羊座，第2宫是金牛座...）
    # 在实际占星软件中，这取决于上升星座和分宫制
    
    # 如果chart_data有houses属性（宫头星座列表）
    if hasattr(chart_data, 'houses') and chart_data.houses:
        # chart_data.houses应该是12个元素的列表，每个元素是(星座, 度数)
        if 1 <= house_num <= len(chart_data.houses):
            sign = chart_data.houses[house_num-1][0]  # 获取宫头星座
    else:
        # 简化：使用自然宫位制（白羊座第1宫，金牛座第2宫...）
        sign_list = list(Sign)
        if 1 <= house_num <= 12:
            sign = sign_list[house_num-1]  # 0-based索引
    
    # 根据星座找到守护行星
    # 每个星座有1-2个守护行星（庙宫）
    sign_to_lords: Dict[Sign, List[Planet]] = {}
    
    # 从DOMICILE_SIGNS反推星座的守护行星
    from .constants import DOMICILE_SIGNS
    for planet, signs in DOMICILE_SIGNS.items():
        for sign in signs:
            if sign not in sign_to_lords:
                sign_to_lords[sign] = []
            sign_to_lords[sign].append(planet)
    
    # 获取宫头星座的守护行星
    if 'sign' in locals() and sign in sign_to_lords:
        lords = sign_to_lords[sign]
        # 如果有多个守护行星，返回第一个（通常是主要守护行星）
        return lords[0] if lords else None
    
    return None


def get_planets_in_house(house_num: int, chart_data: ChartData) -> List[Planet]:
    """
    获取指定宫位中的所有行星
    
    参数:
        house_num: 宫位编号（1-12）
        chart_data: ChartData对象
    
    返回:
        该宫位中的行星列表
    
    示例:
        >>> get_planets_in_house(1, chart_data)
        [Planet.MARS, Planet.VENUS]  # 火星和金星在第1宫
    """
    planets_in_house = []
    
    # 遍历所有行星
    for planet, planet_info in chart_data.planets.items():
        if planet_info.house == house_num:
            planets_in_house.append(planet)
    
    return planets_in_house


def has_aspect_between(planet1: Planet, planet2: Planet, chart_data: ChartData) -> bool:
    """
    判断两个行星之间是否有相位
    
    简化版本：只检查基本相位（合、冲、刑、拱、六合）
    
    参数:
        planet1: 第一个行星
        planet2: 第二个行星
        chart_data: ChartData对象
    
    返回:
        bool: 是否有相位
    
    注意：这是一个简化实现，完整实现需要相位检测算法
    """
    if planet1 == planet2:
        return False
    
    # 获取行星的黄经
    info1 = chart_data.get_planet_info(planet1)
    info2 = chart_data.get_planet_info(planet2)
    
    if not info1 or not info2:
        return False
    
    # 计算绝对黄经
    long1 = info1.get_absolute_position()
    long2 = info2.get_absolute_position()
    
    # 计算角度差
    diff = abs(long1 - long2) % 360.0
    diff = min(diff, 360.0 - diff)
    
    # 主要相位及其容许度
    aspects = [
        (0, 8.5),      # 合相
        (60, 6.0),     # 六合
        (90, 8.0),     # 刑相
        (120, 8.0),    # 拱相
        (180, 10.0),   # 冲相
    ]
    
    # 检查是否在任何相位容许度内
    for aspect_angle, orb in aspects:
        if abs(diff - aspect_angle) <= orb:
            return True
    
    return False


def get_aspect_strength(planet1: Planet, planet2: Planet, chart_data: ChartData) -> float:
    """
    获取两个行星之间相位的强度
    
    强度计算基于容许度：容许度越小，强度越大
    
    参数:
        planet1: 第一个行星
        planet2: 第二个行星
        chart_data: ChartData对象
    
    返回:
        相位强度 [0, 1]
    """
    if planet1 == planet2:
        return 0.0
    
    info1 = chart_data.get_planet_info(planet1)
    info2 = chart_data.get_planet_info(planet2)
    
    if not info1 or not info2:
        return 0.0
    
    # 计算绝对黄经
    long1 = info1.get_absolute_position()
    long2 = info2.get_absolute_position()
    
    # 计算角度差
    diff = abs(long1 - long2) % 360.0
    diff = min(diff, 360.0 - diff)
    
    # 主要相位及其容许度、基本强度
    aspects = [
        (0, 8.5, 1.0),      # 合相
        (60, 6.0, 0.6),     # 六合
        (90, 8.0, 0.8),     # 刑相
        (120, 8.0, 0.9),    # 拱相
        (180, 10.0, 0.8),   # 冲相
    ]
    
    best_strength = 0.0
    
    for aspect_angle, orb, base_strength in aspects:
        distance = abs(diff - aspect_angle)
        
        if distance <= orb:
            # 计算强度：越精确（容许度越小）强度越大
            precision = 1.0 - (distance / orb)  # 精确度 [0, 1]
            strength = base_strength * precision
            best_strength = max(best_strength, strength)
    
    return best_strength


def detect_house_special_configs(house_num: int, chart_data: ChartData) -> float:
    """
    检测宫位的特殊配置
    
    特殊配置包括：宫内有吉星、宫内有凶星、宫内星有重要相位等
    
    参数:
        house_num: 宫位编号
        chart_data: ChartData对象
    
    返回:
        特殊配置加成分数 [-1, 1]
    """
    score = 0.0
    planets_in_house = get_planets_in_house(house_num, chart_data)
    
    if not planets_in_house:
        return 0.0
    
    # 检查宫内行星的性质
    for planet in planets_in_house:
        # 吉星加分
        if planet.is_benefic:
            score += 0.3
            print(f"调试: 第{house_num}宫有吉星{planet.value} +0.3")
        
        # 凶星减分
        if planet.is_malefic:
            score -= 0.3
            print(f"调试: 第{house_num}宫有凶星{planet.value} -0.3")
        
        # 外行星（现代占星中视为中性偏凶）
        if planet.is_outer:
            if chart_data.mode == 'MODERN':
                # 现代模式中，外行星通常被视为有挑战性
                score -= 0.2
                print(f"调试: 第{house_num}宫有外行星{planet.value}（现代模式） -0.2")
    
    # 检查宫内行星是否有重要相位（合相、冲相、刑相、拱相）
    for i, planet1 in enumerate(planets_in_house):
        for planet2 in planets_in_house[i+1:]:
            if has_aspect_between(planet1, planet2, chart_data):
                strength = get_aspect_strength(planet1, planet2, chart_data)
                if strength > 0.5:
                    score += 0.2 * strength
                    print(f"调试: 第{house_num}宫内{planet1.value}与{planet2.value}有强相位 +{0.2*strength:.2f}")
    
    # 检查宫主星的状态（通过尊贵度）
    lord = get_house_lord(house_num, chart_data)
    if lord:
        dignity = get_dignity_for_planet(lord, chart_data)
        if dignity > 0.3:
            score += 0.2
            print(f"调试: 第{house_num}宫主星{lord.value}尊贵度高 +0.2")
        elif dignity < -0.3:
            score -= 0.2
            print(f"调试: 第{house_num}宫主星{lord.value}尊贵度低 -0.2")
    
    return clamp(score, -1.0, 1.0)


def get_house_theme_bonus(house_num: int) -> float:
    """
    获取宫位主题修正
    
    根据不同宫位的主题（如财帛宫、兄弟宫等）给予轻微修正
    这是独立于角续果宫之外的额外修正
    
    参数:
        house_num: 宫位编号
    
    返回:
        主题修正分数 [-0.5, 0.5]
    """
    # 宫位主题修正表
    # 正数表示该宫位通常有正面影响，负数表示通常有挑战性
    
    theme_bonus: Dict[int, float] = {
        1: 0.2,   # 第1宫（命宫）：自我、个性 - 轻微正面
        2: 0.3,   # 第2宫（财帛宫）：金钱、资源 - 正面
        3: 0.1,   # 第3宫（兄弟宫）：沟通、短途旅行 - 中性偏正
        4: 0.2,   # 第4宫（田宅宫）：家庭、根基 - 正面
        5: 0.4,   # 第5宫（子女宫）：创意、爱情、娱乐 - 较强正面
        6: -0.3,  # 第6宫（奴仆宫）：健康、工作 - 挑战性
        7: 0.2,   # 第7宫（夫妻宫）：关系、合作 - 正面
        8: -0.4,  # 第8宫（疾厄宫）：死亡、他人资源 - 较强挑战性
        9: 0.3,   # 第9宫（迁移宫）：高等教育、长途旅行 - 正面
        10: 0.4,  # 第10宫（官禄宫）：事业、地位 - 较强正面
        11: 0.3,  # 第11宫（福德宫）：朋友、愿望 - 正面
        12: -0.5, # 第12宫（玄秘宫）：隐藏、灵性、限制 - 较强挑战性
    }
    
    bonus = theme_bonus.get(house_num, 0.0)
    print(f"调试: 第{house_num}宫主题修正: {bonus:+.2f}")
    
    return bonus


def detect_house_special_patterns(chart_data: ChartData, house_num: int) -> Dict[str, Any]:
    """
    检测宫位的特殊格局
    
    参数:
        chart_data: ChartData对象
        house_num: 宫位编号
    
    返回:
        特殊格局信息
    """
    patterns = {}
    planets_in_house = get_planets_in_house(house_num, chart_data)
    
    if not planets_in_house:
        return patterns
    
    # 检查是否有行星聚集（3个或更多行星在同一宫）
    if len(planets_in_house) >= 3:
        patterns['stellium'] = {
            'planets': [p.value for p in planets_in_house],
            'count': len(planets_in_house),
            'strength': min(0.5, len(planets_in_house) * 0.15)  # 最多0.5分
        }
        print(f"调试: 第{house_num}宫有行星聚集（{len(planets_in_house)}颗行星）")
    
    # 检查宫内是否有合相
    conjunctions = []
    for i, p1 in enumerate(planets_in_house):
        for p2 in planets_in_house[i+1:]:
            if has_aspect_between(p1, p2, chart_data):
                # 检查是否是合相（角度差小于8度）
                info1 = chart_data.get_planet_info(p1)
                info2 = chart_data.get_planet_info(p2)
                if info1 and info2:
                    diff = abs(info1.get_absolute_position() - info2.get_absolute_position()) % 360.0
                    diff = min(diff, 360.0 - diff)
                    if diff <= 8.0:
                        conjunctions.append((p1.value, p2.value, diff))
    
    if conjunctions:
        patterns['conjunctions'] = conjunctions
        print(f"调试: 第{house_num}宫内有{len(conjunctions)}组合相")
    
    return patterns


# ============================================================================
# 2. 宫位力量计算（核心函数，根据PRD 3.1节）
# ============================================================================

def compute_all_house_powers(chart_data: ChartData) -> Dict[int, float]:
    """
    计算所有宫位的力量，存储到chart_data.house_powers
    
    根据PRD中3.1节的算法实现。
    注意：不含角续果宫（已在意外尊贵中计算）
    
    参数:
        chart_data: ChartData对象
    
    返回:
        宫位力量字典 {宫位编号: 力量值}
    
    示例:
        >>> chart = ChartData()
        >>> # 添加行星数据...
        >>> house_powers = compute_all_house_powers(chart)
        >>> print(house_powers[1])  # 第1宫的力量
        0.5
    """
    house_powers = {}
    
    print("=" * 60)
    print("开始计算全盘宫位力量...")
    print(f"计算模式: {chart_data.mode.value}")
    print("=" * 60)
    
    for house_num in range(1, 13):
        print(f"\n计算第{house_num}宫力量:")
        print("-" * 40)
        
        strength = 0.0
        
        # 1. 宫主星本质尊贵（权重40%）
        lord = get_house_lord(house_num, chart_data)
        lord_essential_score = 0.0
        
        if lord:
            # 计算宫主星的本质尊贵原始分
            essential_raw = compute_essential_dignity_for_planet(lord, chart_data)
            # 本质尊贵归一化：除以10.0后限制在[-1, 1]
            essential_norm = clamp(essential_raw / 10.0, -1.0, 1.0)
            
            strength += 0.4 * essential_norm
            lord_essential_score = essential_norm
            
            print(f"宫主星: {lord.value}")
            print(f"本质尊贵原始分: {essential_raw:.2f}")
            print(f"归一化尊贵度: {essential_norm:.3f}")
            print(f"宫主星贡献: {0.4 * essential_norm:.3f} (权重0.4)")
        else:
            print(f"警告: 第{house_num}宫无法确定宫主星")
        
        # 2. 宫内行星影响
        planets_in_house = get_planets_in_house(house_num, chart_data)
        
        if planets_in_house:
            print(f"宫内行星: {[p.value for p in planets_in_house]}")
            
            aspect_contribution = 0.0
            planet_contribution = 0.0
            
            for planet in planets_in_house:
                # 2.1 宫内行星与宫主星的相位（权重15%）
                if lord and has_aspect_between(planet, lord, chart_data):
                    aspect_strength = get_aspect_strength(planet, lord, chart_data)
                    aspect_contribution += aspect_strength
                    
                    print(f"  {planet.value}与宫主星{lord.value}有相位，强度: {aspect_strength:.3f}")
                
                # 2.2 宫内行星本质状态（权重5%，轻度影响）
                planet_essential = compute_essential_dignity_for_planet(planet, chart_data)
                planet_norm = clamp(planet_essential / 10.0, -1.0, 1.0)
                planet_contribution += planet_norm
                
                print(f"  {planet.value}本质尊贵: {planet_essential:.2f}, 归一化: {planet_norm:.3f}")
            
            # 计算平均贡献
            if planets_in_house:
                avg_aspect = aspect_contribution / len(planets_in_house) if planets_in_house else 0.0
                avg_planet = planet_contribution / len(planets_in_house) if planets_in_house else 0.0
                
                strength += 0.15 * avg_aspect
                strength += 0.05 * avg_planet
                
                print(f"相位平均贡献: {avg_aspect:.3f} × 0.15 = {0.15 * avg_aspect:.3f}")
                print(f"行星平均贡献: {avg_planet:.3f} × 0.05 = {0.05 * avg_planet:.3f}")
        else:
            print(f"宫内行星: 无")
        
        # 3. 宫位特殊配置（权重20%，不重复角续果）
        config_bonus = detect_house_special_configs(house_num, chart_data)
        strength += 0.2 * config_bonus
        
        print(f"特殊配置: {config_bonus:.3f} × 0.2 = {0.2 * config_bonus:.3f}")
        
        # 4. 宫位主题修正（独立于角续果）
        theme_bonus = get_house_theme_bonus(house_num)
        strength += theme_bonus
        
        print(f"主题修正: {theme_bonus:+.3f}")
        
        # 最终限制在[-1, 1]范围内
        final_strength = clamp(strength, -1.0, 1.0)
        house_powers[house_num] = final_strength
        
        print(f"第{house_num}宫总力量: {final_strength:.3f}")
        
        # 记录调试信息
        if 'debug' not in chart_data.__dict__:
            chart_data.debug = {}
        
        chart_data.debug[f'house_{house_num}'] = {
            'lord': lord.value if lord else None,
            'lord_essential': lord_essential_score,
            'planets_in_house': [p.value for p in planets_in_house],
            'config_bonus': config_bonus,
            'theme_bonus': theme_bonus,
            'raw_strength': strength,
            'final_strength': final_strength
        }
    
    # 存储到chart_data
    chart_data.house_powers = house_powers
    
    print("\n" + "=" * 60)
    print("全盘宫位力量计算完成!")
    print("=" * 60)
    
    # 打印摘要
    print("\n宫位力量摘要:")
    for house_num in range(1, 13):
        strength = house_powers.get(house_num, 0.0)
        
        if strength > 0.3:
            rating = "很强"
        elif strength > 0.1:
            rating = "较强"
        elif strength > -0.1:
            rating = "中等"
        elif strength > -0.3:
            rating = "较弱"
        else:
            rating = "很弱"
        
        house_type = chart_data.get_house_type(house_num)
        print(f"  第{house_num:2d}宫 ({house_type:8s}): {strength:+.3f} ({rating})")
    
    return house_powers


def get_house_power_for_planet(planet: Planet, chart_data: ChartData) -> float:
    """
    获取行星所在宫位的宫位力量
    
    参数:
        planet: 行星
        chart_data: ChartData对象
    
    返回:
        宫位力量值（[-1, 1]），如果行星不在星盘中则返回0.0
    
    示例:
        >>> power = get_house_power_for_planet(Planet.SUN, chart_data)
        >>> print(f"太阳所在宫位的力量: {power:.3f}")
    """
    # 检查是否已经计算过宫位力量
    if not hasattr(chart_data, 'house_powers') or not chart_data.house_powers:
        print(f"提示: 宫位力量未计算，先计算全盘宫位力量...")
        compute_all_house_powers(chart_data)
    
    # 获取行星信息
    planet_info = chart_data.get_planet_info(planet)
    if not planet_info:
        print(f"警告: 行星 {planet.value} 不在星盘中")
        return 0.0
    
    # 获取行星所在宫位
    house_num = planet_info.house
    if house_num == 0:  # 宫位未设置
        print(f"警告: 行星 {planet.value} 的宫位未设置")
        return 0.0
    
    # 返回宫位力量
    return chart_data.house_powers.get(house_num, 0.0)


def compute_house_power_for_single(house_num: int, chart_data: ChartData) -> float:
    """
    计算单个宫位的力量（增量更新时使用）
    
    参数:
        house_num: 宫位编号
        chart_data: ChartData对象
    
    返回:
        该宫位的力量值
    
    注意：用于增量更新，避免重新计算所有宫位
    """
    print(f"计算单个宫位力量: 第{house_num}宫")
    
    # 重用compute_all_house_powers中的逻辑
    # 这里简化为直接调用完整的计算并返回该宫位的结果
    if not hasattr(chart_data, 'house_powers') or not chart_data.house_powers:
        compute_all_house_powers(chart_data)
    
    return chart_data.house_powers.get(house_num, 0.0)


# ============================================================================
# 3. 宫位分析工具
# ============================================================================

def analyze_house_distribution(chart_data: ChartData) -> Dict[str, Any]:
    """
    分析宫位分布情况
    
    参数:
        chart_data: ChartData对象
    
    返回:
        宫位分布分析结果
    """
    if not hasattr(chart_data, 'house_powers') or not chart_data.house_powers:
        compute_all_house_powers(chart_data)
    
    house_powers = chart_data.house_powers
    
    # 计算统计数据
    values = list(house_powers.values())
    
    analysis = {
        'count': len(values),
        'mean': sum(values) / len(values) if values else 0.0,
        'max': max(values) if values else 0.0,
        'min': min(values) if values else 0.0,
        'strong_houses': [],    # 力量强的宫位（>0.3）
        'weak_houses': [],      # 力量弱的宫位（<-0.3）
        'balanced_houses': [],  # 平衡的宫位（-0.1到0.1）
    }
    
    # 分类宫位
    for house_num, power in house_powers.items():
        house_info = {
            'house': house_num,
            'power': power,
            'type': chart_data.get_house_type(house_num),
            'planets': [p.value for p in get_planets_in_house(house_num, chart_data)]
        }
        
        if power > 0.3:
            analysis['strong_houses'].append(house_info)
        elif power < -0.3:
            analysis['weak_houses'].append(house_info)
        elif -0.1 <= power <= 0.1:
            analysis['balanced_houses'].append(house_info)
    
    # 最强和最弱宫位
    if house_powers:
        strongest = max(house_powers.items(), key=lambda x: x[1])
        weakest = min(house_powers.items(), key=lambda x: x[1])
        
        analysis['strongest_house'] = {
            'house': strongest[0],
            'power': strongest[1],
            'planets': [p.value for p in get_planets_in_house(strongest[0], chart_data)]
        }
        
        analysis['weakest_house'] = {
            'house': weakest[0],
            'power': weakest[1],
            'planets': [p.value for p in get_planets_in_house(weakest[0], chart_data)]
        }
    
    # 按宫位类型统计
    angular_powers = []
    succedent_powers = []
    cadent_powers = []
    
    for house_num, power in house_powers.items():
        house_type = chart_data.get_house_type(house_num)
        
        if house_type == 'angular':
            angular_powers.append(power)
        elif house_type == 'succedent':
            succedent_powers.append(power)
        elif house_type == 'cadent':
            cadent_powers.append(power)
    
    analysis['by_type'] = {
        'angular': {
            'count': len(angular_powers),
            'mean': sum(angular_powers) / len(angular_powers) if angular_powers else 0.0,
            'houses': [h for h in range(1, 13) if chart_data.get_house_type(h) == 'angular']
        },
        'succedent': {
            'count': len(succedent_powers),
            'mean': sum(succedent_powers) / len(succedent_powers) if succedent_powers else 0.0,
            'houses': [h for h in range(1, 13) if chart_data.get_house_type(h) == 'succedent']
        },
        'cadent': {
            'count': len(cadent_powers),
            'mean': sum(cadent_powers) / len(cadent_powers) if cadent_powers else 0.0,
            'houses': [h for h in range(1, 13) if chart_data.get_house_type(h) == 'cadent']
        }
    }
    
    return analysis


def print_house_report(chart_data: ChartData) -> None:
    """
    打印宫位详细报告
    
    参数:
        chart_data: ChartData对象
    """
    if not hasattr(chart_data, 'house_powers') or not chart_data.house_powers:
        compute_all_house_powers(chart_data)
    
    house_powers = chart_data.house_powers
    
    print("\n" + "=" * 70)
    print("宫位力量详细报告")
    print("=" * 70)
    
    # 按力量排序
    sorted_houses = sorted(house_powers.items(), key=lambda x: x[1], reverse=True)
    
    for house_num, power in sorted_houses:
        # 获取宫位信息
        house_type = chart_data.get_house_type(house_num)
        planets_in_house = get_planets_in_house(house_num, chart_data)
        lord = get_house_lord(house_num, chart_data)
        
        # 获取力量描述
        if power > 0.7:
            desc = "极其强势"
        elif power > 0.4:
            desc = "非常强势"
        elif power > 0.1:
            desc = "略微强势"
        elif power > -0.1:
            desc = "基本平衡"
        elif power > -0.4:
            desc = "略微弱势"
        elif power > -0.7:
            desc = "非常弱势"
        else:
            desc = "极其弱势"
        
        # 打印宫位信息
        print(f"\n第{house_num:2d}宫 ({house_type:8s}):")
        print(f"  宫位力量: {power:+.3f} ({desc})")
        
        if lord:
            print(f"  宫主星: {lord.value}")
        
        if planets_in_house:
            planets_str = ", ".join([p.value for p in planets_in_house])
            print(f"  宫内行星: {planets_str} ({len(planets_in_house)}颗)")
        else:
            print(f"  宫内行星: 无")
        
        # 打印调试信息（如果存在）
        debug_key = f'house_{house_num}'
        if debug_key in chart_data.debug:
            debug_info = chart_data.debug[debug_key]
            if 'lord_essential' in debug_info:
                print(f"  宫主星尊贵贡献: {debug_info.get('lord_essential', 0):.3f}")
            if 'config_bonus' in debug_info:
                print(f"  特殊配置加成: {debug_info.get('config_bonus', 0):+.3f}")
            if 'theme_bonus' in debug_info:
                print(f"  主题修正: {debug_info.get('theme_bonus', 0):+.3f}")
    
    print("\n" + "=" * 70)
    print("报告结束")
    print("=" * 70)


def find_strongest_houses(chart_data: ChartData, limit: int = 3) -> List[Dict[str, Any]]:
    """
    找出力量最强的几个宫位
    
    参数:
        chart_data: ChartData对象
        limit: 返回的数量限制
    
    返回:
        最强宫位列表
    """
    if not hasattr(chart_data, 'house_powers') or not chart_data.house_powers:
        compute_all_house_powers(chart_data)
    
    # 按力量排序
    sorted_houses = sorted(
        chart_data.house_powers.items(),
        key=lambda x: x[1],
        reverse=True
    )[:limit]
    
    result = []
    for house_num, power in sorted_houses:
        planets_in_house = get_planets_in_house(house_num, chart_data)
        lord = get_house_lord(house_num, chart_data)
        
        result.append({
            'house': house_num,
            'power': power,
            'type': chart_data.get_house_type(house_num),
            'lord': lord.value if lord else None,
            'planets': [p.value for p in planets_in_house],
            'planet_count': len(planets_in_house)
        })
    
    return result


def find_weakest_houses(chart_data: ChartData, limit: int = 3) -> List[Dict[str, Any]]:
    """
    找出力量最弱的几个宫位
    
    参数:
        chart_data: ChartData对象
        limit: 返回的数量限制
    
    返回:
        最弱宫位列表
    """
    if not hasattr(chart_data, 'house_powers') or not chart_data.house_powers:
        compute_all_house_powers(chart_data)
    
    # 按力量排序（升序）
    sorted_houses = sorted(
        chart_data.house_powers.items(),
        key=lambda x: x[1]
    )[:limit]
    
    result = []
    for house_num, power in sorted_houses:
        planets_in_house = get_planets_in_house(house_num, chart_data)
        lord = get_house_lord(house_num, chart_data)
        
        result.append({
            'house': house_num,
            'power': power,
            'type': chart_data.get_house_type(house_num),
            'lord': lord.value if lord else None,
            'planets': [p.value for p in planets_in_house],
            'planet_count': len(planets_in_house)
        })
    
    return result


# ============================================================================
# 4. 增量更新支持（根据PRD性能优化部分）
# ============================================================================

def update_house_powers_on_change(chart_data: ChartData, changed_planets: List[Planet]) -> None:
    """
    增量更新：只重新计算受影响的宫位
    
    当行星位置发生变化时，只更新相关宫位的力量，
    避免重新计算所有宫位，提高性能。
    
    参数:
        chart_data: ChartData对象
        changed_planets: 发生变化的行星列表
    """
    if not hasattr(chart_data, 'house_powers') or not chart_data.house_powers:
        # 如果还没有计算过，直接计算全盘
        compute_all_house_powers(chart_data)
        return
    
    print(f"增量更新宫位力量，受影响行星: {[p.value for p in changed_planets]}")
    
    # 找出所有受影响的宫位
    affected_houses: Set[int] = set()
    
    for planet in changed_planets:
        planet_info = chart_data.get_planet_info(planet)
        if planet_info and planet_info.house != 0:
            affected_houses.add(planet_info.house)
    
    print(f"受影响的宫位: {sorted(affected_houses)}")
    
    # 重新计算受影响的宫位
    for house_num in affected_houses:
        old_power = chart_data.house_powers.get(house_num, 0.0)
        
        # 重新计算该宫位力量
        strength = 0.0
        lord = get_house_lord(house_num, chart_data)
        
        # 1. 宫主星本质尊贵
        if lord:
            essential_raw = compute_essential_dignity_for_planet(lord, chart_data)
            essential_norm = clamp(essential_raw / 10.0, -1.0, 1.0)
            strength += 0.4 * essential_norm
        
        # 2. 宫内行星影响
        planets_in_house = get_planets_in_house(house_num, chart_data)
        
        if planets_in_house:
            aspect_contribution = 0.0
            planet_contribution = 0.0
            
            for planet in planets_in_house:
                if lord and has_aspect_between(planet, lord, chart_data):
                    aspect_strength = get_aspect_strength(planet, lord, chart_data)
                    aspect_contribution += aspect_strength
                
                planet_essential = compute_essential_dignity_for_planet(planet, chart_data)
                planet_norm = clamp(planet_essential / 10.0, -1.0, 1.0)
                planet_contribution += planet_norm
            
            if planets_in_house:
                avg_aspect = aspect_contribution / len(planets_in_house)
                avg_planet = planet_contribution / len(planets_in_house)
                strength += 0.15 * avg_aspect + 0.05 * avg_planet
        
        # 3. 宫位特殊配置
        config_bonus = detect_house_special_configs(house_num, chart_data)
        strength += 0.2 * config_bonus
        
        # 4. 宫位主题修正
        theme_bonus = get_house_theme_bonus(house_num)
        strength += theme_bonus
        
        # 更新力量值
        new_power = clamp(strength, -1.0, 1.0)
        chart_data.house_powers[house_num] = new_power
        
        print(f"第{house_num}宫力量更新: {old_power:.3f} → {new_power:.3f} (变化: {new_power - old_power:+.3f})")
    
    print("宫位力量增量更新完成")


# ============================================================================
# 5. 导出函数
# ============================================================================

__all__ = [
    # 宫位力量计算
    "compute_all_house_powers",
    "get_house_power_for_planet",
    "compute_house_power_for_single",
    
    # 辅助函数
    "get_house_lord",
    "get_planets_in_house",
    "has_aspect_between",
    "get_aspect_strength",
    "detect_house_special_configs",
    "get_house_theme_bonus",
    "detect_house_special_patterns",
    
    # 分析工具
    "analyze_house_distribution",
    "print_house_report",
    "find_strongest_houses",
    "find_weakest_houses",
    
    # 增量更新
    "update_house_powers_on_change",
]