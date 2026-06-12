"""
scoring.py - 运势节点评分系统

这个模块实现了运势节点综合评分的计算，包括：
1. 层级权重计算
2. OHLC四象限计算
3. 趋势和波动性计算
4. 最终评分输出

这是整个星盘评分引擎的最终输出模块。
"""

from typing import Dict, List, Optional, Tuple, Any
import math
from datetime import datetime

# 导入常量和模型
from .constants import (
    Planet, Sign, CalculationMode, clamp,
    normalize_to_range, safe_divide,
    DOMICILE_SIGNS, EXALTATION_SIGNS, DETRIMENT_SIGNS, FALL_SIGNS
)
from .models import ChartData, PlanetFeature, NodeScoreResult, PlanetInfo

# 导入特征计算模块
from .features import compute_planet_features


# ============================================================================
# 1. 层级权重和配置
# ============================================================================

def get_level_weights(node_type: str) -> Dict[str, float]:
    """
    获取层级权重（独立函数）
    
    根据PRD中7.2节的权重表实现。
    
    参数:
        node_type: 节点类型
    
    返回:
        权重字典
    
    示例:
        >>> weights = get_level_weights('life')
        >>> print(f"人生层级权重: {weights}")
    """
    # 根据PRD 7.2节的权重表
    weights_config = {
        'life': {
            'dignity': 0.30,    # 尊贵度权重
            'support': 0.25,    # 支持资源权重
            'pressure': 0.20,   # 压力负荷权重（注意：计算中会减去）
            'coherence': 0.15,  # 主题一致性权重
            'reception': 0.10   # 接纳权重
        },
        'year': {
            'dignity': 0.25,
            'support': 0.25,
            'pressure': 0.20,
            'coherence': 0.20,
            'reception': 0.10
        },
        'month': {
            'dignity': 0.20,
            'support': 0.25,
            'pressure': 0.25,
            'coherence': 0.20,
            'reception': 0.10
        },
        'week': {
            'dignity': 0.15,
            'support': 0.30,
            'pressure': 0.25,
            'coherence': 0.20,
            'reception': 0.10
        },
        'day': {
            'dignity': 0.10,
            'support': 0.35,
            'pressure': 0.30,
            'coherence': 0.15,
            'reception': 0.10
        }
    }
    
    # 返回指定类型的权重，默认为month
    return weights_config.get(node_type, weights_config['month'])


def validate_weights(weights: Dict[str, float]) -> bool:
    """
    验证权重配置的有效性
    
    参数:
        weights: 权重字典
    
    返回:
        bool: 权重是否有效
    """
    # 检查必需字段
    required_fields = ['dignity', 'support', 'pressure', 'coherence', 'reception']
    for field in required_fields:
        if field not in weights:
            print(f"错误: 缺少权重字段 '{field}'")
            return False
    
    # 检查权重范围
    total = 0.0
    for field, weight in weights.items():
        if weight < 0 or weight > 1:
            print(f"错误: 权重 '{field}' 的值 {weight} 超出范围 [0, 1]")
            return False
        total += weight
    
    # 检查权重总和（应该接近1.0，允许微小误差）
    if abs(total - 1.0) > 0.01:
        print(f"警告: 权重总和 {total:.3f} 不等于1.0")
        # 这里不返回False，因为可能是有意设计
    
    return True


# ============================================================================
# 2. OHLC四象限计算（根据PRD 7.3节）
# ============================================================================

