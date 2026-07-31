"""Deterministic fallback text for the LLM surface.

Even when the LLM is unavailable, the engine must still produce a complete
consultation micro-cycle. This module renders each ``TurnPlan`` without any
network call.
"""
from __future__ import annotations

from typing import Iterable

from .models import ChartEvidence, ConsultationStage, TurnPlan


def _format_evidence(evidence: list[ChartEvidence]) -> str:
    if not evidence:
        return "（今天没有显示新的星盘证据，会沿用之前聊到的结构）"
    head = evidence[0]
    extras = []
    for item in evidence[1:3]:
        extras.append(item.fact)
    if extras:
        return f"{head.fact}。{'; '.join(extras)}"
    return head.fact


def _interpretation_text(options: Iterable[str]) -> str:
    items = [item for item in options if item]
    if not items:
        return "也可能有我们还没想到的表现。"
    return "可能的几种表现：" + "、".join(items[:3]) + "。也可以是这里没列出来的样子，甚至都不算。".join(
        ["", ""]
    )[0:1] + "".join(items[:3]) + "；都算，或者都不算，都请直接告诉我。".join(
        ["", ""]
    )[0:1]


def render_opening(plan: TurnPlan) -> str:
    evidence_text = _format_evidence(plan.evidence)
    options = plan.interpretation_options or []
    options_text = "；".join(options[:3]) if options else "我们需要看到具体事件才能验证"
    return (
        f"{plan.objective}。\n\n"
        f"先说星盘上的依据：{evidence_text}。\n\n"
        f"我对这一段的几种理解是：{options_text}。\n\n"
        f"{plan.question}"
    )


def render_explaining(plan: TurnPlan) -> str:
    return (
        f"{plan.objective}。\n"
        f"星盘上能看到：{_format_evidence(plan.evidence)}。\n"
        f"它通常会表现为：{'; '.join(plan.interpretation_options[:3]) or '需要先看具体事件'}。\n"
        f"{plan.question}"
    )


def render_inquiry(plan: TurnPlan) -> str:
    return plan.question or _render(plan)


def render_validation(plan: TurnPlan) -> str:
    return plan.question or _render(plan)


def render_insight(plan: TurnPlan) -> str:
    if plan.insight_draft is None:
        return plan.fallback_text
    draft = plan.insight_draft
    return (
        f"我先把这句用你的话写下来，等你确认或改写：\n\n"
        f"——{draft.summary}\n\n"
        f"用到的星盘依据：{_format_evidence(plan.evidence)}。\n\n"
        f"{plan.question}"
    )


def render_action(plan: TurnPlan) -> str:
    action = plan.interpretation_options[0] if plan.interpretation_options else plan.fallback_text
    return (
        f"我为你先列一个可以观察的小动作：\n\n"
        f"——{action}\n\n"
        f"{plan.question}"
    )


def render_pause(plan: TurnPlan) -> str:
    return plan.fallback_text


def render_close(plan: TurnPlan) -> str:
    return plan.fallback_text


_RENDERERS = {
    ConsultationStage.INTRODUCTION: render_opening,
    ConsultationStage.TOPIC_READY: render_explaining,
    ConsultationStage.STRUCTURE_EXPLAINING: render_explaining,
    ConsultationStage.EXPERIENCE_INQUIRY: render_inquiry,
    ConsultationStage.HYPOTHESIS_VALIDATION: render_validation,
    ConsultationStage.INSIGHT_DRAFT: render_insight,
    ConsultationStage.ACTION_EXPERIMENT: render_action,
    ConsultationStage.PAUSED: render_pause,
    ConsultationStage.CLOSED: render_close,
}


def render(plan: TurnPlan) -> str:
    renderer = _RENDERERS.get(plan.stage, _render)
    return renderer(plan)


def _render(plan: TurnPlan) -> str:
    return plan.fallback_text or plan.question or "我在听你讲。"
