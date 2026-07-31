"""Repository for confirmed consultation insights (persistent layer).

Confirmed/partial insights are durable business data and live in SQLite (the
DAO layer), while short-term session state lives in Redis. This repository is
the single write path for the report/diary projection: it stores insight
drafts and decisions, exposes them grouped by planet/domain, and is what the
"living report" overlay reads from.

Pending-only drafts that the user has not yet decided on are kept in Redis
session state and never written here, so abandoned consultations leave no
personal data behind beyond the chat messages already stored.
"""
from __future__ import annotations

import json
import logging
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any, Iterable

from backend.database import get_db

logger = logging.getLogger(__name__)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _uid() -> str:
    return uuid.uuid4().hex[:16]


def ensure_schema(db: sqlite3.Connection) -> None:
    """Idempotently add the consultation_insights table and star_diary link.

    Kept additive and guarded by ``PRAGMA table_info`` so it is safe alongside
    the existing ``migrate_db`` flow without requiring a full Alembic rollout
    for the first iteration; the Alembic migration mirrors this DDL for
    production upgrades.
    """
    cols = {row[1] for row in db.execute("PRAGMA table_info(star_diary)").fetchall()}
    if "consultation_insight_id" not in cols:
        db.execute(
            "ALTER TABLE star_diary ADD COLUMN consultation_insight_id TEXT DEFAULT ''"
        )
    if "request_id" not in cols:
        db.execute("ALTER TABLE star_diary ADD COLUMN request_id TEXT DEFAULT ''")

    db.execute(
        """
        CREATE TABLE IF NOT EXISTS consultation_insights (
            id TEXT PRIMARY KEY,
            report_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            session_id TEXT NOT NULL,
            planet TEXT NOT NULL,
            topic_key TEXT NOT NULL,
            hypothesis_id TEXT DEFAULT '',
            evidence_json TEXT DEFAULT '[]',
            hypothesis_text TEXT DEFAULT '',
            user_quote TEXT DEFAULT '',
            summary TEXT DEFAULT '',
            domain_tags TEXT DEFAULT '[]',
            growth_action TEXT DEFAULT '',
            validation_status TEXT DEFAULT 'pending',
            revision INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    db.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_consultation_insight_request "
        "ON consultation_insights(id)"
    )
    db.execute(
        "CREATE INDEX IF NOT EXISTS idx_consultation_insight_report "
        "ON consultation_insights(report_id, user_id, updated_at DESC)"
    )
    db.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_star_diary_request "
        "ON star_diary(request_id) WHERE request_id <> ''"
    )


def upsert_insight(insight: dict[str, Any], *, report_id: str, user_id: str) -> dict[str, Any]:
    """Insert or update a confirmed/partial insight record."""
    db = get_db()
    ensure_schema(db)
    insight_id = insight.get("insight_id") or _uid()
    now = _now()
    payload = {
        "report_id": report_id,
        "user_id": user_id,
        "session_id": insight.get("session_id", ""),
        "planet": insight.get("planet", ""),
        "topic_key": insight.get("topic_key", ""),
        "hypothesis_id": insight.get("hypothesis_id", ""),
        "evidence_json": json.dumps(insight.get("evidence_ids", []), ensure_ascii=False),
        "hypothesis_text": insight.get("summary", ""),
        "user_quote": insight.get("user_quote", ""),
        "summary": insight.get("summary", ""),
        "domain_tags": json.dumps(insight.get("domain_tags", []), ensure_ascii=False),
        "growth_action": insight.get("growth_action", ""),
        "validation_status": insight.get("validation_status", "pending"),
        "updated_at": now,
    }
    existing = db.execute(
        "SELECT revision FROM consultation_insights WHERE id=?",
        (insight_id,),
    ).fetchone()
    if existing is None:
        payload["revision"] = 0
        db.execute(
            """
            INSERT INTO consultation_insights
            (id, report_id, user_id, session_id, planet, topic_key, hypothesis_id,
             evidence_json, hypothesis_text, user_quote, summary, domain_tags,
             growth_action, validation_status, revision, created_at, updated_at)
            VALUES (:id, :report_id, :user_id, :session_id, :planet, :topic_key,
                    :hypothesis_id, :evidence_json, :hypothesis_text, :user_quote,
                    :summary, :domain_tags, :growth_action, :validation_status,
                    :revision, :created_at, :updated_at)
            """,
            {"id": insight_id, "created_at": now, **payload},
        )
    else:
        payload["revision"] = int(existing["revision"] or 0) + 1
        set_clause = ", ".join(f"{col}=:{col}" for col in payload)
        db.execute(
            f"UPDATE consultation_insights SET {set_clause} WHERE id=:id",
            {"id": insight_id, **payload},
        )
    db.commit()
    db.close()
    return {"insight_id": insight_id, "revision": payload["revision"]}


def list_insights(report_id: str, *, user_id: str, limit: int = 50) -> list[dict[str, Any]]:
    db = get_db()
    ensure_schema(db)
    rows = db.execute(
        """
        SELECT id, report_id, user_id, session_id, planet, topic_key, hypothesis_id,
               evidence_json, hypothesis_text, user_quote, summary, domain_tags,
               growth_action, validation_status, revision, created_at, updated_at
        FROM consultation_insights
        WHERE report_id=? AND user_id=?
        ORDER BY updated_at DESC
        LIMIT ?
        """,
        (report_id, user_id, limit),
    ).fetchall()
    db.close()
    return [_row_to_dict(row) for row in rows]


def overlay_by_planet(report_id: str, *, user_id: str) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for item in list_insights(report_id, user_id=user_id):
        if item["validation_status"] not in {"confirmed", "partial"}:
            continue
        grouped.setdefault(item["planet"], []).append(item)
    return grouped


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    for field in ("evidence_json", "domain_tags"):
        try:
            data[field.replace("_json", "") if field == "evidence_json" else field] = (
                json.loads(data.get(field) or "[]")
            )
        except (TypeError, ValueError):
            data[field] = []
    data["evidence_ids"] = data.pop("evidence", [])
    return data


def delete_for_user(user_id: str) -> None:
    db = get_db()
    ensure_schema(db)
    db.execute("DELETE FROM consultation_insights WHERE user_id=?", (user_id,))
    db.commit()
    db.close()


def attach_insight_to_diary(entry_id: str, insight_id: str, *, request_id: str = "") -> None:
    db = get_db()
    ensure_schema(db)
    db.execute(
        "UPDATE star_diary SET consultation_insight_id=?, request_id=? WHERE id=?",
        (insight_id, request_id, entry_id),
    )
    db.commit()
    db.close()


def insights_for_report(report_id: str, *, user_id: str) -> Iterable[dict[str, Any]]:
    return list_insights(report_id, user_id=user_id)
