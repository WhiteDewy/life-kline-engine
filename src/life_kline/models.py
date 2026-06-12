"""
models.py - 核心数据模型定义

这个文件定义了星盘计算引擎的核心数据结构：
1. PlanetFeature: 单个行星的特征集合
2. ChartData: 整个星盘的数据集合
3. 相关的数据类型定义
"""

from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime

# 导入常量
from .constants import (
    Planet, Sign, AspectType, CalculationMode, 
    ANGULAR_HOUSES, SUCCEDENT_HOUSES, CADENT_HOUSES
)


# ============================================================================
# 1. 行星信息结构
# ============================================================================

@dataclass
class PlanetInfo:
    """
    行星的详细信息
    
    属性:
        sign: 行星所在的星座
        degree: 行星在星座中的度数（0-29.999）
        house: 行星所在的宫位（1-12）
        is_retrograde: 是否逆行
        speed: 行星的运行速度（度/天）
        latitude: 行星的黄纬
        longitude: 行星的绝对黄经（0-360度）
    """
    sign: Sign
    degree: float
    house: int
    name: str = ""
    is_retrograde: bool = False
    speed: float = 0.0
    latitude: float = 0.0
    longitude: float = 0.0
    
    def __post_init__(self):
        """初始化后的验证和调整"""
        # 确保度数是有效的
        if self.degree < 0 or self.degree >= 30:
            self.degree = self.degree % 30
        
        # 确保宫位是有效的
        if self.house < 1 or self.house > 12:
            raise ValueError(f"宫位必须在1-12之间，当前为: {self.house}")
    
    def get_absolute_position(self) -> float:
        """
        获取行星的绝对黄经（0-360度）
        
        返回:
            绝对黄经度数
        """
        # 星座的起始度数 + 行星在该星座中的度数
        sign_index = list(Sign).index(self.sign)
        return sign_index * 30 + self.degree


# ============================================================================
# 2. 行星特征类（根据PRD定义）
# ============================================================================

class PlanetFeature:
    """
    当前焦点行星的特征集合
    
    这个类存储了单个行星的所有计算特征值，每个特征都有明确定义的范围。
    用于最终的评分计算。
    """
    
    def __init__(self):
        """
        初始化行星特征
        
        所有特征值都有明确定义的范围：
        1. [-1, +1] 表示好坏程度（-1最差，+1最好）
        2. [0, 1] 表示强度或程度
        """
        
        # 当前行星的单个值特征（所有值都有明确定义的范围）
        self.dignity = 0.0           # [-1, +1] 当前行星尊贵度
        self.house_power = 0.0       # [-1, +1] 当前行星所在宫位力量
        self.aspect_benefic = 0.0    # [0, 1] 吉相位强度
        self.aspect_malefic = 0.0    # [0, 1] 凶相位强度
        self.reception = 0.0         # [0, 1] 接纳互容强度
        self.support_resources = 0.0 # [0, 1] 资源助力
        self.load_pressure = 0.0     # [0, 1] 压力负荷
        self.theme_coherence = 0.0   # [0, 1] 主题一致性
        self.data_quality = 0.0      # [0, 1] 数据质量
        
        # 调试信息（不参与计算，仅用于分析和调试）
        self.debug = {
            'dignity_breakdown': {},      # 尊贵度分项计算详情
            'aspect_details': [],         # 相位详情列表
            'reception_details': [],      # 接纳详情列表
            'feature_calculation': {},    # 特征计算的中间值
            'timestamp': datetime.now().isoformat()  # 计算时间戳
        }
    
    def validate(self) -> bool:
        """
        验证所有特征值是否在有效范围内
        
        返回:
            bool: 所有特征值是否有效
        
        异常:
            如果特征值超出范围，会打印警告信息
        """
        valid = True
        
        # 检查 [-1, 1] 范围的特征
        for attr, value in [
            ('dignity', self.dignity),
            ('house_power', self.house_power)
        ]:
            if value < -1.0 or value > 1.0:
                print(f"警告: {attr} 值 {value:.3f} 超出范围 [-1, 1]")
                valid = False
        
        # 检查 [0, 1] 范围的特征
        for attr, value in [
            ('aspect_benefic', self.aspect_benefic),
            ('aspect_malefic', self.aspect_malefic),
            ('reception', self.reception),
            ('support_resources', self.support_resources),
            ('load_pressure', self.load_pressure),
            ('theme_coherence', self.theme_coherence),
            ('data_quality', self.data_quality)
        ]:
            if value < 0.0 or value > 1.0:
                print(f"警告: {attr} 值 {value:.3f} 超出范围 [0, 1]")
                valid = False
        
        return valid
    
    def to_dict(self) -> Dict[str, Any]:
        """
        将特征转换为字典格式（便于序列化）
        
        返回:
            包含所有特征的字典
        """
        return {
            'dignity': self.dignity,
            'house_power': self.house_power,
            'aspect_benefic': self.aspect_benefic,
            'aspect_malefic': self.aspect_malefic,
            'reception': self.reception,
            'support_resources': self.support_resources,
            'load_pressure': self.load_pressure,
            'theme_coherence': self.theme_coherence,
            'data_quality': self.data_quality,
            'debug': self.debug
        }
    
    def summary(self) -> str:
        """
        生成特征的文本摘要
        
        返回:
            特征摘要字符串
        """
        lines = [
            "行星特征摘要:",
            f"  尊贵度: {self.dignity:+.3f}",
            f"  宫位力量: {self.house_power:+.3f}",
            f"  吉相位强度: {self.aspect_benefic:.3f}",
            f"  凶相位强度: {self.aspect_malefic:.3f}",
            f"  接纳强度: {self.reception:.3f}",
            f"  资源支持: {self.support_resources:.3f}",
            f"  压力负荷: {self.load_pressure:.3f}",
            f"  主题一致性: {self.theme_coherence:.3f}",
            f"  数据质量: {self.data_quality:.3f}",
        ]
        return "\n".join(lines)


