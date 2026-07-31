"""Build complete, structured star-spirit dossiers from engine-owned report data.

Every engine-computed fact that lives in the report JSON is eligible for
inclusion here. The dossier is the *single source of truth* for what a
star-spirit knows about itself in a consultation.
"""
from __future__ import annotations

from typing import Any

from life_kline.domains.helpers import plabel
from life_kline.engine_astrologer import ChartReader

from .models import (
    ChartEvidence,
    EvidenceSource,
    SpiritDossier,
    StructureTopic,
    stable_evidence_id,
)

# ── 古占尊贵细分 ──
_DIGNITY_DEEP_LABELS: dict[str, str] = {
    "triplicity_lord": "三分主星",
    "term_lord": "界主星",
    "face_lord": "面主星",
    "combust": "燃烧",
    "cazimi": "日核",
    "oriental": "东出",
    "occidental": "西入",
    "hayz": "喜乐",
    "in_joy": "喜乐宫",
}

# ── 格局中文标签 ──
_ASPECT_PATTERN_LABELS: dict[str, str] = {
    "grand_trine": "大三角",
    "t_square": "T三角",
    "grand_cross": "大十字",
    "kite": "风筝",
}

_ENCLOSURE_LABELS: dict[str, str] = {
    "benefic_enclosure": "吉星夹辅",
    "malefic_siege": "凶星夹制",
    "mixed_enclosure": "吉凶夹",
}

_FLYSTAR_DIMENSIONS: dict[str, str] = {
    "dignity_score": "尊贵",
    "aspect_score": "相位",
    "reception_score": "接纳",
    "house_score": "宫位",
    "special_score": "特殊",
}


_DIGNITY_OPTIONS: dict[str, list[str]] = {
    "domicile": ["这股力量通常表达得直接自然", "也可能因为太熟悉而不容易察觉自己的影响"],
    "exaltation": ["这股力量容易被放大或寄予期待", "有时会先追求理想状态，再处理现实细节"],
    "detriment": ["这股力量可能需要借助关系或环境才能顺畅表达", "也可能发展出不同于常规的处理方式"],
    "fall": ["这股力量可能先以敏感、笨拙或反复试错出现", "它也可能成为你最愿意认真练习的能力"],
    "peregrine": ["这股力量会随场景而变化", "它可能需要其他结构支持后才更稳定"],
}


def _evidence(
    source: EvidenceSource,
    title: str,
    fact: str,
    payload: dict[str, Any],
    *,
    importance: int,
    current: bool = False,
    supportive: bool | None = None,
) -> ChartEvidence:
    return ChartEvidence(
        evidence_id=stable_evidence_id(source, payload),
        source=source,
        title=title,
        fact=fact,
        payload=payload,
        importance=importance,
        current=current,
        supportive=supportive,
    )


def _today_payload(today_spirit: Any) -> dict[str, Any]:
    if today_spirit is None:
        return {}
    if hasattr(today_spirit, "to_dict"):
        return dict(today_spirit.to_dict())
    if isinstance(today_spirit, dict):
        return dict(today_spirit)
    return {}


def _firdaria_payload(period: Any) -> dict[str, Any]:
    if period is None:
        return {}
    if isinstance(period, dict):
        return dict(period)
    major = getattr(period, "major_lord", None)
    minor = getattr(period, "minor_lord", None)
    return {
        "major_lord": getattr(major, "value", major) or "",
        "minor_lord": getattr(minor, "value", minor) or "",
        "start_age": getattr(period, "start_age", None),
        "end_age": getattr(period, "end_age", None),
    }


