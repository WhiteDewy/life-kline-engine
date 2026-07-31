"""
test_guide_spirit_narrative.py — 引路星灵自述引擎单元测试

覆盖：
- 逆向宫主星计算（7 传统行星）
- 自守宫位（宫内星 == 宫主星）
- 4 种触发类型
- 外行星无传统守护
- 命主星标识
- 尊贵状态变化
- 边界情况
"""
from __future__ import annotations

import pytest

from life_kline.guide_spirit_narrative import (
    GuideSpiritNarrativeEngine,
    GuideSpiritNarrative,
    compute_planet_rulerships,
    compute_guide_narrative,
)
from life_kline.today_engine import TodayStarSpirit


# ═══════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════

@pytest.fixture
def standard_houses() -> list:
    """标准12宫头：每宫一个星座，从白羊到双鱼"""
    return [
        ("ARIES", 15.0),       # 1 → MARS
        ("TAURUS", 10.0),      # 2 → VENUS
        ("GEMINI", 5.0),       # 3 → MERCURY
        ("CANCER", 20.0),      # 4 → MOON
        ("LEO", 12.0),         # 5 → SUN
        ("VIRGO", 8.0),        # 6 → MERCURY
        ("LIBRA", 22.0),       # 7 → VENUS
        ("SCORPIO", 3.0),      # 8 → MARS
        ("SAGITTARIUS", 18.0), # 9 → JUPITER
        ("CAPRICORN", 7.0),    # 10 → SATURN
        ("AQUARIUS", 14.0),    # 11 → SATURN
        ("PISCES", 25.0),      # 12 → JUPITER
    ]


@pytest.fixture
def natal_chart(standard_houses: list) -> dict:
    return {"houses": standard_houses}


@pytest.fixture
def engine() -> GuideSpiritNarrativeEngine:
    return GuideSpiritNarrativeEngine()


# ═══════════════════════════════════════════════════════════════
# 逆向宫主星计算
# ═══════════════════════════════════════════════════════════════

class TestReverseRulership:
    def test_all_traditional_rulers(self, standard_houses: list):
        """每个传统行星的宫主星映射正确"""
        result = compute_planet_rulerships(standard_houses)
        assert result["SUN"] == [5]
        assert result["MOON"] == [4]
        assert result["MERCURY"] == [3, 6]
        assert result["VENUS"] == [2, 7]
        assert result["MARS"] == [1, 8]
        assert result["JUPITER"] == [9, 12]
        assert result["SATURN"] == [10, 11]

    def test_outer_planets_not_in_result(self):
        """三王星不在传统宫主星映射中"""
        houses = [("ARIES", 0.0)] * 12
        result = compute_planet_rulerships(houses)
        assert "URANUS" not in result
        assert "NEPTUNE" not in result
        assert "PLUTO" not in result

    def test_only_one_house_per_sign(self, standard_houses: list):
        """确保每个宫号只出现一次（没有重复映射）"""
        result = compute_planet_rulerships(standard_houses)
        all_houses = []
        for houses in result.values():
            all_houses.extend(houses)
        assert len(all_houses) == 12
        assert sorted(all_houses) == list(range(1, 13))

    def test_empty_houses(self):
        """空宫头列表不崩溃"""
        result = compute_planet_rulerships([])
        for planet, houses in result.items():
            assert houses == []

    def test_non_tuple_cusp_format(self):
        """兼容对象格式的宫头数据"""
        class MockCusp:
            def __init__(self, value):
                self.value = value

        houses = [MockCusp("ARIES")] * 12
        result = compute_planet_rulerships(houses)
        assert result["MARS"] == list(range(1, 13))


# ═══════════════════════════════════════════════════════════════
# 精准行运触发
# ═══════════════════════════════════════════════════════════════