# ============================================================================
# 3. 星盘数据类（根据PRD定义）
# ============================================================================

class ChartData:
    """
    全盘数据（共享给所有行星）
    
    这个类存储了整个星盘的所有数据，包括：
    1. 所有行星的位置信息
    2. 计算出的尊贵度、宫位力量、相位等
    3. 盘的基本属性（昼夜、时间精度等）
    
    注意：这个类的实例会被多个计算函数共享使用。
    """
    
    def __init__(self):
        """
        初始化星盘数据
        
        注意：所有数据字典都应该在计算前初始化，避免None值错误。
        """
        
        # 核心数据：行星位置信息
        self.planets: Dict[Planet, PlanetInfo] = {}
        
        # 计算缓存：避免重复计算
        self.dignities_by_planet: Dict[Planet, float] = {}      # 行星→尊贵度
        self.house_powers: Dict[int, float] = {}                # 宫位编号→力量值
        self.aspect_matrix: Dict[Planet, Dict[Planet, Dict]] = {}  # 相位矩阵
        self.reception_matrix: Dict[Planet, Dict[Planet, float]] = {}  # 接纳矩阵
        
        # 盘基本信息
        self.is_day_chart: bool = True              # 是否为日间盘
        self.sun_longitude: float = 0.0             # 太阳黄经度数
        self.time_accuracy: str = 'unknown'         # 时间精度
        self.mode: CalculationMode = CalculationMode.MODERN  # 计算模式
        
        # 技术覆盖标志
        self.has_fixed_stars: bool = False          # 是否有恒星数据
        self.has_arabic_parts: bool = False         # 是否有阿拉伯点
        self.has_antiscia: bool = False             # 是否有映点
        self.has_parallels: bool = False            # 是否有赤纬平行
        
        # 辅助数据
        self.chart_time: Optional[datetime] = None  # 星盘时间
        self.location: Optional[Dict[str, float]] = None  # 地理位置
        self.historical_data: List[Dict] = []       # 历史数据（用于趋势计算）
        self.firdaria_lord: Optional[Planet] = None # 法达大运主星（用于趋势计算）
        
        # 调试信息
        self.debug: Dict[str, Any] = {
            'calculation_log': [],                   # 计算日志
            'warnings': [],                          # 警告信息
            'performance': {}                        # 性能数据
        }
    
    def add_planet(self, planet: Planet, planet_info: PlanetInfo) -> None:
        """
        添加行星到星盘
        
        参数:
            planet: 行星枚举
            planet_info: 行星信息对象
        
        异常:
            ValueError: 如果行星已存在或信息无效
        """
        if planet in self.planets:
            raise ValueError(f"行星 {planet.value} 已存在于星盘中")
        
        # 验证宫位范围
        if planet_info.house < 1 or planet_info.house > 12:
            raise ValueError(f"行星 {planet.value} 的宫位必须为1-12")
        
        # 验证度数范围
        if planet_info.degree < 0 or planet_info.degree >= 30:
            raise ValueError(f"行星 {planet.value} 的度数必须在0-30之间")
        
        self.planets[planet] = planet_info
    
    def get_planet_info(self, planet: Planet) -> Optional[PlanetInfo]:
        """
        获取行星信息
        
        参数:
            planet: 行星枚举
        
        返回:
            行星信息对象，如果不存在则返回None
        """
        return self.planets.get(planet)
    
    def get_planet_house(self, planet: Planet) -> Optional[int]:
        """
        获取行星所在的宫位
        
        参数:
            planet: 行星枚举
        
        返回:
            宫位编号（1-12），如果行星不存在则返回None
        """
        planet_info = self.get_planet_info(planet)
        return planet_info.house if planet_info else None
    
    def get_planets_in_house(self, house: int) -> List[Planet]:
        """
        获取指定宫位中的所有行星
        
        参数:
            house: 宫位编号（1-12）
        
        返回:
            该宫位中的行星列表
        """
        if house < 1 or house > 12:
            return []
        
        planets_in_house = []
        for planet, info in self.planets.items():
            if info.house == house:
                planets_in_house.append(planet)
        
        return planets_in_house
    
    def get_house_type(self, house: int) -> str:
        """
        获取宫位类型（角宫、续宫、果宫）
        
        参数:
            house: 宫位编号
        
        返回:
            宫位类型字符串
        """
        if house in ANGULAR_HOUSES:
            return 'angular'     # 角宫
        elif house in SUCCEDENT_HOUSES:
            return 'succedent'   # 续宫
        elif house in CADENT_HOUSES:
            return 'cadent'      # 果宫
        else:
            return 'unknown'
    
    def is_planet_in_angular_house(self, planet: Planet) -> bool:
        """
        判断行星是否在角宫
        
        参数:
            planet: 行星枚举
        
        返回:
            bool: 是否在角宫
        """
        house = self.get_planet_house(planet)
        return house in ANGULAR_HOUSES if house else False
    
    def clear_cache(self) -> None:
        """
        清空计算缓存
        
        当星盘数据发生变化时，需要调用此函数清除缓存，
        以确保下次计算使用最新的数据。
        """
        self.dignities_by_planet.clear()
        self.house_powers.clear()
        self.aspect_matrix.clear()
        self.reception_matrix.clear()
        
        # 记录缓存清除日志
        self.debug['calculation_log'].append({
            'action': 'clear_cache',
            'timestamp': datetime.now().isoformat()
        })
    
    def validate(self) -> bool:
        """
        验证星盘数据的完整性
        
        返回:
            bool: 数据是否基本完整
        """
        # 检查必需的行星（太阳和月亮）
        required_planets = [Planet.SUN, Planet.MOON]
        missing = [p for p in required_planets if p not in self.planets]
        
        if missing:
            print(f"警告: 缺少必需的行星: {[p.value for p in missing]}")
            return False
        
        # 检查行星信息的完整性
        for planet, info in self.planets.items():
            if info.house == 0:
                print(f"警告: 行星 {planet.value} 没有设置宫位")
                return False
        
        return True
    
    def summary(self) -> str:
        """
        生成星盘数据的文本摘要
        
        返回:
            星盘摘要字符串
        """
        lines = [
            f"星盘数据摘要:",
            f"  模式: {self.mode.value}",
            f"  昼夜: {'日间盘' if self.is_day_chart else '夜间盘'}",
            f"  时间精度: {self.time_accuracy}",
            f"  行星数量: {len(self.planets)}",
        ]
        
        # 行星位置摘要
        if self.planets:
            lines.append("  行星位置:")
            for planet, info in sorted(self.planets.items()):
                lines.append(f"    {planet.value}: {info.sign.value} {info.degree:.1f}° "
                           f"(第{info.house}宫, {'逆行' if info.is_retrograde else '顺行'})")
        
        # 技术覆盖
        tech_lines = []
        if self.has_fixed_stars:
            tech_lines.append("恒星")
        if self.has_arabic_parts:
            tech_lines.append("阿拉伯点")
        if self.has_antiscia:
            tech_lines.append("映点")
        if self.has_parallels:
            tech_lines.append("赤纬平行")
        
        if tech_lines:
            lines.append(f"  技术覆盖: {', '.join(tech_lines)}")
        
        return "\n".join(lines)


