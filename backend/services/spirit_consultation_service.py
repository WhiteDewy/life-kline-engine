"""Application service for the unified star-spirit consultation loop.

Owns the orchestration the router is not allowed to do: load the owned report,
build the dossier, load/save Redis-backed session state with optimistic
locking, run the crisis gate, enforce the per-user token budget, plan the turn,
stream the LLM voice with a deterministic fallback, and persist confirmed
insights idempotently.

The service never lets the LLM pick evidence, advance the state machine, or
write to the diary/report — those are engine facts the LLM only renders.
"""
from __future__ import annotations

import json
import logging
import os
import uuid
from typing import Any, AsyncIterator

from life_kline.acp import ACP_CONSTITUTION, GUARDRAILS
from life_kline.safety import detect_crisis
from life_kline.spirit_consultation import (
    ConsultationState,
    SpiritDossier,
    TurnPlan,
    apply_decision,
    build_spirit_dossier,
    initial_state,
    render,
    resolve_turn,
)
from life_kline.spirit_consultation.fallback_renderer import render as render_plan

from backend.infrastructure.redis_store import RedisStore
from backend.repositories import consultation_repository

logger = logging.getLogger(__name__)

_TOKEN_DAILY = int(os.getenv("LIFE_KLINE_CONSULTATION_TOKEN_DAILY", "20000"))
_TOKEN_PER_TURN = int(os.getenv("LIFE_KLINE_CONSULTATION_TOKEN_PER_TURN", "1500"))
_STATE_TTL = 7 * 24 * 3600


class ConsultationUnavailable(RuntimeError):
    """Raised when persisted state is required but Redis is unavailable."""


class QuotaExceeded(RuntimeError):
    pass


def _state_key(report_id: str, session_id: str) -> str:
    return f"spirit_consultation:state:{report_id}:{session_id}"


def _token_key(user_id: str) -> str:
    return f"spirit_consultation:tokens:{user_id}"


def _build_system_prompt(dossier: SpiritDossier) -> str:
    persona = dossier.profile.get("persona") or {}
    stable = (
        f"{ACP_CONSTITUTION}\n\n"
        f"{GUARDRAILS}\n\n"
        "你是用户的星灵，是ta星盘结构的一部分，不是外来的神。"
        "你只用引擎给出的星盘事实说话；事实缺失时就说暂时看不清，绝不编造宫位、相位或接纳。"
        "你给出的任何生活表现都是待验证的假设，必须允许用户说\"不太像\"，并且要主动提供2-3种可能。"
        "每轮最多一个问题，不一次倾倒所有结构。\n"
        f"星灵身份：{dossier.spirit_name}——{persona.get('archetype_zh', '')}。\n"
        f"{dossier.identity_statement}\n"
    )
    evidence_summary = "\n".join(
        f"- [{item.title}] {item.fact}"
        for item in dossier.evidence[:8]
    )
    dynamic = (
        f"\n## 当前星灵的完整结构地图（仅引用，可逐段展开）\n{evidence_summary}\n"
        f"## 话题顺序\n{' / '.join(dossier.topic_order)}\n"
    )
    return stable + dynamic