def compute_ohlc_breakdown_safe(
    feat: PlanetFeature,
    weights: Optional[Dict[str, float]] = None
) -> Dict[str, float]:
    """
    OHLC计算（添加安全范围保护）
    
    根据PRD中7.3节的算法实现。
    
    参数:
        feat: PlanetFeature对象
        weights: 权重字典（当前未使用，保留参数）
    
    返回:
        OHLC字典，包含open, high, low, close四个值
    
    示例:
        >>> ohlc = compute_ohlc_breakdown_safe(features)
        >>> print(f"OHLC: 开盘={ohlc['open']:.3f}, 高点={ohlc['high']:.3f}, "
        >>>       f"低点={ohlc['low']:.3f}, 收盘={ohlc['close']:.3f}")
    """
    print("\n计算OHLC四象限:")
    print("=" * 40)
    
    # Open: 起始状态（尊贵+宫位）
    open_score = 0.6 * feat.dignity + 0.4 * feat.house_power
    print(f"Open (起始状态):")
    print(f"  0.6 × 尊贵度({feat.dignity:+.3f}) + 0.4 × 宫位力量({feat.house_power:+.3f}) = {open_score:+.3f}")
    
    # High: 最佳潜力（支持资源+吉相位+正向尊贵）
    high_base = 0.5 * feat.support_resources + 0.3 * feat.aspect_benefic
    high_extra = 0.2 * max(0, feat.dignity)  # 只取正向
    high_score = high_base + high_extra
    print(f"\nHigh (最佳潜力):")
    print(f"  基础: 0.5 × 支持资源({feat.support_resources:.3f}) + 0.3 × 吉相位({feat.aspect_benefic:.3f}) = {high_base:.3f}")
    print(f"  额外: 0.2 × 正向尊贵度({max(0, feat.dignity):.3f}) = {high_extra:.3f}")
    print(f"  总分: {high_score:.3f}")
    
    # Low: 最低风险（压力负荷+凶相位+负向尊贵）
    low_base = 0.5 * feat.load_pressure + 0.3 * feat.aspect_malefic
    low_extra = 0.2 * abs(min(0, feat.dignity))  # 只取负向绝对值
    low_score = low_base + low_extra
    print(f"\nLow (最低风险):")
    print(f"  基础: 0.5 × 压力负荷({feat.load_pressure:.3f}) + 0.3 × 凶相位({feat.aspect_malefic:.3f}) = {low_base:.3f}")
    print(f"  额外: 0.2 × 负向尊贵度({abs(min(0, feat.dignity)):.3f}) = {low_extra:.3f}")
    print(f"  总分: {low_score:.3f}")
    
    # Close: 最终结果（一致性+接纳+净支持）
    close_support = 0.4 * feat.theme_coherence      # [0, 0.4]
    close_reception = 0.3 * feat.reception          # [0, 0.3]
    close_net = 0.3 * (feat.support_resources - feat.load_pressure)  # [-0.3, 0.3]
    close_score = close_support + close_reception + close_net
    print(f"\nClose (最终结果):")
    print(f"  一致性: 0.4 × 主题一致性({feat.theme_coherence:.3f}) = {close_support:.3f}")
    print(f"  接纳: 0.3 × 接纳强度({feat.reception:.3f}) = {close_reception:.3f}")
    print(f"  净支持: 0.3 × (支持{feat.support_resources:.3f} - 压力{feat.load_pressure:.3f}) = {close_net:+.3f}")
    print(f"  总分: {close_score:.3f}")
    
    # 安全归一化函数
    def safe_normalize(value: float, min_val: float, max_val: float) -> float:
        """安全归一化，避免除零错误"""
        clamped = max(min_val, min(max_val, value))
        range_size = max_val - min_val
        if range_size < 1e-10:
            return 0.5  # 如果范围为零，返回中间值
        return (clamped - min_val) / range_size
    
    # 计算每个值的理论范围
    open_range = (-1.0, 1.0)          # dignity[-1,1], house_power[-1,1] → open[-1,1]
    high_range = (0.0, 1.0)           # support[0,1], aspect_benefic[0,1], max(0,dignity)[0,1] → high[0,1]
    low_range = (0.0, 1.0)            # 同上，low[0,1]
    close_range = (-0.3, 1.0)         # 根据公式计算的理论范围
    
    print(f"\n归一化范围:")
    print(f"  Open: {open_range[0]:+.1f} 到 {open_range[1]:+.1f}")
    print(f"  High: {high_range[0]:+.1f} 到 {high_range[1]:+.1f}")
    print(f"  Low:  {low_range[0]:+.1f} 到 {low_range[1]:+.1f}")
    print(f"  Close: {close_range[0]:+.1f} 到 {close_range[1]:+.1f}")
    
    # 归一化到[0, 1]范围
    ohlc = {
        'open': safe_normalize(open_score, *open_range),
        'high': safe_normalize(high_score, *high_range),
        'low': safe_normalize(low_score, *low_range),
        'close': safe_normalize(close_score, *close_range)
    }
    
    print(f"\n归一化后的OHLC:")
    print(f"  Open:  {ohlc['open']:.3f}")
    print(f"  High:  {ohlc['high']:.3f}")
    print(f"  Low:   {ohlc['low']:.3f}")
    print(f"  Close: {ohlc['close']:.3f}")
    
    return ohlc


