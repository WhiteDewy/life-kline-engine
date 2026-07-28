"""
memory.py — 用户记忆管理器

为星灵对话提供长期记忆能力：
- 对话历史摘要（recent_topics）
- 成长里程碑（recent_milestones）
- 主题状态追踪（theme_states）
- 成长叙事（growth_insights）

数据存储：growth_conversations / growth_milestones 表（通过 dao 访问）
"""
from __future__ import annotations

import json as _json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

# ---------------------------------------------------------------------------
# 数据结构
# ---------------------------------------------------------------------------


@dataclass
class ThemeState:
    """主题状态"""
    fear_level: float = 0.5        # 0.0~1.0
    awareness_level: float = 0.5   # 0.0~1.0
    action_level: float = 0.0      # 0.0~1.0
    narrative: str = ""            # 最新状态描述
    updated_at: str = ""           # ISO 时间戳

    def to_dict(self) -> dict[str, Any]:
        return {
            "fear_level": self.fear_level,
            "awareness_level": self.awareness_level,
            "action_level": self.action_level,
            "narrative": self.narrative,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> ThemeState:
        return cls(
            fear_level=float(d.get("fear_level", 0.5)),
            awareness_level=float(d.get("awareness_level", 0.5)),
            action_level=float(d.get("action_level", 0.0)),
            narrative=str(d.get("narrative", "")),
            updated_at=str(d.get("updated_at", "")),
        )


# ---------------------------------------------------------------------------
# MemoryManager
# ---------------------------------------------------------------------------

class MemoryManager:
    """
    管理单个报告的用户记忆。

    对话记忆来自 growth_conversations 表；
    里程碑来自 growth_milestones 表；
    主题状态存于内存（首次从数据库恢复，之后与 dao 同步）。
    """

    def __init__(self, report_id: str):
        self.report_id = report_id
        self._theme_states: dict[str, ThemeState] = {}
        self._recent_topics: list[str] = []
        self._milestones: list[dict] = []
        self._loaded = False

    # ------------------------------------------------------------------
    # 加载
    # ------------------------------------------------------------------

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        self._loaded = True

        # 从数据库恢复主题状态（如果有的话）
        self._load_from_db()

    def _load_from_db(self) -> None:
        """从 dao 加载对话历史和里程碑，构建 recent_topics。"""
        try:
            from ..backend.dao import (
                list_growth_conversations,
                list_growth_milestones,
            )
            convos = list_growth_conversations(self.report_id, limit=100)
            milestones = list_growth_milestones(self.report_id)

            self._milestones = milestones

            # 从对话中提取最近话题
            topics: list[str] = []
            for c in convos:
                topic = c.get("topic", "").strip()
                if topic and topic not in topics:
                    topics.append(topic)
            self._recent_topics = topics[-10:]  # 保留最近 10 个

        except Exception:
            self._recent_topics = []
            self._milestones = []

    # ------------------------------------------------------------------
    # 公开 API
    # ------------------------------------------------------------------

    def get_memory_context_for_agent(self) -> dict[str, Any]:
        """
        返回供 LLM Agent 使用的记忆上下文。

        Returns:
            {
                recent_topics: list[str],        # 最近聊过的话题
                recent_milestones: list[dict],   # 最近的成长里程碑
                growth_insights: list[dict],     # 各主题的成长洞察
            }
        """
        self._ensure_loaded()

        # 构建 growth_insights
        growth_insights = []
        for theme_key, state in self._theme_states.items():
            narrative = self.get_theme_growth_narrative(theme_key)
            if narrative:
                growth_insights.append({
                    "theme_key": theme_key,
                    "insight": narrative,
                })

        return {
            "recent_topics": self._recent_topics.copy(),
            "recent_milestones": self._milestones.copy(),
            "growth_insights": growth_insights,
        }

    def get_theme_growth_narrative(self, theme_key: str) -> str:
        """
        返回某个主题的成长叙事描述。

        基于当前状态生成一句自然语言描述。
        """
        self._ensure_loaded()
        state = self._theme_states.get(theme_key)
        if not state:
            return ""

        # 生成叙事（简单规则）
        if state.action_level >= 0.7:
            return f"你在「{theme_key}」主题上已经采取了行动，保持觉察继续前行。"
        elif state.awareness_level >= 0.7:
            return f"你对「{theme_key}」有较高的觉察，正在酝酿下一步行动。"
        elif state.fear_level >= 0.7:
            return f"「{theme_key}」让你感到不安，建议给自己更多耐心。"
        else:
            return f"「{theme_key}」对你来说是一个正在探索的主题。"

    def update_theme_state(
        self,
        theme_key: str,
        fear_level: float | None = None,
        awareness_level: float | None = None,
        action_level: float | None = None,
        narrative: str = "",
    ) -> None:
        """更新某个主题的状态（写入内存，下次 save 时持久化）。"""
        self._ensure_loaded()

        state = self._theme_states.get(theme_key)
        if state is None:
            state = ThemeState()
            self._theme_states[theme_key] = state

        if fear_level is not None:
            state.fear_level = max(0.0, min(1.0, fear_level))
        if awareness_level is not None:
            state.awareness_level = max(0.0, min(1.0, awareness_level))
        if action_level is not None:
            state.action_level = max(0.0, min(1.0, action_level))
        if narrative:
            state.narrative = narrative
        state.updated_at = datetime.now().isoformat()

        # TODO: 异步写入数据库（growth_milestones）
        try:
            from ..backend.dao import insert_growth_milestone
            insert_growth_milestone(
                report_id=self.report_id,
                milestone_type=f"theme_update_{theme_key}",
                sign=theme_key,
                description=state.narrative or self.get_theme_growth_narrative(theme_key),
            )
        except Exception:
            pass

    def add_topic(self, topic: str) -> None:
        """记录一个新话题到记忆。"""
        self._ensure_loaded()
        if topic and topic not in self._recent_topics:
            self._recent_topics.append(topic)
            self._recent_topics = self._recent_topics[-20:]

    def add_conversation(
        self,
        sign: str,
        topic: str,
        user_message: str,
        character_response: str,
        emotional_context: str = "general",
        user_id: str = "",
    ) -> None:
        """记录一段对话到数据库。"""
        try:
            from ..backend.dao import insert_growth_conversation
            insert_growth_conversation(
                report_id=self.report_id,
                user_id=user_id,
                sign=sign,
                topic=topic,
                user_message=user_message,
                character_response=character_response,
                emotional_context=emotional_context,
            )
            self.add_topic(topic)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# 工厂函数
# ---------------------------------------------------------------------------

# 进程内缓存：report_id -> MemoryManager 实例
_memory_cache: dict[str, MemoryManager] = {}


def load_memory(report_id: str) -> MemoryManager:
    """
    加载或创建一个 MemoryManager 实例。

    同一 report_id 在同一进程内复用实例。
    """
    if report_id not in _memory_cache:
        _memory_cache[report_id] = MemoryManager(report_id)
    return _memory_cache[report_id]
