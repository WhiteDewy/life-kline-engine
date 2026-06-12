"""
utils.py - 通用工具函数库

这个模块包含在整个项目中使用的通用工具函数：
1. 数学和统计工具
2. 数据处理工具
3. 验证和检查工具
4. 格式化和输出工具
5. 性能优化工具

这些函数被多个模块共享使用。
"""

import math
import time
import json
from typing import Dict, List, Optional, Tuple, Any, Union, Callable
from datetime import datetime
from functools import wraps
import statistics


# ============================================================================
# 1. 数学和统计工具
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


def weighted_average(values: List[float], weights: List[float]) -> float:
    """
    计算加权平均值
    
    参数:
        values: 值列表
        weights: 权重列表
    
    返回:
        加权平均值
    
    异常:
        ValueError: 当值和权重数量不一致时
    
    示例:
        >>> weighted_average([1, 2, 3], [0.1, 0.3, 0.6])
        2.5
    """
    if len(values) != len(weights):
        raise ValueError("值和权重数量必须一致")
    
    if not values:
        return 0.0
    
    total_weight = sum(weights)
    if total_weight == 0:
        return sum(values) / len(values) if values else 0.0
    
    weighted_sum = sum(v * w for v, w in zip(values, weights))
    return weighted_sum / total_weight


def moving_average(values: List[float], window: int = 3) -> List[float]:
    """
    计算移动平均值
    
    参数:
        values: 值列表
        window: 窗口大小
    
    返回:
        移动平均值列表
    
    示例:
        >>> moving_average([1, 2, 3, 4, 5], 3)
        [2.0, 3.0, 4.0]
    """
    if not values or window <= 0 or window > len(values):
        return values.copy() if values else []
    
    result = []
    for i in range(len(values) - window + 1):
        window_values = values[i:i + window]
        avg = sum(window_values) / window
        result.append(avg)
    
    return result


def standard_deviation(values: List[float]) -> float:
    """
    计算标准差
    
    参数:
        values: 值列表
    
    返回:
        标准差
    
    示例:
        >>> standard_deviation([1, 2, 3, 4, 5])
        1.4142135623730951
    """
    if not values or len(values) < 2:
        return 0.0
    
    try:
        return statistics.stdev(values)
    except:
        # 手动计算
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return math.sqrt(variance)


# ============================================================================
# 2. 数据处理工具
# ============================================================================

def filter_dict_by_keys(original_dict: Dict, keys_to_keep: List) -> Dict:
    """
    根据键列表过滤字典
    
    参数:
        original_dict: 原始字典
        keys_to_keep: 要保留的键列表
    
    返回:
        过滤后的字典
    
    示例:
        >>> filter_dict_by_keys({'a': 1, 'b': 2, 'c': 3}, ['a', 'c'])
        {'a': 1, 'c': 3}
    """
    return {k: v for k, v in original_dict.items() if k in keys_to_keep}


