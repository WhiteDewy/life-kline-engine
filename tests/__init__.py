"""
life_kline - 基于莉莉体系的星盘评分核心引擎 (v3.3)
"""

# 首先定义 __all__ 列表
__all__ = []

# 导入核心模型
from .models import ChartData, PlanetFeature
__all__.extend(["ChartData", "PlanetFeature"])

# 导入核心函数
from .scoring import compute_node_score
__all__.append("compute_node_score")

from .dignities import compute_all_dignities
__all__.append("compute_all_dignities")

from .houses import compute_all_house_powers
__all__.append("compute_all_house_powers")

# 版本信息
__version__ = "0.3.3"
__author__ = "xiatian"

# 辅助函数
def get_version() -> str:
    """获取版本号"""
    return __version__

def get_available_functions() -> list:
    """获取可用函数列表"""
    return __all__.copy()