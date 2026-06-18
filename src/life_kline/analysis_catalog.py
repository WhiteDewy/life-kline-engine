"""
Static analysis catalog for the astrology product surface.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Optional


ANALYSIS_TYPES: List[Dict[str, Any]] = [
    {
        "key": "natal_blueprint",
        "title": "本命蓝图",
        "tagline": "先看你是什么样的人，再看你适合把自己活成什么职业路径。",
        "description": (
            "围绕星体、星座、宫位、相位与互溶接纳，先定人格基调与用户角色，再分析结构、杠杆、发光点和可发展的职业路线。"
        ),
        "category": "structure",
        "status": "active",
        "subjects_count": 1,
        "required_inputs": ["birth_time", "lat", "lon", "timezone"],
        "engines": ["natal_core"],
        "modules": ["用户角色", "结构与杠杆", "职业路线", "理论依据", "本命星盘", "样例校验"],
        "primary_cta": "进入体验",
        "output_route": "/reports/:id",
    },
    {
        "key": "phase_navigation",
        "title": "阶段导航",
        "tagline": "用本命结构 + 法达阶段理解你当下的人生旋律。",
        "description": (
            "当前版本的核心可用分析。先用本命结构定义底盘，再用法达主运与子运识别人生命题、机会窗口和风险点。"
        ),
        "category": "timing",
        "status": "active",
        "subjects_count": 1,
        "required_inputs": ["birth_time", "lat", "lon", "timezone"],
        "engines": ["natal_core", "firdaria"],
        "modules": [
            "阶段总览",
            "本命星盘",
            "本命蓝图",
            "高级规则",
            "样例校验",
            "当前阶段",
            "人生主轴",
            "人生曲线",
            "领域投射",
            "阶段时间表",
        ],
        "primary_cta": "进入体验",
        "output_route": "/reports/:id",
    },
    {
        "key": "annual_profection",
        "title": "年度节奏",
        "tagline": "把每一个年龄年的主轴和重点议题拆出来。",
        "description": (
            "后续将通过小限、年度主星与主题宫位，判断某一年应把火力集中在哪里。"
        ),
        "category": "timing",
        "status": "planned",
        "subjects_count": 1,
        "required_inputs": ["birth_time", "lat", "lon", "timezone"],
        "engines": ["natal_core", "profection"],
        "modules": ["年度焦点", "主星切换", "主题强化"],
        "primary_cta": "路线图中",
        "output_route": "/reports/:id",
    },
    {
        "key": "secondary_progression",
        "title": "次限演化",
        "tagline": "看一个人内部心理节奏如何慢慢变化。",
        "description": (
            "后续会把次限月亮、次限太阳和重要次限相位纳入，专门处理心理成熟与生命阶段演化。"
        ),
        "category": "timing",
        "status": "planned",
        "subjects_count": 1,
        "required_inputs": ["birth_time", "lat", "lon", "timezone"],
        "engines": ["natal_core", "secondary_progression"],
        "modules": ["内在节奏", "进展高光", "阶段简报"],
        "primary_cta": "路线图中",
        "output_route": "/reports/:id",
    },
    {
        "key": "synastry",
        "title": "关系合盘",
        "tagline": "分析两个人的吸引、摩擦与长期结构。",
        "description": (
            "后续会支持双人出生资料输入，从吸引机制、冲突模式、关系边界和长期协同来解释关系。"
        ),
        "category": "relationship",
        "status": "planned",
        "subjects_count": 2,
        "required_inputs": ["birth_time", "lat", "lon", "timezone"],
        "engines": ["natal_core", "synastry"],
        "modules": ["关系总览", "吸引轴", "摩擦轴", "成长建议"],
        "primary_cta": "路线图中",
        "output_route": "/reports/:id",
    },
]


def list_analysis_types() -> List[Dict[str, Any]]:
    return deepcopy(ANALYSIS_TYPES)


def get_analysis_type(key: str) -> Optional[Dict[str, Any]]:
    for item in ANALYSIS_TYPES:
        if item["key"] == key:
            return deepcopy(item)
    return None
