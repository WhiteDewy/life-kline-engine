"""
council_types.py — 星灵议会核心数据类

定义 CouncilMember、CouncilSession、CouncilRelation 等核心数据结构。
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any
from enum import Enum


# ============================================================================
# 议会关系类型
# ============================================================================


class CouncilRelation(str, Enum):
    """行星在议会中的关系类型"""
    UNANIMOUS = "unanimous"           # 一致
    TENSION = "tension"               # 紧张
    COMPLEMENTARY = "complementary"   # 互补


# ============================================================================
# 行星发言风格定义
# ============================================================================

# PRD 第835行定义的行星发言风格
COUNCIL_PLANETS = ["SUN", "MOON", "MARS", "VENUS", "SATURN"]

COUNCIL_SPEAKING_STYLES: dict[str, dict[str, str]] = {
    "SUN": {
        "style": "身份目的型",
        "tone": "有力量感、直接",
        "focus": "身份认同、人生方向、自我实现",
    },
    "MOON": {
        "style": "情感感受型",
        "tone": "温柔、倾听",
        "focus": "情绪感受、安全感、内心需求",
    },
    "MARS": {
        "style": "行动驱动型",
        "tone": "直接、有力量感",
        "focus": "行动力、竞争、欲望驱动",
    },
    "VENUS": {
        "style": "关系价值型",
        "tone": "温和、关系导向",
        "focus": "人际关系、价值观、美与和谐",
    },
    "SATURN": {
        "style": "结构现实型",
        "tone": "谨慎、结构化",
        "focus": "责任、纪律、长期规划",
    },
}


# ============================================================================
# Council Member — 议会成员
# ============================================================================


@dataclass
class CouncilMember:
    """
    议会成员——单一行星视角。

    包含该行星的完整画像及其在当前议题下的发言内容。
    """
    planet: str                           # 行星名：SUN, MOON, MARS, VENUS, SATURN
    name_zh: str                         # 中文名：太阳、月亮、火星、金星、土星
    archetype_zh: str                     # 原型标签：如「主角」「情感」「欲望」
    sign_house: str                       # 落座落宫：「天蝎座第8宫」
    dignity_label: str                    # 尊贵状态：「庙旺」「失势」等
    speaking_style: str                   # 发言风格：如「身份目的型」
    speaking_tone: str                    # 语气：如「有力量感、直接」
    core_view: str = ""                   # 关于当前议题的核心观点
    contribution: str = ""                 # 该视角的贡献
    limitation: str = ""                  # 该视角的局限
    statement: str = ""                    # 最终生成的发言内容

    def to_dict(self) -> dict[str, Any]:
        return {
            "planet": self.planet,
            "name_zh": self.name_zh,
            "archetype_zh": self.archetype_zh,
            "sign_house": self.sign_house,
            "dignity_label": self.dignity_label,
            "speaking_style": self.speaking_style,
            "speaking_tone": self.speaking_tone,
            "core_view": self.core_view,
            "contribution": self.contribution,
            "limitation": self.limitation,
            "statement": self.statement,
        }


# ============================================================================
# Council Session — 议会会话
# ============================================================================


@dataclass
class CouncilSession:
    """
    一次完整的议会对话。

    包含所有成员、会话内容、整合结果。
    """
    session_id: str
    topic: str                            # 议会讨论的主题/问题
    members: list[CouncilMember]           # 议会成员列表
    member_statements: dict[str, str] = field(default_factory=dict)  # planet -> statement
    synthesis: str = ""                   # 各行星观点的整合描述
    conclusion: str = ""                  # 最终统一建议/觉察
    relation_type: CouncilRelation = CouncilRelation.COMPLEMENTARY  # 行星间关系

    def __post_init__(self):
        if not self.session_id:
            self.session_id = str(uuid.uuid4())[:12]

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "topic": self.topic,
            "members": [m.to_dict() for m in self.members],
            "member_statements": self.member_statements,
            "synthesis": self.synthesis,
            "conclusion": self.conclusion,
            "relation_type": self.relation_type.value,
        }

    @property
    def participating_planets(self) -> list[str]:
        """获取参与的行星列表"""
        return [m.planet for m in self.members]

    def get_member(self, planet: str) -> CouncilMember | None:
        """获取指定行星的成员信息"""
        for m in self.members:
            if m.planet == planet:
                return m
        return None
