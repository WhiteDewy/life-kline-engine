"""Async Redis connection manager with safe in-memory fallback.

The consultation state machine stores short-term session state, the topic
stack, optimistic-lock versions and per-user/session token budgets here so the
service can scale horizontally. When Redis is unavailable the store degrades
to a process-local dict and reports ``available=False`` so the service layer
can tell the user progress cannot be persisted — never silently switching to a
mode that breaks under multi-instance deployment.

Redis is optional at runtime (dev without Redis still works), but the code
never assumes process-local state is authoritative for production: the service
checks ``RedisStore.available`` and refuses to persist when it is ``False``.
"""
from __future__ import annotations

import json
import logging
import os
import time
from typing import Any, Awaitable, Callable

logger = logging.getLogger(__name__)


def _env(key: str, default: str = "") -> str:
    return os.getenv(key, default).strip()


class RedisStore:
    """Thin async wrapper over an optional ``redis.asyncio`` client."""

    SESSION_TTL_SECONDS = 7 * 24 * 3600
    _TOKEN_TTL_SECONDS = 24 * 3600

    def __init__(self) -> None:
        self._url = _env("LIFE_KLINE_REDIS_URL")
        self._client: Any = None
        self._available: bool = False
        self._fallback: dict[str, str] = {}
        self._fallback_expiry: dict[str, float] = {}

    @property
    def available(self) -> bool:
        return self._available

    async def connect(self) -> None:
        if not self._url:
            logger.warning("LIFE_KLINE_REDIS_URL 未配置，咨询状态将临时存于进程内存（仅开发可用）")
            self._available = False
            return
        try:
            import redis.asyncio as aioredis  # type: ignore

            self._client = aioredis.from_url(
                self._url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=3,
                socket_timeout=3,
                health_check_interval=30,
            )
            await self._client.ping()
            self._available = True
            logger.info("Redis 已连接，咨询状态将外置存储")
        except Exception as exc:  # pragma: no cover - depends on env
            logger.warning("Redis 连接失败，降级为进程内存（不可用于生产）：%s", exc)
            self._client = None
            self._available = False

    async def close(self) -> None:
        if self._client is not None:
            try:
                await self._client.aclose()
            except Exception:  # pragma: no cover
                logger.exception("关闭 Redis 连接失败")
            finally:
                self._client = None
                self._available = False

    async def get_json(self, key: str) -> dict[str, Any] | None:
        raw = await self._get(key)
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except (TypeError, ValueError):
            return None

    async def set_json(self, key: str, value: dict[str, Any], *, ttl: int | None = None) -> None:
        payload = json.dumps(value, ensure_ascii=False, default=str)
        await self._set(key, payload, ttl=ttl or self.SESSION_TTL_SECONDS)

    async def delete(self, key: str) -> None:
        if self._available and self._client is not None:
            await self._client.delete(key)
            return
        self._fallback.pop(key, None)
        self._fallback_expiry.pop(key, None)

    async def increment_with_cap(
        self,
        key: str,
        *,
        limit: int,
        ttl: int | None = None,
    ) -> tuple[int, bool]:
        """Atomically increment a counter and return (new_value, within_limit)."""
        if self._available and self._client is not None:
            pipe = self._client.pipeline()
            pipe.incr(key)
            pipe.expire(key, ttl or self._TOKEN_TTL_SECONDS)
            value, _ = await pipe.execute()
            return int(value), int(value) <= limit
        # Fallback: non-atomic but fine for single-process dev
        now = time.monotonic()
        current = int(self._fallback.get(key, "0"))
        expiry = self._fallback_expiry.get(key)
        if expiry is not None and expiry < now:
            current = 0
        current += 1
        self._fallback[key] = str(current)
        self._fallback_expiry[key] = now + (ttl or self._TOKEN_TTL_SECONDS)
        return current, current <= limit

    async def _get(self, key: str) -> str | None:
        if self._available and self._client is not None:
            return await self._client.get(key)
        now = time.monotonic()
        expiry = self._fallback_expiry.get(key)
        if expiry is not None and expiry < now:
            self._fallback.pop(key, None)
            self._fallback_expiry.pop(key, None)
            return None
        return self._fallback.get(key)

    async def _set(self, key: str, value: str, *, ttl: int) -> None:
        if self._available and self._client is not None:
            await self._client.set(key, value, ex=ttl)
            return
        self._fallback[key] = value
        self._fallback_expiry[key] = time.monotonic() + ttl


_store: RedisStore | None = None


def get_redis_store() -> RedisStore:
    global _store
    if _store is None:
        _store = RedisStore()
    return _store


async def run_with_redis_ready(
    store: RedisStore,
    action: Callable[[], Awaitable[Any]],
    *,
    unavailable_message: str,
) -> Any:
    """Guard an action that requires persisted state.

    When Redis is unavailable we surface a clear degradation rather than
    silently writing to process memory, so a multi-instance rollout never
    silently drops consultation state.
    """
    if not store.available:
        raise RuntimeError(unavailable_message)
    return await action()
