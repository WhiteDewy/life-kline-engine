"""
chart_structure.py — 全盘结构分析器 (ChartStructureAnalyzer)

对整张星盘进行跨领域的结构分析，输出：
- 元素/模式权重分布
- 半球分布
- 定位链终点
- 相位格局（T三角/大十字/大三角/风筝/Yod）
- 互溶接纳网络
- 角宫/续宫/果宫分布
- 昼夜派系
- 南北交点轴线
- 发光体状态
- 命主星状态

供 ConsultationEngine（星语者）在四步对话中注入全盘上下文。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .constants import (
    Planet, Sign,
    ANGULAR_HOUSES, SUCCEDENT_HOUSES, CADENT_HOUSES,
    SIGN_ELEMENT, SIGN_MODALITY, DOMICILE_SIGNS,
)
from .domains.helpers import (
    plabel, slabel, dlabel, house_title,
    planet_sign, planet_house, planet_dignity_code,
    chart_ruler_name, house_ruler_name,
    SIGN_RULER_MAP,
)


# ── 元素 / 模式映射 ───────────────────────────────────────

ELEMENT_LABELS: dict[str, str] = {
    "fire": "火", "earth": "土", "air": "风", "water": "水",
}

MODALITY_LABELS: dict[str, str] = {
    "cardinal": "基本", "fixed": "固定", "mutable": "变动",
}

ELEMENT_ORDER = ["fire", "earth", "air", "water"]
MODALITY_ORDER = ["cardinal", "fixed", "mutable"]


# ── 数据类 ─────────────────────────────────────────────────

@dataclass
class ChartStructureReport:
    """全盘结构分析报告"""
    # 元素分布
    element_balance: dict[str, int] = field(default_factory=dict)
    dominant_element: str = ""
    lacking_element: str = ""
    element_narrative: str = ""

    # 模式分布
    modality_balance: dict[str, int] = field(default_factory=dict)
    dominant_modality: str = ""
    modality_narrative: str = ""

    # 半球
    hemisphere_horizontal: str = ""   # 上半球(7-12) / 下半球(1-6)
    hemisphere_vertical: str = ""     # 左半球(4-9) / 右半球(10-3)
    hemisphere_narrative: str = ""

    # 角宫分布
    angularity: dict[str, int] = field(default_factory=dict)
    angularity_narrative: str = ""

    # 定位链
    final_dispositor: str = ""
    dispositor_chain_summary: str = ""

    # 相位格局
    aspect_patterns: list[str] = field(default_factory=list)
    aspect_pattern_narrative: str = ""

    # 互溶接纳
    mutual_receptions: list[str] = field(default_factory=list)

    # 昼夜派
    sect: str = ""                     # "day" | "night"
    sect_narrative: str = ""

    # 发光体
    sun_summary: str = ""
    moon_summary: str = ""
    luminaries_narrative: str = ""

    # 命主星
    chart_ruler_summary: str = ""
    chart_ruler_narrative: str = ""

    # 南北交
    nodes_axis: str = ""
    nodes_narrative: str = ""

    # 合成
    full_summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "element_balance": self.element_balance,
            "dominant_element": self.dominant_element,
            "lacking_element": self.lacking_element,
            "element_narrative": self.element_narrative,
            "modality_balance": self.modality_balance,
            "dominant_modality": self.dominant_modality,
            "modality_narrative": self.modality_narrative,
            "hemisphere_horizontal": self.hemisphere_horizontal,
            "hemisphere_vertical": self.hemisphere_vertical,
            "hemisphere_narrative": self.hemisphere_narrative,
            "angularity": self.angularity,
            "angularity_narrative": self.angularity_narrative,
            "final_dispositor": self.final_dispositor,
            "dispositor_chain_summary": self.dispositor_chain_summary,
            "aspect_patterns": self.aspect_patterns,
            "aspect_pattern_narrative": self.aspect_pattern_narrative,
            "mutual_receptions": self.mutual_receptions,
            "sect": self.sect,
            "sect_narrative": self.sect_narrative,
            "sun_summary": self.sun_summary,
            "moon_summary": self.moon_summary,
            "luminaries_narrative": self.luminaries_narrative,
            "chart_ruler_summary": self.chart_ruler_summary,
            "chart_ruler_narrative": self.chart_ruler_narrative,
            "nodes_axis": self.nodes_axis,
            "nodes_narrative": self.nodes_narrative,
            "full_summary": self.full_summary,
        }


# ── 分析器 ─────────────────────────────────────────────────

class ChartStructureAnalyzer:
    """从星盘报告数据中提取全盘结构"""

    def __init__(self, report_data: dict[str, Any]):
        self._data = report_data
        self._natal = report_data.get("natal_chart", {})
        self._patterns = report_data.get("advanced_patterns", {})
        self._user_info = report_data.get("user_info", {})
        self._planet_chars = report_data.get("planet_characters", {}).get("planet_characters", {})
        self._domains = report_data.get("domains", {})

    # ── 公共入口 ──

    def analyze(self) -> ChartStructureReport:
        report = ChartStructureReport()

        report.element_balance = self._compute_element_balance()
        report.dominant_element, report.lacking_element = self._summarize_elements(report.element_balance)
        report.element_narrative = self._build_element_narrative(report)

        report.modality_balance = self._compute_modality_balance()
        report.dominant_modality = self._summarize_modality(report.modality_balance)
        report.modality_narrative = self._build_modality_narrative(report)

        hh, hv = self._compute_hemispheres()
        report.hemisphere_horizontal = hh
        report.hemisphere_vertical = hv
        report.hemisphere_narrative = self._build_hemisphere_narrative(report)

        report.angularity = self._compute_angularity()
        report.angularity_narrative = self._build_angularity_narrative(report)

        report.final_dispositor = self._compute_final_dispositor()
        report.dispositor_chain_summary = self._build_dispositor_narrative(report)

        report.aspect_patterns = self._detect_aspect_patterns()
        report.aspect_pattern_narrative = self._build_pattern_narrative(report)

        report.mutual_receptions = self._detect_mutual_receptions()

        report.sect = "day" if self._user_info.get("is_day_chart", True) else "night"
        report.sect_narrative = self._build_sect_narrative(report)

        report.sun_summary = self._summarize_sun()
        report.moon_summary = self._summarize_moon()
        report.luminaries_narrative = self._build_luminaries_narrative(report)

        cr = self._summarize_chart_ruler()
        report.chart_ruler_summary = cr["summary"]
        report.chart_ruler_narrative = cr["narrative"]

        report.nodes_axis = self._detect_nodes_axis()
        report.nodes_narrative = self._build_nodes_narrative(report)

        report.full_summary = self._build_full_summary(report)

        return report

    # ── 元素权重 ──

    def _compute_element_balance(self) -> dict[str, int]:
        balance: dict[str, int] = {"fire": 0, "earth": 0, "air": 0, "water": 0}
        traditional = {"SUN", "MOON", "MERCURY", "VENUS", "MARS", "JUPITER", "SATURN"}

        for planet_key, profile in self._planet_chars.items():
            if planet_key not in traditional:
                continue
            sign = profile.get("sign", "")
            element = SIGN_ELEMENT.get(sign, "")
            if element in balance:
                weight = 2 if planet_key in ("SUN", "MOON") else 1
                balance[element] += weight

        # ASC 额外权重
        asc_sign = self._natal.get("ascendant", {}).get("sign", "")
        asc_elem = SIGN_ELEMENT.get(asc_sign, "")
        if asc_elem in balance:
            balance[asc_elem] += 1

        return balance

    def _summarize_elements(self, balance: dict[str, int]) -> tuple[str, str]:
        if not balance:
            return "未知", "无"
        sorted_el = sorted(balance.items(), key=lambda x: -x[1])
        dominant = sorted_el[0][0]
        lacking = sorted_el[-1][0]
        return dominant, lacking

    def _build_element_narrative(self, report: ChartStructureReport) -> str:
        parts = []
        dom = report.dominant_element
        lack = report.lacking_element
        if dom:
            parts.append(f"元素以{ELEMENT_LABELS.get(dom, dom)}象为主导。")
        if lack and lack != dom:
            parts.append(f"{ELEMENT_LABELS.get(lack, lack)}象是稀缺资源，相关领域的体验需要更多意识参与。")

        dom_count = report.element_balance.get(dom, 0)
        if dom_count >= 6:
            parts.append("该元素过度集中，可能形成单一视角的盲区。")

        return "".join(parts) if parts else "元素分布均衡，四象各有表达。"

    # ── 模式权重 ──

    def _compute_modality_balance(self) -> dict[str, int]:
        balance: dict[str, int] = {"cardinal": 0, "fixed": 0, "mutable": 0}
        traditional = {"SUN", "MOON", "MERCURY", "VENUS", "MARS", "JUPITER", "SATURN"}

        for planet_key, profile in self._planet_chars.items():
            if planet_key not in traditional:
                continue
            sign = profile.get("sign", "")
            mod = SIGN_MODALITY.get(sign, "")
            if mod in balance:
                weight = 2 if planet_key in ("SUN", "MOON") else 1
                balance[mod] += weight

        return balance

    def _summarize_modality(self, balance: dict[str, int]) -> str:
        if not balance:
            return "未知"
        return max(balance, key=lambda k: balance[k])

    def _build_modality_narrative(self, report: ChartStructureReport) -> str:
        dom = report.dominant_modality
        label = MODALITY_LABELS.get(dom, dom)
        if dom == "cardinal":
            return f"基本宫（{label}）主导——主动开创是你的惯性模式。"
        elif dom == "fixed":
            return f"固定宫（{label}）主导——稳定持久是你的核心力量。"
        elif dom == "mutable":
            return f"变动宫（{label}）主导——灵活适应是你的生存策略。"
        return "模式分布均衡，三种节奏都能调动。"

    # ── 半球分布 ──

    def _compute_hemispheres(self) -> tuple[str, str]:
        upper = 0
        lower = 0
        left = 0
        right = 0

        for planet_key, profile in self._planet_chars.items():
            house = profile.get("house", 0)
            if 7 <= house <= 12:
                upper += 1
            elif 1 <= house <= 6:
                lower += 1
            if 4 <= house <= 9:
                left += 1
            elif house in (1, 2, 3, 10, 11, 12):
                right += 1

        h_label = "上半球重（外向，社会导向）" if upper > lower else "下半球重（内向，个人导向）"
        v_label = "左半球重（主动，自我驱动）" if left > right else "右半球重（回应，他人驱动）"
        return h_label, v_label

    def _build_hemisphere_narrative(self, report: ChartStructureReport) -> str:
        return f"{report.hemisphere_horizontal}；{report.hemisphere_vertical}。"

    # ── 角宫分布 ──

    def _compute_angularity(self) -> dict[str, int]:
        dist: dict[str, int] = {"angular": 0, "succedent": 0, "cadent": 0}
        for planet_key, profile in self._planet_chars.items():
            house = profile.get("house", 0)
            if house in ANGULAR_HOUSES:
                dist["angular"] += 1
            elif house in SUCCEDENT_HOUSES:
                dist["succedent"] += 1
            elif house in CADENT_HOUSES:
                dist["cadent"] += 1
        return dist

    def _build_angularity_narrative(self, report: ChartStructureReport) -> str:
        a = report.angularity.get("angular", 0)
        s = report.angularity.get("succedent", 0)
        c = report.angularity.get("cadent", 0)
        if a >= 3:
            return f"群星角宫（{a}颗）——人生主轴清晰，多数事情主动找上你。"
        elif c >= 3:
            return f"群星果宫（{c}颗）——力量在学习适应中积累，后发制人。"
        return f"角宫{a}·续宫{s}·果宫{c}，分布相对均衡。"

    # ── 定位链 ──

    def _compute_final_dispositor(self) -> str:
        """走定位链找到最终定位星"""
        ruler_map: dict[str, str] = {}
        traditional = ["SUN", "MOON", "MERCURY", "VENUS", "MARS", "JUPITER", "SATURN"]

        for planet_key in traditional:
            profile = self._planet_chars.get(planet_key, {})
            sign = profile.get("sign", "")
            ruler = SIGN_RULER_MAP.get(sign, "")
            if ruler:
                ruler_map[planet_key] = ruler

        # 找闭环或终点
        visited: set[str] = set()
        for start in traditional:
            current = start
            path: list[str] = []
            for _ in range(12):  # 最多12步防死循环
                if current not in ruler_map:
                    return current
                nxt = ruler_map[current]
                if nxt == current:
                    return current          # 入庙，自己定位自己
                if (current, nxt) in {(p, ruler_map.get(p, "")) for p in path}:
                    # 闭环 — 返回环中权重最大的
                    cycle_planets = {current, nxt}
                    for a, b in path:
                        if a == nxt or b == current:
                            cycle_planets.add(a)
                            cycle_planets.add(b)
                    return self._pick_strongest_in_cycle(cycle_planets)
                path.append((current, nxt))
                current = nxt
            return current

        return "SUN"  # 回退：太阳

    def _pick_strongest_in_cycle(self, planets: set[str]) -> str:
        best = ""
        best_score = -999
        for p in planets:
            profile = self._planet_chars.get(p, {})
            score = profile.get("core_strength", 0)
            if score > best_score:
                best_score = score
                best = p
        return best or next(iter(planets), "SUN")

    def _build_dispositor_narrative(self, report: ChartStructureReport) -> str:
        fd = report.final_dispositor
        fd_label = plabel(fd)
        return f"全盘能量最终流向{fd_label}——{fd_label}是你的星盘引擎，它决定了各领域的能量出口方式。"

    # ── 相位格局 ──

    def _detect_aspect_patterns(self) -> list[str]:
        patterns: list[str] = []
        pattern_data = self._patterns.get("pattern_readings", [])
        if pattern_data:
            for p in pattern_data:
                if isinstance(p, str):
                    patterns.append(p)
                elif isinstance(p, dict):
                    patterns.append(p.get("description", str(p)))
        return patterns or []

    def _build_pattern_narrative(self, report: ChartStructureReport) -> str:
        patterns = report.aspect_patterns
        if not patterns:
            return "无明显特殊相位格局。"
        return "；".join(patterns[:3]) if patterns else ""

    # ── 互溶接纳 ──

    def _detect_mutual_receptions(self) -> list[str]:
        receptions: list[str] = []
        mr_data = self._patterns.get("mutual_receptions", [])
        for mr in mr_data:
            if isinstance(mr, str):
                receptions.append(mr)
            elif isinstance(mr, dict):
                receptions.append(mr.get("description", str(mr)))
        return receptions

    # ── 昼夜派 ──

    def _build_sect_narrative(self, report: ChartStructureReport) -> str:
        if report.sect == "day":
            return "日生盘——太阳主导，木星为主要吉星，外向型表达更自然。"
        return "夜生盘——月亮主导，金星为主要吉星，内敛型感知更敏锐。"

    # ── 发光体 ──

    def _summarize_sun(self) -> str:
        sun = self._planet_chars.get("SUN", {})
        sign = sun.get("sign", "未知")
        house = sun.get("house", 0)
        dignity = sun.get("dignity_code", "peregrine")
        return f"太阳{slabel(sign)}{house}宫（{dlabel(dignity)}）"

    def _summarize_moon(self) -> str:
        moon = self._planet_chars.get("MOON", {})
        sign = moon.get("sign", "未知")
        house = moon.get("house", 0)
        dignity = moon.get("dignity_code", "peregrine")
        return f"月亮{slabel(sign)}{house}宫（{dlabel(dignity)}）"

    def _build_luminaries_narrative(self, report: ChartStructureReport) -> str:
        sun = self._planet_chars.get("SUN", {})
        moon = self._planet_chars.get("MOON", {})
        sun_sign = sun.get("sign", "")
        moon_sign = moon.get("sign", "")

        parts = [f"你的意志力核心是{slabel(sun_sign)}，情绪安全感来自{slabel(moon_sign)}。"]

        # 日月相位关系
        sun_elem = SIGN_ELEMENT.get(sun_sign, "")
        moon_elem = SIGN_ELEMENT.get(moon_sign, "")
        if sun_elem == moon_elem:
            parts.append("日月同元素——意志和情绪内在一致，做事内外统一。")
        elif (sun_elem, moon_elem) in {("fire", "air"), ("air", "fire"), ("earth", "water"), ("water", "earth")}:
            parts.append("日月元素互补——意图和感受互相滋养。")
        else:
            parts.append("日月元素不同质——理性和感性有时各说各话，需要刻意整合。")

        return "".join(parts)

    # ── 命主星 ──

    def _summarize_chart_ruler(self) -> dict[str, str]:
        cr_name = chart_ruler_name_via_data(self._natal, self._planet_chars)
        cr_profile = self._planet_chars.get(cr_name, {})
        sign = cr_profile.get("sign", "未知")
        house = cr_profile.get("house", 0)
        dignity = cr_profile.get("dignity_code", "peregrine")
        strength = cr_profile.get("core_strength", 50)

        summary = f"命主星{plabel(cr_name)}落{slabel(sign)}{house}宫（{dlabel(dignity)}），强度{strength}%"

        narrative = (
            f"你的命主星是{plabel(cr_name)}——它是你星盘的'我'的代表。"
            f"落在{slabel(sign)}意味着你的行动风格带有{slabel(sign)}的特质，"
        )
        if dignity == "domicile":
            narrative += "入庙状态让它天然有力，自我表达不费力。"
        elif dignity == "exaltation":
            narrative += "擢升状态让它高调发光，容易在人群中站出位置。"
        elif dignity in ("detriment", "fall"):
            narrative += "处于失势/落陷，意味着你需要用更多的后天策略来补先天短板。但这不代表你弱——只是你的力量需要迂回释放。"
        else:
            narrative += "平常状态——不突出但也不拖累，关键在于你如何使用它。"
        narrative += f"落在第{house}宫，{house_title(house)}是你最重要的'人生舞台'。"

        return {"summary": summary, "narrative": narrative}

    # ── 南北交点 ──

    def _detect_nodes_axis(self) -> str:
        sn_sign = ""
        nn_sign = ""
        for planet_key, profile in self._planet_chars.items():
            if planet_key == "SOUTH_NODE":
                sn_sign = profile.get("sign", "")
                sn_house = profile.get("house", 0)
            if planet_key == "NORTH_NODE":
                nn_sign = profile.get("sign", "")
                nn_house = profile.get("house", 0)

        sn_sign = sn_sign or self._get_node_sign("SOUTH_NODE")
        sn_house = self._get_node_house("SOUTH_NODE")
        nn_sign = nn_sign or self._get_node_sign("NORTH_NODE")
        nn_house = self._get_node_house("NORTH_NODE")

        if sn_sign and nn_sign:
            return f"南交{slabel(sn_sign)}{sn_house}宫 → 北交{slabel(nn_sign)}{nn_house}宫"
        return "南北交点数据暂缺"

    def _get_node_sign(self, node_name: str) -> str:
        nodes_data = self._patterns.get("nodes", {})
        node = nodes_data.get(node_name, {})
        return node.get("sign", "")

    def _get_node_house(self, node_name: str) -> int:
        nodes_data = self._patterns.get("nodes", {})
        node = nodes_data.get(node_name, {})
        return node.get("house", 0)

    def _build_nodes_narrative(self, report: ChartStructureReport) -> str:
        if "→" not in report.nodes_axis:
            return ""
        parts = report.nodes_axis.split(" → ")
        sn = parts[0].replace("南交", "") if len(parts) > 0 else ""
        nn = parts[1].replace("北交", "") if len(parts) > 1 else ""
        return f"你的灵魂进化方向是从南交（{sn}的舒适区）走向北交（{nn}的成长区）。南交是你天生的'老本'，北交是你这一生要学的'新课'。"

    # ── 全盘合成 ──

    def _build_full_summary(self, report: ChartStructureReport) -> str:
        parts: list[str] = []

        if report.element_narrative:
            parts.append(report.element_narrative)
        if report.modality_narrative:
            parts.append(report.modality_narrative)
        if report.angularity_narrative:
            parts.append(report.angularity_narrative)
        if report.dispositor_chain_summary:
            parts.append(report.dispositor_chain_summary)
        if report.luminaries_narrative:
            parts.append(report.luminaries_narrative)
        if report.sect_narrative:
            parts.append(report.sect_narrative)
        if report.aspect_pattern_narrative:
            parts.append(f"格局：{report.aspect_pattern_narrative}")
        if report.nodes_narrative:
            parts.append(report.nodes_narrative)

        return " ".join(parts)


# ── 辅助 ──

def chart_ruler_name_via_data(natal: dict, planet_chars: dict) -> str:
    """从报告数据中提取命主星名"""
    # 优先从 natal_chart 取
    cr = natal.get("chart_ruler", "")
    if cr:
        return cr

    # 从 ASC 反推
    asc_sign = natal.get("ascendant", {}).get("sign", "")
    return SIGN_RULER_MAP.get(asc_sign, "SUN")
