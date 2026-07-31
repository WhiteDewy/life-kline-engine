"""Unit tests for the spirit_consultation domain package."""
from __future__ import annotations

import pytest

from life_kline.spirit_consultation import (
    ConsultationStage,
    SpiritDossier,
    TurnIntent,
    apply_decision,
    build_spirit_dossier,
    initial_state,
    match_topic,
    projections_for_report,
    render,
    resolve_turn,
)
from life_kline.spirit_consultation.fallback_renderer import render as render_fallback
from life_kline.spirit_consultation.state_machine import _open_hypothesis
from life_kline.spirit_consultation.models import ValidationStatus


def _planet_payload(planet: str, *, house: int, sign: str, dignity: str = "peregrine") -> dict:
    return {
        "house": house,
        "sign": sign,
        "sign_label": {"ARIES": "白羊座", "TAURUS": "金牛座", "CANCER": "巨蟹座",
                       "LEO": "狮子座", "LIBRA": "天秤座", "SCORPIO": "天蝎座",
                       "SAGITTARIUS": "射手座", "CAPRICORN": "摩羯座",
                       "AQUARIUS": "水瓶座", "PISCES": "双鱼座"}.get(sign, sign),
        "house_label": {1: "自我与身体", 2: "财务与价值", 3: "沟通与学习", 4: "家庭与根基",
                          5: "创造与恋爱", 6: "工作与日常", 7: "关系与合作", 8: "共享与转化",
                          9: "远方与信念", 10: "事业与责任", 11: "团体与愿景",
                          12: "灵性与隐退"}.get(house, f"第{house}宫"),
        "dignity_code": dignity,
        "dignity_label": {"domicile": "入庙", "exaltation": "擢升",
                            "peregrine": "平常", "detriment": "失势",
                            "fall": "落陷"}.get(dignity, "平常"),
        "is_chart_ruler": False,
        "role_tag": "天赋维度",
        "core_strength": 75,
        "linked_domains": ["romance", "self"],
        "persona": {"name_zh": "金星", "archetype_zh": "调和者", "symbol": "♀"},
    }


def _report_data() -> dict:
    return {
        "user_info": {"is_day_chart": True, "birth_time_local": "1990-01-01T08:00:00"},
        "natal_chart": {
            "major_aspects": [
                {"title": "金星刑海王星", "nature": "challenging", "strength": 0.6,
                 "summary": "金星在关系中容易出现理想化与现实落差"}
            ]
        },
        "advanced_patterns": {
            "ruler_groups": [
                {"ruler": "VENUS", "houses": [2, 7], "house_titles": ["财务与价值", "关系与合作"],
                 "ruler_house": 5, "ruler_house_title": "创造与恋爱",
                 "dignity": "peregrine", "dignity_label": "平常",
                 "notation": "R2/R7 → 5", "line": "金星掌管 2/7 宫，从 5 宫发力"},
            ],
            "house_rulers": [
                {"ruler": "VENUS", "house": 2, "title": "财务与价值",
                 "ruler_house": 5, "ruler_house_title": "创造与恋爱",
                 "notation": "R2 → 5", "line": "第 2 宫主星飞入第 5 宫",
                 "flight_summary": "价值感经由创造与恋爱表达",
                 "flight_tone": "中性", "flight_positive": "创造带来收入",
                 "flight_negative": "感情用钱填补", "flight_note": "留意过度付出",
                 "fortune_level": "neutral", "fortune_score": 50,
                 "summary": "中性", "recommendation": "保持节律"},
                {"ruler": "VENUS", "house": 7, "title": "关系与合作",
                 "ruler_house": 5, "ruler_house_title": "创造与恋爱",
                 "notation": "R7 → 5", "line": "第 7 宫主星飞入第 5 宫",
                 "flight_summary": "关系为创造提供舞台",
                 "flight_tone": "得吉", "flight_positive": "合作激发灵感",
                 "flight_negative": "创作被关系牵动", "flight_note": "注意边界",
                 "fortune_level": "fortunate", "fortune_score": 75,
                 "summary": "得吉", "recommendation": "顺势表达"},
            ],
            "flystar_fortunes": {
                "2R->5": {"fortune_level": "neutral", "fortune_score": 50,
                            "summary": "中性", "recommendation": "保持节律"},
                "7R->5": {"fortune_level": "fortunate", "fortune_score": 75,
                            "summary": "得吉", "recommendation": "顺势表达"},
            },
            "reception_groups": [],
            "mutual_receptions": [{"pair": ["VENUS", "MARS"], "line": "金星与火星互溶",
                                    "summary": "情感与行动彼此支持",
                                    "labels": ["金星", "火星"]}],
        },
        "domains": {
            "romance": {"core_theme": "通过共创建立长期关系", "structure": "", "psychology": "", "suggestion": ""},
            "self": {"core_theme": "以创造表达自我价值", "structure": "", "psychology": "", "suggestion": ""},
        },
        "planet_characters": {
            "planet_characters": {
                "VENUS": _planet_payload("VENUS", house=5, sign="LIBRA", dignity="domicile"),
                "MARS": _planet_payload("MARS", house=1, sign="ARIES", dignity="domicile"),
                "MOON": _planet_payload("MOON", house=4, sign="CANCER", dignity="domicile"),
            }
        },
    }