# ============================================================================
# 3. 趋势和波动性计算
# ============================================================================

def compute_trend(
    current_feat: PlanetFeature,
    historical_data: List[Dict[str, Any]]
) -> float:
    """
    计算趋势（如果有历史数据）
    
    参数:
        current_feat: 当前特征
        historical_data: 历史数据列表
    
    返回:
        趋势值 [-1, 1]，正数表示上升趋势
    
    注意：这是一个简化实现，实际可能需要更复杂的算法
    """
    if not historical_data or len(historical_data) < 2:
        return 0.0  # 无足够历史数据
    
    print(f"计算趋势，使用 {len(historical_data)} 个历史数据点")
    
    # 提取历史评分
    historical_scores = []
    for data in historical_data[-10:]:  # 使用最近10个点
        if 'score' in data:
            historical_scores.append(data['score'])
    
    if len(historical_scores) < 2:
        return 0.0
    
    # 简单线性趋势计算
    n = len(historical_scores)
    x_sum = sum(range(n))
    y_sum = sum(historical_scores)
    xy_sum = sum(i * score for i, score in enumerate(historical_scores))
    x2_sum = sum(i * i for i in range(n))
    
    # 计算斜率（简单线性回归）
    numerator = n * xy_sum - x_sum * y_sum
    denominator = n * x2_sum - x_sum * x_sum
    
    if abs(denominator) < 1e-10:
        return 0.0
    
    slope = numerator / denominator
    
    # 归一化趋势值
    # 假设最大斜率约为0.1每时间单位
    MAX_SLOPE = 0.1
    trend = clamp(slope / MAX_SLOPE, -1.0, 1.0)
    
    print(f"  历史评分: {historical_scores}")
    print(f"  计算斜率: {slope:.4f}")
    print(f"  归一化趋势: {trend:.3f}")
    
    return trend


def compute_volatility(
    feat: PlanetFeature,
    historical_data: Optional[List[Dict[str, Any]]] = None
) -> float:
    """
    计算波动性
    
    参数:
        feat: 当前特征
        historical_data: 历史数据（可选）
    
    返回:
        波动性值 [0, 1]
    """
    # 方法1: 基于特征计算波动性
    feature_volatility = 0.0
    
    # 尊贵度的波动性（如果尊贵度接近0，可能更不稳定）
    dignity_stability = 1.0 - abs(feat.dignity)
    
    # 支持与压力的差异（差异大可能更波动）
    support_pressure_diff = abs(feat.support_resources - feat.load_pressure)
    
    # 综合波动性估计
    feature_volatility = (dignity_stability * 0.4 + support_pressure_diff * 0.6)
    
    print(f"基于特征的波动性估计:")
    print(f"  尊贵度稳定性: {dignity_stability:.3f} (1 - |{feat.dignity:.3f}|)")
    print(f"  支持压力差异: {support_pressure_diff:.3f}")
    print(f"  特征波动性: {feature_volatility:.3f}")
    
    # 方法2: 如果有历史数据，计算实际波动性
    historical_volatility = 0.0
    if historical_data and len(historical_data) >= 2:
        scores = []
        for data in historical_data[-20:]:  # 使用最近20个点
            if 'score' in data:
                scores.append(data['score'])
        
        if len(scores) >= 2:
            # 计算标准差
            mean = sum(scores) / len(scores)
            variance = sum((s - mean) ** 2 for s in scores) / len(scores)
            std_dev = math.sqrt(variance)
            
            # 归一化到[0, 1]（假设最大标准差为0.5）
            MAX_STD_DEV = 0.5
            historical_volatility = clamp(std_dev / MAX_STD_DEV, 0.0, 1.0)
            
            print(f"基于历史的波动性:")
            print(f"  历史评分标准差: {std_dev:.4f}")
            print(f"  历史波动性: {historical_volatility:.3f}")
    
    # 综合两种方法
    if historical_volatility > 0:
        # 如果历史数据，加权平均
        volatility = 0.3 * feature_volatility + 0.7 * historical_volatility
    else:
        volatility = feature_volatility
    
    volatility = clamp(volatility, 0.0, 1.0)
    print(f"综合波动性: {volatility:.3f}")
    
    return volatility


