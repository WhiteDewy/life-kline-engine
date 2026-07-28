"""
narrative.py — AKG 主题叙事生成 + ACP-0003 Narrative Schema

build_theme_narrative(theme, report_data) -> str
匹配既有 seam（consultation_engine.py:805），返回 ACP 合规的 prose 字符串。

build_narrative(theme, report_data) -> Narrative
产出 ACP-0003 七字段结构化 Narrative（Theme/Origin/Evidence/Psychology/
Pattern/Healing Goal/Growth），挂到 ThemeNode.narrative_schema，
经既有 recognized_themes 持久化路径自动落盘（state_json / report_json）。

铁律：只引用 ThemeNode.evidence 里已算好的星盘事实，不重新解读。
ACP 合规：经 acp.sanitize_fatalism 后处理，禁用"注定/一定/必须"。
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..acp import NARRATIVE_SCHEMA_FIELDS, sanitize_fatalism
from .recognizer import ThemeNode


# ============================================================================
# ACP-0003 Narrative Schema
# ============================================================================

@dataclass
class Narrative:
    """ACP-0003 七字段人生叙事——整个产品最重要的数据对象。"""
    theme: str = ""            # 主题点题
    origin: str = ""           # 发展性根源
    evidence: list[str] = field(default_factory=list)   # 星盘证据
    psychology: str = ""       # 心理模式
    pattern: str = ""          # 重复模式
    healing_goal: str = ""     # 疗愈方向
    growth: str = ""           # 成长轨迹（初始空，由纵向记忆填充）

    def to_dict(self) -> dict:
        return {f: getattr(self, f) for f in NARRATIVE_SCHEMA_FIELDS}

    def render(self) -> str:
        """渲染成 ACP 合规的 prose 段落。"""
        if not self.theme:
            return ""
        parts = [f"关于「{self.theme}」", ""]
        if self.origin:
            parts.append(self.origin)
        if self.evidence:
            parts.append("从你的星盘里，我注意到这些线索：")
            parts.extend(f"· {e}" for e in self.evidence)
        if self.psychology:
            parts.append("")
            parts.append(self.psychology)
        if self.pattern:
            parts.append("")
            parts.append(self.pattern)
        if self.healing_goal:
            parts.append("")
            parts.append(self.healing_goal)
        if self.growth:
            parts.append("")
            parts.append(self.growth)
        return "\n".join(parts)


# ============================================================================
# per-theme 模板（Origin / Pattern / Healing Goal）
# 规则驱动、泛化，不针对具体个人。
# ============================================================================

_GENERIC = {
    "origin": "这个主题在你的生命里反复出现，往往和更早的经历相连。",
    "pattern": "它容易在你不太留意的时刻再次上演，成为一种熟悉的反应方式。",
    "healing_goal": "看见它，就是改变的开始。学着在它再次出现时，多给自己一个选择。",
}

THEME_NARRATIVE_TEMPLATES: dict[str, dict[str, str]] = {
    "authority": {
        "origin": "这份对权威的敏感，往往来自成长过程中父亲、长辈或其他权威人物较高的期待——你逐渐把「被认可」和「必须做到很好」联系在一起。",
        "pattern": "面对领导、上级或任何评判你的人和场景时，你容易再次启动这种熟悉的心理模式——要么过度用力证明自己，要么退缩不敢发声。",
        "healing_goal": "不必再从外部权威那里讨要认可。学着区分「被要求」和「自己真正想做的事」，在尊重权威的同时保有自己的声音。",
    },
    "intimacy": {
        "origin": "你在亲密关系里的拉扯，往往和早年对「靠近就会受伤」或「被爱是有条件的」体验有关。",
        "pattern": "一旦关系变近，你容易在「想要靠近」和「害怕失去自我」之间来回摇摆——要么全情投入忘了自己，要么一感到威胁就先撤退。",
        "healing_goal": "亲密不必以失去自我为代价。学着在关系中既敞开又保持边界，允许自己被看见，也允许自己有需求。",
    },
    "money": {
        "origin": "你和钱的关系，往往承载着比钱本身更多的东西——安全感、自我价值、或对未知的掌控。",
        "pattern": "面对金钱决策，你容易在「拼命攥紧」和「冲动释放」之间摆动，钱成了情绪的出口而非工具。",
        "healing_goal": "把钱还原成钱。学着区分「安全感的需求」和「真实的财务需要」，建立自己能稳住的节奏。",
    },
    "self_worth": {
        "origin": "那个「我不够好」的声音，多半是很早就种下的——比任何具体成就都早。",
        "pattern": "每当做一件事之前，你容易先自我审查、压低自己，把外在成就当成衡量自身价值的唯一尺子。",
        "healing_goal": "价值不必靠证明。学着看见自己本来的样子就足够，把「做到」和「值得」分开。",
    },
    "safety": {
        "origin": "你对安全感的深切需要，往往根植于早年那些不确定、或情绪未被稳稳接住的时刻。",
        "pattern": "面对不确定，你容易先收紧、先预演最坏情况，用控制来换取一点踏实感。",
        "healing_goal": "安全不等于没有波动。学着在不确定里也能稳住自己，相信自己的承受力比想象中大。",
    },
    "career": {
        "origin": "你对事业方向的反复掂量，背后是「该走现实稳妥的路还是忠于热爱」的长期拉扯。",
        "pattern": "面对职业选择，你容易在「外界期待的好路径」和「内心真正想做的事」之间犹豫，迟迟不敢迈步。",
        "healing_goal": "事业是长跑，不必一次想清楚。学着用小步试错代替反复权衡，让行动带你澄清方向。",
    },
    "communication": {
        "origin": "你在表达上的困难，往往和「说错话会被否定」或「我的感受不重要」的早期体验有关。",
        "pattern": "面对需要表达的场合，你容易要么憋回去、要么一下子冲出来，很难恰如其分地说出心里话。",
        "healing_goal": "表达不必完美。学着先说出口、再调整，允许自己的声音被听见，哪怕一开始笨拙。",
    },
    "growth": {
        "origin": "你对人生意义的反复追问，背后是「活着总要图点什么」的深层渴望。",
        "pattern": "你容易在「追寻远方意义」和「过好眼前日子」之间摇摆，时而充满信念、时而陷入迷茫。",
        "healing_goal": "意义不在远方，在每一天的具体里。学着把信念落地为可行动的小事，让成长从抽象变成可见。",
    },
}


def _psychology_from_polarity(evidence: list[dict]) -> str:
    """从证据极性派生心理模式描述。"""
    if not evidence:
        return ""
    sup = sum(1 for e in evidence if e.get("polarity") == "support")
    chl = sum(1 for e in evidence if e.get("polarity") == "challenge")
    total = sup + chl
    if total == 0:
        return "在这个面向上，你有着独特的体验方式。"
    sup_ratio = sup / total
    if sup_ratio >= 0.6:
        return "在这个面向上，你其实是有底气的——星盘给了你足够的资源，只是你有时没意识到。"
    if sup_ratio <= 0.4:
        return "在这个面向上，你更容易感到压力和恐惧——不是你不行，而是这股能量需要更费力地驾驭。"
    return "在这个面向上，你常常在两种力量之间拉扯——既有想靠近的冲动，也有想退缩的本能。"


# ============================================================================
# 生产 + 渲染
# ============================================================================

def build_narrative(theme: ThemeNode, report_data: dict) -> Narrative:
    """从 ThemeNode + 证据构建 ACP-0003 七字段 Narrative。"""
    if not theme:
        return Narrative()

    tmpl = THEME_NARRATIVE_TEMPLATES.get(theme.key, _GENERIC)
    ev_sorted = sorted(theme.evidence, key=lambda e: e.get("weight", 0), reverse=True)
    ev_lines = [e["text"] for e in ev_sorted[:5] if e.get("text")]

    return Narrative(
        theme=f"{theme.label}——{theme.description}",
        origin=tmpl["origin"],
        evidence=ev_lines,
        psychology=_psychology_from_polarity(theme.evidence),
        pattern=tmpl["pattern"],
        healing_goal=tmpl["healing_goal"],
        growth="",   # 初始空，留给纵向 MemoryManager 填充
    )


def build_theme_narrative(theme: ThemeNode, chart_data: dict) -> str:
    """既有 seam 入口：返回 ACP 合规 prose 字符串。

    副作用：把 7 字段 Narrative 挂到 theme.narrative_schema，
    使其经 recognized_themes 持久化路径自动落盘。
    """
    if not theme or not theme.evidence:
        return ""

    narrative = build_narrative(theme, chart_data)
    # 挂到 ThemeNode，供 to_dict() 序列化进 recognized_themes
    try:
        theme.narrative_schema = narrative.to_dict()
    except Exception:
        pass

    prose = narrative.render()
    if not prose:
        return ""
    return sanitize_fatalism(prose)
