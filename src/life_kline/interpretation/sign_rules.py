"""
星座规则（PRD v1.3 §6）

星座作为行星的"过滤器"——修饰行星的表达风格。
提供元素、形态、极性、persona、社交面具等完整模型。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..constants import Sign, get_sign_element, get_sign_modality


SIGN_RULES: dict[str, dict[str, Any]] = {
    "ARIES": {
        "element": "火",
        "modality": "基本",
        "polarity": "阳",
        "persona": "主动、直接、敢先开路",
        "work_style": "更适合高节奏、要抢先手、能快速拍板的环境",
        "social_mask": "别人最先看到你的冲劲和果敢，像一团往前烧的火",
        "comfort_zone": "在竞争中感到安全，在停滞中感到不安",
        "stress_response": "遇到阻力时的第一反应是正面推进，撞了墙再想别的办法",
        "planet_filter": "{星}在这里被加速——行动快、决断快，但也容易三分钟热度",
    },
    "TAURUS": {
        "element": "土",
        "modality": "固定",
        "polarity": "阴",
        "persona": "稳、耐久、重价值和体感",
        "work_style": "更适合需要长期积累、审美判断和资源沉淀的环境",
        "social_mask": "别人最先看到你的沉稳和可靠，像大地一样让人踏实",
        "comfort_zone": "在稳定和舒适中感到安全，在被催促时感到不适",
        "stress_response": "遇到阻力时先停下来评估，一旦决定就不轻易改变",
        "planet_filter": "{星}在这里被稳住——不急不躁，重结果，但有时太固执",
    },
    "GEMINI": {
        "element": "风",
        "modality": "变动",
        "polarity": "阳",
        "persona": "灵活、好奇、反应快、会连接信息",
        "work_style": "更适合多线程沟通、交易、传播和中间枢纽型工作",
        "social_mask": "别人最先看到你的机智和健谈，像一阵抓不住的风",
        "comfort_zone": "在信息流动和新鲜感中感到安全，在重复中感到窒息",
        "stress_response": "遇到阻力时换个角度绕过去，正面硬撞不是你的风格",
        "planet_filter": "{星}在这里被激活——表达灵活、适应快，但深度可能不够",
    },
    "CANCER": {
        "element": "水",
        "modality": "基本",
        "polarity": "阴",
        "persona": "敏感、照料型、会先感受环境",
        "work_style": "更适合需要照护、承接和建立安全感的环境",
        "social_mask": "别人最先看到你的温柔和体贴，像一池温热的池塘",
        "comfort_zone": "在被需要和被记住时感到安全，在冷漠的环境中退缩",
        "stress_response": "遇到阻力时先缩回壳里保护自己，再决定怎么应对",
        "planet_filter": "{星}在这里被包裹——情绪驱动、记忆力强，但边界感较弱",
    },
    "LEO": {
        "element": "火",
        "modality": "固定",
        "polarity": "阳",
        "persona": "有舞台感、想被看见、愿意发光",
        "work_style": "更适合需要个人风格、表达魅力和带队气场的环境",
        "social_mask": "别人最先看到你的光芒和自信，像一团不灭的火焰",
        "comfort_zone": "在被认可和尊重时感到安全，在被忽视时感到受伤",
        "stress_response": "遇到阻力时不能接受被看低，会加倍努力证明自己",
        "planet_filter": "{星}在这里被放大——表现力强、有创造力，但容易要面子",
    },
    "VIRGO": {
        "element": "土",
        "modality": "变动",
        "polarity": "阴",
        "persona": "细、准、讲流程、重实用性",
        "work_style": "更适合需要打磨标准、拆解问题和优化效率的环境",
        "social_mask": "别人最先看到你的精准和务实，像一把精密的尺子",
        "comfort_zone": "在事情被梳理清楚时感到安全，在混乱中感到焦虑",
        "stress_response": "遇到阻力时会再分析一遍，看看是不是自己漏了什么",
        "planet_filter": "{星}在这里被精炼——分析力强、细节控，但也容易过度自我批评",
    },
    "LIBRA": {
        "element": "风",
        "modality": "基本",
        "polarity": "阳",
        "persona": "会权衡、讲体面、重关系平衡",
        "work_style": "更适合协商、审美、对外形象和关系撮合型工作",
        "social_mask": "别人最先看到你的优雅和公正，像一面平滑的天平",
        "comfort_zone": "在关系和谐和公平中感到安全，在冲突中感到消耗",
        "stress_response": "遇到阻力时先考虑各方感受，试图找到一个平衡点",
        "planet_filter": "{星}在这里被调和——关系意识强、审美好，但决策可能犹豫",
    },
    "SCORPIO": {
        "element": "水",
        "modality": "固定",
        "polarity": "阴",
        "persona": "深、狠、能扛压力、会看暗线",
        "work_style": "更适合高保密、高风险、深调查和强掌控的环境",
        "social_mask": "别人最先感受到你的深度和力量，像一道看不清底的深湖",
        "comfort_zone": "在掌控局面时感到安全，在被看透时感到脆弱",
        "stress_response": "遇到阻力不会公开对抗，而是积蓄力量等待关键一击",
        "planet_filter": "{星}在这里被加深——洞察力强、不轻易相信，但可能过度控制",
    },
    "SAGITTARIUS": {
        "element": "火",
        "modality": "变动",
        "polarity": "阳",
        "persona": "外扩、讲信念、追求更大空间",
        "work_style": "更适合要讲愿景、带方向、连远方资源的环境",
        "social_mask": "别人最先看到你的乐观和远见，像一支射向远方的箭",
        "comfort_zone": "在有新的可能性和空间时感到安全，在被束缚时感到窒息",
        "stress_response": "遇到阻力时换个方向继续跑，不让你做的事就找别的事做",
        "planet_filter": "{星}在这里被开放——视野宽、乐观，但可能承诺过量",
    },
    "CAPRICORN": {
        "element": "土",
        "modality": "基本",
        "polarity": "阴",
        "persona": "稳重、现实、能忍耐、讲结果",
        "work_style": "更适合制度化、长期建设、层级分明的环境",
        "social_mask": "别人最先看到你的沉稳和能力，像一座不会倒的山",
        "comfort_zone": "在事情被按计划推进时感到安全，在失控时感到压力",
        "stress_response": "遇到阻力时默默忍耐并加倍努力，时间是你的盟友",
        "planet_filter": "{星}在这里被纪律化——有耐心、善规划，但也容易压抑",
    },
    "AQUARIUS": {
        "element": "风",
        "modality": "固定",
        "polarity": "阳",
        "persona": "理性、独立、反常规、重系统",
        "work_style": "更适合创新、改革、平台化和群体连接型工作",
        "social_mask": "别人最先看到你的独立和前瞻，像一股不按常规吹的风",
        "comfort_zone": "在思想自由和独立时感到安全，在被要求从众时感到抗拒",
        "stress_response": "遇到阻力时从更高的视角审视问题，不被情绪裹挟",
        "planet_filter": "{星}在这里被疏离——思辨能力强、创新，但情感连接可能偏冷",
    },
    "PISCES": {
        "element": "水",
        "modality": "变动",
        "polarity": "阴",
        "persona": "感受力强、会融合、边界感松",
        "work_style": "更适合灵感型、疗愈型、艺术型或幕后支持型工作",
        "social_mask": "别人最先感受到你的柔软和善意，像一片看不见边的大海",
        "comfort_zone": "在被理解和被包容时感到安全，在被尖锐评判时感到受伤",
        "stress_response": "遇到阻力时倾向于回避或内化，需要独处消化",
        "planet_filter": "{星}在这里被消融——共情力强、灵感多，但边界感容易模糊",
    },
}


@dataclass
class SignProfile:
    sign: Sign
    element: str
    modality: str
    polarity: str
    persona: str
    work_style: str
    social_mask: str
    comfort_zone: str
    stress_response: str
    planet_filter: str

    def to_dict(self) -> dict[str, str]:
        return {
            "sign": self.sign.value,
            "element": self.element,
            "modality": self.modality,
            "polarity": self.polarity,
            "persona": self.persona,
            "work_style": self.work_style,
            "social_mask": self.social_mask,
            "comfort_zone": self.comfort_zone,
            "stress_response": self.stress_response,
            "planet_filter": self.planet_filter,
        }


def get_sign_profile(sign: Sign) -> SignProfile:
    rules = SIGN_RULES.get(sign.value, {})
    return SignProfile(
        sign=sign,
        element=rules.get("element", ""),
        modality=rules.get("modality", ""),
        polarity=rules.get("polarity", ""),
        persona=rules.get("persona", ""),
        work_style=rules.get("work_style", ""),
        social_mask=rules.get("social_mask", ""),
        comfort_zone=rules.get("comfort_zone", ""),
        stress_response=rules.get("stress_response", ""),
        planet_filter=rules.get("planet_filter", ""),
    )


def apply_planet_filter(sign: Sign, planet_description: str) -> str:
    """用星座的 filter 模板修饰行星描述"""
    rules = SIGN_RULES.get(sign.value, {})
    template = rules.get("planet_filter", "{星}")
    return template.replace("{星}", planet_description)
