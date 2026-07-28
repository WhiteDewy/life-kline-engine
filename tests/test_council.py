"""
test_council.py — 星灵议会（Council）单元测试

覆盖：
- LLM 未配置 → 降级规则桩（保护现有行为）
- member system prompt 含 ACP 宪法 + 星盘事实 grounding
- mock LLM → 发言与合成来自 LLM
- 单颗行星 LLM 失败 → 该行星回退规则桩，其余仍来自 LLM

纯离线可跑，不依赖网络/真实 LLM。
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from life_kline.council import CouncilEngine
from life_kline.council.prompts import (
    build_council_member_system_prompt,
    ACP_CONSTITUTION,
)


# ──────────── fixture：最小 report_data ────────────

def _planet_profile(name_zh, archetype, sign, house, dignity, persona_extra=None):
    persona = {
        "name_zh": name_zh,
        "archetype_zh": archetype,
        "essence": f"{name_zh}的核心本质。",
        "personality": f"{name_zh}的性格描述。",
        "voice_tone": f"{name_zh}的语气。",
        "gift_to_user": f"{name_zh}给你的礼物。",
        "challenge_to_user": f"{name_zh}对你的挑战。",
        "advice_approach": f"{name_zh}的建议方式。",
    }
    if persona_extra:
        persona.update(persona_extra)
    return {
        "persona": persona,
        "sign_label": sign,
        "house": house,
        "dignity_label": dignity,
        "house_context": {"title": f"第{house}宫", "topic": "主题"},
    }


def _sample_report_data():
    profiles = {
        "SUN": _planet_profile("太阳", "主角", "狮子", 10, "庙旺"),
        "MOON": _planet_profile("月亮", "情感", "巨蟹", 4, "庙旺"),
        "MARS": _planet_profile("火星", "欲望", "白羊", 1, "庙旺"),
        "VENUS": _planet_profile("金星", "关系", "金牛", 2, "庙旺"),
        "SATURN": _planet_profile("土星", "建筑师", "摩羯", 10, "庙旺"),
    }
    natal_planets = {
        p: {
            "gift": f"{prof['persona']['name_zh']}的天赋",
            "shadow": f"{prof['persona']['name_zh']}的阴影",
            "strategy": f"{prof['persona']['name_zh']}的策略",
            "aspect_signature": [f"{prof['persona']['name_zh']} 合相 水星 1.0°"],
            "dignity_label": prof["dignity_label"],
        }
        for p, prof in profiles.items()
    }
    return {
        "planet_characters": {"planet_characters": profiles},
        "natal_chart": {"planets": natal_planets},
    }


# ──────────── fake LLM client ────────────

class _FakeLLM:
    """假 LLMClient：按行星返回固定发言；可控制某行星失败。"""

    def __init__(self, fail_planets: set[str] | None = None, configured=True):
        self._configured = configured
        self._fail = fail_planets or set()

    @property
    def is_configured(self) -> bool:
        return self._configured

    async def chat_async(self, system_prompt: str, user_message: str, history=None) -> str:
        # 主持人合成调用
        if "星灵议会系统" in system_prompt and "各行星的发言" in user_message:
            return "我听到你内心有不同的声音在拉扯，也许这就是你此刻的处境。"
        # 单颗行星发言调用：从 system_prompt 提取行星名
        for name in ("太阳", "月亮", "火星", "金星", "土星"):
            if f"**{name}**" in system_prompt:
                # 反查 planet key
                key = {"太阳": "SUN", "月亮": "MOON", "火星": "MARS",
                       "金星": "VENUS", "土星": "SATURN"}[name]
                if key in self._fail:
                    return ""
                return f"【LLM】{name}的发言"
        return ""


# ──────────── tests ────────────

def test_council_fallback_without_llm():
    """LLM 未配置 → 走规则桩，source=council_rule。"""
    report = _sample_report_data()
    engine = CouncilEngine(report, llm_client=_FakeLLM(configured=False))
    session = engine.create_session("想辞职但不敢跟领导说")

    import asyncio
    result = asyncio.run(
        engine.generate_council_response_async(session, "想辞职但不敢跟领导说")
    )
    assert result["source"] == "council_rule"
    assert result["statements"], "规则桩应产出非空发言"
    assert result["synthesis"], "规则桩应产出非空合成"
    print("✓ LLM 未配置降级规则桩")


def test_build_council_member_system_prompt_contains_acp_and_facts():
    """member system prompt 含 ACP 关键词 + 星盘事实 grounding。"""
    report = _sample_report_data()
    prompt = build_council_member_system_prompt(report, "SATURN")
    # ACP 宪法
    assert "自由意志" in prompt, "应包含 ACP 自由意志条款"
    assert "宿命" in prompt, "应包含 ACP 宿命禁令"
    # persona 正文
    assert "土星" in prompt
    assert "建筑师" in prompt
    # grounding 事实
    assert "庙旺" in prompt, "应包含 dignity 事实"
    assert "土星的天赋" in prompt, "应包含 gift 事实"
    assert "合相" in prompt, "应包含 aspect_signature 事实"
    # 角色锁定
    assert "只" in prompt and "表达" in prompt
    print("✓ member system prompt 含 ACP + grounding")


def test_council_llm_mock():
    """mock LLM → 发言与合成均来自 LLM，source=council_llm。"""
    report = _sample_report_data()
    engine = CouncilEngine(report, llm_client=_FakeLLM())
    session = engine.create_session("想辞职但不敢跟领导说")

    import asyncio
    result = asyncio.run(
        engine.generate_council_response_async(session, "想辞职但不敢跟领导说")
    )
    assert result["source"] == "council_llm"
    # 5 颗行星都应有 LM 标记发言
    for planet in ("SUN", "MOON", "MARS", "VENUS", "SATURN"):
        assert result["statements"][planet].startswith("【LLM】"), f"{planet} 应来自 LLM"
    assert "我听到" in result["synthesis"], "合成应来自 LLM"
    print("✓ mock LLM 全流程")


def test_council_llm_partial_failure():
    """火星 LLM 返回空 → 火星回退规则桩，其余仍来自 LLM。"""
    report = _sample_report_data()
    engine = CouncilEngine(report, llm_client=_FakeLLM(fail_planets={"MARS"}))
    session = engine.create_session("想辞职但不敢跟领导说")

    import asyncio
    result = asyncio.run(
        engine.generate_council_response_async(session, "想辞职但不敢跟领导说")
    )
    assert result["source"] == "council_llm"
    # 火星回退到规则桩的固定文案
    assert "行动" in result["statements"]["MARS"], "火星应回退规则桩文案"
    assert not result["statements"]["MARS"].startswith("【LLM】"), "火星不应来自 LLM"
    # 其他行星仍来自 LLM
    assert result["statements"]["SUN"].startswith("【LLM】")
    print("✓ 单颗行星失败回退规则桩")


if __name__ == "__main__":
    test_council_fallback_without_llm()
    test_build_council_member_system_prompt_contains_acp_and_facts()
    test_council_llm_mock()
    test_council_llm_partial_failure()
    print("\n全部 council 测试通过 ✓")
