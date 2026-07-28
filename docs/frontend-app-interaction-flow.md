# 星灵花园 · 前端 App 交互流程

> 基于后端引擎能力 + 当前已接入/未接入接口，梳理完整用户旅程与页面流转。
> 文档用途：前端开发蓝图、产品体验评审、接口联调对照。

---

## 一、用户主路径总览

```
启动
  │
  ▼
未登录 ──→ 登录/注册 ──→ 建档案 ──→ 生成报告 ──────────────────┐
  │                                                          │
  │（有缓存token）                                           │
  ▼                                                          ▼
首页（星灵花园） ──→ 星盘解读 ──→ 聊天 ──→ 花园咨询 ──→ 日记 ←┘
                    │              │            │
                    └──────────────┴────────────┴──→ 付费/会员
```

---

## 二、启动 & 身份层

### 2.1 闪屏页（Splash）

**后端调用：无**

**交互：**
- 读取本地 `lk_token`
- 有 token → 调用 `GET /api/auth/check` 验证有效性
  - 有效 → 跳转首页
  - 无效/过期 → 跳转登录页
- 无 token → 跳转登录页

---

### 2.2 登录 / 注册页

**后端调用：**
- `POST /api/auth/send-code` — 发送验证码
- `POST /api/auth/verify-code` — 验证登录（开发绕过：`LIFE_KLINE_DEV_BYPASS_PHONE=1` + 验证码 `000000`）

**交互流程：**
```
输入手机号 ──→ 点击获取验证码 ──→ 输入6位验证码 ──→ 提交
                                              │
                               ┌───────────────┴───────────────┐
                               ▼                               ▼
                           登录成功                         登录失败
                           跳转建档页                       提示错误
```

**开发绕过说明：**
- 环境变量 `VITE_DEV_BYPASS_PHONE=1` 时，验证码输入 `000000` 直通登录
- 该变量写入 `frontend/.env.development`

---

### 2.3 建档页（首次注册）

**后端调用：**
- `POST /api/profiles` — 创建出生档案（含地理编码 + DST 自动判定）
- `POST /api/geocode` — 地名 → 经纬度（单独校验用）

**表单字段：**
| 字段 | 来源 | 说明 |
|---|---|---|
| 昵称 | 用户输入 | 非必填 |
| 性别 | 用户选择 | 必填 |
| 出生日期 | 用户选择 | 必填 |
| 出生时间 | 用户选择 | 必填（影响上升点/月亮） |
| 出生地 | 用户输入 + 自动补全 | 调用 `POST /api/geocode` 解析经纬度 |
| 时区 | 自动（默认8） | 可手动调整 |

**交互流程：**
```
填写表单 ──→ 自动地理编码（输入即解析，300ms防抖） ──→ 确认信息 ──→ 提交
                                                                        │
                                               ┌────────────────────────┴───────┐
                                               ▼                                    ▼
                                           建档成功                            建档失败
                                           调用 POST /analyses                提示错误
                                           生成报告（loading）               可重试
                                               │
                                               ▼
                                           报告生成完成 ──→ 跳转首页
```

---

## 三、首页（星灵花园）

**后端调用（按需并发）：**
- `GET /api/me` — 用户信息
- `GET /api/reports/history` — 最新报告
- `GET /api/analyses/{report_id}` — 完整报告数据
- `GET /api/characters/{report_id}/daily` — 今日角色激活
- `GET /api/today-star-spirit/{report_id}` — 今日引路星灵
- `GET /api/daily-question/{report_id}` — 每日一问
- `GET /api/daily-transits/{report_id}` — 今日星象
- `GET /api/spirit-diary/{report_id}?limit=30` — 最近日记

**页面布局（三段式）：**

```
┌──────────────────────────────────┐
│ 顶部三段                          │
│ ① 今日星灵入口（TodayStarSpirit）  │
│ ② 每日一问（DailyQuestion）         │
│ ③ 每日星象高亮（DailyTransit）       │
└──────────────────────────────────┘
┌──────────────────────────────────┐
│ 视频背景区（占星宫/星座主题）         │
│ 太阳星座 + 行星落座信息             │
│ 「触碰你的内在星辰」CTA             │
└──────────────────────────────────┘
┌──────────────────────────────────┐
│ 底部导航                          │
│ 首页 │ 星盘 │ 花园 │ 我的           │
└──────────────────────────────────┘
```

**点击「今日星灵」：**
- 弹出该星灵的问候语 + 疗愈主题
- 提供「和 TA 对话」按钮 → 跳转聊天页