class TestExactTransitTrigger:
    def test_venus_normal_case(self, natal_chart: dict, engine: GuideSpiritNarrativeEngine):
        """金星：宫主2+7，落7宫入庙 → 自守宫位 + 另一个宫"""
        spirit = TodayStarSpirit(
            planet="VENUS", planet_label="金星", symbol="♀",
            reason="行运金星合相你的本命太阳（orb 0.3°）——金星今天是你最强的引路星灵",
            confidence=94.0, sign="LIBRA", sign_label="天秤座",
            trigger_type="exact_transit",
            transit_aspect={
                "transiting_planet": "VENUS", "natal_planet": "SUN",
                "aspect_type": "CONJUNCTION", "aspect_label": "合相",
                "orb": 0.3, "strength": 0.97,
            },
        )
        planet_chars = {
            "VENUS": {
                "house": 7, "sign": "LIBRA", "sign_label": "天秤座",
                "dignity_code": "domicile", "dignity_label": "入庙",
                "is_chart_ruler": False,
            },
        }

        result = engine.compute(spirit, natal_chart, planet_chars)

        assert result.spirit_planet == "VENUS"
        assert result.trigger_type == "exact_transit"
        assert result.ruled_houses == [2, 7]
        assert result.located_house == 7
        assert result.dignity_code == "domicile"

        # 段1：宫主星身份
        assert "第2宫" in result.segment_who_am_i
        assert "第7宫" in result.segment_who_am_i

        # 段2：宫内星 + 自守提示
        assert "入庙" in result.segment_where_i_work or "主场" in result.segment_where_i_work

        # 段3：飞星链 —— 不应出现 7→7 自循环
        assert "第2宫" in result.segment_flystar_chain
        # 不应同时提到第7宫作为结果目标

        # 段4：行运描述
        assert "合相" in result.segment_why_me_today or "金星" in result.segment_why_me_today

        # 段5：建议
        assert len(result.segment_guidance) > 0

        # 完整文本包含所有段
        assert len(result.full_introduction) > 100
        assert result.full_introduction.startswith(f"你好，我是{result.spirit_name}")

    def test_mars_chart_ruler(self, natal_chart: dict, engine: GuideSpiritNarrativeEngine):
        """火星：宫主1+8，落3宫，命主星"""
        spirit = TodayStarSpirit(
            planet="MARS", planet_label="火星", symbol="♂",
            reason="行运火星刑相你的本命土星（orb 0.5°）——火星今天是你最强的引路星灵",
            confidence=90.0, sign="GEMINI", sign_label="双子座",
            trigger_type="exact_transit",
            transit_aspect={
                "transiting_planet": "MARS", "natal_planet": "SATURN",
                "aspect_type": "SQUARE", "aspect_label": "刑相",
                "orb": 0.5, "strength": 0.90,
            },
        )
        planet_chars = {
            "MARS": {
                "house": 3, "sign": "GEMINI", "sign_label": "双子座",
                "dignity_code": "peregrine", "dignity_label": "平常",
                "is_chart_ruler": True,
            },
        }

        result = engine.compute(spirit, natal_chart, planet_chars)

        assert result.ruled_houses == [1, 8]
        assert result.located_house == 3
        assert result.is_chart_ruler is True

        # 命主星提示应出现在第一段
        assert "命主星" in result.segment_who_am_i

        # 段3：3宫(学习与表达)→1宫(自我与身体)+8宫(风险与转化) 的飞星链
        assert "学习与表达" in result.segment_flystar_chain
        assert "自我与身体" in result.segment_flystar_chain or "风险与转化" in result.segment_flystar_chain

        # 段4：刑相（施压）描述
        assert len(result.segment_why_me_today) > 20

    def test_outer_planet_no_rulership(self, natal_chart: dict, engine: GuideSpiritNarrativeEngine):
        """天王星：无传统宫主星，仅作为宫内星"""
        spirit = TodayStarSpirit(
            planet="URANUS", planet_label="天王星", symbol="♅",
            reason="行运天王星对冲你的本命金星（orb 0.8°）——天王星今天是你最强的引路星灵",
            confidence=84.0, sign="AQUARIUS", sign_label="水瓶座",
            trigger_type="exact_transit",
            transit_aspect={
                "transiting_planet": "URANUS", "natal_planet": "VENUS",
                "aspect_type": "OPPOSITION", "aspect_label": "对冲",
                "orb": 0.8, "strength": 0.84,
            },
        )
        planet_chars = {
            "URANUS": {
                "house": 5, "sign": "AQUARIUS", "sign_label": "水瓶座",
                "dignity_code": "peregrine", "dignity_label": "平常",
                "is_chart_ruler": False,
            },
        }

        result = engine.compute(spirit, natal_chart, planet_chars)

        assert result.ruled_houses == []  # 外行星无传统守护
        assert result.located_house == 5

        # 段1：应说明无传统宫主星
        assert "传统守护" in result.segment_who_am_i or "不掌管" in result.segment_who_am_i

        # 段3：聚焦过程本身
        assert "创造与恋爱" in result.segment_flystar_chain

    def test_outer_planet_as_chart_ruler(self, natal_chart: dict, engine: GuideSpiritNarrativeEngine):
        """天王星为命主星（水瓶上升）——即使无传统宫主星，仍强调命主星身份"""
        spirit = TodayStarSpirit(
            planet="URANUS", planet_label="天王星", symbol="♅",
            reason="行运天王星合相你的本命太阳（orb 2.5°）",
            confidence=50.0, sign="AQUARIUS", sign_label="水瓶座",
        )
        planet_chars = {
            "URANUS": {
                "house": 11, "sign": "AQUARIUS", "sign_label": "水瓶座",
                "dignity_code": "peregrine", "dignity_label": "平常",
                "is_chart_ruler": True,
            },
        }

        result = engine.compute(spirit, natal_chart, planet_chars)
        assert "命主星" in result.segment_who_am_i


