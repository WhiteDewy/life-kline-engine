"""
receptions.py - 接纳互容系统

这个模块实现了古典占星学中的接纳（Reception）计算，包括：
1. 接纳类型检测（庙宫接纳、擢升接纳等）
2. 互容（Mutual Reception）计算
3. 接纳矩阵构建
4. 接纳特征提取

遵循莉莉《基督占星》体系，提供完整接纳规则。
"""

from typing import Dict, List, Optional, Tuple, Any
from enum import Enum

# 导入常量和模型
from .constants import (
    Planet, Sign, CalculationMode,
    DOMICILE_SIGNS, EXALTATION_SIGNS, DETRIMENT_SIGNS, FALL_SIGNS,
    RECEPTION_WEIGHTS, clamp
)
from .models import ChartData, PlanetInfo


# ============================================================================
# 1. 接纳类型定义和检测
# ============================================================================

class ReceptionType(str, Enum):
    """接纳类型枚举"""
    NONE = "NONE"                 # 无接纳
    DOMICILE = "DOMICILE"         # 庙宫接纳（行星在对方的庙宫）
    EXALTATION = "EXALTATION"     # 擢升接纳（行星在对方的擢升宫）
    DETRIMENT = "DETRIMENT"       # 失势接纳（行星在对方的失势宫）- 通常不考虑
    FALL = "FALL"                 # 落陷接纳（行星在对方的落陷宫）- 通常不考虑
    TRIPLICITY = "TRIPLICITY"     # 三分接纳（行星在对方的三分宫）
    TERM = "TERM"                 # 界接纳（行星在对方的界）
    FACE = "FACE"                 # 面接纳（行星在对方的面）
    
    # 互容类型（双向接纳）
    MUTUAL_DOMICILE = "MUTUAL_DOMICILE"      # 互相庙宫接纳
    MUTUAL_EXALTATION = "MUTUAL_EXALTATION"  # 互相擢升接纳
    MUTUAL_OTHER = "MUTUAL_OTHER"            # 其他互容


def check_reception_detail(
    planet1: Planet,
    planet2: Planet,
    chart_data: ChartData
) -> Dict[str, Any]:
    """
    检查行星1对行星2的接纳详情
    
    参数:
        planet1: 接纳方行星（检查此行星是否接纳对方）
        planet2: 被接纳方行星
        chart_data: ChartData对象
    
    返回:
        接纳详情字典，包含类型和强度
    
    示例:
        >>> detail = check_reception_detail(Planet.SUN, Planet.MOON, chart_data)
        >>> if detail['type'] != ReceptionType.NONE:
        >>>     print(f"太阳接纳月亮: {detail['type'].value}")
    """
    if planet1 == planet2:
        return {'type': ReceptionType.NONE, 'strength': 0.0}
    
    # 获取行星信息
    info1 = chart_data.get_planet_info(planet1)
    info2 = chart_data.get_planet_info(planet2)
    
    if not info1 or not info2:
        return {'type': ReceptionType.NONE, 'strength': 0.0}
    
    sign1 = info1.sign  # 行星1所在的星座
    sign2 = info2.sign  # 行星2所在的星座
    
    # 1. 庙宫接纳（Domicile Reception）
    # 行星1在行星2的庙宫中（即行星1的星座是行星2守护的星座）
    if sign1 in DOMICILE_SIGNS.get(planet2, []):
        return {
            'type': ReceptionType.DOMICILE,
            'strength': 1.0,  # 庙宫接纳最强
            'description': f"{planet1.value}在{planet2.value}的庙宫{sign1.value}中",
            'planets': (planet1.value, planet2.value),
            'signs': (sign1.value, sign2.value)
        }
    
    # 2. 擢升接纳（Exaltation Reception）
    # 行星1在行星2的擢升宫中
    if sign1 in EXALTATION_SIGNS.get(planet2, []):
        # 检查是否接近擢升度数
        strength = 1.0
        if planet2 in EXALTATION_SIGNS:  # 行星2有擢升度数定义
            # 可以增加接近擢升度数的强度调整
            pass
        
        return {
            'type': ReceptionType.EXALTATION,
            'strength': 0.8,  # 擢升接纳稍弱于庙宫接纳
            'description': f"{planet1.value}在{planet2.value}的擢升宫{sign1.value}中",
            'planets': (planet1.value, planet2.value),
            'signs': (sign1.value, sign2.value)
        }
    
    # 3. 失势和落陷接纳（通常不考虑或视为负面）
    # 古典占星中通常不考虑失势和落陷的接纳，因为它们是负面状态
    # 但为了完整性，这里仍然检测
    
    if sign1 in DETRIMENT_SIGNS.get(planet2, []):
        return {
            'type': ReceptionType.DETRIMENT,
            'strength': -0.5,  # 负面接纳
            'description': f"{planet1.value}在{planet2.value}的失势宫{sign1.value}中（负面）",
            'planets': (planet1.value, planet2.value),
            'signs': (sign1.value, sign2.value)
        }
    
    if sign1 in FALL_SIGNS.get(planet2, []):
        return {
            'type': ReceptionType.FALL,
            'strength': -0.4,  # 负面接纳
            'description': f"{planet1.value}在{planet2.value}的落陷宫{sign1.value}中（负面）",
            'planets': (planet1.value, planet2.value),
            'signs': (sign1.value, sign2.value)
        }
    
    # 4. 其他接纳类型（三分、界、面）
    # 注意：这里需要实现get_term_lord和get_face_lord函数
    # 这些函数在dignities.py中已经实现，但这里需要导入或重新实现
    
    # 暂时省略三分、界、面的详细检测，只考虑庙宫和擢升接纳
    
    return {'type': ReceptionType.NONE, 'strength': 0.0}


