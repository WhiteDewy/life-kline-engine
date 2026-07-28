"""
test_akg.py — AKG 主题层 + 证据融合单元测试

覆盖：
- seam 导入点亮（ThemeRecognizer/ThemeNode/build_theme_narrative）
- 关键词识别（用户问题 → 主题）
- 证据收集（含「尊贵」「相位」前缀，来自 report_data）
- 置信度范围
- 叙事 ACP 合规（不含「注定/一定」）
- 无关键词 fallback（按星盘强度排序）

纯离线可跑，不依赖网络/真实 LLM。
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from life_kline.akg import (
    ThemeRecognizer, ThemeNode, build_theme_narrative, THEME_CATALOG,
)
from life_kline.akg.evidence import collect_theme_evidence, score_theme, theme_confidence
from life_kline.akg.theme_catalog import get_theme
from life_kline.akg.narrative import Narrative, build_narrative
from life_kline.acp import NARRATIVE_SCHEMA_FIELDS


# ──────────── fixture：最小 report_data ────────────

def _planet(sign, sign_label, house, house_title, dignity, dignity_label, aspects=None):
    return {
        "sign": sign, "sign_label": sign_label,
        "house": house, "house_title": house_title,
        "dignity": dignity, "dignity_label": dignity_label,
        "aspect_signature": aspects or [],
    }


def _baseline(composite, tone):
    return {"composite": composite, "narrative_tone": tone}


def _sample_report_data():
    planets = {
        "SUN": _planet("LEO", "狮子", 10, "事业与社会地位", "domicile", "庙旺",
                       ["太阳 合相 水星 1.0°", "太阳 刑 土星 2.0°"]),
        "SATURN": _planet("CAPRICORN", "摩羯", 10, "事业与社会地位", "domicile", "庙旺",
                          ["土星 对冲 月亮 1.5°"]),
        "MOON": _planet("CANCER", "巨蟹", 4, "家庭与根基", "domicile", "庙旺"),
        "VENUS": _planet("TAURUS", "金牛", 2, "财富与资源", "domicile", "庙旺"),
        "MARS": _planet("ARIES", "白羊", 1, "自我与身体", "domicile", "庙旺"),
        "JUPITER": _planet("SAGITTARIUS", "射手", 9, "信念与远方", "domicile", "庙旺"),
        "MERCURY": _planet("GEMINI", "双子", 3, "沟通与近邻", "domicile", "庙旺"),
    }
    houses = [
        {"house": h, "sign": "X", "sign_label": "X", "title": f"第{h}宫主题",
         "degree": 0.0} for h in range(1, 13)
    ]
    major_aspects = [
        {"title": "太阳 刑 土星", "nature": "challenging", "strength": 0.8, "summary": "..."},
        {"title": "金星 合相 木星", "nature": "supportive", "strength": 0.7, "summary": "..."},
    ]
    baselines = {
        "SUN": _baseline(9.5, "天然优势"),
        "SATURN": _baseline(8.0, "天然优势"),
        "MOON": _baseline(7.0, "底子好"),
        "VENUS": _baseline(6.0, "底子好"),
    }
    return {
        "natal_chart": {
            "planets": planets,
            "houses": houses,
            "major_aspects": major_aspects,
        },
        "_analysis_evidence": {"planet_baselines": baselines},
    }


# ──────────── tests ────────────

def test_seam_imports():
    """seam 导入点亮（consultation.py / consultation_engine.py 依赖）。"""
    from life_kline.akg import ThemeRecognizer, ThemeNode, build_theme_narrative
    assert ThemeRecognizer is not None
    assert ThemeNode is not None
    assert callable(build_theme_narrative)
    # theme_reflections 期望的 5 个 key 必须存在
    for k in ("authority", "intimacy", "money", "self_worth", "safety"):
        assert k in THEME_CATALOG, f"theme_reflections key 缺失: {k}"
    print("✓ seam 导入 + reflection key 对齐")


def test_recognize_by_keyword():
    """关键词命中 → 正确主题排前。"""
    report = _sample_report_data()
    themes = ThemeRecognizer().recognize("我害怕领导，不敢跟上级说话", report, top_k=3)
    assert themes, "应识别出主题"
    assert themes[0].key == "authority", f"top 应为 authority，实际 {themes[0].key}"
    print(f"✓ 关键词识别：top={themes[0].key}")


def test_evidence_collected():
    """证据含前缀字符串 + 来自 report_data 的事实。"""
    report = _sample_report_data()
    theme = get_theme("authority")
    ev = collect_theme_evidence(theme, report)
    assert ev, "authority 应有证据"
    texts = [e.text for e in ev]
    assert any("【尊贵】" in t for t in texts), "应有尊贵证据"
    assert any("【落宫落座】" in t for t in texts), "应有落宫落座证据"
    assert any("【主题相位】" in t for t in texts), "应有主题相位证据（太阳刑土星）"
    assert any("庙旺" in t for t in texts), "应含 dignity 事实"
    print(f"✓ 证据收集：{len(ev)} 条")


def test_confidence_range():
    """置信度在 [0, 0.95]。"""
    report = _sample_report_data()
    for t in ThemeRecognizer().recognize("工作与事业方向", report, top_k=5):
        assert 0.0 <= t.confidence <= 0.95, f"{t.key} confidence 越界: {t.confidence}"
        assert 0.0 <= t.strength <= 1.0, f"{t.key} strength 越界: {t.strength}"
    print("✓ 置信度/强度范围合法")


def test_narrative_acp():
    """叙事非空且不含宿命禁用词。"""
    report = _sample_report_data()
    themes = ThemeRecognizer().recognize("我想升职但怕领导", report, top_k=1)
    assert themes
    narrative = build_theme_narrative(themes[0], report)
    assert narrative, "叙事应非空"
    for word in ("注定", "一定", "必须"):
        assert word not in narrative, f"叙事含禁用词 {word}"
    assert "自由意志" in narrative or "倾向" in narrative, "应含 ACP 收束"
    print("✓ 叙事 ACP 合规")


def test_recognize_fallback_no_keyword():
    """无关键词命中 → 仍按星盘强度返回非空 themes。"""
    report = _sample_report_data()
    themes = ThemeRecognizer().recognize("今天天气不错啊", report, top_k=3)
    assert themes, "fallback 应返回按强度排序的主题"
    # 强度应单调递减
    strengths = [t.strength for t in themes]
    assert strengths == sorted(strengths, reverse=True), "应按强度降序"
    print(f"✓ fallback 排序：{[(t.key, round(t.strength,2)) for t in themes]}")


def test_theme_node_to_dict():
    """ThemeNode.to_dict() 含 seam 期望字段。"""
    report = _sample_report_data()
    themes = ThemeRecognizer().recognize("我害怕领导", report, top_k=1)
    d = themes[0].to_dict()
    for k in ("key", "label", "evidence", "strength", "confidence"):
        assert k in d, f"to_dict 缺字段 {k}"
    print("✓ ThemeNode.to_dict 字段完整")


def test_narrative_schema():
    """ACP-0003 七字段 Narrative Schema 固化。"""
    report = _sample_report_data()
    themes = ThemeRecognizer().recognize("我害怕领导，不敢跟上级说话", report, top_k=1)
    theme = themes[0]

    # build_narrative 产出 7 字段
    n = build_narrative(theme, report)
    d = n.to_dict()
    assert set(d.keys()) == set(NARRATIVE_SCHEMA_FIELDS), f"字段不符: {d.keys()}"
    for f in ("theme", "origin", "evidence", "psychology", "pattern", "healing_goal"):
        assert d[f], f"字段 {f} 应非空"
    # growth 初始允许空（留给纵向 MemoryManager）
    assert d["growth"] == "", "growth 初始应为空"

    # build_theme_narrative 把 schema 挂到 ThemeNode（seam 持久化路径）
    prose = build_theme_narrative(theme, report)
    assert prose, "渲染 prose 应非空"
    assert theme.narrative_schema, "ThemeNode.narrative_schema 应被填充"
    assert set(theme.narrative_schema.keys()) == set(NARRATIVE_SCHEMA_FIELDS)
    # ACP 合规：prose 不含禁用词
    for word in ("注定", "一定", "必须"):
        assert word not in prose, f"prose 含禁用词 {word}"

    # to_dict 携带 narrative_schema（经 recognized_themes 自动持久化）
    td = theme.to_dict()
    assert "narrative_schema" in td and td["narrative_schema"]
    print("✓ Narrative 7 字段 Schema 固化 + ACP 合规")


if __name__ == "__main__":
    test_seam_imports()
    test_recognize_by_keyword()
    test_evidence_collected()
    test_confidence_range()
    test_narrative_acp()
    test_recognize_fallback_no_keyword()
    test_theme_node_to_dict()
    test_narrative_schema()
    print("\n全部 AKG 测试通过 ✓")