# ═══════════════════════════════════════════════════════════════
# 月亮触发
# ═══════════════════════════════════════════════════════════════

class TestMoonTrigger:
    def test_moon_trigger_type(self, natal_chart: dict, engine: GuideSpiritNarrativeEngine):
        """行运月亮触发本命行星"""
        spirit = TodayStarSpirit(
            planet="SATURN", planet_label="土星", symbol="♄",
            reason="行运月亮触发你的本命土星——土星今天是你情绪的引路人",
            confidence=60.0, sign="CAPRICORN", sign_label="摩羯座",
            trigger_type="moon_trigger",
            transit_aspect={
                "transiting_planet": "MOON", "natal_planet": "SATURN",
                "aspect_type": "TRINE", "aspect_label": "三合",
                "orb": 2.0,
            },
        )
        planet_chars = {
            "SATURN": {
                "house": 10, "sign": "CAPRICORN", "sign_label": "摩羯座",
                "dignity_code": "domicile", "dignity_label": "入庙",
                "is_chart_ruler": False,
            },
        }

        result = engine.compute(spirit, natal_chart, planet_chars)

        assert result.trigger_type == "moon_trigger"
        assert "月亮" in result.segment_why_me_today
        assert "情绪" in result.segment_why_me_today

    def test_moon_ruler_trigger_type(self, natal_chart: dict, engine: GuideSpiritNarrativeEngine):
        """月亮星座守护触发"""
        spirit = TodayStarSpirit(
            planet="JUPITER", planet_label="木星", symbol="♃",
            reason="今日月亮在射手座，木星是你的今日引路星灵",
            confidence=35.0, sign="SAGITTARIUS", sign_label="射手座",
            trigger_type="moon_ruler",
        )
        planet_chars = {
            "JUPITER": {
                "house": 9, "sign": "SAGITTARIUS", "sign_label": "射手座",
                "dignity_code": "domicile", "dignity_label": "入庙",
                "is_chart_ruler": False,
            },
        }

        result = engine.compute(spirit, natal_chart, planet_chars)
        assert result.trigger_type == "moon_ruler"
        assert "月亮" in result.segment_why_me_today


# ═══════════════════════════════════════════════════════════════
# 法达触发
# ═══════════════════════════════════════════════════════════════

class TestFirdariaTrigger:
    def test_firdaria_trigger_type(self, natal_chart: dict, engine: GuideSpiritNarrativeEngine):
        """法达大运驱动"""
        spirit = TodayStarSpirit(
            planet="MOON", planet_label="月亮", symbol="☽",
            reason="你正处在法达月亮大运——月亮是你这段人生的守护星，今天也不例外",
            confidence=40.0, sign="CANCER", sign_label="巨蟹座",
            trigger_type="firdaria",
        )
        planet_chars = {
            "MOON": {
                "house": 4, "sign": "CANCER", "sign_label": "巨蟹座",
                "dignity_code": "domicile", "dignity_label": "入庙",
                "is_chart_ruler": False,
            },
        }

        result = engine.compute(spirit, natal_chart, planet_chars)
        assert result.trigger_type == "firdaria"
        assert "大运" in result.segment_why_me_today


# ═══════════════════════════════════════════════════════════════
# 边界情况
# ═══════════════════════════════════════════════════════════════