def check_mutual_reception(
    planet1: Planet,
    planet2: Planet,
    chart_data: ChartData
) -> Optional[Dict[str, Any]]:
    """
    检查两个行星是否互容（互相接纳）
    
    参数:
        planet1: 第一个行星
        planet2: 第二个行星
        chart_data: ChartData对象
    
    返回:
        互容详情字典，如果没有互容则返回None
    
    示例:
        >>> mutual = check_mutual_reception(Planet.VENUS, Planet.MARS, chart_data)
        >>> if mutual:
        >>>     print(f"金星和火星互容: {mutual['type'].value}")
    """
    if planet1 == planet2:
        return None
    
    # 检查双向接纳
    rec1 = check_reception_detail(planet1, planet2, chart_data)
    rec2 = check_reception_detail(planet2, planet1, chart_data)
    
    has_rec1 = rec1['type'] != ReceptionType.NONE
    has_rec2 = rec2['type'] != ReceptionType.NONE
    
    if has_rec1 and has_rec2:
        # 互容成立
        mutual_type = None
        description = ""
        
        # 确定互容类型
        if (rec1['type'] == ReceptionType.DOMICILE and 
            rec2['type'] == ReceptionType.DOMICILE):
            mutual_type = ReceptionType.MUTUAL_DOMICILE
            description = f"{planet1.value}和{planet2.value}互相庙宫接纳"
        elif (rec1['type'] == ReceptionType.EXALTATION and 
              rec2['type'] == ReceptionType.EXALTATION):
            mutual_type = ReceptionType.MUTUAL_EXALTATION
            description = f"{planet1.value}和{planet2.value}互相擢升接纳"
        else:
            mutual_type = ReceptionType.MUTUAL_OTHER
            description = f"{planet1.value}和{planet2.value}互容"
        
        # 计算平均强度
        avg_strength = (rec1['strength'] + rec2['strength']) / 2.0
        
        return {
            'type': mutual_type,
            'strength': avg_strength,
            'description': description,
            'planets': (planet1.value, planet2.value),
            'reception1': rec1,
            'reception2': rec2
        }
    
    return None


# ============================================================================
# 2. 接纳评分函数（根据PRD 5.2节）
# ============================================================================

