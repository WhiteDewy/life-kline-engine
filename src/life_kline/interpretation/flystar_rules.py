"""
飞星规则（PRD v1.3 §8）

宫性优先、星性修饰。三层模板引擎：
- 行星飞行风格（PLANET_FLIGHT_STYLES）
- 目标宫位场景（TARGET_HOUSE_SCENES）
- 自动组合 planet_mod 生成器
+ 单步/两步飞星链路 + 互溶 + 12宫主星分组。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# ═══════════════════════════════════════════════════════════
# 12宫主优先级分组
# ═══════════════════════════════════════════════════════════

RULER_PRIORITY_GROUPS: dict[str, list[int]] = {
    "life_axis":      [1, 10],
    "core_resources": [7, 4, 2],
    "life_scenes":    [5, 11, 6, 8],
    "mind_dissolve":  [3, 9, 12],
}

RULER_GROUP_LABELS: dict[str, str] = {
    "life_axis": "人生主轴",
    "core_resources": "核心关系与资源",
    "life_scenes": "具体场景",
    "mind_dissolve": "心智与消融",
}


def get_ruler_priority_group(source_house: int) -> str:
    for group, houses in RULER_PRIORITY_GROUPS.items():
        if source_house in houses:
            return group
    return "mind_dissolve"


# ═══════════════════════════════════════════════════════════
# 三层模板：行星飞行风格 × 目标宫位场景 → planet_mod
# ═══════════════════════════════════════════════════════════

PLANET_FLIGHT_STYLES: dict[str, dict[str, str]] = {
    "SUN": {
        "verb": "照耀、主导、定义",
        "posture": "你带着一种天然的自我意识进入这个领域，"
                  "你不只是在做事——你是在这个领域里确认'我是谁'。",
        "tone_strong": "光芒被放大，你能成为这个领域的中心人物。",
        "tone_weak": "光芒受阻，你容易在这个领域里感到'被忽视'或'不被认可'，"
                     "需要先学会为自己发光。",
        "need": "你需要被看见。",
    },
    "MOON": {
        "verb": "感受、照料、承接",
        "posture": "你带着情绪雷达进入这个领域，"
                  "你能感受到别人忽略的冷暖变化。",
        "tone_strong": "安全感自然流淌，你能在这个领域里滋养自己和他人。",
        "tone_weak": "安全感不足，你容易在这个领域里过于敏感或过度依赖他人的反馈，"
                     "需要先建立自己的情绪容器。",
        "need": "你需要被记住、被温柔对待。",
    },
    "MERCURY": {
        "verb": "连接、传递、拆解",
        "posture": "你带着好奇心和信息处理能力进入这个领域，"
                  "你天然的倾向是'先搞清楚怎么回事'再行动。",
        "tone_strong": "信息流动顺畅，你是这个领域的枢纽和信息节点。",
        "tone_weak": "信息容易卡顿或失真，你需要在这个领域里学会区分'信号'和'噪音'。",
        "need": "你需要被理解、需要信息透明。",
    },
    "VENUS": {
        "verb": "吸引、调和、经营",
        "posture": "你带着审美感和价值判断进入这个领域，"
                  "你不会硬来——你更擅长让事情自然地变好。",
        "tone_strong": "关系顺滑、资源自然流动。你不费劲就能在这个领域里建立好感和价值。",
        "tone_weak": "关系或资源容易失衡——你可能过度付出或过度索取，"
                     "需要在这个领域里建立'给和拿'的边界。",
        "need": "你需要被欣赏、需要关系有质感。",
    },
    "MARS": {
        "verb": "推进、竞争、突破",
        "posture": "你带着行动力和竞争意识进入这个领域，"
                  "你不会等——你的第一反应是'去做点什么'。",
        "tone_strong": "行动力爆表，你能在这个领域里快速拿到结果，不拖泥带水。",
        "tone_weak": "行动容易踩错节奏——该出手时犹豫、该收手时冲动，"
                     "需要在这个领域里学会'先瞄准再开枪'。",
        "need": "你需要有目标、需要看到进展。",
    },
    "JUPITER": {
        "verb": "扩张、整合、信任",
        "posture": "你带着乐观和整合能力进入这个领域，"
                  "你能看到更大的图景，能把分散的资源和人串联起来。",
        "tone_strong": "机会和人脉自然涌入，这个领域是你的人生放大器。",
        "tone_weak": "容易承诺过量或过度乐观，需要在这个领域里保留'退出机制'。",
        "need": "你需要空间和信任、需要看到意义。",
    },
    "SATURN": {
        "verb": "结构、筛选、沉淀",
        "posture": "你带着审慎和长期主义进入这个领域，"
                  "你不会轻易出手——你在等对的时机和对的结构。",
        "tone_strong": "慢但是稳。一旦在这个领域建立起结构，就不容易被动摇。",
        "tone_weak": "容易过度谨慎或感到被压抑，需要在这个领域里区分'耐心'和'恐惧'。",
        "need": "你需要确定性和长期承诺。",
    },
}

TARGET_HOUSE_SCENES: dict[int, dict[str, str]] = {
    1:  {"scene": "自我表达和个人身份的确立",
         "question": "别人怎么看你？你怎么看自己？"},
    2:  {"scene": "资源积累和价值变现",
         "question": "你的钱从哪里来？什么东西值得你投入？"},
    3:  {"scene": "信息流通和日常连接",
         "question": "你怎么获取信息？你怎么把话说出去？"},
    4:  {"scene": "家庭根基和内心安全感",
         "question": "你的根在哪里？什么东西让你觉得'到家了'？"},
    5:  {"scene": "创造力释放和个人舞台",
         "question": "你怎么发光？什么东西让你觉得活着有劲？"},
    6:  {"scene": "日常执行和健康管理",
         "question": "你每天在做什么？你的身体和习惯在帮你还是拖你？"},
    7:  {"scene": "一对一关系和契约合作",
         "question": "你选择和什么样的人站在一起？你怎么处理'我们'？"},
    8:  {"scene": "深层转化和共享资源",
         "question": "你如何处理风险和信任？什么东西让你愿意押注？"},
    9:  {"scene": "高阶学习和意义追寻",
         "question": "你相信什么？你要去的远方在哪里？"},
    10: {"scene": "社会角色和公开成就",
         "question": "你被社会记住的方式是什么？你的位置在哪里？"},
    11: {"scene": "群体归属和长期愿景",
         "question": "你和什么样的一群人在一起？你们要一起做成什么？"},
    12: {"scene": "幕后运作和内在消融",
         "question": "什么东西你自己都不一定看得清、却在暗中影响你的选择？"},
}


def generate_planet_mod(
    planet_name: str,
    target_house: int,
    dignified: bool = False,
    debilitated: bool = False,
) -> str:
    """组合行星飞行风格 × 目标宫位场景，生成 planet_mod 文本。"""
    style = PLANET_FLIGHT_STYLES.get(planet_name, PLANET_FLIGHT_STYLES["MERCURY"])
    scene = TARGET_HOUSE_SCENES.get(target_house, TARGET_HOUSE_SCENES[1])

    posture = style["posture"].format(scene=scene["scene"])
    tone = (
        style["tone_strong"] if dignified
        else style["tone_weak"] if debilitated
        else f"在这个领域里，你的{style['verb']}方式是中性的——取决于你如何借力和调整节奏。"
    )
    need = style["need"]

    return (
        f"{posture}\n\n"
        f"具体来说：{tone}\n\n"
        f"核心需求：{need} {scene['question']}"
    )


# ═══════════════════════════════════════════════════════════
# 飞星模板
# ═══════════════════════════════════════════════════════════

FLIGHT_TEMPLATE = (
    "{source_label}（{source_house}宫议题）通过{planet_style}带到{target_label}（{target_house}宫领域）——"
    "你通过{target_domain}来处理{source_domain}，方式是{style_modifier}。"
)

MUTUAL_RECEPTION_TEMPLATE = (
    "{source_label}在{target_house}宫，{target_label}在{source_house}宫——"
    "这两个宫位形成闭环，议题互相绑定，拆不开。"
    "{source_domain}和{target_domain}在你的生命中不可分割。"
)


# ═══════════════════════════════════════════════════════════
# 数据类
# ═══════════════════════════════════════════════════════════

@dataclass
class FlystarStep:
    source_house: int
    target_house: int
    ruler_planet_name: str
    ruler_planet_style: str
    source_domain: str
    target_domain: str

    def render(self) -> str:
        return FLIGHT_TEMPLATE.format(
            source_label=f"{self.ruler_planet_name}（{self.source_house}R）",
            source_house=self.source_house,
            planet_style=self.ruler_planet_style,
            target_label=f"第{self.target_house}宫",
            target_house=self.target_house,
            target_domain=self.target_domain,
            style_modifier=self.ruler_planet_style,
        )


@dataclass
class FlystarChain:
    steps: list[FlystarStep] = field(default_factory=list)

    def render_two_step(self) -> str:
        if len(self.steps) < 2:
            return self.steps[0].render() if self.steps else ""
        s1, s2 = self.steps[0], self.steps[1]
        return (
            f"你的{s1.source_domain}（{s1.source_house}宫）"
            f"先通过{s1.ruler_planet_name}的表达进入{s1.target_domain}（{s1.target_house}宫），"
            f"再以{s2.ruler_planet_name}的方式最终影响{s2.target_domain}（{s2.target_house}宫）。"
            f"这意味着{s1.source_domain}的真正落点不在{s1.target_domain}，而在{s2.target_domain}。"
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "chain": [
                {
                    "from_house": s.source_house,
                    "to_house": s.target_house,
                    "ruler": s.ruler_planet_name,
                    "style": s.ruler_planet_style,
                }
                for s in self.steps
            ],
            "narrative": self.render_two_step(),
        }