**点击「每日一问」：**
- 展示问题 + 来源星灵
- 点击「回应 TA」→ 跳转聊天页，带 entry_context

**点击「每日星象」：**
- 展开今日行运分层报告（月亮/快行星/逆行/慢行星背景）

**点击「星盘解读」：**
- 跳转 `/kline`（本命盘解读页）

**点击底部「花园」Tab：**
- 跳转花园页面（见 §六）

---

## 四、本命盘解读页（/kline）

**后端调用：**
- `GET /api/analyses/{report_id}` — 已在首页加载，store 共享
- `GET /api/natal-chart/{report_id}` — **未接入** ← 本地合成数据，引擎有独立接口

**推荐新增调用：**
- `GET /api/natal-chart/{report_id}` — 本命盘详情（法达100年 + 接纳互溶）

**页面区块：**

```
┌──────────────────────────────────┐
│ Hero叙事区                        │
│ 分类段落：观察/行运/法达/钩子        │
│ 悬念引导（钩子段落末尾的 CTA 句）     │
└──────────────────────────────────┘
┌──────────────────────────────────┐
│ 星盘速览条（太阳/月亮/上升/金星/火星） │
└──────────────────────────────────┘
┌──────────────────────────────────┐
│ 人生阶段时间轴（法达周期）           │
│ ← 每段可展开 →                    │
│ 触发深度：GET /api/natal-chart     │
└──────────────────────────────────┘
┌──────────────────────────────────┐
│ 行星互喂关系（接纳/互溶）图谱         │
│ 触发深度：GET /api/natal-chart     │
└──────────────────────────────────┘
┌──────────────────────────────────┐
│ 八大领域折叠面板                   │
│ ersonal / Finance / Family 等     │
│ 每领域末尾有钩子引导付费            │
└──────────────────────────────────┘
```

**法达时间轴交互：**
- 默认展示当前年龄 ± 5 年
- 左右滑动/拖拽查看其他阶段
- 点击阶段卡片 → 展开该阶段详细解读
- 数据来源：`/api/natal-chart/{id}` → `firdaria_periods[]`

**行星互喂关系图：**
- 节点：10 颗行星
- 边：接纳（实线）/ 互溶（虚线）
- 颜色：入庙>旺>弱>陷（4 档色）
- 点击节点 → 弹出该行星详情弹窗
- 数据来源：`/api/natal-chart/{id}` → `receptions[]`

---

## 五、星灵对话（聊天）页

### 5.1 入口

- 首页「今日星灵」→ 带 `planet` 参数进入
- 首页「每日一问回应」→ 带 `entry_context: daily_question` 进入
- 星灵议会点击某行星「和 TA 聊聊」→ 带 `planet` 参数进入
- 花园咨询结束后 → 带 `entry_context: consultation` 进入
- 行星详情面板「和 TA 对话」→ 进入

### 5.2 对话模式选择

**后端调用（推荐新增）：**
- `GET /api/access/{user_id}` — 查询当前用户额度，决定展示 V1/V2

**交互：**
```
进入聊天 ──→ 检查额度 ──→ 有 AI 额度 ──→ 弹窗选择「引擎对话」/「AI 增强对话」
                    │
                    └─→ 无 AI 额度 ──→ 直接进入 V1 引擎对话
```

### 5.3 V1 引擎对话

**后端调用：**
- `POST /api/spirit-chat/{report_id}`

**请求参数：**
```ts
{
  planet: string,           // 当前聊天行星
  topic: "personal",       // 话题域
  message: string,         // 用户输入
  history: [{role, text}],  // 对话历史
  entry_context?: {         // 来源上下文
    type: "today_star_spirit" | "daily_question" | "council" | "consultation"
  }
}
```

**响应结构：**
```ts
{
  planet,
  response,                 // 完整回复
  engine_reading: {
    acknowledgment,         // 共情
    mirroring,             // 镜像
    guidance,              // 引导
    evidence: string[]      // 星盘证据
  },
  source: "engine" | "llm_enhanced" | "crisis_guard",
  suggested_followup: string[],
  diary_style_suggestions: string[]  // 日记风格建议
}
```

**界面交互：**
- 引擎回复 → 展示气泡 + 星盘依据折叠面板
- 用户可点击「查看星盘依据」展开证据列表
- 底部快捷建议气泡（`suggested_followup`）
- 「一键生成日记」→ 调用 `POST /api/spirit-diary/{id}/entry`

### 5.4 V2 咨询式对话（五阶段）