def build_spirit_dossier(
    report_data: dict[str, Any],
    planet: str,
    *,
    today_spirit: Any = None,
    firdaria_period: Any = None,
    entry_context: dict[str, Any] | None = None,
) -> SpiritDossier:
    """Create a complete topic map for one planet without using the LLM."""
    planet_key = planet.upper()
    reader = ChartReader(report_data)
    profile = reader.read_planet_profile(planet_key)
    if not profile:
        raise ValueError(f"报告中缺少 {planet_key} 的行星角色数据")

    persona = profile.get("persona") or {}
    spirit_name = str(persona.get("name_zh") or plabel(planet_key))
    archetype = str(persona.get("archetype_zh") or "")
    evidence: list[ChartEvidence] = []

    placement_payload = {
        "planet": planet_key,
        "sign": profile.get("sign", ""),
        "sign_label": profile.get("sign_label", ""),
        "house": profile.get("house", 0),
        "house_label": profile.get("house_label", ""),
        "role_tag": profile.get("role_tag", ""),
        "is_chart_ruler": bool(profile.get("is_chart_ruler", False)),
    }
    placement_fact = (
        f"{spirit_name}落在{placement_payload['sign_label']}第{placement_payload['house']}宫"
        f"「{placement_payload['house_label']}」"
    )
    placement_ev = _evidence(
        EvidenceSource.NATAL_PLACEMENT,
        "落座与落宫",
        placement_fact,
        placement_payload,
        importance=95,
    )
    evidence.append(placement_ev)

    dignity_payload = {
        "planet": planet_key,
        "dignity_code": profile.get("dignity_code", "peregrine"),
        "dignity_label": profile.get("dignity_label", "平常"),
        "core_strength": profile.get("core_strength", 50),
        "breakdown": (
            report_data.get("_analysis_evidence", {})
            .get("dignity_breakdown", {})
            .get(planet_key, {})
        ),
    }
    dignity_ev = _evidence(
        EvidenceSource.NATAL_DIGNITY,
        "力量状态",
        f"{spirit_name}的尊贵状态是{dignity_payload['dignity_label']}",
        dignity_payload,
        importance=80,
        supportive=dignity_payload["dignity_code"] in {"domicile", "exaltation"},
    )
    evidence.append(dignity_ev)

    rulership_ids: list[str] = []
    rulerships = reader.read_rulerships(planet_key)
    for item in rulerships:
        payload = {"planet": planet_key, **item}
        fact = (
            f"{spirit_name}掌管第{item.get('house', 0)}宫"
            f"「{item.get('house_title', '')}」"
        )
        ev = _evidence(
            EvidenceSource.NATAL_RULERSHIP,
            "掌宫",
            fact,
            payload,
            importance=90,
        )
        evidence.append(ev)
        rulership_ids.append(ev.evidence_id)

    flystar_ids: list[str] = []
    for item in reader.read_flystars(planet_key):
        payload = {"planet": planet_key, **item}
        fact = (
            f"第{item.get('from_house', 0)}宫主星{spirit_name}飞入"
            f"第{item.get('to_house', 0)}宫「{item.get('to_house_title', '')}」"
        )
        ev = _evidence(
            EvidenceSource.NATAL_FLYSTAR,
            "飞星链",
            fact,
            payload,
            importance=88,
            supportive={"fortunate": True, "afflicted": False}.get(
                item.get("fortune_level")
            ),
        )
        evidence.append(ev)
        flystar_ids.append(ev.evidence_id)

    aspect_ids: list[str] = []
    for item in reader.read_aspects(planet_key).get("planet_aspects", []):
        payload = {"planet": planet_key, **item}
        ev = _evidence(
            EvidenceSource.NATAL_ASPECT,
            "主要相位",
            str(item.get("title") or item.get("summary") or "相位关系"),
            payload,
            importance=75 + int(float(item.get("strength", 0)) * 10),
            supportive={"supportive": True, "challenging": False}.get(item.get("nature")),
        )
        evidence.append(ev)
        aspect_ids.append(ev.evidence_id)

    reception_ids: list[str] = []
    receptions = reader.read_receptions(planet_key)
    for kind in ("received", "hosting", "mutuals"):
        for item in receptions.get(kind, []):
            payload = {"planet": planet_key, "kind": kind, **item}
            ev = _evidence(
                EvidenceSource.NATAL_RECEPTION,
                "互溶接纳" if kind == "mutuals" else "接纳关系",
                str(item.get("line") or item.get("summary") or "接纳关系"),
                payload,
                importance=82 if kind == "mutuals" else 70,
                supportive=True,
            )
            evidence.append(ev)
            reception_ids.append(ev.evidence_id)

    timing_ids: list[str] = []
    today = _today_payload(today_spirit)
    if today and str(today.get("planet", "")).upper() == planet_key:
        payload = {
            "planet": planet_key,
            "trigger_type": today.get("trigger_type", "default"),
            "reason": today.get("reason", ""),
            "confidence": today.get("confidence", 0),
            "trigger_evidence": today.get("trigger_evidence", []),
            "transit_aspect": today.get("transit_aspect"),
        }
        ev = _evidence(
            EvidenceSource.TODAY_ACTIVATION,
            "今日触发",
            str(today.get("reason") or f"今天由{spirit_name}引路"),
            payload,
            importance=100,
            current=True,
        )
        evidence.append(ev)
        timing_ids.append(ev.evidence_id)

    firdaria = _firdaria_payload(firdaria_period)
    major = str(firdaria.get("major_lord", "")).upper()
    minor = str(firdaria.get("minor_lord", "")).upper()
    if planet_key in {major, minor}:
        role = "主运星" if planet_key == major else "子运星"
        payload = {"planet": planet_key, "role": role, **firdaria}
        ev = _evidence(
            EvidenceSource.FIRDARIA,
            "当前法达",
            f"{spirit_name}是当前法达的{role}",
            payload,
            importance=85,
            current=True,
        )
        evidence.append(ev)
        timing_ids.append(ev.evidence_id)

    domain_ids: list[str] = []
    linked_domains = list(profile.get("linked_domains") or [])
    requested_domain = str((entry_context or {}).get("domain") or "")
    if requested_domain and requested_domain not in linked_domains:
        linked_domains.insert(0, requested_domain)
    for domain_key in linked_domains[:4]:
        domain = reader.read_domain(domain_key)
        domain_label = str(domain.get("domain_label") or domain_key)
        if not domain.get("core_theme"):
            continue
        payload = {"planet": planet_key, "domain": domain_key, **domain}
        ev = _evidence(
            EvidenceSource.DOMAIN_REPORT,
            domain_label,
            str(domain.get("core_theme")),
            payload,
            importance=65,
        )
        evidence.append(ev)
        domain_ids.append(ev.evidence_id)

    topics = _build_topics(
        profile=profile,
        placement_id=placement_ev.evidence_id,
        dignity_id=dignity_ev.evidence_id,
        rulership_ids=rulership_ids,
        flystar_ids=flystar_ids,
        aspect_ids=aspect_ids,
        reception_ids=reception_ids,
        timing_ids=timing_ids,
        domain_ids=domain_ids,
    )

    entry_source = str((entry_context or {}).get("source") or "")
    is_today = bool(timing_ids) and (
        entry_source in {"today_star_spirit", "transit", "daily_question"}
        or str(today.get("planet", "")).upper() == planet_key
    )
    preferred = (
        ["timing", "placement", "rulership", "dignity", "aspects", "receptions", "domains"]
        if is_today
        else ["placement", "rulership", "dignity", "aspects", "receptions", "timing", "domains"]
    )
        # -- enrich from all engine data sources --
    from .dossier_enrich import (
        enrich_dignity_deep, enrich_aspect_patterns, enrich_enclosures,
        enrich_flystar_details, enrich_transits, enrich_interceptions,
        enrich_hero_context,
    )
    evidence = enrich_dignity_deep(report_data, planet_key, evidence)
    evidence = enrich_aspect_patterns(report_data, planet_key, evidence)
    evidence = enrich_enclosures(report_data, planet_key, evidence)
    evidence = enrich_flystar_details(report_data, planet_key, evidence)
    evidence = enrich_transits(report_data, planet_key, evidence)
    evidence = enrich_interceptions(report_data, planet_key, evidence)
    evidence = enrich_hero_context(report_data, planet_key, evidence)

    available = {item.key for item in topics}
    topic_order = [key for key in preferred if key in available]

    identity = (
        f"我是你的{spirit_name}"
        f"——{archetype or '内在行星力量'}。我不是外来的神，我就是你的一部分。"
    )
    return SpiritDossier(
        planet=planet_key,
        spirit_name=spirit_name,
        archetype=archetype,
        identity_statement=identity,
        profile=profile,
        evidence=sorted(evidence, key=lambda item: item.importance, reverse=True),
        topics=topics,
        topic_order=topic_order,
        entry_mode="today" if is_today else "natal",
        today_trigger_type=str(today.get("trigger_type", "")) if is_today else "",
    )


