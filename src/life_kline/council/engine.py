"""
engine.py — CouncilEngine：星灵议会引擎

多行星视角协作系统，实现 PRD 定义的「内在议会」机制：

用户提问
    ↓
SUN: 追求真正热爱的事情
MARS: 开始行动
MOON: 先照顾情绪
SATURN: 先准备风险
VENUS: 关系面向
    ↓
Council 输出：统一建议

与 PlanetCharacterEngine 的关系：
- PlanetCharacterEngine：提供单一行星视角的个性化画像
- CouncilEngine：整合多个行星视角，生成统一建议
"""
from __future__ import annotations

import asyncio
from typing import Any

from .council_types import (
    CouncilMember,
    CouncilSession,
    CouncilRelation,
    COUNCIL_PLANETS,
    COUNCIL_SPEAKING_STYLES,
)
from .prompts import (
    build_council_system_prompt,
    build_council_member_system_prompt,
    build_council_member_user_prompt,
    build_council_synthesis_user_prompt,
)


# ============================================================================
# Council Engine
# ============================================================================


class CouncilEngine:
    """
    星灵议会引擎——多行星视角协作系统。

    使用方法：
        engine = CouncilEngine(report_data)
        session = engine.create_session("我想辞职但不敢跟领导说")
        result = engine.generate_council_response(session, user_question)
    """

    def __init__(self, report_data: dict[str, Any], llm_client: Any | None = None):
        """
        Args:
            report_data: 完整报告数据（包含 planet_characters 子树）
            llm_client: 可选 LLMClient 实例；None 时惰性创建。
                未配置（is_configured=False）时降级到规则桩。
        """
        self._report_data = report_data
        self._planet_chars = report_data.get("planet_characters", {}).get(
            "planet_characters", {}
        )
        if llm_client is not None:
            self._llm = llm_client
        else:
            from ..llm_client import LLMClient
            self._llm = LLMClient()

    def create_session(
        self,
        topic: str,
        council_planets: list[str] | None = None,
    ) -> CouncilSession:
        """
        创建一次议会会话。

        Args:
            topic: 议会讨论的主题/问题
            council_planets: 参与的行星列表，默认 SUN, MOON, MARS, VENUS, SATURN

        Returns:
            CouncilSession 实例
        """
        planets = council_planets or COUNCIL_PLANETS
        members = self._build_members(planets, topic)

        return CouncilSession(
            session_id="",
            topic=topic,
            members=members,
        )

    def generate_council_response(
        self,
        session: CouncilSession,
        user_question: str,
    ) -> dict[str, Any]:
        """
        生成议会响应（多行星视角 + 整合）。

        核心流程：
        1. 各行星基于星盘配置生成核心观点
        2. 分析行星间关系（一致/紧张/互补）
        3. 生成整合建议

        Args:
            session: 议会会话
            user_question: 用户的问题

        Returns:
            {
                "statements": {planet: statement, ...},
                "relation": CouncilRelation,
                "synthesis": str,
            }
        """
        # Step 1: 为每个成员生成核心观点
        statements = self._generate_member_statements(session, user_question)

        # Step 2: 更新 session 中的发言
        session.member_statements = statements

        # Step 3: 分析行星间关系
        relation = self._analyze_relation(statements)
        session.relation_type = relation

        # Step 4: 生成整合建议
        synthesis = self._generate_synthesis(session, statements, relation)
        session.synthesis = synthesis

        return {
            "statements": statements,
            "relation": relation,
            "synthesis": synthesis,
        }

    # ── LLM 异步生成 ─────────────────────────────────────

    async def generate_council_response_async(
        self,
        session: CouncilSession,
        user_question: str,
        theme: Any | None = None,
    ) -> dict[str, Any]:
        """LLM 驱动的议会响应（多行星并行发言 + 主持人合成）。

        架构：每颗行星一次独立 LLM 调用（声音分离），并行执行；
        再用一次调用做主持人合成。任何调用失败或 LLM 未配置时，
        降级回规则桩（generate_council_response），保证离线/测试可用。

        Args:
            theme: 可选 ThemeNode（AKG 识别）。提供时把其证据文本作为
                额外 grounding 注入各行星发言，并在响应里附 theme 字段。

        Returns:
            {
                "statements": {planet: statement, ...},
                "relation": CouncilRelation,
                "synthesis": str,
                "source": "council_llm" | "council_rule",
                "theme": dict | None,
            }
        """
        # LLM 未配置 → 直接走规则桩
        if not getattr(self._llm, "is_configured", False):
            result = self.generate_council_response(session, user_question)
            result["source"] = "council_rule"
            result["theme"] = theme.to_dict() if theme is not None and hasattr(theme, "to_dict") else None
            return result

        members = session.members
        entry_context = {"council_planets": [m.planet for m in members]}

        # 可选：从 ThemeNode 抽取证据文本，作为额外 grounding
        theme_evidence: list[str] | None = None
        if theme is not None:
            ev = getattr(theme, "evidence", None) or []
            theme_evidence = [e.get("text", "") for e in ev if isinstance(e, dict) and e.get("text")] or None

        theme_dict = theme.to_dict() if theme is not None and hasattr(theme, "to_dict") else None

        # Step 1: 并行为每个成员生成发言（单颗失败 → 回退规则桩）
        async def _one(member: CouncilMember) -> str:
            try:
                sys_prompt = build_council_member_system_prompt(
                    self._report_data, member.planet, theme_evidence=theme_evidence
                )
                usr_prompt = build_council_member_user_prompt(
                    member.name_zh, user_question
                )
                text = await self._llm.chat_async(
                    system_prompt=sys_prompt,
                    user_message=usr_prompt,
                    history=[],
                )
                if text and text.strip():
                    return text.strip()
            except Exception as e:
                print(f"[Council] {member.planet} LLM 调用失败，降级规则桩: {e}")
            # 回退：用现有规则桩为该成员生成
            return self._build_statement(member, user_question)

        statements_list = await asyncio.gather(*[_one(m) for m in members])
        statements = {m.planet: s for m, s in zip(members, statements_list)}
        for m in members:
            m.statement = statements[m.planet]
        session.member_statements = statements

        # Step 2: 分析关系（廉价规则，够用）
        relation = self._analyze_relation(statements)
        session.relation_type = relation

        # Step 3: 主持人合成（失败 → 回退规则桩合成）
        synthesis = ""
        try:
            sys_prompt = build_council_system_prompt(
                self._report_data, session.topic, entry_context
            )
            usr_prompt = build_council_synthesis_user_prompt(
                session.topic, statements, user_question
            )
            text = await self._llm.chat_async(
                system_prompt=sys_prompt,
                user_message=usr_prompt,
                history=[],
            )
            if text and text.strip():
                synthesis = text.strip()
        except Exception as e:
            print(f"[Council] 合成 LLM 调用失败，降级规则桩: {e}")
        if not synthesis:
            synthesis = self._generate_synthesis(session, statements, relation)
        session.synthesis = synthesis

        return {
            "statements": statements,
            "relation": relation,
            "synthesis": synthesis,
            "source": "council_llm",
            "theme": theme_dict,
        }

    # ── 内部方法 ──────────────────────────────────────────

    def _build_members(
        self,
        planets: list[str],
        topic: str,
    ) -> list[CouncilMember]:
        """为每个行星构建议会成员"""
        members = []

        for planet in planets:
            profile = self._planet_chars.get(planet, {})
            persona = profile.get("persona", {})
            sign_label = profile.get("sign_label", "未知")
            house = profile.get("house", 0)
            dignity_label = profile.get("dignity_label", "未知")

            style_info = COUNCIL_SPEAKING_STYLES.get(planet, {})
            name_zh = self._get_planet_name_zh(planet)

            member = CouncilMember(
                planet=planet,
                name_zh=name_zh,
                archetype_zh=persona.get("archetype_zh", "") if persona else "",
                sign_house=f"{sign_label}座第{house}宫",
                dignity_label=dignity_label,
                speaking_style=style_info.get("style", ""),
                speaking_tone=style_info.get("tone", ""),
                core_view=self._generate_core_view(planet, topic),
                contribution=self._generate_contribution(planet),
                limitation=self._generate_limitation(planet),
            )
            members.append(member)

        return members

    def _generate_core_view(self, planet: str, topic: str) -> str:
        """
        生成指定行星关于当前议题的核心观点。

        这是基于行星本性的启发式生成。
        实际发言由 LLM 基于此框架生成更丰富的内容。
        """
        views = {
            "SUN": f"关于「{topic}」，太阳视角关心的是：这是否符合你真实的身份认同和人生方向？",
            "MOON": f"关于「{topic}」，月亮视角关心的是：你的情绪感受如何？这件事让你感到安全还是不安？",
            "MARS": f"关于「{topic}」，火星视角关心的是：需要采取什么行动？阻力在哪里？",
            "VENUS": f"关于「{topic}」，金星视角关心的是：这如何影响你的人际关系和价值感受？",
            "SATURN": f"关于「{topic}」，土星视角关心的是：现实的责任和后果是什么？需要什么结构和计划？",
        }
        return views.get(planet, f"关于「{topic}」，{planet}视角在思考...")

    def _generate_contribution(self, planet: str) -> str:
        """生成指定行星视角的贡献"""
        contributions = {
            "SUN": "带来方向感和自我认同的清晰度",
            "MOON": "关注情绪需求和内心安全感",
            "MARS": "提供行动力和勇气",
            "VENUS": "强调关系和价值的重要性",
            "SATURN": "提供现实结构和长远规划",
        }
        return contributions.get(planet, "提供独特视角")

    def _generate_limitation(self, planet: str) -> str:
        """生成指定行星视角的局限"""
        limitations = {
            "SUN": "可能过于关注自我而忽视他人感受",
            "MOON": "可能过于情绪化或需要过度安全感",
            "MARS": "可能冲动或过于激进",
            "VENUS": "可能回避冲突或过于迎合他人",
            "SATURN": "可能过于严苛或恐惧失败",
        }
        return limitations.get(planet, "有其局限性")

    def _generate_member_statements(
        self,
        session: CouncilSession,
        user_question: str,
    ) -> dict[str, str]:
        """
        生成各行星的发言内容。

        这是基于规则的简化版本。
        实际使用时，发言内容由 LLM 基于 PlanetCharacterProfile 和 CouncilSession 生成。
        """
        statements = {}

        for member in session.members:
            # 基于行星本性和发言风格生成简短的引导性发言
            # 实际丰富内容由 LLM prompt 生成
            statement = self._build_statement(member, user_question)
            statements[member.planet] = statement
            member.statement = statement

        return statements

    def _build_statement(self, member: CouncilMember, user_question: str) -> str:
        """为单个成员构建发言"""
        # 这里返回的是一个框架，实际发言由 LLM 生成更丰富的内容
        tone = member.speaking_tone
        style = member.speaking_style
        contribution = member.contribution

        # 生成基于行星特性的简短引导
        if member.planet == "SUN":
            base = "我想问你：这件事背后，你真正想要的是什么？"
        elif member.planet == "MOON":
            base = "我注意到你的情绪...这对你来说意味着什么？"
        elif member.planet == "MARS":
            base = "有什么在阻止你行动？让我们面对它。"
        elif member.planet == "VENUS":
            base = "想想你珍视的关系...这会如何影响它们？"
        elif member.planet == "SATURN":
            base = "现实一点看，我们需要面对什么样的责任？"
        else:
            base = "让我从我的角度说说..."

        return base

    def _analyze_relation(
        self,
        statements: dict[str, str],
    ) -> CouncilRelation:
        """
        分析行星间的关系类型。

        当前实现：基于发言内容的情感分析（简化版）。
        实际可扩展为基于星盘配置的分析。
        """
        # 简化实现：检查是否存在明显对立的关键词
        tension_keywords = ["但是", "然而", "冲突", "矛盾", "但是", "不过"]
        complementary_keywords = ["同时", "而且", "也", "并且"]

        tension_count = 0
        complementary_count = 0

        for statement in statements.values():
            for kw in tension_keywords:
                if kw in statement:
                    tension_count += 1
            for kw in complementary_keywords:
                if kw in statement:
                    complementary_count += 1

        if tension_count > complementary_count:
            return CouncilRelation.TENSION
        elif complementary_count > tension_count:
            return CouncilRelation.COMPLEMENTARY
        else:
            return CouncilRelation.COMPLEMENTARY

    def _generate_synthesis(
        self,
        session: CouncilSession,
        statements: dict[str, str],
        relation: CouncilRelation,
    ) -> str:
        """
        生成整合建议。

        整合不是给建议，而是帮助用户看到自己的不同面向。
        """
        planets = list(statements.keys())

        # 构建整合描述
        synthesis_parts = []

        if relation == CouncilRelation.UNANIMOUS:
            synthesis_parts.append(
                "所有声音都在指向同一个方向——"
            )
        elif relation == CouncilRelation.TENSION:
            synthesis_parts.append(
                "我听到你内在有不同的声音在拉扯——"
            )
        else:  # COMPLEMENTARY
            synthesis_parts.append(
                "你内在的不同面向其实可以一起工作——"
            )

        # 添加行星视角总结
        if "SUN" in planets and "MOON" in planets:
            synthesis_parts.append(
                "太阳说要追求方向，月亮说要照顾感受，"
            )
        if "MARS" in planets:
            synthesis_parts.append("火星说要行动，")
        if "SATURN" in planets:
            synthesis_parts.append("土星说要面对现实，")
        if "VENUS" in planets:
            synthesis_parts.append("金星说要考虑关系。")

        synthesis_parts.append(
            "这些声音都是你的一部分。"
        )

        return "".join(synthesis_parts)

    def _get_planet_name_zh(self, planet: str) -> str:
        """获取行星中文名"""
        names = {
            "SUN": "太阳",
            "MOON": "月亮",
            "MARS": "火星",
            "VENUS": "金星",
            "SATURN": "土星",
            "MERCURY": "水星",
            "JUPITER": "木星",
            "URANUS": "天王星",
            "NEPTUNE": "海王星",
            "PLUTO": "冥王星",
        }
        return names.get(planet, planet)
