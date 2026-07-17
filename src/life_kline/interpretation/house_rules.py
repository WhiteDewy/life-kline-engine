"""
宫位规则（PRD v1.3 §7）

宫位三层义：基础义 + 成人社会义 + 权力义
+ 对宫关系 + 三方宫位组 + 角/续/果分类
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


HOUSE_DATA: dict[int, dict[str, Any]] = {
    1: {
        "title": "自我与身体",
        "keywords": ["自我定位", "身体状态", "个人意志"],
        "adult": "个人姿态、身体存在感、出面方式",
        "power": "决定你是以什么样的姿态让他人记住你",
    },
    2: {
        "title": "收入与资源",
        "keywords": ["现金流", "价值感", "可支配资源"],
        "adult": "现金流、资源控制、利益分配、可变现能力",
        "power": "决定你如何把资源、欲望和实际收益绑定成钱",
    },
    3: {
        "title": "学习与表达",
        "keywords": ["沟通", "技能", "短途连接"],
        "adult": "信息网络、线报、传播、谈判、地面关系、组织口径",
        "power": "决定你如何通过消息、人脉、名单和传播形成影响力",
    },
    4: {
        "title": "家庭与根基",
        "keywords": ["原生家庭", "居所", "情绪根基"],
        "adult": "家族根基、地盘、安全盘、退路",
        "power": "决定你是否有足够稳的根基去承受外部扩张",
    },
    5: {
        "title": "创造与恋爱",
        "keywords": ["创作", "恋爱", "个人表达"],
        "adult": "创作表达、名色、娱乐场、个人招牌",
        "power": "决定你如何把个人魅力与舞台感变成影响力",
    },
    6: {
        "title": "工作与健康",
        "keywords": ["执行", "习惯", "健康管理"],
        "adult": "执行系统、差事、日常工序、用人管理",
        "power": "决定你能否把复杂事务做成持续运转的流程",
    },
    7: {
        "title": "伴侣与合作",
        "keywords": ["伴侣", "合作", "契约关系"],
        "adult": "联盟、客户、对手、契约、师徒、保护关系",
        "power": "决定你如何通过他人进入更大的系统并借力扩张",
    },
    8: {
        "title": "风险与转化",
        "keywords": ["风险", "共享资源", "深层转变"],
        "adult": "风险共担、利益绑定、债务与筹码",
        "power": "决定你如何处理权力背后的代价、筹码和深度绑定",
    },
    9: {
        "title": "远方与意义",
        "keywords": ["高阶学习", "远行", "世界观"],
        "adult": "理念、旗号、远方资源、合法性",
        "power": "决定你如何给自己的路径找到更大的叙事和正当性",
    },
    10: {
        "title": "事业与名望",
        "keywords": ["事业地位", "公众形象", "成就"],
        "adult": "公开地位、制度名望、社会抬头",
        "power": "决定你如何被公众看见，以及以什么身份被承认",
    },
    11: {
        "title": "社群与愿景",
        "keywords": ["人脉", "社群", "长期愿景"],
        "adult": "人脉团体、门生网络、长期势力",
        "power": "决定你能否把个人关系做成成规模的势力网络",
    },
    12: {
        "title": "潜意识与退隐",
        "keywords": ["隐性压力", "疗愈", "收尾"],
        "adult": "幕后运作、监禁清算、隐形敌人、收尾代价",
        "power": "决定你如何处理台面下的力量，以及后期如何被回收",
    },
}

HOUSE_PAIRS: dict[int, int] = {1: 7, 2: 8, 3: 9, 4: 10, 5: 11, 6: 12,
                                7: 1, 8: 2, 9: 3, 10: 4, 11: 5, 12: 6}

HOUSE_PAIR_LABELS: dict[tuple[int, int], str] = {
    (1, 7): "自我 vs 他人",
    (2, 8): "我的资源 vs 共享资源",
    (3, 9): "日常信息 vs 高阶真理",
    (4, 10): "私人根基 vs 公开地位",
    (5, 11): "个人创造 vs 群体愿景",
    (6, 12): "日常执行 vs 幕后消融",
}

HOUSE_TRIADS: dict[str, list[int]] = {
    "career_line": [2, 6, 10],        # 事业线：资源→执行→地位
    "karma_line": [4, 8, 12],         # 业力线：根基→转化→消融
    "growth_line": [1, 5, 9],         # 成长线：自我→创造→信念
    "relationship_line": [3, 7, 11],  # 关系线：信息→合作→社群
}

HOUSE_TRIAD_LABELS: dict[str, str] = {
    "career_line": "资源→执行→地位（事业线）",
    "karma_line": "根基→转化→消融（业力线）",
    "growth_line": "自我→创造→信念（成长线）",
    "relationship_line": "信息→合作→社群（关系线）",
}


@dataclass
class HouseProfile:
    house: int
    title: str
    keywords: list[str]
    adult_meaning: str
    power_dynamic: str
    pair_house: int
    pair_label: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "house": self.house,
            "title": self.title,
            "keywords": self.keywords,
            "adult_meaning": self.adult_meaning,
            "power_dynamic": self.power_dynamic,
            "pair_house": self.pair_house,
            "pair_label": self.pair_label,
        }


def get_house_profile(house: int) -> HouseProfile:
    data = HOUSE_DATA.get(house, HOUSE_DATA.get(1, {}))
    pair = HOUSE_PAIRS.get(house, 1)
    pair_key = (min(house, pair), max(house, pair))
    pair_label = HOUSE_PAIR_LABELS.get(pair_key, "")
    return HouseProfile(
        house=house,
        title=str(data.get("title", "")),
        keywords=list(data.get("keywords", [])),
        adult_meaning=str(data.get("adult", "")),
        power_dynamic=str(data.get("power", "")),
        pair_house=pair,
        pair_label=pair_label,
    )


def get_triad_for_house(house: int) -> str | None:
    for triad_key, houses in HOUSE_TRIADS.items():
        if house in houses:
            return triad_key
    return None


def get_triad_label(triad_key: str) -> str:
    return HOUSE_TRIAD_LABELS.get(triad_key, triad_key)