def compute_reception_score(
    planet1: Planet,
    planet2: Planet,
    chart_data: ChartData
) -> float:
    """
    计算两行星间接纳分数（使用统一权重表）
    
    根据PRD中5.2节的算法实现。
    
    参数:
        planet1: 行星1
        planet2: 行星2
        chart_data: ChartData对象
    
    返回:
        接纳分数
    
    示例:
        >>> score = compute_reception_score(Planet.SUN, Planet.MOON, chart_data)
        >>> print(f"太阳对月亮的接纳分数: {score:.2f}")
    """
    if planet1 == planet2:
        return 0.0
    
    print(f"计算接纳分数: {planet1.value} ↔ {planet2.value}")
    
    # 检查双向接纳（互容）
    mutual = check_mutual_reception(planet1, planet2, chart_data)
    
    if mutual:
        mutual_type = mutual['type']
        
        if mutual_type == ReceptionType.MUTUAL_DOMICILE:
            score = RECEPTION_WEIGHTS['MUTUAL_DOMICILE']  # 固定1.5
            print(f"  互容类型: 互相庙宫接纳，分数: {score}")
        elif mutual_type == ReceptionType.MUTUAL_EXALTATION:
            score = RECEPTION_WEIGHTS['MUTUAL_EXALTATION'] if 'MUTUAL_EXALTATION' in RECEPTION_WEIGHTS else 1.3
            print(f"  互容类型: 互相擢升接纳，分数: {score}")
        else:
            score = RECEPTION_WEIGHTS['MUTUAL_OTHER']  # 固定1.2
            print(f"  互容类型: 其他互容，分数: {score}")
        
        return score
    
    # 检查单向接纳
    rec1 = check_reception_detail(planet1, planet2, chart_data)  # 1接纳2
    rec2 = check_reception_detail(planet2, planet1, chart_data)  # 2接纳1
    
    has_rec1 = rec1['type'] != ReceptionType.NONE
    has_rec2 = rec2['type'] != ReceptionType.NONE
    
    if has_rec1:
        rec_type = rec1['type'].value
        weight_key = rec_type if rec_type in RECEPTION_WEIGHTS else rec_type.upper()
        score = RECEPTION_WEIGHTS.get(weight_key, 0.0)
        
        print(f"  单向接纳: {planet1.value}接纳{planet2.value} ({rec1['type'].value})，分数: {score}")
        return score
    
    if has_rec2:
        rec_type = rec2['type'].value
        weight_key = rec_type if rec_type in RECEPTION_WEIGHTS else rec_type.upper()
        score = RECEPTION_WEIGHTS.get(weight_key, 0.0)
        
        print(f"  单向接纳: {planet2.value}接纳{planet1.value} ({rec2['type'].value})，分数: {score}")
        return score
    
    # 无接纳
    print(f"  无接纳")
    return 0.0


# ============================================================================
# 3. 全盘接纳矩阵计算（根据PRD 5.1节）
# ============================================================================

def compute_all_receptions(chart_data: ChartData) -> Dict[Planet, Dict[Planet, float]]:
    """
    计算全盘接纳矩阵，存储到chart_data.reception_matrix
    
    根据PRD中5.1节的算法实现。
    
    参数:
        chart_data: ChartData对象
    
    返回:
        接纳矩阵（嵌套字典）
    
    示例:
        >>> matrix = compute_all_receptions(chart_data)
        >>> print(f"太阳对月亮的接纳分数: {matrix[Planet.SUN][Planet.MOON]:.2f}")
    """
    # 获取所有行星
    all_planets = list(chart_data.planets.keys())
    
    if not all_planets:
        print("警告: 星盘中无行星")
        return {}
    
    # 初始化矩阵
    matrix: Dict[Planet, Dict[Planet, float]] = {
        p: {p2: 0.0 for p2 in all_planets} for p in all_planets
    }
    
    print("=" * 60)
    print("开始计算全盘接纳矩阵...")
    print("=" * 60)
    
    mutual_receptions = []  # 记录互容关系
    
    # 计算所有行星对的接纳分数
    for i, p1 in enumerate(all_planets):
        for p2 in all_planets[i+1:]:  # 避免重复计算
            score = compute_reception_score(p1, p2, chart_data)
            
            # 存储双向分数（矩阵是对称的）
            matrix[p1][p2] = score
            matrix[p2][p1] = score
            
            # 记录互容关系
            if score >= 1.2:  # 互容通常分数较高
                mutual_receptions.append((p1, p2, score))
    
    # 存储到chart_data
    chart_data.reception_matrix = matrix
    
    print("\n" + "=" * 60)
    print("全盘接纳矩阵计算完成!")
    print("=" * 60)
    
    # 打印互容关系摘要
    if mutual_receptions:
        print(f"\n发现 {len(mutual_receptions)} 个互容关系:")
        for p1, p2, score in mutual_receptions:
            mutual_detail = check_mutual_reception(p1, p2, chart_data)
            desc = mutual_detail['description'] if mutual_detail else f"{p1.value}-{p2.value}"
            print(f"  {desc}: 分数 {score:.2f}")
    else:
        print("\n未发现互容关系")
    
    # 打印接纳分数摘要
    print("\n接纳分数摘要:")
    for p1 in all_planets:
        total_score = sum(score for p2, score in matrix[p1].items() if p2 != p1)
        if total_score > 0:
            print(f"  {p1.value}: 总接纳分数 {total_score:.2f}")
    
    return matrix


