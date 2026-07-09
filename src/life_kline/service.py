"""
High-level report service for the Life K-Line product.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from itertools import combinations
from statistics import mean
from typing import Any, Dict, Iterable, Optional

try:
    import swisseph as swe
except ImportError:
    swe = None

from .constants import (
    ANGULAR_HOUSES,
    ASPECT_CONFIG,
    CADENT_HOUSES,
    DOMICILE_SIGNS,
    deg_diff,
    DETRIMENT_SIGNS,
    EXALTATION_SIGNS,
    FALL_SIGNS,
    JOY_HOUSES,
    SUCCEDENT_HOUSES,
    AspectType,
    Planet,
    Sign,
)
from .ephemeris import EphemerisEngine
from .flystar_catalog import get_house_ruler_flight_entry
from .firdaria import FirdariaPeriod, calculate_firdaria_periods


PLANET_LABELS: Dict[Planet, str] = {
    Planet.SUN: "太阳",
    Planet.MOON: "月亮",
    Planet.MERCURY: "水星",
    Planet.VENUS: "金星",
    Planet.MARS: "火星",
    Planet.JUPITER: "木星",
    Planet.SATURN: "土星",
    Planet.URANUS: "天王星",
    Planet.NEPTUNE: "海王星",
    Planet.PLUTO: "冥王星",
    Planet.NORTH_NODE: "北交点",
    Planet.SOUTH_NODE: "南交点",
}

AUXILIARY_BODY_LABELS: Dict[str, str] = {
    "CHIRON": "凯龙星",
    "JUNO": "婚神星",
    "CERES": "谷神星",
    "PALLAS": "智神星",
    "VESTA": "灶神星",
    "NORTH_NODE": "北交点",
    "SOUTH_NODE": "南交点",
}

SIGN_LABELS: Dict[Sign, str] = {
    Sign.ARIES: "白羊座",
    Sign.TAURUS: "金牛座",
    Sign.GEMINI: "双子座",
    Sign.CANCER: "巨蟹座",
    Sign.LEO: "狮子座",
    Sign.VIRGO: "处女座",
    Sign.LIBRA: "天秤座",
    Sign.SCORPIO: "天蝎座",
    Sign.SAGITTARIUS: "射手座",
    Sign.CAPRICORN: "摩羯座",
    Sign.AQUARIUS: "水瓶座",
    Sign.PISCES: "双鱼座",
}

SIGN_ELEMENT_LABELS: Dict[Sign, str] = {
    Sign.ARIES: "火",
    Sign.LEO: "火",
    Sign.SAGITTARIUS: "火",
    Sign.TAURUS: "土",
    Sign.VIRGO: "土",
    Sign.CAPRICORN: "土",
    Sign.GEMINI: "风",
    Sign.LIBRA: "风",
    Sign.AQUARIUS: "风",
    Sign.CANCER: "水",
    Sign.SCORPIO: "水",
    Sign.PISCES: "水",
}

SIGN_MODALITY_LABELS: Dict[Sign, str] = {
    Sign.ARIES: "本位",
    Sign.CANCER: "本位",
    Sign.LIBRA: "本位",
    Sign.CAPRICORN: "本位",
    Sign.TAURUS: "固定",
    Sign.LEO: "固定",
    Sign.SCORPIO: "固定",
    Sign.AQUARIUS: "固定",
    Sign.GEMINI: "变动",
    Sign.VIRGO: "变动",
    Sign.SAGITTARIUS: "变动",
    Sign.PISCES: "变动",
}

SIGN_RULERS: Dict[Sign, Planet] = {
    Sign.ARIES: Planet.MARS,
    Sign.TAURUS: Planet.VENUS,
    Sign.GEMINI: Planet.MERCURY,
    Sign.CANCER: Planet.MOON,
    Sign.LEO: Planet.SUN,
    Sign.VIRGO: Planet.MERCURY,
    Sign.LIBRA: Planet.VENUS,
    Sign.SCORPIO: Planet.MARS,
    Sign.SAGITTARIUS: Planet.JUPITER,
    Sign.CAPRICORN: Planet.SATURN,
    Sign.AQUARIUS: Planet.SATURN,
    Sign.PISCES: Planet.JUPITER,
}

DIGNITY_LABELS = {
    "domicile": "入庙",
    "exaltation": "旺相",
    "detriment": "失势",
    "fall": "落陷",
    "peregrine": "平常",
}

PLANET_ARCHETYPES: Dict[Planet, Dict[str, str]] = {
    Planet.SUN: {
        "gift": "自我定义与主导能力",
        "shadow": "过度自尊或只按意志推进",
        "strategy": "把注意力放在长期目标、名望与作品沉淀上。",
    },
    Planet.MOON: {
        "gift": "情绪感知、照料与安全需求的把握",
        "shadow": "情绪卷入、节奏被环境牵动",
        "strategy": "先稳定作息与关系边界，再谈效率和决策。",
    },
    Planet.MERCURY: {
        "gift": "信息整合、表达、交易与学习能力",
        "shadow": "犹疑、分心、过度比较",
        "strategy": "把复杂问题拆成流程，建立可复用的认知框架。",
    },
    Planet.VENUS: {
        "gift": "关系经营、审美、合作与资源协调",
        "shadow": "讨好、依赖外部认可、享乐分散",
        "strategy": "通过关系与价值交换打开局面，但不要牺牲底线。",
    },
    Planet.MARS: {
        "gift": "行动力、竞争性、突破与执行",
        "shadow": "急躁、对抗、提前消耗",
        "strategy": "把火力聚焦在关键战役，而不是到处起冲突。",
    },
    Planet.JUPITER: {
        "gift": "扩张、信念、机会识别与贵人运",
        "shadow": "过度乐观、承诺过量、理想化",
        "strategy": "扩张时保留边界与节奏，把好运落到制度上。",
    },
    Planet.SATURN: {
        "gift": "结构、耐力、长期主义与责任",
        "shadow": "压抑、迟滞、过度保守",
        "strategy": "用时间换确定性，先筑底盘再谈跃迁。",
    },
    Planet.NORTH_NODE: {
        "gift": "增长方向、未来牵引",
        "shadow": "急于跳向新阶段而失去根基",
        "strategy": "把陌生感当作成长入口，但别抛弃原有能力。",
    },
    Planet.SOUTH_NODE: {
        "gift": "熟练、旧天赋、天然顺手的惯性",
        "shadow": "停在舒适区、消耗旧模式",
        "strategy": "保留经验，但要主动更新做事逻辑。",
    },
}

HOUSE_TOPICS: Dict[int, Dict[str, Any]] = {
    1: {"title": "自我与身体", "keywords": ["自我定位", "身体状态", "个人意志"]},
    2: {"title": "收入与资源", "keywords": ["现金流", "价值感", "可支配资源"]},
    3: {"title": "学习与表达", "keywords": ["沟通", "技能", "短途连接"]},
    4: {"title": "家庭与根基", "keywords": ["原生家庭", "居所", "情绪根基"]},
    5: {"title": "创造与恋爱", "keywords": ["创作", "恋爱", "个人表达"]},
    6: {"title": "工作与健康", "keywords": ["执行", "习惯", "健康管理"]},
    7: {"title": "伴侣与合作", "keywords": ["伴侣", "合作", "契约关系"]},
    8: {"title": "风险与转化", "keywords": ["风险", "共享资源", "深层转变"]},
    9: {"title": "远方与意义", "keywords": ["高阶学习", "远行", "世界观"]},
    10: {"title": "事业与名望", "keywords": ["事业地位", "公众形象", "成就"]},
    11: {"title": "社群与愿景", "keywords": ["人脉", "社群", "长期愿景"]},
    12: {"title": "潜意识与退隐", "keywords": ["隐性压力", "疗愈", "收尾"]},
}

HOUSE_ADULT_MEANINGS: Dict[int, Dict[str, str]] = {
    1: {
        "adult": "个人姿态、身体存在感、出面方式",
        "power": "决定你是以什么样的姿态让他人记住你。",
    },
    2: {
        "adult": "现金流、资源控制、利益分配、可变现能力",
        "power": "决定你如何把资源、欲望和实际收益绑定成钱。",
    },
    3: {
        "adult": "信息网络、线报、传播、谈判、地面关系、组织口径",
        "power": "决定你如何通过消息、人脉、名单和传播形成影响力。",
    },
    4: {
        "adult": "家族根基、地盘、安全盘、退路",
        "power": "决定你是否有足够稳的根基去承受外部扩张。",
    },
    5: {
        "adult": "创作表达、名色、娱乐场、个人招牌",
        "power": "决定你如何把个人魅力与舞台感变成影响力。",
    },
    6: {
        "adult": "执行系统、差事、日常工序、用人管理",
        "power": "决定你能否把复杂事务做成持续运转的流程。",
    },
    7: {
        "adult": "联盟、客户、对手、契约、师徒、保护关系",
        "power": "决定你如何通过他人进入更大的系统并借力扩张。",
    },
    8: {
        "adult": "风险共担、利益绑定、债务与筹码",
        "power": "决定你如何处理权力背后的代价、筹码和深度绑定。",
    },
    9: {
        "adult": "理念、旗号、远方资源、合法性",
        "power": "决定你如何给自己的路径找到更大的叙事和正当性。",
    },
    10: {
        "adult": "公开地位、制度名望、社会抬头",
        "power": "决定你如何被公众看见，以及以什么身份被承认。",
    },
    11: {
        "adult": "人脉团体、门生网络、长期势力",
        "power": "决定你能否把个人关系做成成规模的势力网络。",
    },
    12: {
        "adult": "幕后运作、监禁清算、隐形敌人、收尾代价",
        "power": "决定你如何处理台面下的力量，以及后期如何被回收。",
    },
}

SIGN_ARCHETYPES: Dict[Sign, Dict[str, Any]] = {
    Sign.ARIES: {
        "persona": "主动、直接、敢先开路",
        "work_style": "更适合高节奏、要抢先手、能快速拍板的环境",
        "career_tags": ["创业开拓", "销售攻坚", "项目突击", "运动竞技", "应急响应", "前线执行", "安保执法", "业务破局"],
    },
    Sign.TAURUS: {
        "persona": "稳、耐久、重价值和体感",
        "work_style": "更适合需要长期积累、审美判断和资源沉淀的环境",
        "career_tags": ["金融理财", "餐饮美食", "美业零售", "地产家居", "供应链", "资产经营", "珠宝奢品", "农业园艺"],
    },
    Sign.GEMINI: {
        "persona": "灵活、好奇、反应快、会连接信息",
        "work_style": "更适合多线程沟通、交易、传播和中间枢纽型工作",
        "career_tags": ["媒体内容", "教育培训", "商务交易", "运营策划", "咨询顾问", "交通物流", "主持口才", "翻译口译"],
    },
    Sign.CANCER: {
        "persona": "敏感、照料型、会先感受环境",
        "work_style": "更适合需要照护、承接和建立安全感的环境",
        "career_tags": ["心理咨询", "母婴教育", "护理医疗", "餐饮服务", "社区运营", "家居照护", "家庭教育", "非营利服务"],
    },
    Sign.LEO: {
        "persona": "有舞台感、想被看见、愿意发光",
        "work_style": "更适合需要个人风格、表达魅力和带队气场的环境",
        "career_tags": ["品牌公关", "管理带队", "表演娱乐", "内容主理", "青少教育", "IP打造", "舞台主持", "创始人角色"],
    },
    Sign.VIRGO: {
        "persona": "细、准、讲流程、重实用性",
        "work_style": "更适合需要打磨标准、拆解问题和优化效率的环境",
        "career_tags": ["数据分析", "编辑校对", "医药健康", "质控审计", "流程运营", "研究支持", "检测修复", "咨询实施"],
    },
    Sign.LIBRA: {
        "persona": "会权衡、讲体面、重关系平衡",
        "work_style": "更适合协商、审美、对外形象和关系撮合型工作",
        "career_tags": ["法律咨询", "公关传播", "品牌设计", "人力资源", "客户管理", "艺术商业", "婚恋咨询", "法务协调"],
    },
    Sign.SCORPIO: {
        "persona": "深、狠、能扛压力、会看暗线",
        "work_style": "更适合高保密、高风险、深调查和强掌控的环境",
        "career_tags": ["金融投资", "风险控制", "心理研究", "法务调查", "医疗外科", "危机管理", "情报分析", "战略博弈"],
    },
    Sign.SAGITTARIUS: {
        "persona": "外扩、讲信念、追求更大空间",
        "work_style": "更适合要讲愿景、带方向、连远方资源的环境",
        "career_tags": ["教育培训", "法律出版", "国际业务", "旅行文旅", "咨询顾问", "思想传播", "高校科研", "跨境传播"],
    },
    Sign.CAPRICORN: {
        "persona": "稳重、现实、能忍耐、讲结果",
        "work_style": "更适合制度化、长期建设、层级分明的环境",
        "career_tags": ["政府机构", "工程建设", "企业管理", "审计财会", "地产基建", "组织治理", "制度建设", "项目交付"],
    },
    Sign.AQUARIUS: {
        "persona": "理性、独立、反常规、重系统",
        "work_style": "更适合创新、改革、平台化和群体连接型工作",
        "career_tags": ["互联网科技", "产品策略", "社群平台", "社会创新", "科研工程", "组织变革", "数据产品", "社区创新"],
    },
    Sign.PISCES: {
        "persona": "感受力强、会融合、边界感松",
        "work_style": "更适合灵感型、疗愈型、艺术型或幕后支持型工作",
        "career_tags": ["影视音乐", "疗愈身心", "公益慈善", "摄影影像", "酒旅服务", "宗教灵性", "艺术疗愈", "幕后编导"],
    },
}

PLANET_CAREER_SYMBOLS: Dict[Planet, Dict[str, Any]] = {
    Planet.SUN: {
        "theme": "主导、表达、自我定义",
        "roles": ["管理者", "品牌主理人", "创业者", "公众人物", "教育带头人", "内容IP", "舞台型角色", "领导岗位"],
    },
    Planet.MOON: {
        "theme": "照料、感受、承接需求",
        "roles": ["心理咨询师", "护理与照护", "餐饮服务", "社群陪伴", "母婴工作者", "生活方式主理人", "社区服务", "家庭教育"],
    },
    Planet.MERCURY: {
        "theme": "信息、表达、交易、学习",
        "roles": ["教师培训", "编辑写作", "媒体运营", "商务销售", "咨询顾问", "产品运营", "翻译传播", "数据策划"],
    },
    Planet.VENUS: {
        "theme": "关系、审美、价值交换",
        "roles": ["品牌公关", "设计审美", "美业时尚", "客户经理", "艺术商业", "奢品零售", "商务接待", "关系经营"],
    },
    Planet.MARS: {
        "theme": "行动、竞争、执行、攻坚",
        "roles": ["运动竞技", "军事警务", "工程施工", "手术急救", "项目推进", "危机处置", "外勤执行", "谈判攻坚"],
    },
    Planet.JUPITER: {
        "theme": "扩张、信念、教育、远见",
        "roles": ["法律咨询", "教育培训", "顾问导师", "国际业务", "投资拓展", "出版传播", "出海业务", "资源拓展"],
    },
    Planet.SATURN: {
        "theme": "结构、规则、长期建设",
        "roles": ["项目管理", "企业治理", "审计风控", "工程制造", "制度研究", "地产基建", "流程搭建", "交付管理"],
    },
    Planet.URANUS: {
        "theme": "创新、科技、突破旧系统",
        "roles": ["互联网产品", "前沿科技", "算法工程", "社会创新", "组织变革", "平台架构"],
    },
    Planet.NEPTUNE: {
        "theme": "灵感、想象、疗愈、融合",
        "roles": ["影视音乐", "摄影影像", "心理疗愈", "公益慈善", "身心灵工作", "酒旅服务"],
    },
    Planet.PLUTO: {
        "theme": "掌控、调查、转化、极限压力",
        "roles": ["金融交易", "风控合规", "法务调查", "心理分析", "外科手术", "危机管理"],
    },
    Planet.NORTH_NODE: {
        "theme": "增长、升级、未来牵引",
        "roles": ["新赛道开拓", "成长业务", "转型项目", "跨界探索"],
    },
    Planet.SOUTH_NODE: {
        "theme": "旧经验、熟练路径、惯性天赋",
        "roles": ["传统技艺", "成熟流程岗位", "经验型顾问", "旧资源经营"],
    },
}

HOUSE_CAREER_SYMBOLS: Dict[int, Dict[str, Any]] = {
    1: {
        "path_title": "个人品牌路径",
        "roles": ["创业者", "主理人", "教练顾问", "主播博主", "艺人IP", "个人品牌经营", "自由职业", "顾问型业务"],
    },
    2: {
        "path_title": "资源变现路径",
        "roles": ["财务会计", "资产管理", "采购供应", "定价销售", "电商经营", "资源整合", "资金管理", "商业化岗位"],
    },
    3: {
        "path_title": "传播表达路径",
        "roles": ["媒体编辑", "教育培训", "商务拓展", "运营策划", "记者主持", "物流交通", "课程研发", "新媒体传播"],
    },
    4: {
        "path_title": "根基经营路径",
        "roles": ["地产家居", "酒店民宿", "家族生意", "社区服务", "土地农业", "空间运营", "家政收纳", "园区运营"],
    },
    5: {
        "path_title": "创作表现路径",
        "roles": ["娱乐演艺", "内容创作", "广告营销", "儿童教育", "IP孵化", "活动策展", "直播内容", "兴趣商业"],
    },
    6: {
        "path_title": "执行管理路径",
        "roles": ["运营管理", "行政流程", "医护健康", "健身营养", "宠物服务", "人事支持", "助理统筹", "服务交付"],
    },
    7: {
        "path_title": "合作联盟路径",
        "roles": ["客户经理", "律师顾问", "渠道合作", "咨询销售", "商务谈判", "合伙经营", "婚庆顾问", "签约经纪"],
    },
    8: {
        "path_title": "风险筹码路径",
        "roles": ["投资金融", "税务保险", "风控审计", "心理咨询", "遗产信托", "危机处理", "并购重组", "深度调查"],
    },
    9: {
        "path_title": "理念扩张路径",
        "roles": ["教育学术", "法律出版", "国际业务", "文旅出海", "宗教哲学", "政策研究", "跨境内容", "知识付费"],
    },
    10: {
        "path_title": "公开成就路径",
        "roles": ["企业高管", "公职体系", "品牌负责人", "行业领头人", "公共事务", "名望职业", "管理层岗位", "行业专家"],
    },
    11: {
        "path_title": "社群组织路径",
        "roles": ["互联网平台", "社群运营", "商业联盟", "NGO组织", "用户增长", "资源网络搭建", "会员体系", "私域经营"],
    },
    12: {
        "path_title": "幕后支持路径",
        "roles": ["研究分析", "疗愈服务", "保密项目", "机构后勤", "公益支持", "收尾修复", "幕后策划", "机构支持岗"],
    },
}

PLANET_ROLE_STEMS: Dict[Planet, str] = {
    Planet.SUN: "主导",
    Planet.MOON: "照护",
    Planet.MERCURY: "信息",
    Planet.VENUS: "关系",
    Planet.MARS: "行动",
    Planet.JUPITER: "扩张",
    Planet.SATURN: "结构",
}

PLANET_ROLE_ENDINGS: Dict[Planet, str] = {
    Planet.SUN: "带头者",
    Planet.MOON: "承接者",
    Planet.MERCURY: "组织者",
    Planet.VENUS: "经营者",
    Planet.MARS: "推进者",
    Planet.JUPITER: "整合者",
    Planet.SATURN: "架构者",
}

HOUSE_ROLE_STEMS: Dict[int, str] = {
    1: "个人",
    2: "资源",
    3: "传播",
    4: "根基",
    5: "创作",
    6: "执行",
    7: "联盟",
    8: "风控",
    9: "理念",
    10: "公开",
    11: "社群",
    12: "幕后",
}

LATE_FIVE_HOUSE_ORB = 5.0

HOUSE_DOMAIN_WEIGHTS: Dict[int, Dict[str, float]] = {
    1: {"career": 0.20, "wealth": 0.10, "relationship": 0.15, "health": 0.45, "family": 0.10},
    2: {"career": 0.20, "wealth": 0.55, "relationship": 0.05, "health": 0.05, "family": 0.15},
    3: {"career": 0.25, "wealth": 0.10, "relationship": 0.10, "health": 0.10, "family": 0.30},
    4: {"career": 0.10, "wealth": 0.10, "relationship": 0.20, "health": 0.10, "family": 0.50},
    5: {"career": 0.15, "wealth": 0.10, "relationship": 0.45, "health": 0.10, "family": 0.20},
    6: {"career": 0.35, "wealth": 0.10, "relationship": 0.05, "health": 0.40, "family": 0.10},
    7: {"career": 0.15, "wealth": 0.10, "relationship": 0.55, "health": 0.05, "family": 0.15},
    8: {"career": 0.10, "wealth": 0.45, "relationship": 0.10, "health": 0.25, "family": 0.10},
    9: {"career": 0.25, "wealth": 0.10, "relationship": 0.10, "health": 0.05, "family": 0.10},
    10: {"career": 0.55, "wealth": 0.15, "relationship": 0.05, "health": 0.05, "family": 0.05},
    11: {"career": 0.25, "wealth": 0.25, "relationship": 0.25, "health": 0.05, "family": 0.05},
    12: {"career": 0.05, "wealth": 0.05, "relationship": 0.10, "health": 0.40, "family": 0.20},
}

PLANET_DOMAIN_WEIGHTS: Dict[Planet, Dict[str, float]] = {
    Planet.SUN: {"career": 0.40, "wealth": 0.15, "relationship": 0.10, "health": 0.10, "family": 0.05},
    Planet.MOON: {"career": 0.05, "wealth": 0.10, "relationship": 0.25, "health": 0.25, "family": 0.30},
    Planet.MERCURY: {"career": 0.30, "wealth": 0.20, "relationship": 0.10, "health": 0.05, "family": 0.05},
    Planet.VENUS: {"career": 0.10, "wealth": 0.15, "relationship": 0.40, "health": 0.05, "family": 0.15},
    Planet.MARS: {"career": 0.35, "wealth": 0.15, "relationship": 0.05, "health": 0.20, "family": 0.05},
    Planet.JUPITER: {"career": 0.20, "wealth": 0.35, "relationship": 0.15, "health": 0.05, "family": 0.10},
    Planet.SATURN: {"career": 0.35, "wealth": 0.15, "relationship": 0.05, "health": 0.15, "family": 0.10},
    Planet.NORTH_NODE: {"career": 0.20, "wealth": 0.20, "relationship": 0.20, "health": 0.10, "family": 0.10},
    Planet.SOUTH_NODE: {"career": 0.10, "wealth": 0.10, "relationship": 0.10, "health": 0.20, "family": 0.20},
}

ASPECT_LABELS = {
    AspectType.CONJUNCTION: "合相",
    AspectType.SEXTILE: "六合",
    AspectType.SQUARE: "刑相",
    AspectType.TRINE: "三合",
    AspectType.OPPOSITION: "对冲",
    AspectType.QUINCUNX: "梅花相",
}

TRADITIONAL_PLANETS = [
    Planet.SUN,
    Planet.MOON,
    Planet.MERCURY,
    Planet.VENUS,
    Planet.MARS,
    Planet.JUPITER,
    Planet.SATURN,
]

SECT_DAY_PLANETS = {Planet.SUN, Planet.JUPITER, Planet.SATURN}
SECT_NIGHT_PLANETS = {Planet.MOON, Planet.VENUS, Planet.MARS}
PLANET_ORBS: Dict[Planet, float] = {
    Planet.SUN: 8.0,
    Planet.MOON: 7.0,
    Planet.MERCURY: 5.5,
    Planet.VENUS: 5.5,
    Planet.MARS: 6.0,
    Planet.JUPITER: 6.0,
    Planet.SATURN: 6.0,
}

SIDEREAL_MONTH_DAYS = 27.321661
LUNAR_RETURN_ORB_DEGREES = 3.0
LUNAR_RETURN_MOON_ASPECTS = [
    {"key": "CONJUNCTION", "label": "合相", "angle": 0.0},
    {"key": "SEXTILE", "label": "六合", "angle": 60.0},
    {"key": "SQUARE", "label": "刑相", "angle": 90.0},
    {"key": "TRINE", "label": "拱相", "angle": 120.0},
    {"key": "QUINCUNX", "label": "梅花", "angle": 150.0},
    {"key": "OPPOSITION", "label": "冲相", "angle": 180.0},
]
LUNAR_RETURN_WINDOW_PLANETS = [
    Planet.SUN,
    Planet.MERCURY,
    Planet.VENUS,
    Planet.MARS,
    Planet.JUPITER,
    Planet.SATURN,
    Planet.URANUS,
    Planet.NEPTUNE,
    Planet.PLUTO,
]


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def planet_label(planet: Planet | str) -> str:
    if isinstance(planet, Planet):
        return PLANET_LABELS.get(planet, planet.value)
    try:
        return PLANET_LABELS[Planet(planet)]
    except Exception:
        return str(planet)


def sign_label(sign: Sign | str) -> str:
    if isinstance(sign, Sign):
        return SIGN_LABELS.get(sign, sign.value)
    try:
        return SIGN_LABELS[Sign(sign)]
    except Exception:
        return str(sign)


def get_planet_orb(planet: Planet) -> float:
    return PLANET_ORBS.get(planet, 5.5)


class LifeKlineService:
    def __init__(self) -> None:
        self.engine = EphemerisEngine()

    def generate_report(
        self,
        birth_time_iso: str,
        lat: float,
        lon: float,
        timezone_offset: float = 8.0,
        gender: Optional[str] = None,
    ) -> Dict[str, Any]:
        birth_time_local, birth_time_utc = self._parse_birth_time(birth_time_iso, timezone_offset)
        chart = self.engine.calculate_chart(birth_time_utc, lat, lon)
        aspect_cache = self._build_aspect_cache(chart)
        planet_profiles = self._build_planet_profiles(chart, aspect_cache)
        periods = calculate_firdaria_periods(chart.is_day_chart)

        output_data: Dict[str, Any] = {
            "meta": {
                "generated_at": datetime.now().isoformat(),
                "engine_version": "2.4.0",
            },
            "user_info": {
                "gender": gender,
                "birth_time_local": birth_time_local.isoformat(),
                "birth_time_utc": birth_time_utc.isoformat(),
                "lat": lat,
                "lon": lon,
                "timezone": f"GMT {timezone_offset:+.2f}",
                "is_day_chart": chart.is_day_chart,
            },
            "kline_data": {"periods": []},
        }

        periods_data = self._build_periods_data(
            periods=periods,
            birth_time_local=birth_time_local,
            chart=chart,
            planet_profiles=planet_profiles,
            aspect_cache=aspect_cache,
        )
        output_data["kline_data"]["periods"] = periods_data

        natal_chart = self._build_natal_chart(
            chart,
            planet_profiles,
            aspect_cache,
            birth_time_utc=birth_time_utc,
            lat=lat,
            lon=lon,
        )
        current_phase = self._build_current_phase(periods_data, birth_time_local)
        life_model = self._build_life_model(
            chart=chart,
            natal_chart=natal_chart,
            periods_data=periods_data,
            current_phase=current_phase,
        )
        advanced_patterns = self._build_advanced_patterns(
            birth_time_iso=birth_time_iso,
            lat=lat,
            lon=lon,
            natal_chart=natal_chart,
            planet_profiles=planet_profiles,
            aspect_cache=aspect_cache,
        )
        natal_blueprint = self._build_natal_blueprint(
            birth_time_iso=birth_time_iso,
            lat=lat,
            lon=lon,
            natal_chart=natal_chart,
            planet_profiles=planet_profiles,
            advanced_patterns=advanced_patterns,
        )
        timeline_validation = self._build_timeline_validation(
            birth_time_iso=birth_time_iso,
            birth_time_local=birth_time_local,
            lat=lat,
            lon=lon,
            periods_data=periods_data,
        )

        output_data["natal_chart"] = natal_chart
        output_data["current_phase"] = current_phase
        output_data["life_model"] = life_model
        output_data["natal_blueprint"] = natal_blueprint
        output_data["advanced_patterns"] = advanced_patterns
        output_data["timeline_validation"] = timeline_validation
        return output_data

    def _parse_birth_time(self, birth_time_iso: str, timezone_offset: float) -> tuple[datetime, datetime]:
        try:
            parsed_birth_time = datetime.fromisoformat(birth_time_iso)
        except ValueError as exc:
            raise ValueError(
                f"Invalid date format: {birth_time_iso}. Expected ISO 8601."
            ) from exc

        if parsed_birth_time.tzinfo is not None:
            birth_time_utc = parsed_birth_time.astimezone(timezone.utc).replace(tzinfo=None)
            birth_time_local = birth_time_utc + timedelta(hours=timezone_offset)
        else:
            birth_time_local = parsed_birth_time
            birth_time_utc = birth_time_local - timedelta(hours=timezone_offset)
        return birth_time_local, birth_time_utc

    def _find_current_lunar_return(
        self,
        natal_chart: Any,
        birth_time_utc: datetime,
        reference_time_utc: datetime,
    ) -> datetime:
        natal_moon = natal_chart.get_planet_info(Planet.MOON)
        if not natal_moon:
            raise ValueError("Natal moon position is unavailable.")

        natal_moon_longitude = self._absolute_longitude(natal_moon)
        days_since_birth = max((reference_time_utc - birth_time_utc).total_seconds() / 86400.0, 0.0)
        cycles_elapsed = max(int(days_since_birth // SIDEREAL_MONTH_DAYS), 0)

        search_start = birth_time_utc + timedelta(days=max(cycles_elapsed - 1, 0) * SIDEREAL_MONTH_DAYS)
        last_match: Optional[datetime] = None

        for cycle_index in range(max(cycles_elapsed + 3, 4)):
            target = self._find_lunar_return_near(
                start_utc=search_start + timedelta(days=cycle_index * SIDEREAL_MONTH_DAYS),
                natal_moon_longitude=natal_moon_longitude,
                lat=natal_chart.location["lat"] if getattr(natal_chart, "location", None) else 0.0,
                lon=natal_chart.location["lon"] if getattr(natal_chart, "location", None) else 0.0,
            )
            if target <= reference_time_utc:
                last_match = target
                continue
            if last_match is not None:
                return last_match
            return target

        if last_match is None:
            raise ValueError("Failed to locate current lunar return.")
        return last_match

    def _find_nth_lunar_return_after(
        self,
        natal_chart: Any,
        birth_time_utc: datetime,
        start_time_utc: datetime,
        count: int,
    ) -> datetime:
        natal_moon = natal_chart.get_planet_info(Planet.MOON)
        if not natal_moon:
            raise ValueError("Natal moon position is unavailable.")

        natal_moon_longitude = self._absolute_longitude(natal_moon)
        current = start_time_utc
        found = 0

        while found < count:
            guess_days = max((current - birth_time_utc).total_seconds() / 86400.0, 0.0)
            cycle_index = max(int(round(guess_days / SIDEREAL_MONTH_DAYS)), 0)
            candidate = self._find_lunar_return_near(
                start_utc=birth_time_utc + timedelta(days=cycle_index * SIDEREAL_MONTH_DAYS),
                natal_moon_longitude=natal_moon_longitude,
                lat=natal_chart.location["lat"] if getattr(natal_chart, "location", None) else 0.0,
                lon=natal_chart.location["lon"] if getattr(natal_chart, "location", None) else 0.0,
            )
            if candidate <= current:
                candidate = self._find_lunar_return_near(
                    start_utc=birth_time_utc + timedelta(days=(cycle_index + 1) * SIDEREAL_MONTH_DAYS),
                    natal_moon_longitude=natal_moon_longitude,
                    lat=natal_chart.location["lat"] if getattr(natal_chart, "location", None) else 0.0,
                    lon=natal_chart.location["lon"] if getattr(natal_chart, "location", None) else 0.0,
                )
            current = candidate + timedelta(minutes=1)
            found += 1
        return current - timedelta(minutes=1)

    def _find_lunar_return_near(
        self,
        start_utc: datetime,
        natal_moon_longitude: float,
        lat: float,
        lon: float,
    ) -> datetime:
        coarse_start = start_utc - timedelta(days=2)
        coarse_end = start_utc + timedelta(days=2)
        step = timedelta(hours=6)
        best_time = coarse_start
        best_value = 999.0

        cursor = coarse_start
        while cursor <= coarse_end:
            moon_longitude = self._moon_longitude_at(cursor, lat, lon)
            distance = deg_diff(moon_longitude, natal_moon_longitude)
            if distance < best_value:
                best_value = distance
                best_time = cursor
            cursor += step

        left = best_time - timedelta(hours=6)
        right = best_time + timedelta(hours=6)

        for delta_seconds in (3600, 300, 60, 1):
            current = left
            local_best_time = current
            local_best_value = 999.0
            local_step = timedelta(seconds=delta_seconds)
            while current <= right:
                moon_longitude = self._moon_longitude_at(current, lat, lon)
                distance = deg_diff(moon_longitude, natal_moon_longitude)
                if distance < local_best_value:
                    local_best_value = distance
                    local_best_time = current
                current += local_step
            left = local_best_time - local_step
            right = local_best_time + local_step
            best_time = local_best_time

        return best_time

    def _moon_longitude_at(self, dt_utc: datetime, lat: float, lon: float) -> float:
        chart = self.engine.calculate_chart(dt_utc, lat, lon)
        moon = chart.get_planet_info(Planet.MOON)
        if not moon:
            raise ValueError("Moon position is unavailable.")
        return self._absolute_longitude(moon)

    def _build_aspect_cache(self, chart: Any) -> Dict[Planet, list[Dict[str, Any]]]:
        cache: Dict[Planet, list[Dict[str, Any]]] = {planet: [] for planet in TRADITIONAL_PLANETS}
        for planet_a, planet_b in combinations(TRADITIONAL_PLANETS, 2):
            info_a = chart.get_planet_info(planet_a)
            info_b = chart.get_planet_info(planet_b)
            if not info_a or not info_b:
                continue

            aspect = self._detect_aspect(planet_a, info_a, planet_b, info_b)
            if not aspect:
                continue

            cache[planet_a].append(aspect)
            cache[planet_b].append(aspect)
        return cache

    def _detect_aspect(self, planet_a: Planet, info_a: Any, planet_b: Planet, info_b: Any) -> Optional[Dict[str, Any]]:
        longitude_a = self._absolute_longitude(info_a)
        longitude_b = self._absolute_longitude(info_b)
        diff = abs(longitude_a - longitude_b) % 360
        diff = min(diff, 360 - diff)

        best: Optional[Dict[str, Any]] = None
        best_orb = 999.0
        pair_orb = (get_planet_orb(planet_a) + get_planet_orb(planet_b)) / 2.0

        for aspect_type in (
            AspectType.CONJUNCTION,
            AspectType.SEXTILE,
            AspectType.SQUARE,
            AspectType.TRINE,
            AspectType.OPPOSITION,
        ):
            config = ASPECT_CONFIG[aspect_type]
            aspect_orb = min(config["orb"], pair_orb)
            orb = abs(diff - config["angle"])
            if orb > aspect_orb or orb >= best_orb:
                continue

            strength = clamp(config["strength"] * (1.0 - orb / aspect_orb), 0.1, 1.0)
            best_orb = orb
            best = {
                "planet1": planet_a,
                "planet2": planet_b,
                "type": aspect_type,
                "orb": round(orb, 2),
                "strength": round(strength, 3),
                "nature": self._aspect_nature(aspect_type, planet_a, planet_b),
                "label": ASPECT_LABELS[aspect_type],
                "summary": self._aspect_summary(aspect_type, planet_a, planet_b),
            }

        return best

    def _aspect_nature(self, aspect_type: AspectType, planet_a: Planet, planet_b: Planet) -> str:
        if aspect_type in (AspectType.TRINE, AspectType.SEXTILE):
            return "supportive"
        if aspect_type in (AspectType.SQUARE, AspectType.OPPOSITION):
            return "challenging"
        if aspect_type == AspectType.CONJUNCTION:
            if planet_a.is_benefic or planet_b.is_benefic:
                return "supportive"
            if planet_a.is_malefic or planet_b.is_malefic:
                return "challenging"
        return "mixed"

    def _aspect_summary(self, aspect_type: AspectType, planet_a: Planet, planet_b: Planet) -> str:
        label_a = planet_label(planet_a)
        label_b = planet_label(planet_b)
        if aspect_type == AspectType.CONJUNCTION:
            return f"{label_a}与{label_b}合流，主题会被放大。"
        if aspect_type == AspectType.TRINE:
            return f"{label_a}与{label_b}形成顺流，推进更自然。"
        if aspect_type == AspectType.SEXTILE:
            return f"{label_a}与{label_b}互相配合，适合主动争取。"
        if aspect_type == AspectType.SQUARE:
            return f"{label_a}与{label_b}存在张力，逼你调整方法。"
        if aspect_type == AspectType.OPPOSITION:
            return f"{label_a}与{label_b}拉扯明显，需要在两端寻找平衡。"
        return f"{label_a}与{label_b}形成复杂联动。"

    def _build_planet_profiles(
        self,
        chart: Any,
        aspect_cache: Dict[Planet, list[Dict[str, Any]]],
    ) -> Dict[Planet, Dict[str, Any]]:
        profiles: Dict[Planet, Dict[str, Any]] = {}
        asc_sign = chart.houses[0][0] if hasattr(chart, "houses") and chart.houses else None
        chart_ruler = SIGN_RULERS.get(asc_sign) if asc_sign else None

        for planet in TRADITIONAL_PLANETS:
            info = chart.get_planet_info(planet)
            if not info:
                continue

            dignity_code, dignity_score = self._dignity_state(planet, info.sign)
            aspects = sorted(
                aspect_cache.get(planet, []),
                key=lambda item: item["strength"],
                reverse=True,
            )
            supportive = sum(a["strength"] for a in aspects if a["nature"] == "supportive")
            challenging = sum(a["strength"] for a in aspects if a["nature"] == "challenging")
            mixed = sum(a["strength"] for a in aspects if a["nature"] == "mixed")
            house_score = self._house_strength(info.house)
            joy_score = 0.35 if JOY_HOUSES.get(planet) == info.house else 0.0
            sect_score = self._sect_modifier(planet, chart.is_day_chart)
            retrograde_penalty = -0.3 if getattr(info, "is_retrograde", False) else 0.0
            ruler_bonus = 0.25 if chart_ruler == planet else 0.0

            score = (
                dignity_score
                + house_score
                + joy_score
                + sect_score
                + supportive * 0.55
                - challenging * 0.65
                - mixed * 0.10
                + retrograde_penalty
                + ruler_bonus
            )
            score = clamp(score, -3.2, 3.2)

            house_title = HOUSE_TOPICS[info.house]["title"]
            keywords = [
                PLANET_ARCHETYPES[planet]["gift"],
                *HOUSE_TOPICS[info.house]["keywords"][:2],
            ]
            profiles[planet] = {
                "planet": planet,
                "label": planet_label(planet),
                "sign": info.sign.value,
                "sign_label": sign_label(info.sign),
                "house": info.house,
                "house_title": house_title,
                "degree": round(info.degree, 6),
                "retrograde": bool(getattr(info, "is_retrograde", False)),
                "dignity": dignity_code,
                "dignity_label": DIGNITY_LABELS[dignity_code],
                "score": round(score, 3),
                "supportive_aspects": round(supportive, 3),
                "challenging_aspects": round(challenging, 3),
                "aspect_signature": [self._format_aspect_line(planet, item) for item in aspects[:3]],
                "aspect_count": len(aspects),
                "keywords": keywords,
                "gift": PLANET_ARCHETYPES[planet]["gift"],
                "shadow": PLANET_ARCHETYPES[planet]["shadow"],
                "strategy": PLANET_ARCHETYPES[planet]["strategy"],
                "reason": self._planet_reason(
                    planet=planet,
                    dignity_label=DIGNITY_LABELS[dignity_code],
                    house_title=house_title,
                    supportive=supportive,
                    challenging=challenging,
                    chart_ruler=chart_ruler,
                ),
            }
        return profiles

    def _planet_reason(
        self,
        planet: Planet,
        dignity_label: str,
        house_title: str,
        supportive: float,
        challenging: float,
        chart_ruler: Optional[Planet],
    ) -> str:
        reason = f"{planet_label(planet)}落在{house_title}，先天状态为{dignity_label}。"
        if supportive > challenging + 0.35:
            reason += " 相位支持较多，能把天赋顺着结构用出来。"
        elif challenging > supportive + 0.35:
            reason += " 相位拉扯偏重，人生会通过摩擦逼出成熟度。"
        else:
            reason += " 支持与压力并存，需要靠节奏管理来定胜负。"
        if chart_ruler == planet:
            reason += " 这也是整张命盘的命主星，权重更高。"
        return reason

    def _format_aspect_line(self, focus_planet: Planet, aspect: Dict[str, Any]) -> str:
        other = aspect["planet2"] if aspect["planet1"] == focus_planet else aspect["planet1"]
        return f"{aspect['label']} {planet_label(other)}，容许度 {aspect['orb']}°"

    def _dignity_state(self, planet: Planet, sign: Sign) -> tuple[str, float]:
        if sign in DOMICILE_SIGNS.get(planet, []):
            return "domicile", 1.8
        if sign in EXALTATION_SIGNS.get(planet, []):
            return "exaltation", 1.35
        if sign in DETRIMENT_SIGNS.get(planet, []):
            return "detriment", -1.35
        if sign in FALL_SIGNS.get(planet, []):
            return "fall", -1.75
        return "peregrine", 0.0

    def _house_strength(self, house: int) -> float:
        if house in ANGULAR_HOUSES:
            return 0.95
        if house in SUCCEDENT_HOUSES:
            return 0.45
        if house in CADENT_HOUSES:
            return 0.1
        return 0.0

    def _sect_modifier(self, planet: Planet, is_day_chart: bool) -> float:
        if planet == Planet.MERCURY:
            return 0.1
        if is_day_chart and planet in SECT_DAY_PLANETS:
            return 0.25
        if (not is_day_chart) and planet in SECT_NIGHT_PLANETS:
            return 0.25
        if is_day_chart and planet == Planet.MARS:
            return -0.2
        if (not is_day_chart) and planet == Planet.SATURN:
            return -0.2
        return 0.0

    def _build_periods_data(
        self,
        periods: Iterable[FirdariaPeriod],
        birth_time_local: datetime,
        chart: Any,
        planet_profiles: Dict[Planet, Dict[str, Any]],
        aspect_cache: Dict[Planet, list[Dict[str, Any]]],
    ) -> list[Dict[str, Any]]:
        data: list[Dict[str, Any]] = []
        for index, period in enumerate(periods):
            major_profile = planet_profiles.get(period.major_lord)
            if not major_profile:
                continue

            sub_profile = planet_profiles.get(period.sub_lord) if period.sub_lord else None
            major_score = major_profile["score"]
            sub_score = sub_profile["score"] if sub_profile else major_score * 0.6
            bonus = clamp((major_score * 0.72 + sub_score * 0.28) / 4.5, -0.75, 0.75)

            trend_type = "stable"
            if bonus >= 0.16:
                trend_type = "bull"
            elif bonus <= -0.16:
                trend_type = "bear"

            start_date = birth_time_local + timedelta(days=period.start_age * 365.242199)
            end_date = birth_time_local + timedelta(days=period.end_age * 365.242199)
            domains = self._build_domain_scores(period, major_profile, sub_profile, bonus)
            summary_pack = self._build_period_summary(
                period=period,
                major_profile=major_profile,
                sub_profile=sub_profile,
                bonus=bonus,
                trend_type=trend_type,
                domains=domains,
                aspect_cache=aspect_cache,
            )

            data.append(
                {
                    "index": index,
                    "timing": {
                        "start_age": round(period.start_age, 2),
                        "end_age": round(period.end_age, 2),
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat(),
                        "duration_years": round(period.duration, 2),
                    },
                    "lords": {
                        "major": period.major_lord.value,
                        "sub": period.sub_lord.value if period.sub_lord else None,
                    },
                    "trend": {
                        "bonus_coefficient": round(bonus, 3),
                        "type": trend_type,
                    },
                    "domains": domains,
                    "astrology": {
                        "sign": major_profile["sign"],
                        "sign_label": major_profile["sign_label"],
                        "house": major_profile["house"],
                        "house_title": major_profile["house_title"],
                        "dignity": major_profile["dignity"],
                        "dignity_label": major_profile["dignity_label"],
                        "major_score": round(major_score, 2),
                        "sub_score": round(sub_score, 2),
                        "aspect_signature": major_profile["aspect_signature"][:2],
                    },
                    "title": summary_pack["title"],
                    "summary": summary_pack["summary"],
                    "themes": summary_pack["themes"],
                    "opportunities": summary_pack["opportunities"],
                    "cautions": summary_pack["cautions"],
                    "action_focus": summary_pack["action_focus"],
                    "type": "major",
                }
            )
        return data

    def _build_domain_scores(
        self,
        period: FirdariaPeriod,
        major_profile: Dict[str, Any],
        sub_profile: Optional[Dict[str, Any]],
        bonus: float,
    ) -> Dict[str, float]:
        house_weights = HOUSE_DOMAIN_WEIGHTS[major_profile["house"]]
        planet_weights = PLANET_DOMAIN_WEIGHTS.get(period.major_lord, HOUSE_DOMAIN_WEIGHTS[major_profile["house"]])
        sub_weights = (
            PLANET_DOMAIN_WEIGHTS.get(period.sub_lord, planet_weights) if period.sub_lord else planet_weights
        )

        base = 50 + bonus * 22
        result: Dict[str, float] = {}
        for domain in ("career", "wealth", "relationship", "health", "family"):
            score = (
                base
                + house_weights[domain] * 22
                + planet_weights.get(domain, 0.1) * 18
                + sub_weights.get(domain, 0.1) * 8
                + major_profile["supportive_aspects"] * 4
                - major_profile["challenging_aspects"] * 5
            )
            result[domain] = round(clamp(score, 18, 92), 1)
        return result

    def _build_period_summary(
        self,
        period: FirdariaPeriod,
        major_profile: Dict[str, Any],
        sub_profile: Optional[Dict[str, Any]],
        bonus: float,
        trend_type: str,
        domains: Dict[str, float],
        aspect_cache: Dict[Planet, list[Dict[str, Any]]],
    ) -> Dict[str, Any]:
        house_topic = major_profile["house_title"]
        major_label = major_profile["label"]
        sub_label = sub_profile["label"] if sub_profile else "无子运"
        top_domains = self._top_domains(domains)
        themes = [
            f"{major_label}主题被放大",
            f"重点落在{house_topic}",
            f"{top_domains[0]['label']}是阶段主轴",
        ]
        opportunities = [
            self._phase_opportunity_line(major_profile, top_domains[0]["label"], trend_type),
            self._phase_opportunity_line(
                sub_profile or major_profile,
                top_domains[1]["label"] if len(top_domains) > 1 else top_domains[0]["label"],
                trend_type,
            ),
        ]
        cautions = [
            self._phase_caution_line(major_profile, trend_type),
            self._phase_caution_line(sub_profile or major_profile, "mixed"),
        ]
        action_focus = [
            f"把时间优先给{top_domains[0]['label']}和{top_domains[1]['label'] if len(top_domains) > 1 else top_domains[0]['label']}。",
            major_profile["strategy"],
            self._house_action_line(major_profile["house"]),
        ]
        summary = (
            f"{major_label}主运、{sub_label}辅运。主星落在{major_profile['house_title']}，"
            f"先天状态为{major_profile['dignity_label']}，"
            f"因此这段时间的人生重心会围绕{top_domains[0]['label']}与{top_domains[1]['label'] if len(top_domains) > 1 else top_domains[0]['label']}展开。"
        )
        title = f"{major_label} - {sub_label} 阶段"

        if trend_type == "bull":
            summary += " 整体是扩张窗口，适合把已经成熟的能力推向更大舞台。"
        elif trend_type == "bear":
            summary += " 整体偏收缩与校准，更适合整顿结构、清理负担、避免高杠杆。"
        else:
            summary += " 整体偏平稳，重点在于打磨方法、搭好结构、耐心推进。"

        return {
            "title": title,
            "summary": summary,
            "themes": themes,
            "opportunities": opportunities,
            "cautions": cautions,
            "action_focus": action_focus,
        }

    def _phase_opportunity_line(self, profile: Dict[str, Any], domain_label: str, trend_type: str) -> str:
        prefix = "放大" if trend_type == "bull" else "稳住" if trend_type == "stable" else "修复"
        return f"{prefix}{profile['label']}在{domain_label}上的能力，优先做可复用、可沉淀的成果。"

    def _phase_caution_line(self, profile: Dict[str, Any], trend_type: str) -> str:
        if trend_type == "bull":
            return f"别让{profile['label']}的顺风感演变成过度承诺，{profile['shadow']}是这段的代价点。"
        if trend_type == "bear":
            return f"这段容易放大{profile['shadow']}，不要在不稳定时做过于激进的押注。"
        return f"即使局面平稳，也要注意{profile['shadow']}，别被惯性牵着走。"

    def _house_action_line(self, house: int) -> str:
        house_title = HOUSE_TOPICS[house]["title"]
        if house == 10:
            return "把资源押在能形成社会可见度、职位抬升或作品背书的事项上。"
        if house == 7:
            return "关键突破来自合作关系，谈规则比谈感觉更重要。"
        if house == 4:
            return "先稳根基，家庭、居住、心理安全感会直接影响外部发挥。"
        if house == 6:
            return "你的胜负点不在灵感，而在习惯、流程和执行耐力。"
        if house == 11:
            return "扩大人脉池、社群协作与长期愿景，比单打独斗更高效。"
        if house == 12:
            return "控制外部噪音，预留退场与修复时间，隐性损耗要先止血。"
        return f"围绕{house_title}做结构化经营，而不是被情绪和偶然性牵着走。"

    def _top_domains(self, domains: Dict[str, float]) -> list[Dict[str, Any]]:
        label_map = {
            "career": "事业",
            "wealth": "财富",
            "relationship": "关系",
            "health": "健康",
            "family": "家庭",
        }
        ranked = sorted(domains.items(), key=lambda item: item[1], reverse=True)
        return [{"key": key, "label": label_map[key], "score": score} for key, score in ranked]

    def _build_natal_chart(
        self,
        chart: Any,
        planet_profiles: Dict[Planet, Dict[str, Any]],
        aspect_cache: Dict[Planet, list[Dict[str, Any]]],
        birth_time_utc: datetime,
        lat: float,
        lon: float,
    ) -> Dict[str, Any]:
        asc_sign = chart.houses[0][0] if hasattr(chart, "houses") and chart.houses else Sign.ARIES
        asc_degree = chart.houses[0][1] if hasattr(chart, "houses") and chart.houses else 0.0
        chart_ruler = SIGN_RULERS.get(asc_sign, Planet.SUN)

        dominant_planets = sorted(
            planet_profiles.values(),
            key=lambda item: item["score"],
            reverse=True,
        )[:3]
        weakest_planets = sorted(
            planet_profiles.values(),
            key=lambda item: item["score"],
        )[:2]

        major_aspects = self._build_major_aspects(aspect_cache)
        house_emphasis = self._build_house_emphasis(chart)
        signature = self._build_signature_text(chart, planet_profiles, chart_ruler, dominant_planets)

        planets_payload = self._build_display_planets_payload(
            chart=chart,
            planet_profiles=planet_profiles,
            birth_time_utc=birth_time_utc,
            lat=lat,
            lon=lon,
        )

        return {
            "ascendant": {
                "sign": asc_sign.value,
                "sign_label": sign_label(asc_sign),
                "degree": round(asc_degree, 6),
            },
            "houses": [
                {
                    "house": index + 1,
                    "sign": sign.value,
                    "sign_label": sign_label(sign),
                    "degree": round(degree, 6),
                    "title": HOUSE_TOPICS[index + 1]["title"],
                }
                for index, (sign, degree) in enumerate(getattr(chart, "houses", [])[:12])
            ],
            "sect": "day" if chart.is_day_chart else "night",
            "sect_label": "日盘" if chart.is_day_chart else "夜盘",
            "chart_ruler": chart_ruler.value,
            "chart_ruler_label": planet_label(chart_ruler),
            "signature": signature,
            "planets": planets_payload,
            "dominant_planets": [
                {
                    "planet": p["planet"].value,
                    "label": p["label"],
                    "score": round(p["score"], 2),
                    "reason": p["reason"],
                }
                for p in dominant_planets
            ],
            "pressure_points": [
                {
                    "planet": p["planet"].value,
                    "label": p["label"],
                    "score": round(p["score"], 2),
                    "reason": p["reason"],
                }
                for p in weakest_planets
            ],
            "house_emphasis": house_emphasis,
            "major_aspects": major_aspects,
        }

    def _build_display_planets_payload(
        self,
        chart: Any,
        planet_profiles: Dict[Planet, Dict[str, Any]],
        birth_time_utc: datetime,
        lat: float,
        lon: float,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {}

        for planet, info in getattr(chart, "planets", {}).items():
            key = planet.value
            longitude = round(float(getattr(info, "longitude", self._longitude_from_sign(info.sign, info.degree))), 6)
            house_title = HOUSE_TOPICS.get(info.house, {}).get("title", f"第{info.house}宫")
            profile = planet_profiles.get(planet)

            if profile:
                payload[key] = {
                    "sign": profile["sign"],
                    "sign_label": profile["sign_label"],
                    "house": profile["house"],
                    "house_title": profile["house_title"],
                    "dignity": profile["dignity"],
                    "dignity_label": profile["dignity_label"],
                    "degree": profile["degree"],
                    "retrograde": profile["retrograde"],
                    "score": round(profile["score"], 2),
                    "keywords": profile["keywords"],
                    "gift": profile["gift"],
                    "shadow": profile["shadow"],
                    "strategy": profile["strategy"],
                    "aspect_signature": profile["aspect_signature"],
                    "reason": profile["reason"],
                    "speed": round(float(getattr(info, "speed", 0.0)), 6),
                    "longitude": longitude,
                }
                continue

            dignity_code, _ = self._dignity_state(planet, info.sign)
            payload[key] = {
                "sign": info.sign.value,
                "sign_label": sign_label(info.sign),
                "house": info.house,
                "house_title": house_title,
                "dignity": dignity_code,
                "dignity_label": DIGNITY_LABELS[dignity_code],
                "degree": round(info.degree, 6),
                "retrograde": bool(getattr(info, "is_retrograde", False)),
                "reason": f"{planet_label(planet)}落在{house_title}，用于补充本命盘的完整轮盘视图。",
                "speed": round(float(getattr(info, "speed", 0.0)), 6),
                "longitude": longitude,
            }

        payload.update(
            self._build_auxiliary_points_payload(
                chart=chart,
                birth_time_utc=birth_time_utc,
                lat=lat,
                lon=lon,
            )
        )
        return payload

    def _build_auxiliary_points_payload(
        self,
        chart: Any,
        birth_time_utc: datetime,
        lat: float,
        lon: float,
    ) -> Dict[str, Any]:
        if swe is None:
            return {}

        jd = swe.julday(
            birth_time_utc.year,
            birth_time_utc.month,
            birth_time_utc.day,
            birth_time_utc.hour
            + birth_time_utc.minute / 60.0
            + birth_time_utc.second / 3600.0
            + birth_time_utc.microsecond / 3600000.0,
        )
        flags = swe.FLG_SPEED | swe.FLG_SWIEPH
        points: Dict[str, Any] = {}

        def add_point(key: str, swe_id: Any) -> None:
            if swe_id is None:
                return

            try:
                result, _ = swe.calc_ut(jd, swe_id, flags)
                longitude_value = float(result[0]) % 360.0
                latitude_value = float(result[1])
                speed_value = float(result[3])
                sign_value, degree_value = self.engine._get_sign_from_longitude(longitude_value)
                house_value = self._infer_house_from_longitude(chart, longitude_value)
                house_title = HOUSE_TOPICS.get(house_value, {}).get("title", f"第{house_value}宫")
                points[key] = {
                    "sign": sign_value.value,
                    "sign_label": sign_label(sign_value),
                    "house": house_value,
                    "house_title": house_title,
                    "dignity": "auxiliary",
                    "dignity_label": "附加点",
                    "degree": round(degree_value, 6),
                    "retrograde": bool(speed_value < 0),
                    "reason": f"{AUXILIARY_BODY_LABELS.get(key, key)}用于补充本命轮盘阅读。",
                    "longitude": round(longitude_value, 6),
                    "_latitude": latitude_value,
                    "_speed": speed_value,
                }
            except Exception:
                return

        for key in ("CHIRON", "CERES", "PALLAS", "JUNO", "VESTA"):
            add_point(key, getattr(swe, key, None))

        node_id = getattr(swe, "TRUE_NODE", None) or getattr(swe, "MEAN_NODE", None)
        add_point("NORTH_NODE", node_id)

        north_node = points.get("NORTH_NODE")
        if north_node:
            south_longitude = (float(north_node["longitude"]) + 180.0) % 360.0
            south_sign, south_degree = self.engine._get_sign_from_longitude(south_longitude)
            south_house = self._infer_house_from_longitude(chart, south_longitude)
            points["SOUTH_NODE"] = {
                "sign": south_sign.value,
                "sign_label": sign_label(south_sign),
                "house": south_house,
                "house_title": HOUSE_TOPICS.get(south_house, {}).get("title", f"第{south_house}宫"),
                "dignity": "auxiliary",
                "dignity_label": "附加点",
                "degree": round(south_degree, 6),
                "retrograde": bool(-float(north_node.get("_speed", 0.0)) < 0),
                "reason": f"{AUXILIARY_BODY_LABELS['SOUTH_NODE']}用于补充本命轮盘阅读。",
                "longitude": round(south_longitude, 6),
            }

        for key, item in list(points.items()):
            item.pop("_latitude", None)
            item.pop("_speed", None)

        return points

    def _infer_house_from_longitude(self, chart: Any, longitude: float) -> int:
        houses = getattr(chart, "houses", [])[:12]
        if not houses:
            return 0

        cusps: list[float] = []
        previous = -1.0
        for sign_value, degree_value in houses:
            cusp_longitude = self._longitude_from_sign(sign_value, degree_value)
            while cusp_longitude <= previous:
                cusp_longitude += 360.0
            cusps.append(cusp_longitude)
            previous = cusp_longitude

        target = longitude % 360.0
        while target < cusps[0]:
            target += 360.0

        for index, start in enumerate(cusps):
            end = cusps[index + 1] if index < len(cusps) - 1 else cusps[0] + 360.0
            if start <= target < end:
                return index + 1
        return 12

    def _longitude_from_sign(self, sign_value: Sign | str, degree_value: float) -> float:
        try:
            sign_enum = sign_value if isinstance(sign_value, Sign) else Sign(sign_value)
        except Exception:
            return float(degree_value or 0.0)
        return list(Sign).index(sign_enum) * 30.0 + float(degree_value or 0.0)

    def _build_house_emphasis(self, chart: Any) -> list[Dict[str, Any]]:
        weights: Dict[int, float] = {house: 0.0 for house in range(1, 13)}
        for planet in TRADITIONAL_PLANETS:
            info = chart.get_planet_info(planet)
            if not info:
                continue
            weights[info.house] += 1.2 if planet in (Planet.SUN, Planet.MOON) else 1.0
        ranked = sorted(weights.items(), key=lambda item: item[1], reverse=True)[:4]
        return [
            {
                "house": house,
                "title": HOUSE_TOPICS[house]["title"],
                "keywords": HOUSE_TOPICS[house]["keywords"],
                "weight": round(weight, 2),
            }
            for house, weight in ranked
            if weight > 0
        ]

    def _build_major_aspects(self, aspect_cache: Dict[Planet, list[Dict[str, Any]]]) -> list[Dict[str, Any]]:
        seen: set[tuple[str, str, str]] = set()
        aspects: list[Dict[str, Any]] = []
        for items in aspect_cache.values():
            for aspect in items:
                key = (
                    aspect["planet1"].value,
                    aspect["planet2"].value,
                    aspect["type"].value,
                )
                reverse_key = (
                    aspect["planet2"].value,
                    aspect["planet1"].value,
                    aspect["type"].value,
                )
                if key in seen or reverse_key in seen:
                    continue
                seen.add(key)
                aspects.append(
                    {
                        "title": f"{planet_label(aspect['planet1'])} {aspect['label']} {planet_label(aspect['planet2'])}",
                        "strength": aspect["strength"],
                        "nature": aspect["nature"],
                        "summary": aspect["summary"],
                    }
                )
        aspects.sort(key=lambda item: item["strength"], reverse=True)
        return aspects[:6]

    def _build_signature_text(
        self,
        chart: Any,
        planet_profiles: Dict[Planet, Dict[str, Any]],
        chart_ruler: Planet,
        dominant_planets: list[Dict[str, Any]],
    ) -> str:
        sun_sign = sign_label(chart.get_planet_info(Planet.SUN).sign) if chart.get_planet_info(Planet.SUN) else "未知"
        moon_sign = sign_label(chart.get_planet_info(Planet.MOON).sign) if chart.get_planet_info(Planet.MOON) else "未知"
        asc_sign = sign_label(chart.houses[0][0]) if hasattr(chart, "houses") and chart.houses else "未知"
        dominant_labels = "、".join(item["label"] for item in dominant_planets[:2])
        return (
            f"这是一个以{asc_sign}上升起盘、太阳落在{sun_sign}、月亮落在{moon_sign}的命盘。"
            f"命主星是{planet_label(chart_ruler)}，主导力量偏向{dominant_labels}。"
            "整体不是靠单一高光取胜，而是靠把人生关键主题做成长期结构。"
        )

    def _build_current_phase(
        self,
        periods_data: list[Dict[str, Any]],
        birth_time_local: datetime,
    ) -> Optional[Dict[str, Any]]:
        current_age = (datetime.now() - birth_time_local).days / 365.2422
        for period in periods_data:
            start_age = period["timing"]["start_age"]
            end_age = period["timing"]["end_age"]
            if not (start_age <= current_age < end_age):
                continue

            domains_ranked = self._top_domains(period["domains"])
            bonus = period["trend"]["bonus_coefficient"]
            trend_type = period["trend"]["type"]
            feeling = self._current_feeling(period["astrology"]["house_title"], trend_type)
            description = self._trend_display_text(trend_type, bonus)
            return {
                "age_range": f"{int(start_age)} - {int(end_age)} 岁",
                "start_date": period["timing"]["start_date"],
                "end_date": period["timing"]["end_date"],
                "major_lord": period["lords"]["major"],
                "sub_lord": period["lords"]["sub"] or "",
                "trend_type": trend_type,
                "score": round(50 + bonus * 40, 1),
                "keywords": period["themes"][:3],
                "feeling": feeling,
                "description": description,
                "summary": period["summary"],
                "opportunities": period["opportunities"],
                "cautions": period["cautions"],
                "action_focus": period["action_focus"],
                "dominant_domains": domains_ranked[:3],
                "why_now": (
                    f"主运星落在{period['astrology']['house_title']}，"
                    f"且先天状态为{period['astrology']['dignity_label']}，"
                    "所以这几年的人生议题会更集中、更具体。"
                ),
            }
        return None

    def _current_feeling(self, house_title: str, trend_type: str) -> str:
        if trend_type == "bull":
            return f"你会明显感觉到，围绕{house_title}的事情更容易出现推力和窗口。"
        if trend_type == "bear":
            return f"你会感到，{house_title}相关的课题在逼你收缩、修正和重新排优先级。"
        return f"当前阶段不会剧烈翻盘，但{house_title}会成为你持续经营的主线。"

    def _trend_display_text(self, trend_type: str, bonus: float) -> str:
        if trend_type == "bull":
            return f"扩张段（基准提升 {bonus:.0%}）"
        if trend_type == "bear":
            return f"收缩段（基准回落 {abs(bonus):.0%}）"
        return "平稳段"

    def _build_natal_blueprint(
        self,
        birth_time_iso: str,
        lat: float,
        lon: float,
        natal_chart: Dict[str, Any],
        planet_profiles: Dict[Planet, Dict[str, Any]],
        advanced_patterns: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        is_historical_sample = self._is_huang_jinrong_sample(birth_time_iso, lat, lon)
        dominant = natal_chart.get("dominant_planets", [])
        pressure_points = natal_chart.get("pressure_points", [])
        houses = natal_chart.get("house_emphasis", [])
        aspects = natal_chart.get("major_aspects", [])
        top_house = houses[0] if houses else None
        second_house = houses[1] if len(houses) > 1 else None
        chart_ruler_value = natal_chart.get("chart_ruler")
        chart_ruler_label = natal_chart.get("chart_ruler_label", "命主星")

        chart_ruler_profile: Optional[Dict[str, Any]] = None
        if chart_ruler_value:
            try:
                chart_ruler_profile = planet_profiles.get(Planet(chart_ruler_value))
            except Exception:
                chart_ruler_profile = None
        sun_profile = planet_profiles.get(Planet.SUN)
        moon_profile = planet_profiles.get(Planet.MOON)

        house_rulers = list(advanced_patterns.get("house_rulers", [])) if advanced_patterns else self._build_house_ruler_map(natal_chart, planet_profiles)
        ruler_groups = list(advanced_patterns.get("ruler_groups", [])) if advanced_patterns else self._build_ruler_groups(house_rulers, planet_profiles)
        reception_groups = list(advanced_patterns.get("reception_groups", [])) if advanced_patterns else []
        mutual_receptions = list(advanced_patterns.get("mutual_receptions", [])) if advanced_patterns else []
        pattern_readings = list(advanced_patterns.get("pattern_readings", [])) if advanced_patterns else []
        house_map = {item["house"]: item for item in house_rulers}
        group_map = {item["ruler"]: item for item in ruler_groups}
        chart_ruler_group = group_map.get(chart_ruler_value) if chart_ruler_value else None
        line_7 = house_map.get(7)
        line_10 = house_map.get(10)
        line_12 = house_map.get(12)

        role_title = self._build_role_title(natal_chart, planet_profiles, is_historical_sample)
        role_keywords = self._build_role_keywords(natal_chart)
        dominant_labels = " / ".join(item["label"] for item in dominant[:2]) if dominant else chart_ruler_label
        chart_ruler_line = (
            f"{chart_ruler_label}落第{chart_ruler_profile['house']}宫 {chart_ruler_profile['house_title']}"
            if chart_ruler_profile
            else f"{chart_ruler_label}主导"
        )
        top_aspect = aspects[0]["title"] if aspects else None
        structure_summary = (
            "这张盘的底层不是靠单点爆发取胜，而是靠把核心议题做成长期结构。"
            if not is_historical_sample
            else "这张盘的底层不是天然高位，而是通过信息、关系、资源与隐性控制一步步做大。"
        )
        power_summary = (
            "真正影响人生走向的，不只是性格，而是你如何获得资源、进入系统并形成控制力。"
        )
        role_summary = (
            "角色层不是只看一个标签，而是把星体先天星性、落座风格、落宫场景与相位结构合并起来，判断你在社会中更像哪一种人。"
        )
        cost_summary = (
            "每种强项都有对应的代价。越能成事的结构，越需要知道它会从哪里反噬。"
        )

        structure_evidence = self._unique_strings(
            [
                f"{natal_chart['ascendant']['sign_label']}上升",
                chart_ruler_line,
                chart_ruler_group["line"] if chart_ruler_group else None,
                f"主导行星 {dominant_labels}",
                f"重点宫位 {self._format_house_titles(houses[:3])}" if houses else None,
                top_aspect,
            ]
        )
        structure_focus_cards = [
            self._blueprint_focus_card(
                label="命主入口",
                value=chart_ruler_line,
                hint=chart_ruler_profile["reason"] if chart_ruler_profile else "命主星决定人生如何起手。",
            ),
            self._blueprint_focus_card(
                label="主导行星",
                value=dominant_labels,
                hint="这几颗星决定整张盘最容易被放大的主线。",
            ),
            self._blueprint_focus_card(
                label="重心宫位",
                value=self._format_house_titles(houses[:2]),
                hint="这些宫位会反复变成你的人生主场景。",
            ),
        ]
        structure_points = [
            (
                f"上升在{natal_chart['ascendant']['sign_label']}，命主星是{chart_ruler_label}。"
                f"这说明你的人生入口更依赖{chart_ruler_profile['gift'] if chart_ruler_profile else '长期经营能力'}。"
            ),
            (
                f"主导力量偏向{'、'.join(item['label'] for item in dominant[:2]) or chart_ruler_label}，"
                "真正能带来跃迁的，往往不是单个高光，而是持续放大的主轴。"
            ),
            (
                f"最强宫位集中在{self._format_house_titles(houses[:3])}，"
                "它们不是零散主题，而是会反复塑造人生路径的主结构。"
            ),
        ]

        if chart_ruler_profile:
            structure_points.append(
                f"{chart_ruler_label}先天状态为{chart_ruler_profile['dignity_label']}，"
                f"{self._dignity_flow_text(chart_ruler_profile['dignity'])}"
            )
        if top_aspect:
            structure_points.append(
                f"命盘显眼相位之一是“{top_aspect}”，说明主轴不是单线推进，而会和其他核心议题持续联动。"
            )

        power_evidence = self._unique_strings(
            [
                f"第一杠杆 第{top_house['house']}宫" if top_house else None,
                f"第二杠杆 第{second_house['house']}宫" if second_house else None,
                line_7["line"] if line_7 else None,
                line_10["line"] if line_10 else None,
                line_12["line"] if line_12 else None,
            ]
        )
        power_focus_cards = [
            self._blueprint_focus_card(
                label="第一杠杆",
                value=f"第{top_house['house']}宫 {top_house['title']}" if top_house else "关键宫位",
                hint=HOUSE_ADULT_MEANINGS.get(top_house["house"], {}).get("adult") if top_house else "最容易做成结构的入口。",
            ),
            self._blueprint_focus_card(
                label="第二杠杆",
                value=f"第{second_house['house']}宫 {second_house['title']}" if second_house else "待识别",
                hint=HOUSE_ADULT_MEANINGS.get(second_house["house"], {}).get("adult") if second_house else "第二层长期支点。",
            ),
            self._blueprint_focus_card(
                label="借力入口",
                value=line_7["line"] if line_7 else (line_10["line"] if line_10 else chart_ruler_line),
                hint="你最容易通过哪里拿到平台、合作、制度入口或公开位置。",
            ),
        ]
        power_points = []
        if top_house:
            power_points.append(
                f"第一权力入口在第{top_house['house']}宫：{HOUSE_ADULT_MEANINGS[top_house['house']]['adult']}。"
            )
            power_points.append(HOUSE_ADULT_MEANINGS[top_house["house"]]["power"])
        if second_house:
            power_points.append(
                f"第二杠杆在第{second_house['house']}宫：{HOUSE_ADULT_MEANINGS[second_house['house']]['adult']}。"
            )
        if line_7:
            power_points.append(
                f"7宫主链路是“{line_7['line']}”，说明伴侣、合作、贵人、对手或联盟关系会直接参与资源流向。"
            )
        if line_10:
            power_points.append(
                f"10宫主链路是“{line_10['line']}”，这决定了公开位置、职业身份和社会认可如何被做出来。"
            )
        if line_12:
            power_points.append(
                f"12宫主链路是“{line_12['line']}”，说明你的杠杆里往往还夹带幕后系统、隐线压力或收尾成本。"
            )
        if is_historical_sample:
            power_points = [
                "3宫过强，说明真正的上位方式不是抽象的“表达”，而是线报、传播、谈判与地面关系。",
                "7宫木星让扩张更多通过联盟、门生、保护关系与更大的制度平台完成。",
                "2宫金星与12宫火星把资源经营和幕后控制绑在一起，钱与权不会完全分开。",
            ]

        role_evidence = self._unique_strings(
            [
                role_title,
                chart_ruler_line,
                chart_ruler_profile["aspect_signature"][0] if chart_ruler_profile and chart_ruler_profile.get("aspect_signature") else None,
                sun_profile["aspect_signature"][0] if sun_profile and sun_profile.get("aspect_signature") else None,
                line_10["line"] if line_10 else None,
                f"主导行星 {dominant_labels}",
                f"重点宫位社会义 {self._format_house_adult_meanings(houses[:3])}" if houses else None,
            ]
        )
        role_focus_cards = [
            self._blueprint_focus_card(
                label="角色标题",
                value=role_title,
                hint="这是把星体先天星性、落座、落宫和相位合并后的社会化角色，不只是性格标签。",
            ),
            self._blueprint_focus_card(
                label="社会舞台",
                value=chart_ruler_profile["house_title"] if chart_ruler_profile else "现实场景",
                hint=(
                    self._planet_cross_reading(chart_ruler_profile, "chart_ruler", concise=True)
                    if chart_ruler_profile
                    else "命主星落宫，决定核心能力最容易在哪类场景显形。"
                ),
            ),
            self._blueprint_focus_card(
                label="公开线",
                value=line_10["line"] if line_10 else "10宫线待识别",
                hint="社会如何看见你，通常要看这条线。",
            ),
        ]
        role_points = [
            f"这张盘更像“{role_title}”，这个角色结论来自星体先天星性、落座方式、落宫场景和相位结构的综合判断，而不是单一标签。",
            self._planet_cross_reading(chart_ruler_profile, "chart_ruler")
            if chart_ruler_profile
            else "命主星决定你的核心能力会通过什么方式在社会里显形。",
            self._planet_cross_reading(sun_profile, "sun")
            if sun_profile
            else "太阳决定你想成为什么样的人，以及你愿意在哪个舞台承担责任。",
            self._planet_cross_reading(moon_profile, "moon")
            if moon_profile
            else "月亮决定你在关系和生活里怎样才会真的稳定。",
            f"重点宫位的成人社会义分别落在：{self._format_house_adult_meanings(houses[:4])}。",
        ]
        if line_10:
            role_points.append(
                f"公开角色会沿着“{line_10['line']}”这条线被社会确认，所以别人记住你的方式，往往和这条职业/名望线路直接相关。"
            )
        if top_aspect:
            role_points.append(
                f"角色层还要兼顾相位网络。“{top_aspect}”说明几条人格线之间会持续联动，所以你的角色不是静态标签，而是一套动态运作方式。"
            )
        if is_historical_sample:
            role_points = [
                "这张盘更像“信息操盘型权力人物”，不是温和的表达型人格。",
                "它的核心不是正面高光，而是把名单、关系、口径、制度缝隙变成控制力。",
                "同样的结构放在现代语境里，也常见于组织操盘者、关系整合者、规则边缘高手。",
            ]

        cost_evidence = self._unique_strings(
            [
                f"第一代价 {pressure_points[0]['label']}" if pressure_points else None,
                f"第二代价 {pressure_points[1]['label']}" if len(pressure_points) > 1 else None,
                line_12["line"] if line_12 else None,
                pressure_points[0]["reason"] if pressure_points else None,
            ]
        )
        cost_focus_cards = [
            self._blueprint_focus_card(
                label="第一压力点",
                value=pressure_points[0]["label"] if pressure_points else "待识别",
                hint=pressure_points[0]["reason"] if pressure_points else "最容易出现失衡和补课的位置。",
            ),
            self._blueprint_focus_card(
                label="隐线代价",
                value=line_12["line"] if line_12 else "第12宫待识别",
                hint="强项背后的幕后压力、收尾机制和延迟代价。",
            ),
            self._blueprint_focus_card(
                label="回收方式",
                value=houses[0]["title"] if houses else "核心主题",
                hint="当最强宫位失衡时，优势最容易从这里变成负担。",
            ),
        ]
        cost_points = []
        if pressure_points:
            cost_points.append(
                f"首要代价点在{pressure_points[0]['label']}：{pressure_points[0]['reason']}"
            )
        if len(pressure_points) > 1:
            cost_points.append(
                f"第二代价点在{pressure_points[1]['label']}：{pressure_points[1]['reason']}"
            )
        if houses:
            cost_points.append(
                f"当第{houses[0]['house']}宫议题失衡时，最容易把优势变成负担。"
            )
        if line_12:
            cost_points.append(
                f"12宫主链路是“{line_12['line']}”，这意味着有些代价不会立刻爆发，而会以幕后压力、关系回收或阶段性清算的方式出现。"
            )
        if is_historical_sample:
            cost_points = [
                "水星失势又合土星，意味着信息优势会越来越带上冷硬、规训与控制色彩。",
                "金星失势落2宫，说明资源与享乐一旦绑定，后期就容易把欲望变成结构性代价。",
                "12宫火星不是简单的内耗，而是幕后冲突、清算与晚年回收机制。",
            ]

        self_profile = self._build_self_profile(
            natal_chart=natal_chart,
            planet_profiles=planet_profiles,
            role_title=role_title,
            chart_ruler_line=chart_ruler_line,
            chart_ruler_profile=chart_ruler_profile,
            house_map=house_map,
            pattern_readings=pattern_readings,
            pressure_points=pressure_points,
        )
        career_blueprint = self._build_career_blueprint(
            natal_chart=natal_chart,
            planet_profiles=planet_profiles,
            role_title=role_title,
            house_map=house_map,
            ruler_groups=group_map,
            reception_groups=reception_groups,
            mutual_receptions=mutual_receptions,
        )
        theory_basis = self._build_blueprint_theory_basis(
            natal_chart=natal_chart,
            chart_ruler_line=chart_ruler_line,
            house_map=house_map,
            pattern_readings=pattern_readings,
            reception_groups=reception_groups,
            mutual_receptions=mutual_receptions,
        )
        question_sections = self._build_blueprint_question_sections(
            natal_chart=natal_chart,
            planet_profiles=planet_profiles,
            role_title=role_title,
            chart_ruler_line=chart_ruler_line,
            chart_ruler_profile=chart_ruler_profile,
            house_map=house_map,
            pattern_readings=pattern_readings,
            pressure_points=pressure_points,
            career_blueprint=career_blueprint,
        )

        return {
            "role_title": role_title,
            "summary": self._build_blueprint_summary(
                role_title=role_title,
                chart_ruler_label=chart_ruler_label,
                chart_ruler_profile=chart_ruler_profile,
                dominant_labels=dominant_labels,
                houses=houses,
                is_historical_sample=is_historical_sample,
            ),
            "signature": natal_chart.get("signature"),
            "keywords": role_keywords,
            "key_signals": self._build_blueprint_key_signals(
                role_title=role_title,
                chart_ruler_line=chart_ruler_line,
                chart_ruler_profile=chart_ruler_profile,
                top_house=top_house,
                second_house=second_house,
                pressure_points=pressure_points,
                hidden_line=line_12["line"] if line_12 else None,
            ),
            "self_profile": self_profile,
            "career_blueprint": career_blueprint,
            "theory_basis": theory_basis,
            "question_sections": question_sections,
            "layers": [
                {
                    "key": "structure",
                    "title": "结构层",
                    "headline": f"{natal_chart['ascendant']['sign_label']}上升 · {chart_ruler_label}命主",
                    "summary": structure_summary,
                    "evidence": structure_evidence,
                    "focus_cards": structure_focus_cards,
                    "points": structure_points,
                },
                {
                    "key": "power",
                    "title": "权力层",
                    "headline": "资源、关系与控制如何运作",
                    "summary": power_summary,
                    "evidence": power_evidence,
                    "focus_cards": power_focus_cards,
                    "points": power_points,
                },
                {
                    "key": "role",
                    "title": "角色层",
                    "headline": role_title,
                    "summary": role_summary,
                    "evidence": role_evidence,
                    "focus_cards": role_focus_cards,
                    "points": role_points,
                },
                {
                    "key": "cost",
                    "title": "代价层",
                    "headline": "能力的反噬点与收束方式",
                    "summary": cost_summary,
                    "evidence": cost_evidence,
                    "focus_cards": cost_focus_cards,
                    "points": cost_points,
                },
            ],
        }

    def _build_blueprint_summary(
        self,
        role_title: str,
        chart_ruler_label: str,
        chart_ruler_profile: Optional[Dict[str, Any]],
        dominant_labels: str,
        houses: list[Dict[str, Any]],
        is_historical_sample: bool,
    ) -> str:
        if is_historical_sample:
            return (
                f"这不是一张只讲性格的盘，而是一张把{dominant_labels}、"
                f"{self._format_house_titles(houses[:3])}和“{role_title}”绑成同一套人生运作方式的蓝图。"
            )

        ruler_part = (
            f"{chart_ruler_label}落在第{chart_ruler_profile['house']}宫 {chart_ruler_profile['house_title']}"
            if chart_ruler_profile
            else f"{chart_ruler_label}主导全盘"
        )
        house_part = self._format_house_titles(houses[:3]) if houses else "关键宫位"
        return (
            f"本命蓝图不只看性格，而是看{ruler_part}之后，"
            f"你如何通过{house_part}这些核心场景，把自己活成“{role_title}”。"
        )

    def _build_blueprint_key_signals(
        self,
        role_title: str,
        chart_ruler_line: str,
        chart_ruler_profile: Optional[Dict[str, Any]],
        top_house: Optional[Dict[str, Any]],
        second_house: Optional[Dict[str, Any]],
        pressure_points: list[Dict[str, Any]],
        hidden_line: Optional[str],
    ) -> list[Dict[str, str]]:
        signals = [
            self._blueprint_focus_card(
                label="命主入口",
                value=chart_ruler_line,
                hint=chart_ruler_profile["reason"] if chart_ruler_profile else "命主星决定人生如何起手。",
            ),
            self._blueprint_focus_card(
                label="第一杠杆",
                value=f"第{top_house['house']}宫 {top_house['title']}" if top_house else "关键宫位",
                hint=HOUSE_ADULT_MEANINGS.get(top_house["house"], {}).get("adult") if top_house else "最容易做成长期结构的入口。",
            ),
            self._blueprint_focus_card(
                label="角色定位",
                value=role_title,
                hint="这不是性格测试结果，而是命盘在社会中的运作身份。",
            ),
            self._blueprint_focus_card(
                label="主要代价",
                value=pressure_points[0]["label"] if pressure_points else (hidden_line or "待识别"),
                hint=(
                    pressure_points[0]["reason"]
                    if pressure_points
                    else (hidden_line or "最强能力背后的延迟成本。")
                ),
            ),
        ]

        if second_house:
            signals.insert(
                2,
                self._blueprint_focus_card(
                    label="第二杠杆",
                    value=f"第{second_house['house']}宫 {second_house['title']}",
                    hint=HOUSE_ADULT_MEANINGS.get(second_house["house"], {}).get("adult", second_house["title"]),
                ),
            )
        return signals

    def _sign_archetype_by_value(self, sign_value: Optional[str]) -> Dict[str, Any]:
        try:
            return SIGN_ARCHETYPES.get(Sign(sign_value or ""), {})
        except Exception:
            return {}

    def _aspect_balance_text(
        self,
        profile: Optional[Dict[str, Any]],
        include_example: bool = True,
    ) -> str:
        if not profile:
            return "相位信息待识别。"

        supportive = float(profile.get("supportive_aspects", 0.0))
        challenging = float(profile.get("challenging_aspects", 0.0))
        if supportive > challenging + 0.35:
            text = "相位支持偏多，这股力量更容易顺着结构稳定发挥。"
        elif challenging > supportive + 0.35:
            text = "相位拉扯偏重，这股力量往往要通过摩擦、压力或补课才能成熟。"
        else:
            text = "相位支持与压力并存，这股力量不是单线顺推，而是边调边走。"

        signatures = list(profile.get("aspect_signature", []))
        if include_example and signatures:
            text += f" 代表性联动是{signatures[0]}。"
        return text

    def _planet_pain_point_text(
        self,
        profile: Optional[Dict[str, Any]],
        concise: bool = False,
    ) -> str:
        if not profile:
            return "痛点层面待识别。"

        house_adult = HOUSE_ADULT_MEANINGS.get(profile["house"], {}).get("adult", profile["house_title"])
        shadow = profile.get("shadow", "这条线容易失衡")
        supportive = float(profile.get("supportive_aspects", 0.0))
        challenging = float(profile.get("challenging_aspects", 0.0))
        dignity = profile.get("dignity")
        retrograde = bool(profile.get("retrograde"))

        if challenging > supportive + 0.35:
            state_text = "这颗星受克偏重，问题通常不是想太多，而是会在现实里反复撞墙。"
        elif dignity in {"detriment", "fall"}:
            state_text = "这颗星先天吃力，容易在关键时候怀疑自己、绕路推进，或者靠代价换结果。"
        elif retrograde:
            state_text = "这颗星的力量来得慢，很多课题不是没有，而是常常后知后觉或需要更长时间消化。"
        else:
            state_text = "即使这颗星整体能用，失衡时也会先从最熟悉的惯性里漏水。"

        if concise:
            return f"痛点层面，{shadow}最容易在{house_adult}这类场景里发作。{state_text}"

        return f"痛点层面，{shadow}最容易在{house_adult}这类现实场景里发作。{state_text}"

    def _planet_cross_reading(
        self,
        profile: Optional[Dict[str, Any]],
        emphasis: str,
        concise: bool = False,
    ) -> str:
        if not profile:
            return "核心星体待识别。"

        sign_profile = self._sign_archetype_by_value(profile.get("sign"))
        house_adult = HOUSE_ADULT_MEANINGS.get(profile["house"], {}).get("adult", profile["house_title"])
        sign_style = sign_profile.get("work_style") or sign_profile.get("persona") or profile["sign_label"]
        dignity_text = self._dignity_flow_text(profile["dignity"])
        aspect_text = self._aspect_balance_text(profile, include_example=not concise)

        lead_map = {
            "chart_ruler": "命主星决定你的人生起手方式",
            "sun": "太阳决定你要成为什么样的人",
            "moon": "月亮决定你如何安放安全感与情绪需求",
            "mercury": "水星决定你如何认知、表达与定位自己",
            "venus": "金星决定你如何展示价值、吸引关系并交换资源",
            "mars": "火星决定你如何行动、争取与执行目标",
            "jupiter": "木星决定你如何扩张自己、相信机会并打开格局",
            "saturn": "土星决定你如何承受压力、磨炼现实能力并建立结构",
            "dominant": "这颗主导行星决定你最容易被世界放大的标签",
        }
        lead = lead_map.get(emphasis, "这颗星体决定一条重要人格线")

        if concise:
            return (
                f"{lead}：先天看{profile['label']}的{profile['gift']}，"
                f"落在{profile['sign_label']}会更偏向{sign_style}，"
                f"落入第{profile['house']}宫 {profile['house_title']}后，重点会放到{house_adult}；"
                f"{self._aspect_balance_text(profile, include_example=False)}"
                f" {self._planet_pain_point_text(profile, concise=True)}"
            )

        return (
            f"{lead}：先天星性上，{profile['label']}主{profile['gift']}，"
            f"先天状态为{profile['dignity_label']}，{dignity_text}"
            f" 落在{profile['sign_label']}时，会更偏向{sign_style}；"
            f"落入第{profile['house']}宫 {profile['house_title']}后，这股力量会主要运作在{house_adult}。"
            f" {aspect_text}"
            f" {self._planet_pain_point_text(profile)}"
        )

    def _career_path_cross_reading(
        self,
        profile: Dict[str, Any],
        context_house: int,
        context_house_title: str,
        planet_symbol: Dict[str, Any],
        sign_symbol: Dict[str, Any],
        house_symbol: Dict[str, Any],
        group: Optional[Dict[str, Any]],
        reception: Optional[Dict[str, Any]],
        mutual: Optional[Dict[str, Any]],
        late_five_note: Optional[str],
    ) -> Dict[str, Any]:
        sign_style = sign_symbol.get("work_style") or sign_symbol.get("persona") or profile["sign_label"]
        house_adult = HOUSE_ADULT_MEANINGS.get(context_house, {}).get("adult", context_house_title)
        dignity_text = self._dignity_flow_text(profile["dignity"])
        aspect_text = self._aspect_balance_text(profile)
        risk_text = self._profile_operating_risk(profile, context_house, domain="career")
        group_topics = self._format_house_number_list(group.get("house_titles", [])) if group else ""

        if reception:
            if reception.get("receiver") == profile["planet"].value:
                reception_text = (
                    f"接纳结构上，{reception['line']}，说明这条职业线不只是顾自己，"
                    f"还会把其他议题一并托举到第{reception['receiver_house']}宫 {reception['receiver_house_title']}去运作。"
                )
            else:
                reception_text = (
                    f"接纳结构上，{reception['line']}，说明这条职业线容易被外部资源、贵人线或更强的系统托举。"
                )
        else:
            reception_text = "接纳结构不算突出，这条路更依赖你自己把能力做成稳定方法。"

        mutual_text = (
            f"互溶结构上，{mutual['line']}，说明这条职业母题会和另一条核心路径互相借力。"
            if mutual
            else "互溶结构不明显，职业推进主要靠这条线自身的稳定度。"
        )
        group_text = (
            f"宫主链上，{group['line']}，会把{group_topics or '多条宫位'}一起带进职业主题。"
            if group
            else "宫主链以这颗星的实际落点为主，职业主题会直接跟着它当前所在场景走。"
        )
        late_text = (
            f"飞宫判断里额外考虑末5°原则：{late_five_note}"
            if late_five_note
            else "飞宫判断没有触发末5°修正，按常规落宫与飞宫场景理解。"
        )

        summary = (
            f"先天星性上，{profile['label']}主{planet_symbol.get('theme', '核心能力')}，"
            f"本身带着{profile.get('gift', '可被职业化的天赋')}这类职业天赋；"
            f"先天状态为{profile['dignity_label']}，{dignity_text}"
            f" 落在{profile['sign_label']}后，职业表达会更偏向{sign_style}；"
            f"按后天宫性，这股力量会主要落到第{context_house}宫 {context_house_title}，"
            f"也就是{house_adult}这类现实场景里显形。"
            f" 但真正把这条线做成职业结果时，{risk_text}"
        )

        theory = self._unique_strings(
            [
                f"先天星性：{profile['label']}主{planet_symbol.get('theme', '核心能力')}，核心天赋是{profile.get('gift', '职业能力')}。",
                f"星体状态：{profile['dignity_label']}。{dignity_text}",
                f"落座风格：{profile['sign_label']}会把这条职业路推向{sign_style}。",
                f"后天宫性：第{context_house}宫 {context_house_title}对应{house_adult}，这是职业最容易落地的现实场景。",
                f"相位结构：{aspect_text}",
                group_text,
                reception_text,
                mutual_text,
                late_text,
                f"风险与代价：{risk_text}",
            ]
        )

        points = self._unique_strings(
            [
                f"职业判定：这条线更接近“{house_symbol.get('path_title', context_house_title)}”这类职业母题。",
                f"这条职业线的底层不是单一岗位，而是“{planet_symbol.get('theme', '核心能力')} × {profile['sign_label']} × 第{context_house}宫 {context_house_title}”的组合。",
                f"从先天星性看，你靠{planet_symbol.get('theme', '核心能力')}与{profile.get('gift', '职业天赋')}吃饭。",
                f"从落座看，这条路更适合用{sign_style}的方式推进，而不是完全照搬别人的职业模板。",
                f"从后天宫性看，这条路最终要落到{house_adult}这类场景里，职业成就也会在那里被看见。",
                f"相位层面，{aspect_text}",
                f"把这条路做成长期职业时，最容易失手的位置是：{risk_text}",
                reception_text,
                mutual_text,
            ]
        )

        return {
            "summary": summary,
            "theory": theory,
            "points": points,
            "group_text": group_text,
            "reception_text": reception_text,
            "mutual_text": mutual_text,
            "late_text": late_text,
            "aspect_text": aspect_text,
            "risk_text": risk_text,
        }

    def _build_self_profile(
        self,
        natal_chart: Dict[str, Any],
        planet_profiles: Dict[Planet, Dict[str, Any]],
        role_title: str,
        chart_ruler_line: str,
        chart_ruler_profile: Optional[Dict[str, Any]],
        house_map: Dict[int, Dict[str, Any]],
        pattern_readings: list[Dict[str, Any]],
        pressure_points: list[Dict[str, Any]],
    ) -> Dict[str, Any]:
        ascendant = natal_chart.get("ascendant", {})
        asc_sign_label = ascendant.get("sign_label") or ascendant.get("sign") or "上升"
        asc_profile = {}
        try:
            asc_profile = SIGN_ARCHETYPES.get(Sign(ascendant.get("sign", "")), {})
        except Exception:
            asc_profile = {}

        sun_profile = planet_profiles.get(Planet.SUN)
        moon_profile = planet_profiles.get(Planet.MOON)
        mercury_profile = planet_profiles.get(Planet.MERCURY)
        venus_profile = planet_profiles.get(Planet.VENUS)
        mars_profile = planet_profiles.get(Planet.MARS)
        jupiter_profile = planet_profiles.get(Planet.JUPITER)
        saturn_profile = planet_profiles.get(Planet.SATURN)
        dominant = natal_chart.get("dominant_planets", [])
        houses = natal_chart.get("house_emphasis", [])
        aspects = natal_chart.get("major_aspects", [])
        top_aspect = aspects[0]["title"] if aspects else None
        bright_spot = dominant[0] if dominant else None
        chart_ruler_value = natal_chart.get("chart_ruler")
        line_2 = house_map.get(2)
        line_7 = house_map.get(7)
        line_10 = house_map.get(10)
        resource_line = line_7["line"] if line_7 else (line_2["line"] if line_2 else (line_10["line"] if line_10 else chart_ruler_line))
        bright_spot_profile = (
            self._planet_profile_by_value(planet_profiles, bright_spot.get("planet"))
            if bright_spot and bright_spot.get("planet")
            else None
        )
        hidden_line = house_map.get(12)
        pain_focus = pressure_points[0] if pressure_points else None
        secondary_pain_focus = pressure_points[1] if len(pressure_points) > 1 else None

        baseline = (
            f"你的本命基调更像“{role_title}”。别人先接收到的，是{asc_sign_label}式的"
            f"{asc_profile.get('persona', '社会化外显')}；但真正的角色分析，要回到星体的先天星性、"
            f"落座方式、落宫场景与相位结构一起看。"
            f" 命主星这条线说明你是怎么起手的：{self._planet_cross_reading(chart_ruler_profile, 'chart_ruler', concise=True)}"
            f" 太阳说明你想成为什么样的人：{self._planet_cross_reading(sun_profile, 'sun', concise=True)}"
            f" 月亮说明你怎样才会真的舒服稳定：{self._planet_cross_reading(moon_profile, 'moon', concise=True)}"
            f" 水星、金星、火星则会继续把你的认知表达、价值吸引和行动执行做实；"
            f" 木星和土星则决定你扩张人生、承担现实与长期磨炼自己的方式。"
            f" 真正的卡点通常不在优点本身，而在{pain_focus['label'] if pain_focus else '那颗最弱又最容易被反复触发的星'}，"
            f"以及{hidden_line['line'] if hidden_line else '12宫隐线'}这种台面下的反噬方式。"
            if chart_ruler_profile and sun_profile and moon_profile
            else f"你的本命基调更像“{role_title}”，角色分析要先看命主星的先天星性，再把太阳、月亮的落座落宫与相位一起合并判断。"
        )

        cards = [
            self._blueprint_focus_card(
                label="用户角色",
                value=role_title,
                hint="角色判断会综合星体先天星性、落座、落宫与相位，不是单一标签。",
            ),
            self._blueprint_focus_card(
                label="命主入口",
                value=(
                    chart_ruler_line
                    if chart_ruler_profile
                    else "命主星主线待识别"
                ),
                hint=(
                    self._planet_cross_reading(chart_ruler_profile, "chart_ruler", concise=True)
                    if chart_ruler_profile
                    else "命主星决定你的人生如何起手。"
                ),
            ),
            self._blueprint_focus_card(
                label="太阳驱力",
                value=(
                    f"{sun_profile['label']}落第{sun_profile['house']}宫 {sun_profile['house_title']}"
                    if sun_profile
                    else "太阳主线待识别"
                ),
                hint=(
                    self._planet_cross_reading(sun_profile, "sun", concise=True)
                    if sun_profile
                    else "太阳负责你想成为什么样的人，以及你愿意在哪个领域承担责任。"
                ),
            ),
            self._blueprint_focus_card(
                label="月亮需求",
                value=(
                    f"{moon_profile['label']}落第{moon_profile['house']}宫 {moon_profile['house_title']}"
                    if moon_profile
                    else "月亮主线待识别"
                ),
                hint=(
                    self._planet_cross_reading(moon_profile, "moon", concise=True)
                    if moon_profile
                    else "月亮决定你的安全感、情绪节奏和最真实的内在需求。"
                ),
            ),
            self._blueprint_focus_card(
                label="水星认知",
                value=(
                    f"{mercury_profile['label']}落第{mercury_profile['house']}宫 {mercury_profile['house_title']}"
                    if mercury_profile
                    else "水星主线待识别"
                ),
                hint=(
                    self._planet_cross_reading(mercury_profile, "mercury", concise=True)
                    if mercury_profile
                    else "水星决定你的认知模式、表达方式和学习路径。"
                ),
            ),
            self._blueprint_focus_card(
                label="金星价值",
                value=(
                    f"{venus_profile['label']}落第{venus_profile['house']}宫 {venus_profile['house_title']}"
                    if venus_profile
                    else "金星主线待识别"
                ),
                hint=(
                    self._planet_cross_reading(venus_profile, "venus", concise=True)
                    if venus_profile
                    else "金星决定你的价值表达、吸引力与关系交换模式。"
                ),
            ),
            self._blueprint_focus_card(
                label="火星行动",
                value=(
                    f"{mars_profile['label']}落第{mars_profile['house']}宫 {mars_profile['house_title']}"
                    if mars_profile
                    else "火星主线待识别"
                ),
                hint=(
                    self._planet_cross_reading(mars_profile, "mars", concise=True)
                    if mars_profile
                    else "火星决定你的行动力、争取方式和执行节奏。"
                ),
            ),
            self._blueprint_focus_card(
                label="木星信念",
                value=(
                    f"{jupiter_profile['label']}落第{jupiter_profile['house']}宫 {jupiter_profile['house_title']}"
                    if jupiter_profile
                    else "木星主线待识别"
                ),
                hint=(
                    self._planet_cross_reading(jupiter_profile, "jupiter", concise=True)
                    if jupiter_profile
                    else "木星决定你的信念、扩张方式和机会感。"
                ),
            ),
            self._blueprint_focus_card(
                label="土星课题",
                value=(
                    f"{saturn_profile['label']}落第{saturn_profile['house']}宫 {saturn_profile['house_title']}"
                    if saturn_profile
                    else "土星主线待识别"
                ),
                hint=(
                    self._planet_cross_reading(saturn_profile, "saturn", concise=True)
                    if saturn_profile
                    else "土星决定你的现实课题、压力来源和长期磨炼方向。"
                ),
            ),
            self._blueprint_focus_card(
                label="长期主轴",
                value=self._format_house_titles(houses[:3]),
                hint="这些宫位代表后天宫性最重的现实场景，会反复塑造你的人生主线。",
            ),
            self._blueprint_focus_card(
                label="资源入口",
                value=resource_line,
                hint="看资源从哪里来，通常要同时看命主线、财路线和合作入口。",
            ),
            self._blueprint_focus_card(
                label="第一痛点",
                value=pain_focus["label"] if pain_focus else "待识别",
                hint=(
                    pain_focus["reason"]
                    if pain_focus
                    else "最容易反复卡住你、让你觉得自己明明有能力却总在关键处失手的位置。"
                ),
            ),
        ]

        if secondary_pain_focus:
            cards.append(
                self._blueprint_focus_card(
                    label="第二痛点",
                    value=secondary_pain_focus["label"],
                    hint=secondary_pain_focus["reason"],
                )
            )

        if bright_spot and bright_spot.get("planet") != chart_ruler_value:
            cards.insert(
                4,
                self._blueprint_focus_card(
                    label="发光点",
                    value=bright_spot["label"],
                    hint=(
                        self._planet_cross_reading(bright_spot_profile, "dominant", concise=True)
                        if bright_spot_profile
                        else bright_spot.get("reason", "这颗星是你最容易被放大的长板。")
                    ),
                ),
            )

        evidence = self._unique_strings(
            [
                f"{asc_sign_label}上升",
                chart_ruler_line,
                chart_ruler_profile["aspect_signature"][0] if chart_ruler_profile and chart_ruler_profile.get("aspect_signature") else None,
                sun_profile["aspect_signature"][0] if sun_profile and sun_profile.get("aspect_signature") else None,
                moon_profile["aspect_signature"][0] if moon_profile and moon_profile.get("aspect_signature") else None,
                mercury_profile["aspect_signature"][0] if mercury_profile and mercury_profile.get("aspect_signature") else None,
                venus_profile["aspect_signature"][0] if venus_profile and venus_profile.get("aspect_signature") else None,
                mars_profile["aspect_signature"][0] if mars_profile and mars_profile.get("aspect_signature") else None,
                jupiter_profile["aspect_signature"][0] if jupiter_profile and jupiter_profile.get("aspect_signature") else None,
                saturn_profile["aspect_signature"][0] if saturn_profile and saturn_profile.get("aspect_signature") else None,
                top_aspect,
                line_10["line"] if line_10 else None,
                pain_focus["label"] if pain_focus else None,
                pain_focus["reason"] if pain_focus else None,
                pattern_readings[0]["title"] if pattern_readings else None,
            ]
        )

        points = [
            (
                f"{asc_sign_label}上升让你在社会化层面先表现出"
                f"{asc_profile.get('persona', '一套稳定的人格面具')}，别人通常先看到这一层。"
            ),
            self._planet_cross_reading(chart_ruler_profile, "chart_ruler")
            if chart_ruler_profile
            else "命主星决定你是靠什么能力起手，这条线比抽象性格更重要。",
            self._planet_cross_reading(sun_profile, "sun")
            if sun_profile
            else "太阳决定你要在哪个领域发光，不能只看表面人设。",
            self._planet_cross_reading(moon_profile, "moon")
            if moon_profile
            else "月亮决定你是否真的舒服、稳定，以及亲密关系里的真实需求。",
            self._planet_cross_reading(mercury_profile, "mercury")
            if mercury_profile
            else "水星决定你的认知、表达和学习路径。",
            self._planet_cross_reading(venus_profile, "venus")
            if venus_profile
            else "金星决定你的价值感、吸引模式和关系交换方式。",
            self._planet_cross_reading(mars_profile, "mars")
            if mars_profile
            else "火星决定你的行动、争取方式和执行节奏。",
            self._planet_cross_reading(jupiter_profile, "jupiter")
            if jupiter_profile
            else "木星决定你的扩张方式、信念感和人生机会入口。",
            self._planet_cross_reading(saturn_profile, "saturn")
            if saturn_profile
            else "土星决定你的现实课题、压力来源和长期成熟方向。",
            (
                self._planet_cross_reading(bright_spot_profile, "dominant")
                if bright_spot_profile and bright_spot and bright_spot.get("planet") != chart_ruler_value
                else f"命主星{natal_chart.get('chart_ruler_label', '命主星')}会成为你最容易被放大的个人标签。"
            ),
            (
                f"命盘不能只看单颗星，还要兼顾相位网络。当前显眼相位包括“{top_aspect}”，"
                "说明你的角色形成不是单线推进，而是几条核心人格线彼此联动。"
                if top_aspect
                else "相位网络决定一颗星是顺流、拧巴还是混合推进，不能跳过不看。"
            ),
            (
                f"真正最容易卡住你的，不一定是你最在意的优点，而往往是{pain_focus['label']}这条线：{pain_focus['reason']}"
                if pain_focus
                else "真正的痛点通常藏在那颗最弱、最容易被现实反复触发的星体上。"
            ),
            (
                f"第二层痛点是{secondary_pain_focus['label']}：{secondary_pain_focus['reason']}"
                if secondary_pain_focus
                else "如果只有一个明显痛点，就先把第一处失衡修稳，不要同时到处补课。"
            ),
            (
                f"12宫主链是“{hidden_line['line']}”，所以很多痛感不会第一时间爆炸，而是以拖延、隐耗、关系回收、情绪积压或幕后成本的方式慢慢出现。"
                if hidden_line
                else "真正的痛点通常还有一层隐线代价，不能只看台面上的表现。"
            ),
            (
                f"长期主轴落在{self._format_house_titles(houses[:3])}，说明你不是随机活着，而是会不断回到这些议题里做出结构。"
                if houses
                else "长期主轴要看重点宫位如何反复出现，它们比短期状态更能定义人生。"
            ),
            (
                f"资源入口沿着“{resource_line}”打开，说明你拿结果的方式不只靠努力本身，还要看合作、变现和公开线如何配合。"
                if resource_line
                else "资源入口要结合命主线、合作线和变现线一起看。"
            ),
            (
                f"真正要警惕的是{chart_ruler_profile['shadow']}，所以最稳的策略不是靠蛮力，而是{chart_ruler_profile['strategy']}"
                if chart_ruler_profile
                else "本命盘的长板一旦失衡，就容易从最熟悉的地方反噬回来。"
            ),
        ]

        return {
            "title": "先认识你自己",
            "summary": "本命蓝图先回答“你是谁”。这里会先看命主星，再看日月水金火木土各自的先天星性、落座、落宫和相位，最后把这些力量合成你的人格基调、发光点、资源入口，以及反复卡住你的痛点和代价。",
            "baseline": baseline,
            "cards": cards,
            "evidence": evidence,
            "points": points,
        }

    def _build_career_blueprint(
        self,
        natal_chart: Dict[str, Any],
        planet_profiles: Dict[Planet, Dict[str, Any]],
        role_title: str,
        house_map: Dict[int, Dict[str, Any]],
        ruler_groups: Dict[str, Dict[str, Any]],
        reception_groups: list[Dict[str, Any]],
        mutual_receptions: list[Dict[str, Any]],
    ) -> Dict[str, Any]:
        candidates: Dict[tuple[str, int], Dict[str, Any]] = {}
        chart_ruler_value = natal_chart.get("chart_ruler")
        career_ruler_value = house_map.get(10, {}).get("ruler")

        def add_candidate(planet_value: Optional[str], source: str, evidence: list[str], weight: float) -> None:
            if not planet_value:
                return
            profile = self._planet_profile_by_value(planet_profiles, planet_value)
            if not profile:
                return

            group = ruler_groups.get(planet_value)
            context_house = int(group["ruler_house"]) if group else int(profile["house"])
            context_house_title = group["ruler_house_title"] if group else profile["house_title"]
            late_five_note = group.get("late_five_note") if group else None
            key = (planet_value, context_house)
            item = candidates.setdefault(
                key,
                {
                    "planet": planet_value,
                    "house": context_house,
                    "house_title": context_house_title,
                    "actual_house": profile["house"],
                    "actual_house_title": profile["house_title"],
                    "weight": 0.0,
                    "sources": [],
                    "evidence": [],
                    "late_five_note": late_five_note,
                },
            )
            item["weight"] += weight
            item["sources"].append(source)
            item["evidence"].extend(evidence)
        if chart_ruler_value:
            add_candidate(chart_ruler_value, "命主星主线", [f"命主星 {natal_chart.get('chart_ruler_label', '命主星')}"], 1.5)

        for house, source, weight in (
            (10, "10宫事业线", 1.6),
            (2, "2宫变现线", 0.8),
            (6, "6宫技能线", 0.8),
            (7, "7宫合作线", 0.9),
            (11, "11宫社群线", 0.9),
        ):
            line = house_map.get(house)
            if line:
                add_candidate(line["ruler"], source, [line["line"]], weight)

        for item in natal_chart.get("dominant_planets", [])[:3]:
            add_candidate(item.get("planet"), "主导行星", [item.get("reason", "")], 1.1)

        for item in natal_chart.get("house_emphasis", [])[:3]:
            line = house_map.get(item["house"])
            if line:
                add_candidate(line["ruler"], f"重点宫位第{item['house']}宫", [line["line"]], 0.9)

        path_cards: list[Dict[str, Any]] = []
        for item in sorted(candidates.values(), key=lambda value: value["weight"], reverse=True):
            profile = self._planet_profile_by_value(planet_profiles, item["planet"])
            if not profile:
                continue

            try:
                planet = Planet(item["planet"])
            except Exception:
                continue

            try:
                sign = Sign(profile["sign"])
            except Exception:
                continue

            context_house = int(item.get("house", profile["house"]))
            context_house_title = item.get("house_title") or profile["house_title"]
            planet_symbol = PLANET_CAREER_SYMBOLS.get(planet, {"theme": "核心能力", "roles": []})
            sign_symbol = SIGN_ARCHETYPES.get(sign, {"persona": "职业表达", "work_style": "需要放回现实场景判断", "career_tags": []})
            house_symbol = HOUSE_CAREER_SYMBOLS.get(context_house, {"path_title": context_house_title, "roles": []})
            group = ruler_groups.get(item["planet"])
            reception = next(
                (
                    entry
                    for entry in reception_groups
                    if entry.get("receiver") == item["planet"]
                    or any(guest.get("planet") == item["planet"] for guest in entry.get("guests", []))
                ),
                None,
            )
            mutual = next(
                (
                    entry
                    for entry in mutual_receptions
                    if item["planet"] in entry.get("pair", [])
                ),
                None,
            )

            roles = self._unique_strings(
                [
                    *house_symbol.get("roles", []),
                    *planet_symbol.get("roles", []),
                    *sign_symbol.get("career_tags", []),
                ]
            )
            aspect_delta = float(profile.get("supportive_aspects", 0.0)) - float(profile.get("challenging_aspects", 0.0))
            aspect_bonus = clamp(aspect_delta * 0.18, -0.35, 0.35)
            reception_bonus = 0.22 if reception else 0.0
            mutual_bonus = 0.3 if mutual else 0.0
            ruler_bonus = 0.12 if group and len(group.get("houses", [])) > 1 else 0.0
            fit_score = round(float(profile["score"]) + float(item["weight"]) + aspect_bonus + reception_bonus + mutual_bonus + ruler_bonus, 2)
            fit_label = self._career_fit_label(fit_score)
            track_decision = self._classify_career_track(
                planet_value=item["planet"],
                group=group,
                sources=item["sources"],
                chart_ruler_value=chart_ruler_value,
                career_ruler_value=career_ruler_value,
            )
            cross_reading = self._career_path_cross_reading(
                profile=profile,
                context_house=context_house,
                context_house_title=context_house_title,
                planet_symbol=planet_symbol,
                sign_symbol=sign_symbol,
                house_symbol=house_symbol,
                group=group,
                reception=reception,
                mutual=mutual,
                late_five_note=item.get("late_five_note"),
            )
            theory = self._unique_strings(
                [
                    *cross_reading["theory"],
                    f"职业轨道：{track_decision['label']}。{track_decision['reason']}",
                ]
            )
            roles_preview = " / ".join(roles[:4]) if roles else house_symbol.get("path_title", context_house_title)
            reading_points = cross_reading["points"]
            points = self._unique_strings(
                [
                    f"系统判断：这条线属于“{track_decision['label']}”，{track_decision['reason']} 它更像“{house_symbol.get('path_title', context_house_title)}”这类职业母题。",
                    *reading_points[1:7],
                    f"可以优先试{roles_preview}这类方向，但不要只看你会不会做，更要看你愿不愿长期承担这条线的代价。",
                    f"这条路的优势在于{profile.get('gift', planet_symbol.get('theme', '核心能力'))}；真正要管住的是{profile.get('shadow', '只靠惯性推进')}，否则很容易在第{context_house}宫 {context_house_title}的场景里自己把路做窄。",
                ]
            )

            path_cards.append(
                {
                    "key": f"{item['planet']}-{context_house}",
                    "title": f"{house_symbol.get('path_title', context_house_title)} · {profile['label']}式路线",
                    "fit_score": fit_score,
                    "fit_label": fit_label,
                    "track_label": track_decision["label"],
                    "track_reason": track_decision["reason"],
                    "track_priority": track_decision["priority"],
                    "summary": cross_reading["summary"],
                    "risk_summary": cross_reading["risk_text"],
                    "sources": self._unique_strings(item["sources"]),
                    "roles": roles[:14],
                    "selection_tags": roles[:10],
                    "evidence": self._unique_strings(item["evidence"] + theory)[:10],
                    "theory": theory,
                    "points": points[:8],
                }
            )

        path_cards.sort(key=lambda item: (item.get("track_priority", 9), -item["fit_score"]))

        return {
            "title": "职业路线",
            "summary": f"对“{role_title}”这类盘，职业路线不只看你适合做什么，还要看每条路靠什么成、最容易因为什么失手。系统会先看星体先天星性与先天状态，再看落座如何表达、落宫如何落地，最后用相位、宫主星飞宫、末5°原则、接纳和互溶判断这条路是主职业、资源线还是副轨。",
            "selection_prompt": "系统已经按主职业、资源线、合作线和副轨直接排好优先级。优先看最前面的主职业路径，但不要只看匹配度，也要看你是否愿意承担这条路对应的压力、卡点和收尾成本。",
            "method_tags": ["先天星性", "星座表达", "后天宫性", "宫主星飞宫", "末5°原则", "相位", "接纳", "互溶"],
            "paths": path_cards,
        }

    def _build_blueprint_theory_basis(
        self,
        natal_chart: Dict[str, Any],
        chart_ruler_line: str,
        house_map: Dict[int, Dict[str, Any]],
        pattern_readings: list[Dict[str, Any]],
        reception_groups: list[Dict[str, Any]],
        mutual_receptions: list[Dict[str, Any]],
    ) -> Dict[str, Any]:
        aspects = natal_chart.get("major_aspects", [])
        top_aspect = aspects[0]["title"] if aspects else None
        line_2 = house_map.get(2)
        line_7 = house_map.get(7)
        line_10 = house_map.get(10)
        line_12 = house_map.get(12)
        first_pattern = pattern_readings[0] if pattern_readings else None
        first_reception = reception_groups[0]["line"] if reception_groups else None
        first_mutual = mutual_receptions[0]["line"] if mutual_receptions else None

        points = self._unique_strings(
            [
                f"先看命主星如何起手：{chart_ruler_line}",
                "本命性格与角色分析默认先看星体先天星性，再看落座风格、落宫场景，最后用相位结构校验这股力量是顺流、拉扯还是混合推进。",
                "职业路线分析沿用同一套顺序：先看星体先天星性与先天状态，再看星座表达、后天宫性，最后叠加飞宫、末5°、相位、接纳与互溶来定主副路径。",
                "再看太阳的主观意志、月亮的安全需求如何把人格做实。",
                "职业与性格判断都先以星体落星座、落宫位为主，不先做空泛标签。",
                f"宫主星飞宫用来判断事情最后落到哪个现实场景：{line_10['line']}" if line_10 else None,
                "宫主星飞宫默认额外考虑末5°原则：行星如果贴近下一宫宫头，会按下一宫论飞宫结果。",
                f"资源与合作入口继续校验：{line_7['line']}" if line_7 else (f"资源变现入口继续校验：{line_2['line']}" if line_2 else None),
                f"隐藏代价与收尾机制看第12宫：{line_12['line']}" if line_12 else None,
                f"关键相位用于判断顺手还是拉扯：{top_aspect}" if top_aspect else None,
                f"宫位结构规则锚点：{first_pattern['title']} - {first_pattern['summary']}" if first_pattern else None,
                f"接纳说明哪颗星在托举哪条线：{first_reception}" if first_reception else None,
                f"互溶说明两条线彼此借力：{first_mutual}" if first_mutual else None,
            ]
        )

        return {
            "title": "理论依据区",
            "summary": "所有判断优先看星体落在什么星座、什么宫位，再用宫主星飞宫、相位、互溶和接纳去验证这条线是顺手放大，还是带着代价运作。",
            "chips": ["星体", "星座", "宫位", "宫主星飞宫", "末5°飞宫", "相位", "互溶接纳", "转宫"],
            "points": points,
        }

    def _build_blueprint_question_sections(
        self,
        natal_chart: Dict[str, Any],
        planet_profiles: Dict[Planet, Dict[str, Any]],
        role_title: str,
        chart_ruler_line: str,
        chart_ruler_profile: Optional[Dict[str, Any]],
        house_map: Dict[int, Dict[str, Any]],
        pattern_readings: list[Dict[str, Any]],
        pressure_points: list[Dict[str, Any]],
        career_blueprint: Dict[str, Any],
    ) -> list[Dict[str, Any]]:
        sections: list[Dict[str, Any]] = []
        houses = natal_chart.get("house_emphasis", [])
        aspects = natal_chart.get("major_aspects", [])
        top_aspect = aspects[0]["title"] if aspects else None
        line_2 = house_map.get(2)
        line_3 = house_map.get(3)
        line_5 = house_map.get(5)
        line_7 = house_map.get(7)
        line_8 = house_map.get(8)
        line_9 = house_map.get(9)
        line_10 = house_map.get(10)
        line_11 = house_map.get(11)
        line_12 = house_map.get(12)

        sun_profile = planet_profiles.get(Planet.SUN)
        moon_profile = planet_profiles.get(Planet.MOON)
        mercury_profile = planet_profiles.get(Planet.MERCURY)
        venus_profile = planet_profiles.get(Planet.VENUS)
        jupiter_profile = planet_profiles.get(Planet.JUPITER)

        wealth_pattern = next(
            (item for item in pattern_readings if item.get("key") == "wealth_pattern"),
            None,
        )
        career_pattern = next(
            (item for item in pattern_readings if item.get("key") == "career_pattern"),
            None,
        )
        alliance_pattern = next(
            (item for item in pattern_readings if item.get("key") in {"alliance_axis", "partner_profile"}),
            None,
        )

        sections.append(
            self._blueprint_question_section(
                key="identity",
                question="我是什么样的人",
                answer=self._identity_answer(
                    role_title=role_title,
                    chart_ruler_profile=chart_ruler_profile,
                    houses=houses,
                    sun_profile=sun_profile,
                    moon_profile=moon_profile,
                    top_aspect=top_aspect,
                ),
                takeaways=self._unique_strings(
                    [
                        self._identity_takeaway(chart_ruler_profile, chart_ruler_line),
                        self._sun_takeaway(sun_profile),
                        self._moon_takeaway(moon_profile),
                    ]
                )[:3],
                risks=self._question_risks(
                    [
                        self._pain_focus_line(pressure_points[0]) if pressure_points else None,
                        f"显眼相位“{top_aspect}”说明你的人生不会只走单线，几股力量很容易互相牵动。" if top_aspect else None,
                    ]
                ),
                actions=self._unique_strings(
                    [
                        chart_ruler_profile.get("strategy") if chart_ruler_profile else None,
                        self._identity_action(chart_ruler_profile, houses),
                    ]
                )[:2],
                evidence=self._unique_strings(
                    [
                        role_title,
                        chart_ruler_line,
                        top_aspect,
                        f"重点宫位 {self._format_house_titles(houses[:3])}" if houses else None,
                    ]
                )[:5],
            )
        )

        career_paths = list(career_blueprint.get("paths", []))
        top_career = career_paths[0] if career_paths else None
        sections.append(
            self._blueprint_question_section(
                key="fit",
                question="我适合做什么事情",
                answer=self._fit_answer(top_career, chart_ruler_profile, line_10, line_11),
                takeaways=self._unique_strings(
                    [
                        self._fit_takeaway(top_career),
                        top_career.get("track_reason") if top_career else None,
                        self._second_path_takeaway(career_paths[1]) if len(career_paths) > 1 else None,
                    ]
                )[:3],
                risks=self._question_risks(
                    [
                        top_career.get("risk_summary") if top_career else None,
                        "不要只看自己会不会做，更要看这条路的节奏、压力和收尾成本你能不能长期扛住。",
                    ]
                ),
                actions=self._unique_strings(
                    [
                        self._fit_action(top_career, line_10, line_11),
                        self._line_action(line_11, "资源放大"),
                    ]
                )[:2],
                evidence=self._unique_strings(
                    [
                        top_career["title"] if top_career else None,
                        top_career["track_label"] if top_career else None,
                        line_10["line"] if line_10 else None,
                        line_11["line"] if line_11 else None,
                    ]
                )[:5],
            )
        )

        sections.append(
            self._blueprint_question_section(
                key="study",
                question="我的学业怎么样",
                answer=self._study_answer(mercury_profile, line_3, line_9),
                takeaways=self._unique_strings(
                    [
                        self._study_takeaway(mercury_profile),
                        self._house_line_takeaway(line_3, "学习和表达"),
                        self._house_line_takeaway(line_9, "高阶学习和认知升级"),
                    ]
                )[:3],
                risks=self._question_risks(
                    [
                        self._study_risk(mercury_profile),
                        "这类盘最怕的不是学不会，而是前期吸收很快、后期沉淀不够，最后变成知道很多、留下很少。",
                    ]
                ),
                actions=self._unique_strings(
                    [
                        mercury_profile.get("strategy") if mercury_profile else None,
                        self._study_action(mercury_profile, line_3, line_9),
                    ]
                )[:2],
                evidence=self._unique_strings(
                    [
                        line_3["line"] if line_3 else None,
                        line_9["line"] if line_9 else None,
                        mercury_profile["aspect_signature"][0] if mercury_profile and mercury_profile.get("aspect_signature") else None,
                    ]
                )[:5],
            )
        )

        sections.append(
            self._blueprint_question_section(
                key="career",
                question="我的事业怎么样",
                answer=self._career_answer(career_pattern, line_10, line_11),
                takeaways=self._unique_strings(
                    [
                        self._career_takeaway(career_pattern, 0),
                        self._career_takeaway(career_pattern, 1),
                        self._house_line_takeaway(line_3, "表达、传播和信息处理"),
                    ]
                )[:3],
                risks=self._question_risks(
                    [
                        career_pattern.get("risk_summary") if career_pattern else None,
                        f"12宫主链路是“{line_12['line']}”，说明事业里还夹带幕后消耗、延迟回收或后期清算成本。" if line_12 else None,
                    ]
                ),
                actions=self._unique_strings(
                    [
                        self._career_action(line_10, career_pattern),
                        self._line_action(line_11, "事业放大"),
                    ]
                )[:2],
                evidence=self._unique_strings(
                    [
                        line_10["line"] if line_10 else None,
                        line_11["line"] if line_11 else None,
                        career_pattern["evidence"][0] if career_pattern and career_pattern.get("evidence") else None,
                    ]
                )[:5],
            )
        )

        sections.append(
            self._blueprint_question_section(
                key="wealth",
                question="我的财富怎么样",
                answer=self._wealth_answer(wealth_pattern, line_2, line_5, line_8, line_11),
                takeaways=self._unique_strings(
                    [
                        self._wealth_takeaway(wealth_pattern, 0),
                        self._wealth_takeaway(wealth_pattern, 3),
                        self._house_line_takeaway(line_5, "偏财、创作和高波动收益"),
                    ]
                )[:3],
                risks=self._question_risks(
                    [
                        wealth_pattern.get("risk_summary") if wealth_pattern else None,
                        f"8宫主链路是“{line_8['line']}”，共享资源、分成、债务和绑定代价绝对不能忽视。" if line_8 else None,
                    ]
                ),
                actions=self._unique_strings(
                    [
                        self._wealth_action(line_2, line_5, line_8, line_11),
                        self._line_action(line_8, "合作、分成、投资和借力的钱"),
                    ]
                )[:2],
                evidence=self._unique_strings(
                    [
                        wealth_pattern["evidence"][0] if wealth_pattern and wealth_pattern.get("evidence") else None,
                        line_8["line"] if line_8 else None,
                        line_11["line"] if line_11 else None,
                    ]
                )[:5],
            )
        )

        relationship_answer = "感情和伴侣要看7宫，不只是看桃花多不多，而是看你会通过什么样的人进入更大的关系、合作和资源系统。"
        if alliance_pattern:
            relationship_answer = self._relationship_answer(alliance_pattern, line_7, line_12, venus_profile, line_5)
        sections.append(
            self._blueprint_question_section(
                key="relationship",
                question="我的桃花和伴侣怎么样",
                answer=relationship_answer,
                takeaways=self._unique_strings(
                    [
                        self._relationship_takeaway(alliance_pattern, 0),
                        self._relationship_takeaway(alliance_pattern, 1),
                        self._relationship_venus_takeaway(venus_profile),
                    ]
                )[:3],
                risks=self._question_risks(
                    [
                        self._relationship_risk(venus_profile),
                        f"12宫主链路是“{line_12['line']}”，关系里要防隐线、拖延、回收成本和看不见的外部变量。" if line_12 else None,
                    ]
                ),
                actions=self._unique_strings(
                    [
                        venus_profile.get("strategy") if venus_profile else None,
                        self._relationship_action(venus_profile, line_7, line_5),
                    ]
                )[:2],
                evidence=self._unique_strings(
                    [
                        line_7["line"] if line_7 else None,
                        line_12["line"] if line_12 else None,
                        jupiter_profile["aspect_signature"][0] if jupiter_profile and jupiter_profile.get("aspect_signature") else None,
                    ]
                )[:5],
            )
        )

        return sections

    def _blueprint_question_section(
        self,
        key: str,
        question: str,
        answer: str,
        takeaways: list[str],
        risks: list[str],
        actions: list[str],
        evidence: list[str],
    ) -> Dict[str, Any]:
        return {
            "key": key,
            "question": question,
            "answer": answer,
            "takeaways": takeaways[:3],
            "risks": risks[:2],
            "actions": actions[:2],
            "evidence": evidence[:6],
        }

    def _question_risks(self, values: Iterable[Optional[str]]) -> list[str]:
        return self._unique_strings([item for item in values if item])[:2]

    def _profile_placement_line(self, profile: Optional[Dict[str, Any]]) -> Optional[str]:
        if not profile:
            return None
        return (
            f"{profile['label']}落{profile['sign_label']}第{profile['house']}宫（{profile['house_title']}），"
            f"先天状态是{profile['dignity_label']}"
        )

    def _profile_reality_field(self, profile: Optional[Dict[str, Any]]) -> Optional[str]:
        if not profile:
            return None
        return HOUSE_ADULT_MEANINGS.get(profile["house"], {}).get("adult", profile["house_title"])

    def _line_reality_text(self, line: Optional[Dict[str, Any]], topic: str) -> Optional[str]:
        if not line:
            return None
        return (
            f"{topic}会顺着“{line['line']}”落到第{line['ruler_house']}宫 "
            f"{line['ruler_house_title']}，不是抽象判断。"
        )

    def _line_action(self, line: Optional[Dict[str, Any]], topic: str) -> Optional[str]:
        if not line:
            return None
        house_adult = HOUSE_ADULT_MEANINGS.get(line["ruler_house"], {}).get("adult", line["ruler_house_title"])
        return (
            f"{topic}不要泛泛用力，优先经营第{line['ruler_house']}宫 {line['ruler_house_title']}对应的"
            f"{house_adult}，因为“{line['line']}”说明结果会从这里打开。"
        )

    def _identity_action(
        self,
        chart_ruler_profile: Optional[Dict[str, Any]],
        houses: list[Dict[str, Any]],
    ) -> Optional[str]:
        if chart_ruler_profile:
            field = self._profile_reality_field(chart_ruler_profile)
            return f"先把{field}做成稳定标签，再向外扩张；你的命主星不适合脱离这个现实场景空谈定位。"
        if houses:
            return f"先围绕{self._format_house_titles(houses[:2])}建立可被看见的成果，再判断自己适合什么身份。"
        return None

    def _fit_action(
        self,
        top_career: Optional[Dict[str, Any]],
        line_10: Optional[Dict[str, Any]],
        line_11: Optional[Dict[str, Any]],
    ) -> Optional[str]:
        if top_career:
            track = top_career.get("track_label") or top_career.get("fit_label") or "主职业"
            return f"先用“{top_career['title']}”作为{track}测试三到六个月，看它是否真的带来作品、位置或资源，而不是只停留在兴趣。"
        return self._line_action(line_10 or line_11, "职业选择")

    def _study_action(
        self,
        mercury_profile: Optional[Dict[str, Any]],
        line_3: Optional[Dict[str, Any]],
        line_9: Optional[Dict[str, Any]],
    ) -> Optional[str]:
        if mercury_profile:
            field = self._profile_reality_field(mercury_profile)
            return f"学习上不要只堆输入，要把{mercury_profile['gift']}落到{field}，用证书、作品、课程、论文或内容输出验证。"
        return self._line_action(line_3 or line_9, "学习")

    def _career_action(
        self,
        line_10: Optional[Dict[str, Any]],
        career_pattern: Optional[Dict[str, Any]],
    ) -> Optional[str]:
        if line_10:
            house_adult = HOUSE_ADULT_MEANINGS.get(line_10["ruler_house"], {}).get("adult", line_10["ruler_house_title"])
            return f"事业上先把第{line_10['ruler_house']}宫 {line_10['ruler_house_title']}对应的{house_adult}做出结果，再去争取更大的头衔和位置。"
        if career_pattern:
            return career_pattern.get("points", [None])[0]
        return None

    def _wealth_action(
        self,
        line_2: Optional[Dict[str, Any]],
        line_5: Optional[Dict[str, Any]],
        line_8: Optional[Dict[str, Any]],
        line_11: Optional[Dict[str, Any]],
    ) -> Optional[str]:
        if line_2:
            return self._line_action(line_2, "正财和现金流")
        if line_8:
            return self._line_action(line_8, "合伙资金和风险筹码")
        if line_11:
            return self._line_action(line_11, "平台型财富")
        if line_5:
            return self._line_action(line_5, "偏财和创作收益")
        return None

    def _relationship_action(
        self,
        venus_profile: Optional[Dict[str, Any]],
        line_7: Optional[Dict[str, Any]],
        line_5: Optional[Dict[str, Any]],
    ) -> Optional[str]:
        if line_7:
            return self._line_action(line_7, "伴侣、客户、合作和契约关系")
        if venus_profile:
            return f"关系里先看对方能不能承接{self._profile_reality_field(venus_profile)}，不要只被一时吸引力带着走。"
        return self._line_action(line_5, "桃花和恋爱感")

    def _identity_answer(
        self,
        role_title: str,
        chart_ruler_profile: Optional[Dict[str, Any]],
        houses: list[Dict[str, Any]],
        sun_profile: Optional[Dict[str, Any]] = None,
        moon_profile: Optional[Dict[str, Any]] = None,
        top_aspect: Optional[str] = None,
    ) -> str:
        parts: list[str] = [f"你不是泛泛的“某一类人”，这张盘更像“{role_title}”。"]
        placement = self._profile_placement_line(chart_ruler_profile)
        if placement and chart_ruler_profile:
            parts.append(
                f"核心差异在命主星：{placement}，你起手靠的是{chart_ruler_profile['gift']}，"
                f"现实里会优先在{self._profile_reality_field(chart_ruler_profile)}这类场景被看见。"
            )
        if sun_profile:
            parts.append(
                f"太阳线显示你想成为的人，重心会落在{self._profile_reality_field(sun_profile)}；"
                f"这和别人只看太阳星座得出的结论会不一样。"
            )
        if moon_profile:
            parts.append(
                f"月亮线则说明真正让你稳定下来的，是{self._profile_reality_field(moon_profile)}，"
                "所以你的情绪和安全感不能脱离这个现实场景去谈。"
            )
        if houses:
            parts.append(f"重点宫位集中在{self._format_house_titles(houses[:3])}，这些才是你反复成事、也反复被考验的地方。")
        if top_aspect:
            parts.append(f"再加上显眼相位“{top_aspect}”，你的性格不会是单线条，而是几股力量同时拉扯后形成的结果。")
        return "".join(parts[:5])

    def _fit_answer(
        self,
        top_career: Optional[Dict[str, Any]],
        chart_ruler_profile: Optional[Dict[str, Any]],
        line_10: Optional[Dict[str, Any]],
        line_11: Optional[Dict[str, Any]],
    ) -> str:
        if top_career:
            track = top_career.get("track_label") or top_career.get("fit_label") or "优先路径"
            score = top_career.get("fit_score")
            score_text = f"，匹配度约{score:.1f}" if isinstance(score, (int, float)) else ""
            reasons = self._unique_strings(
                [
                    f"命主星落点给你的起手能力是{chart_ruler_profile['gift']}" if chart_ruler_profile else None,
                    self._line_reality_text(line_10, "事业线"),
                    self._line_reality_text(line_11, "平台与人脉线"),
                    top_career.get("track_reason"),
                ]
            )
            return (
                f"更适合优先经营“{top_career['title']}”这条线，属于“{track}”{score_text}。"
                f"原因不是模板推荐，而是{'；'.join(reasons[:3])}。"
            )
        if chart_ruler_profile and line_10:
            return (
                f"你适合做那些能把{chart_ruler_profile['gift']}真正落到{line_10['ruler_house_title']}这类现实场景里的事，"
                "而不是只追一阵子的热度。"
            )
        if line_11:
            return f"你适合做那些能借平台、社群、合作或网络被持续放大的事。"
        return "你适合做那些能让命主线、事业线和资源线一起发力的事，而不是只追短期热度。"

    def _study_answer(
        self,
        mercury_profile: Optional[Dict[str, Any]],
        line_3: Optional[Dict[str, Any]],
        line_9: Optional[Dict[str, Any]],
    ) -> str:
        if mercury_profile:
            parts = [
                f"学业首先看水星：{self._profile_placement_line(mercury_profile)}，"
                f"所以你的学习方式不是通用模板，而是要把{mercury_profile['gift']}练成稳定输出。"
            ]
            if line_3:
                parts.append(self._line_reality_text(line_3, "基础学习、表达和技能线") or "")
            if line_9:
                parts.append(self._line_reality_text(line_9, "高阶学习、学历和认知升级线") or "")
            parts.append("成绩好不好，关键不只在努力，而在于能不能把理解、表达和作品沉淀接起来。")
            return "".join(item for item in parts if item)
        return "你的学业不能只看考试那一下，更要看学习力、理解力和表达力，能不能被长期做成结果。"

    def _career_answer(
        self,
        career_pattern: Optional[Dict[str, Any]],
        line_10: Optional[Dict[str, Any]],
        line_11: Optional[Dict[str, Any]],
    ) -> str:
        parts: list[str] = []
        if career_pattern:
            parts.append(career_pattern.get("summary") or "你的事业不是做不出来，关键不在蛮冲，而在于方法是不是走对了路。")
        if line_10:
            parts.append(self._line_reality_text(line_10, "事业、头衔和公开位置") or "")
        if line_11:
            parts.append(self._line_reality_text(line_11, "平台、团队和资源网络") or "")
        if parts:
            return "".join(item for item in parts if item)
        if line_10 and line_11:
            return (
                f"你的事业不是没有格局，关键在于能不能沿着“{line_10['line']}”把位置先做出来，"
                f"再通过“{line_11['line']}”把影响力和结果放大。"
            )
        return "事业能不能做出来，关键看10宫主怎么落地，以及你愿不愿意长期经营这条职业主轴。"

    def _wealth_answer(
        self,
        wealth_pattern: Optional[Dict[str, Any]],
        line_2: Optional[Dict[str, Any]],
        line_5: Optional[Dict[str, Any]],
        line_8: Optional[Dict[str, Any]],
        line_11: Optional[Dict[str, Any]],
    ) -> str:
        parts: list[str] = []
        if wealth_pattern:
            parts.append(wealth_pattern.get("summary") or "你有挣钱能力，但钱能不能留下，和钱从哪里来同样重要。")
        if line_2:
            parts.append(self._line_reality_text(line_2, "正财、现金流和可支配资源") or "")
        if line_5:
            parts.append(self._line_reality_text(line_5, "偏财、创作和高波动收益") or "")
        if line_8:
            parts.append(self._line_reality_text(line_8, "合伙资金、分成和风险筹码") or "")
        if line_11:
            parts.append(self._line_reality_text(line_11, "平台、人脉和众财池") or "")
        if parts:
            return "".join(item for item in parts[:4] if item)
        if line_8 and line_11:
            return (
                "你的财路不太像单靠一份固定收入慢慢累积，更像会被平台资源、合作关系和共享利益一起牵动。"
            )
        return "财运不能只看会不会挣钱，还要一起看钱从哪里来、靠什么放大、又会从哪里漏掉。"

    def _relationship_answer(
        self,
        alliance_pattern: Dict[str, Any],
        line_7: Optional[Dict[str, Any]],
        line_12: Optional[Dict[str, Any]],
        venus_profile: Optional[Dict[str, Any]] = None,
        line_5: Optional[Dict[str, Any]] = None,
    ) -> str:
        parts: list[str] = []
        summary = alliance_pattern.get("summary")
        if summary:
            parts.append(summary)
        if line_7:
            parts.append(self._line_reality_text(line_7, "伴侣、客户、合作和契约关系") or "")
        if venus_profile:
            parts.append(
                f"金星这条吸引力线是{self._profile_placement_line(venus_profile)}，"
                f"你在关系里真正会被触动的，是{self._profile_reality_field(venus_profile)}。"
            )
        if line_5:
            parts.append(self._line_reality_text(line_5, "桃花、恋爱感和短期心动") or "")
        if line_12:
            parts.append("同时要看12宫隐线，关系里有没有拖延、暗线、消耗和回收成本，不能只看当下甜不甜。")
        if parts:
            return "".join(parts[:4])
        return "感情和伴侣要看7宫，不只是看桃花多不多，而是看你会通过什么样的人进入更大的关系、合作和资源系统。"

    def _identity_takeaway(
        self,
        chart_ruler_profile: Optional[Dict[str, Any]],
        chart_ruler_line: str,
    ) -> Optional[str]:
        if not chart_ruler_profile:
            return chart_ruler_line
        return (
            f"你的命主线是“{chart_ruler_line}”，说明你的人生起手真正靠的是"
            f"{chart_ruler_profile['gift']}，不是靠空泛概念。"
        )

    def _sun_takeaway(self, sun_profile: Optional[Dict[str, Any]]) -> Optional[str]:
        if not sun_profile:
            return None
        return (
            f"太阳落在第{sun_profile['house']}宫 {sun_profile['house_title']}，"
            f"你真正想成的人，会把重心放在{HOUSE_ADULT_MEANINGS.get(sun_profile['house'], {}).get('adult', sun_profile['house_title'])}。"
        )

    def _moon_takeaway(self, moon_profile: Optional[Dict[str, Any]]) -> Optional[str]:
        if not moon_profile:
            return None
        return (
            f"月亮落在第{moon_profile['house']}宫 {moon_profile['house_title']}，"
            f"你的安全感不是抽象的，而是要在{HOUSE_ADULT_MEANINGS.get(moon_profile['house'], {}).get('adult', moon_profile['house_title'])}里被安放。"
        )

    def _fit_takeaway(self, top_career: Optional[Dict[str, Any]]) -> Optional[str]:
        if not top_career:
            return None
        return (
            f"眼下最值得优先经营的职业方向，是“{top_career['track_label'] or top_career['fit_label']}”里的"
            f"“{top_career['title']}”。"
        )

    def _second_path_takeaway(self, path: Optional[Dict[str, Any]]) -> Optional[str]:
        if not path:
            return None
        return f"第二顺位可以看“{path['title']}”，它更像补充线或放大线，不一定要一开始就当成第一主轴。"

    def _study_takeaway(self, mercury_profile: Optional[Dict[str, Any]]) -> Optional[str]:
        if not mercury_profile:
            return None
        return (
            f"水星落在第{mercury_profile['house']}宫 {mercury_profile['house_title']}，"
            f"说明你最该练的不是死记，而是把{mercury_profile['gift']}变成稳定输出。"
        )

    def _study_risk(self, mercury_profile: Optional[Dict[str, Any]]) -> Optional[str]:
        if not mercury_profile:
            return None
        return (
            f"学业上真正要防的不是不聪明，而是{mercury_profile['shadow']}，"
            f"尤其在{HOUSE_ADULT_MEANINGS.get(mercury_profile['house'], {}).get('adult', mercury_profile['house_title'])}这类场景里最容易失手。"
        )

    def _career_takeaway(
        self,
        career_pattern: Optional[Dict[str, Any]],
        index: int,
    ) -> Optional[str]:
        if not career_pattern:
            return None
        points = career_pattern.get("points", [])
        if len(points) <= index:
            return None
        return points[index]

    def _wealth_takeaway(
        self,
        wealth_pattern: Optional[Dict[str, Any]],
        index: int,
    ) -> Optional[str]:
        if not wealth_pattern:
            return None
        points = wealth_pattern.get("points", [])
        if len(points) <= index:
            return None
        return points[index]

    def _relationship_takeaway(
        self,
        alliance_pattern: Optional[Dict[str, Any]],
        index: int,
    ) -> Optional[str]:
        if not alliance_pattern:
            return None
        points = alliance_pattern.get("points", [])
        if len(points) <= index:
            return None
        return points[index]

    def _relationship_venus_takeaway(self, venus_profile: Optional[Dict[str, Any]]) -> Optional[str]:
        if not venus_profile:
            return None
        return (
            f"金星落在第{venus_profile['house']}宫 {venus_profile['house_title']}，"
            f"你在感情里真正在意的，不只是心动，而是这段关系有没有现实承接力。"
        )

    def _relationship_risk(self, venus_profile: Optional[Dict[str, Any]]) -> Optional[str]:
        if not venus_profile:
            return None
        return (
            f"感情里最要防的是{venus_profile['shadow']}，"
            f"一失衡就容易把关系做成彼此消耗，而不是互相托举。"
        )

    def _house_line_takeaway(self, line: Optional[Dict[str, Any]], topic: str) -> Optional[str]:
        if not line:
            return None
        return f"{line['line']}说明你的{topic}，最后会通过第{line['ruler_house']}宫 {line['ruler_house_title']}这种场景落地。"

    def _pain_focus_line(self, point: Dict[str, Any]) -> Optional[str]:
        label = point.get("label")
        reason = point.get("reason")
        if label and reason:
            return f"你最容易卡住的点在{label}：{reason}"
        return reason or label

    def _classify_career_track(
        self,
        planet_value: str,
        group: Optional[Dict[str, Any]],
        sources: list[str],
        chart_ruler_value: Optional[str],
        career_ruler_value: Optional[str],
    ) -> Dict[str, Any]:
        houses = set(group.get("houses", [])) if group else set()
        source_text = " / ".join(sources)
        is_chart_ruler = bool(chart_ruler_value and planet_value == chart_ruler_value)
        is_career_ruler = bool(career_ruler_value and planet_value == career_ruler_value) or 10 in houses or ("10宫事业线" in source_text)
        is_money_ruler = 2 in houses or ("2宫变现线" in source_text)
        is_partner_ruler = 7 in houses or ("7宫合作线" in source_text)
        is_network_ruler = 11 in houses or ("11宫社群线" in source_text)
        is_skill_ruler = 6 in houses or ("6宫技能线" in source_text)

        if is_chart_ruler and is_career_ruler:
            return {
                "label": "核心主职业",
                "reason": "它同时连着命主星和10宫主，个人能力、职业身份与社会抬头会绑在同一条主轴上。",
                "priority": 0,
            }
        if is_career_ruler:
            return {
                "label": "主职业路径",
                "reason": "它直接由10宫主带出，社会角色、职业成果和公开位置最容易沿这条线显形。",
                "priority": 1,
            }
        if is_chart_ruler:
            return {
                "label": "主职业路径",
                "reason": "它由命主星直接带出，会和你的长期投入、身份认同与核心能力绑得最紧。",
                "priority": 2,
            }
        if is_money_ruler and (is_partner_ruler or is_network_ruler):
            return {
                "label": "资源放大线",
                "reason": "这条线更负责把钱、合作和人脉资源接进来，适合做收入补充、资源整合或商业放大。",
                "priority": 3,
            }
        if is_money_ruler:
            return {
                "label": "资源变现线",
                "reason": "这条线优先承担变现、现金流和资源调度，更像赚钱方式，而不一定是职业身份本身。",
                "priority": 4,
            }
        if is_partner_ruler or is_network_ruler:
            return {
                "label": "合作副轨",
                "reason": "这条线更依赖合作、客户、社群或外部平台来放大，适合做联盟、副业或关系型机会入口。",
                "priority": 5,
            }
        if is_skill_ruler:
            return {
                "label": "技能副轨",
                "reason": "这条线更像技能、执行或服务能力的延展方向，适合做职业补位和长期积累。",
                "priority": 6,
            }
        return {
            "label": "潜能副轨",
            "reason": "这条线能发展，但更像补充路径、兴趣延展或阶段性转向，不是最优先的职业主轴。",
            "priority": 7,
        }

    def _career_fit_label(self, fit_score: float) -> str:
        if fit_score >= 3.6:
            return "主线候选"
        if fit_score >= 2.4:
            return "重点尝试"
        return "可作副轨"

    def _blueprint_focus_card(self, label: str, value: str, hint: Optional[str] = None) -> Dict[str, str]:
        return {
            "label": label,
            "value": value,
            "hint": hint or "",
        }

    def _build_timeline_validation(
        self,
        birth_time_iso: str,
        birth_time_local: datetime,
        lat: float,
        lon: float,
        periods_data: list[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        if not self._is_huang_jinrong_sample(birth_time_iso, lat, lon):
            return None

        event_specs = [
            {
                "date": "1873-07-01T12:00:00",
                "date_label": "1873年",
                "title": "举家迁往上海",
                "category": "家庭迁移",
                "validation": "家庭、迁移与生存感成为早年主轴，适合用月亮主题来校验早期命运塑形。",
            },
            {
                "date": "1892-07-01T12:00:00",
                "date_label": "1892年",
                "title": "考入法租界巡捕房",
                "category": "进入制度平台",
                "validation": "通过关系、制度入口与更大的平台完成上升，正是这张盘最典型的扩张方式。",
            },
            {
                "date": "1924-07-01T12:00:00",
                "date_label": "1924年",
                "title": "升任督察长",
                "category": "公开地位抬升",
                "validation": "这一步不只是职位变化，而是社会可见度、资源调动权与公共身份同步抬升。",
            },
            {
                "date": "1927-04-12T12:00:00",
                "date_label": "1927年4月12日",
                "title": "参与四一二政变",
                "category": "组织与口径合流",
                "validation": "真正危险的地方不是单纯暴力，而是名单、口径、组织调度与政治站队合流。",
            },
            {
                "date": "1951-05-20T12:00:00",
                "date_label": "1951年5月20日",
                "title": "发表自白并扫街改造",
                "category": "晚年清算",
                "validation": "旧有结构进入回收期，幕后权力被公众评价和新秩序反向处理，代价层彻底显形。",
            },
        ]

        events: list[Dict[str, Any]] = []
        for spec in event_specs:
            event_dt = datetime.fromisoformat(spec["date"])
            age = (event_dt - birth_time_local).days / 365.2422
            period = self._find_period_for_age(periods_data, age)
            if not period:
                continue

            phase_range = f"{int(period['timing']['start_age'])}-{int(period['timing']['end_age'])}岁"
            lords = (
                f"{planet_label(period['lords']['major'])}/"
                f"{planet_label(period['lords']['sub']) if period['lords']['sub'] else '无'}"
            )
            events.append(
                {
                    "date_label": spec["date_label"],
                    "title": spec["title"],
                    "category": spec["category"],
                    "age_label": f"{int(age)}岁左右",
                    "phase_title": period["title"],
                    "phase_range": phase_range,
                    "phase_lords": lords,
                    "phase_summary": period["summary"],
                    "validation": spec["validation"],
                    "reading": (
                        f"对应阶段是{period['title']}，重心落在{period['astrology']['house_title']}，"
                        f"这和“{spec['category']}”形成了直接映射。"
                    ),
                }
            )

        return {
            "mode": "historical_validation",
            "title": "人生节点校验",
            "summary": "这个案例不看“你现在在哪一段”，而是用已知人生事件反推命盘结构和阶段逻辑是否成立。",
            "events": events,
        }

    def _build_advanced_patterns(
        self,
        birth_time_iso: str,
        lat: float,
        lon: float,
        natal_chart: Dict[str, Any],
        planet_profiles: Dict[Planet, Dict[str, Any]],
        aspect_cache: Dict[Planet, list[Dict[str, Any]]],
    ) -> Dict[str, Any]:
        house_rulers = self._build_house_ruler_map(natal_chart, planet_profiles)
        ruler_groups = self._build_ruler_groups(house_rulers, planet_profiles)
        core_threads = self._build_core_threads(house_rulers)
        reception_groups = self._build_reception_groups(planet_profiles, aspect_cache)
        mutual_receptions = self._build_mutual_receptions(planet_profiles)
        derived_houses = self._build_derived_house_profiles(house_rulers)
        pattern_readings = self._build_pattern_readings(
            house_rulers=house_rulers,
            ruler_groups=ruler_groups,
            reception_groups=reception_groups,
            mutual_receptions=mutual_receptions,
            derived_houses=derived_houses,
            planet_profiles=planet_profiles,
        )
        case_themes: list[Dict[str, Any]] = []

        if self._is_huang_jinrong_sample(birth_time_iso, lat, lon):
            case_themes = self._build_huang_jinrong_case_themes(
                natal_chart=natal_chart,
                planet_profiles=planet_profiles,
                house_rulers=house_rulers,
                ruler_groups=ruler_groups,
                reception_groups=reception_groups,
                derived_houses=derived_houses,
            )

        return {
            "summary": "把几宫主飞几宫、同一行星统领哪些宫位，先拆成规则层，再进入现实语言解释。",
            "house_rulers": house_rulers,
            "ruler_groups": ruler_groups,
            "reception_groups": reception_groups,
            "mutual_receptions": mutual_receptions,
            "derived_houses": derived_houses,
            "core_threads": core_threads,
            "pattern_readings": pattern_readings,
            "case_themes": case_themes,
        }

    def _build_house_ruler_map(
        self,
        natal_chart: Dict[str, Any],
        planet_profiles: Dict[Planet, Dict[str, Any]],
    ) -> list[Dict[str, Any]]:
        houses = natal_chart.get("houses", [])
        planets_payload = natal_chart.get("planets", {})
        results: list[Dict[str, Any]] = []

        for item in houses:
            try:
                sign = Sign(item["sign"])
                ruler = SIGN_RULERS[sign]
            except Exception:
                continue

            profile = planet_profiles.get(ruler)
            if not profile:
                continue

            planet_payload = planets_payload.get(ruler.value, {})
            ruler_longitude = float(
                planet_payload.get(
                    "longitude",
                    self._longitude_from_sign(profile["sign"], profile["degree"]),
                )
            )
            effective_house = self._effective_house_for_flying(houses, ruler_longitude)
            effective_house_number = effective_house["house"]
            effective_house_title = HOUSE_TOPICS.get(effective_house_number, {}).get(
                "title",
                f"第{effective_house_number}宫",
            )
            late_five_note = None
            if effective_house["late_five_applied"]:
                late_five_note = (
                    f"{planet_label(ruler)}实际落第{profile['house']}宫 {profile['house_title']}，"
                    f"距离下一宫宫头 {effective_house['distance_to_next_cusp']:.2f}°，"
                    f"按末5°原则视作飞入第{effective_house_number}宫 {effective_house_title}。"
                )
            flight_catalog = self._flight_catalog_note(
                source_house=item["house"],
                target_house=effective_house_number,
                profile=profile,
            )

            line = f"{item['house']}R {planet_label(ruler)}飞{effective_house_number}宫"
            if effective_house["late_five_applied"]:
                line += "（按末5°）"

            results.append(
                {
                    "house": item["house"],
                    "title": item["title"],
                    "sign": item["sign"],
                    "sign_label": item.get("sign_label") or sign_label(sign),
                    "ruler": ruler.value,
                    "ruler_label": planet_label(ruler),
                    "ruler_house": effective_house_number,
                    "ruler_house_title": effective_house_title,
                    "ruler_house_actual": profile["house"],
                    "ruler_house_actual_title": profile["house_title"],
                    "ruler_sign": profile["sign"],
                    "ruler_sign_label": profile["sign_label"],
                    "dignity": profile["dignity"],
                    "dignity_label": profile["dignity_label"],
                    "adult_meaning": HOUSE_ADULT_MEANINGS.get(item["house"], {}).get("adult", item["title"]),
                    "notation": f"{item['house']}R",
                    "line": line,
                    "late_five_applied": effective_house["late_five_applied"],
                    "late_five_distance": round(effective_house["distance_to_next_cusp"], 3),
                    "late_five_note": late_five_note,
                    "flight_summary": flight_catalog["summary"] if flight_catalog else None,
                    "flight_positive": flight_catalog["positive"] if flight_catalog else None,
                    "flight_negative": flight_catalog["negative"] if flight_catalog else None,
                    "flight_tone": flight_catalog["tone"] if flight_catalog else None,
                    "flight_tone_label": flight_catalog["tone_label"] if flight_catalog else None,
                    "flight_note": flight_catalog["note"] if flight_catalog else None,
                    "flight_target_title": flight_catalog["title"] if flight_catalog else None,
                    "flight_target_theme": flight_catalog["theme"] if flight_catalog else None,
                }
            )
        return results

    def _effective_house_for_flying(
        self,
        houses: list[Dict[str, Any]],
        longitude: float,
        threshold: float = LATE_FIVE_HOUSE_ORB,
    ) -> Dict[str, Any]:
        if not houses:
            return {
                "house": 0,
                "actual_house": 0,
                "next_house": 0,
                "distance_to_next_cusp": 999.0,
                "late_five_applied": False,
            }

        cusps: list[float] = []
        previous = -1.0
        for item in houses[:12]:
            cusp_longitude = self._longitude_from_sign(item["sign"], item["degree"])
            while cusp_longitude <= previous:
                cusp_longitude += 360.0
            cusps.append(cusp_longitude)
            previous = cusp_longitude

        target = longitude % 360.0
        while target < cusps[0]:
            target += 360.0

        for index, start in enumerate(cusps):
            end = cusps[index + 1] if index < len(cusps) - 1 else cusps[0] + 360.0
            if start <= target < end:
                actual_house = index + 1
                next_house = 1 if actual_house == 12 else actual_house + 1
                distance_to_next = end - target
                late_five_applied = distance_to_next <= threshold
                return {
                    "house": next_house if late_five_applied else actual_house,
                    "actual_house": actual_house,
                    "next_house": next_house,
                    "distance_to_next_cusp": distance_to_next,
                    "late_five_applied": late_five_applied,
                }

        return {
            "house": 12,
            "actual_house": 12,
            "next_house": 1,
            "distance_to_next_cusp": 999.0,
            "late_five_applied": False,
        }

    def _flight_catalog_tone(self, profile: Optional[Dict[str, Any]]) -> str:
        if not profile:
            return "mixed"

        supportive = float(profile.get("supportive_aspects", 0.0))
        challenging = float(profile.get("challenging_aspects", 0.0))
        dignity = profile.get("dignity")
        retrograde = bool(profile.get("retrograde"))

        if challenging > supportive + 0.35 or dignity in {"detriment", "fall"}:
            return "challenged"
        if supportive > challenging + 0.15 and dignity in {"domicile", "exaltation"} and not retrograde:
            return "supported"
        return "mixed"

    def _flight_catalog_note(
        self,
        source_house: int,
        target_house: int,
        profile: Optional[Dict[str, Any]],
    ) -> Optional[Dict[str, str]]:
        entry = get_house_ruler_flight_entry(source_house, target_house)
        if not entry:
            return None

        tone = self._flight_catalog_tone(profile)
        if tone == "supported":
            tone_label = "更偏得吉"
            interpretation = entry["positive"]
        elif tone == "challenged":
            tone_label = "更偏受克"
            interpretation = entry["negative"]
        else:
            tone_label = "吉凶混合"
            interpretation = f"顺手时：{entry['positive']} 失衡时：{entry['negative']}"

        return {
            "title": entry["target_title"],
            "theme": entry["target_theme"],
            "summary": entry["summary"],
            "positive": entry["positive"],
            "negative": entry["negative"],
            "tone": tone,
            "tone_label": tone_label,
            "note": (
                f"{source_house}R飞{target_house}宫在这套飞星表里的底色是“{entry['summary']}”。"
                f" 当前这条线{tone_label}：{interpretation}"
            ),
        }

    def _build_ruler_groups(
        self,
        house_rulers: list[Dict[str, Any]],
        planet_profiles: Dict[Planet, Dict[str, Any]],
    ) -> list[Dict[str, Any]]:
        grouped: Dict[str, list[Dict[str, Any]]] = {}
        for item in house_rulers:
            grouped.setdefault(item["ruler"], []).append(item)

        results: list[Dict[str, Any]] = []
        for ruler_value, items in grouped.items():
            items.sort(key=lambda value: value["house"])
            try:
                profile = planet_profiles.get(Planet(ruler_value))
            except Exception:
                profile = None
            if not profile:
                continue

            house_numbers = [item["house"] for item in items]
            notation = "/".join(f"{house}R" for house in house_numbers)
            results.append(
                {
                    "ruler": ruler_value,
                    "ruler_label": items[0]["ruler_label"],
                    "houses": house_numbers,
                    "house_titles": [item["title"] for item in items],
                    "notation": notation,
                    "line": (
                        f"{notation} {items[0]['ruler_label']}飞{items[0]['ruler_house']}宫"
                        + ("（按末5°）" if items[0].get("late_five_applied") else "")
                    ),
                    "ruler_house": items[0]["ruler_house"],
                    "ruler_house_title": items[0]["ruler_house_title"],
                    "ruler_house_actual": items[0].get("ruler_house_actual", profile["house"]),
                    "ruler_house_actual_title": items[0].get("ruler_house_actual_title", profile["house_title"]),
                    "ruler_sign": profile["sign"],
                    "ruler_sign_label": profile["sign_label"],
                    "dignity": profile["dignity"],
                    "dignity_label": profile["dignity_label"],
                    "late_five_applied": bool(items[0].get("late_five_applied")),
                    "late_five_distance": items[0].get("late_five_distance"),
                    "late_five_note": items[0].get("late_five_note"),
                }
            )

        results.sort(key=lambda value: min(value["houses"]) if value["houses"] else 99)
        return results

    def _build_core_threads(self, house_rulers: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
        selected_houses = [1, 2, 3, 7, 10, 12]
        selected_map = {item["house"]: item for item in house_rulers}
        threads: list[Dict[str, Any]] = []

        for house in selected_houses:
            item = selected_map.get(house)
            if not item:
                continue

            threads.append(
                {
                    "house": house,
                    "title": f"{item['notation']} {item['ruler_label']}飞{item['ruler_house']}宫",
                    "summary": (
                        (
                            f"{item['title']}不会停留在抽象层，而会通过{item['ruler_house_title']}显形。"
                            f" 这条飞宫在线下语义里更像“{item['flight_summary']}”。"
                            if item.get("flight_summary")
                            else f"{item['title']}不会停留在抽象层，而会通过{item['ruler_house_title']}显形。"
                        )
                    ),
                    "points": self._unique_strings(
                        [
                            f"{item['title']}的成人社会义是：{item['adult_meaning']}。",
                            f"宫主{item['ruler_label']}落在第{item['ruler_house']}宫 {item['ruler_house_title']}，所以这条线会通过具体场景运作。",
                            f"先天状态为{item['dignity_label']}，这会影响这条线是顺手放大，还是带着代价运作。",
                            item.get("flight_note"),
                        ]
                    ),
                }
            )
        return threads

    def _build_reception_groups(
        self,
        planet_profiles: Dict[Planet, Dict[str, Any]],
        aspect_cache: Dict[Planet, list[Dict[str, Any]]],
    ) -> list[Dict[str, Any]]:
        grouped: Dict[Planet, list[Dict[str, Any]]] = {}

        for planet, profile in planet_profiles.items():
            try:
                guest_sign = Sign(profile["sign"])
                receiver = SIGN_RULERS[guest_sign]
            except Exception:
                continue

            if receiver == planet:
                continue

            if not self._has_reception_link(planet, receiver, planet_profiles, aspect_cache):
                continue

            grouped.setdefault(receiver, []).append(
                {
                    "planet": planet.value,
                    "label": profile["label"],
                    "house": profile["house"],
                    "house_title": profile["house_title"],
                    "sign": profile["sign"],
                    "sign_label": profile["sign_label"],
                }
            )

        results: list[Dict[str, Any]] = []
        for receiver, guests in grouped.items():
            receiver_profile = planet_profiles.get(receiver)
            if not receiver_profile:
                continue

            guest_labels = [item["label"] for item in guests]
            results.append(
                {
                    "receiver": receiver.value,
                    "receiver_label": planet_label(receiver),
                    "receiver_house": receiver_profile["house"],
                    "receiver_house_title": receiver_profile["house_title"],
                    "receiver_sign": receiver_profile["sign"],
                    "receiver_sign_label": receiver_profile["sign_label"],
                    "guests": guests,
                    "line": f"{planet_label(receiver)}接纳{'/'.join(guest_labels)}",
                    "summary": (
                        f"{planet_label(receiver)}会接住落在其守护星座内的议题，"
                        f"并把它们带到第{receiver_profile['house']}宫 {receiver_profile['house_title']}去运作。"
                    ),
                }
            )

        results.sort(key=lambda item: (-len(item["guests"]), item["receiver_label"]))
        return results

    def _has_reception_link(
        self,
        guest: Planet,
        receiver: Planet,
        planet_profiles: Dict[Planet, Dict[str, Any]],
        aspect_cache: Dict[Planet, list[Dict[str, Any]]],
    ) -> bool:
        if self._is_mutual_reception_pair(guest, receiver, planet_profiles):
            return True

        for aspect in aspect_cache.get(guest, []):
            other = aspect["planet2"] if aspect["planet1"] == guest else aspect["planet1"]
            if other == receiver:
                return True
        return False

    def _is_mutual_reception_pair(
        self,
        planet_a: Planet,
        planet_b: Planet,
        planet_profiles: Dict[Planet, Dict[str, Any]],
    ) -> bool:
        profile_a = planet_profiles.get(planet_a)
        profile_b = planet_profiles.get(planet_b)
        if not profile_a or not profile_b:
            return False

        try:
            ruler_of_a = SIGN_RULERS[Sign(profile_a["sign"])]
            ruler_of_b = SIGN_RULERS[Sign(profile_b["sign"])]
        except Exception:
            return False

        return ruler_of_a == planet_b and ruler_of_b == planet_a

    def _build_mutual_receptions(
        self,
        planet_profiles: Dict[Planet, Dict[str, Any]],
    ) -> list[Dict[str, Any]]:
        results: list[Dict[str, Any]] = []
        seen: set[tuple[str, str]] = set()
        planets = list(planet_profiles.keys())

        for planet_a in planets:
            for planet_b in planets:
                if planet_a == planet_b:
                    continue
                if not self._is_mutual_reception_pair(planet_a, planet_b, planet_profiles):
                    continue

                key = tuple(sorted([planet_a.value, planet_b.value]))
                if key in seen:
                    continue
                seen.add(key)

                results.append(
                    {
                        "pair": [planet_a.value, planet_b.value],
                        "labels": [planet_label(planet_a), planet_label(planet_b)],
                        "line": f"{planet_label(planet_a)} 与 {planet_label(planet_b)} 互溶",
                        "summary": (
                            f"{planet_label(planet_a)}与{planet_label(planet_b)}互相进入对方守护的星座，"
                            "意味着这两条线会互相借力。"
                        ),
                    }
                )

        return results

    def _build_derived_house_profiles(
        self,
        house_rulers: list[Dict[str, Any]],
    ) -> list[Dict[str, Any]]:
        house_map = {item["house"]: item for item in house_rulers}
        configs = [
            {
                "base_house": 7,
                "base_label": "伴侣",
                "checks": [
                    (1, "伴侣本人"),
                    (2, "伴侣的钱财"),
                    (9, "伴侣的信念"),
                    (10, "伴侣的事业"),
                    (12, "伴侣的隐藏代价"),
                ],
            },
            {
                "base_house": 10,
                "base_label": "事业",
                "checks": [
                    (1, "事业本身"),
                    (2, "事业的钱"),
                    (7, "事业的合作/对手"),
                    (12, "事业的隐性代价"),
                ],
            },
            {
                "base_house": 2,
                "base_label": "财富",
                "checks": [
                    (1, "财富本身"),
                    (5, "财富的投机与扩张"),
                    (7, "财富的合作绑定"),
                    (12, "财富的隐形代价"),
                ],
            },
        ]

        results: list[Dict[str, Any]] = []
        for config in configs:
            links: list[Dict[str, Any]] = []
            for derived_house, label in config["checks"]:
                radical_house = self._turned_house(config["base_house"], derived_house)
                target = house_map.get(radical_house)
                if not target:
                    continue

                links.append(
                    {
                        "label": label,
                        "derived_house": derived_house,
                        "radical_house": radical_house,
                        "title": target["title"],
                        "adult_meaning": target["adult_meaning"],
                        "line": f"{label}看本盘第{radical_house}宫",
                        "ruler_line": target["line"],
                    }
                )

            results.append(
                {
                    "base_house": config["base_house"],
                    "base_label": config["base_label"],
                    "summary": (
                        f"转宫不是单看{config['base_label']}宫位本身，"
                        f"还要看围绕{config['base_label']}展开的信念、事业、资源与隐藏代价。"
                    ),
                    "links": links,
                }
            )

        return results

    def _turned_house(self, base_house: int, derived_house: int) -> int:
        return ((base_house + derived_house - 2) % 12) + 1

    def _build_pattern_readings(
        self,
        house_rulers: list[Dict[str, Any]],
        ruler_groups: list[Dict[str, Any]],
        reception_groups: list[Dict[str, Any]],
        mutual_receptions: list[Dict[str, Any]],
        derived_houses: list[Dict[str, Any]],
        planet_profiles: Dict[Planet, Dict[str, Any]],
    ) -> list[Dict[str, Any]]:
        house_map = {item["house"]: item for item in house_rulers}
        group_map = {item["ruler"]: item for item in ruler_groups}
        reception_map = {item["receiver"]: item for item in reception_groups}
        derived_map = {item["base_house"]: item for item in derived_houses}
        cards: list[Dict[str, Any]] = []

        identity = house_map.get(1)
        career = house_map.get(10)
        if identity and career:
            identity_profile = self._planet_profile_by_value(planet_profiles, identity["ruler"])
            same_ruler = identity["ruler"] == career["ruler"]
            identity_reception = reception_map.get(identity["ruler"])

            evidence = [identity["line"], career["line"]]
            if same_ruler:
                group = group_map.get(identity["ruler"])
                if group:
                    evidence.append(group["line"])
            if identity_reception:
                evidence.append(identity_reception["line"])
            if identity_profile:
                evidence.append(f"{identity['ruler_label']}{identity_profile['dignity_label']}")

            points = [
                f"1宫主 {identity['ruler_label']} 落在第{identity['ruler_house']}宫 {identity['ruler_house_title']}，说明你本人会通过这类现实场景被定义。",
                f"10宫主 {career['ruler_label']} 落在第{career['ruler_house']}宫 {career['ruler_house_title']}，事业和公开位置会顺着这条线被社会看见。",
                (
                    "1宫和10宫由同一颗星统领，个人风格、职业路径与社会身份天然绑在一起。"
                    if same_ruler
                    else "1宫和10宫分属不同主星，说明“你是谁”和“你如何成事”需要两套方法协同。"
                ),
            ]
            if identity_profile:
                points.append(
                    f"{identity['ruler_label']}先天状态为{identity_profile['dignity_label']}，"
                    f"{self._dignity_flow_text(identity_profile['dignity'])}"
                )
            if identity.get("flight_note"):
                points.append(identity["flight_note"])
            if career.get("flight_note"):
                points.append(career["flight_note"])
            if identity_reception:
                guest_topics = self._format_reception_topics(identity_reception, group_map)
                points.append(
                    f"{identity['ruler_label']}还接住了{guest_topics}这些课题，命主线不会只处理自我，还会把更多宫位议题一起卷进现实。"
                )

            cards.append(
                {
                    "key": "core_axis",
                    "title": "命主线与事业线",
                    "summary": (
                        "这张盘先看 1宫主 怎么落地，再看 10宫主 怎么显化。"
                        "它决定了命主是把自己活成事业，还是需要先分清人设与职业。"
                    ),
                    "evidence": self._unique_strings(evidence),
                    "points": points,
                }
            )

        career_pattern = self._build_career_pattern_card(
            house_map=house_map,
            group_map=group_map,
            reception_map=reception_map,
            mutual_receptions=mutual_receptions,
            planet_profiles=planet_profiles,
        )
        if career_pattern:
            cards.append(career_pattern)

        alliance = house_map.get(7)
        spouse_profile = derived_map.get(7)
        if alliance:
            alliance_profile = self._planet_profile_by_value(planet_profiles, alliance["ruler"])
            alliance_reception = reception_map.get(alliance["ruler"])
            spouse_links = {item["derived_house"]: item for item in spouse_profile.get("links", [])} if spouse_profile else {}

            evidence = [alliance["line"]]
            if alliance_reception:
                evidence.append(alliance_reception["line"])
            for derived_house in (1, 9, 10):
                link = spouse_links.get(derived_house)
                if link:
                    evidence.append(link["line"])

            points = [
                f"7宫主 {alliance['ruler_label']} 落在第{alliance['ruler_house']}宫 {alliance['ruler_house_title']}，伴侣、合作、贵人和公开对手会通过这类场景进入命运。",
                "7宫不只讲婚姻，也讲你会通过哪类人进入更大的系统、平台和资源网络。",
            ]
            if alliance_profile:
                points.append(
                    f"7宫主先天状态为{alliance_profile['dignity_label']}，"
                    f"{self._dignity_flow_text(alliance_profile['dignity'])}"
                )
            if alliance.get("flight_note"):
                points.append(alliance["flight_note"])
            if alliance_reception:
                guest_topics = self._format_reception_topics(alliance_reception, group_map)
                points.append(
                    f"{alliance['ruler_label']}接纳了{guest_topics}，说明联盟关系不会只带来感情或合约，也会连带更多资源和任务一起进场。"
                )
            if spouse_links:
                partner_self = spouse_links.get(1)
                partner_belief = spouse_links.get(9)
                partner_career = spouse_links.get(10)
                details: list[str] = []
                if partner_self:
                    details.append(f"伴侣本人看本盘第{partner_self['radical_house']}宫")
                if partner_belief:
                    details.append(f"伴侣的信念看本盘第{partner_belief['radical_house']}宫")
                if partner_career:
                    details.append(f"伴侣的事业看本盘第{partner_career['radical_house']}宫")
                if details:
                    points.append(f"转宫继续展开时，{'；'.join(details)}，所以这类关系会深度卷入你的现实结构。")

            cards.append(
                {
                    "key": "alliance_axis",
                    "title": "7宫助力与联盟入口",
                    "summary": "7宫决定你如何借别人上桌。对很多盘来说，真正的抬升并不来自单打独斗，而来自伴侣、合作、贵人和对手。",
                    "evidence": self._unique_strings(evidence),
                    "points": points,
                }
            )

        wealth = house_map.get(2)
        speculative = house_map.get(5)
        shared = house_map.get(8)
        wealth_profile = derived_map.get(2)
        if wealth and speculative and shared:
            wealth_planet = self._planet_profile_by_value(planet_profiles, wealth["ruler"])
            evidence = [wealth["line"], speculative["line"], shared["line"]]
            if wealth_planet:
                evidence.append(f"{wealth['ruler_label']}{wealth_planet['dignity_label']}")
            if wealth_profile:
                wealth_links = {item["derived_house"]: item for item in wealth_profile.get("links", [])}
                for derived_house in (5, 7, 12):
                    link = wealth_links.get(derived_house)
                    if link:
                        evidence.append(link["line"])

            points = [
                f"2宫主 {wealth['ruler_label']} 落在第{wealth['ruler_house']}宫 {wealth['ruler_house_title']}，说明你的钱会通过这类场景进入和流动。",
                f"5宫主 {speculative['ruler_label']} 落在第{speculative['ruler_house']}宫 {speculative['ruler_house_title']}，投机、创作、名气或让人上头的东西怎么参与财富，会看这条线。",
                f"8宫主 {shared['ruler_label']} 落在第{shared['ruler_house']}宫 {shared['ruler_house_title']}，共享资源、债务、利益绑定与灰度成本也会从这里进入。",
            ]
            if wealth_planet:
                points.append(
                    f"2宫主先天状态为{wealth_planet['dignity_label']}，"
                    f"{self._dignity_flow_text(wealth_planet['dignity'])}"
                )
            if wealth.get("flight_note"):
                points.append(wealth["flight_note"])
            if speculative.get("flight_note"):
                points.append(speculative["flight_note"])
            if shared.get("flight_note"):
                points.append(shared["flight_note"])
            if alliance and wealth["ruler"] == alliance["ruler"]:
                points.append("2宫与7宫同主，钱和伴侣、合作、客户、契约的绑定度通常比较高。")
            if career and wealth["ruler"] == career["ruler"]:
                points.append("2宫与10宫同主，财富和事业往往是同一条路，能不能赚到钱取决于能不能把职业位置做成资源入口。")

            cards.append(
                {
                    "key": "wealth_axis",
                    "title": "财富结构",
                    "summary": "财路不只看 2宫。真正的财富结构要同时看 2宫的变现能力、5宫的扩张方式、8宫的绑定与代价。",
                    "evidence": self._unique_strings(evidence),
                    "points": points,
                }
            )

        wealth_pattern = self._build_wealth_pattern_card(
            house_map=house_map,
            group_map=group_map,
            reception_map=reception_map,
            mutual_receptions=mutual_receptions,
            planet_profiles=planet_profiles,
        )
        if wealth_pattern:
            cards.append(wealth_pattern)

        if spouse_profile and alliance:
            spouse_links = {item["derived_house"]: item for item in spouse_profile.get("links", [])}
            evidence = [alliance["line"]]
            for derived_house in (1, 2, 9, 10, 12):
                link = spouse_links.get(derived_house)
                if link:
                    evidence.append(link["line"])

            points = []
            for derived_house in (1, 2, 9, 10, 12):
                link = spouse_links.get(derived_house)
                if not link:
                    continue
                points.append(
                    f"{link['label']}看本盘第{link['radical_house']}宫 {link['title']}，说明这段关系会把“{link['adult_meaning']}”这类现实议题带进来。"
                )
            points.append("所以 7宫不是单看对象性格，而是看你最容易通过哪类人形成稳定的借力、绑定与代价。")

            cards.append(
                {
                    "key": "partner_profile",
                    "title": "伴侣/合作方画像",
                    "summary": "转宫的价值，在于把“对象本人、对象的钱、对象的信念、对象的事业、对象的隐性代价”拆开看，而不是把7宫压扁成单一情感标签。",
                    "evidence": self._unique_strings(evidence),
                    "points": points,
                }
            )

        hidden = house_map.get(12)
        if hidden:
            hidden_profile = self._planet_profile_by_value(planet_profiles, hidden["ruler"])
            hidden_reception = reception_map.get(hidden["ruler"])
            related_mutuals = [
                item["line"]
                for item in mutual_receptions
                if hidden["ruler"] in item.get("pair", [])
            ]
            evidence = [hidden["line"]]
            if shared:
                evidence.append(shared["line"])
            if hidden_reception:
                evidence.append(hidden_reception["line"])
            evidence.extend(related_mutuals[:2])

            shared_axes: list[str] = []
            for house in (1, 7, 10):
                item = house_map.get(house)
                if item and item["ruler"] == hidden["ruler"] and house != 12:
                    shared_axes.append(f"{house}宫")

            points = [
                f"12宫主 {hidden['ruler_label']} 落在第{hidden['ruler_house']}宫 {hidden['ruler_house_title']}，幕后运作、隐线压力、清算与收束会通过这里出现。",
            ]
            if hidden_profile:
                points.append(
                    f"12宫主先天状态为{hidden_profile['dignity_label']}，"
                    f"{self._dignity_flow_text(hidden_profile['dignity'])}"
                )
            if hidden.get("flight_note"):
                points.append(hidden["flight_note"])
            if shared_axes:
                points.append(f"12宫主同时还统领{self._format_house_number_list(shared_axes)}，说明明线课题和幕后代价是绑在一起的。")
            if hidden_reception:
                guest_topics = self._format_reception_topics(hidden_reception, group_map)
                points.append(f"{hidden['ruler_label']}还接纳了{guest_topics}，所以台面下的问题不会孤立存在，而会和更多生活领域连成系统。")
            if related_mutuals:
                points.append("一旦12宫主参与互溶，往往代表明线与暗线会互相借力，也意味着后期更难完全切割代价。")

            cards.append(
                {
                    "key": "hidden_cost",
                    "title": "幕后结构与后期代价",
                    "summary": "12宫不是一句“潜意识”就能带过。它更像台面下的系统、收尾机制、隐形敌人，以及后期要被回收的代价。",
                    "evidence": self._unique_strings(evidence),
                    "points": points,
                }
            )

        return cards

    def _profile_strength_band(self, profile: Optional[Dict[str, Any]]) -> tuple[str, str]:
        if not profile:
            return "待识别", "这条线还需要放回具体盘面里判断。"

        score = float(profile.get("score", 0.0))
        if score >= 1.6:
            return "强", "这条线本身拿结果的能力强，更容易顺着结构放大。"
        if score >= 0.7:
            return "中上", "这条线可用，能成事，但仍然需要平台、方法和时机配合。"
        if score >= -0.15:
            return "中性", "这条线不是天然躺赢，也不是绝对吃力，成败更多看后天经营。"
        return "偏弱", "这条线先天更吃力，容易带着补课、代价或绕路推进。"

    def _wealth_channel_text(self, house: int) -> str:
        mapping = {
            1: "财富更容易跟个人品牌、个人能力和自我主导绑定。",
            2: "财富更容易沉淀成稳定现金流、资产和可支配资源。",
            3: "财富更容易通过沟通、交易、传播、课程、信息差进入。",
            4: "财富更容易通过家庭、土地、不动产或根基经营进入。",
            5: "财富更容易通过投机、创作、娱乐、名气或高波动收益进入。",
            6: "财富更容易通过技能、服务、执行、打工和辛苦钱进入。",
            7: "财富更容易通过客户、合作、伴侣、合约和他人关系进入。",
            8: "财富更容易通过资本、融资、共享资源、分成和风险筹码进入。",
            9: "财富更容易通过知识、培训、远方资源、海外与理念输出进入。",
            10: "财富更容易通过事业位置、名声、项目经营和公开头衔进入。",
            11: "财富更容易通过平台、团队、社群、众财池和大众资源放大。",
            12: "财富更容易卷入机构、幕后系统、隐线成本或延迟回收机制。",
        }
        return mapping.get(house, "财富通道需要回到具体盘面里判断。")

    def _career_channel_text(self, house: int) -> str:
        mapping = {
            1: "事业更容易和个人品牌、自我主导、独立身份绑在一起。",
            2: "事业更容易围绕资源管理、变现能力和商业化能力展开。",
            3: "事业更容易靠表达、传播、沟通、课程与信息调度做起来。",
            4: "事业更容易建立在原生根基、地产、空间、家庭盘或稳根基之后。",
            5: "事业更容易靠创作、舞台感、曝光度、名气和个人表现力推进。",
            6: "事业更容易通过执行、流程、专业服务、管理日常事务做起来。",
            7: "事业更容易通过合作、客户、签约、联盟或伴侣型资源推进。",
            8: "事业更容易卷入资本、金融、风控、深度博弈和利益绑定。",
            9: "事业更容易靠知识、教育、远方资源、理念输出和高阶认知推进。",
            10: "事业本身就强烈指向职位、抬头、公开成就和社会可见度。",
            11: "事业更容易通过团队、平台、社群、互联网和规模化网络放大。",
            12: "事业更容易与幕后系统、机构支持、研究隐线或收尾修复绑定。",
        }
        return mapping.get(house, "事业通道需要回到具体盘面里判断。")

    def _career_house_risk_text(self, house: int) -> str:
        mapping = {
            1: "容易把职业成败和自我价值绑死，一旦失手就会整个人一起掉状态。",
            2: "容易卡在定价、收入、价值感和现实回报，做事会越来越计较值不值。",
            3: "容易因为信息过载、表达分散、项目过多而消耗主线。",
            4: "容易被家庭根基、居住安排或情绪安全感拖住节奏。",
            5: "容易因为面子、表现欲、恋爱、兴趣和玩心影响职业判断。",
            6: "容易陷入过劳、琐事、执行内耗和长期疲惫。",
            7: "容易过度受客户、合作方、伴侣或外部评价牵制。",
            8: "容易卷入控制、债务、分成、风险博弈和利益清算。",
            9: "容易理想太满、话说太大，或者长期停留在认知升级却落地不足。",
            10: "容易把面子、头衔和外界评价看得过重，导致职业压力持续堆高。",
            11: "容易过度依赖平台、团队、人脉和外部流量，一旦风向变就被动。",
            12: "容易有幕后消耗、隐线敌人、延迟回收和后期清算成本。",
        }
        return mapping.get(house, "这条职业线的风险还要回到具体现实场景里判断。")

    def _wealth_house_risk_text(self, house: int) -> str:
        mapping = {
            1: "钱容易和身份、面子、自我证明绑太紧，花钱和挣钱都容易意气用事。",
            2: "钱能进来也未必留得住，核心是现金流、储蓄和价值感管理。",
            3: "钱路容易碎、散、杂，来得快去得也快，难点在稳定度。",
            4: "钱容易压在家庭、不动产、居住和原生责任上，流动性被拖住。",
            5: "钱最怕投机、冲动消费、情绪买单和高波动决策。",
            6: "钱往往来得辛苦，容易用健康、时间和稳定精力去换。",
            7: "钱容易被合作分走，也容易因为关系、客户和合约问题回款受阻。",
            8: "钱容易卷入债务、杠杆、分成、税务、风控和清算压力。",
            9: "钱容易花在理想、学习、远方、证书和信念扩张上，回收偏慢。",
            10: "钱容易和地位、面子、事业扩张绑在一起，进出规模都更大。",
            11: "钱容易依赖平台、团队、项目池和大众资源，波动也会被放大。",
            12: "钱最怕隐形成本、烂尾项目、拖延回款和看不见的漏损。",
        }
        return mapping.get(house, "这条财路线的风险还要回到具体现实场景里判断。")

    def _profile_operating_risk(
        self,
        profile: Optional[Dict[str, Any]],
        context_house: int,
        domain: str,
    ) -> str:
        if not profile:
            return "这条线的代价点还需要放回具体盘面里判断。"

        supportive = float(profile.get("supportive_aspects", 0.0))
        challenging = float(profile.get("challenging_aspects", 0.0))
        dignity = profile.get("dignity")
        retrograde = bool(profile.get("retrograde"))
        shadow = profile.get("shadow", "这条线一失衡就会用惯性反噬自己。")

        scene_text = (
            self._career_house_risk_text(context_house)
            if domain == "career"
            else self._wealth_house_risk_text(context_house)
        )

        if challenging > supportive + 0.35:
            state_text = "相位受克偏重，关键节点容易因为判断失衡、关系拉扯或外部冲突直接出问题。"
        elif dignity in {"detriment", "fall"}:
            state_text = "先天状态偏弱，这条线更像能做出来，但往往要靠补位、托举、试错或明显代价换结果。"
        elif retrograde:
            state_text = "这条线启动偏慢，前期容易反复试错、推迟兑现，或同一问题来回重做。"
        else:
            state_text = "即便整体可用，也不能只靠顺手感推进，否则很容易从最熟悉的动作里漏结果。"

        prefix = "职业代价" if domain == "career" else "财富代价"
        return f"{prefix}上，{scene_text} 更底层的毛病是{shadow}。{state_text}"

    def _build_career_pattern_card(
        self,
        house_map: Dict[int, Dict[str, Any]],
        group_map: Dict[str, Dict[str, Any]],
        reception_map: Dict[str, Dict[str, Any]],
        mutual_receptions: list[Dict[str, Any]],
        planet_profiles: Dict[Planet, Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        identity = house_map.get(1)
        career = house_map.get(10)
        vision = house_map.get(9)
        communication = house_map.get(3)
        network = house_map.get(11)
        if not identity or not career:
            return None

        identity_profile = self._planet_profile_by_value(planet_profiles, identity["ruler"])
        career_profile = self._planet_profile_by_value(planet_profiles, career["ruler"])
        network_profile = self._planet_profile_by_value(planet_profiles, network["ruler"]) if network else None
        communication_profile = self._planet_profile_by_value(planet_profiles, communication["ruler"]) if communication else None
        vision_profile = self._planet_profile_by_value(planet_profiles, vision["ruler"]) if vision else None

        upper_count = sum(1 for item in planet_profiles.values() if int(item.get("house", 0)) >= 7)
        upper_total = max(len(planet_profiles), 1)
        upper_heavy = upper_count / upper_total >= 0.57

        career_band, career_band_text = self._profile_strength_band(career_profile)
        identity_band, _ = self._profile_strength_band(identity_profile)
        same_ruler = identity["ruler"] == career["ruler"]
        career_risk_text = self._profile_operating_risk(career_profile, career["ruler_house"], domain="career")

        summary = (
            "事业格局偏强，明显更重事业、社会成就和公开位置，但越往上走越不能忽视职业代价。"
            if upper_heavy and career_band in {"强", "中上"}
            else "事业格局可做，但更像靠平台、表达、知识或团队路径逐步抬升，同时也更考验你能不能扛住长期压力。"
            if career_band in {"中上", "中性"}
            else "事业格局不是不能做，而是更依赖后天补位、平台托举和长期经营，起步期尤其容易感觉费力不讨好。"
        )

        evidence = [identity["line"], career["line"]]
        for item in (vision, communication, network):
            if item:
                evidence.append(item["line"])
        if identity_profile:
            evidence.append(f"1宫主{identity_profile['dignity_label']}")
        if career_profile:
            evidence.append(f"10宫主{career_profile['dignity_label']}")
        for planet_value in {identity["ruler"], career["ruler"], vision["ruler"] if vision else None, network["ruler"] if network else None}:
            if not planet_value:
                continue
            reception = reception_map.get(planet_value)
            if reception:
                evidence.append(reception["line"])
        for item in mutual_receptions:
            if identity["ruler"] in item.get("pair", []) or career["ruler"] in item.get("pair", []):
                evidence.append(item["line"])

        points = [
            f"10宫主 {career['ruler_label']} 飞到第{career['ruler_house']}宫 {career['ruler_house_title']}，{self._career_channel_text(career['ruler_house'])}",
            f"10宫主当前属于“{career_band}”档，{career_band_text}",
            f"事业主轴真正要付的代价是：{career_risk_text}",
            f"1宫主 {identity['ruler_label']} 飞到第{identity['ruler_house']}宫 {identity['ruler_house_title']}，说明你本人是用这条路进入事业系统的；命主线强度属于“{identity_band}”档。",
            (
                "1宫与10宫同主，说明你本人、职业身份和社会抬头天然是同一条路，做得好时会一起放大；风险是一旦职业线失衡，会直接打到自我价值和生活秩序。"
                if same_ruler
                else "1宫与10宫不同主，说明“你本人如何起手”和“事业如何做大”需要两套方法协同；风险是人已经很努力，但方法不对路时会出现明显割裂感。"
            ),
            (
                f"上半球行星占比偏高（{upper_count}/{upper_total}），这类盘通常更重事业、社会评价和外部成就；另一面是私人生活、关系和身体感受容易长期给事业让位。"
                if upper_heavy
                else f"上半球力量不算压倒性（{upper_count}/{upper_total}），事业不是唯一主轴，还要看生活结构是否愿意长期让位给成就；否则职业上升会反复被生活议题拉回。"
            ),
        ]
        if career.get("flight_note"):
            points.append(career["flight_note"])
        if identity.get("flight_note"):
            points.append(identity["flight_note"])
        if vision and vision_profile:
            points.append(
                f"9宫主 {vision['ruler_label']} 飞到第{vision['ruler_house']}宫 {vision['ruler_house_title']}，{self._career_channel_text(vision['ruler_house'])}"
            )
        if communication and communication_profile:
            points.append(
                f"3宫主 {communication['ruler_label']} 飞到第{communication['ruler_house']}宫 {communication['ruler_house_title']}，说明表达、沟通和信息处理会直接参与职业上升。"
            )
        if network and network_profile:
            points.append(
                f"11宫主 {network['ruler_label']} 飞到第{network['ruler_house']}宫 {network['ruler_house_title']}，说明团队、平台和资源网络会决定事业能不能规模化。"
            )

        return {
            "key": "career_pattern",
            "title": "事业格局",
            "summary": summary,
            "risk_summary": career_risk_text,
            "evidence": self._unique_strings(evidence)[:8],
            "points": points[:10],
        }

    def _build_wealth_pattern_card(
        self,
        house_map: Dict[int, Dict[str, Any]],
        group_map: Dict[str, Dict[str, Any]],
        reception_map: Dict[str, Dict[str, Any]],
        mutual_receptions: list[Dict[str, Any]],
        planet_profiles: Dict[Planet, Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        wealth = house_map.get(2)
        speculative = house_map.get(5)
        shared = house_map.get(8)
        network = house_map.get(11)
        career = house_map.get(10)
        if not wealth or not speculative or not shared or not network:
            return None

        wealth_profile = self._planet_profile_by_value(planet_profiles, wealth["ruler"])
        speculative_profile = self._planet_profile_by_value(planet_profiles, speculative["ruler"])
        shared_profile = self._planet_profile_by_value(planet_profiles, shared["ruler"])
        network_profile = self._planet_profile_by_value(planet_profiles, network["ruler"])

        wealth_band, wealth_band_text = self._profile_strength_band(wealth_profile)
        speculative_band, _ = self._profile_strength_band(speculative_profile)
        shared_band, shared_band_text = self._profile_strength_band(shared_profile)
        network_band, network_band_text = self._profile_strength_band(network_profile)
        wealth_risk_text = self._profile_operating_risk(wealth_profile, wealth["ruler_house"], domain="wealth")
        speculative_risk_text = self._profile_operating_risk(speculative_profile, speculative["ruler_house"], domain="wealth")
        shared_risk_text = self._profile_operating_risk(shared_profile, shared["ruler_house"], domain="wealth")
        network_risk_text = self._profile_operating_risk(network_profile, network["ruler_house"], domain="wealth")

        wealth_to_career = career and (wealth["ruler"] == career["ruler"] or wealth["ruler_house"] in {10, 11})
        wealth_to_network = wealth["ruler"] == network["ruler"] or wealth["ruler_house"] == 11
        wealth_to_shared = wealth["ruler"] == shared["ruler"] or shared["ruler"] == wealth["ruler"] or any(
            wealth["ruler"] in item.get("pair", []) and shared["ruler"] in item.get("pair", [])
            for item in mutual_receptions
        )

        if wealth_band == "强" and network_band in {"强", "中上"}:
            summary = "财富格局偏强，不只是会挣钱，还能把钱接进更大的平台、团队或众财池；但规模放大后，波动和回收压力也会一起放大。"
        elif wealth_band in {"强", "中上"} and shared_band in {"强", "中上"}:
            summary = "财富格局不低，既能靠自己挣钱，也能卷入资本、合伙或大资金调度；另一面是钱不会特别干净轻松，往往伴随绑定、分配和风控压力。"
        elif wealth_band in {"强", "中上"}:
            summary = "正财格局相对更稳，适合先把稳定收入、职业位置和长期现金流做厚；但也要防止自己挣得到却留不住。"
        else:
            summary = "财富格局不是没有机会，但更像结构性波动盘，钱能不能留住比能不能搞到更重要。"

        evidence = [wealth["line"], speculative["line"], shared["line"], network["line"]]
        if wealth_profile:
            evidence.append(f"2宫主{wealth_profile['dignity_label']}")
        if shared_profile:
            evidence.append(f"8宫主{shared_profile['dignity_label']}")
        if network_profile:
            evidence.append(f"11宫主{network_profile['dignity_label']}")
        for planet_value in {wealth["ruler"], speculative["ruler"], shared["ruler"], network["ruler"]}:
            reception = reception_map.get(planet_value)
            if reception:
                evidence.append(reception["line"])
        for item in mutual_receptions:
            pair = set(item.get("pair", []))
            if pair.intersection({wealth["ruler"], speculative["ruler"], shared["ruler"], network["ruler"]}):
                evidence.append(item["line"])

        points = [
            f"2宫主 {wealth['ruler_label']} 飞到第{wealth['ruler_house']}宫 {wealth['ruler_house_title']}，{self._wealth_channel_text(wealth['ruler_house'])} 这条正财线当前属于“{wealth_band}”档，{wealth_band_text}",
            f"正财线的漏财点和代价是：{wealth_risk_text}",
            f"5宫主 {speculative['ruler_label']} 飞到第{speculative['ruler_house']}宫 {speculative['ruler_house_title']}，偏财、投机、娱乐消费与名气扩张属于“{speculative_band}”档。它的风险是：{speculative_risk_text}",
            f"8宫主 {shared['ruler_label']} 飞到第{shared['ruler_house']}宫 {shared['ruler_house_title']}，{self._wealth_channel_text(shared['ruler_house'])} 这条共享资源线属于“{shared_band}”档，{shared_band_text}",
            f"共享资源线最怕的是：{shared_risk_text}",
            f"11宫主 {network['ruler_label']} 飞到第{network['ruler_house']}宫 {network['ruler_house_title']}，{self._wealth_channel_text(network['ruler_house'])} 这条财富池/平台线属于“{network_band}”档，{network_band_text}",
            f"平台/众财池这条线的波动点是：{network_risk_text}",
            (
                "2宫和10/11宫联系很紧，说明这张盘的钱很容易和事业、项目、平台规模化绑在一起；另一面是只要事业节奏或平台风向一变，现金流也会一起波动。"
                if wealth_to_career or wealth_to_network
                else "2宫和10/11宫没有特别强的同主或直连，说明钱不一定天然跟着事业规模一起放大，也意味着财富更多要靠个人管控能力慢慢沉淀。"
            ),
            (
                "2宫与8宫存在明显联动，钱不仅靠自己挣，也容易卷入融资、分成、合伙和大资金调度；好处是盘子大，代价是你很难完全只赚干净轻松的钱。"
                if wealth_to_shared
                else "2宫与8宫没有特别强的借力结构，说明这张盘更适合把个人变现能力先做扎实，不宜太早依赖高杠杆和复杂绑定。"
            ),
        ]

        if wealth.get("flight_note"):
            points.append(wealth["flight_note"])
        if speculative.get("flight_note"):
            points.append(speculative["flight_note"])
        if shared.get("flight_note"):
            points.append(shared["flight_note"])

        return {
            "key": "wealth_pattern",
            "title": "财富格局",
            "summary": summary,
            "risk_summary": wealth_risk_text,
            "evidence": self._unique_strings(evidence)[:10],
            "points": points[:12],
        }

    def _planet_profile_by_value(
        self,
        planet_profiles: Dict[Planet, Dict[str, Any]],
        planet_value: str,
    ) -> Optional[Dict[str, Any]]:
        try:
            return planet_profiles.get(Planet(planet_value))
        except Exception:
            return None

    def _format_reception_topics(
        self,
        reception_group: Dict[str, Any],
        group_map: Dict[str, Dict[str, Any]],
    ) -> str:
        topics: list[str] = []
        for guest in reception_group.get("guests", []):
            group = group_map.get(guest["planet"])
            topics.append(group["notation"] if group else guest["label"])
        unique_topics = self._unique_strings(topics)
        return "、".join(unique_topics[:4]) if unique_topics else "其他宫位课题"

    def _dignity_flow_text(self, dignity_code: str) -> str:
        mapping = {
            "domicile": "这条线比较稳，做起来更像顺手放大。",
            "exaltation": "这条线容易被放大和看见，但也更容易被寄予高期待。",
            "peregrine": "这条线更依赖后天环境、方法和所处平台来定胜负。",
            "detriment": "这条线能成事，但常常要靠失衡、代价或绕路来推进。",
            "fall": "这条线先天吃力，往往需要托举、补位或付出明显代价。",
        }
        return mapping.get(dignity_code, "这条线需要放回具体环境里判断。")

    def _unique_strings(self, values: Iterable[str]) -> list[str]:
        results: list[str] = []
        seen: set[str] = set()
        for item in values:
            if not item or item in seen:
                continue
            seen.add(item)
            results.append(item)
        return results

    def _format_house_number_list(self, values: Iterable[str]) -> str:
        items = [item for item in values if item]
        if not items:
            return ""
        if len(items) == 1:
            return items[0]
        return "、".join(items[:-1]) + "和" + items[-1]

    def _build_huang_jinrong_case_themes(
        self,
        natal_chart: Dict[str, Any],
        planet_profiles: Dict[Planet, Dict[str, Any]],
        house_rulers: list[Dict[str, Any]],
        ruler_groups: list[Dict[str, Any]],
        reception_groups: list[Dict[str, Any]],
        derived_houses: list[Dict[str, Any]],
    ) -> list[Dict[str, Any]]:
        group_map = {item["ruler"]: item for item in ruler_groups}
        reception_map = {item["receiver"]: item for item in reception_groups}
        spouse_profile = derived_houses[0] if derived_houses else None

        mercury_group = group_map.get(Planet.MERCURY.value)
        jupiter_group = group_map.get(Planet.JUPITER.value)
        venus_group = group_map.get(Planet.VENUS.value)
        saturn_group = group_map.get(Planet.SATURN.value)
        mars_group = group_map.get(Planet.MARS.value)
        moon_group = group_map.get(Planet.MOON.value)
        sun_group = group_map.get(Planet.SUN.value)

        mercury_profile = planet_profiles.get(Planet.MERCURY, {})
        venus_profile = planet_profiles.get(Planet.VENUS, {})
        mars_profile = planet_profiles.get(Planet.MARS, {})

        return [
            {
                "key": "nobility",
                "title": "得贵格局",
                "summary": "先天不是轻松命，后天靠7宫木星与联盟结构托举上位，属于典型的后天得贵。",
                "evidence": [
                    mercury_group["line"] if mercury_group else "1R/10R 水星飞3宫",
                    jupiter_group["line"] if jupiter_group else "4R/7R 木星飞7宫",
                    sun_group["line"] if sun_group else "12R 太阳飞3宫",
                    reception_map.get(Planet.JUPITER.value, {}).get("line", "木星接纳太阳/水星/土星"),
                    f"水星{mercury_profile.get('dignity_label', '失势')}" if mercury_profile else "水星失势",
                ],
                "points": [
                    "命主水星既主1宫也主10宫，却落在3宫且先天失势，说明不是门第型、清望型的轻松贵命。",
                    "真正的抬升点来自7宫木星：贵气不是自己天然带来的，而是通过贵人、伴侣、联盟和更大的制度平台后天形成。",
                    "木星把落在自己星座里的太阳、水星、土星接住，再把这些议题带去7宫运作，所以得贵不是空话，而是有人托、有人带、有人接。",
                    "这类贵不是清贵，而是势贵：先借人、借系统、借关系，后把借来的势做成自己的位置。",
                ],
            },
            {
                "key": "seventh_house_support",
                "title": "7宫助力",
                "summary": "7宫不是单纯婚姻，而是最强的托举口。伴侣、贵人、兄弟网络都会从这里进来。",
                "evidence": [
                    jupiter_group["line"] if jupiter_group else "4R/7R 木星飞7宫",
                    saturn_group["line"] if saturn_group else "5R/6R 土星飞3宫",
                    moon_group["line"] if moon_group else "11R 月亮飞3宫",
                    mercury_group["line"] if mercury_group else "10R 水星飞3宫",
                    spouse_profile["links"][2]["line"] if spouse_profile and len(spouse_profile["links"]) > 2 else "伴侣的信念看本盘第3宫",
                ],
                "points": [
                    "7R 木星飞7，本身就说明伴侣、盟友、保护关系、门生网络是成事入口，不只是情感配置。",
                    "7宫木星不只接住命主，也间接带动事业宫，所以伴侣和联盟对事业抬升有实质帮助。",
                    "11宫月亮飞3宫，朋友、团队、兄弟感和信息网络连在一起，容易形成讲义气、重关系的帮会式结构。",
                ],
            },
            {
                "key": "wealth",
                "title": "财富格局",
                "summary": "有挣钱格局，也有大进大出的格局。能把资源做成钱，但守财和留财不强。",
                "evidence": [
                    venus_group["line"] if venus_group else "2R/9R 金星飞2宫",
                    saturn_group["line"] if saturn_group else "5R/6R 土星飞3宫",
                    mars_group["line"] if mars_group else "3R/8R 火星飞12宫",
                    f"金星{venus_profile.get('dignity_label', '失势')}" if venus_profile else "金星失势",
                ],
                "points": [
                    "2R/9R 金星飞2宫，说明他有财富嗅觉，也懂得把关系、欲望、资源和现实收益绑成钱。",
                    "但金星先天失势，财富不是干净稳态的累积，更像大进大出、能挣但不容易真正留下。",
                    "5R/6R 土星和 3R/8R 火星把投机财、辛苦财、暗财、灰度财连在一起，所以财路往往和技能、跑动、娱乐、地下资源有关。",
                ],
            },
            {
                "key": "dual_system",
                "title": "黑白通吃",
                "summary": "这张盘最大的本事，不是单一权威，而是在台面上和台面下都能运作。",
                "evidence": [
                    mercury_group["line"] if mercury_group else "1R/10R 水星飞3宫",
                    mars_group["line"] if mars_group else "3R/8R 火星飞12宫",
                    sun_group["line"] if sun_group else "12R 太阳飞3宫",
                    "水星合土星",
                ],
                "points": [
                    "1R/10R 水星飞3宫，身份与事业都靠消息、口才、名单、交通、传递、组织网络运作。",
                    "3R/8R 火星飞12宫，说明沟通、风险、暗财、暴力和幕后操作天然有链路，不是完全分开的系统。",
                    "12R 太阳飞3宫又让幕后资源、隐性保护和台面上的说法绑在一起，所以能同时打通黑白两面。",
                ],
            },
            {
                "key": "career",
                "title": "事业暗线",
                "summary": "事业不是常规体制型上升，而是信息、差事、规则边缘和联盟关系推动出来的。",
                "evidence": [
                    mercury_group["line"] if mercury_group else "10R 水星飞3宫",
                    jupiter_group["line"] if jupiter_group else "7R 木星飞7宫",
                    saturn_group["line"] if saturn_group else "6R 土星飞3宫",
                    "木星拱土星",
                ],
                "points": [
                    "10R 水星飞3宫，事业抬升不是靠纯名望，而是靠能跑、能说、能接线、能调度人和规则。",
                    "6R 土星飞3宫说明技能、学徒、劳苦、执行力都和事业底盘绑在一起，先苦后抬升。",
                    "7宫木星再把事业接进联盟和贵人系统，所以职业线经常不是单兵突破，而是被带着往上走。",
                ],
            },
            {
                "key": "marriage",
                "title": "婚姻与外缘",
                "summary": "正宫关系是托举型的，但外缘不会少，婚姻里容易出现隐藏人物与台面下关系。",
                "evidence": [
                    jupiter_group["line"] if jupiter_group else "7R 木星飞7宫",
                    sun_group["line"] if sun_group else "12R 太阳飞3宫",
                    saturn_group["line"] if saturn_group else "5R 土星飞3宫",
                    mars_group["line"] if mars_group else "8R 火星飞12宫",
                    spouse_profile["links"][3]["line"] if spouse_profile and len(spouse_profile["links"]) > 3 else "伴侣的事业看本盘第4宫",
                ],
                "points": [
                    "7R 木星飞7先说明正宫本身有托举、包容和带平台的力量，婚姻不是完全失序的。",
                    "但12宫不断被带进婚姻与社交链路，说明关系里会有隐藏人、暗线、看不见的外部因素。",
                    "5宫和8宫又都牵到12宫，所以短桃花、露水关系、外面有人这类题目更像盘主自己带出来的结构性问题。",
                ],
            },
            {
                "key": "spouse_profile",
                "title": "伴侣画像",
                "summary": "伴侣不是弱角色，更像托举型、包容型、有理想感的人。",
                "evidence": [
                    jupiter_group["line"] if jupiter_group else "7R 木星飞7宫",
                    spouse_profile["links"][0]["line"] if spouse_profile and spouse_profile["links"] else "伴侣本人看本盘第7宫",
                    spouse_profile["links"][2]["line"] if spouse_profile and len(spouse_profile["links"]) > 2 else "伴侣的信念看本盘第3宫",
                    spouse_profile["links"][3]["line"] if spouse_profile and len(spouse_profile["links"]) > 3 else "伴侣的事业看本盘第4宫",
                ],
                "points": [
                    "7宫自己就很强，说明伴侣不是边缘人物，而是能独立成事、能提供平台的人。",
                    "伴侣的信念看本盘第3宫，那里群星集中，说明她身上带着强烈的理念感、讲法、信念与价值判断。",
                    "伴侣的事业与外部位置再看转宫，也能看到她并不是单纯依附型，而是具备实际托举和资源调动能力的人。",
                ],
            },
            {
                "key": "reckoning",
                "title": "晚年清算",
                "summary": "前半生靠幕后、暗线和制度缝隙成事，后半生也容易被这些东西反向回收。",
                "evidence": [
                    mars_group["line"] if mars_group else "8R 火星飞12宫",
                    sun_group["line"] if sun_group else "12R 太阳飞3宫",
                    mercury_group["line"] if mercury_group else "1R/10R 水星飞3宫",
                    f"火星落{mars_profile.get('house_title', '12宫')}" if mars_profile else "火星落12宫",
                ],
                "points": [
                    "12宫在这张盘里不是纯隐退，而是幕后运作、清算、监禁、隐形敌人与回收机制。",
                    "前面那些台面下的助力，在得势时叫保护伞和资源；失势时就会变成公众评价、名单、羞辱和清算。",
                    "所以这是典型的前半生借势，后半生回收的结构盘，晚年很难完全脱离前面留下的因果。",
                ],
            },
        ]

    def _find_period_for_age(
        self,
        periods_data: list[Dict[str, Any]],
        age: float,
    ) -> Optional[Dict[str, Any]]:
        for period in periods_data:
            start_age = period["timing"]["start_age"]
            end_age = period["timing"]["end_age"]
            if start_age <= age < end_age:
                return period
        return None

    def _is_huang_jinrong_sample(self, birth_time_iso: str, lat: float, lon: float) -> bool:
        normalized_time = birth_time_iso.strip()
        return (
            normalized_time.startswith("1868-12-14T00:01")
            and abs(lat - 30.05) < 0.02
            and abs(lon - 121.1667) < 0.02
        )

    def _build_role_title(
        self,
        natal_chart: Dict[str, Any],
        planet_profiles: Dict[Planet, Dict[str, Any]],
        is_historical_sample: bool = False,
    ) -> str:
        if is_historical_sample:
            return "信息操盘型权力人物"

        top_houses = [item["house"] for item in natal_chart.get("house_emphasis", [])]
        chart_ruler = natal_chart.get("chart_ruler")
        chart_ruler_profile = self._planet_profile_by_value(planet_profiles, chart_ruler) if chart_ruler else None
        chart_ruler_planet: Optional[Planet] = None
        try:
            chart_ruler_planet = Planet(chart_ruler) if chart_ruler else None
        except Exception:
            chart_ruler_planet = None

        if chart_ruler_profile and chart_ruler_planet:
            house_stem = HOUSE_ROLE_STEMS.get(chart_ruler_profile["house"], "核心")
            planet_stem = PLANET_ROLE_STEMS.get(chart_ruler_planet, natal_chart.get("chart_ruler_label", "命主"))
            ending = PLANET_ROLE_ENDINGS.get(chart_ruler_planet, "组织者")
            sign_prefix = str(chart_ruler_profile.get("sign_label", "")).replace("座", "")

            if chart_ruler_planet == Planet.MERCURY and chart_ruler_profile["house"] == 11:
                return f"{sign_prefix}社群信息型组织者"
            if chart_ruler_planet == Planet.MERCURY and chart_ruler_profile["house"] in {3, 10}:
                return f"{sign_prefix}传播信息型推进者"
            if chart_ruler_planet == Planet.JUPITER and 7 in top_houses:
                return f"{sign_prefix}联盟扩张型整合者"
            if chart_ruler_planet == Planet.SATURN and chart_ruler_profile["house"] in {9, 10}:
                return f"{sign_prefix}理念结构型架构者"
            if chart_ruler_planet == Planet.VENUS and chart_ruler_profile["house"] in {7, 10}:
                return f"{sign_prefix}关系经营型整合者"
            if chart_ruler_planet == Planet.MARS and chart_ruler_profile["house"] in {1, 10}:
                return f"{sign_prefix}行动攻坚型推进者"

            return f"{sign_prefix}{house_stem}{planet_stem}型{ending}"

        if 3 in top_houses and chart_ruler == Planet.MERCURY.value:
            if 7 in top_houses or any(profile["house"] == 7 for profile in planet_profiles.values()):
                return "关系网络型操盘者"
            if 12 in top_houses or any(profile["house"] == 12 for profile in planet_profiles.values()):
                return "隐性控制型组织者"
            return "信息整合型推进者"
        if 7 in top_houses:
            return "联盟扩张型整合者"
        if 10 in top_houses:
            return "公开角色型推进者"
        return f"{natal_chart['chart_ruler_label']}主导型人生角色"

    def _build_role_keywords(self, natal_chart: Dict[str, Any]) -> list[str]:
        keywords: list[str] = []
        for item in natal_chart.get("house_emphasis", [])[:4]:
            meaning = HOUSE_ADULT_MEANINGS.get(item["house"], {}).get("adult")
            if meaning:
                keywords.append(meaning)
        return keywords[:4]

    def _format_house_titles(self, houses: list[Dict[str, Any]]) -> str:
        if not houses:
            return "关键宫位"
        return "、".join(item["title"] for item in houses)

    def _format_house_adult_meanings(self, houses: list[Dict[str, Any]]) -> str:
        if not houses:
            return "基础社会议题"
        items = []
        for item in houses:
            meaning = HOUSE_ADULT_MEANINGS.get(item["house"], {}).get("adult", item["title"])
            items.append(f"{item['title']}（{meaning}）")
        return "；".join(items)

    def _build_life_model(
        self,
        chart: Any,
        natal_chart: Dict[str, Any],
        periods_data: list[Dict[str, Any]],
        current_phase: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        dominant = natal_chart.get("dominant_planets", [])
        houses = natal_chart.get("house_emphasis", [])
        strongest = dominant[:2]
        pressure_points = natal_chart.get("pressure_points", [])
        best_periods = sorted(periods_data, key=lambda item: item["trend"]["bonus_coefficient"], reverse=True)[:3]
        reset_periods = sorted(periods_data, key=lambda item: item["trend"]["bonus_coefficient"])[:2]

        title = self._life_model_title(dominant, natal_chart)
        core_themes = [
            f"{item['title']}是人生主轴" for item in houses[:3]
        ]
        strengths = [item["reason"] for item in strongest]
        challenges = [item["reason"] for item in pressure_points]
        growth_path = self._growth_path_lines(natal_chart, houses, pressure_points)
        strategy = self._strategy_lines(current_phase, strongest)

        return {
            "title": title,
            "summary": natal_chart["signature"],
            "core_themes": core_themes,
            "strengths": strengths,
            "challenges": challenges,
            "growth_path": growth_path,
            "strategy": strategy,
            "peak_windows": [
                {
                    "age_range": f"{int(item['timing']['start_age'])}-{int(item['timing']['end_age'])}岁",
                    "lords": f"{planet_label(item['lords']['major'])}/{planet_label(item['lords']['sub']) if item['lords']['sub'] else '无'}",
                    "summary": item["summary"],
                }
                for item in best_periods
            ],
            "reset_windows": [
                {
                    "age_range": f"{int(item['timing']['start_age'])}-{int(item['timing']['end_age'])}岁",
                    "lords": f"{planet_label(item['lords']['major'])}/{planet_label(item['lords']['sub']) if item['lords']['sub'] else '无'}",
                    "summary": item["summary"],
                }
                for item in reset_periods
            ],
        }

    def _life_model_title(self, dominant: list[Dict[str, Any]], natal_chart: Dict[str, Any]) -> str:
        asc_label = natal_chart["ascendant"]["sign_label"]
        ruler_label = natal_chart["chart_ruler_label"]
        dominant_labels = " / ".join(item["label"] for item in dominant[:2]) if dominant else ruler_label
        return f"{asc_label}上升 · {dominant_labels} 主导型人生模型"

    def _growth_path_lines(
        self,
        natal_chart: Dict[str, Any],
        houses: list[Dict[str, Any]],
        pressure_points: list[Dict[str, Any]],
    ) -> list[str]:
        lines = []
        if houses:
            lines.append(
                f"先把{houses[0]['title']}做成稳定结构，再去追求更大的舞台和结果。"
            )
        if pressure_points:
            lines.append(
                f"对{pressure_points[0]['label']}的课题，不能只靠天赋，应建立规则、边界与复盘机制。"
            )
        lines.append(
            f"命主星是{natal_chart['chart_ruler_label']}，真正的跃迁来自持续经营而不是偶发爆发。"
        )
        return lines

    def _strategy_lines(
        self,
        current_phase: Optional[Dict[str, Any]],
        strongest: list[Dict[str, Any]],
    ) -> list[str]:
        lines: list[str] = []
        if current_phase:
            lines.append(
                f"当前阶段优先处理{current_phase['dominant_domains'][0]['label']}，这是此刻最能带动全局的入口。"
            )
            lines.extend(current_phase["action_focus"][:2])
        if strongest:
            lines.append(
                f"长期来看，要让{strongest[0]['label']}的优势变成可复制的方法，而不是只在状态好时才出现。"
            )
        return lines[:4]

    def _absolute_longitude(self, info: Any) -> float:
        longitude = getattr(info, "longitude", 0.0)
        if longitude:
            return float(longitude) % 360.0
        sign = getattr(info, "sign")
        degree = getattr(info, "degree", 0.0)
        sign_index = list(Sign).index(sign)
        return sign_index * 30.0 + degree

    def generate_monthly_lunar_return(
        self,
        birth_time_iso: str,
        lat: float,
        lon: float,
        timezone_offset: float = 8.0,
        gender: Optional[str] = None,
        reference_time_utc: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        birth_time_local, birth_time_utc = self._parse_birth_time(birth_time_iso, timezone_offset)
        natal_chart = self.engine.calculate_chart(birth_time_utc, lat, lon)
        natal_aspect_cache = self._build_aspect_cache(natal_chart)
        natal_profiles = self._build_planet_profiles(natal_chart, natal_aspect_cache)
        natal_chart_payload = self._build_natal_chart(
            natal_chart,
            natal_profiles,
            natal_aspect_cache,
            birth_time_utc=birth_time_utc,
            lat=lat,
            lon=lon,
        )

        if reference_time_utc is None:
            reference_time_utc = datetime.utcnow()

        natal_moon = natal_chart.get_planet_info(Planet.MOON)
        if not natal_moon:
            raise ValueError("Natal moon position is unavailable.")

        natal_moon_longitude = self._absolute_longitude(natal_moon)
        lunar_return_exact_utc = self._find_current_lunar_return(
            natal_moon_longitude=natal_moon_longitude,
            birth_time_utc=birth_time_utc,
            reference_time_utc=reference_time_utc,
            lat=lat,
            lon=lon,
        )
        next_lunar_return_exact_utc = self._find_nth_lunar_return_after(
            natal_moon_longitude=natal_moon_longitude,
            birth_time_utc=birth_time_utc,
            start_time_utc=lunar_return_exact_utc + timedelta(minutes=30),
            count=1,
            lat=lat,
            lon=lon,
        )

        lunar_return_exact_local = lunar_return_exact_utc + timedelta(hours=timezone_offset)
        next_lunar_return_exact_local = next_lunar_return_exact_utc + timedelta(hours=timezone_offset)

        lunar_return_chart = self.engine.calculate_chart(lunar_return_exact_utc, lat, lon)
        lunar_return_aspect_cache = self._build_aspect_cache(lunar_return_chart)
        lunar_return_profiles = self._build_planet_profiles(lunar_return_chart, lunar_return_aspect_cache)
        lunar_return_chart_payload = self._build_natal_chart(
            lunar_return_chart,
            lunar_return_profiles,
            lunar_return_aspect_cache,
            birth_time_utc=lunar_return_exact_utc,
            lat=lat,
            lon=lon,
        )

        moon_windows = self._build_lunar_return_moon_windows(
            start_utc=lunar_return_exact_utc,
            end_utc=next_lunar_return_exact_utc,
            lat=lat,
            lon=lon,
            timezone_offset=timezone_offset,
        )

        return {
            "meta": {
                "generated_at": datetime.now().isoformat(),
                "engine_version": "2.5.0",
            },
            "user_info": {
                "gender": gender,
                "birth_time_local": birth_time_local.isoformat(),
                "birth_time_utc": birth_time_utc.isoformat(),
                "lat": lat,
                "lon": lon,
                "timezone": f"GMT {timezone_offset:+.2f}",
                "is_day_chart": natal_chart.is_day_chart,
            },
            "reference": {
                "current_date_utc": reference_time_utc.isoformat(),
                "current_date_local": (reference_time_utc + timedelta(hours=timezone_offset)).isoformat(),
                "timezone_offset": timezone_offset,
            },
            "natal_chart": natal_chart_payload,
            "lunar_return": {
                "cycle_label": lunar_return_exact_local.strftime("%Y-%m 月返"),
                "return_time_local": lunar_return_exact_local.isoformat(),
                "return_time_utc": lunar_return_exact_utc.isoformat(),
                "next_return_time_local": next_lunar_return_exact_local.isoformat(),
                "next_return_time_utc": next_lunar_return_exact_utc.isoformat(),
                "cycle_start_local": lunar_return_exact_local.isoformat(),
                "cycle_end_local": next_lunar_return_exact_local.isoformat(),
                "cycle_start_utc": lunar_return_exact_utc.isoformat(),
                "cycle_end_utc": next_lunar_return_exact_utc.isoformat(),
                "moon_windows": moon_windows,
                "chart": lunar_return_chart_payload,
            },
        }

    def _find_current_lunar_return(
        self,
        natal_moon_longitude: float,
        birth_time_utc: datetime,
        reference_time_utc: datetime,
        lat: float,
        lon: float,
    ) -> datetime:
        days_since_birth = max((reference_time_utc - birth_time_utc).total_seconds() / 86400.0, 0.0)
        cycles_elapsed = max(int(days_since_birth // SIDEREAL_MONTH_DAYS), 0)
        search_start = birth_time_utc + timedelta(days=max(cycles_elapsed - 1, 0) * SIDEREAL_MONTH_DAYS)
        last_match: Optional[datetime] = None

        for cycle_index in range(max(cycles_elapsed + 3, 4)):
            target = self._find_lunar_return_near(
                start_utc=search_start + timedelta(days=cycle_index * SIDEREAL_MONTH_DAYS),
                natal_moon_longitude=natal_moon_longitude,
                lat=lat,
                lon=lon,
            )
            if target <= reference_time_utc:
                last_match = target
                continue
            return last_match or target

        if last_match is None:
            raise ValueError("Failed to locate current lunar return.")
        return last_match

    def _find_nth_lunar_return_after(
        self,
        natal_moon_longitude: float,
        birth_time_utc: datetime,
        start_time_utc: datetime,
        count: int,
        lat: float,
        lon: float,
    ) -> datetime:
        current = start_time_utc
        found = 0

        while found < count:
            guess_days = max((current - birth_time_utc).total_seconds() / 86400.0, 0.0)
            cycle_index = max(int(round(guess_days / SIDEREAL_MONTH_DAYS)), 0)
            candidate = self._find_lunar_return_near(
                start_utc=birth_time_utc + timedelta(days=cycle_index * SIDEREAL_MONTH_DAYS),
                natal_moon_longitude=natal_moon_longitude,
                lat=lat,
                lon=lon,
            )
            if candidate <= current:
                candidate = self._find_lunar_return_near(
                    start_utc=birth_time_utc + timedelta(days=(cycle_index + 1) * SIDEREAL_MONTH_DAYS),
                    natal_moon_longitude=natal_moon_longitude,
                    lat=lat,
                    lon=lon,
                )
            current = candidate + timedelta(minutes=1)
            found += 1

        return current - timedelta(minutes=1)

    def _find_lunar_return_near(
        self,
        start_utc: datetime,
        natal_moon_longitude: float,
        lat: float,
        lon: float,
    ) -> datetime:
        coarse_start = start_utc - timedelta(days=2)
        coarse_end = start_utc + timedelta(days=2)
        best_time = coarse_start
        best_value = 999.0

        cursor = coarse_start
        while cursor <= coarse_end:
            moon_longitude = self._moon_longitude_at(cursor, lat, lon)
            distance = deg_diff(moon_longitude, natal_moon_longitude)
            if distance < best_value:
                best_value = distance
                best_time = cursor
            cursor += timedelta(hours=6)

        left = best_time - timedelta(hours=6)
        right = best_time + timedelta(hours=6)

        for delta_seconds in (3600, 300, 60, 1):
            current = left
            local_best_time = current
            local_best_value = 999.0
            local_step = timedelta(seconds=delta_seconds)
            while current <= right:
                moon_longitude = self._moon_longitude_at(current, lat, lon)
                distance = deg_diff(moon_longitude, natal_moon_longitude)
                if distance < local_best_value:
                    local_best_value = distance
                    local_best_time = current
                current += local_step
            left = local_best_time - local_step
            right = local_best_time + local_step

        return local_best_time

    def _moon_longitude_at(self, dt_utc: datetime, lat: float, lon: float) -> float:
        chart = self.engine.calculate_chart(dt_utc, lat, lon)
        moon = chart.get_planet_info(Planet.MOON)
        if not moon:
            raise ValueError("Moon position is unavailable.")
        return self._absolute_longitude(moon)

    def _build_lunar_return_moon_windows(
        self,
        start_utc: datetime,
        end_utc: datetime,
        lat: float,
        lon: float,
        timezone_offset: float,
    ) -> list[Dict[str, Any]]:
        samples = self._sample_lunar_cycle_positions(start_utc, end_utc, lat, lon)
        windows: list[Dict[str, Any]] = []

        for planet in LUNAR_RETURN_WINDOW_PLANETS:
            for aspect in LUNAR_RETURN_MOON_ASPECTS:
                aspect_angle = float(aspect["angle"])
                series: list[Dict[str, Any]] = []
                for item in samples:
                    moon_position = item["positions"].get(Planet.MOON)
                    target_position = item["positions"].get(planet)
                    if moon_position is None or target_position is None:
                        continue
                    separation = deg_diff(moon_position, target_position)
                    series.append(
                        {
                            "timestamp_utc": item["timestamp_utc"],
                            "delta": abs(separation - aspect_angle),
                            "separation": separation,
                        }
                    )

                for interval in self._extract_orb_intervals(series, LUNAR_RETURN_ORB_DEGREES):
                    exact_sample = min(interval["samples"], key=lambda item: item["delta"])
                    windows.append(
                        {
                            "planet": planet.value,
                            "planet_label": planet_label(planet),
                            "aspect_key": aspect["key"],
                            "aspect_angle": aspect_angle,
                            "aspect_label": aspect["label"],
                            "orb_limit": LUNAR_RETURN_ORB_DEGREES,
                            "start_time_local": (interval["start_utc"] + timedelta(hours=timezone_offset)).isoformat(),
                            "end_time_local": (interval["end_utc"] + timedelta(hours=timezone_offset)).isoformat(),
                            "start_time_utc": interval["start_utc"].isoformat(),
                            "end_time_utc": interval["end_utc"].isoformat(),
                            "exact_time_local": (exact_sample["timestamp_utc"] + timedelta(hours=timezone_offset)).isoformat(),
                            "exact_time_utc": exact_sample["timestamp_utc"].isoformat(),
                            "exact_orb": round(exact_sample["delta"], 3),
                            "exact_separation": round(exact_sample["separation"], 3),
                            "daily_degrees": self._build_daily_orb_rows(
                                planet=planet,
                                aspect_angle=aspect_angle,
                                start_utc=interval["start_utc"],
                                end_utc=interval["end_utc"],
                                lat=lat,
                                lon=lon,
                                timezone_offset=timezone_offset,
                            ),
                        }
                    )

        windows.sort(key=lambda item: item["start_time_utc"])
        return windows

    def _sample_lunar_cycle_positions(
        self,
        start_utc: datetime,
        end_utc: datetime,
        lat: float,
        lon: float,
    ) -> list[Dict[str, Any]]:
        samples: list[Dict[str, Any]] = []
        tracked_planets = set(LUNAR_RETURN_WINDOW_PLANETS)
        tracked_planets.add(Planet.MOON)
        cursor = start_utc

        while cursor <= end_utc:
            chart = self.engine.calculate_chart(cursor, lat, lon)
            positions = {
                planet: self._absolute_longitude(info)
                for planet, info in getattr(chart, "planets", {}).items()
                if planet in tracked_planets
            }
            samples.append({"timestamp_utc": cursor, "positions": positions})
            cursor += timedelta(hours=1)

        if not samples or samples[-1]["timestamp_utc"] < end_utc:
            chart = self.engine.calculate_chart(end_utc, lat, lon)
            positions = {
                planet: self._absolute_longitude(info)
                for planet, info in getattr(chart, "planets", {}).items()
                if planet in tracked_planets
            }
            samples.append({"timestamp_utc": end_utc, "positions": positions})

        return samples

    def _extract_orb_intervals(
        self,
        series: list[Dict[str, Any]],
        threshold: float,
    ) -> list[Dict[str, Any]]:
        intervals: list[Dict[str, Any]] = []
        start_index: Optional[int] = None

        for index, item in enumerate(series):
            is_active = item["delta"] <= threshold
            if is_active and start_index is None:
                start_index = index
                continue
            if not is_active and start_index is not None:
                intervals.append(
                    {
                        "start_utc": series[start_index]["timestamp_utc"],
                        "end_utc": series[index - 1]["timestamp_utc"],
                        "samples": series[start_index:index],
                    }
                )
                start_index = None

        if start_index is not None:
            intervals.append(
                {
                    "start_utc": series[start_index]["timestamp_utc"],
                    "end_utc": series[-1]["timestamp_utc"],
                    "samples": series[start_index:],
                }
            )

        return intervals

    def _build_daily_orb_rows(
        self,
        planet: Planet,
        aspect_angle: float,
        start_utc: datetime,
        end_utc: datetime,
        lat: float,
        lon: float,
        timezone_offset: float,
    ) -> list[Dict[str, Any]]:
        rows: list[Dict[str, Any]] = []
        local_start = start_utc + timedelta(hours=timezone_offset)
        local_end = end_utc + timedelta(hours=timezone_offset)
        day_cursor = local_start.date()
        end_date = local_end.date()

        while day_cursor <= end_date:
            best: Optional[Dict[str, Any]] = None
            for hour in range(24):
                candidate_local = datetime.combine(day_cursor, datetime.min.time()) + timedelta(hours=hour)
                candidate_utc = candidate_local - timedelta(hours=timezone_offset)
                if candidate_utc < start_utc or candidate_utc > end_utc:
                    continue
                chart = self.engine.calculate_chart(candidate_utc, lat, lon)
                moon = chart.get_planet_info(Planet.MOON)
                target = chart.get_planet_info(planet)
                if not moon or not target:
                    continue
                separation = deg_diff(self._absolute_longitude(moon), self._absolute_longitude(target))
                delta = abs(separation - aspect_angle)
                item = {
                    "date": day_cursor.isoformat(),
                    "time_local": candidate_local.isoformat(),
                    "time_utc": candidate_utc.isoformat(),
                    "orb": round(delta, 3),
                    "separation": round(separation, 3),
                }
                if best is None or item["orb"] < best["orb"]:
                    best = item
            if best:
                rows.append(best)
            day_cursor += timedelta(days=1)

        return rows
