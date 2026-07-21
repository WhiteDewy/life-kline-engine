"""
diary_engine.py — 星灵日记引擎

基于用户对话上下文生成星灵日记条目，支持情绪关键词提取、
模板化条目生成和 JSON 文件存储。
"""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Optional

from .constants import Planet
from .service import PLANET_LABELS


# ============================================================================
# 情绪关键词库
# ============================================================================

EMOTIONAL_KEYWORDS: list[str] = [
    "委屈", "不甘", "期待", "害怕", "勇敢", "迷茫", "坚定",
    "温暖", "孤独", "渴望", "释然", "困惑", "感动", "疲惫", "充实",
]

# 情绪 → emoji 映射
MOOD_EMOJI_MAP: dict[str, str] = {
    "委屈": "😞", "不甘": "😤", "期待": "🥰", "害怕": "😨",
    "勇敢": "💪", "迷茫": "😶", "坚定": "🔥", "温暖": "☀️",
    "孤独": "💔", "渴望": "🌟", "释然": "😌", "困惑": "🤔",
    "感动": "🥹", "疲惫": "😮‍💨", "充实": "✨",
}

# 星灵语境模版
SPIRIT_TEMPLATES: dict[str, str] = {
    "SUN": "今天{planet_label}的能量让你感受到了{keywords}。你{action}。太阳提醒你：你本身就是光，不需要借别人的光才能被看见。",
    "MOON": "今天{planet_label}的能量让你的情绪泛起{keywords}的涟漪。你{action}。月亮想对你说：所有的感受都值得被接纳，包括那些你不愿承认的。",
    "MERCURY": "今天{planet_label}的能量让你对{keywords}有了新的思考。你{action}。水星提醒你：有时候最好的答案不在思考中，而在停下来倾听的那一刻。",
    "VENUS": "今天{planet_label}的能量让你体会到{keywords}的滋味。你{action}。金星想告诉你：你值得被好好对待，先从如何对待自己开始。",
    "MARS": "今天{planet_label}的能量让你感到{keywords}。你{action}。火星的指引是：勇气不是没有恐惧，而是带着恐惧依然向前。",
    "JUPITER": "今天{planet_label}的能量带给你{keywords}的信念。你{action}。木星想对你说：相信过程，好运往往发生在你继续走下去的时候。",
    "SATURN": "今天{planet_label}的能量让你面对{keywords}。你{action}。土星提醒你：真正的成长不在舒适区里，而在你选择坚持的那一刻。",
    "URANUS": "今天{planet_label}的能量让你渴望{keywords}的变化。你{action}。天王星鼓励你：打破旧模式需要勇气，但新的可能已经在敲门。",
    "NEPTUNE": "今天{planet_label}的能量让你沉浸在{keywords}的感受里。你{action}。海王星想对你说：梦想不是逃避，而是你内心深处的指南针。",
    "PLUTO": "今天{planet_label}的能量让你触及{keywords}的深处。你{action}。冥王星告诉你：放下不是失去，而是为新的生长腾出空间。",
}

# 通用模版（当行星不在模板列表中时使用）
GENERIC_TEMPLATE = "今天{planet_label}的能量让你感受到{keywords}。你{action}。{planet_label}想告诉你：今天所有的经历都在塑造更完整的你。"

# 动作短语库
ACTION_PHRASES: list[str] = [
    "在情绪的起伏中寻找自己的节奏",
    "在生活的细节中发现了新的意义",
    "在挑战面前选择了面对而非逃避",
    "在平凡的一天里找到了不平凡的自己",
    "在关系里学会了更好地表达自己",
    "在忙碌中不忘给自己留一点空间",
    "在不确定中依然选择相信",
    "在沉默中听到了内心的声音",
    "在变化中保持了自己的节奏",
    "在坚持中看到了不一样的风景",
]


