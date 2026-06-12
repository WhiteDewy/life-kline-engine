# tests/test_dignities.py - 尊贵度计算测试
"""
尊贵度计算测试
测试庙旺失陷等尊贵度计算
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from life_kline.models import ChartData, PlanetInfo
from life_kline.constants import Planet, Sign, CalculationMode
from life_kline.dignities import (
    compute_essential_dignity_raw,
    compute_all_dignities,
    get_dignity_for_planet
)


def test_sun_in_leo():
    """测试太阳在狮子座（庙宫）"""
    print("测试太阳在狮子座（庙宫）...")
    
    dignity = compute_essential_dignity_raw(
        planet=Planet.SUN,
        sign=Sign.LEO,
        degree=10.5,
        is_day=True,
        mode=CalculationMode.MODERN
    )
    
    # 太阳在狮子座应该是庙宫 +5分
    print(f"太阳在狮子座尊贵分: {dignity}")
    assert dignity >= 5.0, f"太阳在狮子座应至少+5分，实际得{dignity}"
    
    print("✅ 太阳在狮子座测试通过")


def test_moon_in_cancer():
    """测试月亮在巨蟹座（庙宫）"""
    print("\n测试月亮在巨蟹座（庙宫）...")
    
    dignity = compute_essential_dignity_raw(
        planet=Planet.MOON,
        sign=Sign.CANCER,
        degree=3.2,
        is_day=True,
        mode=CalculationMode.MODERN
    )
    
    # 月亮在巨蟹座应该是庙宫 +5分
    print(f"月亮在巨蟹座尊贵分: {dignity}")
    assert dignity >= 5.0, f"月亮在巨蟹座应至少+5分，实际得{dignity}"
    
    print("✅ 月亮在巨蟹座测试通过")


def test_venus_in_taurus():
    """测试金星在金牛座（庙宫）"""
    print("\n测试金星在金牛座（庙宫）...")
    
    dignity = compute_essential_dignity_raw(
        planet=Planet.VENUS,
        sign=Sign.TAURUS,
        degree=15.0,
        is_day=True,
        mode=CalculationMode.MODERN
    )
    
    # 金星在金牛座应该是庙宫 +5分
    print(f"金星在金牛座尊贵分: {dignity}")
    assert dignity >= 5.0, f"金星在金牛座应至少+5分，实际得{dignity}"
    
    print("✅ 金星在金牛座测试通过")


def test_mars_in_aries():
    """测试火星在白羊座（庙宫）"""
    print("\n测试火星在白羊座（庙宫）...")
    
    dignity = compute_essential_dignity_raw(
        planet=Planet.MARS,
        sign=Sign.ARIES,
        degree=20.0,
        is_day=True,
        mode=CalculationMode.MODERN
    )
    
    # 火星在白羊座应该是庙宫 +5分
    print(f"火星在白羊座尊贵分: {dignity}")
    assert dignity >= 5.0, f"火星在白羊座应至少+5分，实际得{dignity}"
    
    print("✅ 火星在白羊座测试通过")


def test_compute_all_dignities():
    """测试全盘尊贵度计算"""
    print("\n测试全盘尊贵度计算...")
    
    # 创建测试星盘
    chart = ChartData()
    chart.mode = CalculationMode.MODERN
    chart.is_day_chart = True
    chart.sun_longitude = 120.0
    
    # 添加行星
    chart.add_planet(Planet.SUN, PlanetInfo(Sign.LEO, 10.5, 5))
    chart.add_planet(Planet.MOON, PlanetInfo(Sign.CANCER, 3.2, 4))
    chart.add_planet(Planet.VENUS, PlanetInfo(Sign.TAURUS, 15.0, 2))
    chart.add_planet(Planet.MARS, PlanetInfo(Sign.ARIES, 20.0, 1))
    
    # 计算全盘尊贵度
    dignities = compute_all_dignities(chart)
    
    print(f"计算得到的尊贵度: {dignities}")
    
    # 检查结果
    assert Planet.SUN in dignities
    assert Planet.MOON in dignities
    assert Planet.VENUS in dignities
    assert Planet.MARS in dignities
    
    # 这些行星应该在庙宫，尊贵度应该较高
    assert dignities[Planet.SUN] > 0.3, f"太阳尊贵度应>0.3，实际为{dignities[Planet.SUN]}"
    assert dignities[Planet.MOON] > 0.3, f"月亮尊贵度应>0.3，实际为{dignities[Planet.MOON]}"
    
    print("✅ 全盘尊贵度计算测试通过")


def test_get_dignity_for_planet():
    """测试获取单个行星尊贵度"""
    print("\n测试获取单个行星尊贵度...")
    
    chart = ChartData()
    chart.mode = CalculationMode.MODERN
    chart.is_day_chart = True
    
    chart.add_planet(Planet.SUN, PlanetInfo(Sign.LEO, 10.5, 5))
    chart.add_planet(Planet.MOON, PlanetInfo(Sign.CANCER, 3.2, 4))
    
    # 获取太阳尊贵度（应该自动计算全盘）
    sun_dignity = get_dignity_for_planet(Planet.SUN, chart)
    moon_dignity = get_dignity_for_planet(Planet.MOON, chart)
    
    print(f"太阳尊贵度: {sun_dignity}")
    print(f"月亮尊贵度: {moon_dignity}")
    
    assert sun_dignity > 0.3, f"太阳尊贵度应>0.3，实际为{sun_dignity}"
    assert moon_dignity > 0.3, f"月亮尊贵度应>0.3，实际为{moon_dignity}"
    
    print("✅ 单个行星尊贵度获取测试通过")


def run_dignities_tests():
    """运行所有尊贵度测试"""
    print("=" * 60)
    print("开始运行尊贵度计算测试")
    print("=" * 60)
    
    try:
        test_sun_in_leo()
        test_moon_in_cancer()
        test_venus_in_taurus()
        test_mars_in_aries()
        test_compute_all_dignities()
        test_get_dignity_for_planet()
        
        print("\n" + "=" * 60)
        print("所有尊贵度测试通过! 🎉")
        print("=" * 60)
        return True
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    run_dignities_tests()