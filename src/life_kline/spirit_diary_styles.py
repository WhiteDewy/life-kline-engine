"""
spirit_diary_styles.py — 星灵日记多风格模板引擎。

支持多种日记风格（极简打卡 / 对话记录 / 自我反思 / 星灵风格 / 摘要型），
让日记真正成为用户的"情绪出口"，而不只是冷冰冰的模板生成物。

参考千问的日记方案：
  风格 1 — 极简情绪打卡风（check_in）：日期 + 状态 + 吐槽 + 领悟 + 小确幸 + 标签
  风格 2 — 对话体/播客记录风（dialogue）：对话记录式 + 治愈时刻
  风格 3 — 自我对话/反思风（reflection）：用户叙述 + 反思金句 + 星灵指导

所有模板均为通用模板（规则驱动），不针对特定人物。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ============================================================================
# 风格枚举
# ============================================================================

class DiaryStyle(str, Enum):
    """日记风格"""
    CHECK_IN = "check_in"        # 极简打卡风
    DIALOGUE = "dialogue"        # 对话体/播客风
    REFLECTION = "reflection"    # 自我对话/反思风
    SPIRIT = "spirit"            # 星灵风格（现有，以对话为主）
    SUMMARY = "summary"          # 摘要型（现有，用户内容为主）

    @property
    def label(self) -> str:
        """前端展示用中文标签"""
        return _STYLE_LABELS.get(self, self.value)

    @property
    def emoji(self) -> str:
        """风格 emoji 标识"""
        return _STYLE_EMOJIS.get(self, "✨")


_STYLE_LABELS: dict[DiaryStyle, str] = {
    DiaryStyle.CHECK_IN: "极简打卡",
    DiaryStyle.DIALOGUE: "对话记录",
    DiaryStyle.REFLECTION: "自我反思",
    DiaryStyle.SPIRIT: "星灵对话",
    DiaryStyle.SUMMARY: "对话摘要",
}

_STYLE_EMOJIS: dict[DiaryStyle, str] = {
    DiaryStyle.CHECK_IN: "⚡",
    DiaryStyle.DIALOGUE: "🎙️",
    DiaryStyle.REFLECTION: "💭",
    DiaryStyle.SPIRIT: "🌙",
    DiaryStyle.SUMMARY: "📝",
}


# ============================================================================
# 话题标签库（自动从对话内容抽取）
# ============================================================================

TOPIC_TAGS: dict[str, list[str]] = {
    "工作": ["工作", "老板", "同事", "项目", "加班", "汇报", "上班", "打工", "KPI"],
    "感情": ["感情", "恋爱", "对象", "分手", "暧昧", "喜欢", "心动", "前任", "恋爱"],
    "家庭": ["家庭", "爸妈", "父母", "亲人", "孩子", "家人", "老妈", "老爸"],
    "学习": ["学业", "考试", "论文", "学校", "毕业", "课程", "学习", "同学"],
    "健康": ["身体", "失眠", "睡眠", "病", "累", "头疼", "情绪", "抑郁", "焦虑"],
    "金钱": ["金钱", "钱", "工资", "房租", "消费", "欠", "卡债", "账单"],
    "关系": ["朋友", "社交", "人脉", "认识", "圈子"],
    "自我": ["自己", "自卑", "迷茫", "未来", "方向", "目标", "梦想"],
}

TOPIC_TAG_PREFIX: dict[str, str] = {
    "工作": "#打工人日常",
    "感情": "#情感记录",
    "家庭": "#家庭时光",
    "学习": "#学习打卡",
    "健康": "#身心状态",
    "金钱": "#财务笔记",
    "关系": "#关系观察",
    "自我": "#自我探索",
}


# ============================================================================
# 电量状态（基于情绪关键词推断）
# ============================================================================

ENERGY_LEVEL_MARKERS: dict[str, int] = {
    # 关键词 -> 电量百分比
    "疲惫": 20, "累": 25, "疲惫": 20, "压力": 25, "焦虑": 25,
    "委屈": 30, "迷茫": 35, "困惑": 40,
    "孤独": 35, "害怕": 30, "不甘": 40,
    "释然": 60, "勇敢": 70, "坚定": 75,
    "温暖": 80, "充实": 85, "感动": 80, "期待": 75,
}


def estimate_energy_level(text: str, keywords: Optional[list[str]] = None) -> int:
    """根据对话内容估算电量百分比。

    返回 0-100 的整数。综合文本关键词与预提取的情绪关键词。
    """
    if not text:
        return 50

    candidates = list(keywords or [])
    candidates.extend(EMOTIONAL_KEYWORDS if False else [])  # placeholder

    # 基于情绪关键词
    if keywords:
        scores = [ENERGY_LEVEL_MARKERS.get(k, 50) for k in keywords if k]
        if scores:
            return max(10, min(100, int(sum(scores) / len(scores))))

    # 文本检测
    text_lower = text or ""
    if any(w in text_lower for w in ["累死", "撑不住", "崩溃", "快不行了"]):
        return 15
    if any(w in text_lower for w in ["开心", "幸福", "感恩", "满足", "太棒了"]):
        return 85
    if any(w in text_lower for w in ["还好", "一般", "还行", "凑合"]):
        return 50
    return 50


def energy_label(level: int) -> str:
    """电量百分比 → 文字标签"""
    if level <= 20:
        return "电量耗尽"
    if level <= 40:
        return "电量低"
    if level <= 60:
        return "电量一半"
    if level <= 80:
        return "电量充足"
    return "满电"


# ============================================================================
# 风格模板
# ============================================================================

DIARY_STYLE_TEMPLATES: dict[DiaryStyle, str] = {

    DiaryStyle.CHECK_IN: """📅 {date} {weekday} | {mood_emoji} 状态：{energy_label}（电量{energy_level}%）
