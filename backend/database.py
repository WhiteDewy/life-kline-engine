"""
SQLite 数据库 — 用户系统全量数据接入。

表清单（v1）：
  - users                    用户（手机号 + 昵称）
  - verify_codes             验证码
  - profiles                 星盘档案（一个用户可有多个 profile）
  - reports                  星语者/星盘报告
  - star_diary               星灵日记条目
  - growth_conversations     与星灵角色的对话成长记录
  - growth_milestones        用户成长里程碑
  - growth_daily_visits      每日访问（用于 streak 连续天数）
  - chat_sessions            聊天会话
  - chat_messages            聊天消息
  - checkins                 花园签到
  - consultation_sessions    星语者咨询会话快照
  - consultation_reports     星语者咨询报告快照
  - user_state               用户运行时状态（coins、vip、AI 用量）
  - payments                 支付订单

所有 ID 默认本地 UUID12 字符串，保留索引与外键约束。
"""
from __future__ import annotations

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


# ──────────── 完整 schema ────────────────────────────────────────

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    phone TEXT UNIQUE NOT NULL,
    nickname TEXT DEFAULT '',
    role TEXT DEFAULT 'user',                  -- user / vip / banned
    is_disabled INTEGER DEFAULT 0,
    disabled_at TEXT DEFAULT '',
    deleted_at TEXT DEFAULT '',
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
    birth_place TEXT DEFAULT '',
    house_system TEXT DEFAULT 'B',
    daylight_saving INTEGER DEFAULT 0,
    residence_place TEXT DEFAULT '',
    residence_lat REAL DEFAULT 0.0,
    residence_lon REAL DEFAULT 0.0,
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