# ============================================================================
# 4. 相位数据结构
# ============================================================================

@dataclass
class Aspect:
    """
    相位数据
    
    属性:
        planet1: 第一个行星
        planet2: 第二个行星
        aspect_type: 相位类型
        exact_angle: 理论角度
        actual_angle: 实际角度差
        orb: 容许度误差
        strength: 相位强度（0-1）
        is_applying: 是否在形成中（正向接近）
        is_separating: 是否在分离中（正向远离）
    """
    planet1: Planet
    planet2: Planet
    aspect_type: AspectType
    exact_angle: float
    actual_angle: float
    orb: float
    strength: float
    is_applying: bool = False
    is_separating: bool = False
    
    def is_exact(self, threshold: float = 0.5) -> bool:
        """
        判断相位是否精确（容许度很小）
        
        参数:
            threshold: 精确度阈值
        
        返回:
            bool: 是否精确
        """
        return self.orb <= threshold
    
    def get_description(self) -> str:
        """
        获取相位的文字描述
        
        返回:
            相位描述字符串
        """
        applying = "形成中" if self.is_applying else ""
        separating = "分离中" if self.is_separating else ""
        exact = "精确" if self.is_exact() else ""
        
        status = applying or separating or exact or "非精确"
        
        return (f"{self.planet1.value} {self.aspect_type.value} {self.planet2.value} "
                f"(差{self.orb:.2f}°，强度{self.strength:.2f}) [{status}]")


