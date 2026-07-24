"""
diary_engine.py — 星灵日记引擎

基于用户对话上下文生成星灵日记条目，支持情绪关键词提取、
模板化条目生成和 JSON 文件存储。

v1.1：支持多风格（极简打卡 / 对话记录 / 自我反思 / 星灵 / 摘要）。
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
from .spirit_diary_styles import (
    DiaryStyle,
    DiaryRenderContext,
    EMOTIONAL_KEYWORDS_HINT,
    energy_label,
    estimate_energy_level,
    get_style_previews,
    infer_action,
    infer_closing,
    infer_conclusion,
    infer_evening_expectation,
    infer_insight,
    infer_topic_tag,
    render_diary,
)

try:
    from backend import dao as _dao
except Exception:
    _dao = None  # 数据库不可用时回退到 JSON


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
    diary_style: str = "summary"            # check_in / dialogue / reflection / spirit / summary
    energy_level: int = 50                  # 电量 0-100
    topic_tag: str = ""                     # 例如 "工作"
    topic_tag_hash: str = ""                # 例如 "#打工人日常"
    evening_expectation: str = ""           # 下班后的期待
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class DiaryEngine:
    """星灵日记引擎

    默认把每条 entry 写入 SQLite 的 star_diary 表（数据库为单一可信源）。
    失败时自动回退写入 JSON 文件，保证旧调用方不被打断。
    """

    def __init__(self, diary_dir: str, user_id: str = "", profile_id: str = ""):
        self.diary_dir = diary_dir
        self.user_id = user_id
        self.profile_id = profile_id

    # ========================================================================
    # 条目生成
    # ========================================================================

    def extract_and_generate(
        self,
        report_id: str,
        chat_context: str,
        spirit_planet: str = "",
        mood_emoji: str = "",
        user_messages: Optional[list[str]] = None,
        spirit_responses: Optional[list[str]] = None,
        diary_style: str = "summary",
        evening_expectation: str = "",
    ) -> DiaryEntry:
        """从分角色对话生成日记；缺少新字段时兼容旧 chat_context。

        Args:
            diary_style: 日记风格 (check_in / dialogue / reflection / spirit / summary)
            evening_expectation: 用户下班后的期待（CHECK_IN 风格需要）
        """
        user_messages, spirit_responses = self._normalize_messages(
            chat_context, user_messages, spirit_responses
        )
        user_context = "\n".join(user_messages).strip() or (chat_context or "")
        structured_context = json.dumps(
            {"user_messages": user_messages, "spirit_responses": spirit_responses},
            ensure_ascii=False,
        )
        now_str = datetime.now(timezone.utc).isoformat()
        today_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        keywords = self._extract_keywords(user_context)

        if not mood_emoji and keywords:
            mood_emoji = MOOD_EMOJI_MAP.get(keywords[0], "")

        # 解析风格
        try:
            style = DiaryStyle(diary_style)
        except ValueError:
            style = DiaryStyle.SUMMARY

        topic_hint = self._pick_topic_hint(user_context, keywords)
        topic_label, topic_tag = infer_topic_tag(user_context, fallback="日常")
        # 优先使用 topic_hint（与旧逻辑一致），否则用 infer_topic_tag
        topic = topic_hint or topic_label

        planet_label = self._safe_planet_label(spirit_planet)
        energy_level = estimate_energy_level(user_context, keywords)
        insight_text = self._pick_best_spirit_insight(spirit_responses) or self._pick_guide(keywords)

        user_summary = self._summarize(" ".join(user_messages), 220)
        if not user_summary:
            user_summary = "你没有说很多，但愿意停下来看看自己此刻的状态。"

        # 渲染上下文（多风格统一）
        ctx = DiaryRenderContext(
            date=today_date,
            weekday=self._weekday_label(today_date),
            title=self._pick_title(keywords, topic),
            mood_emoji=mood_emoji or "✨",
            energy_level=energy_level,
            energy_label=energy_label(energy_level),
            user_content_summary=user_summary,
            spirit_insight=insight_text or "你已经做得够好了。",
            evening_expectation=evening_expectation or infer_evening_expectation(user_context),
            insight=infer_insight(keywords, topic),
            conclusion=infer_conclusion(topic),
            action=infer_action(topic, mood_emoji),
            spirit_guidance=self._pick_guide(keywords),
            planet_label=planet_label,
            topic=topic,
            topic_tag=topic,
            topic_tag_line=(topic_tag + " ") if topic_tag else "",
            closing=infer_closing(user_context, planet_label),
            keywords=keywords,
        )

        entry_text = render_diary(style, ctx)

        entry = DiaryEntry(
            id=uuid.uuid4().hex[:12], report_id=report_id, date=today_date,
            keywords=keywords, entry_text=entry_text,
            spirit_planet=spirit_planet or None, mood_emoji=mood_emoji or None,
            diary_style=style.value,
            energy_level=energy_level,
            topic_tag=topic_tag,
            evening_expectation=ctx.evening_expectation,
            created_at=now_str, updated_at=now_str,
        )

        if _dao is not None:
            try:
                row = _dao.insert_star_diary(
                    report_id=report_id, keywords=keywords, entry_text=entry_text,
                    chat_context=structured_context, spirit_planet=spirit_planet or "",
                    spirit_planet_label=planet_label,
                    mood_emoji=mood_emoji or "", user_id=self.user_id,
                    profile_id=self.profile_id, source="chat",
                    user_content_summary=user_summary,
                    spirit_content_summary=self._summarize(insight_text, 160),
                    diary_style=style.value,
                    energy_level=energy_level,
                    topic_tag=topic_tag,
                    evening_expectation=ctx.evening_expectation,
                )
                if row:
                    entry.id = row.get("id", entry.id)
                    entry.created_at = row.get("created_at", entry.created_at)
            except Exception:
                pass

        try:
            self._save_entry(entry)
        except Exception:
            pass
        return entry

    # ------------------------------------------------------------------
    # 多风格预览（前端可选风格使用）
    # ------------------------------------------------------------------

    def get_style_suggestions(
        self,
        report_id: str,
        chat_context: str = "",
        spirit_planet: str = "",
        mood_emoji: str = "",
        user_messages: Optional[list[str]] = None,
        spirit_responses: Optional[list[str]] = None,
    ) -> list[dict]:
        """返回所有可选风格 + 预览。用于前端风格选择面板。"""
        user_messages, spirit_responses = self._normalize_messages(
            chat_context, user_messages, spirit_responses
        )
        user_context = "\n".join(user_messages).strip() or (chat_context or "")
        keywords = self._extract_keywords(user_context)
        if not mood_emoji and keywords:
            mood_emoji = MOOD_EMOJI_MAP.get(keywords[0], "")
        topic_hint = self._pick_topic_hint(user_context, keywords)
        topic_label, topic_tag = infer_topic_tag(user_context, fallback="日常")
        topic = topic_hint or topic_label
        planet_label = self._safe_planet_label(spirit_planet)
        energy_level = estimate_energy_level(user_context, keywords)
        insight_text = self._pick_best_spirit_insight(spirit_responses) or self._pick_guide(keywords)
        user_summary = self._summarize(" ".join(user_messages), 220) or "你没有说很多。"

        ctx = DiaryRenderContext(
            date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            weekday=self._weekday_label(datetime.now(timezone.utc).strftime("%Y-%m-%d")),
            title=self._pick_title(keywords, topic),
            mood_emoji=mood_emoji or "✨",
            energy_level=energy_level,
            energy_label=energy_label(energy_level),
            user_content_summary=user_summary,
            spirit_insight=insight_text or "你已经做得够好了。",
            evening_expectation=infer_evening_expectation(user_context),
            insight=infer_insight(keywords, topic),
            conclusion=infer_conclusion(topic),
            action=infer_action(topic, mood_emoji),
            spirit_guidance=self._pick_guide(keywords),
            planet_label=planet_label,
            topic=topic,
            topic_tag=topic,
            topic_tag_line=(topic_tag + " ") if topic_tag else "",
            closing=infer_closing(user_context, planet_label),
            keywords=keywords,
        )
        return get_style_previews(ctx)

    @staticmethod
    def _safe_planet_label(spirit_planet: str) -> str:
        try:
            return PLANET_LABELS.get(Planet(spirit_planet), "星灵") if spirit_planet else "星灵"
        except (ValueError, KeyError):
            return "星灵"

    @staticmethod
    def _weekday_label(date_str: str) -> str:
        """'YYYY-MM-DD' → '周四'"""
        try:
            d = datetime.strptime(date_str, "%Y-%m-%d")
            cn = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
            return cn[d.weekday()]
        except Exception:
            return ""

    @staticmethod
    def _pick_title(keywords: list[str], topic: str) -> str:
        """为 DIALOGUE 风格生成标题。"""
        if "疲惫" in keywords or "累" in (topic or ""):
            return "打工人的一天"
        if topic == "感情":
            return "心动的瞬间"
        if topic == "家庭":
            return "家的二三事"
        if topic == "自我":
            return "和自己聊聊"
        return "今天的小记录"

    def _normalize_messages(
        self, chat_context: str, user_messages: Optional[list[str]],
        spirit_responses: Optional[list[str]],
    ) -> tuple[list[str], list[str]]:
        """清理分角色消息，并尝试读取结构化 JSON 旧参数。"""
        users = [str(x).strip() for x in (user_messages or []) if str(x).strip()]
        spirits = [str(x).strip() for x in (spirit_responses or []) if str(x).strip()]
        if not users and chat_context:
            try:
                payload = json.loads(chat_context)
                if isinstance(payload, dict):
                    users = [str(x).strip() for x in payload.get("user_messages", []) if str(x).strip()]
                    spirits = spirits or [str(x).strip() for x in payload.get("spirit_responses", []) if str(x).strip()]
            except (json.JSONDecodeError, TypeError):
                users = [chat_context.strip()]
        return users, spirits

    def _pick_best_spirit_insight(self, responses: Optional[list[str]]) -> str:
        """只留一句较完整、带行动或接纳意味的星灵启发。"""
        candidates: list[str] = []
        for response in responses or []:
            for sentence in response.replace("\n", "。").split("。"):
                sentence = sentence.strip(" ，；：.!！？")
                if 8 <= len(sentence) <= 80:
                    candidates.append(sentence)
        if not candidates:
            return ""
        markers = ("可以", "允许", "值得", "不必", "先", "试着", "提醒", "相信")
        return max(candidates, key=lambda s: (sum(m in s for m in markers), min(len(s), 45)))

    @staticmethod
    def _summarize(text: str, limit: int) -> str:
        return " ".join((text or "").split())[:limit]

    def _generate_diary_text(
        self, user_messages: list[str], spirit_response: str, topic: str,
        keywords: list[str], spirit_planet: str,
    ) -> str:
        """用户叙述占正文主体，星灵回复最多保留一句。"""
        try:
            planet_label = PLANET_LABELS.get(Planet(spirit_planet), "星灵") if spirit_planet else "星灵"
        except ValueError:
            planet_label = "星灵"
        opening = f"今天你和{planet_label}聊了关于「{topic}」的事。" if topic else f"今天你和{planet_label}聊了一会儿。"
        user_text = self._summarize(" ".join(user_messages), 300)
        if not user_text:
            user_text = "你没有说很多，但愿意停下来看看自己此刻的状态。"
        parts = [opening, f"你说起了：{user_text}"]
        if spirit_response:
            parts.append(f"留给你的一句启发是：{spirit_response}。")
        if keywords:
            parts.append(f"（关键词：{'、'.join(keywords[:3])}）")
        return "\n\n".join(parts)

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
        """基于用户真实对话生成日记文本（方案A：对话摘要型）。

        目标：让日记内容是用户对话的摘要，而不是通用模板句。
        结构：
          1) 起头「今天你和星灵聊了关于…话题」
          2) 摘要用户原话（最多 220 字）
          3) 星灵给到的回应/方向
          4) 关键词仅做末尾的标签展示
        """
        planet_label = PLANET_LABELS.get(
            Planet(spirit_planet), "星灵"
        ) if spirit_planet else "星灵"

        chat_clean = (chat_context or "").strip()
        if not chat_clean:
            chat_clean = "今天没有特别的事情想说，但你还是来了。"

        # 主题判定：挑选用户原话里最有可能的关键词当话题
        topic_hint = self._pick_topic_hint(chat_clean, keywords)
        kw_str = "、".join(keywords[:3]) if keywords else ""

        # 用户原话摘要（去掉空行）
        user_lines = [
            line.strip() for line in chat_clean.splitlines() if line.strip()
        ]
        user_excerpt = " ".join(user_lines)[:220].strip()

        parts: list[str] = []

        # 1) 起头
        if topic_hint:
            parts.append(f"今天你和{planet_label}聊了关于「{topic_hint}」的话题。")
        else:
            parts.append(f"今天你和{planet_label}聊了一会儿。")

        # 2) 用户原话摘要
        if user_excerpt:
            parts.append(f"你提到：{user_excerpt}")

        # 3) 星灵回应方向（按关键词选一句简短的指引）
        if keywords:
            guide = self._pick_guide(keywords)
            parts.append(f"{planet_label}对你说：{guide}")

        # 4) 关键词标签（不作为正文叙事）
        if kw_str:
            parts.append(f"（关键词：{kw_str}）")

        return "\n\n".join(parts)

    def _pick_topic_hint(self, chat_context: str, keywords: list[str]) -> str:
        """根据对话内容挑选一个具体的话题短语。"""
        # 先用主题词典
        topic_map: list[tuple[list[str], str]] = [
            (["工作", "老板", "同事", "项目", "加班", "汇报"], "工作压力"),
            (["感情", "恋爱", "对象", "分手", "暧昧", "喜欢"], "感情"),
            (["家庭", "爸妈", "父母", "亲人", "孩子"], "家庭"),
            (["学业", "考试", "论文", "学校", "毕业"], "学业"),
            (["金钱", "钱", "工资", "房租", "消费", "欠"], "金钱"),
            (["朋友", "社交", "人脉"], "关系"),
            (["自己", "自卑", "焦虑", "失眠", "迷茫", "未来"], "自我状态"),
        ]
        for words, label in topic_map:
            for w in words:
                if w in chat_context:
                    return label

        # 没有命中就用关键词中的第一个情绪词
        if keywords:
            return keywords[0]
        return ""

    def _pick_guide(self, keywords: list[str]) -> str:
        """根据情绪关键词选一句简短指引。"""
        guide_map: dict[str, str] = {
            "委屈": "先把感受放下来，你不需要证明自己的对错。",
            "不甘": "把力气放在你能改变的事上，而不是输赢上。",
            "期待": "给期待留一个期限，也给自己留一条退路。",
            "害怕": "允许自己慢一点，恐惧常常不是阻止你，是提醒你。",
            "勇敢": "你已经比想象中走得更远了。",
            "迷茫": "先走一步，再调方向，地图会在路上长出来。",
            "坚定": "把今天的选择，写给未来的你看。",
            "温暖": "这一份温度值得被记录下来，反复使用。",
            "孤独": "你不是一个人——星灵在这一侧陪着你。",
            "渴望": "渴望本身就是方向，承认它，比否定它更勇敢。",
            "释然": "放下的那一刻不是妥协，是你把自己还给自己。",
            "困惑": "允许自己暂时没有答案，问题也在等你准备好。",
            "感动": "把这些被看见的瞬间存起来，那是你的燃料。",
            "疲惫": "今天可以只做重要的事，不必把所有事都做完。",
            "充实": "把这份充实的感觉写下来，是你对今天的盖章。",
        }
        for kw in keywords:
            if kw in guide_map:
                return guide_map[kw]
        return "今天就到这里，明天继续。"

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
        # 优先从数据库读取
        if _dao is not None:
            try:
                rows = _dao.list_star_diary(
                    report_id=report_id, limit=limit, offset=offset,
                )
                if rows:
                    out: list[DiaryEntry] = []
                    for r in rows:
                        out.append(DiaryEntry(
                            id=r["id"],
                            report_id=r["report_id"],
                            date=r.get("date") or r.get("entry_date", ""),
                            keywords=list(r.get("keywords") or []),
                            entry_text=r.get("entry_text") or r.get("text") or "",
                            spirit_planet=r.get("spirit_planet") or None,
                            mood_emoji=r.get("mood_emoji") or None,
                            diary_style=r.get("diary_style", "summary"),
                            energy_level=int(r.get("energy_level", 50) or 50),
                            topic_tag=r.get("topic_tag", ""),
                            topic_tag_hash=r.get("topic_tag", ""),
                            evening_expectation=r.get("evening_expectation", ""),
                            created_at=r.get("created_at", ""),
                            updated_at=r.get("updated_at", ""),
                        ))
                    return out
            except Exception:
                pass

        entries = self._load_entries(report_id)
        # 按时间倒序排列
        entries.sort(key=lambda e: e.get("created_at", ""), reverse=True)
        # 分页
        page = entries[offset:offset + limit]
        return [DiaryEntry(**e) for e in page]
