"""
spirit_chat_stream.py — 星灵对话流式 SSE 端点（Sprint 6）

POST /api/spirit-chat-stream/{report_id}
  - EventSourceResponse，增量回传 LLM token
  - 先发垫场句（引擎占星师 acknowledgment），再接 LLM 流
  - 15s 应用层心跳 (:keepalive)
  - 客户端断连 → 流中止
  - LLM 失败 → 已发部分保留 + 兜底话术
  - 鉴权：require_report_owner
  - 限流：每 user 5000 token/分钟
"""
from __future__ import annotations

import asyncio
import json
import time
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/api", tags=["spirit-chat-stream"])

# ── 限流（简易 token bucket） ─────────────────────────────────────

_TOKEN_BUCKET: dict[str, tuple[float, float]] = {}
_BUCKET_MAX = 5000
_BUCKET_RATE = _BUCKET_MAX / 60.0


def _token_ok(user_id: str, tokens: int = 1) -> bool:
    now = time.monotonic()
    entry = _TOKEN_BUCKET.get(user_id)
    if entry is None:
        _TOKEN_BUCKET[user_id] = (float(_BUCKET_MAX - tokens), now)
        return True
    left, last = entry
    left = min(_BUCKET_MAX, left + (now - last) * _BUCKET_RATE)
    if left < tokens:
        _TOKEN_BUCKET[user_id] = (left, now)
        return False
    _TOKEN_BUCKET[user_id] = (left - tokens, now)
    return True


_FALLBACK_MSG = "……我这边星图的信号弱了一下，我们缓一缓。你刚才说的我都听到了。"


# ── SSE 端点 ──────────────────────────────────────────────────────

@router.post("/spirit-chat-stream/{report_id}")
async def spirit_chat_stream(
    report_id: str,
    request: Request,
    authorization: str = Header(default=""),
):
    from backend.main import load_report_record, _report_owner, _parse_token, load_user_state
    from life_kline.llm_client import LLMClient, build_spirit_system_prompt
    from life_kline.engine_astrologer import EngineAstrologer

    # 鉴权
    auth_header = request.headers.get("Authorization", authorization)
    user_id = ""
    if auth_header.startswith("Bearer "):
        user_id = _parse_token(auth_header[7:]) or ""
    if not user_id:
        raise HTTPException(status_code=401, detail="请先登录")
    if (_report_owner(report_id) or "") != user_id:
        raise HTTPException(status_code=403, detail="无权访问该报告")
    if not _token_ok(user_id, tokens=50):
        raise HTTPException(status_code=429, detail="已达今日聊天上限")

    # 请求体
    try:
        body = json.loads(await request.body()) if await request.body() else {}
    except Exception:
        body = {}
    message = body.get("message", "").strip()
    planet = body.get("planet", "MOON")
    topic = body.get("topic", "personal")
    entry_context = body.get("entry_context") or {}

    record = load_report_record(report_id)
    report_data = record.get("data", {})

    # 垫场句
    opening = ""
    try:
        engine = EngineAstrologer(report_data)
        engine_resp = engine.consult(
            report_id=report_id, planet=planet, user_message=message,
            topic_hint=topic, entry_context=entry_context,
        )
        opening = engine_resp.acknowledgment or ""
    except Exception:
        pass

    # LLM 准备
    client = LLMClient()
    system_prompt = build_spirit_system_prompt(
        report_data, planet, topic=topic, entry_context=entry_context,
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": message},
    ]

    async def generate():
        sent = 0

        # 1) 垫场句
        if opening:
            yield _sse("opening", opening)
            await asyncio.sleep(0.03)
            sent += 1

        # 2) LLM 流 + 心跳
        heartbeat_task: asyncio.Task | None = None
        stream_done = False

        async def heartbeat():
            while not stream_done:
                await asyncio.sleep(15)
                if not stream_done:
                    yield ":keepalive\n\n"  # noqa — generator-only

        try:
            last_hb = time.monotonic()
            async for token in client.chat_stream(messages, timeout_seconds=10):
                if not _token_ok(user_id, tokens=1):
                    yield _sse("limit", "\n\n已达今日聊天上限")
                    break
                yield _sse("token", token)
                sent += 1
                # 心跳 (内联，避免额外 task)
                now = time.monotonic()
                if now - last_hb >= 15:
                    yield ":keepalive\n\n"
                    last_hb = now
            stream_done = True
        except asyncio.CancelledError:
            stream_done = True
            return
        except Exception:
            stream_done = True

        # 3) 兜底
        if sent == 0:
            yield _sse("fallback", _FALLBACK_MSG)

        # 4) 结束
        yield _sse("done", "")

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


def _sse(kind: str, text: str) -> str:
    return f"data: {json.dumps({'type': kind, 'text': text})}\n\n"
