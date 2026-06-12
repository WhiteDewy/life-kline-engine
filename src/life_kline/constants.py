"""
constants.py - 占星常量定义

这个文件定义了所有占星学相关的基础常量，包括：
1. 行星列表和属性
2. 星座映射
3. 庙旺失陷映射表
4. 相位配置
5. 接纳权重表
6. 其他技术常量
"""

from enum import Enum
from typing import Dict, List, Set, Tuple

# ============================================================================
# 1. 行星定义
# ============================================================================

class Planet(str, Enum):
    """行星枚举"""
    SUN = "SUN"
    MOON = "MOON"
    MERCURY = "MERCURY"
    VENUS = "VENUS"
    MARS = "MARS"
    JUPITER = "JUPITER"
    SATURN = "SATURN"
    URANUS = "URANUS"
    NEPTUNE = "NEPTUNE"
    PLUTO = "PLUTO"
    NORTH_NODE = "NORTH_NODE"  # 北交点 (罗喉)
    SOUTH_NODE = "SOUTH_NODE"  # 南交点 (计都)
    
    # 方便属性访问
    @property
    def is_traditional(self) -> bool:
        """是否为传统行星（莉莉体系中的行星）"""
        traditional_planets = {
            Planet.SUN, Planet.MOON, Planet.MERCURY, Planet.VENUS,
            Planet.MARS, Planet.JUPITER, Planet.SATURN
        }
        return self in traditional_planets
    
    @property
    def is_outer(self) -> bool:
        """是否为外行星（天王、海王、冥王）"""
        outer_planets = {Planet.URANUS, Planet.NEPTUNE, Planet.PLUTO}
        return self in outer_planets
    
    @property
    def is_benefic(self) -> bool:
        """是否为吉星（金星、木星）"""
        return self in {Planet.VENUS, Planet.JUPITER}
    
    @property
    def is_malefic(self) -> bool:
        """是否为凶星（火星、土星）"""
        return self in {Planet.MARS, Planet.SATURN}


# 行星列表（方便遍历）
ALL_PLANETS = list(Planet)
TRADITIONAL_PLANETS = [p for p in Planet if p.is_traditional]
OUTER_PLANETS = [p for p in Planet if p.is_outer]

# ============================================================================
# 2. 星座定义
# ============================================================================

class Sign(str, Enum):
    """黄道十二星座"""
    ARIES = "ARIES"         # 白羊座
    TAURUS = "TAURUS"       # 金牛座
    GEMINI = "GEMINI"       # 双子座
    CANCER = "CANCER"       # 巨蟹座
    LEO = "LEO"             # 狮子座
    VIRGO = "VIRGO"         # 处女座
    LIBRA = "LIBRA"         # 天秤座
    SCORPIO = "SCORPIO"     # 天蝎座
    SAGITTARIUS = "SAGITTARIUS"  # 射手座
    CAPRICORN = "CAPRICORN" # 摩羯座
    AQUARIUS = "AQUARIUS"   # 水瓶座
    PISCES = "PISCES"       # 双鱼座

# 星座列表（按黄道顺序）
SIGNS_IN_ORDER = list(Sign)

# ============================================================================
# 3. 庙旺失陷映射表（莉莉体系 + 现代扩展）
# ============================================================================

# 庙宫（Domicile）：行星守护的星座
DOMICILE_SIGNS: Dict[Planet, List[Sign]] = {
    Planet.SUN: [Sign.LEO],                    # 太阳守护狮子座
    Planet.MOON: [Sign.CANCER],                # 月亮守护巨蟹座
    Planet.MERCURY: [Sign.GEMINI, Sign.VIRGO],  # 水星守护双子座和处女座
    Planet.VENUS: [Sign.TAURUS, Sign.LIBRA],   # 金星守护金牛座和天秤座
    Planet.MARS: [Sign.ARIES, Sign.SCORPIO],   # 火星守护白羊座和天蝎座
    Planet.JUPITER: [Sign.SAGITTARIUS, Sign.PISCES],  # 木星守护射手座和双鱼座
    Planet.SATURN: [Sign.CAPRICORN, Sign.AQUARIUS],   # 土星守护摩羯座和水瓶座
    
    # 外行星的现代庙宫（现代占星学惯例）
    Planet.URANUS: [Sign.AQUARIUS],            # 天王星守护水瓶座（现代）
    Planet.NEPTUNE: [Sign.PISCES],             # 海王星守护双鱼座（现代）
    Planet.PLUTO: [Sign.SCORPIO],              # 冥王星守护天蝎座（现代）
}

