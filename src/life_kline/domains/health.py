"""
健康体质 — tradition_weight: 0.7。对话体。
"""
from __future__ import annotations
from typing import Any
from .base import DomainAnalyzer
from .helpers import plabel, slabel, asc_sign, chart_ruler_name, planet_dignity_code, house_ruler_name, planet_sign


class HealthAnalyzer(DomainAnalyzer):
    domain_key = "health"
    tradition_weight = 0.7

    def _analyze_traditional(self, chart: Any) -> dict[str, Any]:
        asc = asc_sign(chart)
        asc_l = slabel(asc)
        cr_name = chart_ruler_name(chart)
        cr_l = plabel(cr_name)
        cr_dig = planet_dignity_code(chart, cr_name)
        r6 = house_ruler_name(chart, 6)
        r6l = plabel(r6)
        r6s = planet_sign(chart, r6)
        r6d = planet_dignity_code(chart, r6)
        r8 = house_ruler_name(chart, 8)
        r8l = plabel(r8)
        r12 = house_ruler_name(chart, 12)
        r12l = plabel(r12)

        structure = f"你的先天体质——看上升{asc_l}和命主星{cr_l}。"
        if cr_dig in ("domicile", "exaltation"):
            structure += "你的底子不错——身体的自我修复能力比较强。生个小病恢复得快，不太容易有长期性的健康问题。"
        elif cr_dig in ("detriment", "fall"):
            structure += "先天体质不是最强的那一档——不是说身体不好，是说你比别人更需要主动管理自己的身体。早睡、规律饮食对你来说是刚需，不是养生建议。"
        else:
            structure += "体质中等——不在极端的好或坏。取决于你后天怎么对待它。"

        structure += f"\n\n日常健康——看6宫主星{r6l}在{slabel(r6s)}。"
        if r6d in ("domicile", "exaltation"):
            structure += "日常健康管理比较顺——你适合规律的作息和稳定的生活习惯。身体不大会出意料之外的毛病。"
        elif r6d in ("detriment", "fall"):
            structure += "健康是你需要主动关注的领域——容易因为工作压力、不规律的生活或者长期的忽略而消耗。你可能不是那种'身体自动会好'的人——你需要定期检查、主动保养。"
        else:
            structure += "日常健康中等——你善待它它就善待你，你忽略它它就会提醒你。"

        structure += (
            f"\n\n值得注意的系统：8宫{r8l}指向慢性或突发性的健康风险，12宫{r12l}指向精神状态和隐性消耗。"
            f"这两块是你在高压时期最容易出问题的地方——不一定是生病，也可能是疲惫、失眠、焦虑。"
        )

        suggestion = "以上为占星学参考，不替代医疗诊断。任何持续的身体不适，请先看医生。占星能帮你的是'知道自己的体质倾向'——知道之后，生活方式的选择才是关键。"
        return {"structure": structure, "suggestion": suggestion, "theme_conditions": {}}

    def _analyze_modern(self, chart: Any) -> dict[str, Any]:
        psychology = "身体和你的情绪是连在一起的。12宫的隐性压力、月亮被压抑的情绪——这些不会只在心里待着，它们会在身体上找到出口。身体的紧绷，可能是你一直没说出来的一些'不'。"
        return {"psychology": psychology, "suggestion": ""}
