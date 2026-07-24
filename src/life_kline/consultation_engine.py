"""
consultation_engine.py — 星语者咨询引擎：四步对话状态机

双层架构（v2.5）：
  - 引擎层（永远在线）：规则驱动，收集星盘证据，生成结构化分析
  - AI 层（可选增强）：LLM 翻译引擎输出为自然对话文本
  失败时降级回引擎原文。

不依赖 LLM，纯规则驱动。星语者（AI 占星师）与星灵独立：
  - 星灵 = 单一行星视角，情绪陪伴
  - 星语者 = 全盘综合分析，专业解读

四步法：
  Step 1: 问题锚定 → 定位宫位/星体候选集
  Step 2: 场景定位 → 2-3轮对话缩小取像范围
  Step 3: 星盘验证 → 全盘结构 + 直接指征 + 时间轴
  Step 4: 边界守护 → 安全边界 + 古占/现占双轨判断
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from .garden_catalog import get_category, get_question, FORTUNE_SECTION
from .chart_structure import ChartStructureAnalyzer, ChartStructureReport
from .domains.helpers import plabel, slabel, house_title, dlabel
from .engine_astrologer import DOMAIN_LABELS


# ═══════════════════════════════════════════════════════════════
# 数据类
# ═══════════════════════════════════════════════════════════════

@dataclass
class ConsultationState:
    """咨询会话的完整状态"""
    session_id: str = ""
    step: int = 1                        # 1-4, 5=completed
    category: str = ""
    question_key: str = ""

    # Step 1: 锚定
    anchor_text: str = ""
    anchor_evidence: list[str] = field(default_factory=list)

    # Step 2: 情境澄清
    scenario_context: dict[str, Any] = field(default_factory=dict)
    scenario_rounds: int = 0             # 已进行的澄清轮次
    max_scenario_rounds: int = 3

    # Step 3: 星盘验证
    verified_evidence: list[str] = field(default_factory=list)
    verified_reading: str = ""

    # Step 4: 边界守护
    boundary_notes: list[str] = field(default_factory=list)

    # 对话流
    user_responses: list[str] = field(default_factory=list)
    pending_question: str = ""
    is_complete: bool = False

    # 古占/现占倾向
    tradition_lean: bool | None = None   # True=古占论事, False=现占心理, None=未定

    # 危机检测
    is_crisis: bool = False
    crisis: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "step": self.step,
            "category": self.category,
            "question_key": self.question_key,
            "anchor_text": self.anchor_text,
            "anchor_evidence": self.anchor_evidence,
            "scenario_context": self.scenario_context,
            "scenario_rounds": self.scenario_rounds,
            "verified_evidence": self.verified_evidence,
            "verified_reading": self.verified_reading,
            "boundary_notes": self.boundary_notes,
            "pending_question": self.pending_question,
            "is_complete": self.is_complete,
            "tradition_lean": self.tradition_lean,
            "is_crisis": self.is_crisis,
            "crisis": self.crisis,
        }


@dataclass
class ConsultationReport:
    """咨询最终报告"""
    report_id: str = ""
    session_id: str = ""
    category: str = ""
    question_key: str = ""
    question_label: str = ""
    anchor_summary: str = ""
    scenario_summary: str = ""
    chart_reading: str = ""
    boundary_notes: list[str] = field(default_factory=list)
    fused_narrative: str = ""
    evidence: list[str] = field(default_factory=list)
    generated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "session_id": self.session_id,
            "category": self.category,
            "question_key": self.question_key,
            "question_label": self.question_label,
            "anchor_summary": self.anchor_summary,
            "scenario_summary": self.scenario_summary,
            "chart_reading": self.chart_reading,
            "boundary_notes": self.boundary_notes,
            "fused_narrative": self.fused_narrative,
            "evidence": self.evidence,
            "generated_at": self.generated_at,
        }


# ═══════════════════════════════════════════════════════════════
# 场景定位 — 各领域的追问模板
# ═══════════════════════════════════════════════════════════════

SCENARIO_CLARIFY_QUESTIONS: dict[str, dict[str, list[str]]] = {
    "love": {
        "love_pattern": [
            "你最近一次在感情里有重复模式的感觉，是什么时候？能跟我说说当时的场景吗？",
            "在这段模式里，你是那个'先靠近的人'还是'先退缩的人'？",
            "你觉得自己在感情里最常被什么触发——被忽视？被控制？还是被抛弃的感觉？",
        ],
        "when_meet": [
            "你现在的生活状态是什么样的？比如工作环境、社交圈、平常的休闲方式？",
            "你理想中的相遇场景是什么样的——在社交场合自然认识，还是通过共同朋友？",
            "你现在是否有在主动拓展社交圈，还是更多在等待？",
        ],
        "does_he_like_me": [
            "你们现在的关系状态是什么样的——暧昧、朋友、同事、还是前任？",
            "你能描述一下TA和你互动时的典型方式吗？",
            "TA对你有过什么让你觉得'可能不只是普通朋友'的信号？",
        ],
        "compatibility": [
            "你们最常因为什么事情产生分歧或摩擦？",
            "你们在一起时，你觉得自己'变好'还是'变小'？",
            "你的朋友/家人对这段关系的看法是什么？",
        ],
        "letting_go": [
            "你们分开多久了？现在想起来的时候，最让你难受的是什么——是那个人本身，还是'被放弃'的感觉？",
            "你觉得自己放不下的是TA，还是那个'曾经被爱过的自己'？",
            "你这段时间尝试过什么方式让自己走出来？",
        ],
        "peach_blossom": [
            "你上一次被人明显喜欢是什么时候？当时的你有回应吗？",
            "你觉得自己是被喜欢但不自知，还是真的很少遇到主动靠近的人？",
            "你平常的社交频率和交友方式是什么样的？",
        ],
        "true_love": [
            "你理想中的伴侣需要具备哪三个最重要的品质？",
            "你过去的关系里，最让你感到'对'的是什么？最让你觉得'不对'的又是什么？",
            "你觉得自己准备好进入一段长期关系了吗？还是还有一些个人课题要先处理好？",
        ],
    },
    "career": {
        "career_direction": [
            "你现在的工作（或学习方向）是什么？你最喜欢它什么地方？最不喜欢什么？",
            "你有过让你感觉'这件事我做得特别好'的瞬间吗？是什么事？",
            "如果完全不考虑收入，你最想做什么？",
        ],
    },
    "wealth": {
        "cant_save": [
            "你每个月最大的开销在哪些方面？",
            "你对自己的财务状况有清晰的了解吗，还是迷迷糊糊的？",
            "花钱给你带来的是什么感觉——满足、释放、还是空虚？",
        ],
    },
    "education": {
        "exam_anxiety": [
            "你考试崩的时候是什么感觉——脑袋空白、手抖心慌、还是时间不够？",
            "你平时的复习节奏是什么样的——是平时放松考前突击，还是一直在准备但考试时垮掉？",
            "你觉得自己是'没学会'还是'学会了但考不出来'？",
        ],
    },
    "family": {
        "family_of_origin": [
            "如果用三个词形容你从小到大的家庭氛围，你会怎么形容？",
            "你觉得自己最像父亲还是母亲？在哪方面最像？",
            "你现在和父母的关系是什么样的——亲密、疏远、还是表面和谐？",
        ],
    },
    "health": {
        "always_tired": [
            "你的累是身体上的乏还是心理上的耗竭？",
            "你每天大概几点入睡、几点起来？睡眠质量如何？",
            "最近三个月有没有特别消耗你精力的事情？",
        ],
    },
    "self": {
        "who_am_i": [
            "当别人问'你是什么样的人'时，你通常会怎么回答？你的答案和内心真实感受一致吗？",
            "你觉得自己在不同场合是同一个你，还是像在切换不同面具？",
            "有什么事情是你做了之后感觉'这才是真的我'的？",
        ],
    },
}


# ═══════════════════════════════════════════════════════════════
# 咨询引擎
# ═══════════════════════════════════════════════════════════════

class ConsultationEngine:
    """星语者四步咨询引擎"""

    def __init__(self, report_data: dict[str, Any], llm_client: Any = None):
        self._data = report_data
        self._chart_structure = ChartStructureAnalyzer(report_data).analyze()
        self._domains = report_data.get("domains", {})
        self._planet_chars = report_data.get("planet_characters", {}).get("planet_characters", {})
        self._natal = report_data.get("natal_chart", {})
        self._advanced = report_data.get("advanced_patterns", {})
        self._llm_client = llm_client  # 由调用方注入，None 则自动创建
        self._piercing_map = self._build_piercing_map()  # 穿刺数据

    def _build_piercing_map(self) -> dict[str, dict[str, Any]]:
        """从 advanced_patterns.house_rulers 构建穿刺映射。

        返回: {planet_name: {actual_house, pierced_house, note}}
        例如: {"JUPITER": {"actual_house": 10, "pierced_house": 11, "note": "木星实际落10宫...按末5°视作飞入11宫"}}
        """
        piercing: dict[str, dict[str, Any]] = {}
        house_rulers = self._advanced.get("house_rulers", [])
        for hr in house_rulers:
            if not hr.get("late_five_applied"):
                continue
            ruler = hr.get("ruler", "")
            if not ruler:
                continue
            piercing[ruler] = {
                "actual_house": hr.get("ruler_house_actual", hr.get("ruler_house", 0)),
                "pierced_house": hr.get("ruler_house", 0),
                "note": hr.get("late_five_note", ""),
            }
        return piercing

    def _apply_piercing(self, planet_name: str, base_house: int) -> tuple[int, str]:
        """应用穿刺逻辑：若行星落宫尾5度内，返回穿刺后的宫位和描述。

        Returns: (effective_house, piercing_note)
        """
        if planet_name in self._piercing_map:
            p = self._piercing_map[planet_name]
            return p["pierced_house"], f"（宫尾穿刺：实际落{p['actual_house']}宫，但力量已穿透至{p['pierced_house']}宫，论事时以第{p['pierced_house']}宫为准）"
        return base_house, ""

    # ── AI 增强层 ──

    def _get_llm_client(self) -> Any:
        """获取 LLM 客户端（优先使用注入的实例）"""
        if self._llm_client is None:
            try:
                from .llm_client import LLMClient
                self._llm_client = LLMClient()
            except Exception:
                self._llm_client = False
        return self._llm_client if self._llm_client else None

    def _ai_enhance(self, engine_text: str, step_label: str, context_hint: str = "") -> str:
        """AI 增强：将引擎结构化文本翻译为自然的星语者对话。"""
        client = self._get_llm_client()
        if not client or not client.is_configured:
            return engine_text

        try:
            from .llm_client import build_star_speaker_system_prompt
            system_prompt = build_star_speaker_system_prompt(self._data)
            step_prompt = (
                f"[引擎分析 - {step_label}]\n{engine_text[:800]}\n\n"
                f"{context_hint}\n"
                f"请用星语者的方式自然地表达以上内容。保持占星学的准确性，"
                f"但让语言更温暖流畅，像一位有经验的咨询师在和来访者对话。"
                f"200-400 字。"
            )
            ai_response = client.chat(
                system_prompt=system_prompt,
                user_message=step_prompt,
                history=[],
            )
            return ai_response if ai_response else engine_text
        except Exception as e:
            print(f"[星语者AI] 增强失败，降级到引擎原文: {e}")
            return engine_text

    # ── 公共 API ──

    def start_consultation(
        self, category: str, question_key: str, session_id: str = "",
    ) -> ConsultationState:
        """Step 1: 问题锚定"""
        cat_def = get_category(category)
        question = get_question(category, question_key)

        if not cat_def:
            raise ValueError(f"未知分类: {category}")

        sid = session_id or str(uuid.uuid4())[:12]
        state = ConsultationState(
            session_id=sid, step=1,
            category=category, question_key=question_key,
        )

        if not question:
            state.anchor_text = f"'{question_key}'不属于{cat_def.label}分类的已知问题。你想换个方式问问吗？"
            state.pending_question = "你真正想了解的是什么？"
            return state

        # 构建锚定文本
        state.anchor_text = self._build_anchor(category, question, cat_def)
        state.anchor_evidence = self._gather_anchor_evidence(question)
        state.pending_question = self._pick_scenario_question(category, question_key, 0)

        # 检测古占/现占倾向
        state.tradition_lean = self._detect_tradition_lean(question_key)

        return state

    def continue_consultation(self, state: ConsultationState, user_response: str) -> ConsultationState:
        """根据当前步骤和用户回复推进状态"""
        if state.is_complete:
            return state

        # 危机检测闸门（先于任何咨询逻辑）：命中则脱离占星流程，给真实支持资源。
        from .safety import detect_crisis
        crisis = detect_crisis(user_response)
        if crisis.is_crisis:
            state.user_responses.append(user_response)
            state.is_crisis = True
            state.crisis = crisis.to_dict()
            state.pending_question = crisis.message
            return state

        state.user_responses.append(user_response)

        if state.step in (1, 2):
            return self._handle_scenario_clarify(state, user_response)
        elif state.step == 3:
            return self._handle_chart_verify(state, user_response)
        elif state.step == 4:
            return self._handle_boundary_guard(state)

        return state

    def generate_report(self, state: ConsultationState) -> ConsultationReport:
        """生成最终报告"""
        from datetime import datetime

        question = get_question(state.category, state.question_key)
        q_label = question.label if question else state.question_key

        report = ConsultationReport(
            report_id=str(uuid.uuid4()),
            session_id=state.session_id,
            category=state.category,
            question_key=state.question_key,
            question_label=q_label,
            anchor_summary=state.anchor_text[:300],
            scenario_summary=self._summarize_scenario(state),
            chart_reading=state.verified_reading,
            boundary_notes=state.boundary_notes,
            evidence=state.verified_evidence,
            generated_at=datetime.utcnow().isoformat(),
        )

        report.fused_narrative = self._fuse_report(report)
        return report

    # ── Step 1 实现 ──

    def _build_anchor(self, category: str, question: Any, cat_def: Any) -> str:
        """构建锚定文本（AI增强，fallback为温暖模板）"""
        q = question
        cat_label = cat_def.label if cat_def else category
        domain_label = DOMAIN_LABELS.get(category, cat_label)

        parts = [
            f"你想了解'{q.label}'——这其实是很多人心里都有过的疑问。",
            f"让我从你的星盘来看看属于你的答案。\n",
        ]

        # 关联宫位
        if q.houses:
            house_names = [house_title(h) for h in q.houses]
            parts.append(f"这个问题和你星盘中的{'、'.join(house_names)}最相关。")

        # 关键证据
        key_evidence = self._pick_key_evidence(q)
        if key_evidence:
            parts.append(f"\n我先注意到一个有意思的地方：{key_evidence}")

        raw = "".join(parts)
        return self._ai_enhance(raw, "锚定", f"用户问：{q.label}，分类：{cat_label}。请用温暖、专业的星语者语气回应，不要一股脑给出所有结构性分析——先共情，再问一个自然的跟进问题帮用户说清楚ta的具体情境。")

    def _gather_anchor_evidence(self, question: Any) -> list[str]:
        """收集锚定阶段的星盘证据"""
        evidence: list[str] = []
        q = question

        for planet in q.planets:
            profile = self._planet_chars.get(planet, {})
            if not profile:
                continue
            sign = profile.get("sign", "")
            house = profile.get("house", 0)
            dignity = profile.get("dignity_code", "peregrine")
            if sign and house:
                evidence.append(
                    f"{plabel(planet)}落{slabel(sign)}{house}宫（{dlabel(dignity)}）"
                )

        for h in q.houses:
            domain = self._domains.get(
                {1: "personal", 2: "finance", 3: "education", 4: "family",
                 5: "romance", 6: "work_skill", 7: "marriage", 8: "finance",
                 9: "education", 10: "career", 11: "partnership", 12: "health"}.get(h, "personal"),
                {},
            )
            theme = domain.get("core_theme", "")
            if theme:
                evidence.append(f"{house_title(h)}：{theme}")

        return evidence

    def _pick_key_evidence(self, question: Any) -> str:
        """从 question 的核心行星中挑一个最有信息量的（含穿刺）"""
        for planet in question.planets:
            profile = self._planet_chars.get(planet, {})
            sign = profile.get("sign", "")
            house = profile.get("house", 0)
            dignity = profile.get("dignity_code", "peregrine")
            role_tag = profile.get("role_tag", "")
            if sign:
                eff_house, pierce_note = self._apply_piercing(planet, house)
                line = f"{plabel(planet)}落在{slabel(sign)}{eff_house}宫"
                if pierce_note:
                    line += pierce_note
                elif dignity in ("domicile", "exaltation"):
                    line += f"，{dlabel(dignity)}状态——这是你的天然优势区域。"
                elif dignity in ("detriment", "fall"):
                    line += f"，{dlabel(dignity)}——但这不代表不好，而是你需要用不同方式激活它。"
                else:
                    line += f"，状态平稳。"
                if role_tag:
                    line += f"它在你的星盘里扮演'{role_tag}'的角色。"
                return line
        return ""

    # ── Step 2 实现：情境澄清 ──

    def _handle_scenario_clarify(
        self, state: ConsultationState, user_response: str,
    ) -> ConsultationState:
        # 存储用户的场景描述
        ctx = state.scenario_context
        state.scenario_rounds += 1
        ctx[f"round_{state.scenario_rounds}"] = user_response

        # Step 1 → Step 2 过渡（首次回复）
        if state.step == 1:
            state.step = 2

        if state.scenario_rounds >= state.max_scenario_rounds:
            # 澄清结束 → 先给用户一个过渡提示 → 进入 Step 3
            state.pending_question = (
                "好的，我听明白了。让我现在从你的星盘里，把和这件事相关的线索串起来——"
                "下面是我的完整分析。看完之后你有什么想问的，随时可以继续聊。"
            )
            state.step = 3
            state = self._run_chart_verify(state)
            return state

        # 下一轮澄清问题
        state.pending_question = self._pick_scenario_question(
            state.category, state.question_key, state.scenario_rounds,
        )
        return state

    def _pick_scenario_question(self, category: str, question_key: str, round_idx: int) -> str:
        """选取情境澄清问题"""
        cat_questions = SCENARIO_CLARIFY_QUESTIONS.get(category, {})
        q_list = cat_questions.get(question_key, [])
        if round_idx < len(q_list):
            return q_list[round_idx]

        # 通用回退
        fallback = [
            "再多说一点？我听着。",
            "当时的感受是什么样的？",
            "这件事对你现在的生活有什么影响？",
        ]
        return fallback[round_idx % len(fallback)]

    # ── Step 3 实现：星盘验证 ──

    def _run_chart_verify(self, state: ConsultationState) -> ConsultationState:
        """执行星盘验证"""
        question = get_question(state.category, state.question_key)

        # 收集证据
        all_evidence: list[str] = list(state.anchor_evidence)

        # 全盘结构证据
        cs = self._chart_structure
        if cs.dominant_element:
            all_evidence.append(f"全盘{cs.dominant_element}象主导——{cs.element_narrative}")
        if cs.dominant_modality:
            all_evidence.append(f"全盘{cs.dominant_modality}宫主导——{cs.modality_narrative}")
        if cs.final_dispositor:
            all_evidence.append(f"定位链终点：{plabel(cs.final_dispositor)}——{cs.dispositor_chain_summary}")
        if cs.aspect_patterns:
            all_evidence.append(f"格局：{'；'.join(cs.aspect_patterns[:2])}")

        # 发光体总结
        if cs.luminaries_narrative:
            all_evidence.append(cs.luminaries_narrative)

        # ── 注入 advanced_patterns 格局数据 ──
        adv = self._advanced
        if adv:
            # 围荣/夹辅格局
            for ep in adv.get("enclosure_patterns", []):
                if ep.get("pattern_type") == "benefic_enclosure":
                    all_evidence.append(f"富贵格局：{ep.get('description', '')}——{ep.get('significance', '')}")
            # 相位格局
            for ap in adv.get("aspect_patterns", []):
                all_evidence.append(f"格局：{ap.get('description', '')}——{ap.get('interpretation', '')[:120]}")
            # 劫夺
            interception = adv.get("interception_info", {})
            if interception:
                for house, sign in interception.get("intercepted_signs", {}).items():
                    all_evidence.append(f"宫位劫夺：第{house}宫劫夺{sign}——该星座守护星在现实层面话语权减弱")

        # 补充次要行星证据（含穿刺）
        if question:
            for p in question.secondary_planets:
                profile = self._planet_chars.get(p, {})
                sign = profile.get("sign", "")
                house = profile.get("house", 0)
                if sign:
                    all_evidence.append(
                        f"{plabel(p)}（次要指征）：{slabel(sign)}{house}宫"
                    )

        state.verified_evidence = all_evidence

        # 生成验证解读
        state.verified_reading = self._build_verified_reading(state)

        # 推进到 Step 4
        state.step = 4
        state = self._handle_boundary_guard(state)

        return state

    def _build_verified_reading(self, state: ConsultationState) -> str:
        """生成星盘验证解读文本"""
        question = get_question(state.category, state.question_key)
        q_label = question.label if question else state.question_key
        cat_def = get_category(state.category)
        domain_label = cat_def.label if cat_def else state.category

        parts: list[str] = []
        parts.append(f"让我从你的星盘来完整回答'{q_label}'这个问题。\n")

        # 全盘结构前置
        cs = self._chart_structure
        if cs.element_narrative:
            parts.append(f"\n【你的星盘底色】\n{cs.element_narrative}")

        # 定位链
        if cs.final_dispositor:
            parts.append(f"\n{cs.dispositor_chain_summary}")

        # 直接指征
        if question and question.houses:
            parts.append(f"\n【{domain_label}的核心配置】")
            house_labels = [house_title(h) for h in question.houses]
            parts.append(f"这个议题的核心在{'、'.join(house_labels)}。")

        # 收集每个核心行星的详细描述
        if question:
            for planet in question.planets:
                profile = self._planet_chars.get(planet, {})
                if not profile:
                    continue
                sign = profile.get("sign", "")
                house = profile.get("house", 0)
                dignity = profile.get("dignity_code", "peregrine")
                persona = profile.get("persona", {})
                essence = persona.get("essence", "") if isinstance(persona, dict) else ""
                if sign:
                    eff_house, pierce_note = self._apply_piercing(planet, house)
                    parts.append(
                        f"\n· {plabel(planet)}落在{slabel(sign)}{eff_house}宫"
                        f"（{dlabel(dignity)}）——"
                    )
                    if pierce_note:
                        parts.append(f"{pierce_note}。")
                    if essence and isinstance(essence, str):
                        parts.append(f"{essence[:200]}")

        # 发光体
        if cs.luminaries_narrative:
            parts.append(f"\n\n【意志与感受】\n{cs.luminaries_narrative}")

        # 格局（chart_structure + advanced_patterns 合并）
        pattern_parts: list[str] = []
        if cs.aspect_pattern_narrative:
            pattern_parts.append(cs.aspect_pattern_narrative)
        # 围荣格局
        for ep in self._advanced.get("enclosure_patterns", []):
            pattern_parts.append(f"· {ep.get('description', '')}：{ep.get('significance', '')}")
        # 相位格局
        for ap in self._advanced.get("aspect_patterns", []):
            pattern_parts.append(f"· {ap.get('description', '')}")
        if pattern_parts:
            parts.append(f"\n\n【关键格局】\n{chr(10).join(pattern_parts)}")

        # 南北交
        if cs.nodes_narrative and state.category in ("self", "love", "family"):
            parts.append(f"\n\n【灵魂维度】\n{cs.nodes_narrative}")

        # 行动建议
        parts.append(self._build_action_suggestion(state))

        raw = _sanitize_text("\n".join(parts))
        return self._ai_enhance(raw, "星盘验证", f"问题：{q_label}，分类：{domain_label}")

    def _build_action_suggestion(self, state: ConsultationState) -> str:
        """为报告添加行动建议"""
        tips: dict[str, dict[str, str]] = {
            "love": {
                "love_pattern": "\n\n【今日可以做的事】\n今天留意一下：当你想退缩的时候，先暂停10秒。问自己——是TA真的要走，还是我以为TA要走？这个停顿就是你打破模式的开始。",
                "letting_go": "\n\n【今日可以做的事】\n写一封信给你自己——不是给TA——告诉那个在痛苦中的你：'我看见你了，我陪你熬过去。'",
                "peach_blossom": "\n\n【今日可以做的事】\n今天去做一件让你感到自在的事。桃花往往是在你不刻意找的时候，自己撞上来的。",
                "true_love": "\n\n【今日可以做的事】\n列一个清单：左边写'我被什么样的人吸引'，右边写'什么样的相处让我安心'。两者的交集就是你的正缘画像。",
            },
            "self": {
                "who_am_i": "\n\n【今日可以做的事】\n今天找一个安静的时刻，写下三个'我做XX的时候感觉最像自己'的瞬间。不需要给别人看。",
            },
            "career": {
                "career_direction": "\n\n【今日可以做的事】\n回忆一次让你觉得'这件事我做得特别好'的经历，写下它为什么让你有这种感觉。那个'为什么'里藏着你的职业方向。",
            },
        }
        tip = tips.get(state.category, {}).get(state.question_key, "")
        if not tip:
            tip = "\n\n【今日可以做的事】\n把报告里让你最有共鸣的那句话写下来，放在你今天能看到的地方。星盘的洞察需要时间来沉淀。"
        return tip

    # ── Step 4 实现：边界守护 ──

    def _handle_boundary_guard(self, state: ConsultationState) -> ConsultationState:
        """边界守护检查"""
        notes: list[str] = []

        # 1. 心理安全
        notes.append("⚠️ 星盘分析揭示的是倾向和模式，不是命运。你的自由意志始终在起作用。")

        # 2. 古占/现占提醒
        if state.tradition_lean is True:
            notes.append(
                "本次分析偏向古典占星的论事角度——关注客观事件和时间窗口。"
                "如果你更想了解心理层面的感受，我也可以切换视角。"
            )
        elif state.tradition_lean is False:
            notes.append(
                "本次分析偏向现代占星的心理角度——关注内在体验和成长。"
                "如果你需要更具体的时机判断和客观建议，我也可以切换到古典视角。"
            )
        else:
            notes.append("本次分析兼顾了古典占星的客观判断和现代占星的心理洞察。")

        # 3. 特定领域的伦理边界
        if state.category == "health":
            notes.append(
                "🩺 健康分析仅供生活方式参考，不构成医疗诊断。"
                "如有身体不适，请务必咨询专业医生。"
            )

        if state.category == "family" and state.question_key in (
            "should_have_kids", "understand_my_child",
        ):
            notes.append(
                "关于孩子的话题，星盘能提供倾向判断，但生育和养育决策涉及太多"
                "星盘之外的因素。请把这里的分析当作参考，而不是依据。"
            )

        # 4. 证据充分性
        if len(state.verified_evidence) < 3:
            notes.append(
                "本次分析使用的星盘证据较少。这是因为你的问题涉及的信息在星盘中"
                "没有非常突出的指征——这不代表你的问题不重要，只是星盘给你的空间更自由。"
            )

        state.boundary_notes = notes
        state.step = 5
        state.is_complete = True
        state.pending_question = ""

        return state

    def _handle_chart_verify(
        self, state: ConsultationState, _user_response: str,
    ) -> ConsultationState:
        """处理用户对验证解读的反馈 — 如果有新的内容，可以补充"""
        state.step = 4
        return self._handle_boundary_guard(state)

    # ── 报告融合 ──

    def _summarize_scenario(self, state: ConsultationState) -> str:
        """从多轮澄清中提取一句话场景总结"""
        if not state.scenario_context:
            return ""
        last = state.scenario_context.get(
            f"round_{state.scenario_rounds}",
            list(state.scenario_context.values())[-1] if state.scenario_context else "",
        )
        # 截断
        return f"用户描述：{str(last)[:200]}"

    def _fuse_report(self, report: ConsultationReport) -> str:
        """融合所有部分为完整报告文本"""
        parts = [
            f"## {report.question_label}\n",
        ]
        if report.anchor_summary:
            parts.append(f"### 问题锚定\n{report.anchor_summary}\n")
        if report.scenario_summary:
            parts.append(f"### 情境\n{report.scenario_summary}\n")
        if report.chart_reading:
            parts.append(f"### 星盘解读\n{report.chart_reading}\n")
        if report.boundary_notes:
            parts.append("### 提示\n")
            for note in report.boundary_notes:
                parts.append(f"- {note}")
            parts.append("")

        raw = "\n".join(parts)
        return self._ai_enhance(raw, "综合报告", "这是最终报告，请将以上所有部分融合成一篇完整的咨询文。保持边界守护提示的严谨性。")

    # ── 古占/现占倾向检测 ──

    def _detect_tradition_lean(self, question_key: str) -> bool | None:
        """根据问题类型检测用户更可能需要的分析倾向"""
        # 预测/时机类 → 古占论事
        prediction_keys = {
            "when_meet", "jump_or_stay", "career_change", "should_have_kids",
            "windfall_luck", "invest_fit",
        }
        # 心理/感受类 → 现占心理
        psychology_keys = {
            "who_am_i", "feel_different", "inner_conflict", "letting_go",
            "family_of_origin", "exam_anxiety", "always_tired",
            "money_psychology", "love_pattern", "hidden_talent",
        }

        if question_key in prediction_keys:
            return True      # 古占
        if question_key in psychology_keys:
            return False     # 现占
        return None          # 未定，由对话动态判断


# ═══════════════════════════════════════════════════════════════
# 会话管理
# ═══════════════════════════════════════════════════════════════

# ── 工具函数 ─────────────────────────────────────────────

import re as _re


def _sanitize_text(text: str) -> str:
    """清理文本中的原始 dict/JSON 痕迹，确保纯文本输出"""
    # 移除 {'key': ...} 样式的 Python dict 字符串
    text = _re.sub(r"\{'[^']+':\s*'[^']*'(?:,\s*'[^']+':\s*'[^']*')*\}", "", text)
    # 移除 {"key": ...} 样式的 JSON 字符串
    text = _re.sub(r'\{"[^"]+":\s*"[^"]*"(?:,\s*"[^"]+":\s*"[^"]*")*\}', "", text)
    # 清理多余空白
    text = _re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# ── 会话管理 ─────────────────────────────────────────────

class ConsultationSessionManager:
    """管理多个咨询会话的内存存储"""

    def __init__(self):
        self._sessions: dict[str, ConsultationState] = {}

    def store(self, state: ConsultationState) -> None:
        self._sessions[state.session_id] = state

    def load(self, session_id: str) -> ConsultationState | None:
        return self._sessions.get(session_id)

    def remove(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)

    def list_for_report(self, report_id: str) -> list[ConsultationState]:
        # 简化：返回所有（实际应加 report_id 过滤）
        return list(self._sessions.values())