def get_reception_for_planet(
    planet: Planet,
    chart_data: ChartData,
    use_cache: bool = True
) -> Dict[Planet, float]:
    """
    获取行星对所有其他行星的接纳分数
    
    参数:
        planet: 行星
        chart_data: ChartData对象
        use_cache: 是否使用缓存
    
    返回:
        该行星对其他行星的接纳分数字典
    
    示例:
        >>> receptions = get_reception_for_planet(Planet.SUN, chart_data)
        >>> for other, score in receptions.items():
        >>>     if score > 0:
        >>>         print(f"太阳接纳{other.value}: {score:.2f}")
    """
    # 检查是否已经计算过
    if use_cache and hasattr(chart_data, 'reception_matrix') and chart_data.reception_matrix:
        if planet in chart_data.reception_matrix:
            return chart_data.reception_matrix[planet]
    
    # 如果没有缓存或不允许使用缓存，重新计算
    print(f"提示: 接纳矩阵未计算或未缓存，计算全盘接纳矩阵...")
    compute_all_receptions(chart_data)
    
    return chart_data.reception_matrix.get(planet, {})


# ============================================================================
# 4. 接纳特征计算（根据PRD 5.1节）
# ============================================================================

def compute_reception_for_planet(planet: Planet, chart_data: ChartData) -> float:
    """
    计算单个行星的接纳特征值（返回0-1）
    
    根据PRD中5.1节的算法实现。
    
    参数:
        planet: 行星
        chart_data: ChartData对象
    
    返回:
        接纳特征值（[0, 1]）
    
    示例:
        >>> reception_strength = compute_reception_for_planet(Planet.SUN, chart_data)
        >>> print(f"太阳的接纳特征值: {reception_strength:.3f}")
    """
    # 获取接纳矩阵
    if not hasattr(chart_data, 'reception_matrix') or not chart_data.reception_matrix:
        compute_all_receptions(chart_data)
    
    matrix = chart_data.reception_matrix
    
    if planet not in matrix:
        print(f"警告: 行星 {planet.value} 不在接纳矩阵中")
        return 0.0
    
    # 计算该行星的总接纳分数（只考虑正向接纳）
    total = 0.0
    positive_scores = []
    
    for other, score in matrix[planet].items():
        if other != planet and score > 0:
            total += score
            positive_scores.append((other.value, score))
    
    print(f"\n计算 {planet.value} 的接纳特征:")
    print("-" * 40)
    
    if positive_scores:
        print(f"正向接纳关系:")
        for other, score in positive_scores:
            print(f"  接纳{other}: {score:.2f}")
        print(f"接纳原始总分: {total:.2f}")
    else:
        print(f"无正向接纳关系")
    
    # 归一化：经验上限6.0（根据PRD）
    MAX_EXPECTED = 6.0
    normalized = clamp(total / MAX_EXPECTED, 0.0, 1.0)
    
    print(f"归一化接纳特征: {normalized:.3f} (总分数{total:.2f} / 最大期望{MAX_EXPECTED})")
    
    return normalized


# ============================================================================
# 5. 接纳分析工具
# ============================================================================

