# examples/basic_usage.py - 基本使用示例
"""
Life K-Line Engine 基本使用示例
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from life_kline.models import ChartData, PlanetInfo
from life_kline.constants import Planet, Sign, CalculationMode
from life_kline.scoring import compute_node_score, print_score_report


def create_sample_chart():
    """
    创建一个示例星盘
    
    这是一个简化的示例，实际使用时需要从占星软件获取准确的星盘数据
    """
    print("创建示例星盘...")
    
    chart = ChartData()
    chart.mode = CalculationMode.MODERN
    chart.is_day_chart = True  # 假设是日间盘
    chart.time_accuracy = "exact"
    chart.sun_longitude = 120.0  # 狮子座0度
    
    # 设置宫头星座（简化示例）
    # 注意：实际星盘需要根据上升星座和分宫制计算
    chart.houses = [
        (Sign.ARIES, 0.0),      # 第1宫头：白羊座0度
        (Sign.TAURUS, 0.0),     # 第2宫头：金牛座0度
        (Sign.GEMINI, 0.0),     # 第3宫头：双子座0度
        (Sign.CANCER, 0.0),     # 第4宫头：巨蟹座0度
        (Sign.LEO, 0.0),        # 第5宫头：狮子座0度
        (Sign.VIRGO, 0.0),      # 第6宫头：处女座0度
        (Sign.LIBRA, 0.0),      # 第7宫头：天秤座0度
        (Sign.SCORPIO, 0.0),    # 第8宫头：天蝎座0度
        (Sign.SAGITTARIUS, 0.0), # 第9宫头：射手座0度
        (Sign.CAPRICORN, 0.0),  # 第10宫头：摩羯座0度
        (Sign.AQUARIUS, 0.0),   # 第11宫头：水瓶座0度
        (Sign.PISCES, 0.0),     # 第12宫头：双鱼座0度
    ]
    
    # 添加行星数据
    # 这里使用一些有意义的占星位置作为示例
    
    # 太阳在水瓶座第11宫（落陷，失势）
    chart.add_planet(Planet.SUN, PlanetInfo(
        sign=Sign.AQUARIUS,
        degree=10.5,
        house=11,
        is_retrograde=False,
        speed=1.0,
        latitude=0.0,
        longitude=310.5  # 水瓶座10.5度
    ))
    
    # 月亮在摩羯座第10宫（落陷，失势）
    chart.add_planet(Planet.MOON, PlanetInfo(
        sign=Sign.CAPRICORN,
        degree=3.2,
        house=10,
        is_retrograde=False,
        speed=13.0,
        latitude=0.0,
        longitude=273.2  # 摩羯座3.2度
    ))
    
    # 金星在天蝎座第8宫（落陷，失势）
    chart.add_planet(Planet.VENUS, PlanetInfo(
        sign=Sign.SCORPIO,
        degree=15.0,
        house=8,
        is_retrograde=False,
        speed=1.2,
        latitude=0.0,
        longitude=225.0  # 天蝎座15度
    ))
    
    # 火星在巨蟹座第4宫（落陷，失势）
    chart.add_planet(Planet.MARS, PlanetInfo(
        sign=Sign.CANCER,
        degree=20.0,
        house=4,
        is_retrograde=False,
        speed=0.5,
        latitude=0.0,
        longitude=110.0  # 巨蟹座20度
    ))
    
    # 水星在射手座第9宫（落陷，失势）
    chart.add_planet(Planet.MERCURY, PlanetInfo(
        sign=Sign.SAGITTARIUS,
        degree=5.5,
        house=9,
        is_retrograde=False,
        speed=1.5,
        latitude=0.0,
        longitude=155.5  # 处女座5.5度
    ))
    
    # 木星在射手座第9宫（庙宫）
    chart.add_planet(Planet.JUPITER, PlanetInfo(
        sign=Sign.SAGITTARIUS,
        degree=12.0,
        house=9,
        is_retrograde=False,
        speed=0.08,
        latitude=0.0,
        longitude=252.0  # 射手座12度
    ))
    
    # 土星在摩羯座第10宫（庙宫，角宫）
    chart.add_planet(Planet.SATURN, PlanetInfo(
        sign=Sign.CAPRICORN,
        degree=18.0,
        house=10,
        is_retrograde=False,
        speed=0.03,
        latitude=0.0,
        longitude=288.0  # 摩羯座18度
    ))
    
    print(f"示例星盘创建完成，包含 {len(chart.planets)} 颗行星")
    print(chart.summary())
    
    return chart


def demonstrate_features():
    """演示特征计算"""
    print("\n" + "=" * 70)
    print("特征计算演示")
    print("=" * 70)
    
    chart = create_sample_chart()
    
    from life_kline.features import compute_planet_features
    
    # 计算太阳的特征
    print("\n计算太阳的特征:")
    sun_features = compute_planet_features(Planet.SUN, chart)
    
    print(sun_features.summary())
    
    return chart


def demonstrate_scoring():
    """演示运势评分"""
    print("\n" + "=" * 70)
    print("运势评分演示")
    print("=" * 70)
    
    chart = create_sample_chart()
    
    # 计算太阳的月度运势
    print("\n计算太阳的月度运势评分:")
    sun_result = compute_node_score('month', Planet.SUN, chart)
    
    print(f"\n太阳月度运势结果:")
    print(f"  综合评分: {sun_result.score:+.3f}")
    print(f"  置信度: {sun_result.confidence:.1%}")
    print(f"  趋势: {sun_result.trend:+.3f}")
    print(f"  波动性: {sun_result.volatility:.3f}")
    print(f"  OHLC四象限:")
    print(f"    开盘: {sun_result.ohlc['open']:.3f}")
    print(f"    高点: {sun_result.ohlc['high']:.3f}")
    print(f"    低点: {sun_result.ohlc['low']:.3f}")
    print(f"    收盘: {sun_result.ohlc['close']:.3f}")
    
    return chart, sun_result


def demonstrate_multiple_planets():
    """演示多个行星的评分"""
    print("\n" + "=" * 70)
    print("多行星评分演示")
    print("=" * 70)
    
    chart = create_sample_chart()
    
    from life_kline.scoring import compute_multiple_node_scores
    
    # 选择几个重要的行星
    important_planets = [Planet.SUN, Planet.MOON, Planet.VENUS, Planet.MARS]
    
    print(f"\n计算 {len(important_planets)} 个重要行星的年度运势:")
    
    results = compute_multiple_node_scores('year', important_planets, chart)
    
    # 打印详细报告
    print_score_report(results, "年度运势")
    
    return chart, results


def demonstrate_different_timeframes():
    """演示不同时间层级的评分"""
    print("\n" + "=" * 70)
    print("不同时间层级演示")
    print("=" * 70)
    
    chart = create_sample_chart()
    
    timeframes = ['life', 'year', 'month', 'week', 'day']
    
    print(f"\n太阳在不同时间层级的运势评分:")
    print("-" * 60)
    
    for timeframe in timeframes:
        result = compute_node_score(timeframe, Planet.SUN, chart)
        timeframe_name = {
            'life': '人生',
            'year': '年度',
            'month': '月度',
            'week': '周度',
            'day': '每日'
        }.get(timeframe, timeframe)
        
        status = ""
        if result.score > 0.5:
            status = "（强势）"
        elif result.score > 0.1:
            status = "（良好）"
        elif result.score > -0.1:
            status = "（中性）"
        elif result.score > -0.5:
            status = "（挑战）"
        else:
            status = "（困难）"
        
        print(f"{timeframe_name:6s}: 评分 {result.score:+.3f} {status}")
    
    return chart


def main():
    """主演示函数"""
    print("🌟 Life K-Line Engine 使用演示")
    print("=" * 70)
    
    try:
        # 演示1: 特征计算
        chart1 = demonstrate_features()
        
        # 演示2: 单个行星评分
        chart2, sun_result = demonstrate_scoring()
        
        # 演示3: 多个行星评分
        chart3, multi_results = demonstrate_multiple_planets()
        
        # 演示4: 不同时间层级
        chart4 = demonstrate_different_timeframes()
        
        print("\n" + "=" * 70)
        print("演示完成！🎉")
        print("=" * 70)
        
        print("\n下一步建议:")
        print("1. 使用真实的星盘数据替换示例数据")
        print("2. 运行测试确保系统正常工作: python tests/run_all_tests.py")
        print("3. 参考 examples/ 目录中的更多示例")
        
    except Exception as e:
        print(f"\n❌ 演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()