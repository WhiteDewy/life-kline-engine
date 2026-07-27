"""
council/ — 星灵议会引擎（Council Engine）

ACI 系统的第五层：多行星视角协作系统。

将 llm_client.py 中的 build_council_system_prompt_v2() 升级为独立引擎模块。

模块组成：
    council_types.py  — CouncilMember, CouncilSession, CouncilRelation 数据结构
    engine.py         — CouncilEngine 多行星视角协作引擎
    prompts.py        — LLM prompt 模板（重构自 llm_client.py）
"""

from .council_types import (
    CouncilRelation,
    CouncilMember,
    CouncilSession,
)
from .engine import CouncilEngine

__all__ = [
    "CouncilRelation",
    "CouncilMember",
    "CouncilSession",
    "CouncilEngine",
]
