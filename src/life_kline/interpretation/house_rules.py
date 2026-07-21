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
        "domain_key": "personal",
        "keywords": ["自我定位", "身体状态", "个人意志", "人格面具", "出场方式"],
        "adult": "个人姿态、身体存在感、出面方式",
        "power": "决定你是以什么样的姿态让他人记住你",
        "ruler_meaning": "命主星的状态决定了'你是谁'这个问题的答案——"
                       "不是你想成为谁，是你自然呈现出来的是谁。"
                       "命主星的落宫是你人生的主舞台，落座是你的行为风格。",
        "planet_in_meaning": "宫内星是你天生带出来的特质——这些特质不用学，"
                            "它们就是你的一部分。宫内星告诉你：你用什么方式进场、"
                            "你的第一反应是什么、别人看到你的第一印象。",
    },
    2: {
        "title": "收入与资源",
        "domain_key": "finance",
        "keywords": ["现金流", "价值感", "可支配资源", "自我定价", "正财"],
        "adult": "现金流、资源控制、利益分配、可变现能力",
        "power": "决定你如何把资源、欲望和实际收益绑定成钱",
        "ruler_meaning": "2宫主星的落宫告诉你钱从哪个领域来——"
                       "飞10宫靠事业赚钱，飞7宫靠合作分钱，飞5宫靠创作变现。"
                       "看2宫主星在哪里，就知道你的收入管道在哪里。",
        "planet_in_meaning": "宫内星是你的财务管理风格——"
                            "你花钱是大方还是谨慎、存钱是习惯还是困难、"
                            "对'值不值得'的判断标准是什么。",
    },
    3: {
        "title": "学习与表达",
        "domain_key": "education",
        "keywords": ["沟通", "技能", "短途连接", "信息摄取", "思维方式"],
        "adult": "信息网络、线报、传播、谈判、地面关系、组织口径",
        "power": "决定你如何通过消息、人脉、名单和传播形成影响力",
        "ruler_meaning": "3宫主星的落宫告诉你信息和表达能力在哪个领域变现——"
                       "飞9宫知识变学问，飞10宫表达变事业，飞1宫口才变人格魅力。",
        "planet_in_meaning": "宫内星是你的思维方式——你是理性分析还是直觉跳跃，"
                            "说还是写，学得快还是慢，喜欢广度还是深度。",
    },
    4: {
        "title": "家庭与根基",
        "domain_key": "family",
        "keywords": ["原生家庭", "居所", "情绪根基", "安全感来源", "父亲（古占）"],
        "adult": "家族根基、地盘、安全盘、退路",
        "power": "决定你是否有足够稳的根基去承受外部扩张",
        "ruler_meaning": "4宫主星的落宫告诉你安全感的真正来源——"
                       "飞10宫安全感靠事业成就，飞7宫靠伴侣关系，飞4宫落自己宫位则根基自足。",
        "planet_in_meaning": "宫内星是原生家庭给你的底色——那些你小时候经历的东西"
                            "形成的深层模式。你的情绪反应、你对'家'的定义、你的退路。",
    },
    5: {
        "title": "创造与恋爱",
        "domain_key": "romance",
        "keywords": ["创作", "恋爱", "个人表达", "子女", "快乐方式"],
        "adult": "创作表达、名色、娱乐场、个人招牌",
        "power": "决定你如何把个人魅力与舞台感变成影响力",
        "ruler_meaning": "5宫主星的落宫告诉你创造力和桃花从哪个领域来——"
                       "飞1宫个人魅力是来源，飞3宫靠表达吸引，飞10宫创作变事业。",
        "planet_in_meaning": "宫内星是你表达快乐的方式——你谈恋爱是什么风格，"
                            "释放创造力时像什么，玩起来是什么样子。",
    },
    6: {
        "title": "工作与健康",
        "domain_key": "work_skill",
        "keywords": ["执行", "习惯", "健康管理", "日常工作", "下属同事"],
        "adult": "执行系统、差事、日常工序、用人管理",
        "power": "决定你能否把复杂事务做成持续运转的流程",
        "ruler_meaning": "6宫主星的落宫告诉你日常工作的最终产出方向——"
                       "飞10宫日常工作积累成事业，飞2宫日常工作直接变现，"
                       "飞6宫落自己宫位则专精一门手艺。",
        "planet_in_meaning": "宫内星是你的工作方式和身体节奏——"
                            "你是按计划执行还是随机应变，效率高还是稳扎稳打，"
                            "身体哪里容易出问题。",
    },
    7: {
        "title": "伴侣与合作",
        "domain_key": "marriage",
        "keywords": ["伴侣", "合作", "契约关系", "公开敌人", "一对一"],
        "adult": "联盟、客户、对手、契约、师徒、保护关系",
        "power": "决定你如何通过他人进入更大的系统并借力扩张",
        "ruler_meaning": "7宫主星的落宫告诉你伴侣/合伙人的特质来源和关系最终走向——"
                       "飞1宫伴侣像你，飞9宫伴侣来自远方，飞10宫关系推动事业。"
                       "7宫主星的尊贵状态决定了关系的质量和难易度。",
        "planet_in_meaning": "宫内星是你和他人一对一互动时的本能模式——"
                            "你在关系里是主动还是被动、付出还是索取、"
                            "冲突时是正面解决还是回避。",
    },
    8: {
        "title": "风险与转化",
        "domain_key": "finance",
        "keywords": ["风险", "偏财", "深层转变", "生死", "共享资源"],
        "adult": "风险共担、利益绑定、债务与筹码",
        "power": "决定你如何处理权力背后的代价、筹码和深度绑定",
        "ruler_meaning": "8宫主星的落宫告诉你偏财和深度转化的来源——"
                       "飞5宫偏财来自投机创作，飞2宫偏财直接转化成正财，"
                       "飞8宫落自己宫位则天生懂钱生钱。8宫主星的相位决定了你在权力和信任上的课题。",
        "planet_in_meaning": "宫内星是你面对危机和深层转变的方式——"
                            "你怕什么、怎样处理信任和权力、在不得不放手的时候是什么姿态。",
    },
    9: {
        "title": "远方与意义",
        "domain_key": "education",
        "keywords": ["高阶学习", "远行", "世界观", "哲学法律", "出版传播"],
        "adult": "理念、旗号、远方资源、合法性",
        "power": "决定你如何给自己的路径找到更大的叙事和正当性",
        "ruler_meaning": "9宫主星的落宫告诉你高阶知识和信念在哪个领域落地——"
                       "飞3宫知识变传播，飞10宫学历变地位，飞1宫信念变人格底色。",
        "planet_in_meaning": "宫内星是你探索世界和意义的方式——"
                            "你是通过旅行还是读书、是理性求知还是信念驱动、"
                            "对'远方'的向往是什么形态。",
    },
    10: {
        "title": "事业与名望",
        "domain_key": "career",
        "keywords": ["事业地位", "公众形象", "成就", "社会角色", "母亲（古占）"],
        "adult": "公开地位、制度名望、社会抬头",
        "power": "决定你如何被公众看见，以及以什么身份被承认",
        "ruler_meaning": "10宫主星的落宫告诉你事业成就的来源和路径——"
                       "飞6宫靠日常专业积累，飞1宫靠个人品牌，飞2宫事业直接和收入挂钩。"
                       "10宫主星的尊贵状态决定了事业是坦途还是需要迂回。",
        "planet_in_meaning": "宫内星是你追求社会认可的方式——"
                            "你对成功的定义是什么、在权威面前是什么态度、"
                            "你被公众看见的'人设'是什么样的。",
    },
    11: {
        "title": "社群与愿景",
        "domain_key": "partnership",
        "keywords": ["人脉", "社群", "长期愿景", "贵人", "群体理想"],
        "adult": "人脉团体、门生网络、长期势力",
        "power": "决定你能否把个人关系做成成规模的势力网络",
        "ruler_meaning": "11宫主星的落宫告诉你人脉和愿景从哪个领域汇聚——"
                       "飞7宫伙伴的伙伴成为你的圈子，飞9宫同好同学圈层，"
                       "飞10宫圈子就是你的社会资本。",
        "planet_in_meaning": "宫内星是你和群体互动的方式——"
                            "进圈子是自然融入还是需要被邀请、你在群体中扮演什么角色、"
                            "你的'长期愿望'是务实还是理想主义。",
    },
    12: {
        "title": "潜意识与退隐",
        "domain_key": "health",
        "keywords": ["潜意识", "退隐", "灵性", "隐秘之敌", "自我消融"],
        "adult": "幕后运作、监禁清算、隐形敌人、收尾代价",
        "power": "决定你如何处理台面下的力量，以及后期如何被回收",
        "ruler_meaning": "12宫主星的落宫告诉你什么东西需要'放手'——"
                       "飞6宫日常习惯是你的修行方式，飞4宫内在安全感是你的终极课题，"
                       "飞12宫落自己宫位则需要大量独处和自我消化。",
        "planet_in_meaning": "宫内星是你潜意识深处的驱动力——"
                            "那些你自己都不太明白为什么要做的事，"
                            "那些你以为忘了但一直在影响你的东西。需要注意：无星体落入12宫不代表没有潜意识课题。",
    },
}

# 宫位 → 领域映射（引擎占星师路由用）
HOUSE_TO_DOMAIN: dict[int, str] = {
    1: "personal", 2: "finance", 3: "education", 4: "family",
    5: "romance", 6: "work_skill", 7: "marriage", 8: "finance",
    9: "education", 10: "career", 11: "partnership", 12: "health",
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
    domain_key: str
    ruler_meaning: str
    planet_in_meaning: str
    pair_house: int
    pair_label: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "house": self.house,
            "title": self.title,
            "keywords": self.keywords,
            "adult_meaning": self.adult_meaning,
            "power_dynamic": self.power_dynamic,
            "domain_key": self.domain_key,
            "ruler_meaning": self.ruler_meaning,
            "planet_in_meaning": self.planet_in_meaning,
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
        domain_key=str(data.get("domain_key", "")),
        ruler_meaning=str(data.get("ruler_meaning", "")),
        planet_in_meaning=str(data.get("planet_in_meaning", "")),
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
