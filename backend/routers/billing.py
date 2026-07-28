"""
billing.py — 计费后端路由（P1.2）

承载「定价 → 下单 → 支付凭证校验 → 发放」链路中缺失的后端环节。
- 定价规则本身不变，仍读 life_kline.pricing 的 COIN_PACKAGES / VIP_PLANS。
- 额度校验仍由 AccessChecker 单一真相源负责（见 main.py 的 spirit_chat/council）。
- 本路由只负责：创建订单、校验支付渠道凭证、发放星币/VIP、查询订单。

渠道：
- iap   — iOS IAP（Apple verifyReceipt，需 env APPLE_SHARED_SECRET / APPLE_BUNDLE_ID）
- wechat / alipay — 安卓（需商户配置，凭证校验为扩展点）
- dev   — 仅测试用户 / env LIFE_KLINE_DEV_BYPASS=1 时直发，供无 SDK 的 web 调试

工程规范：薄 handler，业务在 dao/服务层；密钥全走 env（§1 §7 §11）；幂等（§4）；
异步非阻塞 httpx + 超时（§2 §3）。
"""
from __future__ import annotations

import hashlib
import os
import time
from typing import Annotated, Any, Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field

from backend import dao as _dao
from life_kline.pricing import (
    COIN_PACKAGES,
    VIP_PLANS,
    is_test_user,
)

router = APIRouter(prefix="/api/billing", tags=["billing"])

# 苹果 IAP 验证端点（legacy verifyReceipt；生产 status==21007 时转 sandbox）
_APPLE_VERIFY_URL = "https://buy.itunes.apple.com/verifyReceipt"
_APPLE_SANDBOX_URL = "https://sandbox.itunes.apple.com/verifyReceipt"


# ──────────── 鉴权（镜像 main._parse_token，待合并到共享 auth 模块）────────────

def _parse_token(token: str) -> Optional[str]:
    secret = os.getenv("LIFE_KLINE_JWT_SECRET", "")
    try:
        parts = token.split(":")
        if len(parts) != 3:
            return None
        user_id, ts, sig = parts
        expected = hashlib.sha256(f"{user_id}:{ts}:{secret}".encode()).hexdigest()[:16]
        if sig != expected:
            return None
        if int(time.time()) - int(ts) > 86400 * 30:
            return None
        return user_id
    except Exception:
        return None


def _require_user(authorization: Annotated[str, Header()] = "") -> str:
    token = authorization.replace("Bearer ", "") if authorization else ""
    user_id = _parse_token(token) or ""
    if not user_id:
        raise HTTPException(status_code=401, detail="请先登录")
    return user_id


UserDep = Annotated[str, Depends(_require_user)]


# ──────────── 入参模型 ────────────

class CreateOrderInput(BaseModel):
    product_id: str = Field(..., description="coin_100 / monthly_auto / ...")
    channel: str = Field("iap", description="iap / wechat / alipay")


class VerifyInput(BaseModel):
    order_id: str
    channel: str = Field("iap")
    receipt: Optional[str] = Field(None, description="iOS IAP base64 receipt")
    provider_data: Optional[dict] = Field(None, description="微信/支付宝回调数据")


# ──────────── 产品解析与发放 ────────────

def _resolve_product(product_id: str) -> tuple[str, str, float, int]:
    """返回 (product_type, name, price_cny, grant_payload)。

    grant_payload：coin 包为总星币数；VIP 为天数。找不到产品抛 400。
    """
    for pkg in COIN_PACKAGES:
        if pkg.id == product_id:
            return "coin", pkg.name, float(pkg.price_cny), pkg.coins + pkg.bonus
    plan = VIP_PLANS.get(product_id)
    if plan:
        return "vip", plan.name, float(plan.price_cny), plan.duration_days
    raise HTTPException(status_code=400, detail=f"未知产品: {product_id}")


def _grant(user_id: str, product_type: str, grant_payload: int) -> str:
    """发放并返回 granted 描述。"""
    if product_type == "coin":
        _dao.add_coins(user_id, grant_payload)
        return f"coins:+{grant_payload}"
    if product_type == "vip":
        _dao.activate_vip(user_id, grant_payload)
        return f"vip:{grant_payload}d"
    raise HTTPException(status_code=400, detail=f"未知产品类型: {product_type}")


# ──────────── 渠道凭证校验 ────────────

