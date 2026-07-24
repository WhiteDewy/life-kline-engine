---
name: me-api-fix-plan
description: /api/me 前后端字段不一致修复方案 + 安全加固
metadata:
  type: project
---

# /api/me 接口修复方案

## 问题根因

`/api/me` 返回 `"profile": {...}`（单数对象），但前端 Wanxiang、Garden 页面期望的是 `"profiles": [...]`（复数数组），导致前端取不到数据、信息无法回显。

同时 `/api/me` 使用 `SELECT *` 泄露了 `phone`、`is_disabled`、`disabled_at`、`deleted_at` 等不应暴露给前端的字段。

## 影响范围

| 文件 | 行号 | 问题 |
|------|------|------|
| `backend/main.py` | 2773-2776 | `SELECT *` + 返回 `"profile"` (单数) |
| `frontend/src/utils/auth.ts` | 57-63 | `loadMe()` 处理单数 `profile`，需适配 |
| `frontend/src/views/Wanxiang/index.vue` | 376 | `meRes.data?.profiles` 期望复数，当前取不到 |
| `frontend/src/views/Garden/index.vue` | 151 | `const { profiles }` 期望复数，当前取不到 |

## 修复方案

### 方向：后端改 `profile` -> `profiles` 数组，与 `/api/profiles` 保持一致

理由：
1. `/api/profiles` 已经是 `profiles` 数组格式，是已确立的契约
2. Wanxiang 和 Garden 两个主要消费端都期望 `profiles` 数组
3. 一个用户未来可能有多个档案（多地点、多用途），数组更合理
4. 修改量最小：后端改 1 处 + 前端 auth.ts 改 1 处

### 后端改动 (`backend/main.py`)

**第 2767-2776 行，`get_me()` 函数：**

```python
# === 现有代码 ===
@app.get("/api/me")
async def get_me(authorization: str = Header(default="")) -> Dict[str, Any]:
    uid = _parse_token(authorization.replace("Bearer ", ""))
    if not uid:
        raise HTTPException(status_code=401, detail="请先登录")
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
    profile = db.execute("SELECT * FROM profiles WHERE user_id=? ORDER BY created_at DESC LIMIT 1", (uid,)).fetchone()
    db.close()
    return {"status": "success", "user": dict(user) if user else None, "profile": dict(profile) if profile else None}

# === 改为 ===
@app.get("/api/me")
async def get_me(authorization: str = Header(default="")) -> Dict[str, Any]:
    uid = _parse_token(authorization.replace("Bearer ", ""))
    if not uid:
        raise HTTPException(status_code=401, detail="请先登录")
    db = get_db()
    # 安全：显式列名，不暴露 phone / is_disabled / disabled_at / deleted_at
    user = db.execute(
        "SELECT id, nickname, role, created_at, last_login_at FROM users WHERE id=?",
        (uid,),
    ).fetchone()
    rows = db.execute(
        "SELECT id, name, gender, birth_time, lat, lon, timezone, birth_place, "
        "house_system, daylight_saving, residence_place, residence_lat, residence_lon, "
        "is_default, created_at "
        "FROM profiles WHERE user_id=? ORDER BY created_at DESC",
        (uid,),
    ).fetchall()
    db.close()
    return {
        "status": "success",
        "user": dict(user) if user else None,
        "profiles": [dict(r) for r in rows],  # 复数数组，与 /api/profiles 一致
    }
```

**关键变更：**
1. `profile` → `profiles`（带 s，数组）
2. `SELECT *` → 显式列名，users 表排除 `phone`/`is_disabled`/`disabled_at`/`deleted_at`
3. 去掉 `LIMIT 1`，返回用户所有档案（与 `/api/profiles` 行为一致）

### 前端改动 (`frontend/src/utils/auth.ts`)

**第 51-63 行，`loadMe()` 函数：**

```typescript
// === 现有代码 ===
if (res.data?.profile) {
  profiles.value = [res.data.profile];
}

// === 改为 ===
if (res.data?.profiles) {
  profiles.value = res.data.profiles;  // 直接赋值数组，不再包装
}
```

**Wanxiang/index.vue 第 376 行：** 无需改动。`meRes.data?.profiles` 现在能正确取到数组。

**Garden/index.vue 第 151 行：** 无需改动。`const { profiles } = ...data` 解构现在能正确取到数组。

### 数据库

**不需要任何改动。** 表结构不变。

### localStorage 安全审计

`auth.ts` 第 59 行：`_saveJson(USER_KEY, res.data.user)` 将 user 对象存入 localStorage。

修复前：后端返回 `SELECT *`，user 对象包含 `phone` 等敏感字段被写入 localStorage。
修复后：后端只返回 `id, nickname, role, created_at, last_login_at`，不再泄露 phone。

## 副作用评估

1. **向后兼容**：`user` 字段从包含 phone 变为不包含，如果前端有地方读了 `user.phone` 会取到 undefined。需全局搜索确认。
2. **auth.ts 内部 `profiles` ref**：之前是 `[单对象]`，现在是 `[数组]`，所有通过 `useAuth().profiles` 消费的组件自动受益。
3. **无其他 `/api/me` 调用点**：后端只有 `main.py` 一处定义，前端确认只有 3 处调用（auth.ts, Wanxiang, Garden）。

## 工作量

| 改动 | 行数 | 风险 |
|------|------|------|
| `backend/main.py` get_me() | ~10 行 | 低，纯字段名+SQL 调整 |
| `frontend/src/utils/auth.ts` loadMe() | ~1 行 | 低 |
| Wanxiang / Garden | 0 行 | 无需改动即可生效 |

总工作量：约 10 分钟。