def merge_dicts(dict1: Dict, dict2: Dict, overwrite: bool = True) -> Dict:
    """
    合并两个字典
    
    参数:
        dict1: 第一个字典
        dict2: 第二个字典
        overwrite: 如果键冲突，是否用dict2的值覆盖dict1的值
    
    返回:
        合并后的字典
    
    示例:
        >>> merge_dicts({'a': 1, 'b': 2}, {'b': 3, 'c': 4})
        {'a': 1, 'b': 3, 'c': 4}
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key not in result or overwrite:
            result[key] = value
        elif isinstance(result[key], dict) and isinstance(value, dict):
            # 递归合并嵌套字典
            result[key] = merge_dicts(result[key], value, overwrite)
    
    return result


def flatten_dict(nested_dict: Dict, parent_key: str = '', sep: str = '.') -> Dict:
    """
    展平嵌套字典
    
    参数:
        nested_dict: 嵌套字典
        parent_key: 父键前缀
        sep: 分隔符
    
    返回:
        展平后的字典
    
    示例:
        >>> flatten_dict({'a': {'b': 1, 'c': {'d': 2}}, 'e': 3})
        {'a.b': 1, 'a.c.d': 2, 'e': 3}
    """
    items = []
    for key, value in nested_dict.items():
        new_key = f"{parent_key}{sep}{key}" if parent_key else key
        
        if isinstance(value, dict):
            items.extend(flatten_dict(value, new_key, sep=sep).items())
        else:
            items.append((new_key, value))
    
    return dict(items)


def sort_dict_by_value(dictionary: Dict, reverse: bool = False) -> Dict:
    """
    按值对字典排序
    
    参数:
        dictionary: 原始字典
        reverse: 是否降序排序
    
    返回:
        排序后的字典
    
    示例:
        >>> sort_dict_by_value({'a': 3, 'b': 1, 'c': 2})
        {'b': 1, 'c': 2, 'a': 3}
    """
    return {k: v for k, v in sorted(dictionary.items(), key=lambda item: item[1], reverse=reverse)}


def chunk_list(lst: List, chunk_size: int) -> List[List]:
    """
    将列表分块
    
    参数:
        lst: 原始列表
        chunk_size: 块大小
    
    返回:
        分块后的列表
    
    示例:
        >>> chunk_list([1, 2, 3, 4, 5], 2)
        [[1, 2], [3, 4], [5]]
    """
    if chunk_size <= 0:
        return [lst]
    
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def remove_duplicates_preserve_order(lst: List) -> List:
    """
    移除列表中的重复项，保持原始顺序
    
    参数:
        lst: 原始列表
    
    返回:
        去重后的列表
    
    示例:
        >>> remove_duplicates_preserve_order([1, 3, 2, 3, 1, 4])
        [1, 3, 2, 4]
    """
    seen = set()
    result = []
    
    for item in lst:
        if item not in seen:
            seen.add(item)
            result.append(item)
    
    return result


# ============================================================================
# 3. 验证和检查工具
# ============================================================================

def validate_range(value: float, min_val: float, max_val: float, name: str = "值") -> bool:
    """
    验证值是否在指定范围内
    
    参数:
        value: 要验证的值
        min_val: 最小值
        max_val: 最大值
        name: 值名称（用于错误消息）
    
    返回:
        bool: 是否在范围内
    
    异常:
        ValueError: 如果值不在范围内
    """
    if not (min_val <= value <= max_val):
        raise ValueError(f"{name} {value} 超出范围 [{min_val}, {max_val}]")
    return True


def validate_not_none(value: Any, name: str = "值") -> bool:
    """
    验证值是否为None
    
    参数:
        value: 要验证的值
        name: 值名称（用于错误消息）
    
    返回:
        bool: 是否为None
    
    异常:
        ValueError: 如果值为None
    """
    if value is None:
        raise ValueError(f"{name} 不能为None")
    return True


def validate_type(value: Any, expected_type: type, name: str = "值") -> bool:
    """
    验证值的类型
    
    参数:
        value: 要验证的值
        expected_type: 期望的类型
        name: 值名称（用于错误消息）
    
    返回:
        bool: 类型是否正确
    
    异常:
        TypeError: 如果类型不匹配
    """
    if not isinstance(value, expected_type):
        raise TypeError(f"{name} 的类型应为 {expected_type.__name__}，但得到 {type(value).__name__}")
    return True


def check_required_fields(data: Dict, required_fields: List[str]) -> bool:
    """
    检查字典是否包含所有必需的字段
    
    参数:
        data: 要检查的字典
        required_fields: 必需字段列表
    
    返回:
        bool: 是否包含所有必需字段
    
    异常:
        ValueError: 如果缺少必需字段
    """
    missing_fields = [field for field in required_fields if field not in data]
    
    if missing_fields:
        raise ValueError(f"缺少必需字段: {', '.join(missing_fields)}")
    
    return True


def is_valid_email(email: str) -> bool:
    """
    验证电子邮件地址格式（简单验证）
    
    参数:
        email: 电子邮件地址
    
    返回:
        bool: 是否为有效电子邮件地址
    """
    if not email or '@' not in email or '.' not in email:
        return False
    
    # 简单的格式检查
    parts = email.split('@')
    if len(parts) != 2:
        return False
    
    username, domain = parts
    if not username or not domain:
        return False
    
    if '.' not in domain:
        return False
    
    return True


def is_valid_date(date_str: str, fmt: str = "%Y-%m-%d") -> bool:
    """
    验证日期字符串格式
    
    参数:
        date_str: 日期字符串
        fmt: 日期格式
    
    返回:
        bool: 是否为有效日期
    """
    try:
        datetime.strptime(date_str, fmt)
        return True
    except ValueError:
        return False


# ============================================================================
# 4. 格式化和输出工具
# ============================================================================

def format_percentage(value: float, decimals: int = 1) -> str:
    """
    格式化百分比
    
    参数:
        value: 百分比值（0-1）
        decimals: 小数位数
    
    返回:
        格式化后的百分比字符串
    
    示例:
        >>> format_percentage(0.4567, 1)
        '45.7%'
    """
    percentage = value * 100
    return f"{percentage:.{decimals}f}%"


def format_duration(seconds: float) -> str:
    """
    格式化时间 duration
    
    参数:
        seconds: 秒数
    
    返回:
        格式化后的时间字符串
    
    示例:
        >>> format_duration(3661.5)
        '1小时1分1.5秒'
    """
    if seconds < 0:
        return "0秒"
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    
    parts = []
    if hours > 0:
        parts.append(f"{hours}小时")
    if minutes > 0:
        parts.append(f"{minutes}分")
    if secs > 0 or not parts:  # 即使秒为0，如果没有其他部分也显示
        if secs.is_integer():
            parts.append(f"{int(secs)}秒")
        else:
            parts.append(f"{secs:.1f}秒")
    
    return "".join(parts)


def format_large_number(number: float) -> str:
    """
    格式化大数字（添加千位分隔符）
    
    参数:
        number: 数字
    
    返回:
        格式化后的字符串
    
    示例:
        >>> format_large_number(1234567.89)
        '1,234,567.89'
    """
    if number == 0:
        return "0"
    
    # 处理负数
    sign = "-" if number < 0 else ""
    number = abs(number)
    
    # 分离整数和小数部分
    integer_part = int(number)
    decimal_part = number - integer_part
    
    # 格式化整数部分
    integer_str = f"{integer_part:,}"
    
    # 处理小数部分
    if decimal_part > 0:
        # 保留最多2位小数
        decimal_str = f"{decimal_part:.2f}".split('.')[1]
        # 移除末尾的0
        decimal_str = decimal_str.rstrip('0')
        if decimal_str:
            return f"{sign}{integer_str}.{decimal_str}"
    
    return f"{sign}{integer_str}"


def print_table(data: List[Dict[str, Any]], columns: Optional[List[str]] = None) -> None:
    """
    打印表格
    
    参数:
        data: 数据列表（每个字典是一行）
        columns: 列名列表（如果为None，则使用所有键）
    
    示例:
        >>> data = [{'Name': 'Alice', 'Age': 25}, {'Name': 'Bob', 'Age': 30}]
        >>> print_table(data)
        Name  Age
        ----- ---
        Alice 25
        Bob   30
    """
    if not data:
        print("无数据")
        return
    
    # 确定列
    if columns is None:
        columns = list(data[0].keys())
    
    # 计算每列的最大宽度
    col_widths = {}
    for col in columns:
        # 列名宽度
        col_widths[col] = len(str(col))
        # 数据宽度
        for row in data:
            if col in row:
                col_widths[col] = max(col_widths[col], len(str(row[col])))
    
    # 打印表头
    header = "  ".join(str(col).ljust(col_widths[col]) for col in columns)
    print(header)
    
    # 打印分隔线
    separator = "  ".join("-" * col_widths[col] for col in columns)
    print(separator)
    
    # 打印数据行
    for row in data:
        row_str = "  ".join(str(row.get(col, "")).ljust(col_widths[col]) for col in columns)
        print(row_str)


def print_progress_bar(iteration: int, total: int, prefix: str = '', suffix: str = '', 
                      length: int = 50, fill: str = '█', print_end: str = "\r") -> None:
    """
    打印进度条
    
    参数:
        iteration: 当前迭代次数
        total: 总迭代次数
        prefix: 前缀字符串
        suffix: 后缀字符串
        length: 进度条长度
        fill: 填充字符
        print_end: 打印结束字符
    
    示例:
        >>> for i in range(101):
        >>>     print_progress_bar(i, 100, prefix='进度:')
    """
    percent = f"{100 * (iteration / float(total)):.1f}"
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end=print_end)
    
    # 完成后换行
    if iteration == total:
        print()


def json_pretty_print(data: Any, indent: int = 2) -> str:
    """
    美化JSON输出
    
    参数:
        data: JSON数据
        indent: 缩进空格数
    
    返回:
        美化后的JSON字符串
    """
    return json.dumps(data, indent=indent, ensure_ascii=False, default=str)


# ============================================================================
# 5. 性能优化工具
# ============================================================================

def timer(func: Callable) -> Callable:
    """
    函数计时装饰器
    
    参数:
        func: 要计时的函数
    
    返回:
        包装后的函数
    
    示例:
        >>> @timer
        >>> def slow_function():
        >>>     time.sleep(1)
        >>> 
        >>> slow_function()  # 会打印执行时间
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        
        elapsed = end_time - start_time
        print(f"函数 {func.__name__} 执行时间: {format_duration(elapsed)}")
        
        return result
    
    return wrapper


