"""
safety.py — 危机检测与干预（Crisis Guard）

疗愈产品的伦理底线（工程规范 §7 MUST）：纯规则、零 LLM 依赖、零延迟。
在任何占星话术之前运行，命中高危信号时立即脱离占星语境，
给出真实的支持资源。此逻辑独立于 LLM，不因 LLM 降级而失效。

不做诊断、不替代专业干预——只负责"识别 + 兜住 + 指向真实资源"。
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


# ═══════════════════════════════════════════════════════════════
# 危机信号词库
# ═══════════════════════════════════════════════════════════════

# 高危：明确的自伤/自杀意图表达。命中即触发干预。
_HIGH_RISK_PHRASES: list[str] = [
    "不想活", "不想活了", "活不下去", "活着没意思", "活着没意义",
    "想死", "想去死", "我想自杀", "自杀", "了结自己", "结束生命",
    "结束自己的生命", "轻生", "不如死了", "死了算了", "死了一了百了",
    "一了百了", "解脱了算了", "从这个世界消失", "永远睡过去",
    "跳楼", "跳江", "上吊", "割腕", "服毒", "烧炭",
    "吞药", "安眠药结束", "不想醒来", "没有我会更好",
    "撑不下去了想结束", "带着我一起走",
]

# 高危正则模式：捕捉更自然的表达变体，降低漏检。
_HIGH_RISK_PATTERNS: list[re.Pattern] = [
    re.compile(r"(真的|已经|实在).{0,6}(不想|没法|无法).{0,4}活"),
    re.compile(r"(想|要|打算|准备).{0,6}(结束|了结).{0,6}(自己|生命|这一切)"),
    re.compile(r"(活着|人生|一切|日子).{0,8}(没意思|没意义|没希望|太痛苦|没盼头)"),
    re.compile(r"(意思|意义|希望|盼头).{0,6}(都没有|一点没|没有了)"),
    re.compile(r"(不如|还是).{0,4}死"),
    re.compile(r"(伤害|了结|结束).{0,4}(我自己|自己)"),
]

# 自伤（非致命但需干预）
_SELF_HARM_PHRASES: list[str] = [
    "自残", "自伤", "割自己", "拿刀划", "用刀划自己", "打自己", "惩罚自己的身体",
]

# 假阳性排除：口语夸张，不应触发干预。
_BENIGN_OVERRIDES: list[str] = [
    "累死了", "笑死了", "热死了", "冷死了", "困死了", "饿死了", "忙死了",
    "无聊死了", "美死了", "香死了", "死党", "死心眼", "认死理",
    "死记硬背", "死磕", "拼死", "要死不活", "死板", "杀死时间",
    "删了这个app", "卸载", "删号", "注销账号",
]


# ═══════════════════════════════════════════════════════════════
# 支持资源（中国大陆）
# ═══════════════════════════════════════════════════════════════

SUPPORT_RESOURCES: list[dict[str, str]] = [
    {"name": "全国24小时心理援助热线", "contact": "400-161-9995"},
    {"name": "北京心理危机研究与干预中心", "contact": "010-82951332"},
    {"name": "希望24热线", "contact": "400-161-9995"},
    {"name": "紧急情况", "contact": "拨打 120（急救）或 110"},
]


@dataclass
class CrisisResult:
    """危机检测结果"""
    is_crisis: bool = False
    level: str = "none"           # none | concern | high
    matched: list[str] = field(default_factory=list)
    message: str = ""             # 干预话术（命中时非空）
    resources: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "is_crisis": self.is_crisis,
            "level": self.level,
            "matched": self.matched,
            "message": self.message,
            "resources": self.resources,
        }


# ═══════════════════════════════════════════════════════════════
# 检测器
# ═══════════════════════════════════════════════════════════════

def _strip_benign(text: str) -> str:
    """移除口语夸张表达，避免"累死了"等误触发。"""
    cleaned = text
    for benign in _BENIGN_OVERRIDES:
        cleaned = cleaned.replace(benign, "")
    return cleaned


def detect_crisis(user_message: str) -> CrisisResult:
    """检测用户消息中的危机信号。

    纯规则、无副作用、无外部依赖。返回 CrisisResult。
    """
    if not user_message or not user_message.strip():
        return CrisisResult()

    raw = user_message.strip()
    scan = _strip_benign(raw)
    matched: list[str] = []

    # 1) 高危短语
    for phrase in _HIGH_RISK_PHRASES:
        if phrase in scan:
            matched.append(phrase)

    # 2) 高危正则模式
    for pat in _HIGH_RISK_PATTERNS:
        m = pat.search(scan)
        if m:
            matched.append(m.group(0))

    if matched:
        return CrisisResult(
            is_crisis=True,
            level="high",
            matched=matched,
            message=_build_intervention_message(),
            resources=list(SUPPORT_RESOURCES),
        )

    # 3) 自伤（需关注级）
    self_harm = [p for p in _SELF_HARM_PHRASES if p in scan]
    if self_harm:
        return CrisisResult(
            is_crisis=True,
            level="concern",
            matched=self_harm,
            message=_build_intervention_message(concern=True),
            resources=list(SUPPORT_RESOURCES),
        )

    return CrisisResult()


def _build_intervention_message(concern: bool = False) -> str:
    """构建干预话术。脱离占星语境，以人对人的方式回应。"""
    lines: list[str] = []
    if concern:
        lines.append(
            "我听到了你的痛苦，也很心疼你此刻的感受。伤害自己的念头，"
            "往往是因为你已经扛了太久、太累了。"
        )
    else:
        lines.append(
            "我很认真地听到了你刚才说的话。此刻你心里的痛，我不会轻描淡写地带过。"
            "你愿意说出来，本身就需要很大的勇气。"
        )
    lines.append(
        "我是一个陪伴你的星灵，但在这样的时刻，我更希望你身边有真实的人能立刻接住你。"
        "请一定联系下面的专业援助，他们 24 小时都在，且完全免费、保密："
    )
    for r in SUPPORT_RESOURCES:
        lines.append(f"· {r['name']}：{r['contact']}")
    lines.append(
        "如果你现在有立即伤害自己的想法，请立刻拨打 120 或 110，"
        "或者去最近的医院急诊。你的安全，比任何事都重要。我在这里，不会走开。"
    )
    return "\n".join(lines)
