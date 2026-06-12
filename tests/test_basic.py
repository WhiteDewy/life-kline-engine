# tests/test_basic.py - 基础功能测试
"""
基础功能测试
测试常量、模型和工具函数
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from life_kline.constants import Planet, Sign, AspectType, CalculationMode
from life_kline.models import ChartData, PlanetInfo, PlanetFeature
from life_kline.utils import clamp, normalize_to_range, deg_diff


def test_constants():
    """测试常量定义"""
    print("测试常量定义...")
    
    # 测试行星枚举
    assert Planet.SUN == "SUN"
    assert Planet.MOON == "MOON"
    assert Planet.SUN.is_traditional == True
    assert Planet.URANUS.is_outer == True
    assert Planet.VENUS.is_benefic == True
    assert Planet.MARS.is_malefic == True
    
    # 测试星座枚举
    assert Sign.ARIES == "ARIES"
    assert Sign.TAURUS == "TAURUS"
    
    print("✅ 常量测试通过")


def test_models():
    """测试数据模型"""
    print("\n测试数据模型...")
    
    # 测试PlanetInfo
    planet_info = PlanetInfo(
        sign=Sign.LEO,
        degree=10.5,
        house=5,
        is_retrograde=False,
        speed=1.0,
        latitude=0.0
    )
    
    assert planet_info.sign == Sign.LEO
    assert planet_info.degree == 10.5
    assert planet_info.house == 5
    assert planet_info.get_absolute_position() == 4*30 + 10.5  # 狮子座是第5个星座（0-based）
    
    # 测试PlanetFeature
    feat = PlanetFeature()
    feat.dignity = 0.8
    feat.support_resources = 0.7
    
    assert feat.dignity == 0.8
    assert feat.support_resources == 0.7
    assert feat.validate() == True
    
    # 测试ChartData
    chart = ChartData()
    chart.mode = CalculationMode.MODERN
    chart.is_day_chart = True
    
    assert chart.mode == CalculationMode.MODERN
    assert chart.is_day_chart == True
    
    print("✅ 数据模型测试通过")


def test_utils():
    """测试工具函数"""
    print("\n测试工具函数...")
    
    # 测试clamp
    assert clamp(1.5, 0, 1) == 1.0
    assert clamp(-0.5, 0, 1) == 0.0
    assert clamp(0.5, 0, 1) == 0.5
    
    # 测试normalize_to_range
    assert normalize_to_range(50, 0, 100, 0, 1) == 0.5
    assert normalize_to_range(75, 0, 100, 0, 10) == 7.5
    
    # 测试deg_diff
    assert deg_diff(350, 10) == 20.0
    assert deg_diff(10, 350) == 20.0
    assert deg_diff(0, 180) == 180.0
    assert deg_diff(0, 181) == 179.0  # 最小差值
    
    print("✅ 工具函数测试通过")


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("开始运行基础功能测试")
    print("=" * 60)
    
    try:
        test_constants()
        test_models()
        test_utils()
        
        print("\n" + "=" * 60)
        print("所有基础测试通过! 🎉")
        print("=" * 60)
        return True
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    run_all_tests()