# ============================================================================
# 5. 运势节点评分结果
# ============================================================================

@dataclass
class NodeScoreResult:
    """
    运势节点评分结果
    
    根据PRD中compute_node_score函数的返回结构定义
    """
    score: float                    # 综合评分 [-1, 1]
    confidence: float               # 置信度 [0, 1]
    ohlc: Dict[str, float]          # OHLC四象限值
    trend: float                    # 趋势 [-1, 1]
    volatility: float               # 波动性 [0, 1]
    features: Dict[str, float]      # 特征值
    debug: Dict[str, Any]           # 调试信息
    
    def __post_init__(self):
        """验证结果的有效性"""
        # 验证主要分数范围
        if self.score < -1.0 or self.score > 1.0:
            raise ValueError(f"评分 {self.score} 超出范围 [-1, 1]")
        
        if self.confidence < 0.0 or self.confidence > 1.0:
            raise ValueError(f"置信度 {self.confidence} 超出范围 [0, 1]")
        
        # 验证OHLC值
        for key in ['open', 'high', 'low', 'close']:
            if key not in self.ohlc:
                raise ValueError(f"OHLC缺少 {key} 值")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式（便于序列化）
        
        返回:
            结果字典
        """
        return {
            'score': self.score,
            'confidence': self.confidence,
            'ohlc': self.ohlc,
            'trend': self.trend,
            'volatility': self.volatility,
            'features': self.features,
            'debug': self.debug
        }
    
    def summary(self) -> str:
        """
        生成评分结果的文本摘要
        
        返回:
            结果摘要字符串
        """
        lines = [
            "运势节点评分结果:",
            f"  综合评分: {self.score:+.3f}",
            f"  置信度: {self.confidence:.1%}",
            f"  趋势: {self.trend:+.3f}",
            f"  波动性: {self.volatility:.3f}",
            "  OHLC四象限:",
            f"    开盘(起始): {self.ohlc.get('open', 0):.3f}",
            f"    高点(潜力): {self.ohlc.get('high', 0):.3f}",
            f"    低点(风险): {self.ohlc.get('low', 0):.3f}",
            f"    收盘(结果): {self.ohlc.get('close', 0):.3f}",
        ]
        
        # 特征值摘要
        lines.append("  特征值:")
        for feature, value in self.features.items():
            lines.append(f"    {feature}: {value:.3f}")
        
        return "\n".join(lines)


# ============================================================================
# 6. 工具函数（根据PRD必须首先定义）
# ============================================================================

def clamp(value: float, min_value: float, max_value: float) -> float:
    """
    限制值在[min_value, max_value]范围内
    
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
    线性归一化到新范围
    
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


def is_between(value: float, min_val: float, max_val: float, inclusive: bool = True) -> bool:
    """
    判断值是否在范围内
    
    参数:
        value: 要判断的值
        min_val: 范围最小值
        max_val: 范围最大值
        inclusive: 是否包含边界
    
    返回:
        bool: 值是否在范围内
    """
    if inclusive:
        return min_val <= value <= max_val
    else:
        return min_val < value < max_val


# 导出所有重要的类
__all__ = [
    # 数据类
    "PlanetInfo",
    "PlanetFeature",
    "ChartData",
    "Aspect",
    "NodeScoreResult",
    
    # 工具函数
    "clamp",
    "normalize_to_range",
    "safe_divide",
    "deg_diff",
    "is_between",
]