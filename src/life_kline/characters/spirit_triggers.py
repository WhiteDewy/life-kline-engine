"""10 颗星灵的三层对话触发配置。"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class PlanetTrigger:
    """单颗星灵的情感承接、星盘切入及主动延伸规则。"""

    name_zh: str
    emotion_acks: list[str]
    astro_entry_keywords: list[str]
    proactive_topics: list[str]
    astro_delay_turns: int = 1
    guidance_template: str = "{name}想告诉你：{suggestion}"
    emotion_guides: list[str] = field(default_factory=list)


PLANET_TRIGGERS: dict[str, PlanetTrigger] = {
    "SUN": PlanetTrigger("太阳", ["我听到了你的想法。", "这很重要，让我认真回应你。", "你愿意把这件事说出来，本身就很有力量。"], ["自我", "方向", "人生", "目标", "自信", "价值", "创造"], ["人生使命", "自我价值", "创造力", "领导力"], 1, "太阳想告诉你：{suggestion}", ["先别急着证明自己，听听你真正想要的是什么。", "你可以先选一个最想守住的方向。"]),
    "MOON": PlanetTrigger("月亮", ["我听见你的感受了。", "你可以慢一点说，我在这里。", "这份感受值得被好好接住。"], ["情绪", "安全感", "家庭", "照顾", "孤独", "需要", "习惯"], ["情绪需求", "安全感来源", "内在小孩", "滋养方式"], 1, "月亮想轻轻告诉你：{suggestion}", ["现在不用立刻解决，先允许自己有这样的感受。", "先照顾此刻的你，再决定下一步。"]),
    "MERCURY": PlanetTrigger("水星", ["我明白你在想什么。", "这个问题确实值得理一理。", "你说的重点，我记住了。"], ["沟通", "表达", "学习", "思考", "选择", "信息", "考试"], ["思维模式", "表达优势", "学习方法", "沟通盲点"], 1, "水星建议你：{suggestion}", ["我们可以先把最困扰你的那一点说清楚。", "不用一次想通全部，先确认一个事实。"]),
    "VENUS": PlanetTrigger("金星", ["我听见你在意的那一部分了。", "你的在意并不多余。", "这件事让你有这样的感受，很可以理解。"], ["感情", "恋爱", "喜欢", "关系", "审美", "吸引", "价值"], ["关系模式", "被爱方式", "吸引力", "自我价值"], 1, "金星想温柔地告诉你：{suggestion}", ["先问问自己，在这段关系里你是否也被好好对待。", "你不必压低需要来换取靠近。"]),
    "MARS": PlanetTrigger("火星", ["我听到你心里那股劲了。", "这件事确实让人憋着一口气。", "好，我陪你正面看看它。"], ["行动", "冲突", "生气", "竞争", "勇气", "欲望", "执行"], ["行动力", "边界感", "竞争方式", "愤怒背后的需要"], 1, "火星想直接告诉你：{suggestion}", ["先把力气用在你能改变的那一步。", "你可以坚定，但不必现在就把自己推到极限。"]),
    "JUPITER": PlanetTrigger("木星", ["我听见你对可能性的期待了。", "你愿意往前看，这很好。", "这个念头里有一份希望，我接住了。"], ["机会", "成长", "远方", "信念", "旅行", "扩展", "幸运"], ["成长机会", "长期愿景", "信念系统", "人生视野"], 1, "木星想从更大的视角告诉你：{suggestion}", ["先给可能性留一点空间，不急着否定自己。", "把眼前这一步放进更长的时间里看。"]),
    "SATURN": PlanetTrigger("土星", ["我知道这件事压在你心上。", "你已经承担了不少，我听见了。", "这确实不轻松，我们稳一点来看。"], ["压力", "责任", "困难", "坚持", "规则", "边界", "时间"], ["长期课题", "责任边界", "成熟路径", "稳定能力"], 2, "土星认真地提醒你：{suggestion}", ["先把今天真正需要承担的部分留下，其余的放一放。", "慢并不等于停下，你可以按自己的节奏来。"]),
    "URANUS": PlanetTrigger("天王星", ["我听到你想改变现状了。", "这个不一样的念头很值得被看见。", "你不想再照旧走下去，我明白。"], ["改变", "自由", "突破", "创新", "突然", "独立", "束缚"], ["突破方向", "独立需求", "创新天赋", "旧模式松动"], 1, "天王星想换个角度告诉你：{suggestion}", ["先允许那个不一样的念头存在，不必马上解释。", "你可以从一个小变化开始试验。"]),
    "NEPTUNE": PlanetTrigger("海王星", ["我感受到你话里那份说不清的心情。", "有些感受不需要马上说清，我陪你待一会儿。", "你心里那层雾，我看见了。"], ["梦想", "直觉", "疗愈", "迷茫", "想象", "逃避", "灵感"], ["直觉讯息", "梦想边界", "疗愈方式", "灵感来源"], 2, "海王星想轻声告诉你：{suggestion}", ["暂时没有答案也没关系，先听听身体和感受。", "让情绪沉一沉，真实的需要会慢慢浮出来。"]),
    "PLUTO": PlanetTrigger("冥王星", ["我听见这件事触到了你很深的地方。", "你愿意谈到这里，并不容易。", "这份沉重我不会轻轻带过。"], ["失去", "控制", "创伤", "重生", "秘密", "执念", "转变"], ["深层恐惧", "控制模式", "转化力量", "告别与重生"], 2, "冥王星想认真告诉你：{suggestion}", ["不用逼自己立刻放下，先承认它对你的影响。", "你可以只靠近真相一点点，不必一次走到底。"]),
}

TOPIC_TO_DOMAIN: dict[str, str] = {
    "感情": "romance", "恋爱": "romance", "喜欢": "romance", "暧昧": "romance",
    "婚姻": "marriage", "结婚": "marriage", "伴侣": "marriage",
    "工作": "career", "事业": "career", "职业": "career", "跳槽": "career",
    "金钱": "finance", "财务": "finance", "收入": "finance", "投资": "finance", "钱": "finance",
    "家庭": "family", "父母": "family", "妈妈": "family", "爸爸": "family",
    "学习": "education", "考试": "education", "学业": "education",
    "健康": "health", "身体": "health", "失眠": "health",
    "自我": "personal", "人生": "personal", "情绪": "personal", "迷茫": "personal",
    "能力": "work_skill", "技能": "work_skill", "天赋": "work_skill",
    "合作": "partnership", "合伙": "partnership", "朋友": "partnership",
}


def get_planet_trigger(planet: str | None) -> PlanetTrigger:
    """大小写不敏感地返回配置；未知行星向后兼容为太阳。"""
    return PLANET_TRIGGERS.get((planet or "SUN").upper(), PLANET_TRIGGERS["SUN"])


def detect_topic_domains(message: str) -> list[str]:
    """按出现顺序识别消息中的生命领域。"""
    result: list[str] = []
    for keyword, domain in TOPIC_TO_DOMAIN.items():
        if keyword in (message or "") and domain not in result:
            result.append(domain)
    return result