# 旺宫（Exaltation）：行星擢升的星座
EXALTATION_SIGNS: Dict[Planet, List[Sign]] = {
    Planet.SUN: [Sign.ARIES],          # 太阳擢升白羊座
    Planet.MOON: [Sign.TAURUS],        # 月亮擢升金牛座
    Planet.MERCURY: [Sign.VIRGO],      # 水星擢升处女座（有争议，部分为水瓶）
    Planet.VENUS: [Sign.PISCES],       # 金星擢升双鱼座
    Planet.MARS: [Sign.CAPRICORN],     # 火星擢升摩羯座
    Planet.JUPITER: [Sign.CANCER],     # 木星擢升巨蟹座
    Planet.SATURN: [Sign.LIBRA],       # 土星擢升天秤座
    
    # 外行星的现代旺宫（非莉莉体系）
    Planet.URANUS: [Sign.SCORPIO],     # 天王星擢升天蝎座（现代惯例）
    Planet.NEPTUNE: [Sign.CANCER],     # 海王星擢升巨蟹座（现代惯例）
    Planet.PLUTO: [Sign.PISCES],       # 冥王星擢升双鱼座（现代惯例）
}

# 擢升度数（Exaltation Degrees）
EXALTATION_DEGREES: Dict[Planet, float] = {
    Planet.SUN: 19.0,      # 白羊座19°
    Planet.MOON: 3.0,      # 金牛座3°
    Planet.MERCURY: 15.0,  # 处女座15°
    Planet.VENUS: 27.0,    # 双鱼座27°
    Planet.MARS: 28.0,     # 摩羯座28°
    Planet.JUPITER: 15.0,  # 巨蟹座15°
    Planet.SATURN: 21.0,   # 天秤座21°
}

# 失势宫（Detriment）：行星失势的星座（庙宫的对宫）
DETRIMENT_SIGNS: Dict[Planet, List[Sign]] = {
    Planet.SUN: [Sign.AQUARIUS],                     # 太阳失势水瓶座（狮子座对宫）
    Planet.MOON: [Sign.CAPRICORN],                   # 月亮失势摩羯座（巨蟹座对宫）
    Planet.MERCURY: [Sign.SAGITTARIUS, Sign.PISCES], # 水星失势射手座和双鱼座
    Planet.VENUS: [Sign.SCORPIO, Sign.ARIES],        # 金星失势天蝎座和白羊座
    Planet.MARS: [Sign.LIBRA, Sign.TAURUS],          # 火星失势天秤座和金牛座
    Planet.JUPITER: [Sign.GEMINI, Sign.VIRGO],       # 木星失势双子座和处女座
    Planet.SATURN: [Sign.CANCER, Sign.LEO],          # 土星失势巨蟹座和狮子座
    
    # 外行星的现代失势宫
    Planet.URANUS: [Sign.LEO],                       # 天王星失势狮子座
    Planet.NEPTUNE: [Sign.VIRGO],                    # 海王星失势处女座
    Planet.PLUTO: [Sign.TAURUS],                     # 冥王星失势金牛座
}

# 落陷宫（Fall）：行星落陷的星座（旺宫的对宫）
FALL_SIGNS: Dict[Planet, List[Sign]] = {
    Planet.SUN: [Sign.LIBRA],           # 太阳落陷天秤座（白羊座对宫）
    Planet.MOON: [Sign.SCORPIO],        # 月亮落陷天蝎座（金牛座对宫）
    Planet.MERCURY: [Sign.PISCES],      # 水星落陷双鱼座（处女座对宫）
    Planet.VENUS: [Sign.VIRGO],         # 金星落陷处女座（双鱼座对宫）
    Planet.MARS: [Sign.CANCER],         # 火星落陷巨蟹座（摩羯座对宫）
    Planet.JUPITER: [Sign.CAPRICORN],   # 木星落陷摩羯座（巨蟹座对宫）
    Planet.SATURN: [Sign.ARIES],        # 土星落陷白羊座（天秤座对宫）
    
    # 外行星的现代落陷宫
    Planet.URANUS: [Sign.TAURUS],       # 天王星落陷金牛座
    Planet.NEPTUNE: [Sign.CAPRICORN],   # 海王星落陷摩羯座
    Planet.PLUTO: [Sign.VIRGO],         # 冥王星落陷处女座
}

