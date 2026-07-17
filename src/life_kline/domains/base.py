"""
领域分析基类（PRD v1.3 §10.1-10.3）

提供：情境偏置系统 + 多角度解释矩阵 + 古占/现占融合 + 核心议题生成。
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


# ── 情境偏置：三级相关制（PRD v1.3 §10.1）───────────────
# 一级 ×2.0 | 二级 ×1.5 | 三级 ×1.2 | 无关 ×1.0

SITUATIONAL_BIASES: dict[str, dict[str, Any]] = {
    "personal": {
        "houses": {"1": 2.0, "10": 1.5, "4": 1.5},
        "planets": {"CHART_RULER": 1.5, "SUN": 1.3, "MOON": 1.3},
    },
    "finance": {
        "houses": {"2": 2.0, "8": 2.0, "5": 1.5, "10": 1.2},
        "planets": {"VENUS": 1.3, "JUPITER": 1.3, "SATURN": 1.2},
    },
    "family": {
        "houses": {"4": 2.0, "10": 2.0, "1": 1.5},
        "planets": {"SUN": 1.3, "MOON": 1.3, "SATURN": 1.2},
    },
    "romance": {
        "houses": {"5": 2.0, "7": 2.0, "1": 1.5, "8": 1.2},
        "planets": {"VENUS": 1.5, "MARS": 1.3, "MOON": 1.3},
    },
    "marriage": {
        "houses": {"7": 2.0, "1": 1.5, "10": 1.2},
        "planets": {"VENUS": 1.3},
    },
    "work_skill": {
        "houses": {"6": 2.0, "3": 1.5, "10": 1.2},
        "planets": {"MERCURY": 1.3},
    },
    "career": {
        "houses": {"10": 2.0, "1": 1.5, "6": 1.5, "2": 1.2},
        "planets": {"SATURN": 1.3, "SUN": 1.2, "MARS": 1.2},
    },
    "education": {
        "houses": {"3": 2.0, "9": 2.0, "1": 1.5},
        "planets": {"MERCURY": 1.5, "JUPITER": 1.5},
    },
    "appearance": {
        "houses": {"1": 2.0, "6": 1.2},
        "planets": {"CHART_RULER": 1.5},
    },
    "partnership": {
        "houses": {"7": 2.0, "10": 1.5, "1": 1.5, "2": 1.2},
        "planets": {"SATURN": 1.5, "MARS": 1.2},
    },
    "children": {
        "houses": {"5": 2.0, "1": 1.5, "9": 1.2, "4": 1.2},
        "planets": {"MOON": 1.5, "JUPITER": 1.2},
    },
    "health": {
        "houses": {"1": 2.0, "6": 2.0, "8": 1.5, "12": 1.5},
        "planets": {"MARS": 1.5, "SATURN": 1.2, "MOON": 1.2, "NEPTUNE": 1.1},
    },
}

# ── 核心议题生成规则（PRD v1.3 §10.3）────────────────────

CORE_THEME_RULES: dict[str, list[dict[str, Any]]] = {}

def _build_default_themes() -> dict[str, list[dict[str, Any]]]:
    return {
        "personal": [
            {"cond": "生命主线与事业高度绑定", "theme": "自我实现与事业成就互相绑定"},
            {"cond": "早期环境严肃", "theme": "在压力和责任中找到自己的节奏"},
            {"cond": "群星角宫>=3", "theme": "人生主轴清晰，多数事情主动找上你"},
            {"cond": "群星果宫>=3", "theme": "力量在学习适应中积累，后发制人"},
            {"cond": "吉星和谐", "theme": "关系和人脉是你最重要的杠杆"},
            {"default": "在稳定结构中逐步建立自己的主场"},
        ],
        "finance": [
            {"cond": "2R庙旺+角宫", "theme": "正财稳定，财富靠主业积累"},
            {"cond": "2R落陷+果宫", "theme": "正财需迂回策略，不适合单一收入来源"},
            {"cond": "8R>2R", "theme": "偏财嗅觉比正财强，关注投资和资源整合"},
            {"cond": "2R被土刑", "theme": "财富积累慢但稳，先苦后甜型"},
            {"cond": "2R被木拱", "theme": "资源自然增长，关键是别挥霍"},
            {"default": "财务以稳健为主，避免高风险押注"},
        ],
        "career": [
            {"cond": "10R庙旺+角宫", "theme": "事业是你的主场，社会认可来得自然"},
            {"cond": "10R落陷+被接纳", "theme": "事业需借力，关键是选对平台和引路人"},
            {"cond": "日角宫+10R光体相位", "theme": "天生容易被看见，适合台前"},
            {"cond": "10R果宫", "theme": "事业果实偏晚，但根基更稳，大器晚成型"},
            {"default": "事业靠积累而非爆发，把时间当朋友"},
        ],
        "romance": [
            {"cond": "金庙旺+5R强", "theme": "天生有吸引力，感情是你人生的大主题"},
            {"cond": "5R落陷+7R庙旺", "theme": "恋爱多波折，婚姻是你的稳定锚"},
            {"cond": "金土硬相位", "theme": "越成熟越懂爱，年轻时在感情里补课"},
            {"cond": "金火和谐", "theme": "吸引力自然流露，不需刻意经营"},
            {"default": "感情需先理解自己，再寻找共鸣"},
        ],
        "marriage": [
            {"cond": "7R庙旺+角宫", "theme": "伴侣是你的加分项，关系带来实质助力"},
            {"cond": "7R落陷+被刑", "theme": "关系是你的补课题，选对人比努力重要"},
            {"cond": "7R与1R互溶", "theme": "自我和关系绑在一起，独处时你不完整"},
            {"cond": "7R飞10宫", "theme": "伴侣直接影响你的事业高度和社会地位"},
            {"cond": "7R飞8宫", "theme": "关系涉及深层资源绑定和信任博弈"},
            {"default": "关系是你的一面镜子，帮你看见自己"},
        ],
        "work_skill": [
            {"cond": "6R庙旺+角宫", "theme": "日常执行力就是你的核心竞争力"},
            {"cond": "6R与水和谐", "theme": "学习能力强，技能迭代快"},
            {"cond": "6R飞3宫", "theme": "沟通传播是你的核心工作方式"},
            {"cond": "6R落陷+果宫", "theme": "不适合高强度执行岗，适合分析支持型"},
            {"cond": "6R被土拱", "theme": "适合需要耐心和结构的精进型工作"},
            {"default": "找到适合的节奏比追求效率更重要"},
        ],
        "education": [
            {"cond": "水庙旺+3R强", "theme": "天生学得快，早期学习经历给你打了很好的底"},
            {"cond": "木庙旺+9R强", "theme": "高阶学习是你的出路，知识能直接变现"},
            {"cond": "3-9和谐", "theme": "日常信息接收和高阶意义追寻两不误"},
            {"cond": "水落陷+被土刑", "theme": "学习速度不快，但学会的东西不会忘"},
            {"cond": "9R飞10宫", "theme": "学术或高阶资格直接关联社会地位"},
            {"default": "学习方式比学习内容更值得你先搞清楚"},
        ],
        "family": [
            {"cond": "日+4R庙旺", "theme": "父亲形象正、支持够"},
            {"cond": "月+10R庙旺", "theme": "母亲是你的情绪安全网和人生后盾"},
            {"cond": "日月被土刑冲", "theme": "早期家庭环境严肃压抑，需自己重建安全感"},
            {"cond": "4-10吉相位", "theme": "父母关系是你人格稳定的重要来源"},
            {"default": "家庭给了你底色，成年后的路需自己定义"},
        ],
        "appearance": [
            {"cond": "命主庙旺", "theme": "形体优势明显，气场足"},
            {"cond": "命主落陷", "theme": "形体某方面偏弱或与上升特征不一致"},
            {"default": "形体是上升和命主星的综合表达"},
        ],
        "health": [
            {"cond": "1R弱+6R弱", "theme": "先天体质需要后天多加注意"},
            {"cond": "6R庙旺+吉相位", "theme": "身体恢复力好，日常状态稳定"},
            {"cond": "8R被火土刑", "theme": "定期体检很重要，关注慢性和急性风险"},
            {"default": "健康管理需要从1宫和6宫的状态出发"},
        ],
        "partnership": [
            {"cond": "7R庙旺+和谐相位", "theme": "你适合与人合伙，合作能放大你的能力"},
            {"cond": "7R与10R和谐", "theme": "合伙关系是你事业上升的关键推手"},
            {"cond": "7R落陷+被刑", "theme": "选合伙人格外谨慎，选错人比做错事更致命"},
            {"default": "合伙是杠杆，但需要契约兜底和清晰的利益边界"},
        ],
        "children": [
            {"cond": "5R庙旺+月和谐", "theme": "和孩子的关系是你人生中最自然、最滋养的部分"},
            {"cond": "5R落陷+被刑", "theme": "亲子关系是你的课题——需要更多耐心和学习"},
            {"cond": "月庙旺+5R飞角宫", "theme": "你天生懂得给孩子安全感和方向感"},
            {"default": "孩子是你的一面镜子，照见你自己未被活出的部分"},
        ],
    }

CORE_THEME_RULES = _build_default_themes()


def resolve_core_theme(domain: str, context: dict[str, Any]) -> str:
    """根据上下文解析一句话核心议题"""
    rules = CORE_THEME_RULES.get(domain, [])
    for rule in rules:
        if "default" in rule:
            continue
        if _match_cond_registry(rule["cond"], context):
            return rule["theme"]
    for rule in rules:
        if "default" in rule:
            return rule["default"]
    return ""


def _match_cond_registry(cond_key: str, ctx: dict[str, Any]) -> bool:
    """简单条件匹配。实际使用由各领域传入预计算的条件bool。"""
    return ctx.get(cond_key, False)


# ── 数据类 ──────────────────────────────────────────────

@dataclass
class AngleEntry:
    angle_id: str
    angle_label: str
    narrative: str


@dataclass
class InterpretationMatrix:
    primary_angle: AngleEntry
    alternative_angles: list[AngleEntry] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "primary_angle": {
                "angle_id": self.primary_angle.angle_id,
                "angle_label": self.primary_angle.angle_label,
                "narrative": self.primary_angle.narrative,
            },
            "alternative_angles": [
                {
                    "angle_id": a.angle_id,
                    "angle_label": a.angle_label,
                    "narrative": a.narrative,
                }
                for a in self.alternative_angles
            ],
        }


@dataclass
class DomainReport:
    domain: str
    core_theme: str
    tradition_weight: float
    structure: str         # 结构结论 — 古占
    psychology: str         # 心理感受 — 现占
    suggestion: str         # 建议方向 — 融合
    interpretation_matrix: InterpretationMatrix

    def to_dict(self) -> dict[str, Any]:
        return {
            "domain": self.domain,
            "core_theme": self.core_theme,
            "tradition_weight": self.tradition_weight,
            "structure": self.structure,
            "psychology": self.psychology,
            "suggestion": self.suggestion,
            "interpretation_matrix": self.interpretation_matrix.to_dict(),
        }


# ── 基类 ─────────────────────────────────────────────────

class DomainAnalyzer(ABC):
    domain_key: str = ""
    tradition_weight: float = 0.5

    @property
    def bias(self) -> dict[str, Any]:
        return SITUATIONAL_BIASES.get(self.domain_key, {})

    def get_house_weight(self, house: int, ruler_house: int | None = None) -> float:
        hw = self.bias.get("houses", {})
        base = hw.get(str(house), 1.0)
        if ruler_house is not None:
            ruler_w = hw.get(str(ruler_house), 1.0)
            base = max(base, ruler_w)
        return base

    def get_planet_weight(self, planet_name: str, is_ruler_of_core_house: bool = False) -> float:
        pw = self.bias.get("planets", {})
        base = pw.get(planet_name.upper(), 1.0)
        if is_ruler_of_core_house:
            base = max(base, 1.5)
        if planet_name.upper() == "CHART_RULER":
            base = max(base, pw.get("CHART_RULER", 1.3))
        return base

    def analyze(self, chart: Any) -> DomainReport:
        traditional = self._analyze_traditional(chart)
        modern = self._analyze_modern(chart)
        return self._fuse(traditional, modern, chart)

    @abstractmethod
    def _analyze_traditional(self, chart: Any) -> dict[str, Any]:
        ...

    @abstractmethod
    def _analyze_modern(self, chart: Any) -> dict[str, Any]:
        ...

    def _fuse(self, traditional: dict[str, Any], modern: dict[str, Any], chart: Any) -> DomainReport:
        w = self.tradition_weight
        structure = traditional.get("structure", "")
        psychology = modern.get("psychology", "")
        suggestion = self._build_suggestion(traditional, modern)

        primary = AngleEntry(
            angle_id="main",
            angle_label="主取象",
            narrative=f"{structure}\n\n{psychology}\n\n{suggestion}",
        )
        alternatives = self._build_alt_angles(traditional, modern, chart)

        theme_ctx = traditional.get("theme_conditions", {})
        core_theme = resolve_core_theme(self.domain_key, theme_ctx)

        return DomainReport(
            domain=self.domain_key,
            core_theme=core_theme,
            tradition_weight=w,
            structure=structure,
            psychology=psychology,
            suggestion=suggestion,
            interpretation_matrix=InterpretationMatrix(
                primary_angle=primary,
                alternative_angles=alternatives,
            ),
        )

    def _build_suggestion(self, traditional: dict[str, Any], modern: dict[str, Any]) -> str:
        ts = traditional.get("suggestion", "")
        ms = modern.get("suggestion", "")
        if ts and ms:
            return f"{ts}\n\n从心态上来说：{ms}"
        return ts or ms or ""

    def _build_alt_angles(
        self, traditional: dict[str, Any], modern: dict[str, Any], chart: Any,
    ) -> list[AngleEntry]:
        return [
            a for a in [
                self._alt_work_angle(traditional),
                self._alt_reception_angle(traditional),
                self._alt_phase_angle(traditional),
            ] if a is not None
        ]

    def _alt_work_angle(self, trad: dict[str, Any]) -> AngleEntry | None:
        alt = trad.get("alt_work_perspective")
        if alt:
            return AngleEntry(angle_id="work_perspective", angle_label="切换到工作执行视角", narrative=alt)
        return None

    def _alt_reception_angle(self, trad: dict[str, Any]) -> AngleEntry | None:
        alt = trad.get("alt_reception_view")
        if alt:
            return AngleEntry(angle_id="reception_view", angle_label="从贵人助力角度看", narrative=alt)
        return None

    def _alt_phase_angle(self, trad: dict[str, Any]) -> AngleEntry | None:
        alt = trad.get("alt_phase_view")
        if alt:
            return AngleEntry(angle_id="phase_view", angle_label="从相位网络角度看", narrative=alt)
        return None
