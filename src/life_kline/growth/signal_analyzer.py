"""
signal_analyzer.py — GrowthSignalAnalyzer：从对话内容分析成长信号

根据用户对话内容，推断 Theme 相关的心理状态变化（fear/awareness/action）。

遵循 ACI 文档的 Companion Memory 概念：
- 记录「你成长了什么」，不是「说了什么」
- 从对话中检测 fear/awareness/action 的变化信号
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# ============================================================================
# 信号关键词定义
# ============================================================================

# Fear 降低信号（用户感到更勇敢、更放松）
FEAR_DECREASE_SIGNALS = {
    "positive_patterns": [
        # 表达勇气
        "我想试试", "我想尝试", "我打算", "我准备", "我要", "我决定",
        "我想通了", "我明白了", "我懂了", "突然想通了", "一下子明白了",
        "好像没那么怕了", "好像没那么担心了", "好像没那么紧张了",
        # 表达行动
        "我做了", "我开始", "我尝试了", "我迈出", "我踏出", "我主动",
        "我跟他说", "我跟老板说了", "我跟领导说了", "我提了", "我表达了",
        # 表达成长感
        "我发现自己", "我意识到", "我觉察到", "我现在知道了",
        "好像变了", "不一样了", "不一样的感觉", "比以前", "现在能",
    ],
    "negative_patterns": [
        # 仍然恐惧但有突破
        "虽然还是有点怕", "虽然还是担心", "但是我决定", "不过我还是",
    ],
}

# Fear 增加信号（用户更焦虑、更恐惧）
FEAR_INCREASE_SIGNALS = {
    "patterns": [
        "我很怕", "我害怕", "我担心", "我焦虑", "我紧张", "我不敢",
        "怎么办", "万一", "要是", "不敢跟", "不知道该不该", "纠结要不要",
        "睡不着", "吃不下", "难受", "崩溃", "撑不住了", "受不了了",
    ],
}

# Awareness 上升信号（用户有新的自我认知）
AWARENESS_INCREASE_SIGNALS = {
    "patterns": [
        "我发现", "我意识到", "我注意到", "我觉察到", "我明白了",
        "原来", "其实", "可能是因为", "不知道为什么", "突然想到",
        "好像跟", "好像是因为", "可能跟我的", "这让我想到",
        "我好像", "我好像有点", "我好像总是", "我好像每次都",
        "以前不懂", "现在才明白", "以前没想过", "现在才意识到",
    ],
}

# Action 上升信号（用户开始采取行动）
ACTION_INCREASE_SIGNALS = {
    "patterns": [
        "我做了", "我开始做了", "我尝试了", "我迈出", "我踏出",
        "我主动", "我跟", "我找", "我提出", "我写了", "我发了",
        "我约了", "我报名了", "我参加了", "我加入了", "我开始了",
    ],
}

# 主题关键词映射（用于判断用户聊的是什么 Theme）
THEME_KEYWORDS = {
    "authority": ["领导", "老板", "上司", "工作", "辞职", "升职", "同事", "职场", "听话", "服从", "权力"],
    "intimacy": ["喜欢", "恋爱", "分手", "复合", "暧昧", "约会", "暗恋", "追", "感情", "伴侣", "老公", "老婆"],
    "money": ["钱", "收入", "投资", "理财", "财务", "工资", "存款", "赚钱", "负债", "省钱", "副业"],
    "self_worth": ["自信", "自卑", "价值", "配得", "值得", "认可", "成就", "失败", "能力", "优点", "缺点"],
    "family": ["父母", "妈妈", "爸爸", "原生家庭", "家里", "小时候", "童年", "家庭"],
    "career": ["工作", "事业", "方向", "跳槽", "转行", "面试", "同事", "老板", "上班", "加班"],
    "health": ["身体", "健康", "累", "疲劳", "病", "精力", "睡眠", "焦虑", "压力"],
}


# ============================================================================
# 分析结果数据类
# ============================================================================

@dataclass
class GrowthSignals:
    """从单次对话中提取的成长信号"""
    fear_delta: float = 0.0       # -1.0 ~ +1.0，负数=恐惧降低，正数=恐惧增加
    awareness_delta: float = 0.0  # -1.0 ~ +1.0，负数=觉察降低，正数=觉察增加
    action_delta: float = 0.0     # -1.0 ~ +1.0，负数=行动减少，正数=行动增加
    detected_themes: list[str] = field(default_factory=list)  # 检测到的主题列表
    signal_evidence: list[str] = field(default_factory=list)  # 信号证据（匹配的关键词）
    confidence: float = 0.5       # 分析置信度

    def to_dict(self) -> dict[str, Any]:
        return {
            "fear_delta": self.fear_delta,
            "awareness_delta": self.awareness_delta,
            "action_delta": self.action_delta,
            "detected_themes": self.detected_themes,
            "signal_evidence": self.signal_evidence,
            "confidence": self.confidence,
        }


# ============================================================================
# 成长信号分析器
# ============================================================================

class GrowthSignalAnalyzer:
    """
    从用户对话内容中分析成长信号。

    使用方法：
        analyzer = GrowthSignalAnalyzer()
        signals = analyzer.analyze(user_message, conversation_context)
    """

    def __init__(self):
        self._fear_decrease = FEAR_DECREASE_SIGNALS
        self._fear_increase = FEAR_INCREASE_SIGNALS
        self._awareness_increase = AWARENESS_INCREASE_SIGNALS
        self._action_increase = ACTION_INCREASE_SIGNALS
        self._theme_keywords = THEME_KEYWORDS

    def analyze(
        self,
        user_message: str,
        conversation_context: dict[str, Any] | None = None,
    ) -> GrowthSignals:
        """
        分析用户消息，提取成长信号。

        Args:
            user_message: 用户当前消息
            conversation_context: 对话上下文（可选，包含历史信息）

        Returns:
            GrowthSignals: 提取的成长信号
        """
        ctx = conversation_context or {}
        msg = user_message.lower()

        signals = GrowthSignals()
        evidence = []

        # 1. 检测主题
        detected_themes = self._detect_themes(msg)
        signals.detected_themes = detected_themes

        # 2. 检测 Fear 变化
        fear_delta = self._analyze_fear(msg, ctx)
        signals.fear_delta = fear_delta
        if fear_delta < -0.1:
            evidence.append(f"fear_decrease:{fear_delta:.2f}")
        elif fear_delta > 0.1:
            evidence.append(f"fear_increase:{fear_delta:.2f}")

        # 3. 检测 Awareness 变化
        awareness_delta = self._analyze_awareness(msg, ctx)
        signals.awareness_delta = awareness_delta
        if awareness_delta > 0.1:
            evidence.append(f"awareness_increase:{awareness_delta:.2f}")

        # 4. 检测 Action 变化
        action_delta = self._analyze_action(msg, ctx)
        signals.action_delta = action_delta
        if action_delta > 0.1:
            evidence.append(f"action_increase:{action_delta:.2f}")

        signals.signal_evidence = evidence

        # 5. 计算置信度（基于信号强度）
        confidence = min(0.3 + len(evidence) * 0.15, 0.95)
        signals.confidence = confidence

        return signals

    def _detect_themes(self, msg: str) -> list[str]:
        """检测消息涉及的主题"""
        detected = []
        for theme, keywords in self._theme_keywords.items():
            for kw in keywords:
                if kw in msg:
                    if theme not in detected:
                        detected.append(theme)
                    break
        return detected

    def _analyze_fear(self, msg: str, ctx: dict[str, Any]) -> float:
        """分析 Fear 变化"""
        delta = 0.0

        # Fear 降低（负面词出现但有转折 = 正在克服）
        for pattern in self._fear_decrease["positive_patterns"]:
            if pattern in msg:
                delta -= 0.15
        for pattern in self._fear_decrease["negative_patterns"]:
            if pattern in msg:
                delta -= 0.1  # 弱信号

        # Fear 增加（持续恐惧/焦虑）
        for pattern in self._fear_increase["patterns"]:
            if pattern in msg:
                delta += 0.2

        # 边界保护
        return max(-1.0, min(1.0, delta))

    def _analyze_awareness(self, msg: str, ctx: dict[str, Any]) -> float:
        """分析 Awareness 变化"""
        delta = 0.0

        # Awareness 上升信号
        for pattern in self._awareness_increase["patterns"]:
            if pattern in msg:
                delta += 0.15

        return max(-1.0, min(1.0, delta))

    def _analyze_action(self, msg: str, ctx: dict[str, Any]) -> float:
        """分析 Action 变化"""
        delta = 0.0

        # Action 上升信号
        for pattern in self._action_increase["patterns"]:
            if pattern in msg:
                delta += 0.2

        # 检查是否有具体的行动描述
        action_verbs = ["做了", "开始", "尝试", "迈出", "主动", "跟", "找", "提出", "写了", "发了", "约", "报名", "参加", "加入"]
        for verb in action_verbs:
            if verb in msg and len(msg) > 5:
                delta += 0.1
                break

        return max(-1.0, min(1.0, delta))

    def analyze_from_dialogue_state(
        self,
        dialogue_state: dict[str, Any],
    ) -> GrowthSignals:
        """
        从 DialogueState 分析成长信号（用于 spirit_chat_v2）。

        Args:
            dialogue_state: ConsultationV2 的对话状态

        Returns:
            GrowthSignals
        """
        # 从对话状态中提取信息
        user_expressed = dialogue_state.get("user_expressed", "")
        theme_key = dialogue_state.get("theme_key", "")
        emotional_tone = dialogue_state.get("emotional_tone", "")
        stage = dialogue_state.get("stage", "")

        signals = GrowthSignals()
        if theme_key:
            signals.detected_themes = [theme_key]

        # 基于阶段推断信号
        # listen 阶段：用户表达情绪，fear 可能高
        # explore 阶段：用户探索问题，awareness 可能上升
        # reflect 阶段：用户反思，awareness 上升
        # understand 阶段：用户理解自己，awareness + action 可能上升

        if stage in ("listen", "explore"):
            # 用户还在表达情绪，fear 可能较高（但这是正常的）
            # 不做特殊处理
            pass
        elif stage == "reflect":
            # 用户在反思，awareness 上升
            signals.awareness_delta = 0.2
            signals.signal_evidence.append(f"stage_reflect:{stage}")
        elif stage == "understand":
            # 用户在理解自己，awareness + action 可能上升
            signals.awareness_delta = 0.25
            signals.action_delta = 0.15
            signals.signal_evidence.append(f"stage_understand:{stage}")

        # 基于情绪色调调整
        if emotional_tone in ("calm", "hopeful", "reflective"):
            signals.fear_delta = -0.1  # 情绪平稳，略微正念
        elif emotional_tone in ("anxious", "frustrated", "confused"):
            signals.fear_delta = 0.1  # 情绪紧张，轻微恐惧

        signals.confidence = 0.5  # 从对话状态推断置信度较低
        return signals


# ============================================================================
# 便捷函数
# ============================================================================

def analyze_growth_signals(
    user_message: str,
    conversation_context: dict[str, Any] | None = None,
) -> GrowthSignals:
    """便捷函数：分析成长信号"""
    analyzer = GrowthSignalAnalyzer()
    return analyzer.analyze(user_message, conversation_context)


def analyze_from_dialogue_state(
    dialogue_state: dict[str, Any],
) -> GrowthSignals:
    """便捷函数：从对话状态分析成长信号"""
    analyzer = GrowthSignalAnalyzer()
    return analyzer.analyze_from_dialogue_state(dialogue_state)
