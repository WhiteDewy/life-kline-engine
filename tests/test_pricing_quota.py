"""
test_pricing_quota.py — 计费额度持久化与 AccessChecker 单元测试

覆盖（对应 P1.1 修复的漏洞）：
- 非 VIP 引擎日上限（10 轮/天）触发 allowed=False
- 非 VIP 引擎单星灵上限（3 轮/星灵）触发 allowed=False
- VIP AI 月配额（30 轮/月）耗尽后回落星币；星币不足 allowed=False
- 非 VIP AI 日免费额度（3 轮/天）耗尽后回落星币
- 议会周上限（3 次/周）触发 allowed=False
- AccessResult.to_dict 含结构化 used/limit 字段
- AccessChecker 能从「合并 extra 后的 state」读到用量（load_user_state 合并语义）

纯离线可跑，不依赖网络/DB/LLM。
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from life_kline.pricing import AccessChecker, FreeQuota


# ──────────── 辅助 ────────────

def _non_vip_state(**overrides):
    """非 VIP、非测试用户的 state（extra 已合并到顶层，模拟 load_user_state 行为）。"""
    base = {
        "user_id": "u_regular",
        "phone": "",
        "is_vip": False,
        "vip_expire_at": "",
        "coins": 0,
        "ai_usage_today": 0,
        "ai_usage_date": "",
        "engine_usage_today": {},
        "ai_usage_this_month": 0,
        "council_usage_this_week": 0,
    }
    base.update(overrides)
    return base


def _vip_state(**overrides):
    base = _non_vip_state()
    base.update(user_id="u_vip", is_vip=True, vip_expire_at="2099-12-31", coins=0)
    base.update(overrides)
    return base


# ──────────── 引擎日上限 ────────────

def test_engine_daily_limit_blocks_when_exhausted():
    """非 VIP 日总轮次达 10 → allowed=False，action_required=upgrade_vip"""
    usage = {"SUN": 3, "MOON": 3, "VENUS": 4}  # total = 10
    state = _non_vip_state(engine_usage_today=usage)
    r = AccessChecker(state).check_engine_chat("MARS")
    assert r.allowed is False
    assert r.action_required == "upgrade_vip"
    assert r.limit == FreeQuota().engine_daily_rounds
    assert r.used == 10


def test_engine_per_spirit_limit_blocks():
    """单星灵达 3 轮但日总未满 → 仍 allowed=False"""
    usage = {"VENUS": 3, "SUN": 1}  # total = 4 < 10, VENUS=3
    state = _non_vip_state(engine_usage_today=usage)
    r = AccessChecker(state).check_engine_chat("VENUS")
    assert r.allowed is False
    assert r.limit == FreeQuota().engine_per_spirit
    assert r.used == 3


def test_engine_allows_within_limit():
    """日总 4、单星灵 1 → allowed=True，remaining_free=6"""
    state = _non_vip_state(engine_usage_today={"VENUS": 1, "SUN": 3})
    r = AccessChecker(state).check_engine_chat("VENUS")
    assert r.allowed is True
    assert r.remaining_free == 6


def test_engine_vip_unlimited():
    state = _vip_state(engine_usage_today={"SUN": 999})
    r = AccessChecker(state).check_engine_chat("SUN")
    assert r.allowed is True
    assert r.is_vip is True


# ──────────── AI 月配额（VIP）────────────

def test_vip_ai_monthly_quota_exhausted_falls_to_coins():
    """VIP 月 30 轮用完 → 回落星币；星币足 → allowed=True cost_coins=3"""
    state = _vip_state(ai_usage_this_month=30, coins=10)
    r = AccessChecker(state).check_ai_chat()
    assert r.allowed is True
    assert r.cost_coins == 3
    assert r.limit == 30 and r.used == 30


def test_vip_ai_monthly_quota_exhausted_no_coins_blocks():
    """VIP 月配额用完且星币不足 → allowed=False action_required=purchase_coins"""
    state = _vip_state(ai_usage_this_month=30, coins=1)
    r = AccessChecker(state).check_ai_chat()
    assert r.allowed is False
    assert r.action_required == "purchase_coins"


def test_non_vip_ai_daily_free_exhausted_falls_to_coins():
    """非 VIP 日 3 轮用完 → 回落星币"""
    state = _non_vip_state(ai_usage_today=3, coins=10)
    r = AccessChecker(state).check_ai_chat()
    assert r.allowed is True
    assert r.cost_coins == 3
    assert r.limit == FreeQuota().ai_daily_rounds


def test_non_vip_ai_no_free_no_coins_blocks():
    state = _non_vip_state(ai_usage_today=3, coins=0)
    r = AccessChecker(state).check_ai_chat()
    assert r.allowed is False
    assert r.action_required == "purchase_coins"


# ──────────── 议会周上限 ────────────

def test_council_weekly_limit_blocks():
    state = _non_vip_state(council_usage_this_week=3)
    r = AccessChecker(state).check_council()
    assert r.allowed is False
    assert r.action_required == "upgrade_vip"
    assert r.limit == FreeQuota().council_weekly and r.used == 3


def test_council_within_limit_allows():
    state = _non_vip_state(council_usage_this_week=1)
    r = AccessChecker(state).check_council()
    assert r.allowed is True
    assert r.remaining_free == 2


# ──────────── to_dict 结构化字段 ────────────

def test_access_result_to_dict_has_used_limit():
    # 用 MOON（未用）避免命中单星灵上限，使日上限分支返回 used=5/limit=10
    state = _non_vip_state(engine_usage_today={"SUN": 5})
    d = AccessChecker(state).check_engine_chat("MOON").to_dict()
    assert "used" in d and "limit" in d
    assert d["used"] == 5
    assert d["limit"] == FreeQuota().engine_daily_rounds


# ──────────── 合并 extra 语义（load_user_state 行为模拟）────────────

def test_access_checker_reads_merged_extra():
    """extra 里的用量合并到顶层后，AccessChecker 能正确读到并拦截。

    对应 main.py load_user_state 的 state.update(extra) 合并：原本用量存在
    extra 里、AccessChecker 读顶层会拿不到，导致上限失效。
    """
    extra = {
        "engine_usage_today": {"SUN": 10},
        "engine_usage_date": "2099-01-01",
        "ai_usage_this_month": 30,
        "ai_usage_month_label": "2099-01",
        "council_usage_this_week": 3,
        "council_usage_week_label": "2099-W01",
    }
    # 模拟 load_user_state 合并前：用量只在 extra
    raw_state = _non_vip_state()
    raw_state["extra"] = extra
    raw_state.pop("engine_usage_today", None)
    raw_state.pop("ai_usage_this_month", None)
    raw_state.pop("council_usage_this_week", None)
    # 合并前 → 读不到 → 错误放行
    pre = AccessChecker(raw_state).check_engine_chat("SUN")
    assert pre.allowed is True  # 漏洞：本应拦截

    # 合并后（load_user_state 行为）→ 正确拦截
    merged = dict(raw_state)
    merged.update(extra)
    post = AccessChecker(merged).check_engine_chat("SUN")
    assert post.allowed is False  # 修复后：拦截
    assert AccessChecker(merged).check_council().allowed is False
    # AI 月配额（ai_usage_this_month）对 VIP 生效：设为 VIP 后 30 轮用完 + 无星币 → 拦截
    merged_vip = dict(merged)
    merged_vip["is_vip"] = True
    merged_vip["vip_expire_at"] = "2099-12-31"
    assert AccessChecker(merged_vip).check_ai_chat().allowed is False


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
