"""
daily_question_engine.py — 每日一问引擎

基于今日星灵生成每日提问。支持 LLM 模式和规则回退。
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

from .constants import Planet
from .service import PLANET_LABELS


# ============================================================================
# 每日一问题库（至少 3 题/行星 × 10 行星 = 30+ 题）
# ============================================================================

QUESTION_BANK: dict[str, list[str]] = {
    "SUN": [
        "今天你愿意让更多人看见真实的你吗？",
        "你最近一次为别人的成长感到骄傲是什么时候？",
        "有什么事让你觉得自己正在发光？",
        "今天你选择做什么样的人？",
        "你的热情今天被什么点燃了？",
    ],
    "MOON": [
        "今天你的情绪需要什么？",
        "你上一次感到完全安全是什么时候？",
        "有什么柔软的感受你想拥抱？",
        "今天你照顾好自己的内心了吗？",
        "什么让你感到被理解和接纳？",
    ],
    "MERCURY": [
        "今天有什么信息是你一直想表达却还没说的？",
        "你最近在做决定时，是听逻辑更多还是听感觉更多？",
        "哪本书或哪句话最近一直在你脑子里转？",
        "今天你愿意和谁进行一次真诚的对话？",
        "有什么想法你一直在反复思考？",
    ],
    "VENUS": [
        "今天你允许自己感受被爱的感觉了吗？",
        "什么是你最近觉得美好的小事？",
        "你觉得自己值得被好好对待吗？",
        "今天你如何对自己温柔一点？",
        "最近有什么让你心动的人或事？",
    ],
    "MARS": [
        "今天你有勇气把一直想说的话说出来吗？",
        "你最近一次为自己争取是什么时候？",
        "有什么愤怒你一直压在心底？",
        "今天你的能量应该用在哪里？",
        "你想在什么事情上迈出第一步？",
    ],
    "JUPITER": [
        "今天你对什么还保持着信念？",
        "最近什么事情让你觉得'还好我没放弃'？",
        "你的乐观今天帮到了谁？",
        "今天有什么好事正在靠近你？",
        "你相信的愿景是什么？",
    ],
    "SATURN": [
        "今天你愿意面对哪个一直拖延的责任？",
        "你最近在为什么事情默默坚持？",
        "有什么是你觉得'虽然难，但必须做'的？",
        "今天你的耐心用在了哪里？",
        "哪条边界是你今天必须守住的？",
    ],
    "URANUS": [
        "今天有什么旧模式你想打破？",
        "你最近一次感到惊喜的发现是什么？",
        "有什么是你一直想做但觉得'太不一样'的事？",
        "今天你准备好接受变化了吗？",
        "什么让你感到自由？",
    ],
    "NEPTUNE": [
        "今天你的直觉在告诉你什么？",
        "你最近一次被美或艺术打动是什么时候？",
        "有什么梦想你还不敢说出来？",
        "今天你允许自己做一会儿梦了吗？",
        "你内心深处的渴望是什么？",
    ],
    "PLUTO": [
        "今天你有什么需要放下才能前进？",
        "你最近在经历什么深层的变化？",
        "有什么事你一直在控制，却越来越累？",
        "今天你愿意面对什么真相？",
        "什么旧的东西正在你心里慢慢死去？",
    ],
}

# 按 Planet.value 索引的通用字典
# 北交点/南交点也提供少量问题（作为意外回退）
QUESTION_BANK["NORTH_NODE"] = [
    "今天你离你想成为的那个人更近了吗？",
    "什么新方向在向你招手？",
]
QUESTION_BANK["SOUTH_NODE"] = [
    "今天你有什么旧习惯需要放下？",
    "什么熟悉的模式正在阻碍你前进？",
]


@dataclass
class DailyQuestion:
    """每日一问"""
    question: str
    spirit_planet: str
    spirit_planet_label: str
    context_note: str
    voice_text: str
    generated_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "question": self.question,
            "spirit_planet": self.spirit_planet,
            "spirit_planet_label": self.spirit_planet_label,
            "context_note": self.context_note,
            "voice_text": self.voice_text,
            "generated_at": self.generated_at,
        }


class DailyQuestionEngine:
    """每日一问引擎"""

    def __init__(self, llm_client=None):
        self.llm_client = llm_client

    def generate(
        self,
        today_spirit: Any,
        chart: Any = None,
        transits: list = None,
    ) -> DailyQuestion:
        """
        生成每日一问。

        Args:
            today_spirit: TodayStarSpirit 实例
            chart: 本命盘 ChartData（LLM 模式需要）
            transits: 行运列表（LLM 模式需要）
        """
        now_str = datetime.now(timezone.utc).isoformat()

        # 优先 LLM 模式
        if self.llm_client is not None and self.llm_client.is_configured:
            question = self._generate_via_llm(today_spirit, chart, transits)
            if question:
                return DailyQuestion(
                    question=question,
                    spirit_planet=today_spirit.planet,
                    spirit_planet_label=today_spirit.planet_label,
                    context_note="基于你的星盘和今日行运，星灵为你提出了这个问题。",
                    voice_text=f"{today_spirit.planet_label}想知道：{question}",
                    generated_at=now_str,
                )

        # 规则回退：从题库中按行星筛选
        return self._rule_based_fallback(today_spirit, now_str)

    def _generate_via_llm(
        self,
        today_spirit: Any,
        chart: Any,
        transits: list,
    ) -> str:
        """使用 LLM 生成问题"""
        try:
            # ── 构建星盘上下文 ──
            spirit_planet = today_spirit.planet_label
            current_sign = today_spirit.sign_label

            # 从 chart 提取关键信息（防御性访问）
            chart_summary = ""
            if chart is not None:
                try:
                    moon_info = chart.get_planet_info(Planet.MOON) if hasattr(chart, 'get_planet_info') else None
                    asc_info = getattr(chart, 'ascendant', None)
                    dominant = getattr(chart, 'dominant_planets', []) or []
                    dom_labels = [d.get('label', '') if isinstance(d, dict) else str(d) for d in dominant[:3]]
                    dom_text = '、'.join(dom_labels) if dom_labels else '综合'

                    moon_desc = ""
                    if moon_info:
                        moon_sign = moon_info.get('sign_label', '')
                        moon_dignity = moon_info.get('dignity_label', '')
                        moon_desc = f"月亮在{moon_sign}{moon_dignity}，"

                    asc_desc = ""
                    if asc_info:
                        asc_sign = asc_info.get('sign_label', '') if isinstance(asc_info, dict) else str(asc_info)
                        asc_desc = f"上升{asc_sign}，"

                    chart_summary = (
                        f"用户星盘底色：{asc_desc}{moon_desc}主导力量{dom_text}。"
                    )
                except Exception:
                    chart_summary = ""

            # 从 transits 提取最相关的 2 个行运
            transit_summary = ""
            if transits:
                try:
                    relevant = [t for t in transits if t.get('aspect_type') in ('trine', 'sextile', 'conjunction', 'square', 'opposition')][:2]
                    if relevant:
                        transit_lines = []
                        for t in relevant:
                            transit_lines.append(
                                f"{t.get('transiting_planet', '')}{t.get('aspect_label', '')}{t.get('natal_planet', '')}"
                            )
                        transit_summary = f"今日行运：{'；'.join(transit_lines)}。"
                    else:
                        transit_summary = "今日无强烈行运相位。"
                except Exception:
                    transit_summary = ""

            # 今日星灵触发事件
            transit_event = ""
            if today_spirit.transit_aspect:
                transit_event = (
                    f"星灵触发：{today_spirit.transit_aspect.get('transiting_planet', '')}"
                    f"{today_spirit.transit_aspect.get('aspect_label', '')}"
                    f"{today_spirit.transit_aspect.get('natal_planet', '')}。"
                )

            context_parts = [
                f"今日引路星灵：{spirit_planet}（{current_sign}）",
                f"触发事件：{transit_event}" if transit_event else "",
                chart_summary,
                transit_summary,
            ]
            context = "\n".join(p for p in context_parts if p)

            system_prompt = (
                "你是一个温暖、有洞察力的占星陪伴者「每日星灵助手」。\n\n"
                "你的任务是根据用户的今日星盘信息，生成一个不超过40字的每日提问。\n\n"
                "## 提问风格要求\n"
                "- 柔软、开放、不评判\n"
                "- 引导用户向内观察自己，而不是寻求外部答案\n"
                "- 结合今日星灵的能量特点，不是泛泛的问题\n"
                "- 直接返回问题本身，不加标号、前缀或解释\n\n"
                f"## 今日星盘上下文\n{context}\n\n"
                "请直接生成问题："
            )
            user_message = "请根据以上星盘信息，生成今日的每日一问。"

            result = self.llm_client.chat(
                system_prompt=system_prompt,
                user_message=user_message,
            )

            # 防御：LLM 可能返回空或包含 markdown 格式
            if not result:
                return ""
            result = result.strip().strip('"').strip("'")
            if result.startswith("```"):
                result = result.split("\n", 1)[-1]
            if result.endswith("```"):
                result = result[:-3]
            result = result.strip()

            return result
        except Exception:
            return ""

    def _rule_based_fallback(self, today_spirit: Any, now_str: str) -> DailyQuestion:
        """规则回退：从题库中随机选取"""
        planet_key = today_spirit.planet
        questions = QUESTION_BANK.get(planet_key, [])

        if not questions:
            # 如果在题库中找不到，用 MOON 的作为万能回退
            questions = QUESTION_BANK.get("MOON", ["今天你的情绪需要什么？"])

        question = random.choice(questions)

        context_note = (
            f"今日{PLANET_LABELS.get(Planet(today_spirit.planet), today_spirit.planet_label)}指引——"
            f"这个问题来自你的{today_spirit.planet_label}星灵。"
        )
        voice_text = f"{today_spirit.planet_label}想知道：{question}"

        return DailyQuestion(
            question=question,
            spirit_planet=today_spirit.planet,
            spirit_planet_label=today_spirit.planet_label,
            context_note=context_note,
            voice_text=voice_text,
            generated_at=now_str,
        )