@pytest.fixture
def dossier() -> SpiritDossier:
    return build_spirit_dossier(_report_data(), "VENUS")


def test_dossier_collects_all_fact_layers(dossier: SpiritDossier) -> None:
    titles = {item.title for item in dossier.evidence}
    assert "落座与落宫" in titles
    assert "力量状态" in titles
    assert "掌宫" in titles
    assert "飞星链" in titles
    assert "主要相位" in titles
    assert "互溶接纳" in titles
    assert "性格底色" in titles or "桃花感情" in titles
    assert any(item.current for item in dossier.evidence) is False
    assert dossier.entry_mode in {"today", "natal"}


def test_dossier_today_mode_promotes_timing_topic() -> None:
    today = {
        "planet": "VENUS", "planet_label": "金星", "symbol": "♀",
        "reason": "行运金星合相你的本命太阳", "confidence": 90.0,
        "sign": "LIBRA", "sign_label": "天秤座",
        "trigger_type": "exact_transit",
        "trigger_evidence": [],
        "transit_aspect": {"transiting_planet": "VENUS", "natal_planet": "SUN",
                            "aspect_type": "CONJUNCTION", "orb": 0.3},
    }
    data = _report_data()
    dossier = build_spirit_dossier(data, "VENUS", today_spirit=today)
    assert dossier.entry_mode == "today"
    assert "timing" in dossier.topic_order
    assert dossier.topic_order[0] == "timing"


def test_initial_state_starts_with_first_topic(dossier: SpiritDossier) -> None:
    state = initial_state("rep_test", "VENUS", dossier)
    assert state.stage is ConsultationStage.INTRODUCTION
    assert state.current_topic in dossier.topic_order
    assert state.turn_count == 0
    assert state.version == 1


def test_intent_recognition_advances_state(dossier: SpiritDossier) -> None:
    state = initial_state("rep_test", "VENUS", dossier)
    plan = resolve_turn(state, dossier, "")
    assert plan.stage is ConsultationStage.INTRODUCTION
    plan = resolve_turn(state, dossier, "我们先聊聊落宫吧")
    assert plan.stage is ConsultationStage.STRUCTURE_EXPLAINING
    plan = resolve_turn(state, dossier, "上周和伴侣在餐厅起冲突")
    assert plan.stage is ConsultationStage.HYPOTHESIS_VALIDATION
    state.experience_anchor.situation = "餐厅冲突"
    state.experience_anchor.response = "我忍住不说话"
    state.experience_anchor.outcome = "对方也没说话"
    plan = resolve_turn(state, dossier, "对，我就是这样")
    assert plan.stage is ConsultationStage.INSIGHT_DRAFT
    assert state.insights, "confirmed insight should be recorded"
    plan = resolve_turn(state, dossier, "下次我先留意身体再决定")
    assert plan.stage is ConsultationStage.ACTION_EXPERIMENT
    plan = resolve_turn(state, dossier, "下一个话题")
    assert state.free_cycle_complete is True
    assert plan.stage in {
        ConsultationStage.INTRODUCTION,
        ConsultationStage.STRUCTURE_EXPLAINING,
        ConsultationStage.CLOSED,
    }


def test_reject_blocks_evidence_and_does_not_repeat(dossier: SpiritDossier) -> None:
    state = initial_state("rep_test", "VENUS", dossier)
    state.stage = ConsultationStage.HYPOTHESIS_VALIDATION
    _open_hypothesis(state, dossier, dossier.topic_by_key()[state.current_topic], "对照前一段")
    rulership_evidence = [
        item.evidence_id
        for item in dossier.evidence
        if item.source.value == "natal_rulership"
    ]
    state.current_hypothesis().evidence_ids = rulership_evidence
    plan = resolve_turn(state, dossier, "不太像")
    assert plan.stage is ConsultationStage.STRUCTURE_EXPLAINING
    denied = list(state.denied_evidence_ids)
    assert denied, "reject must record denied evidence"
    plan = resolve_turn(state, dossier, "展开讲讲这个")
    rerun_evidence_ids = {item.evidence_id for item in plan.evidence}
    assert rerun_evidence_ids.isdisjoint(set(denied))


