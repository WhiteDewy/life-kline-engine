"""
consultation.py — 咨询式对话引擎 V2

从"规则引擎 + 模板"到"AI 引导 + 适时引入星盘"的咨询式对话。

核心流程（遵循真实占星咨询）：
1. 先倾听和感受用户的状态
2. 问问题（不是给答案）
3. 在合适的时机才引入星盘
4. 把星盘翻译成感受/模式
5. 引导用户自己理解自己

这不是替换 consultation_engine.py，而是新的 V2 层。
原有 consultation_engine 保留用于复杂分析场景。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# ============================================================================
# 对话阶段枚举
# ============================================================================

class DialogueStage:
    """对话阶段，决定 AI 应该如何回应"""
    LISTEN = "listen"           # 倾听阶段：先感受，不急着分析
    EXPLORE = "explore"         # 探索阶段：问问题，帮助用户说清楚
    REFLECT = "reflect"         # 反思阶段：引入星盘，翻译成感受
    UNDERSTAND = "understand"    # 理解阶段：帮助用户看到模式
    CLOSE = "close"             # 结束阶段：总结和下一步


# ============================================================================
# 对话状态
# ============================================================================

@dataclass
class DialogueState:
    """一次对话的状态"""
    stage: str = DialogueStage.LISTEN
    turn_count: int = 0              # 对话轮次
    user_expressed: str = ""         # 用户表达了什么
    emotional_tone: str = "好奇"      # 用户当前的情绪基调
    topic_hints: list[str] = field(default_factory=list)  # 用户提到的话题
    theme_key: str = ""             # 识别到的 Theme
    chart_context_shared: bool = False  # 星盘上下文是否已分享
    reflection_given: bool = False     # 是否已给过反思
    question_asked: str = ""          # 最后问的问题

    def advance_stage(self) -> None:
        """推进对话阶段"""
        stage_order = [
            DialogueStage.LISTEN,
            DialogueStage.EXPLORE,
            DialogueStage.REFLECT,
            DialogueStage.UNDERSTAND,
            DialogueStage.CLOSE,
        ]
        try:
            idx = stage_order.index(self.stage)
            if idx < len(stage_order) - 1:
                self.stage = stage_order[idx + 1]
        except ValueError:
            self.stage = DialogueStage.LISTEN

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage": self.stage,
            "turn_count": self.turn_count,
            "user_expressed": self.user_expressed,
            "emotional_tone": self.emotional_tone,
            "topic_hints": self.topic_hints,
            "theme_key": self.theme_key,
            "chart_context_shared": self.chart_context_shared,
            "reflection_given": self.reflection_given,
            "question_asked": self.question_asked,
        }


# ============================================================================
# 咨询式对话引擎
# ============================================================================

class ConsultationV2:
    """
    咨询式对话引擎 V2。

    核心改变：
    - 不再用规则引擎生成"答案"
    - 用 LLM 作为引导者，先倾听，再适时引入星盘
    - 目标是帮助用户觉察，不是给建议

    使用方法：
        engine = ConsultationV2(report_data, planet)
        response = engine.chat(user_message, dialogue_state)
    """

    def __init__(
        self,
        report_data: dict[str, Any],
        planet: str = "MOON",
        dialogue_state: DialogueState | None = None,
    ):
        self.report_data = report_data
        self.planet = planet
        self.dialogue_state = dialogue_state or DialogueState()

        # 分析用户问题，获得 Theme 上下文
        self._analyze_context()

    def _analyze_context(self) -> None:
        """分析用户问题，获得 Theme 上下文"""
        try:
            from .akg import ThemeRecognizer

            recognizer = ThemeRecognizer()
            themes = recognizer.recognize(
                self.dialogue_state.user_expressed or "一般对话",
                self.report_data,
                top_k=1
            )
            if themes:
                self.dialogue_state.theme_key = themes[0].key
        except Exception:
            pass

    def chat(
        self,
        user_message: str,
        history: list[dict] | None = None,
    ) -> dict[str, Any]:
        """
        处理用户消息，返回咨询式回复。

        Args:
            user_message: 用户的消息
            history: 对话历史

        Returns:
            {
                "response": str,  # AI 的回复
                "dialogue_state": DialogueState,  # 更新后的状态
                "stage": str,  # 当前阶段
                "chart_context_available": bool,  # 是否有星盘上下文可用
            }
        """
        state = self.dialogue_state
        state.turn_count += 1

        # 更新用户表达内容
        if user_message:
            state.user_expressed = user_message

        # 根据阶段生成回复
        if state.stage == DialogueStage.LISTEN:
            response = self._listen_response(user_message, history)
        elif state.stage == DialogueStage.EXPLORE:
            response = self._explore_response(user_message, history)
        elif state.stage == DialogueStage.REFLECT:
            response = self._reflect_response(user_message, history)
        elif state.stage == DialogueStage.UNDERSTAND:
            response = self._understand_response(user_message, history)
        else:
            response = self._close_response(user_message, history)

        return {
            "response": response,
            "dialogue_state": state,
            "stage": state.stage,
            "chart_context_available": True,
        }

    # ── 各阶段回复生成 ──────────────────────────────────────

    def _listen_response(self, user_message: str, history: list | None) -> str:
        """
        倾听阶段：先感受用户的情绪，不急着分析或给建议。

        原则：
        - 承接用户的情绪，不是回应内容
        - 可以问一个简单的问题，帮助用户继续说
        """
        state = self.dialogue_state

        # 检测用户情绪
        emotional_hint = self._detect_emotional_hint(user_message)

        # 倾听模板
        if not user_message or len(user_message.strip()) < 3:
            # 用户只说了很少，先建立连接
            return self._get_opening_prompt()

        # 用户表达了内容，先倾听
        listen_prompts = [
            f"我听到了。你说的这些，我能感受到{emotional_hint}。",
            f"嗯，听你说这些，我能感觉到{emotional_hint}。",
            f"我听到了。{emotional_hint}——这很重要。",
        ]

        import random
        base_listen = random.choice(listen_prompts)

        # 问一个探索性的问题
        state.question_asked = self._get_explore_question(user_message)

        return f"{base_listen} {state.question_asked}"

    def _explore_response(self, user_message: str, history: list | None) -> str:
        """
        探索阶段：帮助用户把感受说清楚。

        原则：
        - 问更多问题，帮助用户深入
        - 不要过早引入星盘
        - 目标是让用户感到被理解
        """
        state = self.dialogue_state

        # 更新话题线索
        if user_message:
            state.topic_hints.append(user_message[:50])

        # 生成探索性问题
        explore_question = self._generate_explore_question(user_message)
        state.question_asked = explore_question

        return explore_question

    def _reflect_response(self, user_message: str, history: list | None) -> str:
        """
        反思阶段：适时引入星盘，把配置翻译成感受。

        原则：
        - 不要直接说配置，要翻译成用户的感受/模式
        - 用"也许"、"听起来"而不是"星盘显示"
        - 引入后继续问问题
        """
        state = self.dialogue_state
        state.chart_context_shared = True

        # 生成反思性陈述 + 星盘连接
        reflection = self._generate_reflection(user_message)

        # 继续问问题
        follow_up = self._get_follow_up_question(user_message)

        return f"{reflection} {follow_up}"

    def _understand_response(self, user_message: str, history: list | None) -> str:
        """
        理解阶段：帮助用户看到自己的模式。

        原则：
        - 连接过去和现在
        - 帮助用户看到重复的模式
        - 不给建议，给空间
        """
        state = self.dialogue_state
        state.reflection_given = True

        # 生成模式连接
        pattern_connection = self._connect_pattern(user_message)

        # 问一个关于行动/选择的问题
        action_question = self._get_action_question(user_message)

        return f"{pattern_connection} {action_question}"

    def _close_response(self, user_message: str, history: list | None) -> str:
        """
        结束阶段：总结 + 给用户空间。

        原则：
        - 总结我们聊了什么
        - 不要给具体建议
        - 让用户知道可以继续聊
        """
        summary = self._summarize_dialogue()
        closing = "你想怎么看待这些？你觉得接下来可以怎么做？"

        return f"{summary} {closing}"

    # ── 辅助方法 ──────────────────────────────────────────

    def _get_opening_prompt(self) -> str:
        """获取开场白"""
        planet_name = self._get_planet_name()
        openings = [
            f"我是你的{planet_name}灵。今天想聊些什么？",
            f"你今天来找我，想聊什么？",
            f"我在听。你想说什么都可以。",
        ]
        import random
        return random.choice(openings)

    def _get_planet_name(self) -> str:
        """获取行星中文名"""
        names = {
            "SUN": "太阳", "MOON": "月亮", "MERCURY": "水星",
            "VENUS": "金星", "MARS": "火星", "JUPITER": "木星",
            "SATURN": "土星", "URANUS": "天王星", "NEPTUNE": "海王星",
            "PLUTO": "冥王星",
        }
        return names.get(self.planet, self.planet)

    def _detect_emotional_hint(self, message: str) -> str:
        """从用户消息中检测情绪基调"""
        message = message.lower()

        emotional_markers = {
            "焦虑": ["焦虑", "担心", "怕", "紧张", "压力", "烦", "不安"],
            "迷茫": ["迷茫", "不知道", "不确定", "纠结", "犹豫", "怎么办", "想不通"],
            "无力": ["累", "疲惫", "无力", "虚", "撑不住", "算了"],
            "愤怒": ["气", "怒", "凭什么", "不公平", "受够了", "烦死了"],
            "难过": ["难过", "伤心", "悲伤", "失落", "失望", "委屈"],
        }

        for emotion, markers in emotional_markers.items():
            for marker in markers:
                if marker in message:
                    return f"你有些{marker}"

        return "你有些复杂的感受"

    def _get_explore_question(self, user_message: str) -> str:
        """生成探索性问题"""
        explore_questions = [
            "能多说一点吗？当时是什么感觉？",
            "这种感觉是从什么时候开始的？",
            "这件事让你最困扰的是什么？",
            "你能形容一下那种感觉吗？",
            "这件事发生的时候，你身边有别人吗？",
        ]
        import random
        return random.choice(explore_questions)

    def _generate_explore_question(self, user_message: str) -> str:
        """基于用户消息生成探索性问题"""
        # 如果用户提到了某个话题，深入问
        topic_questions = {
            "工作": ["最近工作上发生了什么？", "让你感到压力的具体是什么？"],
            "领导": ["你和领导之间，最让你不舒服的是什么？", "你有没有试过表达你的想法？"],
            "辞职": ["是什么让你想辞职？是什么在阻止你？", "如果没有任何顾虑，你会怎么做？"],
            "感情": ["这段关系中，你最在意的是什么？", "你想要的是什么样的关系？"],
            "家人": ["你和家人之间，发生了什么？", "这种情况持续多久了？"],
            "金钱": ["金钱对你来说意味着什么？", "这种焦虑有多久了？"],
        }

        for topic, questions in topic_questions.items():
            if topic in user_message:
                import random
                return random.choice(questions)

        # 默认探索性问题
        return self._get_explore_question(user_message)

    def _generate_reflection(self, user_message: str) -> str:
        """
        生成反思性陈述 + 星盘连接。

        把星盘翻译成感受，不是配置描述。
        """
        theme_key = self.dialogue_state.theme_key

        # Theme → 反思模板
        theme_reflections = {
            "authority": {
                "pattern": "听起来，你一直在一个需要「被认可」的模式里。",
                "chart_connection": "在你的星盘里，我注意到太阳和土星的关系——也许这和从小父亲或权威人物对你的期待有关。",
            },
            "intimacy": {
                "pattern": "听起来，亲密和独立在你心里一直在拉扯。",
                "chart_connection": "你的星盘里，金星和火星的位置也许能解释，为什么在靠近和退缩之间摇摆。",
            },
            "money": {
                "pattern": "听起来，金钱对你来说不只是钱，是安全感。",
                "chart_connection": "也许这和你星盘里第2宫的状态有关——那个关于「够不够」的声音。",
            },
            "self_worth": {
                "pattern": "听起来，你在做一件事之前，总觉得自己还不够好。",
                "chart_connection": "这个「不够格」的声音，也许是从很小的时候就有了。",
            },
            "safety": {
                "pattern": "听起来，你一直需要确认自己是安全的。",
                "chart_connection": "在你星盘里，月亮的位置也许能解释这种需要安全感的渴望。",
            },
        }

        if theme_key in theme_reflections:
            reflection = theme_reflections[theme_key]
            import random
            pattern = random.choice([reflection["pattern"], ""])
            chart = reflection["chart_connection"]
            if pattern:
                return f"{pattern} {chart}"
            return chart

        # 通用反思
        generic_reflections = [
            "我听到你在说一个一直在重复的模式。",
            "也许这个感受，不是第一次出现。",
            "听起来，你在这个状态里有一段时间了。",
        ]
        import random
        return random.choice(generic_reflections)

    def _get_follow_up_question(self, user_message: str) -> str:
        """获取追问"""
        follow_ups = [
            "这让你想起什么吗？",
            "这种感觉，以前也有过吗？",
            "如果你不这样做，会发生什么？",
            "你觉得是什么阻止了你？",
            "如果没有人在看着，你会怎么做？",
        ]
        import random
        return random.choice(follow_ups)

    def _connect_pattern(self, user_message: str) -> str:
        """连接过去和现在的模式"""
        connections = [
            "也许这不是第一次。也许从小到大，你一直有这样的感觉。",
            "你说的这个，让我想起你之前提过的...这之间可能有联系。",
            "也许这是你一直以来的模式——遇到类似的情况，就会有同样的感受。",
            "你有没有注意到，这种感觉每次出现，情境都很像？",
        ]
        import random
        return random.choice(connections)

    def _get_action_question(self, user_message: str) -> str:
        """获取关于行动/选择的问题"""
        questions = [
            "如果没有任何恐惧，你会怎么做？",
            "你觉得接下来可以迈出的一小步是什么？",
            "如果这个问题解决了，你的生活会有什么不同？",
            "你想从这个状态里得到什么？",
            "有没有什么时候，你感觉不太一样？",
        ]
        import random
        return random.choice(questions)

    def _summarize_dialogue(self) -> str:
        """总结对话"""
        state = self.dialogue_state
        topic = state.topic_hints[-1] if state.topic_hints else "这个话题"

        summaries = [
            f"今天我们聊了关于{topic}的事情。",
            f"我听到你在说{topic}——这对你很重要。",
            f"关于{topic}，你说了一些一直压在心里的感受。",
        ]
        import random
        return random.choice(summaries)


# ============================================================================
# 便捷函数
# ============================================================================

def create_consultation(
    report_data: dict[str, Any],
    planet: str = "MOON",
) -> ConsultationV2:
    """创建咨询式对话引擎"""
    return ConsultationV2(report_data, planet)
