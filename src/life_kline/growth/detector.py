"""
detector.py — GrowthDetector：成长检测引擎

检测用户在不同时间点的成长状态变化。
遵循 PRD v1.0 的 Companion Memory 概念：
- 记录「你成长了什么」，不是「说了什么」
- 追踪 Theme 相关的心理状态变化
- 检测里程碑事件
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


# ============================================================================
# 数据类
# ============================================================================


@dataclass
class ThemeState:
    """
    某个时间点的主题状态快照。

    用于记录用户在某一时点的心理状态。
    """
    theme_key: str                          # theme key
    fear_level: float = 0.5                 # 恐惧/焦虑程度 0.0 ~ 1.0
    awareness_level: float = 0.5             # 觉察程度 0.0 ~ 1.0
    action_level: float = 0.0                # 行动程度 0.0 ~ 1.0
    narrative_summary: str = ""              # 状态描述
    evidence_summary: str = ""              # 证据摘要
    recorded_at: str = ""                   # ISO 时间戳

    def to_dict(self) -> dict[str, Any]:
        return {
            "theme_key": self.theme_key,
            "fear_level": self.fear_level,
            "awareness_level": self.awareness_level,
            "action_level": self.action_level,
            "narrative_summary": self.narrative_summary,
            "evidence_summary": self.evidence_summary,
            "recorded_at": self.recorded_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> ThemeState:
        return cls(**d)


@dataclass
class GrowthMilestone:
    """
    成长里程碑。

    记录用户在某个 Theme 上的重大成长转变。
    """
    id: str = ""                           # 唯一标识（自动生成）
    theme_key: str = ""                    # theme key
    from_state: str = ""                   # 变化前的状态描述
    to_state: str = ""                    # 变化后的状态描述
    change_type: str = ""                  # change type: fear_reduced / awareness_increased / action_taken
    description: str = ""                   # 自然语言描述
    evidence: list[str] = field(default_factory=list)  # 支持这个判断的证据列表
    confidence: float = 0.5                # 判断置信度 0.0 ~ 1.0
    detected_at: str = ""                   # ISO 时间戳

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:8]
        if not self.detected_at:
            self.detected_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "theme_key": self.theme_key,
            "from_state": self.from_state,
            "to_state": self.to_state,
            "change_type": self.change_type,
            "description": self.description,
            "evidence": self.evidence,
            "confidence": self.confidence,
            "detected_at": self.detected_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> GrowthMilestone:
        return cls(**d)


@dataclass
class GrowthTrajectory:
    """
    成长轨迹。

    按 Theme 组织的成长历史，包括多个里程碑。
    """
    theme_key: str                          # theme key
    theme_label: str = ""                   # theme label
    states: list[ThemeState] = field(default_factory=list)  # 状态历史
    milestones: list[GrowthMilestone] = field(default_factory=list)  # 里程碑
    current_narrative: str = ""            # AI 生成的当前叙事

    def to_dict(self) -> dict[str, Any]:
        return {
            "theme_key": self.theme_key,
            "theme_label": self.theme_label,
            "states": [s.to_dict() for s in self.states],
            "milestones": [m.to_dict() for m in self.milestones],
            "current_narrative": self.current_narrative,
        }

    @classmethod
    def from_dict(cls, d: dict) -> GrowthTrajectory:
        states = [ThemeState.from_dict(s) for s in d.get("states", [])]
        milestones = [GrowthMilestone.from_dict(m) for m in d.get("milestones", [])]
        return cls(
            theme_key=d.get("theme_key", ""),
            theme_label=d.get("theme_label", ""),
            states=states,
            milestones=milestones,
            current_narrative=d.get("current_narrative", ""),
        )


# ============================================================================
# 变化检测阈值
# ============================================================================

# Fear level 变化阈值
FEAR_CHANGE_THRESHOLD = 0.2
# Awareness 变化阈值
AWARENESS_CHANGE_THRESHOLD = 0.15
# Action 变化阈值
ACTION_CHANGE_THRESHOLD = 0.2


# ============================================================================
# Growth Detector
# ============================================================================

class GrowthDetector:
    """
    检测成长状态变化。

    使用方法：
        detector = GrowthDetector()
        milestone = detector.detect_change(old_state, new_state, theme_key, theme_label)
    """

    def detect_change(
        self,
        old_state: ThemeState | dict,
        new_state: ThemeState | dict,
        theme_key: str,
        theme_label: str = "",
    ) -> GrowthMilestone | None:
        """
        对比两个状态，检测是否有成长变化。

        Args:
            old_state: 旧状态
            new_state: 新状态
            theme_key: theme key
            theme_label: theme label（可选）

        Returns:
            GrowthMilestone 如果检测到变化，否则 None
        """
        # 统一转换为 dict
        old = old_state.to_dict() if hasattr(old_state, 'to_dict') else old_state
        new = new_state.to_dict() if hasattr(new_state, 'to_dict') else new_state

        # 检测 fear 下降
        old_fear = old.get("fear_level", 0.5)
        new_fear = new.get("fear_level", 0.5)
        if new_fear < old_fear - FEAR_CHANGE_THRESHOLD:
            return self._create_fear_milestone(old, new, theme_key, theme_label)

        # 检测 awareness 上升
        old_awareness = old.get("awareness_level", 0.5)
        new_awareness = new.get("awareness_level", 0.5)
        if new_awareness > old_awareness + AWARENESS_CHANGE_THRESHOLD:
            return self._create_awareness_milestone(old, new, theme_key, theme_label)

        # 检测 action 上升
        old_action = old.get("action_level", 0.0)
        new_action = new.get("action_level", 0.0)
        if new_action > old_action + ACTION_CHANGE_THRESHOLD:
            return self._create_action_milestone(old, new, theme_key, theme_label)

        return None

    def _create_fear_milestone(
        self,
        old: dict,
        new: dict,
        theme_key: str,
        theme_label: str,
    ) -> GrowthMilestone:
        """创建恐惧下降的里程碑"""
        old_fear = old.get("fear_level", 0.5)
        new_fear = new.get("fear_level", 0.5)
        decrease = old_fear - new_fear

        return GrowthMilestone(
            theme_key=theme_key,
            from_state=f"对「{theme_label}」的恐惧程度较高（约{old_fear:.0%}）",
            to_state=f"恐惧程度降低（约{new_fear:.0%}），下降{decrease:.0%}",
            change_type="fear_reduced",
            description=f"对「{theme_label}」的恐惧感减少，成长信号",
            evidence=[new.get("evidence_summary", "")],
            confidence=min(decrease * 2, 1.0),
        )

    def _create_awareness_milestone(
        self,
        old: dict,
        new: dict,
        theme_key: str,
        theme_label: str,
    ) -> GrowthMilestone:
        """创建觉察提升的里程碑"""
        old_awareness = old.get("awareness_level", 0.5)
        new_awareness = new.get("awareness_level", 0.5)
        increase = new_awareness - old_awareness

        return GrowthMilestone(
            theme_key=theme_key,
            from_state=f"对「{theme_label}」的觉察较少（约{old_awareness:.0%}）",
            to_state=f"觉察程度提升（约{new_awareness:.0%}），增加{increase:.0%}",
            change_type="awareness_increased",
            description=f"对「{theme_label}」的觉察增强，成长信号",
            evidence=[new.get("evidence_summary", "")],
            confidence=min(increase * 2, 1.0),
        )

    def _create_action_milestone(
        self,
        old: dict,
        new: dict,
        theme_key: str,
        theme_label: str,
    ) -> GrowthMilestone:
        """创建行动采取的里程碑"""
        old_action = old.get("action_level", 0.0)
        new_action = new.get("action_level", 0.0)
        increase = new_action - old_action

        return GrowthMilestone(
            theme_key=theme_key,
            from_state=f"对「{theme_label}」尚未采取行动",
            to_state=f"开始采取行动（程度从{old_action:.0%}提升至{new_action:.0%}）",
            change_type="action_taken",
            description=f"对「{theme_label}」开始采取行动，成长信号",
            evidence=[new.get("evidence_summary", "")],
            confidence=min(increase * 2, 1.0),
        )

    def build_trajectory(
        self,
        theme_key: str,
        theme_label: str,
        states: list[ThemeState],
        milestones: list[GrowthMilestone],
    ) -> GrowthTrajectory:
        """
        从状态历史构建成长轨迹。

        Args:
            theme_key: theme key
            theme_label: theme label
            states: 状态历史列表（按时间排序）
            milestones: 里程碑列表

        Returns:
            GrowthTrajectory
        """
        # 生成当前叙事
        current_narrative = self._generate_narrative(
            theme_key, theme_label, states, milestones
        )

        return GrowthTrajectory(
            theme_key=theme_key,
            theme_label=theme_label,
            states=states,
            milestones=milestones,
            current_narrative=current_narrative,
        )

    def _generate_narrative(
        self,
        theme_key: str,
        theme_label: str,
        states: list[ThemeState],
        milestones: list[GrowthMilestone],
    ) -> str:
        """生成成长轨迹叙事"""
        if not states:
            return f"关于「{theme_label}」，目前没有足够的追踪数据。"

        latest = states[-1]
        latest_date = latest.recorded_at[:10] if latest.recorded_at else "最近"

        # 统计里程碑
        if milestones:
            milestone_count = len(milestones)
            latest_milestone = milestones[-1]
            return (
                f"关于「{theme_label}」，你已经在{latest_date}左右取得了"
                f"{milestone_count}个成长里程碑。"
                f"最近的一个是：{latest_milestone.description}"
            )

        # 无里程碑但有状态
        return (
            f"关于「{theme_label}」，我们在{latest_date}追踪到你的状态。"
            f"恐惧程度约{latest.fear_level:.0%}，觉察程度约{latest.awareness_level:.0%}。"
        )


# ============================================================================
# 便捷函数
# ============================================================================

def detect_growth_change(
    old_state: ThemeState,
    new_state: ThemeState,
    theme_key: str,
    theme_label: str = "",
) -> GrowthMilestone | None:
    """便捷函数：检测成长变化"""
    detector = GrowthDetector()
    return detector.detect_change(old_state, new_state, theme_key, theme_label)
