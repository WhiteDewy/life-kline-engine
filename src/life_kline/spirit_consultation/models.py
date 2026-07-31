"""Data contracts for rule-driven star-spirit consultations."""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class EvidenceSource(str, Enum):
    NATAL_PLACEMENT = "natal_placement"
    NATAL_DIGNITY = "natal_dignity"
    NATAL_RULERSHIP = "natal_rulership"
    NATAL_FLYSTAR = "natal_flystar"
    NATAL_ASPECT = "natal_aspect"
    NATAL_RECEPTION = "natal_reception"
    FIRDARIA = "firdaria"
    TODAY_ACTIVATION = "today_activation"
    DOMAIN_REPORT = "domain_report"


class ConsultationStage(str, Enum):
    INTRODUCTION = "introduction"
    TOPIC_READY = "topic_ready"
    STRUCTURE_EXPLAINING = "structure_explaining"
    EXPERIENCE_INQUIRY = "experience_inquiry"
    HYPOTHESIS_VALIDATION = "hypothesis_validation"
    INSIGHT_DRAFT = "insight_draft"
    ACTION_EXPERIMENT = "action_experiment"
    PAUSED = "paused"
    CLOSED = "closed"


class TurnIntent(str, Enum):
    CONTINUE = "continue"
    DEEPEN = "deepen"
    NEXT_TOPIC = "next_topic"
    PAUSE = "pause"
    RESUME = "resume"
    QUESTION = "question"
    CONFIRM = "confirm"
    PARTIAL = "partial"
    REJECT = "reject"
    UNCERTAIN = "uncertain"
    CLOSE = "close"
    NO_EXPERIENCE = "no_experience"
    SWITCH_TOPIC = "switch_topic"


class ValidationStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PARTIAL = "partial"
    REJECTED = "rejected"
    UNCERTAIN = "uncertain"


@dataclass(frozen=True)
class ChartEvidence:
    evidence_id: str
    source: EvidenceSource
    title: str
    fact: str
    payload: dict[str, Any] = field(default_factory=dict)
    importance: int = 50
    current: bool = False
    supportive: bool | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["source"] = self.source.value
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ChartEvidence:
        return cls(
            evidence_id=str(data.get("evidence_id", "")),
            source=EvidenceSource(data.get("source", EvidenceSource.NATAL_PLACEMENT.value)),
            title=str(data.get("title", "")),
            fact=str(data.get("fact", "")),
            payload=dict(data.get("payload") or {}),
            importance=int(data.get("importance", 50)),
            current=bool(data.get("current", False)),
            supportive=data.get("supportive"),
        )


@dataclass(frozen=True)
class StructureTopic:
    key: str
    title: str
    summary: str
    evidence_ids: list[str]
    interpretation_options: list[str]
    inquiry_question: str
    domain_tags: list[str] = field(default_factory=list)
    subtopic_keys: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StructureTopic:
        return cls(
            key=str(data.get("key", "")),
            title=str(data.get("title", "")),
            summary=str(data.get("summary", "")),
            evidence_ids=list(data.get("evidence_ids") or []),
            interpretation_options=list(data.get("interpretation_options") or []),
            inquiry_question=str(data.get("inquiry_question", "")),
            domain_tags=list(data.get("domain_tags") or []),
            subtopic_keys=list(data.get("subtopic_keys") or []),
        )