class Timer:
    """
    上下文管理器计时器
    
    示例:
        >>> with Timer("某个操作"):
        >>>     time.sleep(1)
        >>> # 会打印: 某个操作 执行时间: 1.0秒
    """
    
    def __init__(self, name: str = "操作"):
        self.name = name
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = time.perf_counter()
        elapsed = end_time - self.start_time
        
        if exc_type is None:
            print(f"{self.name} 执行时间: {format_duration(elapsed)}")
        else:
            print(f"{self.name} 执行失败，已用时间: {format_duration(elapsed)}")


def memoize(func: Callable) -> Callable:
    """
    记忆化装饰器（缓存函数结果）
    
    参数:
        func: 要记忆化的函数
    
    返回:
        包装后的函数
    
    示例:
        >>> @memoize
        >>> def expensive_calculation(x):
        >>>     print(f"计算 {x}")
        >>>     return x * x
        >>> 
        >>> expensive_calculation(5)  # 打印"计算 5"，返回25
        >>> expensive_calculation(5)  # 不打印，直接返回25（从缓存）
    """
    cache = {}
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        # 创建缓存键（注意：对于复杂参数可能不是最优）
        key = (args, tuple(sorted(kwargs.items())))
        
        if key not in cache:
            cache[key] = func(*args, **kwargs)
        
        return cache[key]
    
    return wrapper