**后端调用：**
- `POST /api/spirit-chat-v2/{report_id}`

**五阶段状态机：**
```
Step 1 倾听 ──→ Step 2 探索 ──→ Step 3 反思 ──→ Step 4 理解 ──→ Step 5 结束
  │              │              │              │              │
  └──────────────┴──────────────┴──────────────┴──────────────┘
                       跨轮记忆（dialogue_token）
```

**请求参数（相比 V1 新增）：**
```ts
{
  planet: string,
  topic: "personal",
  message: string,
  history: [],
  dialogue_token?: string,   // 跨轮状态续接
  entry_context?: dict
}
```

**响应结构：**
```ts
{
  source: "consultation_v2" | "consultation_v2_ai",
  stage: "listening" | "exploring" | "reflecting" | "understanding" | "closing",
  dialogue_state: {
    stage, turn_count, theme_key, user_expressed
  },
  dialogue_token: string,    // 下一轮携带
  response: string,           // 星灵回复
  memory_context: {
    recent_topics: string[],
    recent_milestones: string[]
  }
}
```

**界面交互：**
- 每轮显示当前阶段名称（底部进度条）
- 记忆气泡：「之前我们聊过...」
- 里程碑触发时 → 浮层庆祝动效 + 记录到成长数据
- 结束阶段 → 自动触发日记建议

### 5.5 对话通用底部栏

```
┌─────────────────────────────────────────┐
│ [🤍] [💬] [📝日记] [📖解读]              │
│                                          │
│ [输入框.............................] [➡] │
└─────────────────────────────────────────┘
```
- 🤍 — 收藏本轮对话（前端本地）
- 💬 — 快捷问题气泡（来自 `suggested_followup`）
- 📝日记 — 一键生成日记 → `POST /api/spirit-diary/{id}/entry`
- 📖解读 — 跳转本命盘相关段落

---

## 六、花园（Garden）

**后端调用（未接入/部分接入）：**
- `GET /api/garden/categories` — **未接入** ← 花园首页入口数据
- `GET /api/garden/checkin` — **未接入** ← 签到状态
- `POST /api/garden/checkin` — **未接入** ← 执行签到
- `POST /api/garden/consultation/{id}/start` — **未接入** ← 核心：星语者咨询
- `POST /api/garden/consultation/{id}/continue` — **未接入**
- `POST /api/garden/consultation/{id}/report` — **未接入**
- `GET /api/garden/reports` — **未接入** ← 咨询报告历史
- `GET /api/garden/reports/{report_id}` — **未接入**

### 6.1 花园首页

**调用 `GET /api/garden/categories`：**

**响应：**
```ts
{
  categories: [
    {
      key: "career",
      label: "事业方向",
      icon: "💼",
      question_keys: [
        { key: "career_dilemma", label: "职业选择迷茫", question: "..." },
        { key: "career_change", label: "是否该跳槽", question: "..." }
      ]
    },
    // ... personal / finance / romance / marriage / education
  ]
}
```

**交互：**
```
花园首页
  │
  ├── 今日签到卡片（调用 GET /garden/checkin）
  │     ├── 已签到 → 展示「已签到 + 连续N天 + 今日鼓励语」
  │     └── 未签到 → 展示「点击签到」→ POST /garden/checkin
  │
  ├── 咨询入口（7 大领域分类）
  │     └── 点击分类 → 展开抓手问题列表 → 选择问题 → start consultation
  │
  ├── 运势专区（星象播报，不依赖报告）
  │
  └── 历史报告入口
        └── 调用 GET /garden/reports → 报告列表
```

### 6.2 星语者咨询流程（核心）

**Start：调用 `POST /api/garden/consultation/{id}/start`**
```ts
// 请求
{ category: "career", question_key: "career_dilemma" }
// 响应
{ session_id, state: { step: "anchoring", category, question_key, chart_context } }
```

**交互：** 展示问题 + 星语者开场白（Step 1 锚定）

**Continue：调用 `POST /api/garden/consultation/{id}/continue`**
```ts
// 请求
{ session_id, user_response: "我毕业两年了..." }
// 响应
{ session_id, state: { step: "locating" | "exploring", ... }, response }
```

**交互：** 用户多轮回答 → 星语者逐步定位场景（2-3 轮）→ 引入星盘验证