-- 新增：星灵日记（替代 backend/data/diary/{report_id}.json）
CREATE TABLE IF NOT EXISTS star_diary (
    id TEXT PRIMARY KEY,
    report_id TEXT NOT NULL,
    user_id TEXT DEFAULT '',
    profile_id TEXT DEFAULT '',
    entry_date TEXT NOT NULL,
    keywords TEXT DEFAULT '[]',
    entry_text TEXT NOT NULL,
    chat_context TEXT DEFAULT '',
    user_content_summary TEXT DEFAULT '',
    spirit_content_summary TEXT DEFAULT '',
    spirit_planet TEXT DEFAULT '',
    spirit_planet_label TEXT DEFAULT '',
    mood_emoji TEXT DEFAULT '',
    diary_style TEXT DEFAULT 'summary',
    energy_level INTEGER DEFAULT 50,
    topic_tag TEXT DEFAULT '',
    evening_expectation TEXT DEFAULT '',
    source TEXT DEFAULT 'chat',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- 新增：与角色的对话成长（替代 backend/data/{report_id}_growth.json）
CREATE TABLE IF NOT EXISTS growth_conversations (
    id TEXT PRIMARY KEY,
    report_id TEXT NOT NULL,
    user_id TEXT DEFAULT '',
    sign TEXT NOT NULL,
    topic TEXT DEFAULT '',
    user_message TEXT DEFAULT '',
    character_response TEXT DEFAULT '',
    emotional_context TEXT DEFAULT 'general',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS growth_milestones (
    id TEXT PRIMARY KEY,
    report_id TEXT NOT NULL,
    user_id TEXT DEFAULT '',
    milestone_type TEXT NOT NULL,
    sign TEXT DEFAULT '',
    achieved_at TEXT NOT NULL,
    description TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS growth_daily_visits (
    id TEXT PRIMARY KEY,
    report_id TEXT NOT NULL,
    user_id TEXT DEFAULT '',
    visit_date TEXT NOT NULL,
    featured_signs TEXT DEFAULT '[]',
    activation_scores TEXT DEFAULT '{}',
    created_at TEXT NOT NULL
);

-- 聊天会话与消息快照
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

CREATE TABLE IF NOT EXISTS chat_messages (
    id TEXT PRIMARY KEY,
    session_id TEXT REFERENCES chat_sessions(id),
    user_id TEXT NOT NULL REFERENCES users(id),
    report_id TEXT DEFAULT '',
    role TEXT NOT NULL,
    spirit_planet TEXT DEFAULT '',
    content TEXT DEFAULT '',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS checkins (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id),
    checkin_date TEXT NOT NULL,
    streak_count INTEGER DEFAULT 1,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS consultation_sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id),
    report_id TEXT NOT NULL,
    category TEXT NOT NULL,
    question_key TEXT NOT NULL,
    state_json TEXT NOT NULL,
    step INTEGER DEFAULT 1,
    is_complete INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS consultation_reports (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id),
    session_id TEXT REFERENCES consultation_sessions(id),
    category TEXT NOT NULL,
    question_key TEXT NOT NULL,
    report_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

-- 新增：用户运行时状态（替代 backend/data/user_state/{user_id}.json）
CREATE TABLE IF NOT EXISTS user_state (
    user_id TEXT PRIMARY KEY REFERENCES users(id),
    coins INTEGER DEFAULT 0,
    is_vip INTEGER DEFAULT 0,
    vip_expire_at TEXT DEFAULT '',
    ai_usage_today INTEGER DEFAULT 0,
    ai_usage_date TEXT DEFAULT '',
    extra TEXT DEFAULT '{}',
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
CREATE INDEX IF NOT EXISTS idx_checkins_user ON checkins(user_id);
CREATE INDEX IF NOT EXISTS idx_checkins_date ON checkins(checkin_date);
CREATE INDEX IF NOT EXISTS idx_consultation_user ON consultation_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_consultation_reports_user ON consultation_reports(user_id);

CREATE INDEX IF NOT EXISTS idx_star_diary_report ON star_diary(report_id);
CREATE INDEX IF NOT EXISTS idx_star_diary_user ON star_diary(user_id);
CREATE INDEX IF NOT EXISTS idx_star_diary_date ON star_diary(entry_date);

CREATE INDEX IF NOT EXISTS idx_growth_conv_report ON growth_conversations(report_id);
CREATE INDEX IF NOT EXISTS idx_growth_conv_user ON growth_conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_growth_milestones_report ON growth_milestones(report_id);
CREATE INDEX IF NOT EXISTS idx_growth_visits_report ON growth_daily_visits(report_id);

CREATE INDEX IF NOT EXISTS idx_chat_messages_user ON chat_messages(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_report ON chat_messages(report_id);

-- ──────────── 后台管理 CMS（v1）───────────────────

-- 管理员账号
CREATE TABLE IF NOT EXISTS admins (
    id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'admin',     -- admin / super_admin
    is_active INTEGER DEFAULT 1,
    created_at TEXT NOT NULL,
    last_login_at TEXT DEFAULT ''
);

-- 审计日志（记录所有管理后台操作）
CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    admin_id TEXT NOT NULL,
    admin_username TEXT NOT NULL,
    action TEXT NOT NULL,                    -- create_user / disable_user / delete_diary / ...
    target_type TEXT NOT NULL,               -- user / diary / report / system
    target_id TEXT DEFAULT '',
    detail TEXT DEFAULT '',
    ip TEXT DEFAULT '',
    created_at TEXT NOT NULL
);

-- 日记审核状态（在 star_diary 上做扩展）
CREATE TABLE IF NOT EXISTS diary_moderation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    diary_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'visible',  -- visible / hidden / flagged
    moderator_id TEXT DEFAULT '',
    reason TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- 系统配置 KV
CREATE TABLE IF NOT EXISTS system_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_admins_username ON admins(username);
CREATE INDEX IF NOT EXISTS idx_audit_admin ON audit_logs(admin_id);
CREATE INDEX IF NOT EXISTS idx_audit_target ON audit_logs(target_type, target_id);
CREATE INDEX IF NOT EXISTS idx_diary_mod_status ON diary_moderation(status);
CREATE INDEX IF NOT EXISTS idx_diary_mod_diary ON diary_moderation(diary_id);
"""


def init_db() -> None:
    """初始化全部表（幂等）。"""
    db = get_db()
    db.executescript(SCHEMA_SQL)
    db.commit()
    db.close()
    migrate_db()


def migrate_db() -> None:
    """幂等迁移：补充历史用户表上可能缺失的字段（已有用户的旧 schema 兼容）。"""
    db = get_db()

    # profiles
    cols = {row[1] for row in db.execute("PRAGMA table_info(profiles)").fetchall()}
    if "birth_place" not in cols:
        db.execute("ALTER TABLE profiles ADD COLUMN birth_place TEXT DEFAULT ''")
    if "house_system" not in cols:
        db.execute("ALTER TABLE profiles ADD COLUMN house_system TEXT DEFAULT 'B'")
    if "daylight_saving" not in cols:
        db.execute("ALTER TABLE profiles ADD COLUMN daylight_saving INTEGER DEFAULT 0")
    if "residence_place" not in cols:
        db.execute("ALTER TABLE profiles ADD COLUMN residence_place TEXT DEFAULT ''")
    if "residence_lat" not in cols:
        db.execute("ALTER TABLE profiles ADD COLUMN residence_lat REAL DEFAULT 0.0")
    if "residence_lon" not in cols:
        db.execute("ALTER TABLE profiles ADD COLUMN residence_lon REAL DEFAULT 0.0")

    # reports：旧版可能没有额外列
    rcols = {row[1] for row in db.execute("PRAGMA table_info(reports)").fetchall()}
    if "engine_version" not in rcols:
        db.execute("ALTER TABLE reports ADD COLUMN engine_version TEXT DEFAULT '1.0.0'")
    if "kline_summary" not in rcols:
        db.execute("ALTER TABLE reports ADD COLUMN kline_summary TEXT DEFAULT ''")

    # users（CMS 字段）
    ucols = {row[1] for row in db.execute("PRAGMA table_info(users)").fetchall()}
    if "role" not in ucols:
        db.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'")
    if "is_disabled" not in ucols:
        db.execute("ALTER TABLE users ADD COLUMN is_disabled INTEGER DEFAULT 0")
    if "disabled_at" not in ucols:
        db.execute("ALTER TABLE users ADD COLUMN disabled_at TEXT DEFAULT ''")
    if "deleted_at" not in ucols:
        db.execute("ALTER TABLE users ADD COLUMN deleted_at TEXT DEFAULT ''")

    # star_diary：分开保存用户摘要和星灵启发，旧库幂等补列
    dcols = {row[1] for row in db.execute("PRAGMA table_info(star_diary)").fetchall()}
    if "user_content_summary" not in dcols:
        db.execute("ALTER TABLE star_diary ADD COLUMN user_content_summary TEXT DEFAULT ''")
    if "spirit_content_summary" not in dcols:
        db.execute("ALTER TABLE star_diary ADD COLUMN spirit_content_summary TEXT DEFAULT ''")
    # v1.1：日记多风格字段
    if "diary_style" not in dcols:
        db.execute("ALTER TABLE star_diary ADD COLUMN diary_style TEXT DEFAULT 'summary'")
    if "energy_level" not in dcols:
        db.execute("ALTER TABLE star_diary ADD COLUMN energy_level INTEGER DEFAULT 50")
    if "topic_tag" not in dcols:
        db.execute("ALTER TABLE star_diary ADD COLUMN topic_tag TEXT DEFAULT ''")
    if "evening_expectation" not in dcols:
        db.execute("ALTER TABLE star_diary ADD COLUMN evening_expectation TEXT DEFAULT ''")
    if "spirit_planet_label" not in dcols:
        db.execute("ALTER TABLE star_diary ADD COLUMN spirit_planet_label TEXT DEFAULT ''")

    db.commit()
    db.close()