# ============================================================================
# 4. 相位配置
# ============================================================================

class AspectType(str, Enum):
    """相位类型"""
    CONJUNCTION = "CONJUNCTION"    # 合相 (0°)
    SEXTILE = "SEXTILE"           # 六合相 (60°)
    SQUARE = "SQUARE"             # 刑相 (90°)
    TRINE = "TRINE"               # 拱相 (120°)
    OPPOSITION = "OPPOSITION"     # 冲相 (180°)
    QUINCUNX = "QUINCUNX"         # 梅花相 (150°)

# 相位角度和容许度（容许度根据传统占星学设定）
ASPECT_CONFIG: Dict[AspectType, Dict[str, float]] = {
    AspectType.CONJUNCTION: {"angle": 0.0, "orb": 8.0, "strength": 1.0},
    AspectType.SEXTILE: {"angle": 60.0, "orb": 5.0, "strength": 0.6},
    AspectType.SQUARE: {"angle": 90.0, "orb": 6.0, "strength": 0.8},
    AspectType.TRINE: {"angle": 120.0, "orb": 6.0, "strength": 0.9},
    AspectType.OPPOSITION: {"angle": 180.0, "orb": 8.0, "strength": 0.8},
    AspectType.QUINCUNX: {"angle": 150.0, "orb": 2.0, "strength": 0.3},
}

PLANET_ORBS: Dict[Planet, float] = {
    Planet.SUN: 8.0,
    Planet.MOON: 7.0,
    Planet.MERCURY: 5.5,
    Planet.VENUS: 5.5,
    Planet.MARS: 6.0,
    Planet.JUPITER: 6.0,
    Planet.SATURN: 6.0,
    Planet.URANUS: 4.0,
    Planet.NEPTUNE: 4.0,
    Planet.PLUTO: 4.0,
    Planet.NORTH_NODE: 3.0,
    Planet.SOUTH_NODE: 3.0,
}

# ============================================================================
# 5. 接纳权重表（根据PRD中的权重）
# ============================================================================

RECEPTION_WEIGHTS: Dict[str, float] = {
    "DOMICILE": 1.0,           # 接纳（行星在对方的庙宫）
    "EXALTATION": 0.8,         # 擢升接纳
    "MUTUAL_DOMICILE": 1.5,    # 互容（互相在对方的庙宫）
    "MUTUAL_OTHER": 1.2,       # 其他互容
}

# ============================================================================
# 6. 工具常量和阈值
# ============================================================================

# 宫位相关
ANGULAR_HOUSES = [1, 4, 7, 10]       # 角宫
SUCCEDENT_HOUSES = [2, 5, 8, 11]     # 续宫
CADENT_HOUSES = [3, 6, 9, 12]        # 果宫

# 喜乐宫（Joy Houses）
JOY_HOUSES: Dict[Planet, int] = {
    Planet.MERCURY: 1,    # 水星喜乐第1宫
    Planet.MOON: 3,       # 月亮喜乐第3宫
    Planet.VENUS: 5,      # 金星喜乐第5宫
    Planet.MARS: 6,       # 火星喜乐第6宫
    Planet.SUN: 9,        # 太阳喜乐第9宫
    Planet.JUPITER: 11,   # 木星喜乐第11宫
    Planet.SATURN: 12,    # 土星喜乐第12宫
}

# 尊贵度计算的范围限制（用于归一化）
MAX_ESSENTIAL_RAW = 15.0   # 本质尊贵理论最大值
MIN_ESSENTIAL_RAW = -15.0  # 本质尊贵理论最小值

# 相位强度归一化因子
MAX_ASPECT_STRENGTH = 4.0  # 相位强度归一化分母

# 接纳强度归一化因子
MAX_RECEPTION_STRENGTH = 6.0  # 接纳强度归一化分母

# 宫位力量计算的权重（根据PRD）
HOUSE_POWER_WEIGHTS = {
    "lord_essential": 0.4,     # 宫主星本质尊贵
    "aspect_to_lord": 0.15,    # 宫内星与宫主星相位
    "planet_in_house": 0.05,   # 宫内行星状态
    "special_config": 0.2,     # 特殊配置
    "theme_bonus": 0.2,        # 宫位主题修正
}

