"""
SQLite 数据库 — 用户系统（MVP）。
user / profile / report / chat_session / payment 五张表。
"""
import sqlite3
import os
import uuid
from datetime import datetime, timezone

DB_DIR = os.path.join(os.path.dirname(__file__), "data")
DB_PATH = os.path.join(DB_DIR, "app.db")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _uid() -> str:
    return uuid.uuid4().hex[:12]


def get_db() -> sqlite3.Connection:
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    db = get_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            phone TEXT UNIQUE NOT NULL,
            nickname TEXT DEFAULT '',
            created_at TEXT NOT NULL,
            last_login_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS verify_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT NOT NULL,
            code TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            used INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS profiles (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL REFERENCES users(id),
            name TEXT DEFAULT '',
            gender TEXT DEFAULT '',
            birth_time TEXT NOT NULL,
            lat REAL NOT NULL,
            lon REAL NOT NULL,
            timezone REAL DEFAULT 8.0,
            is_default INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS reports (
            id TEXT PRIMARY KEY,
            profile_id TEXT NOT NULL REFERENCES profiles(id),
            user_id TEXT NOT NULL REFERENCES users(id),
            analysis_type TEXT NOT NULL,
            report_data TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS chat_sessions (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL REFERENCES users(id),
            profile_id TEXT NOT NULL REFERENCES profiles(id),
            report_id TEXT REFERENCES reports(id),
            domain TEXT DEFAULT '',
            messages TEXT DEFAULT '[]',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS payments (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL REFERENCES users(id),
            type TEXT NOT NULL,
            amount REAL NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TEXT NOT NULL,
            paid_at TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_profiles_user ON profiles(user_id);
        CREATE INDEX IF NOT EXISTS idx_reports_user ON reports(user_id);
        CREATE INDEX IF NOT EXISTS idx_reports_profile ON reports(profile_id);
        CREATE INDEX IF NOT EXISTS idx_chat_user ON chat_sessions(user_id);
        CREATE INDEX IF NOT EXISTS idx_verify_phone ON verify_codes(phone);
    """)
    db.commit()
    db.close()

    migrate_db()


def migrate_db() -> None:
    """Idempotent migration: add columns to profiles table."""
    db = get_db()

    # Check existing columns in profiles
    existing = {row[1] for row in db.execute("PRAGMA table_info(profiles)").fetchall()}

    if "birth_place" not in existing:
        db.execute("ALTER TABLE profiles ADD COLUMN birth_place TEXT DEFAULT ''")
    if "house_system" not in existing:
        db.execute("ALTER TABLE profiles ADD COLUMN house_system TEXT DEFAULT 'B'")
    if "daylight_saving" not in existing:
        db.execute("ALTER TABLE profiles ADD COLUMN daylight_saving INTEGER DEFAULT 0")

    db.commit()
    db.close()
