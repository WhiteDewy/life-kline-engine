from __future__ import annotations

import random

from life_kline.diary_engine import DiaryEngine
from life_kline.engine_astrologer import ConversationContext, VoiceRenderer
from life_kline.characters.spirit_triggers import PLANET_TRIGGERS, get_planet_trigger


def _reading() -> dict:
    return {
        "planet_in_house": {"planet_label": "金星", "sign_label": "天秤座", "house": 7},
        "domain": {"domain_label": "桃花感情", "core_theme": "关系需要平等", "suggestion": "先确认自己的边界"},
        "evidence": ["金星落天秤座第7宫"],
    }


def test_all_planets_have_complete_trigger_configuration():
    assert len(PLANET_TRIGGERS) == 10
    for trigger in PLANET_TRIGGERS.values():
        assert trigger.emotion_acks
        assert trigger.astro_entry_keywords
        assert trigger.proactive_topics
        assert "{suggestion}" in trigger.guidance_template
    assert get_planet_trigger("unknown") == PLANET_TRIGGERS["SUN"]


def test_first_turn_is_pure_emotional_acknowledgment():
    response = VoiceRenderer().render(
        {"primary_domain": "personal", "emotional_state": "anxious", "confidence": 0.3},
        _reading(), {"planet": "VENUS"}, "我今天有点烦", conversation_context=ConversationContext(),
    )
    assert response.acknowledgment
    assert response.mirroring == ""
    assert response.evidence == []
    assert "星盘" not in response.full_text
    assert "第7宫" not in response.full_text


def test_topic_enters_astrology_after_planet_delay():
    ctx = ConversationContext(turn_count=1)
    response = VoiceRenderer().render(
        {"primary_domain": "romance", "emotional_state": "curious", "confidence": 0.8},
        _reading(), {"planet": "VENUS"}, "我想聊聊感情关系", conversation_context=ctx,
    )
    assert "从你的星盘看" in response.mirroring
    assert response.evidence


def test_proactive_extension_after_deep_conversation(monkeypatch):
    monkeypatch.setattr(random, "random", lambda: 0.0)
    response = VoiceRenderer().render(
        {"primary_domain": "romance", "emotional_state": "curious", "confidence": 0.8},
        _reading(), {"planet": "VENUS"}, "感情让我困惑", conversation_context=ConversationContext(turn_count=2),
    )
    assert "下一步也可以聊聊" in response.full_text


def test_diary_prioritizes_user_messages_and_keeps_one_insight(tmp_path, monkeypatch):
    import life_kline.diary_engine as module
    monkeypatch.setattr(module, "_dao", None)
    entry = DiaryEngine(str(tmp_path)).extract_and_generate(
        "report-1", "旧的完整上下文不应覆盖新字段", "MOON",
        user_messages=["今天工作压力很大，我很疲惫。", "项目延期让我担心。"],
        spirit_responses=["我听见了。你可以先只做最重要的一件事。其余内容很长，不应全放进日记。"],
    )
    assert "今天你和" in entry.entry_text
    assert "工作压力很大" in entry.entry_text
    assert "你可以先只做最重要的一件事" in entry.entry_text
    assert "其余内容很长" not in entry.entry_text
