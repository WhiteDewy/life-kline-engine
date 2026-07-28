"""
test_billing.py — 计费后端单元测试（P1.2）

覆盖：
- 产品解析（coin 包 / VIP）
- create_order → verify(dev bypass) → 发放星币
- 幂等：重复 verify 不重复发放
- VIP 订阅发放：is_vip / vip_expire_at 正确设置
- 非 dev 路径：APPLE_SHARED_SECRET 缺失时 IAP 校验返回 503（不静默放行）

使用临时 DB 文件，不污染 backend/data/app.db。纯离线（dev 旁路，不触网）。
"""
import sys
import os
import asyncio
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import backend.database as _dbmod
from backend import dao as _dao
from backend.routers import billing as _billing

# ── 重定向 DB 到临时文件，避免污染真实库 ──
_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp.close()
_dbmod.DB_PATH = _tmp.name
_dbmod.init_db()
_dbmod.migrate_db()

# 开启 dev 旁路（仅测试）
os.environ["LIFE_KLINE_DEV_BYPASS"] = "1"
# 清掉可能存在的苹果密钥，测非 dev 分支前再恢复
os.environ.pop("APPLE_SHARED_SECRET", None)


from backend.routers.billing import (
    CreateOrderInput,
    VerifyInput,
    create_order,
    verify_payment,
    _resolve_product,
)


USER = "u_billing_test"


def _ensure_user():
    """插入测试用户（user_state/payments 外键引用 users）。"""
    db = _dbmod.get_db()
    db.execute(
        "INSERT OR IGNORE INTO users (id, phone, nickname, created_at, last_login_at) "
        "VALUES (?, ?, '', ?, ?)",
        (USER, "13900000000", _dbmod._now(), _dbmod._now()),
    )
    db.commit()
    db.close()


def _reset_user():
    """每个用例前清零该用户状态。"""
    _ensure_user()
    _dao.upsert_user_state(
        USER, coins=0, is_vip=False, vip_expire_at="", ai_usage_today=0, ai_usage_date="",
    )


# ──────────── 产品解析 ────────────

def test_resolve_coin_package():
    ptype, name, price, payload = _resolve_product("coin_100")
    assert ptype == "coin"
    assert price == 98
    assert payload == 102  # 100 + 2 bonus


def test_resolve_vip_plan():
    ptype, name, price, payload = _resolve_product("monthly_auto")
    assert ptype == "vip"
    assert payload == 30  # duration_days


def test_resolve_unknown_product_400():
    import pytest
    with pytest.raises(Exception):
        _resolve_product("nonexistent")


# ──────────── 下单 → 验证 → 发放（星币）────────────

def test_coin_order_grants_coins():
    _reset_user()
    order = asyncio.run(create_order(CreateOrderInput(product_id="coin_100", channel="dev"), USER))
    assert order["status"] == "success"
    order_id = order["data"]["order_id"]
    assert order["data"]["amount_cny"] == 98

    result = asyncio.run(verify_payment(VerifyInput(order_id=order_id, channel="dev"), USER))
    assert result["status"] == "success"
    assert result["data"]["granted"] == "coins:+102"
    assert result["data"]["coins"] == 102


def test_verify_idempotent_no_double_grant():
    _reset_user()
    order = asyncio.run(create_order(CreateOrderInput(product_id="coin_30", channel="dev"), USER))
    order_id = order["data"]["order_id"]

    r1 = asyncio.run(verify_payment(VerifyInput(order_id=order_id, channel="dev"), USER))
    assert r1["data"]["coins"] == 30
    # 第二次 verify：已是 paid，不重复发放
    r2 = asyncio.run(verify_payment(VerifyInput(order_id=order_id, channel="dev"), USER))
    assert r2["data"].get("already_paid") is True
    state = _dao.get_user_state(USER)
    assert state["coins"] == 30  # 没有变成 60


# ──────────── VIP 订阅发放 ────────────

def test_vip_order_activates_vip():
    _reset_user()
    order = asyncio.run(create_order(CreateOrderInput(product_id="monthly_auto", channel="dev"), USER))
    order_id = order["data"]["order_id"]

    result = asyncio.run(verify_payment(VerifyInput(order_id=order_id, channel="dev"), USER))
    assert result["status"] == "success"
    assert result["data"]["granted"] == "vip:30d"
    assert result["data"]["is_vip"] is True
    assert result["data"]["vip_expire_at"] != ""


# ──────────── 非 dev 路径：IAP 未配置应 503 ────────────

def test_iap_not_configured_returns_503():
    """无 APPLE_SHARED_SECRET 且非 dev 旁路时，IAP 校验必须明确失败，不静默放行。"""
    _reset_user()
    # 临时关闭 dev 旁路
    saved = os.environ.pop("LIFE_KLINE_DEV_BYPASS")
    try:
        order = asyncio.run(create_order(CreateOrderInput(product_id="coin_30", channel="iap"), USER))
        order_id = order["data"]["order_id"]
        import pytest
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            asyncio.run(verify_payment(VerifyInput(order_id=order_id, channel="iap", receipt="fake"), USER))
        assert exc.value.status_code == 503
    finally:
        os.environ["LIFE_KLINE_DEV_BYPASS"] = saved


# ──────────── 订单归属校验 ────────────

def test_verify_rejects_non_owner():
    _reset_user()
    order = asyncio.run(create_order(CreateOrderInput(product_id="coin_30", channel="dev"), USER))
    order_id = order["data"]["order_id"]
    import pytest
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        asyncio.run(verify_payment(VerifyInput(order_id=order_id, channel="dev"), "u_other"))
    assert exc.value.status_code == 403


def test_list_orders():
    _reset_user()
    asyncio.run(create_order(CreateOrderInput(product_id="coin_30", channel="dev"), USER))
    from backend.routers.billing import list_orders
    res = asyncio.run(list_orders(USER))
    assert res["status"] == "success"
    assert len(res["data"]["orders"]) >= 1


# ──────────── 账号注销（被遗忘权）────────────

def test_delete_user_completely():
    """注销账号后，用户在各表的数据全部清除。"""
    _reset_user()
    # 制造一些数据：订单 + 星币
    order = asyncio.run(create_order(CreateOrderInput(product_id="coin_30", channel="dev"), USER))
    asyncio.run(verify_payment(VerifyInput(order_id=order["data"]["order_id"], channel="dev"), USER))
    assert _dao.get_user_state(USER)["coins"] == 30
    assert _dao.list_user_orders(USER)

    # 注销
    _dao.delete_user_completely(USER)

    # user_state / payments / users 全部无残留
    assert _dao.get_user_state(USER).get("coins", 0) == 0
    assert _dao.get_payment_order(order["data"]["order_id"]) is None
    assert not _dao.list_user_orders(USER)
    db = _dbmod.get_db()
    row = db.execute("SELECT id FROM users WHERE id=?", (USER,)).fetchone()
    db.close()
    assert row is None


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
