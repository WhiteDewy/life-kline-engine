"""
growth_tracker.py — 用户成长追踪系统

追踪用户与12星座角色的互动，形成长期成长画像。
存储为 JSON 文件，与现有报告存储模式一致。

追踪维度：
- 对话历史：用户和每个角色聊了什么
- 话题偏好：用户更关心哪些领域
- 亲密度：用户和每个角色的互动频率和深度
- 里程碑：重要互动节点
- 情感轨迹：用户情绪状态变化
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..constants import Sign


# ═══════════════════════════════════════════════════════════════
# 数据类
# ═══════════════════════════════════════════════════════════════

@dataclass
class ConversationTurn:
    """一次对话记录"""
    timestamp: str                            # ISO 时间戳
    sign: str                                 # Sign.value
    topic: str                                # 领域 key
    user_message: str                         # 用户消息（截断至200字）
    character_response: str                   # 角色回复（截断至200字）
    emotional_context: str = "general"        # seeking_advice / venting / celebrating / general

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "sign": self.sign,
            "topic": self.topic,
            "user_message": self.user_message[:200],
            "character_response": self.character_response[:200],
            "emotional_context": self.emotional_context,
        }

    @classmethod
    def from_dict(cls, d: dict) -> ConversationTurn:
        return cls(**d)


@dataclass
class DailyVisit:
    """一次每日访问记录"""
    date: str                                 # ISO 日期
    featured_signs: list[str]                 # 当日登场角色
    activation_scores: dict[str, float]       # 激活度

    def to_dict(self) -> dict[str, Any]:
        return {
            "date": self.date,
            "featured_signs": self.featured_signs,
            "activation_scores": self.activation_scores,
        }

    @classmethod
    def from_dict(cls, d: dict) -> DailyVisit:
        return cls(**d)


@dataclass
class Milestone:
    """成长里程碑"""
    milestone_type: str                       # tenth_conversation / first_daily / topic_deep_dive / streak_7
    sign: str                                 # 关联角色
    achieved_at: str                          # ISO 时间戳
    description: str                          # 里程碑描述

    def to_dict(self) -> dict[str, Any]:
        return {
            "milestone_type": self.milestone_type,
            "sign": self.sign,
            "achieved_at": self.achieved_at,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, d: dict) -> Milestone:
        return cls(**d)


@dataclass
class GrowthSummary:
    """成长概况"""
    total_conversations: int = 0
    most_engaged_character: str = ""          # 互动最多的角色名
    favorite_topics: dict[str, int] = field(default_factory=dict)  # 话题 → 对话次数
    streak_days: int = 0                      # 连续访问天数
    character_affinity: dict[str, float] = field(default_factory=dict)  # sign → 亲密度 0-10
    milestones_achieved: int = 0
    first_interaction_date: str = ""
    last_interaction_date: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_conversations": self.total_conversations,
            "most_engaged_character": self.most_engaged_character,
            "favorite_topics": self.favorite_topics,
            "streak_days": self.streak_days,
            "character_affinity": self.character_affinity,
            "milestones_achieved": self.milestones_achieved,
            "first_interaction_date": self.first_interaction_date,
            "last_interaction_date": self.last_interaction_date,
        }


# ═══════════════════════════════════════════════════════════════
# 成长追踪器
# ═══════════════════════════════════════════════════════════════

class GrowthTracker:
    """追踪用户与角色系统的互动成长。

    存储位置：backend/data/{report_id}_growth.json
    """

    def __init__(self, report_id: str, data_dir: str | None = None):
        self.report_id = report_id
        self.data_dir = data_dir or self._default_data_dir()

        # 状态
        self.conversations: list[ConversationTurn] = []
        self.daily_visits: list[DailyVisit] = []
        self.milestones: list[Milestone] = []

        self._load_state()

    @staticmethod
    def _default_data_dir() -> str:
        """默认数据目录"""
        # 相对于项目根目录
        base = Path(__file__).resolve().parents[3]  # src/life_kline/growth → project root
        return str(base / "backend" / "data")

    @property
    def _file_path(self) -> str:
        return os.path.join(self.data_dir, f"{self.report_id}_growth.json")

    # ── 记录 ──────────────────────────────────────────────

    def record_conversation(
        self,
        sign: Sign,
        topic: str,
        user_message: str,
        character_response: str,
        emotional_context: str = "general",
    ) -> None:
        """记录一次对话"""
        turn = ConversationTurn(
            timestamp=datetime.now(timezone.utc).isoformat(),
            sign=sign.value,
            topic=topic,
            user_message=user_message,
            character_response=character_response,
            emotional_context=emotional_context,
        )
        self.conversations.append(turn)

        # 检查里程碑
        sign_conversations = [c for c in self.conversations if c.sign == sign.value]
        count = len(sign_conversations)

        if count == 1:
            self._add_milestone("first_conversation", sign.value, f"第一次和{sign.value}角色对话")
        elif count == 10:
            self._add_milestone("tenth_conversation", sign.value, f"和{sign.value}角色对话达到10次")
        elif count == 50:
            self._add_milestone("deep_bond", sign.value, f"和{sign.value}角色建立了深厚的连接")

        # 话题深度
        topic_conversations = [
            c for c in self.conversations
            if c.sign == sign.value and c.topic == topic
        ]
        if len(topic_conversations) == 5:
            self._add_milestone(
                "topic_deep_dive", sign.value,
                f"和{sign.value}角色深入探讨了{topic}话题（5次）",
            )

        self._save_state()

    def record_daily_visit(self, activation_scores: dict[str, float], featured: list[str]) -> None:
        """记录一次每日访问"""
        today = datetime.now(timezone.utc).date().isoformat()
        visit = DailyVisit(
            date=today,
            featured_signs=featured,
            activation_scores=activation_scores,
        )
        self.daily_visits.append(visit)

        # 检查连续访问
        streak = self._calculate_streak()
        if streak == 1:
            self._add_milestone("first_daily", "", "第一次打开每日简报")
        elif streak == 7:
            self._add_milestone("streak_7", "", "连续7天查看每日简报")

        self._save_state()

    def _add_milestone(self, mtype: str, sign: str, description: str) -> None:
        """添加里程碑（去重）"""
        # 检查是否已存在
        for m in self.milestones:
            if m.milestone_type == mtype and m.sign == sign:
                return
        self.milestones.append(Milestone(
            milestone_type=mtype,
            sign=sign,
            achieved_at=datetime.now(timezone.utc).isoformat(),
            description=description,
        ))

    # ── 查询 ──────────────────────────────────────────────

    def get_conversation_history(self, sign: Sign | None = None, limit: int = 50) -> list[ConversationTurn]:
        """获取对话历史"""
        if sign:
            filtered = [c for c in self.conversations if c.sign == sign.value]
        else:
            filtered = list(self.conversations)
        return filtered[-limit:]

    def get_character_affinity(self) -> dict[str, float]:
        """计算用户与每个角色的亲密度 (0-10)"""
        affinity: dict[str, float] = {s.value: 0.0 for s in Sign}

        for conv in self.conversations:
            current = affinity.get(conv.sign, 0.0)

            # 基础分
            increment = 0.2

            # 深度对话加分
            if conv.emotional_context in ("seeking_advice", "venting"):
                increment = 0.5

            affinity[conv.sign] = min(current + increment, 10.0)

        # 衰减：每周未互动 -0.05
        # (简化处理：只计算不衰减，亲和度只增不减但增速递减)

        return {k: round(v, 1) for k, v in affinity.items()}

    def get_topic_engagement(self) -> dict[str, int]:
        """话题参与度统计"""
        topics: dict[str, int] = {}
        for conv in self.conversations:
            topics[conv.topic] = topics.get(conv.topic, 0) + 1
        return dict(sorted(topics.items(), key=lambda x: x[1], reverse=True))

    def get_emotional_arc(self, limit: int = 30) -> list[dict[str, Any]]:
        """获取最近的情绪轨迹"""
        recent = self.conversations[-limit:]
        return [
            {
                "date": c.timestamp[:10],
                "sign": c.sign,
                "context": c.emotional_context,
            }
            for c in recent
        ]

    def _calculate_streak(self) -> int:
        """计算连续每日访问天数"""
        if not self.daily_visits:
            return 0

        dates = sorted(set(v.date for v in self.daily_visits), reverse=True)
        if not dates:
            return 0

        from datetime import date, timedelta
        today = date.today()
        streak = 0
        expected = today

        for d_str in dates:
            d = date.fromisoformat(d_str)
            if d == expected:
                streak += 1
                expected = d - timedelta(days=1)
            elif d < expected:
                break

        return streak

    def get_growth_summary(self) -> GrowthSummary:
        """获取成长概况"""
        affinity = self.get_character_affinity()
        topics = self.get_topic_engagement()

        # 最活跃的角色
        sign_counts: dict[str, int] = {}
        for c in self.conversations:
            sign_counts[c.sign] = sign_counts.get(c.sign, 0) + 1
        most_engaged = max(sign_counts, key=sign_counts.get) if sign_counts else ""

        # 首末日期
        first_date = self.conversations[0].timestamp[:10] if self.conversations else ""
        last_date = self.conversations[-1].timestamp[:10] if self.conversations else ""

        return GrowthSummary(
            total_conversations=len(self.conversations),
            most_engaged_character=most_engaged,
            favorite_topics=topics,
            streak_days=self._calculate_streak(),
            character_affinity=affinity,
            milestones_achieved=len(self.milestones),
            first_interaction_date=first_date,
            last_interaction_date=last_date,
        )

    # ── 持久化 ────────────────────────────────────────────

    def _load_state(self) -> None:
        """从 JSON 文件加载状态"""
        if not os.path.exists(self._file_path):
            return

        try:
            with open(self._file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.conversations = [
                ConversationTurn.from_dict(c)
                for c in data.get("conversations", [])
            ]
            self.daily_visits = [
                DailyVisit.from_dict(v)
                for v in data.get("daily_visits", [])
            ]
            self.milestones = [
                Milestone.from_dict(m)
                for m in data.get("milestones", [])
            ]
        except (json.JSONDecodeError, KeyError):
            self.conversations = []
            self.daily_visits = []
            self.milestones = []

    def _save_state(self) -> None:
        """保存状态到 JSON 文件"""
        os.makedirs(self.data_dir, exist_ok=True)

        data = {
            "report_id": self.report_id,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "conversations": [c.to_dict() for c in self.conversations],
            "daily_visits": [v.to_dict() for v in self.daily_visits],
            "milestones": [m.to_dict() for m in self.milestones],
            "summary": self.get_growth_summary().to_dict(),
        }

        # 原子写入
        tmp_path = self._file_path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, self._file_path)

    @classmethod
    def load(cls, report_id: str, data_dir: str | None = None) -> GrowthTracker:
        """加载或创建成长追踪器"""
        return cls(report_id, data_dir)