def calculate_trend_bonus(
    firdaria_lord: Planet,
    chart_data: ChartData
) -> float:
    """
    计算长期趋势（Trend）加成

    根据法达大运主星的尊贵状态决定：
    - 庙/旺：牛市（+20%）
    - 失势/落陷：熊市（-20%）
    - 其他：平稳（0%）

    参数:
        firdaria_lord: 法达大运主星
        chart_data: 星盘数据（包含行星落座信息）

    返回:
        float: 加成系数（如 0.2, -0.2, 0.0）
    """
    # 获取大运主星在星盘中的信息
    planet_info = chart_data.get_planet_info(firdaria_lord)
    if not planet_info:
        return 0.0
    
    sign = planet_info.sign
    
    # 检查庙旺（牛市）
    is_domicile = sign in DOMICILE_SIGNS.get(firdaria_lord, [])
    is_exaltation = sign in EXALTATION_SIGNS.get(firdaria_lord, [])
    
    if is_domicile or is_exaltation:
        print(f"趋势: {firdaria_lord.value}在{sign.value}庙旺，牛市 (+20%)")
        return 0.2  # +20%
    
    # 检查失势落陷（熊市）
    is_detriment = sign in DETRIMENT_SIGNS.get(firdaria_lord, [])
    is_fall = sign in FALL_SIGNS.get(firdaria_lord, [])
    
    if is_detriment or is_fall:
        print(f"趋势: {firdaria_lord.value}在{sign.value}失势/落陷，熊市 (-20%)")
        return -0.2  # -20%
    
    print(f"趋势: {firdaria_lord.value}在{sign.value}平稳 (0%)")
    return 0.0


# ============================================================================
# 4. 运势节点评分主函数（根据PRD 7.2节）
# ============================================================================

