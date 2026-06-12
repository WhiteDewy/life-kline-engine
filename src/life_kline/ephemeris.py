"""
ephemeris.py - Swiss Ephemeris 适配层

这个模块负责调用 pyswisseph 库来计算真实的天文数据，
并将结果转换为本引擎使用的 ChartData 格式。
"""

import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union
import math

try:
    import swisseph as swe
except ImportError:
    swe = None

from .models import ChartData, PlanetInfo
from .constants import Planet, Sign, CalculationMode

class EphemerisEngine:
    """
    Swiss Ephemeris 引擎封装类
    
    负责：
    1. 管理星历表路径
    2. 计算行星位置
    3. 计算宫位
    4. 转换为 ChartData
    """
    
    # 行星映射表：Life-Kline Planet -> Swisseph Planet ID
    PLANET_MAPPING = {
        Planet.SUN: swe.SUN,
        Planet.MOON: swe.MOON,
        Planet.MERCURY: swe.MERCURY,
        Planet.VENUS: swe.VENUS,
        Planet.MARS: swe.MARS,
        Planet.JUPITER: swe.JUPITER,
        Planet.SATURN: swe.SATURN,
        Planet.URANUS: swe.URANUS,
        Planet.NEPTUNE: swe.NEPTUNE,
        Planet.PLUTO: swe.PLUTO,
    }
    
    def __init__(self, ephe_path: Optional[str] = None):
        """
        初始化引擎
        
        参数:
            ephe_path: 星历表文件路径。如果为None，使用默认路径。
        """
        if swe is None:
            raise ImportError("未检测到 pyswisseph 库。请确保已正确安装。")
            
        if ephe_path:
            swe.set_ephe_path(ephe_path)
            
        # 默认设置为地心坐标
        swe.set_topo(0, 0, 0)
        
    def _get_julian_day(self, dt: datetime) -> float:
        """
        将 datetime 转换为 Julian Day (UT)
        
        注意：输入时间必须是 UTC 时间！
        """
        # swe.julday(year, month, day, hour, gregflag)
        # hour 需要包含分钟和秒的小数部分
        hour_decimal = dt.hour + dt.minute / 60.0 + dt.second / 3600.0 + dt.microsecond / 3600000.0
        return swe.julday(dt.year, dt.month, dt.day, hour_decimal)

    def _get_sign_from_longitude(self, longitude: float) -> Tuple[Sign, float]:

        """
        从绝对黄经计算星座和度数
        
        返回:
            (Sign, degree)
        """
        # 归一化到 0-360
        lon = longitude % 360
        
        # 计算星座索引 (0=Aries, 1=Taurus, ...)
        sign_index = int(lon // 30)
        degree = lon % 30
        
        # 映射到 Sign 枚举
        # Sign 定义顺序必须是白羊座开始
        signs = list(Sign)
        return signs[sign_index], degree

    def calculate_chart(
        self, 
        dt: datetime, 
        lat: float, 
        lon: float, 
        alt: float = 0.0,
        house_system: str = 'P' # Placidus
    ) -> ChartData:
        """
        计算星盘数据
        
        参数:
            dt: 时间 (建议使用 UTC)
            lat: 纬度 (北纬为正)
            lon: 经度 (东经为正)
            alt: 海拔 (米)
            house_system: 分宫制代码 ('P'=Placidus, 'W'=Whole Sign 等)
            
        返回:
            ChartData 对象
        """
        # 1. 初始化 ChartData
        chart = ChartData()
        chart.is_day_chart = False 
        chart.time_accuracy = "exact"
        
        jd = self._get_julian_day(dt)
        
        # 2. 计算宫位 (Cusps) 和 ASC/MC
        # swe.houses 返回 (cusps, ascmc)
        # 注意：pyswisseph 返回的 cusps 是 12 个元素的元组 (索引 0-11 对应 1-12 宫)
        # 与 C 版本不同（C 版本通常第 0 个是无效值）
        try:
            cusps, ascmc = swe.houses(jd, lat, lon, str.encode(house_system))
        except Exception as e:
            # Log the error with parameters for debugging
            print(f"ERROR in swe.houses: {e}")
            print(f"Parameters: jd={jd}, lat={lat}, lon={lon}, hsys={house_system}")
            raise e
        
        # 设置宫头
        chart_houses = []
        for i in range(12):
            h_lon = cusps[i]
            h_sign, h_deg = self._get_sign_from_longitude(h_lon)
            chart_houses.append((h_sign, h_deg))
        chart.houses = chart_houses
        
        # 获取上升点 (Ascendant) 用于判断昼夜盘
        asc_lon = ascmc[0]
        
        # 3. 计算行星位置
        # 标志位：SEFLG_SPEED (计算速度), SEFLG_SWIEPH (使用瑞士星历)
        flags = swe.FLG_SPEED | swe.FLG_SWIEPH
        
        sun_lon = 0.0
        
        for planet_enum, swe_id in self.PLANET_MAPPING.items():
            # swe.calc_ut 返回 ((lon, lat, dist, speed_lon, speed_lat, speed_dist), ret_flag)
            # 或者抛出 Error
            try:
                result, ret_flag = swe.calc_ut(jd, swe_id, flags)
                
                lon_val = result[0]
                lat_val = result[1]
                speed_val = result[3]
                
                sign, degree = self._get_sign_from_longitude(lon_val)
                
                # 计算所在宫位
                # swe.house_pos(armc, geolat, eps, hsys, xpin, ypin) 比较复杂
                # 我们可以简化：直接看它落在哪个宫头之间
                # 但更准确的方法是再次调用 swe.house_pos
                # 这里我们用简单的逻辑：
                # 遍历宫头，找到所在的区间
                
                # 简单宫位计算逻辑 (处理跨越 360/0 度的情况比较麻烦)
                # 使用 swisseph 的 house_pos 可能会更好，但这里我们可以先用简单的
                # 为了精确，我们调用 swe.house_pos
                armc = ascmc[2]
                eps = ascmc[0] # 这里有点问题，ascmc[0]是Asc。我们需要黄赤交角
                # 获取黄赤交角
                # swe.calc_ut 返回 (result_tuple, flag)
                ecl_res, ecl_flag = swe.calc_ut(jd, swe.ECL_NUT, 0) 
                true_eps = ecl_res[0]
                
                # swe.house_pos(armc, geolat, eps, (lon, lat), hsys)
                h_pos = swe.house_pos(armc, lat, true_eps, (lon_val, lat_val), str.encode(house_system))
                house_num = int(h_pos) 
                if house_num == 0: house_num = 12 # 偶尔边界情况
                
                # 构建 PlanetInfo
                p_info = PlanetInfo(
                    sign=sign,
                    degree=degree,
                    house=house_num,
                    is_retrograde=(speed_val < 0),
                    speed=speed_val,
                    latitude=lat_val,
                    longitude=lon_val
                )
                
                chart.add_planet(planet_enum, p_info)
                
                if planet_enum == Planet.SUN:
                    sun_lon = lon_val
                    chart.sun_longitude = sun_lon
                    
            except swe.Error as e:
                print(f"Error calculating {planet_enum}: {e}")
                
        # 4. 判断昼夜盘
        # 简单的判断：太阳在地平线上方为昼，下方为夜
        # 我们可以利用 house_pos，如果在 7,8,9,10,11,12 宫，通常为昼（取决于分宫制）
        # 或者比较 ASC 和 太阳位置。
        # 最准确的是看太阳的高度角 (Altitude)
        # 使用 swe.azalt 计算地平坐标
        # swe.azalt(jd, calc_flag, geopos, atpress, attemp, xin) -> (az, true_alt, app_alt)
        # xin 是 (lon, lat, dist)
        
        # 重新获取太阳坐标
        sun_res, _ = swe.calc_ut(jd, swe.SUN, flags)
        xin = (sun_res[0], sun_res[1], sun_res[2])
        geopos = (lon, lat, alt)
        
        # atpress=0, attemp=0 忽略大气折射
        az, true_alt, app_alt = swe.azalt(jd, swe.FLG_EQUATORIAL, geopos, 0, 0, xin)
        
        chart.is_day_chart = (true_alt > 0)
        # 实际上还要考虑大气折射产生的日出日落，但在占星中通常以中心点过地平线为准
        # 或者使用几何中心
        
        return chart


