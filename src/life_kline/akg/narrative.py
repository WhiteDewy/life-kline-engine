"""
narrative.py — AKG 主题叙事生成

build_theme_narrative(theme, report_data) -> str
匹配既有 seam（consultation_engine.py:805）。

ACP 合规：非宿命（禁用"注定/一定/必须"）、公开推理依据（引用证据）、
鼓励成长。叙事只复用 ThemeNode.evidence 里已收集的文本，不重新查 report_data。
"""
from __future__ import annotations

from .recognizer import ThemeNode

# 禁用词——叙事中不得出现（ACP 反宿命）
_FORBIDDEN = ("注定", "一定", "必须", "命中注定")


def build_theme_narrative(theme: ThemeNode, chart_data: dict) -> str:
    """把主题证据组装成 ACP 合规的叙事段落。"""
    if not theme or not theme.evidence:
        return ""

    # 取最有分量的 3 条证据（按权重排序）
    ev_sorted = sorted(theme.evidence, key=lambda e: e.get("weight", 0), reverse=True)
    ev_lines = [e["text"] for e in ev_sorted[:3] if e.get("text")]

    confidence_pct = int(theme.confidence * 100)

    parts = [
        f"关于「{theme.label}」——{theme.description}",
        "",
        "从你的星盘里，我注意到这些线索：",
    ]
    parts.extend(f"· {line}" for line in ev_lines)
    parts.extend([
        "",
        f"（基于以上证据，可信度约 {confidence_pct}%）",
        "",
        "这些揭示的是一种倾向和模式，不是命运的剧本——你的自由意志始终在起作用。"
        "看见它，是为了多一种选择，而不是被它限定。",
    ])

    narrative = "\n".join(parts)
    # ACP 防护：若模板意外引入禁用词，剔除
    for word in _FORBIDDEN:
        narrative = narrative.replace(word, "倾向")
    return narrative