def compute_node_score(
    node_type: str,
    focus_planet: Planet,
    chart_data: ChartData,
    transits: Optional[Dict[Planet, PlanetInfo]] = None
) -> NodeScoreResult:
    """
    计算运势节点综合评分（工程优化版）
    
    根据PRD中7.2节的算法实现。
    
    参数:
        node_type: 节点类型（'life', 'year', 'month', 'week', 'day'）
        focus_planet: 焦点行星ID
        chart_data: ChartData对象
        transits: 流年行星数据（可选）
    
    返回:
        NodeScoreResult对象，包含score、confidence、ohlc等
    
    示例:
        >>> result = compute_node_score('month', Planet.SUN, chart_data)
        >>> print(f"月度运势评分: {result.score:.3f}, 置信度: {result.confidence:.1%}")
    """
    print("\n" + "=" * 70)
    print(f"计算运势节点评分")
    print(f"节点类型: {node_type}")
    print(f"焦点行星: {focus_planet.value}")
    print("=" * 70)
    
    # 1. 计算行星特征
    print(f"\n1. 计算行星特征...")
    feat = compute_planet_features(focus_planet, chart_data, transits)
    
    # 2. 获取层级权重
    print(f"\n2. 获取层级权重...")
    level_weights = get_level_weights(node_type)
    
    if not validate_weights(level_weights):
        print("警告: 权重配置无效，使用默认权重")
        level_weights = get_level_weights('month')  # 默认使用月度权重
    
    print(f"权重配置:")
    for key, weight in level_weights.items():
        print(f"  {key}: {weight:.2f}")
    
    # 3. 计算加权分（确保每个特征在有效范围内）
    print(f"\n3. 计算加权分数...")
    
    # 获取特征值并确保在有效范围内
    dignity = clamp(feat.dignity, -1.0, 1.0)
    support = clamp(feat.support_resources, 0.0, 1.0)
    pressure = clamp(feat.load_pressure, 0.0, 1.0)
    coherence = clamp(feat.theme_coherence, 0.0, 1.0)
    reception = clamp(feat.reception, 0.0, 1.0)
    
    print(f"特征值 (已限制范围):")
    print(f"  尊贵度: {dignity:+.3f}")
    print(f"  支持资源: {support:.3f}")
    print(f"  压力负荷: {pressure:.3f}")
    print(f"  主题一致性: {coherence:.3f}")
    print(f"  接纳强度: {reception:.3f}")
    
    # 将[0,1]特征转为[-1,1]参与加权
    coherence_scaled = (coherence - 0.5) * 2  # 0→-1, 0.5→0, 1→1
    reception_scaled = (reception - 0.5) * 2
    
    print(f"缩放后的特征值:")
    print(f"  一致性缩放: {coherence_scaled:+.3f} ({coherence:.3f} → {coherence_scaled:+.3f})")
    print(f"  接纳缩放: {reception_scaled:+.3f} ({reception:.3f} → {reception_scaled:+.3f})")
    
    # 计算原始加权分
    raw_score = (
        level_weights['dignity'] * dignity +
        level_weights['support'] * support -
        level_weights['pressure'] * pressure +
        level_weights['coherence'] * coherence_scaled +
        level_weights['reception'] * reception_scaled
    )
    
    print(f"\n加权计算:")
    print(f"  {level_weights['dignity']:.2f} × {dignity:+.3f} (尊贵度) = {level_weights['dignity'] * dignity:+.3f}")
    print(f"  {level_weights['support']:.2f} × {support:.3f} (支持资源) = {level_weights['support'] * support:+.3f}")
    print(f"  -{level_weights['pressure']:.2f} × {pressure:.3f} (压力负荷) = {-level_weights['pressure'] * pressure:+.3f}")
    print(f"  {level_weights['coherence']:.2f} × {coherence_scaled:+.3f} (一致性) = {level_weights['coherence'] * coherence_scaled:+.3f}")
    print(f"  {level_weights['reception']:.2f} × {reception_scaled:+.3f} (接纳) = {level_weights['reception'] * reception_scaled:+.3f}")
    print(f"  原始加权总分: {raw_score:+.3f}")
    
    # 4. 数据质量调整（置信度）
    print(f"\n4. 数据质量调整...")
    confidence = clamp(feat.data_quality, 0.0, 1.0)
    adjusted_score = raw_score * confidence
    
    # 如果置信度低，向0收缩（保守估计）
    if confidence < 0.5:
        shrinkage = 1.0 - confidence
        adjusted_score = adjusted_score * (1.0 - shrinkage)  # 向0收缩
        print(f"  置信度低({confidence:.2f})，向0收缩{shrinkage:.1%}")
        
    # 7. 法达趋势加成（Trend Bonus）
    # 插入在最终clamp之前，作为大环境的市场Beta调整
    print(f"\n7. 法达趋势加成 (Trend Bonus)...")
    if hasattr(chart_data, 'firdaria_lord') and chart_data.firdaria_lord:
        trend_bonus = calculate_trend_bonus(chart_data.firdaria_lord, chart_data)
        if trend_bonus != 0.0:
            print(f"  原始分数: {adjusted_score:+.3f}")
            print(f"  趋势加成: {trend_bonus:+.1%} ({trend_bonus:+.3f})")
            # 采用加法逻辑：牛市抬升水位，熊市降低水位
            # 这样对于负分（厄运）在牛市会得到缓解（变大），在熊市会加剧（变小）
            # 例如: -0.5 (厄运) + 0.2 (牛市) = -0.3 (缓解)
            #      -0.5 (厄运) - 0.2 (熊市) = -0.7 (加剧)
            adjusted_score += trend_bonus
            print(f"  加成后分数: {adjusted_score:+.3f}")
    else:
        print("  无法计算趋势加成 (缺少法达大运主星信息)")
    
    final_score = clamp(adjusted_score, -1.0, 1.0)
    
    print(f"  数据质量/置信度: {confidence:.3f}")
    print(f"  调整后分数: {adjusted_score:+.3f}")
    print(f"  最终分数(限制范围): {final_score:+.3f}")
    
    # 5. OHLC四象限
    print(f"\n5. 计算OHLC四象限...")
    ohlc = compute_ohlc_breakdown_safe(feat, level_weights)
    
    # 6. 趋势和波动性（如果有历史数据）
    print(f"\n6. 计算趋势和波动性...")
    trend = 0.0
    volatility = 0.0
    
    if hasattr(chart_data, 'historical_data') and chart_data.historical_data:
        trend = compute_trend(feat, chart_data.historical_data)
        volatility = compute_volatility(feat, chart_data.historical_data)
    else:
        # 如果没有历史数据，基于特征估计波动性
        volatility = compute_volatility(feat)
    
    trend = clamp(trend, -1.0, 1.0)
    volatility = clamp(volatility, 0.0, 1.0)
    
    print(f"  趋势: {trend:+.3f}")
    print(f"  波动性: {volatility:.3f}")
    
    # 7. 准备特征字典
    features_dict = {
        'dignity': feat.dignity,
        'house_power': feat.house_power,
        'aspect_benefic': feat.aspect_benefic,
        'aspect_malefic': feat.aspect_malefic,
        'reception': feat.reception,
        'support_resources': feat.support_resources,
        'load_pressure': feat.load_pressure,
        'theme_coherence': feat.theme_coherence,
        'data_quality': feat.data_quality
    }
    
    # 8. 创建结果对象
    result = NodeScoreResult(
        score=final_score,
        confidence=confidence,
        ohlc=ohlc,
        trend=trend,
        volatility=volatility,
        features=features_dict,
        debug=feat.debug
    )
    
    print("\n" + "=" * 70)
    print("运势节点评分计算完成!")
    print("=" * 70)
    
    # 打印最终结果摘要
    print(f"\n最终结果摘要:")
    print(f"  综合评分: {final_score:+.3f} (范围: -1.0 到 +1.0)")
    print(f"  置信度: {confidence:.1%}")
    print(f"  趋势: {trend:+.3f} ({'上升' if trend > 0.1 else '下降' if trend < -0.1 else '平稳'})")
    print(f"  波动性: {volatility:.3f} ({'高' if volatility > 0.7 else '中' if volatility > 0.3 else '低'})")
    print(f"  OHLC四象限:")
    print(f"    开盘(起始状态): {ohlc['open']:.3f}")
    print(f"    高点(最佳潜力): {ohlc['high']:.3f}")
    print(f"    低点(最低风险): {ohlc['low']:.3f}")
    print(f"    收盘(最终结果): {ohlc['close']:.3f}")
    
    return result