**Report：调用 `POST /api/garden/consultation/{id}/report`**
```ts
// 请求
{ session_id, user_response: "最后想说的话" }
// 响应
{
  consultation_report: {
    summary,                  // 综合结论
    chart_verification: [],  // 星盘验证点
    guidance: [],            // 行动指引
    warnings: [],            // 边界守护
    hook: ""                 // 钩子（引导下一步）
  },
  diary_entry_id             // 自动生成的日记 ID
}
```

**交互：** 展示完整咨询报告 → 提供「重新理解」「写入日记」按钮

### 6.3 花园报告历史

**调用 `GET /api/garden/reports?limit=20&offset=0`**
```ts
{
  reports: [
    { id, category, category_label, question_key, question_label,
      summary, created_at }
  ],
  total
}
```

**交互：** 下拉加载更多 → 点击报告卡片 → 调用 `GET /api/garden/reports/{id}` → 展示报告详情

---

## 七、星灵日记

**后端调用（部分未接入）：**
- `GET /api/spirit-diary/{report_id}/styles` — **未接入** ← 写日记前的风格建议
- `POST /api/spirit-diary/{report_id}/entry` — **未接入** ← 创建日记
- `GET /api/spirit-diary/{report_id}?limit=30` — 已接入（首页）
- `PATCH /api/spirit-diary/{entry_id}` — **未接入** ← 编辑
- `DELETE /api/spirit-diary/{entry_id}` — **未接入** ← 删除

### 7.1 日记时间线

**调用 `GET /api/spirit-diary/{report_id}?limit=30&offset=0`**
```ts
{
  entries: [
    {
      id, diary_style, mood_emoji,
      entry_text, keywords: [],
      energy_level, topic_tag,
      created_at, spirit_planet
    }
  ],
  total
}
```

**交互：**
- 瀑布流/时间线展示日记卡片
- 日记卡片：风格图标 + 心情 emoji + 首句预览 + 能量等级条
- 点击卡片 → 展开全文 + 编辑/删除按钮
- 下拉刷新加载更多

### 7.2 创建日记

**入口：**
- 聊天页「📝日记」→ 弹出日记创建页
- 花园咨询结束 → 自动触发日记创建
- 日记页右上角「+」→ 新建空白日记

**第一步：选择风格（调用 `GET /api/spirit-diary/{id}/styles`）**
```ts
{
  suggestions: [
    { style: "check_in", label: "晨间打卡", emoji: "🌅", description: "..." },
    { style: "dialogue", label: "对话记录", emoji: "💬", description: "..." },
    { style: "reflection", label: "反思复盘", emoji: "🌙", description: "..." },
    { style: "spirit", label: "星灵来信", emoji: "✨", description: "..." },
    { style: "summary", label: "综合周记", emoji: "📝", description: "..." }
  ]
}
```

**第二步：编辑内容**
```
标签（多选）：#关系 #事业 #今日 #心情 #觉察
心情 emoji：😊 😐 😔 😢 😡 （单选）
能量等级：1-5 星
正文编辑框（支持 Markdown 预览）
星灵关联：自动带入当前聊天行星 / 可手动切换
```

**第三步：提交（调用 `POST /api/spirit-diary/{id}/entry`）**
```ts
{
  chat_context?: "...",
  spirit_planet: "SUN",
  mood_emoji: "😊",
  user_messages: ["我今天..."],
  spirit_responses: ["星灵回复..."],
  diary_style: "dialogue",
  evening_expectation?: "..."
}
```

**响应：** `entry` + `diary_preview`（多风格预览）

### 7.3 编辑/删除日记

**调用：**
- `PATCH /api/spirit-diary/{entry_id}` — 更新（关键词/心情/正文）
- `DELETE /api/spirit-diary/{entry_id}` — 删除

**交互：**
- 长按/右上角菜单 → 出现「编辑」「删除」选项
- 删除需二次确认弹窗

---

## 八、会员 & 支付

**后端调用（完全未接入）：**
- `GET /api/pricing` — **未接入** ← 定价信息
- `GET /api/access/{user_id}` — **未接入** ← 用户当前额度
- `POST /api/billing/orders` — **未接入** ← 创建订单
- `POST /api/billing/verify` — **未接入** ← 支付凭证校验
- `GET /api/billing/orders` — **未接入** ← 订单历史

### 8.1 会员页入口

**触发场景：**
- 首页「升级 VIP」按钮
- 聊天页提示「本周免费次数已用完」
- 议会页提示「本周免费次数已用完」
- 个人中心「订阅会员」入口

### 8.2 会员权益页