def _build_topics(
    *,
    profile: dict[str, Any],
    placement_id: str,
    dignity_id: str,
    rulership_ids: list[str],
    flystar_ids: list[str],
    aspect_ids: list[str],
    reception_ids: list[str],
    timing_ids: list[str],
    domain_ids: list[str],
) -> list[StructureTopic]:
    house_label = str(profile.get("house_label") or "这个人生领域")
    sign_label = str(profile.get("sign_label") or "这个星座")
    dignity_code = str(profile.get("dignity_code") or "peregrine")
    linked_domains = list(profile.get("linked_domains") or [])

    topics = [
        StructureTopic(
            key="placement",
            title="我在哪里行动",
            summary=f"{sign_label} · {house_label}",
            evidence_ids=[placement_id],
            interpretation_options=[
                f"这股力量可能先在{house_label}的具体经历里被你感受到",
                f"也可能通过{sign_label}的处理方式影响你的反应节奏",
            ],
            inquiry_question=(
                f"先不急着判断对不对。最近一次你在{house_label}里有明显反应，"
                "当时具体发生了什么？"
            ),
            domain_tags=linked_domains,
        ),
        StructureTopic(
            key="dignity",
            title="我的力量怎样运作",
            summary=str(profile.get("dignity_label") or "平常"),
            evidence_ids=[dignity_id],
            interpretation_options=_DIGNITY_OPTIONS.get(
                dignity_code,
                _DIGNITY_OPTIONS["peregrine"],
            ),
            inquiry_question=(
                "在这类事情里，你更常感到这股力量很自然，还是需要绕一下、练一下才用得出来？"
            ),
            domain_tags=linked_domains,
        ),
    ]

    if rulership_ids or flystar_ids:
        topics.append(
            StructureTopic(
                key="rulership",
                title="我从哪里飞来，又把事情带向哪里",
                summary="掌宫与飞星链",
                evidence_ids=rulership_ids + flystar_ids,
                interpretation_options=[
                    "一个领域发生的事，可能会在另一个领域看到结果",
                    "同一条链也可能表现为资源互相支持，或问题彼此牵动",
                ],
                inquiry_question=(
                    "回看最近一次相关经历：事情开始的领域，和最后真正受影响的领域，是同一个吗？"
                ),
                domain_tags=linked_domains,
            )
        )
    if aspect_ids:
        topics.append(
            StructureTopic(
                key="aspects",
                title="谁在推动我，谁在和我拉扯",
                summary=f"{len(aspect_ids)} 条主要相位",
                evidence_ids=aspect_ids,
                interpretation_options=[
                    "相位可能表现为两股需要协调的内在动力",
                    "也可能通过关系、事件或反复出现的选择被看见",
                ],
                inquiry_question="这些拉扯更常发生在你心里，还是会通过某类关系或具体事件出现？",
                domain_tags=linked_domains,
                subtopic_keys=[f"aspect:{item}" for item in aspect_ids],
            )
        )
    if reception_ids:
        topics.append(
            StructureTopic(
                key="receptions",
                title="我怎样获得支持与交换资源",
                summary=f"{len(reception_ids)} 条接纳关系",
                evidence_ids=reception_ids,
                interpretation_options=[
                    "这可能表现为一股力量替另一股力量提供资源",
                    "也可能出现有条件的支持、交换或彼此牵制",
                ],
                inquiry_question="现实里你更像是在接受帮助、提供帮助，还是双方一直在交换条件？",
                domain_tags=linked_domains,
            )
        )
    if timing_ids:
        topics.append(
            StructureTopic(
                key="timing",
                title="为什么现在轮到我说话",
                summary="今日行运与当前法达",
                evidence_ids=timing_ids,
                interpretation_options=[
                    "今天的触发可能让原有主题更容易被你感受到",
                    "它也可能只是一段背景，需要结合现实事件再判断",
                ],
                inquiry_question="从今天或最近几天看，什么具体事情让这个主题突然变得更明显？",
                domain_tags=linked_domains,
            )
        )
    if domain_ids:
        topics.append(
            StructureTopic(
                key="domains",
                title="这条结构落到哪些生活领域",
                summary="报告领域联动",
                evidence_ids=domain_ids,
                interpretation_options=[
                    "同一结构在不同领域可能呈现不同侧面",
                    "它也可能只在某个阶段集中出现在一个领域",
                ],
                inquiry_question="这些领域里，哪一个现在最有具体事件，也最值得我们先验证？",
                domain_tags=linked_domains,
            )
        )
    return topics