def compute_multiple_node_scores(
    node_type: str,
    planet_list: List[Planet],
    chart_data: ChartData,
    transits: Optional[Dict[Planet, PlanetInfo]] = None
) -> Dict[Planet, NodeScoreResult]:
    """
    批量计算多个行星的运势节点评分
    
    参数:
        node_type: 节点类型
        planet_list: 行星列表
        chart_data: ChartData对象
        transits: 流年行星数据（可选）
    
    返回:
        行星评分结果字典
    
    示例:
        >>> results = compute_multiple_node_scores(
        >>>     'month', [Planet.SUN, Planet.MOON], chart_data
        >>> )
        >>> for planet, result in results.items():
        >>>     print(f"{planet.value}月度评分: {result.score:.3f}")
    """
    results = {}
    
    print(f"\n批量计算 {len(planet_list)} 个行星的{node_type}运势评分...")
    
    for planet in planet_list:
        print(f"\n{'='*60}")
        print(f"计算 {planet.value} 的运势评分")
        print(f"{'='*60}")
        
        result = compute_node_score(node_type, planet, chart_data, transits)
        results[planet] = result
    
    print(f"\n批量计算完成，共计算了 {len(results)} 个行星的运势评分")
    
    return results


# ============================================================================
# 5. 评分分析和工具
# ============================================================================