class Cache:
    """
    简单的缓存类
    
    示例:
        >>> cache = Cache(max_size=100, ttl=3600)  # 最大100项，1小时过期
        >>> cache.set("key", "value")
        >>> value = cache.get("key")
    """
    
    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        """
        初始化缓存
        
        参数:
            max_size: 最大缓存项数
            ttl: 生存时间（秒）
        """
        self.cache = {}
        self.max_size = max_size
        self.ttl = ttl
        self.access_order = []  # 用于LRU淘汰
    
    def set(self, key: Any, value: Any) -> None:
        """
        设置缓存项
        
        参数:
            key: 键
            value: 值
        """
        # 如果达到最大大小，移除最久未使用的项
        if len(self.cache) >= self.max_size and key not in self.cache:
            lru_key = self.access_order.pop(0)
            del self.cache[lru_key]
        
        # 设置缓存项
        self.cache[key] = {
            'value': value,
            'timestamp': time.time()
        }
        
        # 更新访问顺序
        if key in self.access_order:
            self.access_order.remove(key)
        self.access_order.append(key)
    
    def get(self, key: Any, default: Any = None) -> Any:
        """
        获取缓存项
        
        参数:
            key: 键
            default: 默认值
        
        返回:
            缓存值或默认值
        """
        if key not in self.cache:
            return default
        
        item = self.cache[key]
        
        # 检查是否过期
        if time.time() - item['timestamp'] > self.ttl:
            del self.cache[key]
            self.access_order.remove(key)
            return default
        
        # 更新访问顺序
        self.access_order.remove(key)
        self.access_order.append(key)
        
        return item['value']
    
    def clear(self) -> None:
        """清空缓存"""
        self.cache.clear()
        self.access_order.clear()
    
    def size(self) -> int:
        """
        获取缓存大小
        
        返回:
            缓存项数量
        """
        return len(self.cache)


# ============================================================================
# 6. 星座和行星工具（项目专用）
# ============================================================================

