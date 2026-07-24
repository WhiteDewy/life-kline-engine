"""
DAO (Data Access Object) — 数据库访问层。

封装所有 SQL 操作，供 main.py 调用。所有 API 都用这一层，与
引擎逻辑解耦；测试也能替换底层存储。
"""
from __future__ import annotations

import json
from typing import Any, Optional

from .database import get_db, _uid, _now


# ──────────── 通用辅助 ───────────────────────────────────────────

def _rows_to_dicts(rows) -> list[dict]:
    return [dict(r) for r in rows]


# ──────────── 用户状态 ────────────────────────────────────────────

def get_user_state(user_id: str) -> dict:
    db = get_db()
    row = db.execute("SELECT * FROM user_state WHERE user_id=?", (user_id,)).fetchone()
    db.close()
    if row:
        d = dict(row)
        try:
            d["extra"] = json.loads(d.get("extra") or "{}")
        except Exception:
            d["extra"] = {}
        d["is_vip"] = bool(d.get("is_vip", 0))
        return d
    return {
        "user_id": user_id,
        "coins": 0,
        "is_vip": False,
        "vip_expire_at": "",
        "ai_usage_today": 0,
        "ai_usage_date": "",
        "extra": {},
    }


def upsert_user_state(user_id: str, **fields) -> dict:
    """按需更新用户状态字段。"""
    db = get_db()
    existing = db.execute(
        "SELECT user_id FROM user_state WHERE user_id=?", (user_id,)
    ).fetchone()
    if not existing:
        extra_json = json.dumps(fields.get("extra", {}), ensure_ascii=False)
        db.execute(
            """
            INSERT INTO user_state
            (user_id, coins, is_vip, vip_expire_at, ai_usage_today, ai_usage_date, extra, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                int(fields.get("coins", 0)),
                1 if fields.get("is_vip") else 0,
                fields.get("vip_expire_at", ""),
                int(fields.get("ai_usage_today", 0)),
                fields.get("ai_usage_date", ""),
                extra_json,
                _now(),
            ),
        )
    else:
        sets = []
        values = []
        if "coins" in fields:
            sets.append("coins=?"); values.append(int(fields["coins"]))
        if "is_vip" in fields:
            sets.append("is_vip=?"); values.append(1 if fields["is_vip"] else 0)
        if "vip_expire_at" in fields:
            sets.append("vip_expire_at=?"); values.append(fields["vip_expire_at"])
        if "ai_usage_today" in fields:
            sets.append("ai_usage_today=?"); values.append(int(fields["ai_usage_today"]))
        if "ai_usage_date" in fields:
            sets.append("ai_usage_date=?"); values.append(fields["ai_usage_date"])
        if "extra" in fields and isinstance(fields["extra"], dict):
            sets.append("extra=?"); values.append(json.dumps(fields["extra"], ensure_ascii=False))
        if sets:
            sets.append("updated_at=?"); values.append(_now())
            values.append(user_id)
            db.execute(
                f"UPDATE user_state SET {', '.join(sets)} WHERE user_id=?",
                values,
            )
    db.commit()
    db.close()
    return get_user_state(user_id)


def increment_ai_usage(user_id: str) -> int:
    """记录每日 AI 调用次数，返回最新计数值。"""
    from datetime import datetime, timezone
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    db = get_db()
    row = db.execute(
        "SELECT ai_usage_today, ai_usage_date FROM user_state WHERE user_id=?",
        (user_id,),
    ).fetchone()
    if not row:
        db.execute(
            "INSERT INTO user_state (user_id, ai_usage_today, ai_usage_date, updated_at) VALUES (?, ?, ?, ?)",
            (user_id, 1, today, _now()),
        )
        db.commit()
        db.close()
        return 1
    cur_count = int(row["ai_usage_today"] or 0)
    if row["ai_usage_date"] != today:
        cur_count = 0
    new_count = cur_count + 1
    db.execute(
        "UPDATE user_state SET ai_usage_today=?, ai_usage_date=?, updated_at=? WHERE user_id=?",
        (new_count, today, _now(), user_id),
    )
    db.commit()
    db.close()
    return new_count


# ──────────── 星灵日记 ───────────────────────────────────────────

def insert_star_diary(
    report_id: str,
    keywords: list[str],
    entry_text: str,
    chat_context: str = "",
    spirit_planet: str = "",
    spirit_planet_label: str = "",
    mood_emoji: str = "",
    user_id: str = "",
    profile_id: str = "",
    source: str = "chat",
    entry_date: Optional[str] = None,
    user_content_summary: str = "",
    spirit_content_summary: str = "",
    diary_style: str = "summary",
    energy_level: int = 50,
    topic_tag: str = "",
    evening_expectation: str = "",
) -> dict:
    from datetime import datetime, timezone
    if not entry_date:
        entry_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    db = get_db()
    entry_id = _uid()
    db.execute(
        """
        INSERT INTO star_diary
        (id, report_id, user_id, profile_id, entry_date, keywords, entry_text,
         chat_context, user_content_summary, spirit_content_summary,
         spirit_planet, spirit_planet_label, mood_emoji,
         diary_style, energy_level, topic_tag, evening_expectation,
         source, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            entry_id,
            report_id,
            user_id,
            profile_id,
            entry_date,
            json.dumps(keywords or [], ensure_ascii=False),
            entry_text,
            chat_context,
            user_content_summary or "",
            spirit_content_summary or "",
            spirit_planet or "",
            spirit_planet_label or "",
            mood_emoji or "",
            diary_style or "summary",
            int(energy_level or 50),
            topic_tag or "",
            evening_expectation or "",
            source or "chat",
            _now(),
            _now(),
        ),
    )
    db.commit()
    row = db.execute(
        "SELECT * FROM star_diary WHERE id=?", (entry_id,)
    ).fetchone()
    db.close()
    return _row_to_diary(row) if row else {}