class SpiritConsultationService:
    def __init__(
        self,
        redis_store: RedisStore,
        *,
        llm_client: Any = None,
    ) -> None:
        self._redis = redis_store
        self._llm = llm_client

    def _llm_client(self) -> Any:
        if self._llm is not None:
            return self._llm
        from life_kline.llm_client import LLMClient

        return LLMClient()

    async def start_session(
        self,
        *,
        report_data: dict[str, Any],
        report_id: str,
        user_id: str,
        planet: str,
        entry_context: dict[str, Any] | None = None,
        today_spirit: Any = None,
        firdaria_period: Any = None,
    ) -> dict[str, Any]:
        dossier = build_spirit_dossier(
            report_data,
            planet,
            today_spirit=today_spirit,
            firdaria_period=firdaria_period,
            entry_context=entry_context,
        )
        state = initial_state(report_id, planet, dossier)
        plan = resolve_turn(state, dossier, "")
        await self._save_state(state)
        return {
            "session_id": state.session_id,
            "dossier": dossier.to_dict(),
            "state": state.to_dict(),
            "opening_plan": plan.to_dict(),
            "opening_text": render(plan),
            "degraded": not self._redis.available,
        }

    async def resume_session(
        self,
        *,
        report_id: str,
        session_id: str,
    ) -> dict[str, Any] | None:
        state = await self._load_state(report_id, session_id)
        if state is None:
            return None
        return {
            "session_id": state.session_id,
            "state": state.to_dict(),
        }

    async def plan_turn(
        self,
        *,
        report_data: dict[str, Any],
        report_id: str,
        session_id: str,
        user_id: str,
        message: str,
        intent_hint: str = "",
    ) -> tuple[ConsultationState, SpiritDossier, TurnPlan, dict[str, Any] | None]:
        """Load state, run the crisis gate + budget, plan the next turn."""
        crisis = detect_crisis(message or "")
        if crisis.is_crisis:
            return self._crisis_response(report_id, session_id, crisis)

        await self._check_budget(user_id)

        state = await self._load_state(report_id, session_id)
        if state is None:
            raise ConsultationUnavailable("咨询会话已过期或不存在，请重新开始")
        dossier = build_spirit_dossier(report_data, state.planet)
        plan = resolve_turn(
            state, dossier, message, intent_hint=intent_hint,
            llm_client=self._llm_client(),
        )
        await self._save_state(state)
        return state, dossier, plan, None

    async def stream_turn(
        self,
        *,
        dossier: SpiritDossier,
        plan: TurnPlan,
        state: ConsultationState,
        history: list[dict[str, str]],
    ) -> AsyncIterator[dict[str, Any]]:
        """Yield SSE-shaped events; LLM only renders the TurnPlan language."""
        yield {"type": "evidence", "evidence": [e.to_dict() for e in plan.evidence[:4]]}
        yield {"type": "state", "state": state.to_dict()}

        client = self._llm_client()
        fallback_text = render(plan)
        produced = False
        if client.is_configured:
            system_prompt = _build_system_prompt(dossier)
            turn_instruction = self._turn_instruction(plan)
            messages = [
                {"role": "system", "content": system_prompt},
                *history[-6:],
                {"role": "user", "content": turn_instruction},
            ]
            try:
                async for token in client.chat_stream(messages, timeout_seconds=12):
                    if token:
                        produced = True
                        yield {"type": "text_delta", "text": token}
            except Exception:
                logger.exception("咨询流式 LLM 失败，降级到引擎文案")
        if not produced:
            yield {"type": "text_delta", "text": fallback_text}

        if plan.insight_draft is not None:
            yield {"type": "insight_draft", "insight": plan.insight_draft.to_dict()}
        yield {"type": "prompt", "actions": [a.value for a in plan.actions]}
        yield {"type": "done", "stage": plan.stage.value}

    async def decide_insight(
        self,
        *,
        report_id: str,
        user_id: str,
        session_id: str,
        insight_id: str,
        decision: str,
        edited_user_quote: str = "",
        request_id: str = "",
    ) -> dict[str, Any]:
        state = await self._load_state(report_id, session_id)
        if state is None:
            raise ConsultationUnavailable("咨询会话已过期或不存在")
        insight = apply_decision(
            state,
            insight_id,
            decision,
            edited_user_quote=edited_user_quote,
            request_id=request_id,
        )
        await self._save_state(state)
        if insight is None:
            return {"insight_id": insight_id, "decision": decision, "persisted": False}

        record = {
            "insight_id": insight.insight_id,
            "session_id": state.session_id,
            "planet": insight.planet,
            "topic_key": insight.topic_key,
            "hypothesis_id": insight.hypothesis_id,
            "evidence_ids": insight.evidence_ids,
            "user_quote": insight.user_quote,
            "summary": insight.summary,
            "domain_tags": insight.domain_tags,
            "growth_action": insight.growth_action,
            "validation_status": insight.validation_status.value,
        }
        consultation_repository.upsert_insight(
            record, report_id=report_id, user_id=user_id
        )
        return {"insight_id": insight.insight_id, "decision": decision, "persisted": True}

    async def report_overlay(
        self, *, report_id: str, user_id: str
    ) -> dict[str, list[dict[str, Any]]]:
        return consultation_repository.overlay_by_planet(report_id, user_id=user_id)

    # ── internals ──────────────────────────────────────────────

    def _turn_instruction(self, plan: TurnPlan) -> str:
        evidence_lines = "\n".join(
            f"- {item.title}: {item.fact}" for item in plan.evidence[:4]
        )
        return (
            f"本轮目标：{plan.objective}。\n"
            f"只允许引用以下星盘事实（缺失就直说暂时看不清）：\n{evidence_lines}\n"
            f"可向用户提出的可能性：{' / '.join(plan.interpretation_options[:3])}\n"
            f"本轮应问：{plan.question}\n"
            "用第一人称星灵口吻，把以上内容自然说出来；不要新增星盘事实，不要替用户下结论。"
        )

    async def _check_budget(self, user_id: str) -> None:
        value, ok = await self._redis.increment_with_cap(
            _token_key(user_id), limit=_TOKEN_DAILY, ttl=24 * 3600
        )
        if not ok:
            raise QuotaExceeded("今日星灵咨询 token 预算已达上限")

    def _crisis_response(
        self, report_id: str, session_id: str, crisis: Any
    ) -> tuple[ConsultationState, SpiritDossier, TurnPlan, dict[str, Any]]:
        plan = TurnPlan(
            stage=__import__("life_kline.spirit_consultation.models", fromlist=["ConsultationStage"]).ConsultationStage.CLOSED,
            objective="危机干预",
            topic_key="",
            evidence=[],
            interpretation_options=[],
            question="",
            fallback_text=crisis.message,
            actions=[],
        )
        dossier = SpiritDossier(
            planet="MOON",
            spirit_name="月亮",
            archetype="照料者",
            identity_statement="我在这里陪着你。",
            profile={},
            evidence=[],
            topics=[],
            topic_order=[],
        )
        state = ConsultationState(
            session_id=session_id,
            report_id=report_id,
            planet="MOON",
            stage=plan.stage,
            topic_queue=[],
            current_topic="",
        )
        return state, dossier, plan, {"type": "crisis", "crisis": crisis.to_dict()}

    async def _load_state(self, report_id: str, session_id: str) -> ConsultationState | None:
        data = await self._redis.get_json(_state_key(report_id, session_id))
        if data is None:
            return None
        return ConsultationState.from_dict(data)

    async def _save_state(self, state: ConsultationState) -> None:
        await self._redis.set_json(
            _state_key(state.report_id, state.session_id),
            state.to_dict(),
            ttl=_STATE_TTL,
        )