def analyze_reception_distribution(chart_data: ChartData) -> Dict[str, Any]:
    """
    分析接纳分布情况
    
    参数:
        chart_data: ChartData对象
    
    返回:
        接纳分布分析结果
    """
    if not hasattr(chart_data, 'reception_matrix') or not chart_data.reception_matrix:
        compute_all_receptions(chart_data)
    
    matrix = chart_data.reception_matrix
    
    # 收集所有接纳关系
    all_receptions = []
    mutual_receptions = []
    
    planets = list(matrix.keys())
    
    for i, p1 in enumerate(planets):
        for p2 in planets[i+1:]:
            score = matrix[p1][p2]
            
            if score > 0:
                all_receptions.append({
                    'planet1': p1.value,
                    'planet2': p2.value,
                    'score': score,
                    'is_mutual': score >= 1.2  # 互容通常分数较高
                })
                
                if score >= 1.2:
                    mutual_receptions.append({
                        'planet1': p1.value,
                        'planet2': p2.value,
                        'score': score
                    })
    
    # 计算每个行星的总接纳分数
    planet_scores = {}
    for planet in planets:
        total = sum(score for other, score in matrix[planet].items() if other != planet)
        positive = sum(score for other, score in matrix[planet].items() 
                      if other != planet and score > 0)
        negative = sum(score for other, score in matrix[planet].items() 
                      if other != planet and score < 0)
        
        planet_scores[planet.value] = {
            'total': total,
            'positive': positive,
            'negative': negative,
            'count_positive': sum(1 for other, score in matrix[planet].items() 
                                if other != planet and score > 0),
            'count_negative': sum(1 for other, score in matrix[planet].items() 
                                if other != planet and score < 0),
        }
    
    # 找到接纳最强的行星
    strongest_planet = None
    strongest_score = -float('inf')
    
    for planet, scores in planet_scores.items():
        if scores['total'] > strongest_score:
            strongest_score = scores['total']
            strongest_planet = planet
    
    analysis = {
        'total_receptions': len(all_receptions),
        'mutual_receptions': len(mutual_receptions),
        'all_receptions': all_receptions,
        'mutual_receptions_list': mutual_receptions,
        'planet_scores': planet_scores,
        'strongest_planet': {
            'planet': strongest_planet,
            'score': strongest_score if strongest_planet else 0.0
        } if strongest_planet else None,
        'avg_score_per_planet': sum(s['total'] for s in planet_scores.values()) / len(planet_scores) if planet_scores else 0.0,
    }
    
    return analysis


def print_reception_report(chart_data: ChartData) -> None:
    """
    打印接纳详细报告
    
    参数:
        chart_data: ChartData对象
    """
    if not hasattr(chart_data, 'reception_matrix') or not chart_data.reception_matrix:
        compute_all_receptions(chart_data)
    
    matrix = chart_data.reception_matrix
    analysis = analyze_reception_distribution(chart_data)
    
    print("\n" + "=" * 70)
    print("接纳系统详细报告")
    print("=" * 70)
    
    print(f"\n总计: {analysis['total_receptions']} 个接纳关系")
    print(f"互容关系: {analysis['mutual_receptions']} 个")
    print("-" * 70)
    
    # 打印互容关系
    if analysis['mutual_receptions'] > 0:
        print("\n互容关系详情:")
        for mutual in analysis['mutual_receptions_list']:
            detail = check_mutual_reception(
                Planet(mutual['planet1']), 
                Planet(mutual['planet2']), 
                chart_data
            )
            desc = detail['description'] if detail else f"{mutual['planet1']}-{mutual['planet2']}"
            print(f"  {desc}: 分数 {mutual['score']:.2f}")
    
    # 打印每个行星的接纳情况
    print("\n各行星接纳情况:")
    for planet_value, scores in analysis['planet_scores'].items():
        if scores['count_positive'] > 0 or scores['count_negative'] > 0:
            print(f"\n{planet_value}:")
            print(f"  总分数: {scores['total']:+.2f}")
            print(f"  正向接纳: {scores['positive']:.2f} ({scores['count_positive']}个)")
            print(f"  负向接纳: {scores['negative']:.2f} ({scores['count_negative']}个)")
            
            # 打印具体的接纳关系
            planet = Planet(planet_value)
            for other_planet, score in matrix[planet].items():
                if other_planet != planet and score != 0:
                    direction = "→" if score > 0 else "←" if score < 0 else " "
                    abs_score = abs(score)
                    print(f"    {planet_value} {direction} {other_planet.value}: {abs_score:.2f}")
    
    # 打印最强接纳行星
    if analysis['strongest_planet']:
        strongest = analysis['strongest_planet']
        print(f"\n最强接纳行星: {strongest['planet']} (总分数: {strongest['score']:.2f})")
    
    print("\n" + "=" * 70)
    print("报告结束")
    print("=" * 70)


