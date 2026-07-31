"""Alembic-style migration scripts for consultation persistence.

A lightweight, dependency-free migration runner so the project does not need
to introduce Alembic as a hard runtime dependency for the first iteration.
The ``apply_migrations`` function is idempotent and called from ``init_db``;
each migration is also mirrored as standalone SQL files under
``backend/migrations/versions`` for a future Alembic migration path.
"""
from __future__ import annotations

import logging
import os
import sqlite3

from backend.database import get_db
from backend.repositories.consultation_repository import ensure_schema

logger = logging.getLogger(__name__)

VERSIONS_TABLE = "schema_versions"

MIGRATIONS: list[tuple[str, str]] = [
    (
        "20260730_consultation_insights",
        """
        -- Mirror of repositories.consultation_repository.ensure_schema.
        ALTER TABLE star_diary ADD COLUMN consultation_insight_id TEXT DEFAULT '';
        ALTER TABLE star_diary ADD COLUMN request_id TEXT DEFAULT '';

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
        );

        CREATE INDEX IF NOT EXISTS idx_consultation_insight_report
            ON consultation_insights(report_id, user_id, updated_at DESC);
        CREATE UNIQUE INDEX IF NOT EXISTS idx_star_diary_request
            ON star_diary(request_id) WHERE request_id <> '';
        """,
    ),
    (
        "20260731_spirit_consultation_messages",
        """
        CREATE TABLE IF NOT EXISTS spirit_consultation_messages (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            report_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            planet TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_spirit_consultation_messages_session
            ON spirit_consultation_messages(session_id, user_id, created_at ASC);
        """,
    ),
]


def _ensure_versions_table(db: sqlite3.Connection) -> None:
    db.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {VERSIONS_TABLE} (
            name TEXT PRIMARY KEY,
            applied_at TEXT NOT NULL
        )
        """
    )


def apply_migrations() -> list[str]:
    """Apply pending additive migrations idempotently; return applied names."""
    from datetime import datetime, timezone

    db = get_db()
    _ensure_versions_table(db)
    # The repository guard also runs additive ALTERs; call it once so the
    # schema is consistent even when only this runner executes.
    ensure_schema(db)

    applied: list[str] = []
    for name, script in MIGRATIONS:
        already = db.execute(
            f"SELECT name FROM {VERSIONS_TABLE} WHERE name=?", (name,)
        ).fetchone()
        if already is not None:
            continue
        try:
            db.executescript(script)
            db.execute(
                f"INSERT INTO {VERSIONS_TABLE} (name, applied_at) VALUES (?, ?)",
                (name, datetime.now(timezone.utc).isoformat()),
            )
            applied.append(name)
        except sqlite3.OperationalError as exc:
            # Additive ALTERs may already exist from ensure_schema; treat as
            # duplicate-column errors as already-applied.
            if "duplicate column" in str(exc).lower():
                db.execute(
                    f"INSERT OR IGNORE INTO {VERSIONS_TABLE} (name, applied_at) VALUES (?, ?)",
                    (name, datetime.now(timezone.utc).isoformat()),
                )
            else:
                logger.exception("迁移 %s 失败", name)
                raise
    db.commit()
    db.close()
    if applied:
        logger.info("已应用数据库迁移：%s", ", ".join(applied))
    return applied


def write_version_files() -> None:
    """Persist each migration as a standalone .sql file for a future Alembic path."""
    base = os.path.dirname(__file__)
    versions_dir = os.path.join(base, "versions")
    os.makedirs(versions_dir, exist_ok=True)
    for name, script in MIGRATIONS:
        path = os.path.join(versions_dir, f"{name}.sql")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(f"-- {name}\n-- Auto-mirrored from backend/migrations/__init__.py\n\n")
            handle.write(script)
