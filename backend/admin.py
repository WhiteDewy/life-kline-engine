"""
admin.py — 后台管理 (Admin CMS)

功能：
- 管理员账号体系（与普通用户分离）
- JWT token 与普通用户同形态但携带 role=admin
- 启动时从环境变量读取初始管理员账号，自动创建 super_admin
- 所有写操作均写入 audit_logs
"""
from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import time
from typing import Optional

from fastapi import Header, HTTPException, Request
from pydantic import BaseModel

from . import dao as _dao
from .database import _now


JWT_SECRET = os.getenv("LIFE_KLINE_JWT_SECRET", "")
JWT_SECRET_DEFAULT = "dev-secret-change-in-production"

if not JWT_SECRET or JWT_SECRET == JWT_SECRET_DEFAULT:
    raise RuntimeError(
        "环境变量 LIFE_KLINE_JWT_SECRET 未设置或使用了默认值。"
        "请在 backend/.env 中配置一个强随机字符串后再启动 admin 模块。"
    )

# 初始管理员账号：用户名可有默认值，但密码必须显式配置，禁止内置弱口令。
ENV_ADMIN_USER = os.getenv("LIFE_KLINE_ADMIN_USER", "admin")
ENV_ADMIN_PASS = os.getenv("LIFE_KLINE_ADMIN_PASS", "")

_LEGACY_SALT = "lk_admin_salt_v1"  # 仅用于验证历史遗留哈希，禁止再用于新密码
_PBKDF2_ROUNDS = 50000


# ──────────── 密码哈希（PBKDF2 + per-password 随机盐）─────────────────────────

def _pbkdf2(password: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _PBKDF2_ROUNDS, dklen=32)


def _hash_password(password: str) -> str:
    """生成带随机盐的哈希，格式：pbkdf2$<salt_hex>$<hash_hex>。"""
    salt = secrets.token_bytes(16)
    dk = _pbkdf2(password, salt)
    return f"pbkdf2${salt.hex()}${dk.hex()}"


def _verify_password(password: str, password_hash: str) -> bool:
    """验证密码，兼容新格式与历史遗留（共享盐）格式。"""
    if password_hash.startswith("pbkdf2$"):
        try:
            _, salt_hex, hash_hex = password_hash.split("$", 2)
        except ValueError:
            return False
        candidate = _pbkdf2(password, bytes.fromhex(salt_hex)).hex()
        return hmac.compare_digest(candidate, hash_hex)
    # 历史遗留格式：固定盐、裸 hex。仅为兼容旧账号登录。
    legacy = _pbkdf2(password, _LEGACY_SALT.encode()).hex()
    return hmac.compare_digest(legacy, password_hash)


def _make_admin_token(admin_id: str, username: str, role: str) -> str:
    payload = f"{admin_id}:{username}:{role}:{int(time.time())}"
    sig = hashlib.sha256(f"{payload}:{JWT_SECRET}".encode()).hexdigest()[:16]
    return f"{payload}:{sig}"


def _parse_admin_token(token: str) -> Optional[dict]:
    try:
        parts = token.split(":")
        if len(parts) != 5:
            return None
        admin_id, username, role, ts, sig = parts
        expected = hashlib.sha256(
            f"{admin_id}:{username}:{role}:{ts}:{JWT_SECRET}".encode()
        ).hexdigest()[:16]
        if sig != expected:
            return None
        if int(time.time()) - int(ts) > 86400 * 7:  # 7 天过期
            return None
        return {
            "admin_id": admin_id,
            "username": username,
            "role": role,
            "ts": ts,
        }
    except Exception:
        return None


def ensure_root_admin() -> None:
    """启动时调用 — 确保至少有一个 super_admin 账号存在。

    密码必须通过 LIFE_KLINE_ADMIN_PASS 显式配置；未配置时跳过自动创建，
    绝不使用内置弱口令创建 super_admin。
    """
    existing = _dao.get_admin_by_username(ENV_ADMIN_USER)
    if existing:
        return
    if not ENV_ADMIN_PASS or len(ENV_ADMIN_PASS) < 8:
        print(
            "[admin] 未配置 LIFE_KLINE_ADMIN_PASS（或长度 < 8），"
            "跳过初始管理员创建。请设置强密码后重启以创建 super_admin。"
        )
        return
    pwd_hash = _hash_password(ENV_ADMIN_PASS)
    _dao.create_admin(
        username=ENV_ADMIN_USER,
        password_hash=pwd_hash,
        role="super_admin",
    )
    print(
        f"[admin] 已创建初始管理员账号: {ENV_ADMIN_USER} (密码见环境变量 LIFE_KLINE_ADMIN_PASS)"
    )


# ──────────── 管理员上下文（Pydantic BaseModel）────────────────

class AdminContext(BaseModel):
    """管理员运行时上下文。Pydantic 让 FastAPI 接受它作为依赖返回值。"""
    admin_id: str = ""
    username: str = ""
    role: str = "admin"
    request: Optional[Request] = None

    class Config:
        arbitrary_types_allowed = True

    def log(self, action: str, target_type: str, target_id: str = "",
            detail: str = "") -> None:
        ip = ""
        if self.request is not None:
            try:
                ip = self.request.client.host if self.request.client else ""
            except Exception:
                ip = ""
        try:
            _dao.insert_audit_log(
                admin_id=self.admin_id,
                admin_username=self.username,
                action=action,
                target_type=target_type,
                target_id=target_id,
                detail=detail,
                ip=ip,
            )
        except Exception:
            pass


# ──────────── 依赖注入 ───────────────────────────────────────────

def require_admin(
    request: Request, authorization: str = Header(default="")
) -> AdminContext:
    """FastAPI 依赖 — 验证管理员 token 并返回 BaseModel context。"""
    token = authorization.replace("Bearer ", "")
    info = _parse_admin_token(token)
    if not info:
        raise HTTPException(status_code=401, detail="管理员未登录或 token 失效")
    admin = _dao.get_admin_by_username(info["username"])
    if not admin or not admin.get("is_active"):
        raise HTTPException(status_code=403, detail="账号已停用")
    return AdminContext(
        admin_id=info["admin_id"],
        username=info["username"],
        role=info["role"],
        request=request,
    )


def require_super_admin(
    request: Request, authorization: str = Header(default="")
) -> AdminContext:
    """超级管理员依赖 — 与 require_admin 类似但额外校验 role。"""
    ctx = require_admin(request, authorization=authorization)
    if ctx.role != "super_admin":
        raise HTTPException(status_code=403, detail="需要 super_admin 权限")
    return ctx
