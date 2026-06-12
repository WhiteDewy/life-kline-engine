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
        "tagline": "识别人格结构、驱动力和长期人生命题。",
        "description": (
            "围绕上升、命主星、重点宫位和关键相位，建立一个长期稳定的本命结构画像。"
        ),
        "category": "structure",
        "status": "planned",
        "subjects_count": 1,
        "required_inputs": ["birth_time", "lat", "lon", "timezone"],
        "engines": ["natal_core"],
        "modules": ["natal_summary", "house_focus", "aspect_field", "life_strategy"],
        "primary_cta": "即将开放",
        "output_route": "/reports/:id",
    },
    {
        "key": "phase_navigation",
        "title": "阶段导航",
        "tagline": "用本命结构 + 法达阶段理解你当下的主旋律。",
        "description": (
            "当前版本的核心可用分析。先用本命结构定义底盘，再用法达主运与子运识别人生阶段、"
            "机会窗口和风险点。"
        ),
        "category": "timing",
        "status": "active",
        "subjects_count": 1,
        "required_inputs": ["birth_time", "lat", "lon", "timezone"],
        "engines": ["natal_core", "firdaria"],
        "modules": [
            "hero_overview",
            "natal_chart",
            "natal_blueprint",
            "current_phase",
            "life_model",
            "timeline_validation",
            "life_rhythm_chart",
            "domain_projection",
            "firdaria_table",
        ],
        "primary_cta": "进入体验",
        "output_route": "/reports/:id",
    },
    {
        "key": "annual_profection",
        "title": "年度节奏",
        "tagline": "把每个年龄年的主轴和重点议题拆出来。",
        "description": (
            "以后将通过小限、年度主星与主题宫位，判断某一年应把火力集中在哪里。"
        ),
        "category": "timing",
        "status": "planned",
        "subjects_count": 1,
        "required_inputs": ["birth_time", "lat", "lon", "timezone"],
        "engines": ["natal_core", "profection"],
        "modules": ["annual_focus", "lord_cycle", "topic_emphasis"],
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
        "modules": ["inner_timing", "progressed_highlights", "phase_brief"],
        "primary_cta": "路线图中",
        "output_route": "/reports/:id",
    },
    {
        "key": "synastry",
        "title": "关系合盘",
        "tagline": "分析两个人的吸引、磨合与长期结构。",
        "description": (
            "后续会支持双人出生资料输入，从吸引机制、冲突模式、关系边界和长期协同来解释关系。"
        ),
        "category": "relationship",
        "status": "planned",
        "subjects_count": 2,
        "required_inputs": ["birth_time", "lat", "lon", "timezone"],
        "engines": ["natal_core", "synastry"],
        "modules": ["compatibility_overview", "attraction_axis", "friction_axis", "growth_advice"],
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
