"""
test_safety.py — 危机检测器单元测试

覆盖：高危命中、自伤（需关注）、假阳性排除、空输入、正则变体。
纯规则、离线可跑，不依赖 LLM/网络。
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from life_kline.safety import detect_crisis, SUPPORT_RESOURCES


def test_high_risk_direct_phrase():
    for msg in ["我不想活了", "最近总是想死", "感觉活着没意思，想自杀", "死了算了"]:
        r = detect_crisis(msg)
        assert r.is_crisis, f"应命中高危: {msg}"
        assert r.level == "high", f"级别应为 high: {msg}"
        assert r.message, "干预文案应非空"
        assert r.resources, "应附带支持资源"


def test_high_risk_pattern_variants():
    for msg in ["我真的不想活", "只想结束这一切", "人生一点意义都没有太痛苦了"]:
        r = detect_crisis(msg)
        assert r.is_crisis, f"正则变体应命中: {msg}"
        assert r.level == "high"


def test_self_harm_concern_level():
    r = detect_crisis("我又开始自残了")
    assert r.is_crisis
    assert r.level == "concern"
    assert r.message


def test_benign_false_positives_not_triggered():
    # 口语夸张 / 与产品操作相关，绝不能触发危机
    for msg in [
        "今天累死了", "笑死了哈哈哈", "热死了想开空调",
        "这题难死我了", "我想删了这个app", "忙死了没时间聊",
    ]:
        r = detect_crisis(msg)
        assert not r.is_crisis, f"不应误触发: {msg}"
        assert r.level == "none"


def test_normal_message_not_triggered():
    for msg in ["我最近工作压力好大", "喜欢的人不理我了", "想问问我的事业方向"]:
        r = detect_crisis(msg)
        assert not r.is_crisis, f"普通消息不应触发: {msg}"


def test_empty_input():
    assert not detect_crisis("").is_crisis
    assert not detect_crisis("   ").is_crisis
    assert not detect_crisis(None).is_crisis  # type: ignore


def test_mixed_benign_and_real_risk():
    # "累死了"是良性，但"不想活了"是真危机——不能被良性擦除掩盖
    r = detect_crisis("工作累死了，我真的不想活了")
    assert r.is_crisis
    assert r.level == "high"


def test_resources_present():
    assert len(SUPPORT_RESOURCES) >= 1
    for res in SUPPORT_RESOURCES:
        assert res.get("name") and res.get("contact")


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passed = 0
    for t in tests:
        t()
        print(f"  ✓ {t.__name__}")
        passed += 1
    print(f"\n✅ 危机检测测试全部通过 ({passed}/{len(tests)})")
