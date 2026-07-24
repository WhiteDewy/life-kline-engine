"""
花园分类与抓手问题注册表 (Garden Catalog)

静态注册 7 大人生领域 + 运势专区，每个分类下包含具体抓手问题，
每个问题映射到对应的宫位和行星组合，供 ConsultationEngine 做问题锚定。

PRD v1.3 §10 — 星灵花园分析工具集
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# ── 数据类 ─────────────────────────────────────────────────

@dataclass
class QuestionItem:
    """单个抓手问题"""
    key: str
    label: str               # 用户看到的问题文本
    houses: list[int] = field(default_factory=list)   # 核心宫位
    planets: list[str] = field(default_factory=list)  # 核心行星
    secondary_houses: list[int] = field(default_factory=list)  # 次要宫位（全盘取像用）
    secondary_planets: list[str] = field(default_factory=list) # 次要行星
    description: str = ""     # 简短描述，星语者参考
    house_labels: dict[int, str] = field(default_factory=dict)  # 宫位→语境化标签


@dataclass
class CategoryDefinition:
    """单个分类定义"""
    key: str
    label: str
    icon: str
    description: str
    tradition_weight: float   # 古占权重 (0.0~1.0)
    questions: list[QuestionItem] = field(default_factory=list)


@dataclass
class FortuneItem:
    """运势区条目"""
    key: str
    label: str
    icon: str
    description: str
    route: str = ""           # 前端跳转路由
    status: str = "active"    # active | planned


# ── 7 大分类定义 ───────────────────────────────────────────

GARDEN_CATEGORIES: list[CategoryDefinition] = [
    # ── 🔮 自我探索 ─────────────────────────────────────
    CategoryDefinition(
        key="self",
        label="自我探索",
        icon="🔮",
        description="从星盘的核心结构出发，读懂你的性格底色、人生使命和灵魂课题。",
        tradition_weight=0.4,
        questions=[
            QuestionItem(
                key="who_am_i",
                label="我到底是个什么样的人？",
                houses=[1], planets=["SUN", "MOON", "CHART_RULER"],
                secondary_houses=[10, 4],
                secondary_planets=["MERCURY", "VENUS", "MARS"],
                description="三方综合：Sun（意志）+ Moon（情绪）+ ASC（人格面具）",
            ),
            QuestionItem(
                key="repeating_patterns",
                label="为什么我总是反复陷入同样的困境？",
                houses=[12, 8], planets=["SATURN", "CHART_RULER"],
                secondary_houses=[4],
                secondary_planets=["PLUTO", "MOON"],
                description="12宫业力 + 土星压制 + 固定星座执念",
            ),
            QuestionItem(
                key="greatest_gift",
                label="我最大的天赋是什么？为什么发挥不出来？",
                houses=[1, 5], planets=["SUN", "CHART_RULER"],
                secondary_houses=[10],
                secondary_planets=["JUPITER", "VENUS"],
                description="Sun尊贵 + 5宫创造力 + 相位阻碍分析",
            ),
            QuestionItem(
                key="feel_different",
                label="我在人群中为什么总感到格格不入？",
                houses=[1, 11], planets=["CHART_RULER", "URANUS"],
                secondary_houses=[3, 12],
                secondary_planets=["SATURN", "MERCURY"],
                description="ASC + 11宫社群 + 天王星/水瓶/天蝎孤星",
            ),
            QuestionItem(
                key="life_mission",
                label="我的人生使命到底是什么？",
                houses=[10, 9], planets=["SUN", "NORTH_NODE"],
                secondary_houses=[1],
                secondary_planets=["CHART_RULER", "SATURN"],
                description="北交点 + 10宫 + Sun定位链终点",
            ),
            QuestionItem(
                key="inner_conflict",
                label="我性格里最大的矛盾是什么？",
                houses=[1], planets=["SUN", "MOON"],
                secondary_houses=[4, 7, 10],
                secondary_planets=["MARS", "VENUS"],
                description="日月对冲/四分 + T三角顶点 + 定位链冲突",
            ),
            QuestionItem(
                key="past_lives",
                label="我的前世今生有什么业力课题？",
                houses=[12, 4, 8], planets=["SATURN", "SOUTH_NODE"],
                secondary_houses=[1],
                secondary_planets=["PLUTO", "MOON", "CHART_RULER"],
                description="12宫 + 南交点 + 土星 + 冥王星",
            ),
        ],
    ),

    # ── 💕 感情花园 (试点分类) ──────────────────────────
    CategoryDefinition(
        key="love",
        label="感情花园",
        icon="💕",
        description="探索你的感情模式、桃花运势、正缘画像，用星盘读懂你在关系中的样子。",
        tradition_weight=0.3,
        questions=[
            QuestionItem(
                key="love_pattern",
                label="我的感情模式为什么总是重复？",
                houses=[5, 7, 1], planets=["VENUS", "MARS", "MOON"],
                secondary_houses=[8, 12],
                secondary_planets=["SATURN", "PLUTO"],
                description="Venus落座落宫 + 7宫主 + 金星相位 + 全盘结构下的情感稀缺度",
                house_labels={5: "恋爱方式", 7: "关系契约", 1: "自我风格"},
            ),
            QuestionItem(
                key="when_meet",
                label="我什么时候能遇到对的人？",
                houses=[7, 5], planets=["VENUS", "JUPITER"],
                secondary_houses=[1],
                secondary_planets=["CHART_RULER", "MARS"],
                description="7宫主行运 + 法达金星/7宫主周期 + Jupiter行运触发",
                house_labels={7: "伴侣时机", 5: "桃花窗口"},
            ),
            QuestionItem(
                key="does_he_like_me",
                label="TA到底喜不喜欢我？",
                houses=[7, 5], planets=["VENUS", "MARS"],
                secondary_houses=[1, 8],
                secondary_planets=["MOON", "MERCURY"],
                description="比较盘分析（synastry引擎）+ 下降点匹配",
                house_labels={7: "对方信号", 5: "吸引力互动"},
            ),
            QuestionItem(
                key="compatibility",
                label="我们真的合适吗？",
                houses=[7, 1], planets=["VENUS", "CHART_RULER"],
                secondary_houses=[4, 10],
                secondary_planets=["MOON", "SATURN", "MARS"],
                description="日月互动 + 下降点匹配 + 7H-1H轴线 + 月亮安全感兼容",
                house_labels={7: "关系匹配", 1: "自我需求"},
            ),
            QuestionItem(
                key="letting_go",
                label="怎样才能真正放下一个人？",
                houses=[8, 12], planets=["VENUS", "PLUTO"],
                secondary_houses=[5],
                secondary_planets=["MOON", "SATURN"],
                description="8宫执念 + 冥王星 + 天蝎/金牛轴线 + 土星时间药方",
                house_labels={8: "执念转化", 12: "业力释放"},
            ),
            QuestionItem(
                key="peach_blossom",
                label="我的桃花运怎么样？",
                houses=[5, 7], planets=["VENUS", "JUPITER"],
                secondary_houses=[1, 11],
                secondary_planets=["MARS", "URANUS"],
                description="5宫 + Venus + 行运Jupiter触达 + 11宫社交桃花",
                house_labels={5: "恋爱机遇", 7: "关系走向", 11: "社交圈"},
            ),
            QuestionItem(
                key="true_love",
                label="什么样的人才是我真正的正缘？",
                houses=[7], planets=["VENUS", "CHART_RULER"],
                secondary_houses=[1, 4, 5],
                secondary_planets=["JUPITER", "SATURN", "MOON"],
                description="7宫主 + 下降点 + 本命Venus/Jupiter相位 + 金星定位链",
                house_labels={7: "长期契约"},
            ),
        ],
    ),

    # ── 💼 事业罗盘 ─────────────────────────────────────
    CategoryDefinition(
        key="career",
        label="事业罗盘",
        icon="💼",
        description="找到你的职业方向、职场优势和发展时机，让星盘为你的事业导航。",
        tradition_weight=0.6,
        questions=[
            QuestionItem(
                key="career_direction",
                label="我适合做什么工作？",
                houses=[10, 6, 2], planets=["SATURN", "MARS"],
                secondary_houses=[1],
                secondary_planets=["SUN", "CHART_RULER", "MERCURY"],
                description="MC + 10宫主 + Saturn落宫 + 2宫收入来源 + 6宫日常工作",
            ),
            QuestionItem(
                key="workplace_struggle",
                label="为什么我在职场总是不顺？",
                houses=[6, 10], planets=["SATURN", "MARS"],
                secondary_houses=[3, 11],
                secondary_planets=["MERCURY", "CHART_RULER"],
                description="6宫同事/日常 + 10宫上级/方向 + 火星/土星压力",
            ),
            QuestionItem(
                key="jump_or_stay",
                label="我该跳槽还是留下？",
                houses=[10, 6], planets=["SATURN", "CHART_RULER"],
                secondary_houses=[2, 8],
                secondary_planets=["JUPITER", "URANUS"],
                description="法达当前周期 + 行运触发10宫/6宫 + Uranus变动机遇",
            ),
            QuestionItem(
                key="entrepreneurship",
                label="我适合创业当老板吗？",
                houses=[1, 10], planets=["SUN", "MARS", "SATURN"],
                secondary_houses=[7, 8],
                secondary_planets=["CHART_RULER", "JUPITER"],
                description="1宫主 + 10宫 + Saturn + 火/日领导力 + 7H/8H合伙资源",
            ),
            QuestionItem(
                key="career_change",
                label="我该不该转行？",
                houses=[10, 9, 3], planets=["SATURN", "JUPITER", "MERCURY"],
                secondary_houses=[6, 1],
                secondary_planets=["CHART_RULER", "URANUS"],
                description="法达换运 + 10宫主换座 + 本命多能力线",
            ),
            QuestionItem(
                key="hidden_talent",
                label="为什么我总感觉怀才不遇？",
                houses=[10, 1], planets=["SUN", "CHART_RULER"],
                secondary_houses=[12, 6],
                secondary_planets=["SATURN", "MARS"],
                description="Sun落陷 + 10宫主受克 + 发光体被压制 + 12宫隐藏",
            ),
        ],
    ),

    # ── 💰 财富密码 ─────────────────────────────────────
    CategoryDefinition(
        key="wealth",
        label="财富密码",
        icon="💰",
        description="解读你的财富蓝图、赚钱方式和价值感来源，让星盘照见你和金钱的关系。",
        tradition_weight=0.7,
        questions=[
            QuestionItem(
                key="cant_save",
                label="我为什么总是存不住钱？",
                houses=[2, 8], planets=["VENUS", "SATURN"],
                secondary_houses=[5, 6],
                secondary_planets=["MOON", "JUPITER"],
                description="2宫主 + 8宫负债/共享 + Venus消费 + Saturn紧缩",
            ),
            QuestionItem(
                key="how_to_earn",
                label="我该通过什么方式赚钱？",
                houses=[2, 6, 10], planets=["CHART_RULER", "SATURN"],
                secondary_houses=[5, 8, 11],
                secondary_planets=["VENUS", "JUPITER", "MARS"],
                description="多宫位取像：2H正财/5H投机/8H偏财/10H事业财/11H大众财",
            ),
            QuestionItem(
                key="windfall_luck",
                label="我有偏财运吗？",
                houses=[8, 5], planets=["JUPITER", "VENUS"],
                secondary_houses=[2, 11],
                secondary_planets=["PLUTO", "URANUS"],
                description="8宫 + Jupiter + 5宫投机 + 11宫博彩/流量财",
            ),
            QuestionItem(
                key="invest_fit",
                label="我适合投资理财吗？",
                houses=[5, 8, 2], planets=["JUPITER", "MERCURY", "SATURN"],
                secondary_houses=[1],
                secondary_planets=["VENUS", "CHART_RULER"],
                description="5宫投机 vs 2宫储蓄 + Mercury判断力 + Jupiter运气",
            ),
            QuestionItem(
                key="money_psychology",
                label="为什么我总觉得钱不够？",
                houses=[2, 4], planets=["VENUS", "MOON"],
                secondary_houses=[8, 1],
                secondary_planets=["SATURN", "PLUTO"],
                description="2宫主受克 + Moon安全感 + 价值感议题 + 原生家庭金钱观",
            ),
        ],
    ),

    # ── 📚 学业航道 ─────────────────────────────────────
    CategoryDefinition(
        key="education",
        label="学业航道",
        icon="📚",
        description="发现你的学习风格、考试优势和深造方向，用星盘优化你的学业路径。",
        tradition_weight=0.5,
        questions=[
            QuestionItem(
                key="exam_anxiety",
                label="为什么我一到考试就崩？",
                houses=[3, 9], planets=["MERCURY", "MOON"],
                secondary_houses=[6, 12],
                secondary_planets=["SATURN", "NEPTUNE"],
                description="Mercury受克 + 3宫焦虑 + Moon情绪 + Saturn压力",
            ),
            QuestionItem(
                key="study_or_work",
                label="我该考研还是去工作？",
                houses=[9, 10, 2], planets=["JUPITER", "SATURN"],
                secondary_houses=[3, 6],
                secondary_planets=["MERCURY", "CHART_RULER"],
                description="9宫 vs 10宫权重 + 法达当前周期 + 2宫收入现实",
            ),
            QuestionItem(
                key="wrong_major",
                label="我是不是选错了专业？",
                houses=[3, 9], planets=["MERCURY", "JUPITER"],
                secondary_houses=[10, 1],
                secondary_planets=["CHART_RULER", "SUN"],
                description="Mercury + 9宫主 + 3H-9H轴线 + 职业方向对比",
            ),
            QuestionItem(
                key="learning_style",
                label="我的学习方式到底哪里出了问题？",
                houses=[3], planets=["MERCURY", "MOON"],
                secondary_houses=[1, 6],
                secondary_planets=["SATURN", "CHART_RULER"],
                description="Mercury落座学习风格 + Saturn记忆力 + Moon情绪节奏",
            ),
            QuestionItem(
                key="study_abroad",
                label="我适合出国留学吗？",
                houses=[9, 4], planets=["JUPITER", "MOON"],
                secondary_houses=[3, 12],
                secondary_planets=["VENUS", "NEPTUNE"],
                description="9宫 + Jupiter + 4H-9H迁移线 + 12宫远行适应力",
            ),
        ],
    ),

    # ── 🏠 家庭根系 ─────────────────────────────────────
    CategoryDefinition(
        key="family",
        label="家庭根系",
        icon="🏠",
        description="理解原生家庭的影响、父母关系和亲子连结，用星盘读懂你的家族模式。",
        tradition_weight=0.6,
        questions=[
            QuestionItem(
                key="family_of_origin",
                label="原生家庭如何影响了我？",
                houses=[4, 10], planets=["MOON", "SATURN", "SUN"],
                secondary_houses=[1, 12],
                secondary_planets=["CHART_RULER", "PLUTO"],
                description="4宫 + IC + Moon + Saturn父/Moon母 + 家族业力",
            ),
            QuestionItem(
                key="parent_relationship",
                label="我和父母的关系怎么改善？",
                houses=[4, 10], planets=["SUN", "MOON", "SATURN"],
                secondary_houses=[1, 7],
                secondary_planets=["VENUS", "CHART_RULER"],
                description="Sun-Saturn(父) + Moon-Venus(母) + 4H-10H轴线",
            ),
            QuestionItem(
                key="should_have_kids",
                label="我适合要孩子吗？",
                houses=[5], planets=["MOON", "JUPITER"],
                secondary_houses=[1, 4],
                secondary_planets=["VENUS", "MARS"],
                description="5宫 + 子女征象 + 法达生育周期 + 月亮滋养力",
            ),
            QuestionItem(
                key="understand_my_child",
                label="如何理解我的孩子的天性？",
                houses=[5], planets=["MOON", "MERCURY"],
                secondary_houses=[1, 3],
                secondary_planets=["SUN", "CHART_RULER"],
                description="5宫主 + 行运触发子女议题 + 月亮接纳力",
            ),
            QuestionItem(
                key="family_karma",
                label="家族的业力模式是什么？",
                houses=[4, 12, 8], planets=["PLUTO", "SATURN", "MOON"],
                secondary_houses=[1],
                secondary_planets=["SOUTH_NODE", "CHART_RULER"],
                description="4宫 + 12宫 + Pluto + 南交点 + 家族重复模式",
            ),
        ],
    ),

    # ── 🩺 健康星图 ─────────────────────────────────────
    CategoryDefinition(
        key="health",
        label="健康星图",
        icon="🩺",
        description="从星盘看你的体质、精力节律和压力信号，找到最适合你的健康生活方式。",
        tradition_weight=0.7,
        questions=[
            QuestionItem(
                key="body_attention",
                label="我的身体最需要注意什么？",
                houses=[1, 6], planets=["CHART_RULER", "MARS", "SATURN"],
                secondary_houses=[8, 12],
                secondary_planets=["SUN", "MOON"],
                description="6宫 + 1宫主 + 上升 + Mars炎症/Saturn慢性",
            ),
            QuestionItem(
                key="always_tired",
                label="为什么我总是感觉很累？",
                houses=[6, 12], planets=["MARS", "MOON", "SATURN"],
                secondary_houses=[1, 4],
                secondary_planets=["NEPTUNE", "CHART_RULER"],
                description="Mars落陷/受克 + Saturn 6H + Moon情绪耗竭 + Neptune消散",
            ),
            QuestionItem(
                key="emotion_body_link",
                label="我的情绪和身体是什么关系？",
                houses=[6, 4, 12], planets=["MOON", "MARS"],
                secondary_houses=[1],
                secondary_planets=["SATURN", "CHART_RULER"],
                description="Moon落座 + 6宫主 + 4H-6H连结 + 心身映射",
            ),
            QuestionItem(
                key="best_lifestyle",
                label="什么样的生活方式最适合我？",
                houses=[1, 6], planets=["SUN", "MOON", "CHART_RULER"],
                secondary_houses=[5, 9],
                secondary_planets=["VENUS", "MARS", "JUPITER"],
                description="1宫主 + Sun + Moon阴阳平衡 + 元素体质 + Venus享受/Mars行动",
            ),
            QuestionItem(
                key="sleep_issues",
                label="我的睡眠为什么总出问题？",
                houses=[12, 6], planets=["MOON", "MERCURY"],
                secondary_houses=[1, 3],
                secondary_planets=["NEPTUNE", "SATURN"],
                description="Moon + 12宫 + Mercury思虑 + Neptune扰乱 + Saturn紧绷",
            ),
        ],
    ),
]

# ── 运势专区 ───────────────────────────────────────────────

FORTUNE_SECTION: list[FortuneItem] = [
    FortuneItem(
        key="weekly",
        label="周运",
        icon="📅",
        description="本周星象对你的影响与指引",
        status="active",
    ),
    FortuneItem(
        key="monthly",
        label="月运",
        icon="🌙",
        description="月返盘与本命盘的互动解读",
        status="active",
    ),
    FortuneItem(
        key="yearly",
        label="年运",
        icon="🌟",
        description="年度大运与小限的综合分析",
        status="planned",
    ),
    FortuneItem(
        key="firdaria",
        label="法达阶段",
        icon="⏳",
        description="当前法达周期的主题与机遇",
        status="active",
    ),
    FortuneItem(
        key="life_kline",
        label="人生K线",
        icon="📈",
        description="以OHLC模型呈现你的人生周期起伏",
        status="active",
    ),
]


# ── 便捷查询函数 ────────────────────────────────────────────

def get_all_categories() -> list[CategoryDefinition]:
    """返回所有分类"""
    return list(GARDEN_CATEGORIES)


def get_category(key: str) -> CategoryDefinition | None:
    """按 key 获取单个分类"""
    for cat in GARDEN_CATEGORIES:
        if cat.key == key:
            return cat
    return None


def get_question(category_key: str, question_key: str) -> QuestionItem | None:
    """获取指定分类下的单个问题"""
    cat = get_category(category_key)
    if not cat:
        return None
    for q in cat.questions:
        if q.key == question_key:
            return q
    return None


def get_question_by_label(category_key: str, label_fragment: str) -> QuestionItem | None:
    """按标签模糊匹配问题"""
    cat = get_category(category_key)
    if not cat:
        return None
    for q in cat.questions:
        if label_fragment in q.label:
            return q
    return None


def get_all_question_keys() -> dict[str, list[str]]:
    """返回所有分类→问题key的映射"""
    result: dict[str, list[str]] = {}
    for cat in GARDEN_CATEGORIES:
        result[cat.key] = [q.key for q in cat.questions]
    return result


def get_fortune_items() -> list[FortuneItem]:
    """返回运势区条目"""
    return list(FORTUNE_SECTION)


def to_dict() -> dict[str, Any]:
    """将完整注册表序列化为前端可用的 JSON"""
    return {
        "categories": [
            {
                "key": cat.key,
                "label": cat.label,
                "icon": cat.icon,
                "description": cat.description,
                "tradition_weight": cat.tradition_weight,
                "question_count": len(cat.questions),
                "questions": [
                    {
                        "key": q.key,
                        "label": q.label,
                        "houses": q.houses,
                        "planets": q.planets,
                        "secondary_houses": q.secondary_houses,
                        "secondary_planets": q.secondary_planets,
                        "description": q.description,
                        "house_labels": q.house_labels,
                    }
                    for q in cat.questions
                ],
            }
            for cat in GARDEN_CATEGORIES
        ],
        "fortune": [
            {
                "key": f.key,
                "label": f.label,
                "icon": f.icon,
                "description": f.description,
                "status": f.status,
            }
            for f in FORTUNE_SECTION
        ],
    }
