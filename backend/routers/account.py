"""
account.py — 账号管理路由（P5 合规）

App Store / 国内合规强制要求：用户可注销账号并彻底清除数据（被遗忘权）。
"""
from __future__ import annotations

import hashlib
import os
import time
from typing import Annotated, Any

from fastapi import APIRouter, Header, HTTPException

from backend import dao as _dao

router = APIRouter(prefix="/api/account", tags=["account"])


def _parse_token(token: str) -> str | None:
    """镜像 main._parse_token（待合并到共享 auth 模块）。"""
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


@router.delete("")
async def delete_account(authorization: Annotated[str, Header()] = "") -> dict[str, Any]:
    """注销账号 — 彻底删除当前用户全部数据。不可恢复。

    前端调用后应清除本地 token 并跳转登录页。
    """
    token = authorization.replace("Bearer ", "") if authorization else ""
    user_id = _parse_token(token) or ""
    if not user_id:
        raise HTTPException(status_code=401, detail="请先登录")
    _dao.delete_user_completely(user_id)
    return {"status": "success", "data": {"deleted": True}}