今日吐槽：{user_content_summary}
今日领悟：{spirit_insight}
今日小确幸：{evening_expectation}
{topic_tag_line}#星灵日记""",

    DiaryStyle.DIALOGUE: """📅 {date} {weekday} {title}
今天和{planet_label}聊了关于「{topic}」的话题。
你说：{user_content_summary}
{planet_label}说：{spirit_insight}
今天被{planet_label}治愈到了。{closing}
{topic_tag_line}""",

    DiaryStyle.REFLECTION: """📅 {date} {weekday}
{user_content_summary}

以前总觉得{topic}很难，但今天突然想通了：{insight}
既然{conclusion}，不如{action}。
{planet_label}想告诉你：{spirit_guidance}
{topic_tag_line}""",

    DiaryStyle.SPIRIT: """🌙 {date} {weekday} 与{planet_label}的对话
{planet_label}：{spirit_insight}
你说：{user_content_summary}
{planet_label}：{closing}
{topic_tag_line}#星灵日记""",

    DiaryStyle.SUMMARY: """📝 {date} {weekday}
今天你和{planet_label}聊了关于「{topic}」的事。
你说起了：{user_content_summary}
留给你的一句启发是：{spirit_insight}
{topic_tag_line}""",
}


# ============================================================================
# 字段填充数据
# ============================================================================

@dataclass
class DiaryRenderContext:
    """单条日记渲染所需的字段。"""
    date: str = ""
    weekday: str = ""
    title: str = "今天的小记录"
    mood_emoji: str = ""
    energy_level: int = 50
    energy_label: str = "电量一半"
    user_content_summary: str = ""
    spirit_insight: str = ""
    evening_expectation: str = "今天先好好休息。"
    insight: str = "允许自己不完美，也是一种勇气。"
    conclusion: str = "今天已经走过来了"
    action: str = "就允许自己停一停"
    spirit_guidance: str = "你已经做得够好了。"
    planet_label: str = "星灵"
    topic: str = "今天"
    topic_tag: str = ""
    topic_tag_line: str = ""
    closing: str = "今天被允许的疲惫，也是一种温柔。"
    keywords: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}


# ============================================================================
# 核心渲染
# ============================================================================

def render_diary(
    style: DiaryStyle | str,
    ctx: DiaryRenderContext,
) -> str:
    """根据风格 + 渲染上下文生成日记正文。

    Args:
        style: DiaryStyle 枚举或字符串
        ctx: 渲染上下文

    Returns:
        渲染后的日记文本。风格未知时降级为 SUMMARY。
    """
    if isinstance(style, str):
        try:
            style = DiaryStyle(style)
        except ValueError:
            style = DiaryStyle.SUMMARY

    template = DIARY_STYLE_TEMPLATES.get(style, DIARY_STYLE_TEMPLATES[DiaryStyle.SUMMARY])
    try:
        return template.format(**ctx.to_dict()).strip()
    except (KeyError, IndexError):
        # 模板字段缺失时降级到 SUMMARY
        return DIARY_STYLE_TEMPLATES[DiaryStyle.SUMMARY].format(**ctx.to_dict()).strip()


def get_style_previews(
    ctx: DiaryRenderContext,
    styles: Optional[list[DiaryStyle]] = None,
) -> list[dict]:
    """生成多个风格的预览（用于前端展示可选风格）。

    返回 [{style, label, emoji, preview}] 列表。
    """
    if not styles:
        styles = [DiaryStyle.CHECK_IN, DiaryStyle.DIALOGUE, DiaryStyle.REFLECTION]
    out: list[dict] = []
    for s in styles:
        out.append({
            "style": s.value,
            "label": s.label,
            "emoji": s.emoji,
            "preview": render_diary(s, ctx),
        })
    return out


