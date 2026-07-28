"""
test_acp.py — ACP 共享模块测试

覆盖：
- ACP 常量完整（宪法/禁令/禁用词/边界守卫/Narrative 7 字段）
- sanitize_fatalism 反宿命后处理
- council/prompts 重导出 back-compat
- llm_client 5 个 builder 引用共享 GUARDRAILS（消除重复）
- council builder 运行时输出含 ACP 宪法关键词
"""
import sys
import os
import inspect

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from life_kline.acp import (
    ACP_CONSTITUTION, GUARDRAILS, FORBIDDEN_WORDS,
    BOUNDARY_GUARD_NOTE, NARRATIVE_SCHEMA_FIELDS, sanitize_fatalism,
)


def test_acp_constants():
    """ACP 常量非空 + 7 字段规格。"""
    assert ACP_CONSTITUTION and "自由意志" in ACP_CONSTITUTION
    assert "宿命" in ACP_CONSTITUTION
    assert GUARDRAILS and "禁止的事" in GUARDRAILS
    assert FORBIDDEN_WORDS and "注定" in FORBIDDEN_WORDS
    assert BOUNDARY_GUARD_NOTE and "自由意志" in BOUNDARY_GUARD_NOTE
    assert len(NARRATIVE_SCHEMA_FIELDS) == 7
    assert NARRATIVE_SCHEMA_FIELDS == (
        "theme", "origin", "evidence", "psychology", "pattern", "healing_goal", "growth"
    )
    print("✓ ACP 常量完整，7 字段规格正确")


def test_sanitize_fatalism():
    """反宿命禁用词被替换。"""
    for word in FORBIDDEN_WORDS:
        assert word not in sanitize_fatalism(f"你{word}会成功"), f"{word} 未被净化"
    assert sanitize_fatalism("") == ""
    assert sanitize_fatalism("正常的倾向性表达") == "正常的倾向性表达"
    print("✓ sanitize_fatalism 反宿命后处理")


def test_council_prompts_reexport():
    """council/prompts 重导出 ACP 常量（back-compat，test_council 依赖）。"""
    from life_kline.council.prompts import ACP_CONSTITUTION as A2, COUNCIL_GUARDRAILS
    assert A2 is ACP_CONSTITUTION, "ACP_CONSTITUTION 应为同一对象"
    assert COUNCIL_GUARDRAILS is GUARDRAILS, "COUNCIL_GUARDRAILS 应重导出 GUARDRAILS"
    print("✓ council/prompts 重导出 back-compat")


def test_llm_client_builders_reference_shared_guardrails():
    """5 个 llm_client builder 引用共享 GUARDRAILS（消除内联重复）。"""
    from life_kline import llm_client
    builders = [
        "build_spirit_system_prompt",
        "build_spirit_system_prompt_v2",
        "build_star_speaker_system_prompt_v2",
        "build_sign_system_prompt",
        "build_star_speaker_system_prompt",
    ]
    for name in builders:
        fn = getattr(llm_client, name, None)
        assert fn is not None, f"{name} 不存在"
        src = inspect.getsource(fn)
        assert "GUARDRAILS" in src, f"{name} 未引用共享 GUARDRAILS"
    print(f"✓ {len(builders)} 个 builder 均引用共享 GUARDRAILS")


def test_council_builder_contains_acp():
    """council builder 运行时输出含 ACP 宪法关键词。"""
    from life_kline.council.prompts import build_council_system_prompt
    report = {
        "planet_characters": {
            "planet_characters": {
                "SUN": {
                    "persona": {"name_zh": "太阳", "archetype_zh": "主角", "essence": "..."},
                    "sign_label": "狮子", "house": 10, "dignity_label": "庙旺",
                },
            }
        }
    }
    prompt = build_council_system_prompt(report, topic="测试")
    assert "自由意志" in prompt or "宿命" in prompt, "council prompt 应含 ACP 宪法"
    assert "禁止的事" in prompt, "council prompt 应含 GUARDRAILS"
    print("✓ council builder 运行时含 ACP 宪法")


if __name__ == "__main__":
    test_acp_constants()
    test_sanitize_fatalism()
    test_council_prompts_reexport()
    test_llm_client_builders_reference_shared_guardrails()
    test_council_builder_contains_acp()
    print("\n全部 ACP 测试通过 ✓")
