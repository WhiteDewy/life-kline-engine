"""
life_kline - 基于莉莉体系的星盘评分核心引擎 (v3.3)

占星人生模型核心引擎，提供星盘计算、领域分析、叙事生成等功能。
"""

# 核心数据模型
from .models import ChartData, PlanetFeature, PlanetInfo, Aspect

# 核心计算函数（暂时注释掉，等验证各模块后逐步开启）
# from .dignities import compute_all_dignities, DignityResult
# from .houses import compute_all_house_powers, HousePowerResult
# from .scoring import compute_node_score, NodeScoreResult
# from .firdaria import calculate_firdaria_periods, get_firdaria_lord_at_age, FirdariaPeriod

__all__ = [
    # 模型
    "ChartData",
    "PlanetFeature",
    "PlanetInfo",
    "Aspect",
    # 计算
    "compute_all_dignities",
    "compute_essential_dignity",
    "DignityResult",
    "compute_all_house_powers",
    "HousePowerResult",
    "compute_node_score",
    "NodeScoreResult",
    "calculate_firdaria_periods",
    "get_firdaria_lord_at_age",
    "FirdariaPeriod",
]

__version__ = "0.3.3"
__author__ = "xiatian"

def get_version():
    return __version__

def get_available_functions():
    return __all__.copy()
