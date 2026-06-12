# tests/test_integration.py - 集成测试
"""
集成测试
测试整个系统的完整流程
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from life_kline.models import ChartData, PlanetInfo
from life_kline.constants import Planet, Sign, CalculationMode
from life_kline.scoring import compute_node_score
from life_kline.features import compute_planet_features


def create_test_chart():
    """创建测试星盘"""
    print("创建测试星盘...")
    
    chart = ChartData()
    chart.mode = CalculationMode.MODERN
    chart.is_day_chart = True
    chart.time_accuracy = "exact"
    chart.sun_longitude = 120.0
    
    # 添加宫头星座信息（简化：自然宫位制）
    chart.houses = [
        (Sign.ARIES, 0.0),    # 第1宫头
        (Sign.TAURUS, 0.0),   # 第2宫头
        (Sign.GEMINI, 0.0),   # 第3宫头
        (Sign.CANCER, 0.0),   # 第4宫头
        (Sign.LEO, 0.0),      # 第5宫头
        (Sign.VIRGO, 0.0),    # 第6宫头
        (Sign.LIBRA, 0.0),    # 第7宫头
        (Sign.SCORPIO, 0.0),  # 第8宫头
        (Sign.SAGITTARIUS, 0.0),  # 第9宫头
        (Sign.CAPRICORN, 0.0),    # 第10宫头
        (Sign.AQUARIUS, 0.0),     # 第11宫头
        (Sign.PISCES, 0.0),       # 第12宫头
    ]
    
    # 添加行星 - 设置它们在有意义的位置
    # 太阳在狮子座第5宫（庙宫，尊贵）
    chart.add_planet(Planet.SUN, PlanetInfo(
        sign=Sign.LEO,
        degree=10.5,
        house=5,
        is_retrograde=False,
        speed=1.0,
        latitude=0.0
    ))
    
    # 月亮在巨蟹座第4宫（庙宫，尊贵）
    chart.add_planet(Planet.MOON, PlanetInfo(
        sign=Sign.CANCER,
        degree=3.2,
        house=4,
        is_retrograde=False,
        speed=13.0,
        latitude=0.0
    ))
    
    # 金星在金牛座第2宫（庙宫，尊贵）
    chart.add_planet(Planet.VENUS, PlanetInfo(
        sign=Sign.TAURUS,
        degree=15.0,
        house=2,
        is_retrograde=False,
        speed=1.2,
        latitude=0.0
    ))
    
    # 火星在白羊座第1宫（庙宫，角宫）
    chart.add_planet(Planet.MARS, PlanetInfo(
        sign=Sign.ARIES,
        degree=20.0,
        house=1,
        is_retrograde=False,
        speed=0.5,
        latitude=0.0
    ))
    
    # 木星在射手座第9宫（庙宫）
    chart.add_planet(Planet.JUPITER, PlanetInfo(
        sign=Sign.SAGITTARIUS,
        degree=12.0,
        house=9,
        is_retrograde=False,
        speed=0.08,
        latitude=0.0
    ))
    
    # 土星在摩羯座第10宫（庙宫，角宫）
    chart.add_planet(Planet.SATURN, PlanetInfo(
        sign=Sign.CAPRICORN,
        degree=18.0,
        house=10,
        is_retrograde=False,
        speed=0.03,
        latitude=0.0
    ))
    
    print(f"星盘创建完成，包含 {len(chart.planets)} 颗行星")
    return chart


def test_planet_features():
    """测试行星特征计算"""
    print("\n" + "=" * 60)
    print("测试行星特征计算")
    print("=" * 60)
    
    chart = create_test_chart()
    
    # 测试太阳特征
    print("\n计算太阳特征...")
    sun_features = compute_planet_features(Planet.SUN, chart)
    
    # 检查特征值在有效范围内
    assert -1.0 <= sun_features.dignity <= 1.0
    assert 0.0 <= sun_features.support_resources <= 1.0
    assert 0.0 <= sun_features.load_pressure <= 1.0
    assert 0.0 <= sun_features.theme_coherence <= 1.0
    assert 0.0 <= sun_features.data_quality <= 1.0
    
    print(f"太阳尊贵度: {sun_features.dignity:+.3f}")
    print(f"太阳支持资源: {sun_features.support_resources:.3f}")
    print(f"太阳压力负荷: {sun_features.load_pressure:.3f}")
    print(f"太阳主题一致性: {sun_features.theme_coherence:.3f}")
    
    # 太阳在庙宫，尊贵度应该较高
    if sun_features.dignity > 0.5:
        print("✅ 太阳尊贵度高（符合预期）")
    else:
        print("⚠️  太阳尊贵度一般")
    
    return chart, sun_features


def test_scoring():
    """测试运势评分"""
    print("\n" + "=" * 60)
    print("测试运势评分")
    print("=" * 60)
    
    chart, sun_features = test_planet_features()
    
    # 测试月度运势评分
    print("\n计算太阳月度运势评分...")
    result = compute_node_score('month', Planet.SUN, chart)
    
    # 检查结果结构
    assert hasattr(result, 'score')
    assert hasattr(result, 'confidence')
    assert hasattr(result, 'ohlc')
    assert hasattr(result, 'trend')
    assert hasattr(result, 'volatility')
    assert hasattr(result, 'features')
    assert hasattr(result, 'debug')
    
    # 检查值范围
    assert -1.0 <= result.score <= 1.0
    assert 0.0 <= result.confidence <= 1.0
    assert -1.0 <= result.trend <= 1.0
    assert 0.0 <= result.volatility <= 1.0
    
    # 检查OHLC
    assert 'open' in result.ohlc
    assert 'high' in result.ohlc
    assert 'low' in result.ohlc
    assert 'close' in result.ohlc
    
    for key in ['open', 'high', 'low', 'close']:
        assert 0.0 <= result.ohlc[key] <= 1.0
    
    print(f"\n太阳月度运势评分结果:")
    print(f"  综合评分: {result.score:+.3f}")
    print(f"  置信度: {result.confidence:.1%}")
    print(f"  趋势: {result.trend:+.3f}")
    print(f"  波动性: {result.volatility:.3f}")
    print(f"  OHLC: {result.ohlc}")
    
    return result


def test_multiple_planets():
    """测试多个行星的评分"""
    print("\n" + "=" * 60)
    print("测试多个行星评分")
    print("=" * 60)
    
    chart = create_test_chart()
    
    # 测试的行星列表
    test_planets = [Planet.SUN, Planet.MOON, Planet.VENUS]
    
    from life_kline.scoring import compute_multiple_node_scores
    from life_kline.scoring import print_score_report
    
    print(f"计算 {len(test_planets)} 个行星的月度运势评分...")
    results = compute_multiple_node_scores('month', test_planets, chart)
    
    assert len(results) == len(test_planets)
    
    # 打印报告
    print_score_report(results, "月度运势测试")
    
    # 检查每个结果
    for planet in test_planets:
        assert planet in results
        result = results[planet]
        assert -1.0 <= result.score <= 1.0
    
    return results


def run_integration_tests():
    """运行所有集成测试"""
    print("=" * 60)
    print("开始运行集成测试")
    print("=" * 60)
    
    try:
        test_scoring()
        test_multiple_planets()
        
        print("\n" + "=" * 60)
        print("所有集成测试通过! 🎉")
        print("=" * 60)
        return True
    except Exception as e:
        print(f"\n❌ 集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    run_integration_tests()