@dataclass
class DiaryEntry:
    """星灵日记条目"""
    id: str
    report_id: str
    date: str
    keywords: list[str]
    entry_text: str
    spirit_planet: Optional[str] = None
    mood_emoji: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class DiaryEngine:
    """星灵日记引擎"""

    def __init__(self, diary_dir: str):
        self.diary_dir = diary_dir

    # ========================================================================
    # 条目生成
    # ========================================================================

    def extract_and_generate(
        self,
        report_id: str,
        chat_context: str,
        spirit_planet: str = "",
        mood_emoji: str = "",
    ) -> DiaryEntry:
        """
        从对话上下文中提取关键词并生成日记条目。

        Args:
            report_id: 报告 ID
            chat_context: 对话上下文（字符串或消息列表）
            spirit_planet: 星灵行星 key（如 "VENUS"）
            mood_emoji: 可选的情绪 emoji
        """
        now_str = datetime.now(timezone.utc).isoformat()
        today_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        # 提取情绪关键词
        keywords = self._extract_keywords(chat_context)

        # 确定 mood_emoji
        if not mood_emoji and keywords:
            mood_emoji = MOOD_EMOJI_MAP.get(keywords[0], "")

        # 生成条目文本
        entry_text = self._generate_entry_text(
            chat_context=chat_context,
            spirit_planet=spirit_planet,
            keywords=keywords,
        )

        entry = DiaryEntry(
            id=uuid.uuid4().hex[:12],
            report_id=report_id,
            date=today_date,
            keywords=keywords,
            entry_text=entry_text,
            spirit_planet=spirit_planet or None,
            mood_emoji=mood_emoji or None,
            created_at=now_str,
            updated_at=now_str,
        )

        # 保存到文件
        self._save_entry(entry)
        return entry

    def _extract_keywords(self, chat_context: str) -> list[str]:
        """从对话中提取情绪关键词，最多返回 5 个"""
        if not chat_context:
            return ["放松"]

        found = []
        for kw in EMOTIONAL_KEYWORDS:
            if kw in chat_context:
                found.append(kw)
            if len(found) >= 5:
                break

        if not found:
            # 如果没匹配到关键词，尝试检测积极/消极倾向
            positive_indicators = ["开心", "高兴", "好", "棒", "幸福", "感恩", "满足"]
            negative_indicators = ["难过", "伤心", "烦", "焦虑", "压力", "累", "难"]

            for word in positive_indicators:
                if word in chat_context:
                    found.append("温暖")
                    break
            if not found:
                for word in negative_indicators:
                    if word in chat_context:
                        found.append("疲惫")
                        break

        if not found:
            found.append("释然")

        return found[:5]

    def _generate_entry_text(
        self,
        chat_context: str,
        spirit_planet: str,
        keywords: list[str],
    ) -> str:
        """基于模板生成日记文本"""
        planet_label = PLANET_LABELS.get(
            Planet(spirit_planet), "星灵"
        ) if spirit_planet else "星灵"

        kw_str = "、".join(keywords) if keywords else "平静"

        # 选择模板
        template = SPIRIT_TEMPLATES.get(spirit_planet, GENERIC_TEMPLATE)

        # 构建动作描述
        user_message = chat_context[:100].strip() if chat_context else "今天没有特别的事情"
        action = self._pick_action_phrase(user_message)

        entry_text = template.format(
            planet_label=planet_label,
            keywords=kw_str,
            action=action,
        )

        # 附加用户原话摘要
        if chat_context and len(chat_context) > 20:
            summary = chat_context[:150].strip()
            entry_text += f"\n\n你说：{summary}"

        return entry_text

    def _pick_action_phrase(self, context: str) -> str:
        """根据上下文选择匹配的动作短语"""
        import random
        # 尝试匹配
        context_lower = context.lower()
        if any(w in context_lower for w in ["挑战", "困难", "难", "问题", "克服"]):
            return "在挑战面前选择了面对而非逃避"
        if any(w in context_lower for w in ["关系", "朋友", "家人", "爱人", "说"]):
            return "在关系里学会了更好地表达自己"
        if any(w in context_lower for w in ["工作", "忙", "做", "搞", "学"]):
            return "在忙碌中不忘给自己留一点空间"
        if any(w in context_lower for w in ["新", "变", "改变", "开始"]):
            return "在变化中保持了自己的节奏"
        if any(w in context_lower for w in ["坚持", "继续", "不放弃"]):
            return "在坚持中看到了不一样的风景"
        return random.choice(ACTION_PHRASES)

    # ========================================================================
    # 存储
    # ========================================================================

    def _get_file_path(self, report_id: str) -> str:
        """获取日记文件的路径"""
        os.makedirs(self.diary_dir, exist_ok=True)
        return os.path.join(self.diary_dir, f"{report_id}.json")

    def _load_entries(self, report_id: str) -> list[dict]:
        """加载指定报告的所有日记条目"""
        file_path = self._get_file_path(report_id)
        if not os.path.exists(file_path):
            return []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
                return []
        except (json.JSONDecodeError, OSError):
            return []

    def _save_entry(self, entry: DiaryEntry) -> None:
        """保存一个日记条目到文件"""
        entries = self._load_entries(entry.report_id)
        entries.append(entry.to_dict())
        file_path = self._get_file_path(entry.report_id)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(entries, f, ensure_ascii=False, indent=2)

    # ========================================================================
    # 查询
    # ========================================================================

    def get_timeline(
        self,
        report_id: str,
        limit: int = 30,
        offset: int = 0,
    ) -> list[DiaryEntry]:
        """
        获取日记时间线（按时间倒序）。

        Args:
            report_id: 报告 ID
            limit: 返回数量
            offset: 偏移量
        """
        entries = self._load_entries(report_id)
        # 按时间倒序排列
        entries.sort(key=lambda e: e.get("created_at", ""), reverse=True)
        # 分页
        page = entries[offset:offset + limit]
        return [DiaryEntry(**e) for e in page]