async def _verify_iap(receipt_b64: Optional[str]) -> tuple[str, str]:
    """校验 iOS IAP receipt。返回 (provider_order_id, receipt_ref)。

    需要 env APPLE_SHARED_SECRET；未配置则 503（不静默放行）。
    """
    secret = os.getenv("APPLE_SHARED_SECRET", "").strip()
    if not secret:
        raise HTTPException(
            status_code=503,
            detail="IAP 校验未配置（APPLE_SHARED_SECRET 缺失），请联系后台",
        )
    if not receipt_b64:
        raise HTTPException(status_code=400, detail="缺少 receipt")

    import httpx  # 局部导入，避免无 httpx 时影响模块加载

    payload = {
        "receipt-data": receipt_b64,
        "password": secret,
        "exclude-old-transactions": True,
    }
    # 苹果策略：先打生产，status==21007（测试凭证）时转 sandbox
    for url in (_APPLE_VERIFY_URL, _APPLE_SANDBOX_URL):
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=3.0)) as c:
                resp = await c.post(url, json=payload)
            data = resp.json()
        except Exception:
            continue
        status = data.get("status")
        if status == 21007 and url == _APPLE_VERIFY_URL:
            continue  # 转沙箱重试
        if status == 0:
            receipt_info = data.get("receipt", {}) or {}
            in_app = receipt_info.get("in_app") or [{}]
            txn = in_app[0] if in_app else {}
            provider_order_id = txn.get("transaction_id", "")
            receipt_ref = f"iap:{txn.get('product_id', '')}"
            return provider_order_id, receipt_ref
        if url == _APPLE_SANDBOX_URL:
            raise HTTPException(status_code=400, detail=f"IAP 校验失败 status={status}")
    raise HTTPException(status_code=502, detail="IAP 校验服务不可用")


async def _verify_provider(channel: str, body: VerifyInput) -> tuple[str, str]:
    """分发渠道校验，返回 (provider_order_id, receipt_ref)。"""
    if channel == "iap":
        return await _verify_iap(body.receipt)
    if channel in ("wechat", "alipay"):
        # 扩展点：需商户号/密钥/平台证书与查单或回调验签。凭证缺失时明确报错。
        cfg_ok = (
            os.getenv("WXPAY_MCH_ID", "").strip()
            if channel == "wechat"
            else os.getenv("ALIPAY_APP_ID", "").strip()
        )
        if not cfg_ok:
            raise HTTPException(
                status_code=503,
                detail=f"{channel} 支付校验未配置，请联系后台",
            )
        pd = body.provider_data or {}
        return str(pd.get("transaction_id", "")), f"{channel}:{pd.get('product_id', '')}"
    raise HTTPException(status_code=400, detail=f"未知渠道: {channel}")


def _dev_bypass_enabled(user_id: str) -> bool:
    """dev 验证旁路：仅测试用户或 env 显式开启时生效。生产 env 必须关闭。"""
    if os.getenv("LIFE_KLINE_DEV_BYPASS", "") == "1":
        return True
    state = _dao.get_user_state(user_id)
    return is_test_user(user_id, state.get("phone", ""))


# ──────────── 端点 ────────────

@router.post("/orders")
async def create_order(body: CreateOrderInput, user_id: UserDep) -> dict[str, Any]:
    """创建订单。返回 order_id + 金额 + 渠道，供前端拉起原生支付。"""
    product_type, _name, price_cny, _payload = _resolve_product(body.product_id)
    order = _dao.create_payment_order(
        user_id=user_id,
        product_id=body.product_id,
        product_type=product_type,
        channel=body.channel,
        amount_cny=price_cny,
    )
    return {
        "status": "success",
        "data": {
            "order_id": order["id"],
            "product_id": body.product_id,
            "product_type": product_type,
            "channel": body.channel,
            "amount_cny": price_cny,
            "status": "pending",
        },
    }


@router.post("/verify")
async def verify_payment(body: VerifyInput, user_id: UserDep) -> dict[str, Any]:
    """校验支付凭证并发放。幂等：重复 verify 不重复发放。

    dev 旁路：仅测试用户 / env LIFE_KLINE_DEV_BYPASS=1 时跳过渠道校验直发，
    供无原生 SDK 的 web 调试；生产必须关闭。
    """
    order = _dao.get_payment_order(body.order_id)
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="无权操作该订单")

    # 幂等：已支付直接返回当前状态
    if order.get("status") == "paid":
        return {
            "status": "success",
            "data": {
                "order_id": order["id"],
                "already_paid": True,
                "granted": order.get("granted", ""),
            },
        }

    product_type = order.get("product_type") or ""
    product_id = order.get("product_id") or ""
    _pt, _name, _price, grant_payload = _resolve_product(product_id)

    if _dev_bypass_enabled(user_id):
        provider_order_id, receipt_ref = "dev-bypass", "dev:"
    else:
        provider_order_id, receipt_ref = await _verify_provider(body.channel, body)

    granted_desc = _grant(user_id, product_type, grant_payload)
    _dao.complete_payment_order(body.order_id, provider_order_id, receipt_ref, granted_desc)

    state = _dao.get_user_state(user_id)
    return {
        "status": "success",
        "data": {
            "order_id": order["id"],
            "granted": granted_desc,
            "coins": int(state.get("coins", 0)),
            "is_vip": bool(state.get("is_vip", 0)),
            "vip_expire_at": state.get("vip_expire_at", ""),
        },
    }


@router.get("/orders")
async def list_orders(user_id: UserDep) -> dict[str, Any]:
    """当前用户订单列表（提审需要「购买记录/恢复购买」入口）。"""
    orders = _dao.list_user_orders(user_id, limit=50)
    return {"status": "success", "data": {"orders": orders}}