# ============================================================================
# 7. 计算模式枚举
# ============================================================================

class CalculationMode(str, Enum):
    """计算模式"""
    LILLY_PURE = "LILLY_PURE"  # 莉莉原版模式，外行星不参与尊贵计算
    MODERN = "MODERN"          # 现代模式，包含外行星的现代规则

# ============================================================================
# 8. 时间精度权重（用于数据质量计算）
# ============================================================================

TIME_ACCURACY_WEIGHTS: Dict[str, float] = {
    "exact": 1.0,           # 精确时间
    "within_15min": 0.85,   # 15分钟内
    "within_1hour": 0.65,   # 1小时内
    "within_4hour": 0.4,    # 4小时内
    "unknown": 0.2,         # 时间未知
}

# ============================================================================
# 9. 工具函数
# ============================================================================

def clamp(value: float, min_value: float, max_value: float) -> float:
    """
    将值限制在指定范围内
    
    参数:
        value: 原始值
        min_value: 最小值
        max_value: 最大值
    
    返回:
        限制后的值
    
    示例:
        >>> clamp(1.5, 0, 1)
        1.0
        >>> clamp(-0.5, 0, 1)
        0.0
    """
    return max(min_value, min(max_value, value))


def normalize_to_range(
    value: float, 
    old_min: float, 
    old_max: float, 
    new_min: float = 0.0, 
    new_max: float = 1.0
) -> float:
    """
    将值从旧范围线性映射到新范围
    
    参数:
        value: 原始值
        old_min: 旧范围最小值
        old_max: 旧范围最大值
        new_min: 新范围最小值
        new_max: 新范围最大值
    
    返回:
        映射到新范围的值
    
    示例:
        >>> normalize_to_range(50, 0, 100, 0, 1)
        0.5
        >>> normalize_to_range(75, 0, 100, 0, 10)
        7.5
    """
    # 避免除零错误
    if abs(old_max - old_min) < 1e-10:
        return new_min
    
    # 线性映射公式
    return ((value - old_min) / (old_max - old_min)) * (new_max - new_min) + new_min


def deg_diff(deg1: float, deg2: float) -> float:
    """
    计算两个度数之间的最小差值（考虑360°循环）
    
    参数:
        deg1: 第一个度数
        deg2: 第二个度数
    
    返回:
        最小差值（0-180之间）
    
    示例:
        >>> deg_diff(350, 10)
        20.0
        >>> deg_diff(10, 350)
        20.0
    """
    diff = abs(deg1 - deg2) % 360.0
    return min(diff, 360.0 - diff)


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    安全除法，避免除零错误
    
    参数:
        numerator: 分子
        denominator: 分母
        default: 除零时返回的默认值
    
    返回:
        除法结果或默认值
    """
    if abs(denominator) < 1e-10:
        return default
    return numerator / denominator


def get_planet_orb(planet: Planet) -> float:
    return PLANET_ORBS.get(planet, 5.5)


# 导出所有重要的常量
__all__ = [
    # 枚举类
    "Planet",
    "Sign",
    "AspectType",
    "CalculationMode",
    
    # 列表
    "ALL_PLANETS",
    "TRADITIONAL_PLANETS",
    "OUTER_PLANETS",
    "SIGNS_IN_ORDER",
    
    # 映射表
    "DOMICILE_SIGNS",
    "EXALTATION_SIGNS",
    "EXALTATION_DEGREES",
    "DETRIMENT_SIGNS",
    "FALL_SIGNS",
    "ASPECT_CONFIG",
    "RECEPTION_WEIGHTS",
    "JOY_HOUSES",
    "TIME_ACCURACY_WEIGHTS",
    "HOUSE_POWER_WEIGHTS",
    "PLANET_ORBS",
    "get_planet_orb",
    
    # 常量
    "ANGULAR_HOUSES",
    "SUCCEDENT_HOUSES",
    "CADENT_HOUSES",
    "MAX_ESSENTIAL_RAW",
    "MIN_ESSENTIAL_RAW",
    "MAX_ASPECT_STRENGTH",
    "MAX_RECEPTION_STRENGTH",
    
    # 工具函数
    "clamp",
    "normalize_to_range",
    "deg_diff",
    "safe_divide",
]