def test_pause_and_resume_keeps_state(dossier: SpiritDossier) -> None:
    state = initial_state("rep_test", "VENUS", dossier)
    plan = resolve_turn(state, dossier, "暂停")
    assert plan.stage is ConsultationStage.PAUSED
    plan = resolve_turn(state, dossier, "我们继续")
    assert plan.stage is ConsultationStage.INTRODUCTION


def test_match_topic_routes_questions() -> None:
    today = {
        "planet": "VENUS", "planet_label": "金星", "symbol": "♀",
        "reason": "行运金星合相你的本命太阳", "confidence": 90.0,
        "sign": "LIBRA", "sign_label": "天秤座",
        "trigger_type": "exact_transit",
        "trigger_evidence": [],
    }
    dossier = build_spirit_dossier(_report_data(), "VENUS", today_spirit=today)
    assert "timing" in dossier.topic_order
    assert match_topic(dossier, "我的金星掌管哪几个宫") == "rulership"
    assert match_topic(dossier, "今天金星有没有被行运触发") == "timing"
    assert match_topic(dossier, "我和伴侣的关系") == "domains"
    assert match_topic(dossier, "") == ""


def test_apply_decision_confirms_insight(dossier: SpiritDossier) -> None:
    state = initial_state("rep_test", "VENUS", dossier)
    state.stage = ConsultationStage.HYPOTHESIS_VALIDATION
    _open_hypothesis(state, dossier, dossier.topic_by_key()[state.current_topic], "对照前一段")
    plan = resolve_turn(state, dossier, "对，是这样")
    assert plan.insight_draft is not None
    insight = state.insights[-1]
    confirmed = apply_decision(state, insight.insight_id, "confirmed", edited_user_quote="我经常")
    assert confirmed is not None
    assert confirmed.validation_status is ValidationStatus.CONFIRMED
    grouped = projections_for_report(state)
    assert "VENUS" in grouped


def test_apply_decision_reject_removes_insight(dossier: SpiritDossier) -> None:
    state = initial_state("rep_test", "VENUS", dossier)
    state.stage = ConsultationStage.HYPOTHESIS_VALIDATION
    _open_hypothesis(state, dossier, dossier.topic_by_key()[state.current_topic], "对照前一段")
    plan = resolve_turn(state, dossier, "对，是这样")
    assert plan.insight_draft is not None
    insight = state.insights[-1]
    apply_decision(state, insight.insight_id, "rejected")
    assert all(item.insight_id != insight.insight_id for item in state.insights)


def test_fallback_renderer_uses_only_evidence(dossier: SpiritDossier) -> None:
    state = initial_state("rep_test", "VENUS", dossier)
    plan = resolve_turn(state, dossier, "")
    text = render(plan)
    assert "星盘" in text or "星图" in text
    plan = resolve_turn(state, dossier, "聊一聊飞星吧")
    plan.stage = ConsultationStage.STRUCTURE_EXPLAINING  # type: ignore[misc]
    text = render_fallback(plan)
    for fact in {item.fact for item in plan.evidence[:1]}:
        assert any(word in text for word in fact)


def test_hypotheses_carry_user_quote(dossier: SpiritDossier) -> None:
    state = initial_state("rep_test", "VENUS", dossier)
    state.stage = ConsultationStage.STRUCTURE_EXPLAINING
    resolve_turn(state, dossier, "我和伴侣在餐厅起冲突")
    state.experience_anchor.situation = "餐厅冲突"
    state.experience_anchor.response = "我忍住不说话"
    state.experience_anchor.outcome = "对方也没说话"
    plan = resolve_turn(state, dossier, "我会先在脑内演完一整部剧")
    assert plan.stage is ConsultationStage.HYPOTHESIS_VALIDATION
    plan = resolve_turn(state, dossier, "对，我就是这样")
    assert plan.stage is ConsultationStage.INSIGHT_DRAFT
    assert plan.insight_draft is not None
    assert "餐厅" in plan.insight_draft.summary or "我忍住" in plan.insight_draft.summary