class TestEdgeCases:
    def test_planet_not_in_planet_characters(self, natal_chart: dict, engine: GuideSpiritNarrativeEngine):
        """planet_characters 中缺少该行星的数据：回退到空"""
        spirit = TodayStarSpirit(
            planet="MERCURY", planet_label="水星", symbol="☿",
            reason="行运水星三合你的本命木星（orb 0.6°）——水星今天是你最强的引路星灵",
            confidence=88.0, sign="GEMINI", sign_label="双子座",
        )
        # 空的 planet_characters
        result = engine.compute(spirit, natal_chart, {})

        assert result.located_house == 0
        assert result.dignity_code == "peregrine"
        # 仍应正常渲染（可能缺少部分段）
        assert len(result.full_introduction) > 0

    def test_no_houses_in_chart(self, engine: GuideSpiritNarrativeEngine):
        """natal_chart 无 houses 键"""
        spirit = TodayStarSpirit(
            planet="SUN", planet_label="太阳", symbol="☉",
            reason="行运太阳合相你的本命火星（orb 0.5°）——太阳今天是你最强的引路星灵",
            confidence=90.0, sign="LEO", sign_label="狮子座",
        )
        planet_chars = {
            "SUN": {
                "house": 1, "sign": "LEO", "sign_label": "狮子座",
                "dignity_code": "domicile", "dignity_label": "入庙",
                "is_chart_ruler": False,
            },
        }

        result = engine.compute(spirit, {}, planet_chars)
        assert result.ruled_houses == []
        assert result.located_house == 1

    def test_default_trigger_fallback(self, natal_chart: dict, engine: GuideSpiritNarrativeEngine):
        """无匹配触发类型时回退到 default"""
        spirit = TodayStarSpirit(
            planet="MOON", planet_label="月亮", symbol="☽",
            reason="今日没有明显的行运指引，月亮是你的自然引路星灵",
            confidence=30.0, sign="UNKNOWN", sign_label="未知",
        )
        planet_chars = {
            "MOON": {
                "house": 4, "sign": "CANCER", "sign_label": "巨蟹座",
                "dignity_code": "domicile", "dignity_label": "入庙",
                "is_chart_ruler": False,
            },
        }

        result = engine.compute(spirit, natal_chart, planet_chars)
        assert result.trigger_type == "default"
        assert result.confidence == 30.0

    def test_all_segments_non_empty_for_valid_input(self, natal_chart: dict, engine: GuideSpiritNarrativeEngine):
        """正常输入下所有段落非空"""
        spirit = TodayStarSpirit(
            planet="JUPITER", planet_label="木星", symbol="♃",
            reason="行运木星三合你的本命月亮（orb 0.7°）——木星今天是你最强的引路星灵",
            confidence=86.0, sign="SAGITTARIUS", sign_label="射手座",
            transit_aspect={
                "transiting_planet": "JUPITER", "natal_planet": "MOON",
                "aspect_type": "TRINE", "aspect_label": "三合",
                "orb": 0.7, "strength": 0.86,
            },
        )
        planet_chars = {
            "JUPITER": {
                "house": 9, "sign": "SAGITTARIUS", "sign_label": "射手座",
                "dignity_code": "domicile", "dignity_label": "入庙",
                "is_chart_ruler": False,
            },
        }

        result = engine.compute(spirit, natal_chart, planet_chars)

        assert len(result.segment_who_am_i) > 10
        assert len(result.segment_where_i_work) > 10
        assert len(result.segment_flystar_chain) > 10
        assert len(result.segment_why_me_today) > 10
        assert len(result.segment_guidance) > 10
        assert len(result.full_introduction) > 200

    def test_to_dict_has_required_keys(self, natal_chart: dict, engine: GuideSpiritNarrativeEngine):
        """to_dict 输出包含所有必需键"""
        spirit = TodayStarSpirit(
            planet="VENUS", planet_label="金星", symbol="♀",
            reason="行运金星合相太阳（orb 0.3°）", confidence=94.0,
            sign="LIBRA", sign_label="天秤座",
        )
        planet_chars = {
            "VENUS": {
                "house": 7, "sign": "LIBRA", "sign_label": "天秤座",
                "dignity_code": "domicile", "dignity_label": "入庙",
                "is_chart_ruler": False,
            },
        }

        result = engine.compute(spirit, natal_chart, planet_chars)
        d = result.to_dict()

        required_keys = [
            "spirit_planet", "spirit_name", "spirit_symbol",
            "trigger_type", "confidence", "ruled_houses",
            "located_house", "located_sign", "dignity_code",
            "dignity_label", "is_chart_ruler",
            "segments", "full_introduction", "evidence", "persona_snapshot",
        ]
        for key in required_keys:
            assert key in d, f"Missing key: {key}"

        segments = d["segments"]
        for seg_name in ["who_am_i", "where_i_work", "flystar_chain", "why_me_today", "guidance"]:
            assert seg_name in segments, f"Missing segment: {seg_name}"


# ═══════════════════════════════════════════════════════════════
# 便捷函数
# ═══════════════════════════════════════════════════════════════

