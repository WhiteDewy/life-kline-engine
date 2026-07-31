"""Pure event-driven consultation state machine."""
from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from typing import Any

from .dossier import match_topic as _route_topic
from .models import (
    ChartEvidence,
    ConfirmedInsight,
    ConsultationHypothesis,
    ConsultationStage,
    ConsultationState,
    ExperienceAnchor,
    SpiritDossier,
    StructureTopic,
    TurnIntent,
    TurnPlan,
    ValidationStatus,
    stable_object_id,
)


_FALSIFIABLE_INTENTS = {
    TurnIntent.QUESTION,
    TurnIntent.CONTINUE,
    TurnIntent.DEEPEN,
    TurnIntent.PARTIAL,
    TurnIntent.UNCERTAIN,
}

_INQUIRY_TEMPLATES = {
    ConsultationStage.STRUCTURE_EXPLAINING: (
        "在聊到这一段之前，先不判断它对不对——"
        "你能想到一个最近的、具体的事件或场景吗？"
    ),
    ConsultationStage.EXPERIENCE_INQUIRY: (
        "那一次，你有没有注意到身体或情绪上的什么反应？"
        "最后是做了什么、还是没做什么，事情才走到那个结果？"
    ),
    ConsultationStage.HYPOTHESIS_VALIDATION: (
        "听上去像 / 不太像 —— 你是更常这样，还是偶尔会不同？"
    ),
    ConsultationStage.INSIGHT_DRAFT: (
        "如果让我用你自己的话，替这句话起个标题，你会怎么起？"
    ),
    ConsultationStage.ACTION_EXPERIMENT: (
        "那我们把这次的觉察变成一个可以观察的小动作："
        "在下周 / 下一次出现类似场景时，你打算先留意哪一件事？"
    ),
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_session_id() -> str:
    return "ses_" + uuid.uuid4().hex[:12]


def _new_hypothesis_id() -> str:
    return "hyp_" + uuid.uuid4().hex[:12]


def _new_insight_id() -> str:
    return "ins_" + uuid.uuid4().hex[:12]


def _detect_question_intent(text: str, has_command: bool) -> TurnIntent:
    if not text:
        return TurnIntent.CONTINUE
    if has_command:
        return TurnIntent.QUESTION
    return TurnIntent.QUESTION if re.search(
        r"([?？]|吗(?:[，。！？\s]|$)|什么|怎么|哪[个种里些]|谁|为什么|是否|"
        r"是不是|能不能|会不会|有没有|可不可以|何时|什么时候|多少|"
        r"聊聊|聊一聊|想聊|问问|想知道)",
        text,
    ) else TurnIntent.CONTINUE


def _coerce_intent(value: str) -> TurnIntent | None:
    """Parse the wire value (``confirm``), not the enum member name."""
    try:
        return TurnIntent(value.strip().lower())
    except (AttributeError, ValueError):
        return None


def _detect_command_intent(text: str) -> TurnIntent | None:
    normalized = text.strip()
    if not normalized:
        return None
    if any(word in normalized for word in ("暂停", "停一下", "稍后")):
        return TurnIntent.PAUSE
    if any(word in normalized for word in ("回来", "继续聊", "我们继续")):
        return TurnIntent.RESUME
    if any(word in normalized for word in ("下一个", "换话题", "切到下一个", "另一个话题")):
        return TurnIntent.NEXT_TOPIC
    if any(word in normalized for word in ("深入", "展开", "多说点", "再讲")):
        return TurnIntent.DEEPEN
    if any(word in normalized for word in ("结束", "收尾", "今天到这", "够了")):
        return TurnIntent.CLOSE
    if any(word in normalized for word in ("不太像", "不是", "不像我", "不符合", "不一样")):
        return TurnIntent.REJECT
    if any(word in normalized for word in ("部分像", "有一点像", "一半", "类似但")):
        return TurnIntent.PARTIAL
    if any(word in normalized for word in ("不确定", "不知道", "说不清", "再想想", "说不准")):
        return TurnIntent.UNCERTAIN
    if normalized == "对" or normalized.startswith("对，") or normalized.startswith("对,") or normalized.startswith("对。") or any(
        word in normalized for word in ("是的", "确实", "就是这样", "确认", "说得对", "对啊", "对呀")
    ):
        return TurnIntent.CONFIRM
    return None


def initial_state(report_id: str, planet: str, dossier: SpiritDossier) -> ConsultationState:
    """Build the starting state for a fresh consultation session."""
    queue = list(dossier.topic_order)
    first_topic = queue[0] if queue else ""
    return ConsultationState(
        session_id=_new_session_id(),
        report_id=report_id,
        planet=planet,
        stage=ConsultationStage.INTRODUCTION,
        topic_queue=queue,
        current_topic=first_topic,
        topic_stack=[],
        completed_topics=[],
        evidence_used=[],
        denied_evidence_ids=[],
        turn_count=0,
        version=1,
        guided_mode=True,
        free_cycle_complete=False,
        experience_anchor=ExperienceAnchor(),
        hypotheses=[],
        insights=[],
        created_at=_now(),
        updated_at=_now(),
    )


def _claim_topic(
    state: ConsultationState,
    dossier: SpiritDossier,
    intent: TurnIntent,
) -> tuple[str, list[StructureTopic]]:
    if intent is TurnIntent.NEXT_TOPIC and state.completed_topics:
        for key in state.topic_queue:
            if key in state.completed_topics:
                continue
            return key, [dossier.topic_by_key()[key]] if key in dossier.topic_by_key() else []
    if state.current_topic and intent in {TurnIntent.DEEPEN, TurnIntent.QUESTION}:
        topic = dossier.topic_by_key().get(state.current_topic)
        if topic:
            return state.current_topic, [topic]
    if state.current_topic and intent not in {TurnIntent.NEXT_TOPIC}:
        topic = dossier.topic_by_key().get(state.current_topic)
        if topic:
            return state.current_topic, [topic]
    candidates = [
        dossier.topic_by_key()[key]
        for key in state.topic_queue
        if key not in state.completed_topics
    ]
    candidates = [item for item in candidates if item]
    if state.current_topic:
        current = dossier.topic_by_key().get(state.current_topic)
        if current in candidates:
            candidates.remove(current)
            candidates.insert(0, current)
    if not candidates:
        return state.current_topic, []
    return candidates[0].key, candidates[:1]


def _mark_topic_progress(state: ConsultationState, topic_key: str) -> None:
    if topic_key and topic_key not in state.completed_topics:
        state.completed_topics.append(topic_key)


def _available_evidence(dossier: SpiritDossier, topic: StructureTopic) -> list[ChartEvidence]:
    by_id = dossier.evidence_by_id()
    return [by_id[item] for item in topic.evidence_ids if item in by_id]


def _record_evidence_usage(state: ConsultationState, evidence: list[ChartEvidence]) -> None:
    for item in evidence:
        if (
            item.evidence_id not in state.evidence_used
            and item.evidence_id not in state.denied_evidence_ids
        ):
            state.evidence_used.append(item.evidence_id)


def _build_hypothesis(
    state: ConsultationState,
    dossier: SpiritDossier,
    topic: StructureTopic,
    evidence: list[ChartEvidence],
) -> ConsultationHypothesis:
    summary = f"从{topic.title}看，可能出现这些倾向：{' / '.join(topic.interpretation_options[:2])}"
    return ConsultationHypothesis(
        hypothesis_id=_new_hypothesis_id(),
        topic_key=topic.key,
        evidence_ids=[item.evidence_id for item in evidence],
        statement=summary,
        alternatives=list(topic.interpretation_options),
    )


def _build_insight_draft(
    state: ConsultationState,
    hypothesis: ConsultationHypothesis,
    topic: StructureTopic,
    user_quote: str,
) -> ConfirmedInsight:
    anchor = state.experience_anchor
    summary = (
        f"在{topic.title}上，你的具体经历是「{anchor.situation or '——'}」，"
        f"其中{anchor.response or '——'}是你的反应；"
        f"用你自己的话说：「{user_quote or '（请用你的话补一句）'}」"
    )
    return ConfirmedInsight(
        insight_id=_new_insight_id(),
        hypothesis_id=hypothesis.hypothesis_id,
        planet=state.planet,
        topic_key=topic.key,
        evidence_ids=list(hypothesis.evidence_ids),
        user_quote=user_quote,
        summary=summary,
        domain_tags=list(topic.domain_tags),
        growth_action="下次类似场景下，先观察身体或情绪的触发，再用一次不同的反应看看结果。",
    )


def plan_introduction(
    state: ConsultationState, dossier: SpiritDossier
) -> TurnPlan:
    topic_key, topics = _claim_topic(state, dossier, TurnIntent.CONTINUE)
    topic = topics[0] if topics else None
    evidence: list[ChartEvidence] = []
    if topic:
        evidence = _available_evidence(dossier, topic)
        _record_evidence_usage(state, evidence)
    fallback = (
        f"{dossier.identity_statement}\n\n"
        f"我们一起从「{topic.title}」开始：{topic.summary if topic else '先看看你的整体结构'}。"
    )
    return TurnPlan(
        stage=ConsultationStage.INTRODUCTION,
        objective="让星灵先报出身份并确认进入方向",
        topic_key=topic_key,
        evidence=evidence,
        interpretation_options=topic.interpretation_options if topic else [],
        question=topic.inquiry_question if topic else "先从哪个话题开始？",
        fallback_text=fallback,
        actions=[TurnIntent.CONTINUE, TurnIntent.DEEPEN, TurnIntent.NEXT_TOPIC],
    )


def plan_explaining(
    state: ConsultationState, dossier: SpiritDossier
) -> TurnPlan:
    topic_key, topics = _claim_topic(state, dossier, TurnIntent.CONTINUE)
    topic = topics[0] if topics else None
    evidence: list[ChartEvidence] = []
    options: list[str] = []
    question = "可以告诉我最近一次的具体事件吗？"
    if topic:
        available = _available_evidence(dossier, topic)
        evidence = [
            item for item in available if item.evidence_id not in state.denied_evidence_ids
        ]
        if not evidence and available:
            evidence = available
        _record_evidence_usage(state, evidence)
        options = list(topic.interpretation_options)
        question = topic.inquiry_question
    state.stage = ConsultationStage.STRUCTURE_EXPLAINING
    state.current_topic = topic_key
    return TurnPlan(
        stage=ConsultationStage.STRUCTURE_EXPLAINING,
        objective="只解释一个结构事实并引出 2-3 种可能性",
        topic_key=topic_key,
        evidence=evidence[:4],
        interpretation_options=options,
        question=question,
        fallback_text=_INQUIRY_TEMPLATES[ConsultationStage.STRUCTURE_EXPLAINING],
        actions=[TurnIntent.CONTINUE, TurnIntent.DEEPEN, TurnIntent.NEXT_TOPIC, TurnIntent.PAUSE],
    )


def plan_inquiry(
    state: ConsultationState, dossier: SpiritDossier
) -> TurnPlan:
    topic = dossier.topic_by_key().get(state.current_topic)
    evidence = _available_evidence(dossier, topic) if topic else []
    options = list(topic.interpretation_options) if topic else []
    question = _INQUIRY_TEMPLATES[ConsultationStage.EXPERIENCE_INQUIRY]
    return TurnPlan(
        stage=ConsultationStage.EXPERIENCE_INQUIRY,
        objective="收集最近一次现实事件中的细节",
        topic_key=state.current_topic,
        evidence=evidence,
        interpretation_options=options,
        question=question,
        fallback_text=question,
        actions=[TurnIntent.CONTINUE, TurnIntent.DEEPEN, TurnIntent.NEXT_TOPIC],
    )


def plan_validation(
    state: ConsultationState, dossier: SpiritDossier
) -> TurnPlan:
    topic = dossier.topic_by_key().get(state.current_topic)
    evidence = _available_evidence(dossier, topic) if topic else []
    options = list(topic.interpretation_options) if topic else []
    question = _INQUIRY_TEMPLATES[ConsultationStage.HYPOTHESIS_VALIDATION]
    return TurnPlan(
        stage=ConsultationStage.HYPOTHESIS_VALIDATION,
        objective="根据用户反应给出一句假设并请求对或不对",
        topic_key=state.current_topic,
        evidence=evidence,
        interpretation_options=options,
        question=question,
        fallback_text=question,
        actions=[
            TurnIntent.CONFIRM,
            TurnIntent.PARTIAL,
            TurnIntent.REJECT,
            TurnIntent.UNCERTAIN,
        ],
    )


def plan_insight_draft(
    state: ConsultationState, dossier: SpiritDossier
) -> TurnPlan:
    hypothesis = state.current_hypothesis()
    if not hypothesis or hypothesis.validation_status is not ValidationStatus.CONFIRMED:
        return plan_validation(state, dossier)
    topic = dossier.topic_by_key().get(hypothesis.topic_key) or dossier.topic_by_key().get(state.current_topic)
    user_quote = (hypothesis.user_quote or "").strip()
    insight = _build_insight_draft(state, hypothesis, topic, user_quote)
    state.hypotheses = [
        item for item in state.hypotheses if item.hypothesis_id != hypothesis.hypothesis_id
    ] + [hypothesis]
    state.insights.append(insight)
    state.stage = ConsultationStage.INSIGHT_DRAFT
    return TurnPlan(
        stage=ConsultationStage.INSIGHT_DRAFT,
        objective="把可验证的洞察交给用户，提示如何用证据交叉核对",
        topic_key=hypothesis.topic_key,
        evidence=_available_evidence(dossier, topic),
        interpretation_options=[insight.summary],
        question=_INQUIRY_TEMPLATES[ConsultationStage.INSIGHT_DRAFT],
        fallback_text=insight.summary,
        actions=[
            TurnIntent.CONFIRM,
            TurnIntent.PARTIAL,
            TurnIntent.REJECT,
            TurnIntent.DEEPEN,
        ],
        insight_draft=insight,
    )


def plan_action(
    state: ConsultationState, dossier: SpiritDossier
) -> TurnPlan:
    insight = state.insights[-1] if state.insights else None
    topic = dossier.topic_by_key().get(insight.topic_key) if insight else None
    return TurnPlan(
        stage=ConsultationStage.ACTION_EXPERIMENT,
        objective="请用户为这次洞察起一个标题，并约定一个可观察的行动",
        topic_key=insight.topic_key if insight else state.current_topic,
        evidence=_available_evidence(dossier, topic) if topic else [],
        interpretation_options=[insight.growth_action] if insight else [],
        question=_INQUIRY_TEMPLATES[ConsultationStage.ACTION_EXPERIMENT],
        fallback_text=(
            insight.growth_action
            if insight
            else "下次类似场景下，先留意身体的反应再决定下一步。"
        ),
        actions=[TurnIntent.CONFIRM, TurnIntent.NEXT_TOPIC, TurnIntent.CLOSE],
    )


def _open_hypothesis(
    state: ConsultationState,
    dossier: SpiritDossier,
    topic: StructureTopic,
    user_quote: str,
) -> ConsultationHypothesis:
    by_id = dossier.evidence_by_id()
    evidence_ids = [item for item in topic.evidence_ids if item in by_id]
    hypothesis = ConsultationHypothesis(
        hypothesis_id=_new_hypothesis_id(),
        topic_key=topic.key,
        evidence_ids=evidence_ids,
        statement=f"可能表现为：{' / '.join(topic.interpretation_options[:2])}",
        alternatives=list(topic.interpretation_options),
        user_quote=user_quote,
    )
    state.hypotheses.append(hypothesis)
    return hypothesis


def state_topic_evidence_map(
    state: ConsultationState, topic: StructureTopic
) -> dict[str, ChartEvidence]:
    by_id: dict[str, ChartEvidence] = {}
    for item in topic.evidence_ids:
        if item not in state.evidence_used:
            by_id[item] = None  # type: ignore[assignment]
    return {item.evidence_id: item for item in []}  # populated by caller via dossier


def resolve_turn(
    state: ConsultationState,
    dossier: SpiritDossier,
    user_message: str,
    intent_hint: str = "",
    topic_hint: str = "",
    *,
    llm_client: Any = None,
) -> TurnPlan:
    """Plan the engine side of a consultation turn; LLM only renders language."""
    state.turn_count += 1
    state.version += 1
    state.updated_at = _now()
    text = (user_message or "").strip()

    # UI commands and the async semantic classifier both use enum wire values.
    # Explicit UI actions win; natural-language commands are the deterministic
    # fallback when the classifier is unavailable.
    hinted_intent = _coerce_intent(intent_hint)
    command = _detect_command_intent(text) if text else None
    if hinted_intent is not None:
        intent = hinted_intent
    elif command is not None:
        intent = command
    else:
        intent = _detect_question_intent(text, has_command=False)
    routed_topic_from_llm = topic_hint if topic_hint in dossier.topic_order else ""

    if intent is TurnIntent.CLOSE:
        state.stage = ConsultationStage.CLOSED
        return _build_close_plan(state, dossier)
    if intent is TurnIntent.PAUSE:
        state.stage = ConsultationStage.PAUSED
        return _build_pause_plan(state, dossier)
    if intent is TurnIntent.RESUME and state.stage is ConsultationStage.PAUSED:
        state.stage = ConsultationStage.TOPIC_READY
        return plan_introduction(state, dossier)
    if (
        intent is TurnIntent.SWITCH_TOPIC
        and routed_topic_from_llm
        and routed_topic_from_llm != state.current_topic
    ):
        if state.current_topic:
            state.topic_stack.append(state.current_topic)
        state.current_topic = routed_topic_from_llm
        state.stage = ConsultationStage.STRUCTURE_EXPLAINING
        return plan_explaining(state, dossier)
    if intent is TurnIntent.SWITCH_TOPIC:
        intent = TurnIntent.NEXT_TOPIC

    if intent is TurnIntent.NEXT_TOPIC:
        if state.stage in {ConsultationStage.ACTION_EXPERIMENT, ConsultationStage.INSIGHT_DRAFT}:
            state.free_cycle_complete = True
        topic_key, topics = _claim_topic(state, dossier, intent)
        if not topics:
            state.stage = ConsultationStage.CLOSED
            return _build_close_plan(state, dossier)
        state.current_topic = topic_key
        state.stage = ConsultationStage.STRUCTURE_EXPLAINING
        return plan_explaining(state, dossier)
    if intent is TurnIntent.DEEPEN and state.current_topic:
        return plan_explaining(state, dossier)

    # ── 话题路由：LLM 分类 + 关键词双层匹配 ──
    routed_topic = routed_topic_from_llm
    if (
        not routed_topic
        and text
        and (
            intent is TurnIntent.QUESTION
            or state.stage in {ConsultationStage.INTRODUCTION, ConsultationStage.TOPIC_READY}
        )
    ):
        routed_topic = _route_topic(dossier, text)
    if routed_topic and routed_topic != state.current_topic and routed_topic in state.topic_queue:
        state.topic_stack.append(state.current_topic)
        state.current_topic = routed_topic
        state.stage = ConsultationStage.STRUCTURE_EXPLAINING
        return plan_explaining(state, dossier)

    if state.stage is ConsultationStage.INTRODUCTION or state.stage is ConsultationStage.TOPIC_READY:
        if state.stage is ConsultationStage.INTRODUCTION and text:
            # 用户发了第一条消息（任何内容）→ 离开开场，进入结构拆解
            state.stage = ConsultationStage.STRUCTURE_EXPLAINING
            return plan_explaining(state, dossier)
        if intent is TurnIntent.QUESTION and state.current_topic:
            state.stage = ConsultationStage.STRUCTURE_EXPLAINING
            return plan_explaining(state, dossier)
        if intent is TurnIntent.DEEPEN and state.current_topic:
            state.stage = ConsultationStage.STRUCTURE_EXPLAINING
            return plan_explaining(state, dossier)
        if intent is TurnIntent.CONTINUE and text and state.current_topic:
            state.stage = ConsultationStage.STRUCTURE_EXPLAINING
            return plan_explaining(state, dossier)
        return plan_introduction(state, dossier)

    topic = dossier.topic_by_key().get(state.current_topic)
    if not topic:
        return plan_introduction(state, dossier)

    # ── 任意阶段的话题切换：用户提到另一个已有话题的关键词时 ──
    if routed_topic and routed_topic != state.current_topic:
        state.topic_stack.append(state.current_topic)
        state.current_topic = routed_topic
        state.stage = ConsultationStage.STRUCTURE_EXPLAINING
        return plan_explaining(state, dossier)

    # ── 自由提问：关键词没匹配到任何话题时，不硬塞当前结构 ──
    if intent is TurnIntent.QUESTION and not routed_topic:
        return _plan_unmatched_question(state, dossier, text)

    if state.stage is ConsultationStage.STRUCTURE_EXPLAINING:
        # 用户说"想不出/没有/不知道" → LLM 分类或关键词，不强行假设
        if intent is TurnIntent.NO_EXPERIENCE or _is_no_experience(text):
            state.stage = ConsultationStage.TOPIC_READY
            _, topics = _claim_topic(state, dossier, TurnIntent.NEXT_TOPIC)
            if topics:
                state.current_topic = topics[0].key
                state.stage = ConsultationStage.STRUCTURE_EXPLAINING
                return plan_explaining(state, dossier)
            state.stage = ConsultationStage.CLOSED
            return _build_close_plan(state, dossier)
        state.experience_anchor = _update_anchor(state.experience_anchor, text)
        _open_hypothesis(state, dossier, topic, text or state.experience_anchor.situation)
        state.stage = ConsultationStage.HYPOTHESIS_VALIDATION
        return plan_validation(state, dossier)

    if state.stage is ConsultationStage.EXPERIENCE_INQUIRY:
        state.experience_anchor = _update_anchor(state.experience_anchor, text)
        _open_hypothesis(state, dossier, topic, text or state.experience_anchor.situation)
        state.stage = ConsultationStage.HYPOTHESIS_VALIDATION
        return plan_validation(state, dossier)
    if state.stage is ConsultationStage.HYPOTHESIS_VALIDATION:
        hyp = state.current_hypothesis()
        if hyp is not None:
            hyp.user_quote = text or hyp.user_quote
        if intent is TurnIntent.CONFIRM and hyp is not None:
            hyp.validation_status = ValidationStatus.CONFIRMED
            _mark_topic_progress(state, topic.key)
            state.stage = ConsultationStage.INSIGHT_DRAFT
            return plan_insight_draft(state, dossier)
        if intent is TurnIntent.PARTIAL and hyp is not None:
            hyp.validation_status = ValidationStatus.PARTIAL
            return plan_validation(state, dossier)
        if intent is TurnIntent.UNCERTAIN and hyp is not None:
            hyp.validation_status = ValidationStatus.UNCERTAIN
            return plan_action(state, dossier)
        if intent is TurnIntent.REJECT and hyp is not None:
            hyp.validation_status = ValidationStatus.REJECTED
            for item in hyp.evidence_ids:
                if item not in state.denied_evidence_ids:
                    state.denied_evidence_ids.append(item)
            return plan_explaining(state, dossier)
        return plan_validation(state, dossier)
    if state.stage is ConsultationStage.INSIGHT_DRAFT:
        if intent in {TurnIntent.CONFIRM, TurnIntent.DEEPEN, TurnIntent.CONTINUE}:
            state.stage = ConsultationStage.ACTION_EXPERIMENT
            if state.insights:
                state.insights[-1].user_quote = text or state.insights[-1].user_quote
            return plan_action(state, dossier)
        if intent is TurnIntent.PARTIAL:
            if state.insights:
                state.insights[-1].user_quote = text or state.insights[-1].user_quote
            state.stage = ConsultationStage.ACTION_EXPERIMENT
            return plan_action(state, dossier)
        if intent is TurnIntent.REJECT:
            if state.insights:
                state.insights.pop()
            state.stage = ConsultationStage.HYPOTHESIS_VALIDATION
            return plan_validation(state, dossier)
        if intent is TurnIntent.QUESTION:
            return plan_insight_draft(state, dossier)
        return plan_insight_draft(state, dossier)
    if state.stage is ConsultationStage.ACTION_EXPERIMENT:
        if intent is TurnIntent.NEXT_TOPIC:
            state.free_cycle_complete = True
            topic_key, topics = _claim_topic(state, dossier, TurnIntent.NEXT_TOPIC)
            if not topics:
                state.stage = ConsultationStage.CLOSED
                return _build_close_plan(state, dossier)
            state.current_topic = topic_key
            state.stage = ConsultationStage.TOPIC_READY
            return plan_introduction(state, dossier)
        if intent is TurnIntent.CLOSE:
            state.stage = ConsultationStage.CLOSED
            return _build_close_plan(state, dossier)
        if intent is TurnIntent.CONFIRM:
            state.stage = ConsultationStage.CLOSED
            return _build_close_plan(state, dossier)
        return plan_action(state, dossier)
    return plan_introduction(state, dossier)


def _plan_unmatched_question(
    state: ConsultationState, dossier: SpiritDossier, text: str
) -> TurnPlan:
    """When the user asks something that doesn't match any dossier topic.

    The engine must NOT pretend to answer predictive questions ("will I win?")
    or give medical/legal advice. It should acknowledge the question, connect
    to whatever structural evidence is currently available, and invite the
    user to pick a topic that the engine CAN structure around.
    """
    # Pick the highest-importance evidence across all topics the user
    # hasn't denied, as fallback context.
    available = [
        e for e in dossier.evidence
        if e.evidence_id not in state.denied_evidence_ids
    ]
    available.sort(key=lambda e: e.importance, reverse=True)
    context = available[:3]

    topic_hints = "、".join(
        dossier.topic_by_key().get(k, StructureTopic(k, k, "", [], [], "")).title
        for k in dossier.topic_order[:5]
    )
    return TurnPlan(
        stage=state.stage,
        objective=(
            "用户问了一个具体的、但引擎无法直接给出是/否答案的问题。"
            "先承认你听懂了，再诚实地说星盘能看什么/不能看什么（不能预测输赢、不能做医疗/投资建议），"
            "然后把问题跟你已有的星盘结构挂钩——如果有相关的宫位或相位证据，就用它们来解释可能的影响方向"
        ),
        topic_key=state.current_topic,
        evidence=context,
        interpretation_options=[
            "这个问题可以从你星盘里这几个角度去看，但不会得出一个确定的输赢答案",
            "如果只看相关结构，它可能表现为一种倾向或概率方向——但这是倾向，不是结论",
        ],
        question="你更想聊哪个方面：是" + topic_hints + "？",
        fallback_text=(
            "这是个好问题，但星盘没有办法直接回答'能不能赢'这样的预测性问题——"
            "它只能告诉你相关的结构和倾向，帮你看清自己的模式。"
            "你现在想从哪个结构开始聊？"
        ),
        actions=[TurnIntent.CONTINUE, TurnIntent.DEEPEN, TurnIntent.NEXT_TOPIC],
    )


def _build_pause_plan(state: ConsultationState, dossier: SpiritDossier) -> TurnPlan:
    return TurnPlan(
        stage=ConsultationStage.PAUSED,
        objective="保存进度并暂停",
        topic_key=state.current_topic,
        evidence=[],
        interpretation_options=[],
        question="需要我等你，还是先记一笔，下次回来继续？",
        fallback_text="好的，先把这部分保存下来。下次回来时我会记得我们停在哪里。",
        actions=[TurnIntent.RESUME, TurnIntent.CLOSE],
    )


def _build_close_plan(state: ConsultationState, dossier: SpiritDossier) -> TurnPlan:
    state.stage = ConsultationStage.CLOSED
    return TurnPlan(
        stage=ConsultationStage.CLOSED,
        objective="温和地收束并指出下一步",
        topic_key=state.current_topic,
        evidence=[],
        interpretation_options=[],
        question="需要把今天的确认写进日记里吗？",
        fallback_text="今天我们走到了这里。你确认下来的几条洞察，已经在星灵日记和报告里等着你。",
        actions=[TurnIntent.CLOSE],
    )


_NO_EXPERIENCE_WORDS = (
    "想不到", "想不出", "不知道", "没有", "没什么", "不清楚",
    "好像没有", "没注意", "说不出来", "想不起来", "不记得",
    "没想过", "还好吧", "还行", "一般般", "没感觉",
    "不太清楚", "没啥", "想不太到", "想不出来", "想不到什么",
)


def _is_no_experience(text: str) -> bool:
    return any(w in text for w in _NO_EXPERIENCE_WORDS) and len(text) < 50


def _update_anchor(anchor: ExperienceAnchor, text: str) -> ExperienceAnchor:
    if not text:
        return anchor
    if not anchor.situation:
        anchor.situation = text[:240]
    elif not anchor.response:
        anchor.response = text[:240]
    elif not anchor.outcome:
        anchor.outcome = text[:240]
    else:
        anchor.recurrence = text[:240]
    return anchor


def mark_topic_completed(state: ConsultationState, topic_key: str) -> None:
    _mark_topic_progress(state, topic_key)


def apply_decision(
    state: ConsultationState,
    insight_id: str,
    decision: str,
    edited_user_quote: str = "",
    request_id: str = "",
) -> ConfirmedInsight | None:
    """Materialize the decision made on a draft insight (confirm/partial/reject/uncertain)."""
    insight = next((item for item in state.insights if item.insight_id == insight_id), None)
    if insight is None:
        return None
    if edited_user_quote:
        insight.user_quote = edited_user_quote
    if decision == ValidationStatus.CONFIRMED.value:
        insight.validation_status = ValidationStatus.CONFIRMED
        return insight
    if decision == ValidationStatus.PARTIAL.value:
        insight.validation_status = ValidationStatus.PARTIAL
        return insight
    if decision == ValidationStatus.UNCERTAIN.value:
        insight.validation_status = ValidationStatus.UNCERTAIN
        return insight
    if decision == ValidationStatus.REJECTED.value:
        insight.validation_status = ValidationStatus.REJECTED
        state.insights = [item for item in state.insights if item.insight_id != insight_id]
        return None
    return None


def projections_for_report(state: ConsultationState) -> dict[str, list[dict[str, Any]]]:
    """Map confirmed/partial insights onto planets and domains for the report overlay."""
    grouped: dict[str, list[dict[str, Any]]] = {}
    for item in state.insights:
        if item.validation_status not in {
            ValidationStatus.CONFIRMED,
            ValidationStatus.PARTIAL,
        }:
            continue
        planet_group = grouped.setdefault(item.planet, [])
        planet_group.append(
            {
                "topic_key": item.topic_key,
                "summary": item.summary,
                "user_quote": item.user_quote,
                "domain_tags": item.domain_tags,
                "evidence_ids": item.evidence_ids,
                "validation": item.validation_status.value,
            }
        )
    return grouped
