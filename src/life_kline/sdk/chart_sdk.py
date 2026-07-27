"""
chart_sdk.py — 星盘计算 SDK

封装核心星盘计算能力，提供简洁的 API 接口。

用法：
    sdk = ChartSDK()
    chart = sdk.calculate_natal(birth_time, lat, lon, tz)
    positions = sdk.get_planet_positions(birth_time, lat, lon, tz)
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from ..ephemeris import EphemerisEngine
from ..constants import Planet, Sign


class ChartSDK:
    """
    星盘计算 SDK。

    提供核心的星盘计算能力，包括：
    - 本命盘计算
    - 行星位置获取
    - 宫位计算
    - 基本相位计算
    """

    def __init__(self):
        self._engine = EphemerisEngine()

    def calculate_natal(
        self,
        birth_time: datetime,
        lat: float,
        lon: float,
        timezone_offset: float = 8.0,
        house_system: str = 'B',
    ) -> dict[str, Any]:
        """
        计算本命盘。

        Args:
            birth_time: 出生时间（本地时间）
            lat: 纬度
            lon: 经度
            timezone_offset: 时区偏移（默认 +8.0 中国）
            house_system: 宫位系统（默认 B = Placidus）

        Returns:
            本命盘数据字典，包含：
            - planets: 行星位置
            - houses: 宫位
            - aspects: 相位
            - asc: 上升点
            - mc: 天顶
        """
        chart = self._engine.calculate_chart(
            birth_time, lat, lon, house_system=house_system
        )

        return {
            "planets": {
                p.value: {
                    "longitude": chart.planet_positions[p].longitude,
                    "latitude": chart.planet_positions[p].latitude,
                    "speed": chart.planet_positions[p].speed,
                    "sign": chart.planet_signs[p].value,
                    "sign_longitude": chart.planet_sign_longitudes[p],
                    "house": chart.planet_houses[p],
                }
                for p in Planet
                if p in chart.planet_positions
            },
            "houses": {
                "signs": [h.sign.value for h in chart.houses],
                "cusps": [h.cusp for h in chart.houses],
            },
            "asc": chart.asc,
            "mc": chart.mc,
            "is_day_chart": chart.is_day_chart,
            "house_system": house_system,
        }

    def get_planet_positions(
        self,
        birth_time: datetime,
        lat: float,
        lon: float,
    ) -> dict[str, dict[str, Any]]:
        """
        获取行星位置。

        Args:
            birth_time: 出生时间
            lat: 纬度
            lon: 经度

        Returns:
            行星位置字典
        """
        chart = self._engine.calculate_chart(birth_time, lat, lon)

        return {
            p.value: {
                "longitude": chart.planet_positions[p].longitude,
                "sign": chart.planet_signs[p].value,
                "house": chart.planet_houses[p],
            }
            for p in Planet
            if p in chart.planet_positions
        }

    def get_aspects(
        self,
        birth_time: datetime,
        lat: float,
        lon: float,
    ) -> list[dict[str, Any]]:
        """
        计算主要相位。

        Args:
            birth_time: 出生时间
            lat: 纬度
            lon: 经度

        Returns:
            相位列表
        """
        from ..aspects import AspectCalculator

        chart = self._engine.calculate_chart(birth_time, lat, lon)
        calculator = AspectCalculator()
        aspects = calculator.calculate_aspects(chart.planet_positions)

        return [
            {
                "planet1": a.planet1.value,
                "planet2": a.planet2.value,
                "aspect_type": a.aspect_type.value,
                "orb": a.orb,
            }
            for a in aspects
        ]

    def get_houses(
        self,
        birth_time: datetime,
        lat: float,
        lon: float,
        house_system: str = 'B',
    ) -> dict[str, Any]:
        """
        获取宫位数据。

        Args:
            birth_time: 出生时间
            lat: 纬度
            lon: 经度
            house_system: 宫位系统

        Returns:
            宫位数据字典
        """
        chart = self._engine.calculate_chart(
            birth_time, lat, lon, house_system=house_system
        )

        return {
            "houses": [
                {"sign": h.sign.value, "cusp": h.cusp}
                for h in chart.houses
            ],
            "asc": chart.asc,
            "mc": chart.mc,
        }

    def get_asc_sign(
        self,
        birth_time: datetime,
        lat: float,
        lon: float,
    ) -> str:
        """
        获取上升星座。

        Args:
            birth_time: 出生时间
            lat: 纬度
            lon: 经度

        Returns:
            上升星座名称（如 "ARIES"）
        """
        chart = self._engine.calculate_chart(birth_time, lat, lon)
        return chart.houses[0].sign.value if chart.houses else "UNKNOWN"


# ============================================================================
# 便捷函数
# ============================================================================

def calculate_natal_chart(
    birth_time: datetime,
    lat: float,
    lon: float,
    timezone_offset: float = 8.0,
) -> dict[str, Any]:
    """
    便捷函数：计算本命盘。

    Args:
        birth_time: 出生时间
        lat: 纬度
        lon: 经度
        timezone_offset: 时区偏移

    Returns:
        本命盘数据字典
    """
    sdk = ChartSDK()
    return sdk.calculate_natal(birth_time, lat, lon, timezone_offset)