def list_star_diary(
    report_id: str = "",
    user_id: str = "",
    limit: int = 30,
    offset: int = 0,
) -> list[dict]:
    db = get_db()
    if report_id:
        rows = db.execute(
            "SELECT * FROM star_diary WHERE report_id=? ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (report_id, limit, offset),
        ).fetchall()
    elif user_id:
        rows = db.execute(
            "SELECT * FROM star_diary WHERE user_id=? ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (user_id, limit, offset),
        ).fetchall()
    else:
        rows = db.execute(
            "SELECT * FROM star_diary ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
    db.close()
    return [_row_to_diary(r) for r in rows]


def count_star_diary(report_id: str = "", user_id: str = "") -> int:
    db = get_db()
    if report_id:
        n = db.execute(
            "SELECT COUNT(*) AS c FROM star_diary WHERE report_id=?",
            (report_id,),
        ).fetchone()["c"]
    elif user_id:
        n = db.execute(
            "SELECT COUNT(*) AS c FROM star_diary WHERE user_id=?",
            (user_id,),
        ).fetchone()["c"]
    else:
        n = db.execute("SELECT COUNT(*) AS c FROM star_diary").fetchone()["c"]
    db.close()
    return int(n or 0)


def get_star_diary_by_id(entry_id: str) -> Optional[dict]:
    db = get_db()
    row = db.execute(
        "SELECT * FROM star_diary WHERE id=?", (entry_id,)
    ).fetchone()
    db.close()
    return _row_to_diary(row) if row else None


def update_star_diary(
    entry_id: str,
    user_id: str,
    entry_text: Optional[str] = None,
    keywords: Optional[list[str]] = None,
    mood_emoji: Optional[str] = None,
    diary_style: Optional[str] = None,
    evening_expectation: Optional[str] = None,
    topic_tag: Optional[str] = None,
    energy_level: Optional[int] = None,
) -> Optional[dict]:
    """更新日记条目。仅允许更新自己的日记（user_id 校验）。

    返回更新后的行 dict；若条目不存在或不属于该 user_id，则返回 None。
    """
    db = get_db()
    existing = db.execute(
        "SELECT id, user_id FROM star_diary WHERE id=?", (entry_id,)
    ).fetchone()
    if not existing:
        db.close()
        return None
    # 用户本人校验（空 user_id 表示历史匿名数据，管理员接口已绕开此处）
    if user_id and existing["user_id"] and existing["user_id"] != user_id:
        db.close()
        return None

    sets: list[str] = []
    values: list[Any] = []
    if entry_text is not None:
        sets.append("entry_text=?")
        values.append(entry_text)
    if keywords is not None:
        sets.append("keywords=?")
        values.append(json.dumps(keywords or [], ensure_ascii=False))
    if mood_emoji is not None:
        sets.append("mood_emoji=?")
        values.append(mood_emoji)
    if diary_style is not None:
        sets.append("diary_style=?")
        values.append(diary_style)
    if evening_expectation is not None:
        sets.append("evening_expectation=?")
        values.append(evening_expectation)
    if topic_tag is not None:
        sets.append("topic_tag=?")
        values.append(topic_tag)
    if energy_level is not None:
        sets.append("energy_level=?")
        values.append(int(energy_level))

    if not sets:
        db.close()
        return _row_to_diary(existing)

    sets.append("updated_at=?")
    values.append(_now())
    values.append(entry_id)
    db.execute(
        f"UPDATE star_diary SET {', '.join(sets)} WHERE id=?",
        values,
    )
    db.commit()
    row = db.execute(
        "SELECT * FROM star_diary WHERE id=?", (entry_id,)
    ).fetchone()
    db.close()
    return _row_to_diary(row) if row else None


def delete_star_diary(entry_id: str, user_id: str = "") -> bool:
    db = get_db()
    if user_id:
        cur = db.execute(
            "DELETE FROM star_diary WHERE id=? AND user_id=?",
            (entry_id, user_id),
        )
    else:
        cur = db.execute("DELETE FROM star_diary WHERE id=?", (entry_id,))
    db.commit()
    deleted = cur.rowcount > 0
    db.close()
    return deleted


def _row_to_diary(row) -> dict:
    if not row:
        return {}
    d = dict(row)
    try:
        d["keywords"] = json.loads(d.get("keywords") or "[]")
    except Exception:
        d["keywords"] = []
    d["id"] = d["id"]
    d["report_id"] = d["report_id"]
    d["date"] = d["entry_date"]
    d["text"] = d["entry_text"]
    d["created_at"] = d["created_at"]
    # 多风格字段（缺列时 SQLAlchemy / sqlite3.Row 没有这些 key，统一用 .get）
    d["diary_style"] = d.get("diary_style", "summary")
    d["energy_level"] = int(d.get("energy_level", 50) or 50)
    d["topic_tag"] = d.get("topic_tag", "")
    d["evening_expectation"] = d.get("evening_expectation", "")
    d["spirit_planet_label"] = d.get("spirit_planet_label", "")
    return d


# ──────────── 报告存储 ────────────────────────────────────────────

def save_report(
    report_id: str,
    user_id: str,
    profile_id: str,
    analysis_type: str,
    report_data: Any,
    engine_version: str = "1.0.0",
    kline_summary: str = "",
    created_at: Optional[str] = None,
) -> None:
    db = get_db()
    db.execute(
        "DELETE FROM reports WHERE id=?",
        (report_id,),
    )
    db.execute(
        """
        INSERT INTO reports
        (id, profile_id, user_id, analysis_type, report_data,
         engine_version, kline_summary, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            report_id,
            profile_id,
            user_id,
            analysis_type,
            json.dumps(report_data, ensure_ascii=False),
            engine_version,
            kline_summary,
            created_at or _now(),
        ),
    )
    db.commit()
    db.close()


def load_report(report_id: str) -> Optional[dict]:
    db = get_db()
    row = db.execute(
        "SELECT * FROM reports WHERE id=?", (report_id,)
    ).fetchone()
    db.close()
    if not row:
        return None
    d = dict(row)
    try:
        d["report_data"] = json.loads(d["report_data"])
    except Exception:
        d["report_data"] = {}
    return d


def list_reports_by_user(user_id: str, limit: int = 50) -> list[dict]:
    db = get_db()
    rows = db.execute(
        "SELECT id, profile_id, analysis_type, kline_summary, created_at "
        "FROM reports WHERE user_id=? ORDER BY created_at DESC LIMIT ?",
        (user_id, limit),
    ).fetchall()
    db.close()
    return _rows_to_dicts(rows)


# ──────────── 成长追踪 ────────────────────────────────────────────

def insert_growth_conversation(
    report_id: str,
    sign: str,
    topic: str,
    user_message: str,
    character_response: str,
    user_id: str = "",
    emotional_context: str = "general",
) -> dict:
    db = get_db()
    convo_id = _uid()
    db.execute(
        """
        INSERT INTO growth_conversations
        (id, report_id, user_id, sign, topic, user_message,
         character_response, emotional_context, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            convo_id, report_id, user_id, sign, topic,
            user_message[:200], character_response[:200],
            emotional_context, _now(),
        ),
    )
    db.commit()
    row = db.execute(
        "SELECT * FROM growth_conversations WHERE id=?", (convo_id,)
    ).fetchone()
    db.close()
    return _rows_to_dicts([row])[0] if row else {}


def list_growth_conversations(
    report_id: str, sign: str = "", limit: int = 50
) -> list[dict]:
    db = get_db()
    if sign:
        rows = db.execute(
            "SELECT * FROM growth_conversations WHERE report_id=? AND sign=? "
            "ORDER BY created_at ASC LIMIT ?",
            (report_id, sign, limit),
        ).fetchall()
    else:
        rows = db.execute(
            "SELECT * FROM growth_conversations WHERE report_id=? "
            "ORDER BY created_at ASC LIMIT ?",
            (report_id, limit),
        ).fetchall()
    db.close()
    return _rows_to_dicts(rows)


def count_growth_conversations(report_id: str) -> int:
    db = get_db()
    n = db.execute(
        "SELECT COUNT(*) AS c FROM growth_conversations WHERE report_id=?",
        (report_id,),
    ).fetchone()["c"]
    db.close()
    return int(n or 0)


def insert_growth_milestone(
    report_id: str,
    milestone_type: str,
    sign: str,
    description: str,
    user_id: str = "",
) -> Optional[dict]:
    """去重后插入里程碑，返回插入后的行（已存在则返回 None）。"""
    db = get_db()
    existing = db.execute(
        "SELECT id FROM growth_milestones WHERE report_id=? AND milestone_type=? AND sign=?",
        (report_id, milestone_type, sign),
    ).fetchone()
    if existing:
        db.close()
        return None
    m_id = _uid()
    db.execute(
        """
        INSERT INTO growth_milestones
        (id, report_id, user_id, milestone_type, sign, achieved_at, description)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (m_id, report_id, user_id, milestone_type, sign, _now(), description),
    )
    db.commit()
    row = db.execute(
        "SELECT * FROM growth_milestones WHERE id=?", (m_id,)
    ).fetchone()
    db.close()
    return _rows_to_dicts([row])[0] if row else None


def list_growth_milestones(report_id: str) -> list[dict]:
    db = get_db()
    rows = db.execute(
        "SELECT * FROM growth_milestones WHERE report_id=? ORDER BY achieved_at ASC",
        (report_id,),
    ).fetchall()
    db.close()
    return _rows_to_dicts(rows)


def upsert_daily_visit(
    report_id: str,
    visit_date: str,
    featured_signs: list[str],
    activation_scores: dict,
    user_id: str = "",
) -> None:
    db = get_db()
    existing = db.execute(
        "SELECT id FROM growth_daily_visits WHERE report_id=? AND visit_date=?",
        (report_id, visit_date),
    ).fetchone()
    payload_signs = json.dumps(featured_signs or [], ensure_ascii=False)
    payload_scores = json.dumps(activation_scores or {}, ensure_ascii=False)
    if existing:
        db.execute(
            "UPDATE growth_daily_visits SET featured_signs=?, activation_scores=? WHERE id=?",
            (payload_signs, payload_scores, existing["id"]),
        )
    else:
        db.execute(
            """
            INSERT INTO growth_daily_visits
            (id, report_id, user_id, visit_date, featured_signs,
             activation_scores, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                _uid(), report_id, user_id, visit_date,
                payload_signs, payload_scores, _now(),
            ),
        )
    db.commit()
    db.close()


def list_growth_visits(report_id: str, limit: int = 60) -> list[dict]:
    db = get_db()
    rows = db.execute(
        "SELECT * FROM growth_daily_visits WHERE report_id=? "
        "ORDER BY visit_date DESC LIMIT ?",
        (report_id, limit),
    ).fetchall()
    db.close()
    out = []
    for r in rows:
        d = dict(r)
        try:
            d["featured_signs"] = json.loads(d.get("featured_signs") or "[]")
        except Exception:
            d["featured_signs"] = []
        try:
            d["activation_scores"] = json.loads(d.get("activation_scores") or "{}")
        except Exception:
            d["activation_scores"] = {}
        out.append(d)
    return out


def compute_growth_summary(report_id: str) -> dict:
    """从 DB 重新聚合成前端期待的 summary 结构。"""
    convs = list_growth_conversations(report_id, limit=1000)
    visits = list_growth_visits(report_id, limit=60)
    milestones = list_growth_milestones(report_id)

    total = len(convs)
    sign_counts: dict[str, int] = {}
    topic_counts: dict[str, int] = {}
    affinity: dict[str, float] = {s: 0.0 for s in [
        "ARIES", "TAURUS", "GEMINI", "CANCER", "LEO", "VIRGO",
        "LIBRA", "SCORPIO", "SAGITTARIUS", "CAPRICORN", "AQUARIUS", "PISCES",
    ]}

    for c in convs:
        sign_counts[c["sign"]] = sign_counts.get(c["sign"], 0) + 1
        topic_counts[c["topic"]] = topic_counts.get(c["topic"], 0) + 1
        inc = 0.2 if c.get("emotional_context") == "general" else 0.5
        affinity[c["sign"]] = min(affinity.get(c["sign"], 0.0) + inc, 10.0)

    most_engaged = ""
    if sign_counts:
        most_engaged = max(sign_counts, key=sign_counts.get)

    # 连续天数
    from datetime import date, timedelta
    dates = sorted({v["visit_date"] for v in visits}, reverse=True)
    streak = 0
    if dates:
        expected = date.today()
        ok = True
        for ds in dates:
            d = date.fromisoformat(ds)
            if d == expected:
                streak += 1
                expected = expected - timedelta(days=1)
            elif d < expected and ok:
                break
            elif d < expected:
                break

    first = convs[0]["created_at"][:10] if convs else ""
    last = convs[-1]["created_at"][:10] if convs else ""

    return {
        "total_conversations": total,
        "most_engaged_character": most_engaged,
        "favorite_topics": dict(sorted(topic_counts.items(), key=lambda x: -x[1])),
        "streak_days": streak,
        "character_affinity": {k: round(v, 1) for k, v in affinity.items()},
        "milestones_achieved": len(milestones),
        "first_interaction_date": first,
        "last_interaction_date": last,
    }


# ──────────── 聊天消息 ─────────────────────────────────────────────

def insert_chat_message(
    user_id: str,
    role: str,
    content: str,
    report_id: str = "",
    spirit_planet: str = "",
    session_id: str = "",
) -> dict:
    db = get_db()
    m_id = _uid()
    db.execute(
        """
        INSERT INTO chat_messages
        (id, session_id, user_id, report_id, role, spirit_planet, content, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (m_id, session_id or None, user_id, report_id, role, spirit_planet, content, _now()),
    )
    db.commit()
    row = db.execute(
        "SELECT * FROM chat_messages WHERE id=?", (m_id,)
    ).fetchone()
    db.close()
    return _rows_to_dicts([row])[0] if row else {}


def list_chat_messages(
    report_id: str = "", user_id: str = "", limit: int = 100
) -> list[dict]:
    db = get_db()
    if report_id and user_id:
        rows = db.execute(
            "SELECT * FROM chat_messages WHERE report_id=? AND user_id=? "
            "ORDER BY created_at ASC LIMIT ?",
            (report_id, user_id, limit),
        ).fetchall()
    elif user_id:
        rows = db.execute(
            "SELECT * FROM chat_messages WHERE user_id=? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
    else:
        rows = db.execute(
            "SELECT * FROM chat_messages ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    db.close()
    return _rows_to_dicts(rows)


# ════════════════════════════════════════════════════════════════
# 后台管理 (Admin CMS) DAO
# ════════════════════════════════════════════════════════════════

# ──────────── 用户管理 ─────────────────────────────────────────

def list_all_users(
    keyword: str = "",
    is_disabled: Optional[int] = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict]:
    db = get_db()
    where = ["1=1"]
    params: list = []
    if keyword:
        where.append("(phone LIKE ? OR nickname LIKE ?)")
        kw = f"%{keyword}%"
        params.extend([kw, kw])
    if is_disabled is None:
        where.append("(u.is_disabled IS NULL OR u.is_disabled=0)")
    elif is_disabled == 1:
        where.append("u.is_disabled=1")
    else:
        where.append("(u.is_disabled IS NULL OR u.is_disabled=0)")
    where.append("u.deleted_at IS NULL OR u.deleted_at=''")
    sql = (
        "SELECT u.*, "
        "(SELECT COUNT(*) FROM reports r WHERE r.user_id=u.id) AS report_count, "
        "(SELECT COUNT(*) FROM star_diary d WHERE d.user_id=u.id) AS diary_count "
        f"FROM users u WHERE {' AND '.join(where)} "
        "ORDER BY u.created_at DESC LIMIT ? OFFSET ?"
    )
    params.extend([limit, offset])
    rows = db.execute(sql, params).fetchall()
    db.close()
    return _rows_to_dicts(rows)


def count_all_users(
    keyword: str = "", is_disabled: Optional[int] = None
) -> int:
    db = get_db()
    where = ["1=1"]
    params: list = []
    if keyword:
        where.append("(phone LIKE ? OR nickname LIKE ?)")
        kw = f"%{keyword}%"
        params.extend([kw, kw])
    if is_disabled is None:
        where.append("(is_disabled IS NULL OR is_disabled=0)")
    elif is_disabled == 1:
        where.append("is_disabled=1")
    where.append("deleted_at IS NULL OR deleted_at=''")
    sql = f"SELECT COUNT(*) AS c FROM users WHERE {' AND '.join(where)}"
    n = db.execute(sql, params).fetchone()["c"]
    db.close()
    return int(n or 0)


def set_user_disabled(user_id: str, disabled: bool) -> None:
    db = get_db()
    db.execute(
        "UPDATE users SET is_disabled=?, disabled_at=? WHERE id=?",
        (1 if disabled else 0, _now() if disabled else "", user_id),
    )
    db.commit()
    db.close()


def update_user_profile(user_id: str, nickname: Optional[str] = None) -> None:
    db = get_db()
    if nickname is not None:
        db.execute(
            "UPDATE users SET nickname=? WHERE id=?",
            (nickname, user_id),
        )
    db.commit()
    db.close()


def soft_delete_user(user_id: str) -> None:
    db = get_db()
    db.execute(
        "UPDATE users SET deleted_at=?, is_disabled=1 WHERE id=?",
        (_now(), user_id),
    )
    db.commit()
    db.close()


# ──────────── 日记管理 ─────────────────────────────────────────

def list_all_diary(
    keyword: str = "",
    status: str = "",
    spirit_planet: str = "",
    user_id: str = "",
    limit: int = 50,
    offset: int = 0,
) -> list[dict]:
    db = get_db()
    where = ["1=1"]
    params: list = []
    if keyword:
        where.append("(entry_text LIKE ? OR chat_context LIKE ?)")
        kw = f"%{keyword}%"
        params.extend([kw, kw])
    if spirit_planet:
        where.append("spirit_planet=?")
        params.append(spirit_planet)
    if user_id:
        where.append("user_id=?")
        params.append(user_id)
    if status == "all":
        pass
    elif status == "visible":
        where.append("(m.id IS NULL OR m.status='visible')")
    elif status == "hidden":
        where.append("m.status='hidden'")
    elif status == "flagged":
        where.append("m.status='flagged'")

    sql = (
        "SELECT d.*, COALESCE(m.status, 'visible') AS mod_status, m.reason AS mod_reason "
        "FROM star_diary d LEFT JOIN diary_moderation m ON d.id = m.diary_id "
        f"WHERE {' AND '.join(where)} "
        "ORDER BY d.created_at DESC LIMIT ? OFFSET ?"
    )
    params.extend([limit, offset])
    rows = db.execute(sql, params).fetchall()
    db.close()
    return [_row_to_diary_full(r) for r in rows]


def count_all_diary(
    keyword: str = "", status: str = "",
    spirit_planet: str = "", user_id: str = "",
) -> int:
    db = get_db()
    where = ["1=1"]
    params: list = []
    if keyword:
        where.append("(entry_text LIKE ? OR chat_context LIKE ?)")
        kw = f"%{keyword}%"
        params.extend([kw, kw])
    if spirit_planet:
        where.append("spirit_planet=?")
        params.append(spirit_planet)
    if user_id:
        where.append("user_id=?")
        params.append(user_id)
    if status == "visible":
        where.append("(m.id IS NULL OR m.status='visible')")
    elif status == "hidden":
        where.append("m.status='hidden'")
    elif status == "flagged":
        where.append("m.status='flagged'")
    sql = (
        "SELECT COUNT(*) AS c FROM star_diary d "
        "LEFT JOIN diary_moderation m ON d.id = m.diary_id "
        f"WHERE {' AND '.join(where)}"
    )
    n = db.execute(sql, params).fetchone()["c"]
    db.close()
    return int(n or 0)


def set_diary_moderation(
    diary_id: str, status: str, moderator_id: str = "", reason: str = ""
) -> dict:
    db = get_db()
    existing = db.execute(
        "SELECT id FROM diary_moderation WHERE diary_id=?", (diary_id,)
    ).fetchone()
    if existing:
        db.execute(
            """UPDATE diary_moderation
               SET status=?, moderator_id=?, reason=?, updated_at=?
               WHERE diary_id=?""",
            (status, moderator_id, reason, _now(), diary_id),
        )
    else:
        db.execute(
            """INSERT INTO diary_moderation
               (diary_id, status, moderator_id, reason, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (diary_id, status, moderator_id, reason, _now(), _now()),
        )
    db.commit()
    row = db.execute(
        "SELECT * FROM diary_moderation WHERE diary_id=?", (diary_id,)
    ).fetchone()
    db.close()
    return _rows_to_dicts([row])[0] if row else {}


def _row_to_diary_full(row) -> dict:
    if not row:
        return {}
    d = _row_to_diary(row)
    d["mod_status"] = row["mod_status"] if "mod_status" in row.keys() else "visible"
    d["mod_reason"] = row["mod_reason"] if "mod_reason" in row.keys() else ""
    return d


# ──────────── 报告管理 ─────────────────────────────────────────

def list_all_reports(
    keyword: str = "", user_id: str = "",
    analysis_type: str = "", limit: int = 50, offset: int = 0,
) -> list[dict]:
    db = get_db()
    where = ["1=1"]
    params: list = []
    if user_id:
        where.append("r.user_id=?")
        params.append(user_id)
    if analysis_type:
        where.append("r.analysis_type=?")
        params.append(analysis_type)
    if keyword:
        where.append("(r.id LIKE ? OR r.kline_summary LIKE ?)")
        kw = f"%{keyword}%"
        params.extend([kw, kw])
    sql = (
        "SELECT r.id, r.user_id, r.profile_id, r.analysis_type, "
        "r.kline_summary, r.created_at, "
        "u.phone, u.nickname "
        "FROM reports r LEFT JOIN users u ON r.user_id=u.id "
        f"WHERE {' AND '.join(where)} "
        "ORDER BY r.created_at DESC LIMIT ? OFFSET ?"
    )
    params.extend([limit, offset])
    rows = db.execute(sql, params).fetchall()
    db.close()
    return _rows_to_dicts(rows)


def count_all_reports(
    keyword: str = "", user_id: str = "", analysis_type: str = ""
) -> int:
    db = get_db()
    where = ["1=1"]
    params: list = []
    if user_id:
        where.append("user_id=?"); params.append(user_id)
    if analysis_type:
        where.append("analysis_type=?"); params.append(analysis_type)
    if keyword:
        where.append("(id LIKE ? OR kline_summary LIKE ?)")
        kw = f"%{keyword}%"
        params.extend([kw, kw])
    sql = f"SELECT COUNT(*) AS c FROM reports WHERE {' AND '.join(where)}"
    n = db.execute(sql, params).fetchone()["c"]
    db.close()
    return int(n or 0)


# ──────────── 统计 ─────────────────────────────────────────────

def get_system_stats() -> dict:
    db = get_db()
    out: dict[str, Any] = {}

    out["total_users"] = int(db.execute(
        "SELECT COUNT(*) c FROM users WHERE deleted_at IS NULL OR deleted_at=''"
    ).fetchone()["c"] or 0)
    out["active_users"] = int(db.execute(
        "SELECT COUNT(*) c FROM users "
        "WHERE (is_disabled IS NULL OR is_disabled=0) "
        "AND (deleted_at IS NULL OR deleted_at='')"
    ).fetchone()["c"] or 0)
    out["disabled_users"] = int(db.execute(
        "SELECT COUNT(*) c FROM users WHERE is_disabled=1"
    ).fetchone()["c"] or 0)
    out["total_profiles"] = int(db.execute(
        "SELECT COUNT(*) c FROM profiles"
    ).fetchone()["c"] or 0)
    out["total_reports"] = int(db.execute(
        "SELECT COUNT(*) c FROM reports"
    ).fetchone()["c"] or 0)
    out["total_diary"] = int(db.execute(
        "SELECT COUNT(*) c FROM star_diary"
    ).fetchone()["c"] or 0)
    out["hidden_diary"] = int(db.execute(
        "SELECT COUNT(*) c FROM diary_moderation WHERE status='hidden'"
    ).fetchone()["c"] or 0)
    out["flagged_diary"] = int(db.execute(
        "SELECT COUNT(*) c FROM diary_moderation WHERE status='flagged'"
    ).fetchone()["c"] or 0)
    out["total_consultations"] = int(db.execute(
        "SELECT COUNT(*) c FROM consultation_reports"
    ).fetchone()["c"] or 0)
    out["total_checkins"] = int(db.execute(
        "SELECT COUNT(*) c FROM checkins"
    ).fetchone()["c"] or 0)
    out["total_growth_convos"] = int(db.execute(
        "SELECT COUNT(*) c FROM growth_conversations"
    ).fetchone()["c"] or 0)

    # 7 日活跃
    from datetime import datetime, timedelta, timezone
    seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    out["active_users_7d"] = int(db.execute(
        "SELECT COUNT(DISTINCT user_id) c FROM reports WHERE created_at>=?",
        (seven_days_ago,),
    ).fetchone()["c"] or 0)

    # 报表类型分布
    rows = db.execute(
        "SELECT analysis_type, COUNT(*) c FROM reports "
        "GROUP BY analysis_type ORDER BY c DESC"
    ).fetchall()
    out["reports_by_type"] = {r["analysis_type"]: r["c"] for r in rows}

    # 用户创建 14 日趋势
    rows2 = db.execute(
        "SELECT substr(created_at, 1, 10) AS d, COUNT(*) c FROM users "
        "WHERE created_at >= ? GROUP BY d ORDER BY d ASC",
        ((datetime.now(timezone.utc) - timedelta(days=14)).isoformat(),),
    ).fetchall()
    out["user_signup_trend"] = [{"date": r["d"], "count": r["c"]} for r in rows2]

    # 日记 14 日趋势
    rows3 = db.execute(
        "SELECT substr(created_at, 1, 10) AS d, COUNT(*) c FROM star_diary "
        "WHERE created_at >= ? GROUP BY d ORDER BY d ASC",
        ((datetime.now(timezone.utc) - timedelta(days=14)).isoformat(),),
    ).fetchall()
    out["diary_trend"] = [{"date": r["d"], "count": r["c"]} for r in rows3]

    db.close()
    return out


# ──────────── 管理员账号 ───────────────────────────────────────

def get_admin_by_username(username: str) -> Optional[dict]:
    db = get_db()
    row = db.execute(
        "SELECT * FROM admins WHERE username=?", (username,)
    ).fetchone()
    db.close()
    return _rows_to_dicts([row])[0] if row else None


def update_admin_last_login(admin_id: str) -> None:
    db = get_db()
    db.execute(
        "UPDATE admins SET last_login_at=? WHERE id=?", (_now(), admin_id)
    )
    db.commit()
    db.close()


def create_admin(
    username: str, password_hash: str, role: str = "admin"
) -> dict:
    db = get_db()
    admin_id = _uid()
    db.execute(
        """INSERT INTO admins
           (id, username, password_hash, role, is_active, created_at)
           VALUES (?, ?, ?, ?, 1, ?)""",
        (admin_id, username, password_hash, role, _now()),
    )
    db.commit()
    row = db.execute("SELECT * FROM admins WHERE id=?", (admin_id,)).fetchone()
    db.close()
    return _rows_to_dicts([row])[0] if row else {}


def list_admins() -> list[dict]:
    db = get_db()
    rows = db.execute(
        "SELECT id, username, role, is_active, created_at, last_login_at "
        "FROM admins ORDER BY created_at ASC"
    ).fetchall()
    db.close()
    return _rows_to_dicts(rows)


# ──────────── 审计日志 ─────────────────────────────────────────

def insert_audit_log(
    admin_id: str,
    admin_username: str,
    action: str,
    target_type: str,
    target_id: str = "",
    detail: str = "",
    ip: str = "",
) -> None:
    db = get_db()
    db.execute(
        """INSERT INTO audit_logs
           (admin_id, admin_username, action, target_type, target_id,
            detail, ip, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            admin_id, admin_username, action, target_type, target_id,
            detail, ip, _now(),
        ),
    )
    db.commit()
    db.close()


def list_audit_logs(
    admin_username: str = "", action: str = "",
    target_type: str = "", limit: int = 50, offset: int = 0,
) -> list[dict]:
    db = get_db()
    where = ["1=1"]
    params: list = []
    if admin_username:
        where.append("admin_username=?"); params.append(admin_username)
    if action:
        where.append("action=?"); params.append(action)
    if target_type:
        where.append("target_type=?"); params.append(target_type)
    sql = (
        "SELECT * FROM audit_logs "
        f"WHERE {' AND '.join(where)} "
        "ORDER BY created_at DESC LIMIT ? OFFSET ?"
    )
    params.extend([limit, offset])
    rows = db.execute(sql, params).fetchall()
    db.close()
    return _rows_to_dicts(rows)


def count_audit_logs(
    admin_username: str = "", action: str = "", target_type: str = ""
) -> int:
    db = get_db()
    where = ["1=1"]
    params: list = []
    if admin_username:
        where.append("admin_username=?"); params.append(admin_username)
    if action:
        where.append("action=?"); params.append(action)
    if target_type:
        where.append("target_type=?"); params.append(target_type)
    sql = (
        f"SELECT COUNT(*) c FROM audit_logs WHERE {' AND '.join(where)}"
    )
    n = db.execute(sql, params).fetchone()["c"]
    db.close()
    return int(n or 0)


# ──────────── 系统设置 ─────────────────────────────────────────

def get_setting(key: str, default: str = "") -> str:
    db = get_db()
    row = db.execute(
        "SELECT value FROM system_settings WHERE key=?", (key,)
    ).fetchone()
    db.close()
    return row["value"] if row else default


def set_setting(key: str, value: str) -> None:
    db = get_db()
    db.execute(
        """INSERT INTO system_settings (key, value, updated_at)
           VALUES (?, ?, ?)
           ON CONFLICT(key) DO UPDATE SET value=?, updated_at=?""",
        (key, value, _now(), value, _now()),
    )
    db.commit()
    db.close()


def list_settings() -> list[dict]:
    db = get_db()
    rows = db.execute(
        "SELECT key, value, updated_at FROM system_settings ORDER BY key ASC"
    ).fetchall()
    db.close()
    return _rows_to_dicts(rows)
