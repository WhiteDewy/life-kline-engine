---
name: project-architecture-2026-07
description: 项目架构、分离状态、技术栈一览
metadata:
  type: project
---

# 项目架构状态 (2026-07-23)

## 项目分离状态

```
life-kline-engine/
├── frontend/              # 星灵花园 App（用户端），端口 5173
├── admin-frontend/        # 后台管理系统，端口 5174
└── backend/              # 单一后端，端口 8000，共用 SQLite
```

### 开发命令

```bash
# 用户端
cd frontend && npm run dev          # http://localhost:5173

# 管理端
cd admin-frontend && npm run dev    # http://localhost:5174

# 后端
python -m uvicorn backend.main:app --reload
```

### 管理员账号
- 用户端：用户自行注册
- 管理后台：`admin` / `admin@2026`

## 技术栈

| 层级 | 技术 |
|------|------|
| 用户端 | Vue 3 + TypeScript + Vite |
| 管理端 | Vue 3 + TypeScript + Vite（独立项目） |
| 后端 | FastAPI + Python |
| 数据库 | SQLite（`backend/data/app.db`） |

## 数据库表

### 核心业务表
- `users` — 用户
- `star_diary` — 星灵日记（含新字段）
- `chat_messages` — 对话记录
- `growth_conversations` — 成长对话
- `reports` — 报告

### 管理端表
- `admins` — 管理员
- `audit_logs` — 审计日志
- `diary_moderation` — 日记审核
- `system_settings` — 系统配置 KV

## 星灵日记字段

```sql
star_diary (
    id, report_id, user_id, profile_id,
    entry_date,
    keywords, entry_text, chat_context,
    spirit_planet, spirit_planet_label, mood_emoji, source,
    -- 新增字段
    diary_style,    -- check_in/dialogue/reflection/spirit/summary
    energy_level,   -- 0-100% 电量
    topic_tag,      -- #打工人日常 等
    evening_expectation, -- 下班期待
    user_content_summary, spirit_content_summary,
    created_at, updated_at
)
```

## 星灵系统（10颗）

太阳、月亮、水星、金星、火星、木星、土星、天王星、海王星、冥王星

性格定义：`src/life_kline/characters/planet_personas.py`
触发配置：`src/life_kline/characters/spirit_triggers.py`
日记风格：`src/life_kline/spirit_diary_styles.py`

## API 路由概览

| 前缀 | 说明 |
|------|------|
| `/api/analyze` | 分析入口 |
| `/api/spirit-chat/{report_id}` | 星灵对话 |
| `/api/spirit-diary/{report_id}` | 日记 CRUD |
| `/api/admin/*` | 管理端 API |

## 近期完成的功能

- [x] 前端/后端/管理端分离
- [x] 数据库落地（用户、日记、报告）
- [x] Admin CMS 嵌套路由
- [x] 星灵对话三层触发机制
- [x] 日记多风格模板（打卡/对话/反思）
- [x] 星灵性格触发统一配置

**Why:** 项目已从单体拆分为多前端+单后端架构，星灵系统完成核心重构
**How to apply:** 后续开发新功能时，需考虑三端分离架构；星灵相关逻辑在 src/life_kline/ 下
