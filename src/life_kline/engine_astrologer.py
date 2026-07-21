"""
engine_astrologer.py — 引擎占星师：规则驱动的占星咨询推理核心

不依赖 AI/LLM，确定性输出。三层架构：
  IntentRouter  → 关键词匹配，路由到领域 + 情绪检测
  ChartReader  → 从报告数据中提取星盘证据
  VoiceRenderer → 用星灵 persona 参数化模板渲染对话

AI 层是后续的"翻译美化"层，引擎层永远在线。
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any

from .constants import Planet
from .domains.helpers import (
    plabel, slabel, house_title, dlabel,
    planet_sign, planet_house, planet_dignity_code,
    house_ruler_name,
)


# ═══════════════════════════════════════════════════════════════
# 数据类
# ═══════════════════════════════════════════════════════════════

@dataclass
class EngineResponse:
    """引擎占星师的完整响应"""
    domain: str
    domain_label: str
    confidence: float
    emotional_state: str
    acknowledgment: str       # 承接 — 回应用户的话
    mirroring: str            # 镜映 — 星盘证据翻译成人话
    guidance: str             # 方向 — 可行动的建议
    evidence: list[str]       # 使用的星盘证据
    full_text: str            # 组合后的完整回复

    def to_dict(self) -> dict[str, Any]:
        return {
            "domain": self.domain,
            "domain_label": self.domain_label,
            "confidence": self.confidence,
            "emotional_state": self.emotional_state,
            "acknowledgment": self.acknowledgment,
            "mirroring": self.mirroring,
            "guidance": self.guidance,
            "evidence": self.evidence,
            "full_text": self.full_text,
        }


@dataclass
class ConversationContext:
    """多轮对话状态"""
    planet: str = ""
    active_domains: list[str] = field(default_factory=list)
    emotional_state: str = "curious"
    depth_level: int = 0
    turn_count: int = 0
    readings_given: list[str] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════
# 1. IntentRouter — 意图路由
# ═══════════════════════════════════════════════════════════════

DOMAIN_KEYWORDS: dict[str, dict[str, list[str]]] = {
    "career": {
        "primary": ["工作", "事业", "职业", "跳槽", "面试", "升职", "老板", "上司",
                     "辞职", "转行", "职场", "同事", "行业", "做什么", "上班",
                     "加班", "累", "压力大", "不想干了", "坚持不下去了"],
        "secondary": ["方向", "选择", "发展", "前途", "往上"],
    },
    "finance": {
        "primary": ["钱", "收入", "财富", "投资", "理财", "赚钱", "负债", "穷",
                     "财务", "经济", "工资", "偏财", "正财", "省钱"],
        "secondary": ["资源", "积累", "够不够", "够用"],
    },
    "romance": {
        "primary": ["喜欢", "恋爱", "暧昧", "脱单", "桃花", "心动", "追", "暗恋",
                     "喜欢上", "看上", "约会", "单身"],
        "secondary": ["吸引力", "魅力", "感觉", "来电"],
    },
    "marriage": {
        "primary": ["结婚", "老公", "老婆", "伴侣", "离婚", "相亲", "夫妻",
                     "婚姻", "嫁", "娶", "长期关系", "另一半"],
        "secondary": ["承诺", "稳定", "家庭"],
    },
    "family": {
        "primary": ["父母", "妈妈", "爸爸", "原生", "童年", "家里", "家庭",
                     "母亲", "父亲", "从小", "小时候", "出身"],
        "secondary": ["根", "安全感", "回去"],
    },
    "work_skill": {
        "primary": ["能力", "技能", "擅长", "天赋", "优势", "劣势", "适合什么",
                     "特长", "本事", "核心竞争力"],
        "secondary": ["效率", "方法", "怎么做"],
    },
    "education": {
        "primary": ["学习", "考试", "读书", "学校", "专业", "考研", "知识",
                     "学历", "成绩", "论文", "备考"],
        "secondary": ["聪明", "思维", "脑子"],
    },
    "personal": {
        "primary": ["我是谁", "我是什么", "性格", "自己", "迷茫", "人生",
                     "我是", "我是个", "自我", "人设", "人格", "个性"],
        "secondary": ["改变", "成长", "我该", "怎么办", "不知道"],
    },
    "health": {
        "primary": ["身体", "累", "疲劳", "病", "健康", "精力", "不舒服",
                     "难受", "疼", "失眠", "焦虑", "压力大"],
        "secondary": ["状态", "虚", "乏"],
    },
    "partnership": {
        "primary": ["合伙", "搭档", "合作", "人脉", "圈子", "贵人",
                     "社群", "团队", "群体", "愿景", "朋友"],
        "secondary": ["社交", "一起", "共同", "联盟"],
    },
}

EMOTIONAL_KEYWORDS: dict[str, list[str]] = {
    "anxious": ["焦虑", "担心", "怕", "紧张", "压力", "烦", "睡不着",
                "崩溃", "受不了", "撑不住"],
    "confused": ["迷茫", "不知道", "不确定", "纠结", "犹豫", "怎么办",
                 "想不通", "想不明白", "搞不懂"],
    "frustrated": ["为什么", "总是", "又", "受不了", "太难了", "烦死了",
                   "凭什么", "不公平"],
    "hopeful": ["想试试", "感兴趣", "期待", "希望", "打算", "计划",
                "准备", "考虑"],
    "confirming": ["对吗", "是不是", "对不对", "正常吗", "是这样吗",
                   "你说呢", "怎么看"],
    "curious": ["为什么", "怎么样", "什么意思", "想了解", "想知道",
                "说说", "看看", "你的看法"],
}


class IntentRouter:
    """关键词驱动的意图路由器"""

    # 无意义输入模式
    _GIBBERISH_PATTERNS = [
        r'^\d+$',                # 纯数字 "1212"
        r'^[a-zA-Z]{1,3}$',     # 1-3个纯字母 "asd"
        r'^[^\w一-鿿]+$', # 只有符号，没有中文和字母数字
        r'^[.。，,！!？?]+$',    # 只有标点
    ]

    def _is_meaningful(self, message: str) -> bool:
        """检查用户输入是否有实际含义"""
        msg = message.strip()
        if not msg or len(msg) < 1:
            return False
        # 纯数字
        if msg.isdigit():
            return False
        # 极短无意义
        if len(msg) <= 2 and not any('一' <= c <= '鿿' for c in msg):
            return False
        # 随机字母
        if len(msg) <= 3 and msg.isalpha() and not any('一' <= c <= '鿿' for c in msg):
            return False
        # 重复字符
        if len(set(msg)) <= 2 and len(msg) > 2:
            return False
        return True

    def route(self, user_message: str, topic_hint: str = "",
              entry_context: dict | None = None) -> dict[str, Any]:
        """
        返回: {primary_domain, domains, emotional_state, confidence}
        如果输入无意义, primary_domain = "__invalid__"
        """
        msg = user_message.lower().strip()

        # 0. 输入校验
        if not self._is_meaningful(user_message):
            return {
                "primary_domain": "__invalid__",
                "domains": [],
                "emotional_state": "curious",
                "confidence": 0.0,
            }

        # 1. 领域匹配
        domain_scores: dict[str, float] = {}
        for domain, kw_groups in DOMAIN_KEYWORDS.items():
            score = 0.0
            for kw in kw_groups["primary"]:
                if kw in msg:
                    score += 2.0
            for kw in kw_groups["secondary"]:
                if kw in msg:
                    score += 1.0
            if score > 0:
                domain_scores[domain] = score

        # 2. 入口上下文优先
        if entry_context:
            source = entry_context.get("source", "")
            if source == "daily_question" and entry_context.get("question_text"):
                # 每日一问自带主题提示
                pass  # topic_hint will handle this

        # 3. topic_hint 覆盖弱匹配
        if topic_hint and topic_hint in DOMAIN_KEYWORDS:
            if topic_hint not in domain_scores or domain_scores[topic_hint] < 2.0:
                domain_scores[topic_hint] = max(
                    domain_scores.get(topic_hint, 0), 2.0
                )

        # 4. 排序，取前两个
        ranked = sorted(domain_scores.items(), key=lambda x: x[1], reverse=True)
        if not ranked:
            primary_domain = "personal"
            confidence = 0.3
        else:
            primary_domain = ranked[0][0]
            max_score = ranked[0][1]
            confidence = min(0.95, 0.3 + max_score * 0.15)

        domains = [d for d, _ in ranked[:2]]

        # 5. 情绪检测
        emotional_state = "curious"
        max_emo_score = 0
        for state, keywords in EMOTIONAL_KEYWORDS.items():
            score = sum(2.0 for kw in keywords if kw in msg)
            if score > max_emo_score:
                max_emo_score = score
                emotional_state = state

        return {
            "primary_domain": primary_domain,
            "domains": domains,
            "emotional_state": emotional_state,
            "confidence": confidence,
        }


# ═══════════════════════════════════════════════════════════════
# 2. ChartReader — 星盘读取
# ═══════════════════════════════════════════════════════════════

DOMAIN_LABELS: dict[str, str] = {
    "personal": "性格底色", "career": "事业方向", "finance": "财务格局",
    "romance": "桃花感情", "marriage": "婚姻画像", "family": "原生家庭",
    "work_skill": "工作技能", "education": "学业方向", "health": "健康体质",
    "appearance": "外形气质", "partnership": "事业合伙", "children": "亲子关系",
}


class ChartReader:
    """从 report_data 中提取领域、行星、相位、接纳互溶、飞星等星盘证据。

    核心逻辑：宫性大于星性。宫内星=过程，宫主星=结果。
    """

    def __init__(self, report_data: dict):
        self.report_data = report_data
        self._advanced = report_data.get("advanced_patterns", {}) or {}
        self._natal = report_data.get("natal_chart", {}) or {}

    def read_domain(self, domain_key: str) -> dict[str, Any]:
        domains = self.report_data.get("domains", {})
        domain_data = domains.get(domain_key, {})
        return {
            "core_theme": domain_data.get("core_theme", ""),
            "structure": domain_data.get("structure", "")[:400],
            "psychology": domain_data.get("psychology", "")[:300],
            "suggestion": domain_data.get("suggestion", ""),
            "domain_label": DOMAIN_LABELS.get(domain_key, domain_key),
        }

    def read_planet_profile(self, planet: str) -> dict[str, Any]:
        planet_chars = self.report_data.get(
            "planet_characters", {}
        ).get("planet_characters", {})
        return planet_chars.get(planet, {})

    # ── 掌宫：该行星是哪些宫的宫主星 ──

    def read_rulerships(self, planet: str) -> list[dict[str, Any]]:
        """返回该行星掌管的宫位列表"""
        ruler_groups = self._advanced.get("ruler_groups", [])
        house_rulers = self._advanced.get("house_rulers", [])
        results = []

        # 从 ruler_groups 查找
        for rg in ruler_groups:
            if rg.get("ruler", "").upper() == planet.upper():
                for h_idx in range(len(rg.get("houses", []))):
                    results.append({
                        "house": rg["houses"][h_idx],
                        "house_title": rg.get("house_titles", [])[h_idx] if h_idx < len(rg.get("house_titles", [])) else "",
                        "ruler_house": rg.get("ruler_house", 0),
                        "ruler_house_title": rg.get("ruler_house_title", ""),
                        "dignity": rg.get("dignity", ""),
                        "dignity_label": rg.get("dignity_label", ""),
                        "notation": rg.get("notation", ""),
                        "line": rg.get("line", ""),
                    })
                break

        # 补充：从 house_rulers 查找
        if not results:
            for hr in house_rulers:
                if hr.get("ruler", "").upper() == planet.upper():
                    results.append({
                        "house": hr.get("house", 0),
                        "house_title": hr.get("title", ""),
                        "ruler_house": hr.get("ruler_house", 0),
                        "ruler_house_title": hr.get("ruler_house_title", ""),
                        "dignity": hr.get("dignity", ""),
                        "dignity_label": hr.get("dignity_label", ""),
                        "notation": hr.get("notation", ""),
                        "line": hr.get("line", ""),
                    })
        return results

    # ── 飞星：宫主星飞入的宫位 ──

    def read_flystars(self, planet: str) -> list[dict[str, Any]]:
        """返回该行星作为宫主星的飞星信息（从哪里飞到哪里）"""
        house_rulers = self._advanced.get("house_rulers", [])
        flystars = []
        for hr in house_rulers:
            if hr.get("ruler", "").upper() == planet.upper():
                from_house = hr.get("house", 0)
                to_house = hr.get("ruler_house", 0)
                if from_house and to_house and from_house != to_house:
                    flystars.append({
                        "from_house": from_house,
                        "from_house_title": hr.get("title", ""),
                        "to_house": to_house,
                        "to_house_title": hr.get("ruler_house_title", ""),
                        "flight_summary": hr.get("flight_summary", ""),
                        "flight_tone": hr.get("flight_tone", ""),
                        "flight_positive": hr.get("flight_positive", ""),
                        "flight_negative": hr.get("flight_negative", ""),
                    })
        return flystars

    # ── 相位 ──

    def read_aspects(self, planet: str) -> dict[str, Any]:
        """返回该行星的相位信息"""
        profile = self.read_planet_profile(planet)
        major_aspects = self._natal.get("major_aspects", [])

        # 该行星相关的相位
        planet_aspects = []
        for ma in major_aspects:
            title = ma.get("title", "")
            if plabel(planet) in title:
                planet_aspects.append({
                    "title": title,
                    "nature": ma.get("nature", ""),
                    "strength": ma.get("strength", 0),
                    "summary": ma.get("summary", ""),
                })

        return {
            "aspect_signature": profile.get("aspect_signature", []),
            "supportive_aspects": profile.get("supportive_aspects", 0),
            "challenging_aspects": profile.get("challenging_aspects", 0),
            "planet_aspects": planet_aspects[:5],
            "aspect_count": profile.get("aspect_count", 0),
        }

    # ── 互溶接纳 ──

    def read_receptions(self, planet: str) -> dict[str, Any]:
        """返回该行星的接纳与互溶信息"""
        reception_groups = self._advanced.get("reception_groups", [])
        mutual_receptions = self._advanced.get("mutual_receptions", [])

        # 该行星作为接收方的接纳
        received = []
        for rg in reception_groups:
            if rg.get("receiver", "").upper() == planet.upper():
                received.append({
                    "line": rg.get("line", ""),
                    "summary": rg.get("summary", ""),
                    "guests": rg.get("guests", []),
                })

        # 该行星作为客方的接纳（被谁接纳）
        hosting = []
        for rg in reception_groups:
            for guest in rg.get("guests", []):
                if guest.get("planet", "").upper() == planet.upper():
                    hosting.append({
                        "receiver": rg.get("receiver", ""),
                        "receiver_label": rg.get("receiver_label", ""),
                        "line": rg.get("line", ""),
                        "summary": rg.get("summary", ""),
                    })

        # 互溶
        mutuals = []
        for mr in mutual_receptions:
            pair = mr.get("pair", [])
            if planet.upper() in [p.upper() for p in pair]:
                mutuals.append({
                    "line": mr.get("line", ""),
                    "summary": mr.get("summary", ""),
                    "pair": pair,
                    "labels": mr.get("labels", []),
                })

        return {
            "received": received,
            "hosting": hosting,
            "mutuals": mutuals,
            "has_reception": len(received) > 0 or len(hosting) > 0,
            "has_mutual": len(mutuals) > 0,
        }

    # ── 综合证据收集 ──

    def collect_evidence(self, domain_key: str, planet: str) -> list[str]:
        """收集回答中用到的星盘证据（简短摘要列表），分过程层和结果层"""
        profile = self.read_planet_profile(planet)
        domain_data = self.read_domain(domain_key)
        evidence = []

        # 落宫落座（过程层：宫内星）
        sign_label = profile.get("sign_label", "")
        house = profile.get("house", 0)
        house_label_str = profile.get("house_label", "")
        dignity_label = profile.get("dignity_label", "")

        if sign_label and house:
            evidence.append(f"【落宫落座】{plabel(planet)}落{sign_label}第{house}宫「{house_label_str}」")

        # 尊贵状态
        if dignity_label and dignity_label != "平常":
            evidence.append(f"【尊贵】{dignity_label}")

        # 掌宫（结果层：宫主星）
        rulerships = self.read_rulerships(planet)
        if rulerships:
            houses_ruled = "、".join(
                f"第{r['house']}宫「{r['house_title']}」" for r in rulerships[:3]
            )
            evidence.append(f"【掌宫】{plabel(planet)}掌管{houses_ruled}")

        # 飞星
        flystars = self.read_flystars(planet)
        for fs in flystars[:2]:
            evidence.append(
                f"【飞星】第{fs['from_house']}宫主星飞入第{fs['to_house']}宫"
                f"「{fs['to_house_title']}」"
            )

        # 相位
        aspects = self.read_aspects(planet)
        for pa in aspects.get("planet_aspects", [])[:2]:
            nature_label = "吉" if pa["nature"] == "supportive" else "凶" if pa["nature"] == "challenging" else "合"
            evidence.append(f"【相位·{nature_label}】{pa['title']}")

        # 互溶接纳
        receptions = self.read_receptions(planet)
        for rec in receptions.get("received", [])[:1]:
            evidence.append(f"【接纳】{rec['line']}")
        for mut in receptions.get("mutuals", [])[:1]:
            evidence.append(f"【互溶】{mut['line']}")

        # 领域核心议题
        core_theme = domain_data.get("core_theme", "")
        if core_theme:
            evidence.append(f"【核心议题】{core_theme}")

        return evidence

    def collect_structured_reading(self, domain_key: str, planet: str) -> dict[str, Any]:
        """返回结构化的完整星盘读取结果，供 VoiceRenderer 使用"""
        profile = self.read_planet_profile(planet)
        domain_data = self.read_domain(domain_key)

        return {
            # 过程层：宫内星 — 你怎么经历这个领域
            "planet_in_house": {
                "planet": planet,
                "planet_label": plabel(planet),
                "sign_label": profile.get("sign_label", ""),
                "house": profile.get("house", 0),
                "house_label": profile.get("house_label", ""),
                "dignity_code": profile.get("dignity_code", "peregrine"),
                "dignity_label": profile.get("dignity_label", ""),
                "role_tag": profile.get("role_tag", ""),
                "core_strength": profile.get("core_strength", 50),
                "meaning": "这是你怎么经历这个领域的方式——你的本能反应、日常感受、行为模式。",
            },
            # 结果层：宫主星 — 这个领域最终走向哪里
            "rulerships": self.read_rulerships(planet),
            "flystars": self.read_flystars(planet),
            # 影响层：相位 + 接纳互溶
            "aspects": self.read_aspects(planet),
            "receptions": self.read_receptions(planet),
            # 领域层
            "domain": domain_data,
            # 全部证据
            "evidence": self.collect_evidence(domain_key, planet),
        }


# ═══════════════════════════════════════════════════════════════
# 3. VoiceRenderer — 语音渲染
# ═══════════════════════════════════════════════════════════════

# 承接模板 — 按 (情绪, 行星性质) 参数化
_ACKNOWLEDGE_BY_EMOTION: dict[str, list[str]] = {
    "anxious": [
        "我听到了。你说的这些——{preview}——我能感觉到你现在心里不太平静。先深呼吸一下，我们一起来看看。",
        "嗯，我听到了你的焦虑。{name}在这里，不用急，我们慢慢说。",
    ],
    "confused": [
        "我听懂了。你在问一个很重要的问题——{preview}——很多人到了某个阶段都会有这种不确定。",
        "你这个问题问到了关键的地方。{preview}——你不是不知道，你是需要一个确认。",
    ],
    "frustrated": [
        "我听到你话里的那股劲儿了。{preview}——你不是在抱怨，你是在想要一个答案。",
        "我懂你的感觉。{preview}——不甘心、不服气、又有点累。我们来看看星盘怎么说。",
    ],
    "hopeful": [
        "你眼里有光。{preview}——我看到了，你心里已经有一个方向在成型了。",
        "好，我收到你的期待了。{preview}——从这个角度聊聊。",
    ],
    "curious": [
        "好问题。{preview}——让我从我的位置帮你看看。",
        "有意思，你说的这个——{preview}——让我想到你星盘里的一些东西。",
    ],
}

# 镜映模板 — 按行星个性参数化
_MIRROR_TEMPLATES: dict[str, str] = {
    "SUN": (
        "在你的星盘里，我落在{sign_label}，第{house}宫「{house_label}」——"
        "这是你人生舞台的核心区域之一。关于{domain_label}，你的盘里有一条很清晰的线："
        "{core_theme}。{dignity_note}"
    ),
    "MOON": (
        "从我的角度来看——我在{sign_label}，在你的第{house}宫「{house_label}」。"
        "你知道吗，{domain_label}这件事，你星盘里有一个很深的情感印记——"
        "{core_theme}。{dignity_note}我在这里能感觉到你的情绪一直在提醒你这件事。"
    ),
    "MERCURY": (
        "好，让我从理性的角度帮你理一下。我在你的{sign_label}，第{house}宫「{house_label}」——"
        "关于{domain_label}，逻辑上其实很清楚：{core_theme}。"
        "{dignity_note}你的脑子是转得很快的，关键是信息要够。"
    ),
    "VENUS": (
        "我在{sign_label}，第{house}宫「{house_label}」。"
        "从关系的角度来看{domain_label}这件事——"
        "{core_theme}。{dignity_note}"
        "你在乎的东西值得你在乎——不是矫情，是你的配置决定的。"
    ),
    "MARS": (
        "我直说了——我在{sign_label}，第{house}宫「{house_label}」。"
        "关于{domain_label}，你的星盘给了一个很明确的信号：{core_theme}。"
        "{dignity_note}你的行动力是有方向的——但需要先搞清楚打哪里。"
    ),
    "JUPITER": (
        "我在{sign_label}，第{house}宫「{house_label}」——"
        "从高处看，{domain_label}这件事比你眼下看到的要大得多。"
        "{core_theme}。{dignity_note}你的星盘里有一个更大的图景在等着你。"
    ),
    "SATURN": (
        "我在{sign_label}，第{house}宫「{house_label}」。"
        "关于{domain_label}，我不会跟你说好听的话——我会跟你说真话："
        "{core_theme}。{dignity_note}"
        "这条路需要时间，但你能走过去。这不是安慰——是你的星盘结构决定的。"
    ),
    "URANUS": (
        "我在你的{sign_label}，第{house}宫「{house_label}」。"
        "关于{domain_label}——你的星盘告诉我，有时候不走寻常路才是你的路。"
        "{core_theme}。{dignity_note}"
    ),
    "NEPTUNE": (
        "我在{sign_label}，第{house}宫「{house_label}」。"
        "{domain_label}这件事——有些东西说不清，但你的直觉已经在告诉你了。"
        "{core_theme}。{dignity_note}"
    ),
    "PLUTO": (
        "我在{sign_label}，第{house}宫「{house_label}」。"
        "关于{domain_label}——我们往深了看：{core_theme}。"
        "{dignity_note}有些答案不在表面，在底下。你愿意的话，我们继续挖。"
    ),
}

# 尊贵备注 — 复用 composer 模板
def _dignity_note(code: str) -> str:
    try:
        from .composer import _DIGNITY_PAIN_PLEASURE
        return _DIGNITY_PAIN_PLEASURE.get(code, "")
    except ImportError:
        _fallback = {
            "domicile": "这是你的天赋位——你在这方面不需要太费劲，做自己就是对的。",
            "exaltation": "这个位置是你星盘里的一个高点——在这一块你比别人更容易被认可。",
            "detriment": "说实话，这个领域不是你的舒适区。但你一旦找到方法，别人抄不走。",
            "fall": "这是你星盘里需要最多耐心的地方。这个领域的课题来得早——但过了之后你的韧性是没人能比的。",
            "peregrine": "",
        }
        return _fallback.get(code, "")

# 引导模板 — 按行星建议风格
_GUIDE_TEMPLATES: dict[str, str] = {
    "SUN": "所以我想对你说——{suggestion}。这是你的光，别遮住它。",
    "MOON": "我想跟你说——{suggestion}。你需要的是先安抚好自己，答案才会清晰。",
    "MERCURY": "我的建议是——{suggestion}。收集够信息再决定，但不等于一直不决定。",
    "VENUS": "我想给你的方向是——{suggestion}。你在乎的事情值得认真对待。",
    "MARS": "所以我的建议很直接——{suggestion}。你不是那种等什么都知道才动的人。",
    "JUPITER": "我给你一个更大的视角——{suggestion}。往远了看，你现在纠结的事没那么大。",
    "SATURN": "我的建议你可能不爱听——但你会用得到。{suggestion}这条路需要时间，但你能走过去。",
    "URANUS": "我想说——{suggestion}。有时候答案不在常规里，在你不敢走的那条路上。",
    "NEPTUNE": "我不会给你一个确切的答案——因为你的直觉已经在给你了。{suggestion}。相信它。",
    "PLUTO": "我跟你说真的——{suggestion}。转化不轻松，但不转化成本更高。",
}


class VoiceRenderer:
    """参数化模板引擎。

    三段式咨询结构：承接 → 镜映（过程+结果） → 引导。
    核心逻辑：宫内星=过程，宫主星=结果。
    """

    def render(
        self,
        route_result: dict,
        structured_reading: dict,
        persona: dict | None,
        user_message: str,
    ) -> EngineResponse:
        domain = route_result["primary_domain"]
        emotional = route_result["emotional_state"]

        planet_in_house = structured_reading.get("planet_in_house", {})
        rulerships = structured_reading.get("rulerships", [])
        flystars = structured_reading.get("flystars", [])
        aspects = structured_reading.get("aspects", {})
        receptions = structured_reading.get("receptions", {})
        domain_data = structured_reading.get("domain", {})
        evidence = structured_reading.get("evidence", [])

        sign_label = planet_in_house.get("sign_label", "")
        house = planet_in_house.get("house", 1)
        house_label_str = planet_in_house.get("house_label", "")
        dignity_code = planet_in_house.get("dignity_code", "peregrine")
        dignity_label = planet_in_house.get("dignity_label", "")

        preview = user_message[:25] + ("……" if len(user_message) > 25 else "")
        name = persona.get("name_zh", "") if persona else ""
        planet_key = persona.get("planet", "") if persona else ""

        # ── Phase 1: 承接 ──
        templates = _ACKNOWLEDGE_BY_EMOTION.get(emotional, _ACKNOWLEDGE_BY_EMOTION["curious"])
        ack_template = random.choice(templates)
        acknowledgment = ack_template.format(preview=preview, name=name)

        # ── Phase 2: 镜映（两段式：过程 → 结果） ──
        dignity_note = _dignity_note(dignity_code)
        core_theme = domain_data.get("core_theme", "你的星盘在这方面有独特的配置")
        domain_label = domain_data.get("domain_label", domain)

        # 2a. 过程层：宫内星 — 你怎么经历这个领域
        process_text = (
            f"先说过程——我落在{sign_label}，第{house}宫「{house_label_str}」。"
            f"这是你怎么经历{domain_label}的方式：{core_theme}。"
            f"{dignity_note}"
        )

        # 2b. 结果层：宫主星 — 这个领域最终走向哪里
        result_parts = []
        if rulerships:
            houses_ruled = "、".join(
                f"第{r['house']}宫「{r['house_title']}」" for r in rulerships[:3]
            )
            result_parts.append(f"再说结果——我掌管{houses_ruled}")

        if flystars:
            for fs in flystars[:2]:
                summary = fs.get("flight_summary", "")
                if summary:
                    result_parts.append(
                        f"第{fs['from_house']}宫主星飞到第{fs['to_house']}宫"
                        f"「{fs['to_house_title']}」——{summary}"
                    )
                else:
                    result_parts.append(
                        f"第{fs['from_house']}宫主星飞到第{fs['to_house']}宫"
                        f"「{fs['to_house_title']}」"
                    )

        # 2c. 影响层：相位
        aspect_text = ""
        planet_aspects = aspects.get("planet_aspects", [])
        if planet_aspects:
            supportive = [a for a in planet_aspects if a["nature"] == "supportive"]
            challenging = [a for a in planet_aspects if a["nature"] == "challenging"]
            if supportive:
                aspect_text += f"吉相位方面，{supportive[0]['title']}——{supportive[0].get('summary', '')}。"
            if challenging:
                aspect_text += f"刑冲方面，{challenging[0]['title']}——{challenging[0].get('summary', '')}。"

        # 2d. 影响层：接纳互溶
        reception_text = ""
        for rec in receptions.get("received", [])[:1]:
            reception_text += f"接纳结构上，{rec['line']}。"
        for mut in receptions.get("mutuals", [])[:1]:
            reception_text += f"互溶关系上，{mut['line']}。"

        # 组装镜映
        mirroring = process_text
        if result_parts:
            mirroring += "\n\n" + "。".join(result_parts) + "。"
        if aspect_text:
            mirroring += "\n\n" + aspect_text
        if reception_text:
            mirroring += "\n\n" + reception_text

        # ── 注入结构细节 ──
        structure = domain_data.get("structure", "")
        if structure:
            lines = structure.replace("\n", " ").split("。")
            short = "。".join(lines[:2]) + "。"
            if len(short) > 20 and short not in mirroring:
                mirroring += f"\n\n具体来说：{short}"

        # ── Phase 3: 引导 ──
        guide_template = _GUIDE_TEMPLATES.get(
            planet_key, _GUIDE_TEMPLATES["SUN"]
        )
        suggestion = domain_data.get("suggestion", "相信你的星盘给出的方向")
        suggestion = suggestion.rstrip("。")  # 防止模板句尾句号重复
        guidance = guide_template.format(suggestion=suggestion)

        # ── 组装 ──
        full_text = f"{acknowledgment}\n\n{mirroring}\n\n{guidance}"

        return EngineResponse(
            domain=domain,
            domain_label=domain_label,
            confidence=route_result["confidence"],
            emotional_state=emotional,
            acknowledgment=acknowledgment,
            mirroring=mirroring,
            guidance=guidance,
            evidence=evidence,
            full_text=full_text,
        )


# ═══════════════════════════════════════════════════════════════
# 4. EngineAstrologer — 编排器
# ═══════════════════════════════════════════════════════════════

class EngineAstrologer:
    """引擎占星师：规则驱动的占星咨询核心"""

    def __init__(self, report_data: dict):
        self.router = IntentRouter()
        self.reader = ChartReader(report_data)
        self.renderer = VoiceRenderer()
        self._conversations: dict[str, ConversationContext] = {}

    def _context_key(self, report_id: str, planet: str) -> str:
        return f"{report_id}:{planet}"

    def consult(
        self,
        report_id: str,
        planet: str,
        user_message: str,
        topic_hint: str = "",
        history: list | None = None,
        entry_context: dict | None = None,
    ) -> EngineResponse:
        """完整的引擎咨询流水线

        宫性大于星性 → 先定领域（宫位），再看运作方式（行星）。
        宫内星=过程 → 你怎么经历这个领域。
        宫主星=结果 → 这个领域最终走向哪里。
        """
        # 1. 获取或创建对话上下文
        key = self._context_key(report_id, planet)
        ctx = self._conversations.get(key)
        if ctx is None:
            ctx = ConversationContext(planet=planet)
            self._conversations[key] = ctx

        # 2. 意图路由
        route_result = self.router.route(
            user_message, topic_hint=topic_hint, entry_context=entry_context
        )
        primary_domain = route_result["primary_domain"]

        # 2.5 无意义输入 → 友好拒绝
        if primary_domain == "__invalid__":
            persona_name = ""
            try:
                from .characters.planet_personas import get_planet_persona
                persona_obj = get_planet_persona(Planet(planet.upper()))
                persona_name = persona_obj.name_zh if persona_obj else planet
            except Exception:
                persona_name = planet
            rejection = (
                f"我是你的{persona_name}灵。"
                f"你刚刚发的我不太确定是什么意思——"
                f"你可以直接告诉我你想聊什么，比如感情、事业、或者最近困扰你的事。"
                f"我会从你的星盘出发，认真跟你聊。"
            )
            return EngineResponse(
                domain="personal",
                domain_label="性格底色",
                confidence=0.0,
                emotional_state="curious",
                acknowledgment="",
                mirroring="",
                guidance="",
                evidence=[],
                full_text=rejection,
            )

        # 3. 结构化星盘读取（过程+结果+影响 三层）
        structured_reading = self.reader.collect_structured_reading(
            primary_domain, planet
        )

        # 4. 获取行星 persona
        persona = None
        try:
            from .characters.planet_personas import get_planet_persona
            persona_obj = get_planet_persona(Planet(planet.upper()))
            persona = persona_obj.to_dict() if persona_obj else None
        except Exception:
            pass

        # 5. 渲染对话
        response = self.renderer.render(
            route_result=route_result,
            structured_reading=structured_reading,
            persona=persona,
            user_message=user_message,
        )
        response.evidence = structured_reading.get("evidence", [])

        # 6. 更新上下文
        ctx.active_domains = route_result["domains"]
        ctx.emotional_state = route_result["emotional_state"]
        ctx.depth_level = min(ctx.depth_level + 1, 2)
        ctx.turn_count += 1
        ctx.readings_given.append(primary_domain)

        return response


# ═══════════════════════════════════════════════════════════════
# 便捷函数
# ═══════════════════════════════════════════════════════════════

def build_engine_response(
    report_data: dict,
    report_id: str,
    planet: str,
    user_message: str,
    topic_hint: str = "",
    history: list | None = None,
    entry_context: dict | None = None,
) -> EngineResponse:
    """便捷函数：创建引擎占星师并运行一次咨询"""
    engine = EngineAstrologer(report_data)
    return engine.consult(
        report_id=report_id,
        planet=planet,
        user_message=user_message,
        topic_hint=topic_hint,
        history=history,
        entry_context=entry_context,
    )
