"""
用户成长追踪系统

记录用户与角色的互动历史、话题偏好、情感轨迹。
"""

from .growth_tracker import GrowthTracker
from .detector import GrowthDetector, ThemeState, GrowthMilestone, GrowthTrajectory
from .signal_analyzer import GrowthSignalAnalyzer, GrowthSignals, analyze_growth_signals

__all__ = [
    "GrowthTracker",
    "GrowthDetector",
    "ThemeState",
    "GrowthMilestone",
    "GrowthTrajectory",
    "GrowthSignalAnalyzer",
    "GrowthSignals",
    "analyze_growth_signals",
]