class TestConvenienceFunction:
    def test_compute_guide_narrative(self, natal_chart: dict):
        spirit = TodayStarSpirit(
            planet="SUN", planet_label="太阳", symbol="☉",
            reason="行运太阳合相本命火星（orb 0.5°）", confidence=90.0,
            sign="LEO", sign_label="狮子座",
        )
        planet_chars = {
            "SUN": {
                "house": 1, "sign": "LEO", "sign_label": "狮子座",
                "dignity_code": "domicile", "dignity_label": "入庙",
                "is_chart_ruler": True,
            },
        }

        result = compute_guide_narrative(spirit, natal_chart, planet_chars)
        assert isinstance(result, GuideSpiritNarrative)
        assert result.spirit_planet == "SUN"
        assert result.is_chart_ruler is True


# ═══════════════════════════════════════════════════════════════
# 尊贵状态变化
# ═══════════════════════════════════════════════════════════════

class TestDignityTone:
    def test_fall_dignity_tone(self, natal_chart: dict, engine: GuideSpiritNarrativeEngine):
        """落陷行星的叙事语气不同"""
        spirit = TodayStarSpirit(
            planet="VENUS", planet_label="金星", symbol="♀",
            reason="行运金星合相太阳（orb 0.4°）", confidence=92.0,
            sign="VIRGO", sign_label="处女座",
        )
        planet_chars = {
            "VENUS": {
                "house": 6, "sign": "VIRGO", "sign_label": "处女座",
                "dignity_code": "fall", "dignity_label": "落陷",
                "is_chart_ruler": False,
            },
        }

        result = engine.compute(spirit, natal_chart, planet_chars)
        assert result.dignity_code == "fall"

        # 落陷的段2 应该有"最弱"或"摔跤"或"痛"等叙事
        seg2 = result.segment_where_i_work
        assert len(seg2) > 10
        # 落陷 tone 不应该说"主场"或"被放大"
        assert "主场" not in seg2

    def test_exaltation_dignity_tone(self, natal_chart: dict, engine: GuideSpiritNarrativeEngine):
        """擢升行星的叙事语气"""
        spirit = TodayStarSpirit(
            planet="MOON", planet_label="月亮", symbol="☽",
            reason="行运月亮合相太阳（orb 0.5°）", confidence=90.0,
            sign="TAURUS", sign_label="金牛座",
        )
        planet_chars = {
            "MOON": {
                "house": 2, "sign": "TAURUS", "sign_label": "金牛座",
                "dignity_code": "exaltation", "dignity_label": "擢升",
                "is_chart_ruler": False,
            },
        }

        result = engine.compute(spirit, natal_chart, planet_chars)
        assert result.dignity_code == "exaltation"
        # 擢升 tone 应该有"被放大"或"超出预期"
        seg2 = result.segment_where_i_work
        assert len(seg2) > 10


# ═══════════════════════════════════════════════════════════════
# 10 行星 persona 覆盖
# ═══════════════════════════════════════════════════════════════

class TestAllPlanets:
    @pytest.mark.parametrize("planet,house", [
        ("SUN", 1), ("MOON", 4), ("MERCURY", 3), ("VENUS", 7),
        ("MARS", 1), ("JUPITER", 9), ("SATURN", 10),
        ("URANUS", 11), ("NEPTUNE", 12), ("PLUTO", 8),
    ])
    def test_all_10_planet_narratives(self, natal_chart: dict, engine: GuideSpiritNarrativeEngine,
                                       planet: str, house: int):
        """所有10颗行星都能正常渲染自述"""
        from life_kline.characters.planet_personas import get_planet_persona_by_name

        persona = get_planet_persona_by_name(
            {"SUN": "太阳", "MOON": "月亮", "MERCURY": "水星", "VENUS": "金星",
             "MARS": "火星", "JUPITER": "木星", "SATURN": "土星",
             "URANUS": "天王星", "NEPTUNE": "海王星", "PLUTO": "冥王星"}[planet]
        )
        assert persona is not None, f"No persona for {planet}"

        spirit = TodayStarSpirit(
            planet=planet, planet_label=persona.name_zh, symbol=persona.symbol,
            reason=f"行运{persona.name_zh}三合本命太阳（orb 0.5°）",
            confidence=90.0, sign="LEO", sign_label="狮子座",
        )
        planet_chars = {
            planet: {
                "house": house, "sign": "LEO", "sign_label": "狮子座",
                "dignity_code": "peregrine", "dignity_label": "平常",
                "is_chart_ruler": False,
            },
        }

        result = engine.compute(spirit, natal_chart, planet_chars)
        assert result.spirit_name == persona.name_zh
        assert len(result.full_introduction) > 50
        assert result.persona_snapshot["name_zh"] == persona.name_zh