def find_strongest_receptions(
    chart_data: ChartData, 
    min_score: float = 1.0,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """
    找出最强的接纳关系
    
    参数:
        chart_data: ChartData对象
        min_score: 最小分数阈值
        limit: 返回的数量限制
    
    返回:
        最强接纳关系列表
    """
    if not hasattr(chart_data, 'reception_matrix') or not chart_data.reception_matrix:
        compute_all_receptions(chart_data)
    
    matrix = chart_data.reception_matrix
    
    # 收集所有接纳关系
    all_receptions = []
    planets = list(matrix.keys())
    
    for i, p1 in enumerate(planets):
        for p2 in planets[i+1:]:
            score = matrix[p1][p2]
            if abs(score) >= min_score:
                all_receptions.append({
                    'planet1': p1.value,
                    'planet2': p2.value,
                    'score': score,
                    'is_mutual': score >= 1.2
                })
    
    # 按分数绝对值排序
    all_receptions.sort(key=lambda x: abs(x['score']), reverse=True)
    
    return all_receptions[:limit]


def get_planets_with_strong_receptions(
    chart_data: ChartData,
    min_total_score: float = 2.0
) -> List[Dict[str, Any]]:
    """
    获取有强接纳的行星
    
    参数:
        chart_data: ChartData对象
        min_total_score: 最小总分数阈值
    
    返回:
        有强接纳的行星信息列表
    """
    if not hasattr(chart_data, 'reception_matrix') or not chart_data.reception_matrix:
        compute_all_receptions(chart_data)
    
    matrix = chart_data.reception_matrix
    result = []
    
    for planet in matrix.keys():
        total_score = sum(score for other, score in matrix[planet].items() if other != planet)
        
        if abs(total_score) >= min_total_score:
            # 收集具体接纳关系
            receptions = []
            for other, score in matrix[planet].items():
                if other != planet and score != 0:
                    receptions.append({
                        'other_planet': other.value,
                        'score': score,
                        'is_positive': score > 0
                    })
            
            result.append({
                'planet': planet.value,
                'total_score': total_score,
                'reception_count': len(receptions),
                'positive_count': sum(1 for r in receptions if r['is_positive']),
                'negative_count': sum(1 for r in receptions if not r['is_positive']),
                'receptions': receptions
            })
    
    # 按总分数排序
    result.sort(key=lambda x: abs(x['total_score']), reverse=True)
    
    return result


# ============================================================================
# 6. 增量更新支持
# ============================================================================

def update_receptions_on_change(
    chart_data: ChartData,
    changed_planets: List[Planet]
) -> None:
    """
    增量更新：只重新计算受影响的接纳关系
    
    当行星位置发生变化时，只更新相关接纳关系，
    避免重新计算所有关系，提高性能。
    
    参数:
        chart_data: ChartData对象
        changed_planets: 发生变化的行星列表
    """
    if not hasattr(chart_data, 'reception_matrix') or not chart_data.reception_matrix:
        # 如果还没有计算过，直接计算全盘
        compute_all_receptions(chart_data)
        return
    
    print(f"增量更新接纳矩阵，受影响行星: {[p.value for p in changed_planets]}")
    
    matrix = chart_data.reception_matrix
    all_planets = list(matrix.keys())
    
    # 重新计算所有涉及变化行星的接纳关系
    for p1 in changed_planets:
        if p1 not in matrix:
            matrix[p1] = {}
        
        for p2 in all_planets:
            if p2 == p1:
                continue
            
            # 重新计算接纳分数
            old_score = matrix[p1].get(p2, 0.0)
            new_score = compute_reception_score(p1, p2, chart_data)
            
            # 更新双向关系
            matrix[p1][p2] = new_score
            matrix[p2][p1] = new_score
            
            if abs(new_score - old_score) > 0.01:  # 有显著变化
                print(f"  更新接纳: {p1.value}-{p2.value}: {old_score:.2f} → {new_score:.2f}")
    
    print("接纳矩阵增量更新完成")


# ============================================================================
# 7. 导出函数
# ============================================================================

__all__ = [
    # 接纳类型和检测
    "ReceptionType",
    "check_reception_detail",
    "check_mutual_reception",
    
    # 接纳评分
    "compute_reception_score",
    
    # 全盘接纳计算
    "compute_all_receptions",
    "get_reception_for_planet",
    
    # 接纳特征计算
    "compute_reception_for_planet",
    
    # 分析工具
    "analyze_reception_distribution",
    "print_reception_report",
    "find_strongest_receptions",
    "get_planets_with_strong_receptions",
    
    # 增量更新
    "update_receptions_on_change",
]