def match_topic(dossier: SpiritDossier, text: str) -> str:
    """Route explicit user questions to a dossier topic; keep current on ambiguity."""
    normalized = text.strip()
    if not normalized:
        return ""
    available = set(dossier.topic_order)
    if (
        "行运" in normalized
        and "有没有" in normalized
        and "timing" in available
    ):
        return "timing"
    keyword_map = {
        "timing": ("今天", "最近", "现在", "行运", "法达", "什么时候", "为何是", "被行运", "被触发", "运势"),
        "placement": ("落宫", "落座", "星座", "第几宫", "宫位", "落在"),
        "rulership": ("掌宫", "宫主", "飞星", "从哪", "结果", "掌管", "几个宫", "几宫主"),
        "dignity": ("尊贵", "入庙", "擢升", "失势", "落陷", "强不强", "弱不弱"),
        "aspects": ("相位", "合相", "对冲", "刑", "三合", "六合"),
        "receptions": ("接纳", "互溶", "谁帮助", "资源"),
        "domains": ("事业", "感情", "婚姻", "家庭", "财务", "学业", "健康", "伴侣", "关系", "麻将", "打牌", "游戏", "娱乐", "赢", "输"),
    }
    for key, keywords in keyword_map.items():
        if key in available and any(word in normalized for word in keywords):
            return key
    return ""
