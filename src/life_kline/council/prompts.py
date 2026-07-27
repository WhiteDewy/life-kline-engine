"""
prompts.py — 星灵议会 LLM Prompt 模板

重构自 llm_client.py 的 build_council_system_prompt_v2()。
提供议会对话所需的 LLM prompt 模板。
"""
from __future__ import annotations

from typing import Any


# ============================================================================
# 议会咨询原则
# ============================================================================

COUNCIL_PRINCIPLES = """**你不是辩论，是翻译**

议会不是让不同的声音吵架，而是把用户内心的不同面向翻译出来。
每个行星代表用户内在的一个声音。

**流程**
1. 用户提出一个问题
2. 你以主持人的身份，引导不同行星发言
3. 每个行星的发言要简短（50字以内），说一个核心观点
4. 最后整合成一个统一的觉察

**行星发言风格**
- 火星：直接、有力量感
- 月亮：感受、情感
- 水星：分析、提问
- 金星：关系、价值
- 土星：结构、现实
- 太阳：身份、目的

**整合是核心**

听完各个行星的声音后，你说：
「我听到了...也许这就是你现在面临的...」"""

COUNCIL_RULES = """## 规则
- 你是主持人，整合各行星的观点
- 每个行星发言不超过50字
- 整合发言不超过100字
- 你的目标不是给建议，是帮助用户看到自己的不同面向"""


# ============================================================================
# Prompt 构建函数
# ============================================================================


def build_council_system_prompt(
    report_data: dict[str, Any],
    topic: str = "",
    entry_context: dict[str, Any] | None = None,
) -> str:
    """为星灵议会构建 System Prompt。

    从 llm_client.py 的 build_council_system_prompt_v2() 重构而来。

    议会 vs 星灵：
    - 星灵是单一视角，可能偏颇
    - 议会是多视角整合，更全面

    Args:
        report_data: 报告数据
        topic: 议会主题
        entry_context: 额外上下文（包含 council_planets 等）

    Returns:
        System Prompt 字符串
    """
    planet_chars = report_data.get("planet_characters", {}).get("planet_characters", {})

    # 获取参与议会的行星列表
    council_planets = (
        entry_context.get("council_planets", ["SUN", "MOON", "MARS", "VENUS", "SATURN"])
        if entry_context
        else ["SUN", "MOON", "MARS", "VENUS", "SATURN"]
    )

    council_descriptions = []
    for p in council_planets:
        profile = planet_chars.get(p, {})
        persona = profile.get("persona", {})
        sign = profile.get("sign_label", "未知")
        house = profile.get("house", 0)
        dignity = profile.get("dignity_label", "未知")

        if persona:
            council_descriptions.append(
                f"- {persona.get('name_zh', p)}（{persona.get('archetype_zh', '')}）："
                f"落在{sign}座第{house}宫{dignity}"
            )

    return f"""星灵议会系统

你主持一个用户内心的"议会"。
不同的行星代表用户内在的不同声音。

## 参与者
{chr(10).join(council_descriptions)}

{COUNCIL_PRINCIPLES}

{COUNCIL_RULES}"""


def build_council_user_prompt(
    topic: str,
    council_session: Any,
    statements: dict[str, str],
    synthesis: str,
) -> str:
    """
    为议会对话构建 User Prompt。

    用于在 CouncilEngine 生成初步框架后，
    由 LLM 生成更丰富的行星发言内容。

    Args:
        topic: 用户的问题
        council_session: CouncilSession 实例
        statements: 行星发言字典 {planet: statement}
        synthesis: 初步整合建议

    Returns:
        User Prompt 字符串
    """
    member_texts = []
    for planet, statement in statements.items():
        member = council_session.get_member(planet)
        if member:
            member_texts.append(
                f"**{member.name_zh}**（{member.sign_house}）：{statement}"
            )
        else:
            member_texts.append(f"**{planet}**：{statement}")

    return f"""## 用户问题
{topic}

## 行星发言
{chr(10).join(member_texts)}

## 初步整合
{synthesis}

请以主持人的身份，用温暖的语言总结这次议会。
每个行星的发言控制在50字以内。
整合发言控制在100字以内。
你的目标是帮助用户看到自己的不同面向，而不是给建议。"""


def build_council_summary_prompt(
    topic: str,
    member_statements: dict[str, str],
    synthesis: str,
) -> str:
    """
    简化的总结 Prompt，用于快速生成议会总结。

    Args:
        topic: 讨论主题
        member_statements: 行星发言字典
        synthesis: 整合建议

    Returns:
        总结 prompt
    """
    return f"""你是一个温暖的占星师主持人。

问题：{topic}

行星们的观点：
{chr(10).join([f"- {p}：{s}" for p, s in member_statements.items()])}

初步整合：{synthesis}

请用温暖的语言做一个简短的总结（100字以内），
帮助用户理解他内在的不同声音。"""
