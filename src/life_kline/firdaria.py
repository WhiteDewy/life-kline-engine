"""
firdaria.py - 法达星限系统 (Firdaria)

这个模块实现了法达星限（Firdaria）的时间推运系统。
法达星限是一种将人生划分为不同行星掌管周期的古老技术。
通常用于判断长期运势趋势（The Trend）。
周期总长 75 年，之后循环。
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import math

from .constants import Planet

# 法达年限配置
FIRDARIA_YEARS = {
    Planet.SUN: 10,
    Planet.VENUS: 8,
    Planet.MERCURY: 13,
    Planet.MOON: 9,
    Planet.SATURN: 11,
    Planet.JUPITER: 12,
    Planet.MARS: 7,
    Planet.NORTH_NODE: 3,
    Planet.SOUTH_NODE: 2,
}

# 迦勒底星序 (Chaldean Order): 土 -> 木 -> 火 -> 日 -> 金 -> 水 -> 月
# 用于确定子运（Sub-period）的顺序
CHALDEAN_ORDER = [
    Planet.SATURN,
    Planet.JUPITER,
    Planet.MARS,
    Planet.SUN,
    Planet.VENUS,
    Planet.MERCURY,
    Planet.MOON
]

# 昼间盘主运顺序 (Sun -> Venus -> Mercury -> Moon -> Saturn -> Jupiter -> Mars -> Nodes)
DAY_ORDER = [
    Planet.SUN, Planet.VENUS, Planet.MERCURY, Planet.MOON,
    Planet.SATURN, Planet.JUPITER, Planet.MARS,
    Planet.NORTH_NODE, Planet.SOUTH_NODE
]

# 夜间盘主运顺序 (Moon -> Saturn -> Jupiter -> Mars -> Sun -> Venus -> Mercury -> Nodes)
NIGHT_ORDER = [
    Planet.MOON, Planet.SATURN, Planet.JUPITER, Planet.MARS,
    Planet.SUN, Planet.VENUS, Planet.MERCURY,
    Planet.NORTH_NODE, Planet.SOUTH_NODE
]

@dataclass
class FirdariaPeriod:
    """法达周期数据类"""
    start_age: float        # 起始年龄
    end_age: float          # 结束年龄
    major_lord: Planet      # 大运主星
    sub_lord: Optional[Planet] # 子运主星（交点期为None）
    duration: float         # 周期持续时间（年）

    @property
    def is_node_period(self) -> bool:
        """是否为交点时期（无子运）"""
        return self.major_lord in (Planet.NORTH_NODE, Planet.SOUTH_NODE)


def get_next_chaldean_planet(current: Planet) -> Planet:
    """获取迦勒底星序中的下一颗行星"""
    if current not in CHALDEAN_ORDER:
        # 如果不是七政（如交点），返回原星（不应发生）
        return current 
    idx = CHALDEAN_ORDER.index(current)
    return CHALDEAN_ORDER[(idx + 1) % len(CHALDEAN_ORDER)]


def get_sub_lords(major_lord: Planet) -> List[Planet]:
    """
    获取指定大运主星下的7个子运主星序列
    
    规则：
    1. 子运第一星为大运主星本身
    2. 后续依照迦勒底星序排列
    """
    if major_lord not in CHALDEAN_ORDER:
        return [] # 交点没有子运
    
    sub_lords = []
    current = major_lord
    for _ in range(7):
        sub_lords.append(current)
        current = get_next_chaldean_planet(current)
    return sub_lords


def calculate_firdaria_periods(is_day_chart: bool, max_age: float = 100.0) -> List[FirdariaPeriod]:
    """
    计算法达星限周期列表
    
    参数:
        is_day_chart: 是否为日间盘
        max_age: 最大计算年龄（默认为100岁）
        
    返回:
        FirdariaPeriod对象列表，按时间顺序排列
    """
    periods = []
    current_age = 0.0
    
    # 确定主运顺序
    order = DAY_ORDER if is_day_chart else NIGHT_ORDER
    
    # 循环直到达到最大年龄
    # 注意：标准法达周期为75年，之后通常循环，或者进入特殊的高龄期
    # 这里我们采用循环模式
    cycle_index = 0
    
    # 防止死循环
    while current_age < max_age and cycle_index < 1000:
        # 当前周期内的主星索引
        planet_idx = cycle_index % len(order)
        major_lord = order[planet_idx]
        major_duration = FIRDARIA_YEARS[major_lord]
        
        # 检查是否为南北交点 (无子运)
        if major_lord in (Planet.NORTH_NODE, Planet.SOUTH_NODE):
            end_age = current_age + major_duration
            periods.append(FirdariaPeriod(
                start_age=current_age,
                end_age=end_age,
                major_lord=major_lord,
                sub_lord=None,
                duration=major_duration
            ))
            current_age = end_age
        else:
            # 正常行星，有7个子运
            sub_duration = major_duration / 7.0
            sub_lords = get_sub_lords(major_lord)
            
            for sub_lord in sub_lords:
                end_age = current_age + sub_duration
                # 截断超出max_age的部分（可选，这里保留完整周期）
                
                periods.append(FirdariaPeriod(
                    start_age=current_age,
                    end_age=end_age,
                    major_lord=major_lord,
                    sub_lord=sub_lord,
                    duration=sub_duration
                ))
                current_age = end_age
                
        cycle_index += 1
        
    return periods


def get_firdaria_lord_at_age(age: float, is_day_chart: bool) -> Optional[FirdariaPeriod]:
    """
    获取指定年龄的法达主星和子星
    
    参数:
        age: 年龄（浮点数）
        is_day_chart: 是否为日间盘
        
    返回:
        FirdariaPeriod对象，包含当前的主运和子运信息
    """
    # 只需要计算到这个年龄即可，稍微多一点以确保覆盖
    periods = calculate_firdaria_periods(is_day_chart, max_age=age + 1.0)
    
    for p in periods:
        if p.start_age <= age < p.end_age:
            return p
            
    return None
