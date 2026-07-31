"""Pure engine for the star-spirit consultation loop.

The package contains:

* :mod:`models` — data contracts that separate chart evidence, hypotheses, the
  consultation state machine and the per-turn plan.
* :mod:`dossier` — build a complete topic map for one planet by reusing the
  existing :class:`ChartReader`; no LLM and no hard-coded people.
* :mod:`state_machine` — event-driven transitions that decide the next
  ``TurnPlan`` and which evidence may surface.
* :mod:`fallback_renderer` — deterministic text per turn so the consultation
  micro-cycle keeps working without the LLM.
"""
from .dossier import build_spirit_dossier, match_topic
from .fallback_renderer import render
from .models import (
    ChartEvidence,
    ConfirmedInsight,
    ConsultationHypothesis,
    ConsultationStage,
    ConsultationState,
    EvidenceSource,
    ExperienceAnchor,
    SpiritDossier,
    StructureTopic,
    TurnIntent,
    TurnPlan,
    ValidationStatus,
)
from .state_machine import (
    apply_decision,
    initial_state,
    plan_introduction,
    projections_for_report,
    resolve_turn,
)

__all__ = [
    "ChartEvidence",
    "ConfirmedInsight",
    "ConsultationHypothesis",
    "ConsultationStage",
    "ConsultationState",
    "EvidenceSource",
    "ExperienceAnchor",
    "SpiritDossier",
    "StructureTopic",
    "TurnIntent",
    "TurnPlan",
    "ValidationStatus",
    "apply_decision",
    "build_spirit_dossier",
    "initial_state",
    "match_topic",
    "plan_introduction",
    "projections_for_report",
    "render",
    "resolve_turn",
]