**调用 `GET /api/pricing`：**
```ts
{
  vip_plans: [
    { id: "monthly_auto", name: "月卡", price_cny: 29.9, duration_days: 30 },
    { id: "yearly_auto", name: "年卡", price_cny: 299, duration_days: 365 }
  ],
  coin_packages: [
    { id: "coin_100", name: "星币100", price_cny: 6, coins: 100, bonus: 0 },
    { id: "coin_500", name: "星币500", price_cny: 28, coins: 500, bonus: 50 }
  ],
  free_quota: { council_weekly: 3, ai_chat_free: 3 }
}
```

**调用 `GET /api/access/{user_id}`：**
```ts
{
  is_vip: false,
  coins: 20,
  engine: { quota_remaining: -1 },    // 引擎对话无限
  ai: { quota_remaining: 2 },         // AI对话剩余次数
  council: { quota_remaining: 1 }    // 议会剩余次数
}
```

**页面展示：**
```
┌──────────────────────────────────┐
│ 当前身份：免费用户                 │
│ 星币余额：20                      │
│ 本周剩余：AI对话 2次 │ 议会 1次    │
└──────────────────────────────────┘

┌──────────────────────────────────┐
│ ⭐ VIP 会员                       │
│ 月卡 ¥29.9/月   年卡 ¥299/年      │
│ 权益：无限AI对话 + 无限议会 + ...  │
│ [立即订阅]                        │
└──────────────────────────────────┘

┌──────────────────────────────────┐
│ 💎 星币充值                       │
│ 100星币 ¥6   500星币 ¥28（送50）  │
│ [充值]                           │
└──────────────────────────────────┘
```

### 8.3 订阅/充值流程

**月卡/年卡订阅：**
```
点击「立即订阅」──→ 选择档位（月/年）──→ 唤起支付
                                            │
                       ┌────────────────────┴────────────────────┐
                       ▼                                          ▼
                 支付成功                                      支付取消/失败
                 POST /api/billing/verify                      提示重新选择
                       │
                       ▼
                 刷新 access 数据 ──→ 更新 UI 显示 VIP 生效
```

**星币充值：**
```
点击「充值」──→ 选择星币包 ──→ 唤起支付
                        │
                        ▼
                  支付成功 ──→ POST /api/billing/verify
                        │
                        ▼
                  刷新 access 数据 ──→ 更新星币余额
```

**iOS 内购特殊流程：**
- 前端调用 `Capacitor.Plugins.InAppPurchase.purchase(productId)`
- 获得 `receipt` → 前端调用 `POST /api/billing/verify` 带上 receipt
- 后端调用 Apple verifyReceipt 接口校验
- 校验通过 → 发放星币/VIP

### 8.4 订单历史

**调用 `GET /api/billing/orders`：**
```ts
{
  orders: [
    { id, product_id, product_type, channel, amount_cny,
      status: "pending" | "paid" | "refunded",
      granted: "coins:+100",
      created_at }
  ]
}
```

**交互：** 展示订单列表（待支付/已支付/已退款），点击可查看详情

---

## 九、个人中心

**后端调用：**
- `GET /api/me` — 已接入
- `GET /api/profiles` — 已接入
- `POST /api/profiles` — 部分接入（新建档案）
- `PUT /api/profiles/{profile_id}` — **未完整接入** ← 档案编辑保存
- `DELETE /api/account` — **未接入** ← 账号注销

### 9.1 个人信息展示

```
┌──────────────────────────────────┐
│ [头像] 昵称                       │
│ 会员状态 / 星币余额                │
└──────────────────────────────────┘
┌──────────────────────────────────┐
│ 我的档案                          │
│ 夏季 · 女 · 1991-03-21            │
│ 北京 · GMT+8                      │
│ [编辑档案]                        │
└──────────────────────────────────┘
```

### 9.2 档案编辑

**调用 `PUT /api/profiles/{profile_id}`（部分更新）：**
```ts
// 请求（model_dump(exclude_unset=True)）
{
  name?: "新昵称",
  gender?: "女",
  birth_time?: "1991-03-21T09:25:00",
  lat?: 39.9,
  lon?: 116.4,
  timezone?: 8,
  birth_place?: "北京",
  house_system?: "B",
  daylight_saving?: false,
  residence_place?: "北京",
  residence_lat?: 39.9,
  residence_lon?: 116.4
}
```

**交互：**
- 编辑出生地 → 调用 `POST /api/geocode` 实时解析经纬度
- 切换宫位制 → 重新请求 `/api/users/chart?house_system=B` 预览
- 保存时附带头顶「最近编辑」标记 → 重新生成报告？

### 9.3 账号注销