# ============================================================================
# 自动字段推断工具
# ============================================================================

EMOTIONAL_KEYWORDS_HINT: list[str] = [
    "委屈", "不甘", "期待", "害怕", "勇敢", "迷茫", "坚定",
    "温暖", "孤独", "渴望", "释然", "困惑", "感动", "疲惫", "充实",
]


def infer_topic_tag(chat_context: str, fallback: str = "日常") -> tuple[str, str]:
    """从对话内容推断话题与标签。

    Returns:
        (topic_label, tag_string) — 例如 ("工作", "#打工人日常")
    """
    if not chat_context:
        return (fallback, "")
    for topic_label, markers in TOPIC_TAGS.items():
        for w in markers:
            if w in chat_context:
                return (topic_label, TOPIC_TAG_PREFIX.get(topic_label, ""))
    return (fallback, "")


def infer_closing(chat_context: str, planet_label: str) -> str:
    """根据上下文推断收束语。"""
    text = chat_context or ""
    if any(w in text for w in ["累", "疲惫", "扛不住"]):
        return f"今天被允许的疲惫，也是一种温柔——来自{planet_label}的提醒。"
    if any(w in text for w in ["迷茫", "困惑", "不知道"]):
        return f"走一步，再调方向，地图会在路上长出来——这是{planet_label}给你的承诺。"
    if any(w in text for w in ["开心", "幸福", "好极了"]):
        return f"好日子值得被记录——{planet_label}替你按下保存键。"
    if any(w in text for w in ["委屈", "不甘", "难过"]):
        return f"先把感受放下来，明天再决定要不要反击——{planet_label}陪你。"
    return f"今天就到这里，{planet_label}一直在。"


def infer_evening_expectation(chat_context: str) -> str:
    """从对话内容推断用户下班后 / 一天结束后想要的期待。"""
    text = chat_context or ""
    if any(w in text for w in ["累", "疲惫", "撑不住"]):
        return "今晚回去彻底摆烂，先瘫一会儿。"
    if any(w in text for w in ["饿", "想吃", "馋"]):
        return "今晚回去吃点好的，奖励自己。"
    if any(w in text for w in ["追剧", "剧", "综艺"]):
        return "今晚回去追一集喜欢的剧。"
    if any(w in text for w in ["游戏", "打机"]):
        return "今晚回去打两把游戏解压。"
    if any(w in text for w in ["书", "阅读"]):
        return "今晚回去翻几页书，给大脑放个假。"
    return "今晚回去好好休息，明天再说。"


def infer_insight(keywords: list[str], topic: str) -> str:
    """根据情绪关键词生成反思金句。"""
    insight_map: dict[str, str] = {
        "委屈": "委屈不是软肋，是你在乎的证据。",
        "不甘": "把不甘化成下一件事的燃料，而不是停在这里。",
        "期待": "期待值得被好好保护，也值得被认真审视。",
        "害怕": "允许自己慢一点，恐惧常常是提醒，不是阻止。",
        "勇敢": "你已经比想象中走得更远了。",
        "迷茫": "先走一步，地图会在路上长出来。",
        "坚定": "今天的笃定，是写给未来的自己的一封信。",
        "温暖": "这份温度值得反复使用。",
        "孤独": "你不是一个人。",
        "渴望": "承认渴望，比否定它更勇敢。",
        "释然": "放下的那一刻，是把自己还给自己。",
        "困惑": "允许暂时没有答案，问题也在等你准备好。",
        "感动": "把这些被看见的瞬间存起来，那是燃料。",
        "疲惫": "今天可以只做重要的事，不必做完所有事。",
        "充实": "这份充实，是你对今天的盖章。",
    }
    for k in keywords or []:
        if k in insight_map:
            return insight_map[k]
    if topic == "工作":
        return "打工不是全部，但你今天还是顶住了。"
    if topic == "感情":
        return "心动也好，遗憾也好，都是真实的你。"
    return "今天到这里，已经足够好了。"


def infer_conclusion(topic: str) -> str:
    """根据话题生成'既然...'的过渡句。"""
    if topic == "工作":
        return "今天已经走过来了"
    if topic == "感情":
        return "心情已经说了真话"
    if topic == "家庭":
        return "家和自己的关系，本来就要慢慢磨"
    if topic == "自我":
        return "今天的你比昨天更清楚一点点"
    return "今天就是今天"


def infer_action(topic: str, mood_emoji: str) -> str:
    """根据话题 + 情绪推断行动建议。"""
    if mood_emoji in ("😮‍💨", "😞", "😤"):
        return "就允许自己彻底摆烂一会儿"
    if topic == "工作":
        return "下班以后就别再回工作消息了"
    if topic == "感情":
        return "想说什么就说，不必非得体面"
    return "就让自己停一停"