def analyze_score_distribution(
    results_dict: Dict[Planet, NodeScoreResult]
) -> Dict[str, Any]:
    """
    分析评分分布情况
    
    参数:
        results_dict: 评分结果字典
    
    返回:
        评分分布分析结果
    """
    if not results_dict:
        return {}
    
    analysis = {
        'count': len(results_dict),
        'scores': [],
        'by_planet': {},
        'statistics': {},
        'recommendations': []
    }
    
    # 收集所有评分
    scores = []
    for planet, result in results_dict.items():
        score_info = {
            'planet': planet.value,
            'score': result.score,
            'confidence': result.confidence,
            'trend': result.trend,
            'volatility': result.volatility,
            'ohlc': result.ohlc
        }
        
        scores.append(score_info)
        analysis['by_planet'][planet.value] = score_info
    
    # 计算统计
    score_values = [s['score'] for s in scores]
    confidence_values = [s['confidence'] for s in scores]
    
    analysis['statistics'] = {
        'score_mean': sum(score_values) / len(score_values),
        'score_std': (sum((s - sum(score_values)/len(score_values))**2 for s in score_values) / len(score_values))**0.5 if len(score_values) > 1 else 0.0,
        'score_max': max(score_values),
        'score_min': min(score_values),
        'confidence_mean': sum(confidence_values) / len(confidence_values),
        'positive_count': sum(1 for s in score_values if s > 0),
        'negative_count': sum(1 for s in score_values if s < 0),
        'neutral_count': sum(1 for s in score_values if abs(s) < 0.1),
    }
    
    # 找出最强和最弱
    if scores:
        strongest = max(scores, key=lambda x: x['score'])
        weakest = min(scores, key=lambda x: x['score'])
        
        analysis['strongest'] = strongest
        analysis['weakest'] = weakest
        
        # 生成建议
        if strongest['score'] > 0.5:
            analysis['recommendations'].append(
                f"重点关注行星: {strongest['planet']} (评分{strongest['score']:+.2f})，当前处于强势状态"
            )
        
        if weakest['score'] < -0.5:
            analysis['recommendations'].append(
                f"谨慎关注行星: {weakest['planet']} (评分{weakest['score']:+.2f})，当前面临挑战"
            )
        
        # 检查高风险（低置信度高波动性）
        high_risk = []
        for score_info in scores:
            if score_info['confidence'] < 0.5 and score_info['volatility'] > 0.7:
                high_risk.append(score_info['planet'])
        
        if high_risk:
            analysis['recommendations'].append(
                f"高风险行星: {', '.join(high_risk)} (置信度低且波动性高)"
            )
    
    analysis['scores'] = scores
    
    return analysis


def print_score_report(
    results_dict: Dict[Planet, NodeScoreResult],
    node_type: str = "运势"
) -> None:
    """
    打印评分报告
    
    参数:
        results_dict: 评分结果字典
        node_type: 节点类型描述
    """
    if not results_dict:
        print("无评分数据")
        return
    
    print("\n" + "=" * 100)
    print(f"{node_type}评分综合报告")
    print("=" * 100)
    
    # 表头
    headers = ["行星", "评分", "置信度", "趋势", "波动性", "开盘", "高点", "低点", "收盘", "状态"]
    header_format = "{:<8} {:>8} {:>8} {:>8} {:>8} {:>8} {:>8} {:>8} {:>8} {:>10}"
    
    print(header_format.format(*headers))
    print("-" * 100)
    
    # 数据行
    for planet, result in sorted(results_dict.items(), key=lambda x: x[1].score, reverse=True):
        # 确定状态描述
        score = result.score
        if score > 0.7:
            status = "极佳"
        elif score > 0.3:
            status = "良好"
        elif score > 0.1:
            status = "略好"
        elif score > -0.1:
            status = "中性"
        elif score > -0.3:
            status = "略差"
        elif score > -0.7:
            status = "较差"
        else:
            status = "极差"
        
        # 趋势描述
        trend = result.trend
        if trend > 0.3:
            trend_symbol = "↗强升"
        elif trend > 0.1:
            trend_symbol = "↗升"
        elif trend > -0.1:
            trend_symbol = "→平"
        elif trend > -0.3:
            trend_symbol = "↘降"
        else:
            trend_symbol = "↘强降"
        
        row = [
            planet.value,
            f"{score:+.3f}",
            f"{result.confidence:.1%}",
            trend_symbol,
            f"{result.volatility:.2f}",
            f"{result.ohlc['open']:.2f}",
            f"{result.ohlc['high']:.2f}",
            f"{result.ohlc['low']:.2f}",
            f"{result.ohlc['close']:.2f}",
            status
        ]
        print(header_format.format(*row))
    
    print("=" * 100)
    
    # 摘要统计
    analysis = analyze_score_distribution(results_dict)
    stats = analysis['statistics']
    
    print(f"\n统计摘要:")
    print(f"  平均评分: {stats['score_mean']:+.3f}")
    print(f"  评分标准差: {stats['score_std']:.3f}")
    print(f"  最高评分: {stats['score_max']:+.3f}")
    print(f"  最低评分: {stats['score_min']:+.3f}")
    print(f"  平均置信度: {stats['confidence_mean']:.1%}")
    print(f"  正面评分: {stats['positive_count']}个")
    print(f"  负面评分: {stats['negative_count']}个")
    print(f"  中性评分: {stats['neutral_count']}个")
    
    # 建议
    if analysis['recommendations']:
        print(f"\n建议:")
        for rec in analysis['recommendations']:
            print(f"  • {rec}")
    
    # 最强和最弱
    if 'strongest' in analysis and 'weakest' in analysis:
        strongest = analysis['strongest']
        weakest = analysis['weakest']
        
        print(f"\n关键发现:")
        print(f"  最强行星: {strongest['planet']} (评分{strongest['score']:+.3f})")
        print(f"  最弱行星: {weakest['planet']} (评分{weakest['score']:+.3f})")
    
    print("\n" + "=" * 100)