**调用 `DELETE /api/account`（需 `Authorization` header）：**

**交互流程：**
```
个人中心 ──→ 底部「注销账号」──→ 二次确认弹窗
                                     │
                    ┌────────────────┴────────────────┐
                    ▼                                  ▼
              输入「注销」确认                      取消
                    │
                    ▼
              调用 DELETE /api/account
                    │
                    ▼
              清除本地 token + user 数据
                    │
                    ▼
              跳转登录页（带提示：账号已注销）
```

**二次确认弹窗文案：**
> 「注销后你的所有数据将被永久删除，包括星盘档案、日记、聊天记录，且无法恢复。确定要继续吗？」

---

## 十、实时行运页

**后端调用（**未接入**）：**
- `GET /api/transit/now` — **未接入** ← 当下全球星象（无报告依赖）

**页面用途：** 不需要登录，任何访客都可查看当下星象

```
┌──────────────────────────────────┐
│ 🌌 此刻星象（实时）                │
│                                  │
│ ☀️ 太阳 @ 白羊座 15°23'           │
│ 🌙 月亮 @ 天蝎座 8°              │
│ ☿️ 水星 @ 金牛座 22°（逆行中）     │
│ ...                              │
│                                  │
│ 「今日宇宙能量提示」               │
└──────────────────────────────────┘
```

---

## 十一、接口优先级 & 接入顺序建议

### Phase 1 — 核心闭环（商业化 + 体验完整）

| 顺序 | 功能 | 涉及接口 | 前端文件 |
|---|---|---|---|
| 1 | 本命盘详情（法达+接纳） | `GET /natal-chart/{id}` | `Kline/index.vue` |
| 2 | 支付链路完整接入 | `GET /pricing`, `GET /access`, `POST /billing/orders`, `POST /billing/verify` | `PaymentModal.vue` |
| 3 | 额度展示（无处不显示） | `GET /access/{user_id}` | 公共 Header 或弹层 |

### Phase 2 — 花园核心

| 顺序 | 功能 | 涉及接口 |
|---|---|---|
| 4 | 花园分类入口 | `GET /garden/categories` |
| 5 | 签到（签到墙） | `GET/POST /garden/checkin` |
| 6 | 星语者咨询（全流程） | `POST /garden/consultation/{id}/start\|continue\|report` |
| 7 | 花园报告历史 | `GET /garden/reports` |

### Phase 3 — 日记完善

| 顺序 | 功能 | 涉及接口 |
|---|---|---|
| 8 | 日记风格建议 | `GET /spirit-diary/{id}/styles` |
| 9 | 创建日记（含 AI 生成） | `POST /spirit-diary/{id}/entry` |
| 10 | 编辑/删除日记 | `PATCH/DELETE /spirit-diary/{entry_id}` |

### Phase 4 — 体验升级

| 顺序 | 功能 | 涉及接口 |
|---|---|---|
| 11 | 实时行运 | `GET /transit/now` |
| 12 | 地理编码（档案编辑） | `POST /geocode` |
| 13 | 账号注销 | `DELETE /account` |
| 14 | 订单历史 | `GET /billing/orders` |
| 15 | 星座角色对话/议会 | `POST /characters/{id}/chat\|council` |

---

## 十二、通用组件层（跨页面复用）

### 12.1 升级弹窗（QuotaError 处理）

所有调用 `spirit-chat` / `council` / `spirit-chat-v2` 的页面，需统一处理 `QuotaError`：

```ts
// 全局 response interceptor 已处理 401
// 页面内需处理 QuotaError：
catch (e: QuotaError) {
  showUpgradeModal({
    message: e.message,
    action: e.action_required, // "upgrade" | "buy_coins"
    access: e.access            // { council, ai, engine }
  })
}
```

**模态框内容：**
- 当前剩余额度可视化
- 「升级 VIP」主按钮 → 跳转会员页
- 「充值星币」次按钮

### 12.2 统一 Loading 态

- 报告生成中：`POST /analyses` → 全屏毛玻璃 loading + 进度文案
- 花园咨询中：`POST /garden/consultation/{id}/continue` → 打字机效果 + 星语者头像呼吸动效

### 12.3 危机检测处理

`soul-chat` / `council` 响应 `status: "crisis"` 时：

```ts
if (response.data?.status === "crisis") {
  // 不展示普通回复
  // 弹出危机关怀弹窗（引导拨打热线）
  showCrisisModal(response.data)
}
```

---

*文档版本：v0.1 | 最后更新：2026-07-28*
