"""
theme_catalog.py — AKG 主题注册表（Astrology Knowledge Graph · Theme Layer）

Theme 是「用户语言」与「占星知识」之间的桥梁。
每个 Theme 连接一组行星 / 宫位 / 相位对 / 用户语言关键词，
Evidence Collector 据此从星盘事实中抽取证据，形成带置信度的结论。

key 对齐 consultation.py 的 theme_reflections 映射（authority/intimacy/money/
self_worth/safety），使既有 seam 零改动点亮；career/communication/growth 无
reflection 条目时优雅降级（reflection map 未命中即跳过）。
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ThemeDef:
    """主题定义——占星知识与用户语言之间的桥梁。"""

    key: str                                  # "authority"
    label: str                                # "权威与认可"
    description: str                          # 一句话说明
    planets: list[str] = field(default_factory=list)        # 关联行星 key
    houses: list[int] = field(default_factory=list)         # 关联宫位
    aspect_pairs: list[tuple[str, str]] = field(default_factory=list)  # 关键相位对
    keywords: list[str] = field(default_factory=list)       # 用户语言触发词


# ============================================================================
# 8 个核心主题
# ============================================================================

THEME_CATALOG: dict[str, ThemeDef] = {
    "authority": ThemeDef(
        key="authority",
        label="权威与认可",
        description="来自父亲、长辈、上级等权威人物的期待，以及你如何被认可。",
        planets=["SUN", "SATURN"],
        houses=[10, 1],
        aspect_pairs=[("SUN", "SATURN")],
        keywords=["领导", "权威", "父亲", "上级", "认可", "升职", "老板", "上司",
                  "管我", "压制", "权威人物"],
    ),
    "intimacy": ThemeDef(
        key="intimacy",
        label="亲密关系",
        description="恋爱、吸引、亲密与独立之间的拉扯。",
        planets=["VENUS", "MOON", "MARS"],
        houses=[7, 5],
        aspect_pairs=[("VENUS", "MARS"), ("VENUS", "MOON")],
        keywords=["恋爱", "亲密", "感情", "前任", "吸引", "伴侣", "喜欢的人",
                  "表白", "分手", "暧昧", "关系"],
    ),
    "money": ThemeDef(
        key="money",
        label="金钱与资源",
        description="赚钱能力、财务安全感、对物质的态度。",
        planets=["JUPITER", "VENUS"],
        houses=[2, 8],
        aspect_pairs=[("JUPITER", "VENUS")],
        keywords=["钱", "财务", "收入", "赚钱", "存款", "物质", "穷", "富裕",
                  "理财", "消费"],
    ),
    "self_worth": ThemeDef(
        key="self_worth",
        label="自我价值",
        description="「我够不够好」的自我评估与自我表达。",
        planets=["SUN"],
        houses=[1, 2],
        aspect_pairs=[("SUN", "SATURN")],
        keywords=["价值", "不够好", "自信", "配不上", "表现自己", "自卑", "存在感",
                  "被看见", "认可自己"],
    ),
    "safety": ThemeDef(
        key="safety",
        label="安全感",
        description="情感安全、归属、稳定与不安的底色。",
        planets=["MOON"],
        houses=[4],
        aspect_pairs=[("MOON", "SATURN")],
        keywords=["安全", "稳定", "害怕", "不安", "踏实", "归属", "焦虑", "失控",
                  "不确定", "家"],
    ),
    "career": ThemeDef(
        key="career",
        label="事业方向",
        description="事业定位、职业转型、长期发展路径。",
        planets=["SATURN", "JUPITER", "MERCURY"],
        houses=[10, 6],
        aspect_pairs=[("SATURN", "JUPITER")],
        keywords=["工作", "事业", "职业", "方向", "转型", "辞职", "跳槽", "发展",
                  "前途", "适合做什么"],
    ),
    "communication": ThemeDef(
        key="communication",
        label="表达与沟通",
        description="如何表达自己、与他人交换信息、说服与被理解。",
        planets=["MERCURY"],
        houses=[3],
        aspect_pairs=[("MERCURY", "SATURN")],
        keywords=["表达", "沟通", "说话", "写作", "说服", "吵架", "说不出口",
                  "被误解", "表达自己"],
    ),
    "growth": ThemeDef(
        key="growth",
        label="成长与信念",
        description="人生意义、信念系统、学习与远方。",
        planets=["JUPITER"],
        houses=[9],
        aspect_pairs=[("JUPITER", "SATURN")],
        keywords=["意义", "信念", "学习", "成长", "哲学", "远方", "信仰", "迷茫",
                  "人生方向"],
    ),
}


def get_theme(key: str) -> ThemeDef | None:
    return THEME_CATALOG.get(key)


def all_themes() -> list[ThemeDef]:
    return list(THEME_CATALOG.values())