def generate_score_summary(
    result: NodeScoreResult,
    planet_name: str,
    node_type: str
) -> str:
    """
    生成评分摘要文本
    
    参数:
        result: 评分结果
        planet_name: 行星名称
        node_type: 节点类型
    
    返回:
        摘要文本
    """
    score = result.score
    
    # 评分描述
    if score > 0.7:
        score_desc = "极佳"
    elif score > 0.3:
        score_desc = "良好"
    elif score > 0.1:
        score_desc = "略好"
    elif score > -0.1:
        score_desc = "中性"
    elif score > -0.3:
        score_desc = "略差"
    elif score > -0.7:
        score_desc = "较差"
    else:
        score_desc = "极差"
    
    # 趋势描述
    trend = result.trend
    if trend > 0.3:
        trend_desc = "强烈上升"
    elif trend > 0.1:
        trend_desc = "上升"
    elif trend > -0.1:
        trend_desc = "平稳"
    elif trend > -0.3:
        trend_desc = "下降"
    else:
        trend_desc = "强烈下降"
    
    # 波动性描述
    volatility = result.volatility
    if volatility > 0.7:
        volatility_desc = "高"
    elif volatility > 0.3:
        volatility_desc = "中"
    else:
        volatility_desc = "低"
    
    summary = f"""
{planet_name}的{node_type}运势评分摘要:
────────────────────────────────────
综合评分: {score:+.3f} ({score_desc})
置信度: {result.confidence:.1%}
趋势: {trend_desc} ({trend:+.2f})
波动性: {volatility_desc} ({volatility:.2f})

OHLC四象限分析:
• 开盘(起始状态): {result.ohlc['open']:.3f}
• 高点(最佳潜力): {result.ohlc['high']:.3f}
• 低点(最低风险): {result.ohlc['low']:.3f}
• 收盘(最终结果): {result.ohlc['close']:.3f}

关键特征:
• 尊贵度: {result.features['dignity']:+.3f}
• 支持资源: {result.features['support_resources']:.3f}
• 压力负荷: {result.features['load_pressure']:.3f}
• 主题一致性: {result.features['theme_coherence']:.3f}
────────────────────────────────────
"""
    
    return summary


# ============================================================================
# 6. 导出函数
# ============================================================================

__all__ = [
    # 权重配置
    "get_level_weights",
    "validate_weights",
    
    # OHLC计算
    "compute_ohlc_breakdown_safe",
    
    # 趋势和波动性
    "compute_trend",
    "compute_volatility",
    
    # 主评分函数
    "compute_node_score",
    "compute_multiple_node_scores",
    
    # 分析工具
    "analyze_score_distribution",
    "print_score_report",
    "generate_score_summary",
]