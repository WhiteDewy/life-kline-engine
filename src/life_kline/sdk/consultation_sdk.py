"""
consultation_sdk.py — 咨询 SDK

封装咨询引擎能力，提供对话式咨询接口。

用法：
    sdk = ConsultationSDK()
    session = sdk.start_session(report_id, planet="MOON")
    response = sdk.send_message(session.id, "我最近工作很累")
    insights = sdk.get_growth_insights(session.id)
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from ..companion import (
    CompanionContext,
    CompanionResponse,
    PlanetCompanion,
    CompanionGrowthTracker,
)
from ..memory import MemoryManager, load_memory
from ..engine_astrologer import EngineAstrologer, build_engine_response
from ..constants import Planet


# ============================================================================
# 数据类
# ============================================================================

@dataclass
class ConsultationSession:
    """咨询会话"""
    id: str
    report_id: str
    planet: Planet
    created_at: str = ""
    turn_count: int = 0
    memory: Optional[MemoryManager] = None

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


@dataclass
class ConsultationResponse:
    """咨询回复"""
    text: str
    planet: str
    emotional_state: str
    is_growth_insight: bool = False
    growth_insight_text: str = ""
    suggested_topic: str = ""
    evidence: list[str] = field(default_factory=list)
    session_id: str = ""


# ============================================================================
# 咨询 SDK
# ============================================================================

class ConsultationSDK:
    """
    咨询 SDK。

    封装咨询引擎，提供：
    - 会话管理
    - 消息处理
    - 成长追踪
    """

    def __init__(self, report_data: dict[str, Any] | None = None):
        """
        Args:
            report_data: 可选的星盘报告数据，用于个性化咨询
        """
        self._report_data = report_data or {}
        self._sessions: dict[str, ConsultationSession] = {}
        self._companions: dict[Planet, PlanetCompanion] = {}

    def start_session(
        self,
        report_id: str,
        planet: str | Planet = "MOON",
        session_id: str | None = None,
    ) -> ConsultationSession:
        """
        开启新的咨询会话。

        Args:
            report_id: 报告 ID（用于加载记忆）
            planet: 行星（默认为 "MOON"）
            session_id: 可选的会话 ID

        Returns:
            ConsultationSession 实例
        """
        # 解析行星
        if isinstance(planet, str):
            try:
                planet_enum = Planet(planet.upper())
            except ValueError:
                planet_enum = Planet.MOON
        else:
            planet_enum = planet

        sid = session_id or str(uuid.uuid4())[:12]

        # 加载记忆
        memory = load_memory(report_id)

        session = ConsultationSession(
            id=sid,
            report_id=report_id,
            planet=planet_enum,
            memory=memory,
        )

        self._sessions[sid] = session

        # 获取或创建伴侣
        if planet_enum not in self._companions:
            self._companions[planet_enum] = PlanetCompanion(
                planet=planet_enum,
                report_data=self._report_data,
            )

        return session

    def send_message(
        self,
        session_id: str,
        message: str,
        topic_hint: str = "",
    ) -> ConsultationResponse:
        """
        发送消息并获取回复。

        Args:
            session_id: 会话 ID
            message: 用户消息
            topic_hint: 可选的话题提示

        Returns:
            ConsultationResponse 实例
        """
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        # 更新对话深度
        session.turn_count += 1

        # 获取伴侣
        companion = self._companions.get(session.planet)
        if not companion:
            companion = PlanetCompanion(
                planet=session.planet,
                report_data=self._report_data,
            )
            self._companions[session.planet] = companion

        # 构建上下文
        memory_context = {}
        if session.memory:
            memory_context = session.memory.get_memory_context_for_agent()

        # 检测情绪（简化版）
        emotional_state = self._detect_emotional_state(message)

        context = CompanionContext(
            message=message,
            memory_context=memory_context,
            emotional_state=emotional_state,
            turn_count=session.turn_count,
            recent_topics=memory_context.get("recent_topics", []),
        )

        # 获取伴侣回复
        response = companion.respond(context)

        # 如果有引擎数据，也可以用引擎增强
        if self._report_data:
            engine_response = build_engine_response(
                report_data=self._report_data,
                report_id=session.report_id,
                planet=session.planet.value,
                user_message=message,
                topic_hint=topic_hint,
            )
            # 优先使用伴侣的回复，但可以合并引擎的证据
            if engine_response.evidence and not response.evidence:
                response.evidence = engine_response.evidence

        return ConsultationResponse(
            text=response.text,
            planet=session.planet.value,
            emotional_state=response.emotional_state,
            is_growth_insight=response.is_growth_insight,
            growth_insight_text=response.growth_insight_text,
            suggested_topic=response.suggested_topic,
            evidence=response.evidence,
            session_id=session_id,
        )

    def get_growth_insights(
        self,
        session_id: str,
        theme_key: str = "",
    ) -> list[dict[str, str]]:
        """
        获取成长洞察。

        Args:
            session_id: 会话 ID
            theme_key: 可选的特定 theme key

        Returns:
            成长洞察列表
        """
        session = self._sessions.get(session_id)
        if not session or not session.memory:
            return []

        if theme_key:
            insight = session.memory.get_theme_growth_narrative(theme_key)
            if insight:
                return [{"theme_key": theme_key, "insight": insight}]
            return []

        # 返回所有成长洞察
        memory_context = session.memory.get_memory_context_for_agent()
        return memory_context.get("growth_insights", [])

    def update_theme_state(
        self,
        session_id: str,
        theme_key: str,
        fear_level: float | None = None,
        awareness_level: float | None = None,
        action_level: float | None = None,
        narrative: str = "",
    ) -> None:
        """
        更新主题状态。

        Args:
            session_id: 会话 ID
            theme_key: theme key
            fear_level: 恐惧程度 (0.0 ~ 1.0)
            awareness_level: 觉察程度 (0.0 ~ 1.0)
            action_level: 行动程度 (0.0 ~ 1.0)
            narrative: 状态描述
        """
        session = self._sessions.get(session_id)
        if not session or not session.memory:
            return

        session.memory.update_theme_state(
            theme_key=theme_key,
            fear_level=fear_level,
            awareness_level=awareness_level,
            action_level=action_level,
            narrative=narrative,
        )

    def get_session(self, session_id: str) -> ConsultationSession | None:
        """
        获取会话。

        Args:
            session_id: 会话 ID

        Returns:
            ConsultationSession 或 None
        """
        return self._sessions.get(session_id)

    def list_sessions(self) -> list[ConsultationSession]:
        """
        列出所有会话。

        Returns:
            会话列表
        """
        return list(self._sessions.values())

    def _detect_emotional_state(self, message: str) -> str:
        """检测情绪状态（简化版）"""
        message_lower = message.lower()

        if any(kw in message_lower for kw in ["焦虑", "担心", "怕", "紧张", "压力", "烦"]):
            return "anxious"
        if any(kw in message_lower for kw in ["迷茫", "不知道", "不确定", "纠结", "怎么办"]):
            return "confused"
        if any(kw in message_lower for kw in ["为什么", "难受", "不公平", "太难了"]):
            return "frustrated"
        if any(kw in message_lower for kw in ["想试试", "期待", "希望", "打算"]):
            return "hopeful"

        return "curious"


# ============================================================================
# 便捷函数
# ============================================================================

def start_consultation(
    report_id: str,
    planet: str = "MOON",
    report_data: dict[str, Any] | None = None,
) -> ConsultationSession:
    """
    便捷函数：开启咨询会话。

    Args:
        report_id: 报告 ID
        planet: 行星
        report_data: 可选的报告数据

    Returns:
        ConsultationSession
    """
    sdk = ConsultationSDK(report_data)
    return sdk.start_session(report_id, planet)


def send_consultation_message(
    session_id: str,
    message: str,
    session: ConsultationSession | None = None,
) -> ConsultationResponse:
    """
    便捷函数：发送咨询消息。

    Args:
        session_id: 会话 ID
        message: 用户消息
        session: 可选的会话对象

    Returns:
        ConsultationResponse
    """
    if not session:
        raise ValueError("session is required")

    sdk = ConsultationSDK()
    sdk._sessions[session_id] = session
    return sdk.send_message(session_id, message)