@dataclass(frozen=True)
class SpiritDossier:
    planet: str
    spirit_name: str
    archetype: str
    identity_statement: str
    profile: dict[str, Any]
    evidence: list[ChartEvidence]
    topics: list[StructureTopic]
    topic_order: list[str]
    entry_mode: str = "natal"
    today_trigger_type: str = ""

    def evidence_by_id(self) -> dict[str, ChartEvidence]:
        return {item.evidence_id: item for item in self.evidence}

    def topic_by_key(self) -> dict[str, StructureTopic]:
        return {item.key: item for item in self.topics}

    def to_dict(self) -> dict[str, Any]:
        return {
            "planet": self.planet,
            "spirit_name": self.spirit_name,
            "archetype": self.archetype,
            "identity_statement": self.identity_statement,
            "profile": self.profile,
            "evidence": [item.to_dict() for item in self.evidence],
            "topics": [item.to_dict() for item in self.topics],
            "topic_order": self.topic_order,
            "entry_mode": self.entry_mode,
            "today_trigger_type": self.today_trigger_type,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SpiritDossier:
        return cls(
            planet=str(data.get("planet", "MOON")),
            spirit_name=str(data.get("spirit_name", "月亮")),
            archetype=str(data.get("archetype", "")),
            identity_statement=str(data.get("identity_statement", "")),
            profile=dict(data.get("profile") or {}),
            evidence=[ChartEvidence.from_dict(item) for item in data.get("evidence") or []],
            topics=[StructureTopic.from_dict(item) for item in data.get("topics") or []],
            topic_order=list(data.get("topic_order") or []),
            entry_mode=str(data.get("entry_mode", "natal")),
            today_trigger_type=str(data.get("today_trigger_type", "")),
        )


@dataclass
class ExperienceAnchor:
    situation: str = ""
    people: list[str] = field(default_factory=list)
    trigger: str = ""
    body_or_emotion: str = ""
    response: str = ""
    outcome: str = ""
    recurrence: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> ExperienceAnchor:
        source = data or {}
        return cls(
            situation=str(source.get("situation", "")),
            people=list(source.get("people") or []),
            trigger=str(source.get("trigger", "")),
            body_or_emotion=str(source.get("body_or_emotion", "")),
            response=str(source.get("response", "")),
            outcome=str(source.get("outcome", "")),
            recurrence=str(source.get("recurrence", "")),
        )


@dataclass
class ConsultationHypothesis:
    hypothesis_id: str
    topic_key: str
    evidence_ids: list[str]
    statement: str
    alternatives: list[str]
    user_quote: str = ""
    validation_status: ValidationStatus = ValidationStatus.PENDING

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["validation_status"] = self.validation_status.value
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ConsultationHypothesis:
        return cls(
            hypothesis_id=str(data.get("hypothesis_id", "")),
            topic_key=str(data.get("topic_key", "")),
            evidence_ids=list(data.get("evidence_ids") or []),
            statement=str(data.get("statement", "")),
            alternatives=list(data.get("alternatives") or []),
            user_quote=str(data.get("user_quote", "")),
            validation_status=ValidationStatus(
                data.get("validation_status", ValidationStatus.PENDING.value)
            ),
        )


@dataclass
class ConfirmedInsight:
    insight_id: str
    hypothesis_id: str
    planet: str
    topic_key: str
    evidence_ids: list[str]
    user_quote: str
    summary: str
    domain_tags: list[str]
    growth_action: str
    validation_status: ValidationStatus = ValidationStatus.CONFIRMED

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["validation_status"] = self.validation_status.value
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ConfirmedInsight:
        return cls(
            insight_id=str(data.get("insight_id", "")),
            hypothesis_id=str(data.get("hypothesis_id", "")),
            planet=str(data.get("planet", "")),
            topic_key=str(data.get("topic_key", "")),
            evidence_ids=list(data.get("evidence_ids") or []),
            user_quote=str(data.get("user_quote", "")),
            summary=str(data.get("summary", "")),
            domain_tags=list(data.get("domain_tags") or []),
            growth_action=str(data.get("growth_action", "")),
            validation_status=ValidationStatus(
                data.get("validation_status", ValidationStatus.CONFIRMED.value)
            ),
        )


@dataclass
class ConsultationState:
    session_id: str
    report_id: str
    planet: str
    stage: ConsultationStage
    topic_queue: list[str]
    current_topic: str = ""
    topic_stack: list[str] = field(default_factory=list)
    completed_topics: list[str] = field(default_factory=list)
    evidence_used: list[str] = field(default_factory=list)
    denied_evidence_ids: list[str] = field(default_factory=list)
    turn_count: int = 0
    version: int = 1
    guided_mode: bool = True
    free_cycle_complete: bool = False
    experience_anchor: ExperienceAnchor = field(default_factory=ExperienceAnchor)
    hypotheses: list[ConsultationHypothesis] = field(default_factory=list)
    insights: list[ConfirmedInsight] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""

    def current_hypothesis(self) -> ConsultationHypothesis | None:
        return next(
            (
                item
                for item in reversed(self.hypotheses)
                if item.validation_status
                in {ValidationStatus.PENDING, ValidationStatus.CONFIRMED}
            ),
            None,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "report_id": self.report_id,
            "planet": self.planet,
            "stage": self.stage.value,
            "topic_queue": self.topic_queue,
            "current_topic": self.current_topic,
            "topic_stack": self.topic_stack,
            "completed_topics": self.completed_topics,
            "evidence_used": self.evidence_used,
            "denied_evidence_ids": self.denied_evidence_ids,
            "turn_count": self.turn_count,
            "version": self.version,
            "guided_mode": self.guided_mode,
            "free_cycle_complete": self.free_cycle_complete,
            "experience_anchor": self.experience_anchor.to_dict(),
            "hypotheses": [item.to_dict() for item in self.hypotheses],
            "insights": [item.to_dict() for item in self.insights],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ConsultationState:
        return cls(
            session_id=str(data.get("session_id", "")),
            report_id=str(data.get("report_id", "")),
            planet=str(data.get("planet", "MOON")),
            stage=ConsultationStage(data.get("stage", ConsultationStage.INTRODUCTION.value)),
            topic_queue=list(data.get("topic_queue") or []),
            current_topic=str(data.get("current_topic", "")),
            topic_stack=list(data.get("topic_stack") or []),
            completed_topics=list(data.get("completed_topics") or []),
            evidence_used=list(data.get("evidence_used") or []),
            denied_evidence_ids=list(data.get("denied_evidence_ids") or []),
            turn_count=int(data.get("turn_count", 0)),
            version=int(data.get("version", 1)),
            guided_mode=bool(data.get("guided_mode", True)),
            free_cycle_complete=bool(data.get("free_cycle_complete", False)),
            experience_anchor=ExperienceAnchor.from_dict(data.get("experience_anchor")),
            hypotheses=[
                ConsultationHypothesis.from_dict(item)
                for item in data.get("hypotheses") or []
            ],
            insights=[ConfirmedInsight.from_dict(item) for item in data.get("insights") or []],
            created_at=str(data.get("created_at", "")),
            updated_at=str(data.get("updated_at", "")),
        )


@dataclass
class TurnPlan:
    stage: ConsultationStage
    objective: str
    topic_key: str
    evidence: list[ChartEvidence]
    interpretation_options: list[str]
    question: str
    fallback_text: str
    actions: list[TurnIntent]
    hypothesis: ConsultationHypothesis | None = None
    insight_draft: ConfirmedInsight | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage": self.stage.value,
            "objective": self.objective,
            "topic_key": self.topic_key,
            "evidence": [item.to_dict() for item in self.evidence],
            "interpretation_options": self.interpretation_options,
            "question": self.question,
            "fallback_text": self.fallback_text,
            "actions": [item.value for item in self.actions],
            "hypothesis": self.hypothesis.to_dict() if self.hypothesis else None,
            "insight_draft": self.insight_draft.to_dict() if self.insight_draft else None,
        }


def stable_evidence_id(source: EvidenceSource, payload: dict[str, Any]) -> str:
    raw = json.dumps(
        {"source": source.value, "payload": payload},
        ensure_ascii=False,
        sort_keys=True,
        default=str,
        separators=(",", ":"),
    )
    return f"ev_{hashlib.sha256(raw.encode('utf-8')).hexdigest()[:16]}"


def stable_object_id(prefix: str, *parts: str) -> str:
    raw = "|".join(parts)
    return f"{prefix}_{hashlib.sha256(raw.encode('utf-8')).hexdigest()[:16]}"