def degree_to_dms(degrees: float) -> Tuple[int, int, float]:
    """
    将十进制度数转换为度分秒
    
    参数:
        degrees: 十进制度数
    
    返回:
        (度, 分, 秒) 元组
    
    示例:
        >>> degree_to_dms(10.5125)
        (10, 30, 45.0)
    """
    deg = int(degrees)
    minutes_float = (degrees - deg) * 60
    minutes = int(minutes_float)
    seconds = (minutes_float - minutes) * 60
    
    return deg, minutes, seconds


def dms_to_degree(degrees: int, minutes: int, seconds: float) -> float:
    """
    将度分秒转换为十进制度数
    
    参数:
        degrees: 度
        minutes: 分
        seconds: 秒
    
    返回:
        十进制度数
    
    示例:
        >>> dms_to_degree(10, 30, 45)
        10.5125
    """
    return degrees + minutes / 60.0 + seconds / 3600.0


def format_degree(degrees: float, precision: int = 2) -> str:
    """
    格式化度数显示
    
    参数:
        degrees: 度数
        precision: 小数精度
    
    返回:
        格式化后的字符串
    
    示例:
        >>> format_degree(10.5125, 1)
        '10°30'45.0"'
    """
    deg, minutes, seconds = degree_to_dms(degrees)
    return f"{deg}°{minutes}'{seconds:.{precision}f}\""


def get_zodiac_sign(degree: float) -> Tuple[str, float]:
    """
    根据黄经度数获取星座和星座内度数
    
    参数:
        degree: 黄经度数（0-360）
    
    返回:
        (星座名称, 星座内度数) 元组
    
    示例:
        >>> get_zodiac_sign(45.5)
        ('TAURUS', 15.5)  # 45.5° = 金牛座15.5°
    """
    # 星座顺序（从白羊座开始）
    signs = ["ARIES", "TAURUS", "GEMINI", "CANCER", "LEO", "VIRGO",
             "LIBRA", "SCORPIO", "SAGITTARIUS", "CAPRICORN", "AQUARIUS", "PISCES"]
    
    # 每个星座30度
    sign_index = int(degree // 30)
    sign_degree = degree % 30
    
    # 处理边界情况
    if sign_index >= 12:
        sign_index = 11
        sign_degree = 29.999
    
    return signs[sign_index], sign_degree


def get_aspect_angle(planet1_long: float, planet2_long: float) -> float:
    """
    获取两个行星之间的相位角度
    
    参数:
        planet1_long: 行星1黄经
        planet2_long: 行星2黄经
    
    返回:
        相位角度（0-180度）
    """
    return deg_diff(planet1_long, planet2_long)


def is_retrograde_calculator(speed: float, planet: str = "") -> Tuple[bool, str]:
    """
    判断行星是否逆行
    
    参数:
        speed: 行星速度（度/天）
        planet: 行星名称（可选）
    
    返回:
        (是否逆行, 描述) 元组
    
    示例:
        >>> is_retrograde_calculator(-0.5, "Mars")
        (True, "火星逆行")
    """
    is_retro = speed < 0
    
    if planet:
        planet_name = planet
        description = f"{planet_name}{'逆行' if is_retro else '顺行'}"
    else:
        description = "逆行" if is_retro else "顺行"
    
    return is_retro, description


# ============================================================================
# 7. 导出函数
# ============================================================================

__all__ = [
    # 数学和统计工具
    "clamp",
    "normalize_to_range",
    "safe_divide",
    "deg_diff",
    "is_between",
    "weighted_average",
    "moving_average",
    "standard_deviation",
    
    # 数据处理工具
    "filter_dict_by_keys",
    "merge_dicts",
    "flatten_dict",
    "sort_dict_by_value",
    "chunk_list",
    "remove_duplicates_preserve_order",
    
    # 验证和检查工具
    "validate_range",
    "validate_not_none",
    "validate_type",
    "check_required_fields",
    "is_valid_email",
    "is_valid_date",
    
    # 格式化和输出工具
    "format_percentage",
    "format_duration",
    "format_large_number",
    "print_table",
    "print_progress_bar",
    "json_pretty_print",
    
    # 性能优化工具
    "timer",
    "Timer",
    "memoize",
    "Cache",
    
    # 星座和行星工具
    "degree_to_dms",
    "dms_to_degree",
    "format_degree",
    "get_zodiac_sign",
    "get_aspect_angle",
    "is_retrograde_calculator",
]