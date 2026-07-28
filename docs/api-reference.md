# Life K-Line Engine — API 参考手册

> 本文件是星灵花园后端引擎的 **HTTP API 总览**，按功能分组，每个端点记录：调用方法、功能描述、业务描述、用户效果、引擎层归属。
> 所有路由声明在 `backend/main.py` 单文件中（共 62 个端点：1 root + 61 `/api/*`）。无 `APIRouter`、无 WebSocket。
> 维护规则：新增/变更端点时同步更新本文件对应小节 + 末尾「引擎层调用速查表」。

---

## 0. 通用约定

### 鉴权
- **用户 token**：自定义签名 token（`_make_token`/`_parse_token`，`main.py:430-449`，非 JWT，30 天有效）。通过 `Authorization: Bearer <token>` 头传递。
  - 获取：`POST /api/auth/send-code` + `POST /api/auth/verify-code`（手机号验证码登录）。
  - 校验：`GET /api/auth/check`。
  - 开发绕过：env `LIFE_KLINE_DEV_BYPASS_PHONE` + 验证码 `000000` 直登。
- **管理员 token**：`_admin._make_admin_token`，通过 `Depends(_admin.require_admin)` / `require_super_admin` 依赖注入（`backend/admin.py:161/180`）。
- 标注「需登录」的端点必须携带有效用户 token；标注「报告所有者」的端点还会校验 `report_id` 归属。

### 响应包络
绝大多数端点返回统一信封：
```jsonc
{ "status": "ok" | "success" | "error", "data": { ... } }
```
错误时附带 `error_code` / `message`。危机命中时 council / spirit-chat 返回 `{ "status": "crisis", "data": crisis.to_dict() }`；额度超限时返回 `{ "status": "error", "error_code": "QUOTA_EXCEEDED", "data": { "message", "access" } }`。

### 前端代理
`frontend/vite.config.ts`：`/api` 前缀直通后端 `VITE_DEV_PROXY_TARGET`（默认 `http://127.0.0.1:8000`），`changeOrigin: true`，无 rewrite。

### 运行
```bash
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```
FastAPI 自带 `/docs`（Swagger）、`/redoc`、`/openapi.json` 默认开启，可作交互式补充。

---

## 1. 系统 / 健康检查

### `GET /`  ·  `main.py:693`
- **功能**：健康检查/服务存活探测。
- **业务**：返回固定欢迎语，确认进程在运行。
- **用户效果**：无（运维/前端启动探活用）。
- **引擎层**：无。

### `GET /api/analysis-types`  ·  `main.py:698`  · response_model=`AnalysisTypesResponse`
- **请求**：无。
- **响应**：`{ status, data: list[AnalysisDefinitionModel] }`。
- **功能**：列出系统支持的所有分析类型（如 `phase_navigation` 等）及其元数据。
- **业务**：前端「分析类型选择器」的数据源；决定本命盘报告走哪条分析流水线。
- **用户效果**：用户在创建报告前看到可选的分析维度。
- **引擎层**：`list_analysis_types()`（`life_kline.service`）。

---

## 2. 分析 / 报告（核心 K-Line）

### `POST /api/analyses`  ·  `main.py:706`  · response_model=`ServiceResponse`  · 需登录
- **请求**：body `AnalysisRequest`（`main.py:294`）
  - `analysis_type: str`
  - `subjects: list[AnalysisSubject]`（`name, gender, birth_time:str, lat:float, lon:float, timezone:float=8.0`）
  - header `Authorization`
- **响应**：`{ status, report_id, analysis, data }`。
- **功能**：创建一份本命盘分析报告（核心 K-Line 生成入口）。
- **业务**：根据生时/经纬度/时区走 Ephemeris → 特征计算 → 8 领域 → Composer → 报告 JSON，并落库。同步线程执行（`anyio.to_thread`），同时 `INSERT INTO profiles`。
- **用户效果**：用户提交出生信息后，得到一份带 `report_id` 的完整人生分析报告，后续所有星灵/咨询能力都基于此 `report_id`。
- **引擎层**：`run_analysis(input_data, user_id, profile_id)`（`life_kline.service`）。

### `GET /api/reports/history`  ·  `main.py:733`  · 需登录
- **请求**：header `Authorization`。
- **响应**：`{ status, reports: [{ id, report_id, profile_id, analysis_type, kline_summary, created_at }] }`。
- **功能**：列出当前用户的报告历史（上限 50）。
- **业务**：用户多档案/多报告管理；前端报告列表页数据源。
- **用户效果**：用户可查看历史报告并跳转。
- **引擎层**：`_dao.list_reports_by_user(user_id, limit=50)`。

### `GET /api/analyses/{report_id}`  ·  `main.py:754`  · response_model=`ServiceResponse`  · 报告所有者
- **请求**：path `report_id`；header `Authorization`。
- **响应**：`{ status, report_id, analysis, data }`。
- **功能**：按 ID 加载完整报告（DB 优先，JSON 兜底）。
- **业务**：报告回看；前端 `/reports/:id` / `/kline` 主数据源。
- **用户效果**：用户重新打开历史报告，看到完整 K 线与领域分析。
- **引擎层**：`load_owned_report(report_id, authorization)`。

### `POST /api/analyze`  ·  `main.py:1155`  · response_model=`ServiceResponse`  · 需登录  · **Legacy**
- **请求**：body `UserInput`（`main.py:299`：`gender?, birth_time, lat, lon, timezone=8.0`）；header `Authorization`。
- **响应**：同 `ServiceResponse`。
- **功能**：遗留创建报告端点，内部构造 `AnalysisRequest(analysis_type="phase_navigation")` 转发到 `run_analysis`。
- **业务**：向后兼容旧前端调用；新代码应使用 `POST /api/analyses`。
- **用户效果**：与 `/api/analyses` 一致。
- **引擎层**：`run_analysis(request_payload, user_id=uid)`。

### `GET /api/report/{report_id}`  ·  `main.py:1178`  · response_model=`ServiceResponse`  · **Legacy**
- **功能**：遗留报告读取端点，行为同 `GET /api/analyses/{report_id}`，均走 `load_owned_report`。
- **业务**：前端 `/kline` 是 `/reports/:id` 的旧别名。
- **用户效果**：同上。

---

## 3. 本命盘 API

### `GET /api/natal-chart/{report_id}`  ·  `main.py:1261`  · 报告所有者
- **请求**：path `report_id`；header `Authorization`。
- **响应**：`{ status, report_id, data: { natal_chart, firdaria_periods[], receptions[], is_day_chart, current_age } }`
  - `firdaria_periods[]`：`{ start_age, end_age, lord, lord_zh, sub_lord, sub_lord_zh, is_node }`
  - `receptions[]`：`{ from, from_zh, to, to_zh, type, type_zh, description }`
- **功能**：获取本命盘详情——星盘数据 + 相位 + 接纳/互溶 + 100 年法达周期。
- **业务**：本命盘页核心数据；法达周期驱动「人生阶段时间线」，接纳/互溶驱动「行星互喂关系」。
- **用户效果**：用户看到自己 100 年的法达时间轴，以及行星之间的接纳/互溶关系图。
- **引擎层**：`calculate_firdaria_periods(is_day_chart, max_age=100.0)`（`life_kline.firdaria`）；从报告 `advanced_patterns.reception_groups` / `mutual_receptions` 整理接纳/互溶；`planet_label`（`life_kline.service`）。

### `GET /api/users/chart`  ·  `main.py:3415`  · 需登录
- **请求**：query `profile_id?: str`、`house_system?: str="B"`、`daylight_saving?: bool`；header `Authorization`。
- **响应**：`{ status, profile_id, house_system, daylight_saving, data: { natal_chart, firdaria_periods[], receptions[], is_day_chart, current_age } }`。
- **功能**：按用户档案生成本命盘（可指定宫位制/夏令时），结构同上。
- **业务**：不依赖既有报告，直接从 profile 实时算盘；支持不同宫位制对比。
- **用户效果**：用户切换宫位制或刚建档后即时看盘。
- **引擎层**：`service.generate_report(...)`（`LifeKlineService`）+ `calculate_firdaria_periods` + 接纳/互溶整理。

---

## 4. 角色系统 API（12 星座角色 · 计算层）

> ⚠️ 该组端点基于「12 星座角色」人格化体系（`characters/sign_personas` + `character_engine` + `awakening/daily_engine`）。
> 按《星灵花园 Product Bible》方向，12 星座将退回计算层、不再作为对外人格化层；此组端点后续可能重构为「行星激活」语义。当前保留可用。

### `GET /api/characters/{report_id}`  ·  `main.py:1207`  · 报告所有者
- **请求**：path `report_id`；header `Authorization`。
- **响应**：`{ status, report_id, data: characters }`（来自报告 `data.characters`）。
- **功能**：获取 12 星座个性化角色画像。
- **用户效果**：用户看到 12 个星座角色的存在感/舒适度排序与画像。
- **引擎层**：报告生成期由 `CharacterEngine` 写入。

### `GET /api/characters/{report_id}/daily`  ·  `main.py:1218`  · 报告所有者
- **请求**：path `report_id`；header `Authorization`。
- **响应**：`{ status, report_id, data: activation.to_dict() }`。
- **功能**：获取今日角色激活度与「今日登场角色」。
- **业务**：基于法达主周期 + 行运 + 月相 + 月返，算 12 星座角色当日激活权重，取前 3 登场。
- **用户效果**：用户每天看到「今天哪几个星座角色想和你说话」。
- **引擎层**：`EphemerisEngine.calculate_chart` → `CharacterEngine(chart)` + `calculate_firdaria_periods` → `DailyAwakeningEngine(chart, char_engine, current_period).compute_daily_activation()`。

### `POST /api/characters/{report_id}/chat`  ·  `main.py:1358`  · 报告所有者
- **请求**：path `report_id`；body `CharacterChatInput`（`main.py:1193`：`sign:str, topic:str="personal", message?:str, history?:list[dict]`）；header `Authorization`。
- **响应**：`{ status, data: { character, character_name, response, emotional_tone, suggested_followup } }`。
- **功能**：与指定星座角色对话（规则驱动，不依赖 LLM）。
- **业务**：轻量陪伴对话，永远在线、不消耗额度；同时记录成长。
- **用户效果**：用户和某个星座角色闲聊，得到带情绪色调的回复 + 跟进话题。
- **引擎层**：规则驱动构造回复；`GrowthTracker(report_id).record_conversation(...)`。

### `POST /api/characters/{report_id}/council`  ·  `main.py:1539`  · 报告所有者
- **请求**：path `report_id`；body `CouncilInput`（`main.py:1200`：`topic:str, signs?:list[str], message?:str`）；header `Authorization`。
- **响应**：`{ status, data: { topic, topic_label, perspectives[{ character, character_name, archetype, perspective, visual_color }], synthesis } }`。
- **功能**：获取多个星座角色对同一话题的不同视角（纯规则合成，不调 LLM）。
- **用户效果**：用户看到同一问题下不同星座角色的多元观点 + 合成。
- **引擎层**：纯规则合成。

### `GET /api/characters/{report_id}/growth`  ·  `main.py:1609`
- **请求**：path `report_id`（⚠️ 无 auth 校验）。
- **响应**：`{ status, report_id, data: { summary, milestones[], recent_conversations[] } }`。
- **功能**：获取用户成长数据（亲密度、里程碑、近期对话）。
- **用户效果**：用户看到自己与角色的关系成长轨迹与里程碑。
- **引擎层**：`GrowthTracker.load(report_id)` → `get_growth_summary()` / `milestones` / `get_conversation_history(limit=10)`。

---

## 5. 星灵议会（Council · 10 行星视角协作）

### `POST /api/council/{report_id}`  ·  `main.py:1458`  · 需登录  · 报告所有者
- **请求**：path `report_id`；body `CouncilChatInput`（`main.py:1449`）：
  - `topic: str`
  - `message: str`
  - `council_planets?: list[str]`（默认 `["SUN","MOON","MARS","VENUS","SATURN"]`）
  - header `Authorization`
- **响应**：
  - 正常：`{ status: "ok", data: { topic, perspectives[], relation, synthesis, source, theme, members[], access } }`
  - 危机：`{ status: "crisis", data: crisis.to_dict() }`
  - 超额：`{ status: "error", error_code: "QUOTA_EXCEEDED", data: { message, access } }`
- **功能**：星灵议会——多行星视角协作 + 主持人合成（LLM 驱动）。
- **业务**：每颗行星以「已算好的星盘事实 + 人格」为 grounding，用 LLM 独立发言（并行）；主持人合成统一觉察。LLM 不可用时降级规则桩。全程受 ACP 宪法约束。前置：危机检测 → 额度校验。
- **用户效果**：用户提一个问题，多颗星灵各给一句不同角度的话 + 主持人综合；用户感受到「对的部分被叫出来了」。额度：测试用户/VIP 直通；非 VIP 每周 3 次免费。
- **引擎层**：`detect_crisis`（`life_kline.safety`）→ `AccessChecker.check_council()` → `CouncilEngine(report_data, llm_client).create_session(...)` → **`engine.generate_council_response_async(session, message, theme=theme)`**；`ThemeRecognizer().recognize` + `build_theme_narrative`（`life_kline.akg`）；`_dao.increment_council_usage`。

---

## 6. 今日星灵 / 每日一问

### `GET /api/today-star-spirit/{report_id}`  ·  `main.py:1661`  · 需登录
- **请求**：path `report_id`；header `Authorization`。
- **响应**：`{ status, report_id, data: result.to_dict() }`（含 `planet, planet_label, symbol, reason, confidence, sign, sign_label`）；失败回退月亮。
- **功能**：获取用户今日「引路星灵」。
- **业务**：三层优先级算法——①精准行运（orb≤1°）→ ②行运月亮触发本命 → ③当前月亮星座守护 → 默认月亮。
- **用户效果**：用户每天进 App 知道「今天花园想请出哪颗星灵」及原因。
- **引擎层**：`_reconstruct_chart_from_user_info`（`EphemerisEngine`）→ **`TodayStarSpiritEngine(service).compute_today_star_spirit(chart)`**。

### `GET /api/daily-question/{report_id}`  ·  `main.py:1704`  · 需登录
- **请求**：path `report_id`；header `Authorization`。
- **响应**：`{ status, report_id, data: question.to_dict() }`（含 `question, spirit_planet, spirit_planet_label, context_note, voice_text, generated_at`）。
- **功能**：获取每日一问（LLM 模式 + 规则回退）。
- **业务**：基于今日引路星灵 + 行运，生成一句引导用户自我觉察的提问。
- **用户效果**：用户每天收到一颗星灵抛来的一个问题，作为当日觉察入口。
- **引擎层**：`TodayStarSpiritEngine(...).compute_today_star_spirit(chart)` → `DailyQuestionEngine(llm_client=LLMClient()).generate(today_spirit, chart, transits)`；`service.compute_transits(chart)`。

---

## 7. 星灵日记（Spirit Diary）

### `GET /api/spirit-diary/{report_id}/styles`  ·  `main.py:1768`
- **请求**：path `report_id`；query `spirit_planet?: str`、`mood_emoji?: str`、`message?: str`。
- **响应**：`{ status, report_id, data: suggestions }`。
- **功能**：获取日记风格建议（基于最近对话上下文）。
- **业务**：用于前端「创建日记前」展示可选风格（check_in / dialogue / reflection / spirit / summary）。
- **用户效果**：用户写日记前看到几种风格预览，点选即用。
- **引擎层**：`DiaryEngine(diary_dir=DIARY_DIR).get_style_suggestions(...)`。

### `POST /api/spirit-diary/{report_id}/entry`  ·  `main.py:1802`  · Authorization 可选
- **请求**：path `report_id`；body `DiaryInput`（`main.py:1754`：`chat_context?, spirit_planet?, mood_emoji?, user_messages?:list[str], spirit_responses?:list[str], diary_style?:str="summary", evening_expectation?`）。
- **响应**：`{ status, report_id, data: entry.to_dict(), diary_preview: previews }`。
- **功能**：创建星灵日记条目（优先写 DB，JSON 兜底）。
- **用户效果**：用户和星灵聊完后，一键生成一条带风格/关键词/能量等级的日记，沉淀到时间线。
- **引擎层**：`DiaryEngine(...).get_style_suggestions(...)` + `engine.extract_and_generate(..., diary_style)`。

### `GET /api/spirit-diary/{report_id}`  ·  `main.py:1863`  · 需登录
- **请求**：path `report_id`；query `limit?: int=30`、`offset?: int=0`。
- **响应**：`{ status, report_id, data: { entries[], total } }`。
- **功能**：获取星灵日记时间线（DB 读取，JSON 兜底）。
- **用户效果**：用户翻看自己的日记历史。
- **引擎层**：`_dao.list_star_diary` + `_dao.count_star_diary`；兜底 `DiaryEngine.get_timeline`。

### `PATCH /api/spirit-diary/{entry_id}`  ·  `main.py:1926`  · 需登录
- **请求**：path `entry_id`；body `DiaryUpdateInput`（`main.py:1915`：`entry_text?, keywords?:list[str], mood_emoji?, diary_style?, evening_expectation?, topic_tag?, energy_level?:int`）。
- **响应**：`{ status, data: row }`；404 无权编辑。
- **功能**：更新日记条目（仅本人）。
- **用户效果**：用户编辑日记内容/心情/标签。
- **引擎层**：`_dao.update_star_diary(...)`。

### `DELETE /api/spirit-diary/{entry_id}`  ·  `main.py:1970`  · 需登录
- **请求**：path `entry_id`。
- **响应**：`{ status, entry_id }`（硬删除）。
- **功能**：删除日记条目（仅本人）。前端删除后需刷新列表。
- **引擎层**：`_dao.delete_star_diary(entry_id, user_id)`。

---

## 8. AI 星灵对话（引擎 + LLM 双层）

### `POST /api/spirit-chat/{report_id}`  ·  `main.py:2069`  · 需登录  · 报告所有者
- **请求**：path `report_id`；body `SpiritChatInput`（`main.py:2061`）：
  - `planet: str`
  - `topic: str = "personal"`
  - `message: str`
  - `history: list[dict] = []`
  - `entry_context?: dict`（来源标记：`transit` / `daily_question` / `today_star_spirit` / `council` / `diary_revisit`）
  - header `Authorization`
- **响应**：
  - 正常：`{ status, data: { planet, response, user_message, spirit_response, domain, emotional_state, engine_reading{ acknowledgment, mirroring, guidance, evidence }, source("engine"|"llm_enhanced"|"crisis_guard"), ai_access, suggested_followup, diary_style_suggestions[] } }`
  - 危机：`{ status:"success", source:"crisis_guard", data:{ spirit_response, is_crisis, crisis, engine } }`
- **功能**：星灵对话——引擎占星师 + AI 增强双层架构（V1 prompt）。
- **业务**：引擎层（永远在线）路由意图 → 读取星盘证据 → 渲染结构化回复（acknowledgment/mirroring/guidance/evidence）；AI 层（可选）拿到结构化输出后做语音翻译美化。引擎对话有免费额度，AI 对话消耗星币或 VIP 额度。
- **用户效果**：用户和某颗星灵对话，得到「先共情 → 镜像 → 引导 → 给星盘证据」的结构化陪伴；并附带可跟进话题与日记风格建议。
- **引擎层**：**`EngineAstrologer(report_data).consult(report_id, planet, user_message, topic_hint, history, entry_context)`** → 危机短路 → `LLMClient.chat_async`（`build_spirit_system_prompt` V1）→ `GrowthTracker.record_conversation` + `_dao.insert_chat_message` + `_dao.increment_ai_usage` + `DiaryEngine.get_style_suggestions`。

### `POST /api/spirit-chat-v2/{report_id}`  ·  `main.py:2293`  · 需登录  · 报告所有者
- **请求**：path `report_id`；body `SpiritChatV2Input`（`main.py:2282`）：
  - `planet: str`
  - `topic: str = "personal"`
  - `message: str`
  - `history: list[dict] = []`
  - `entry_context?: dict`
  - `dialogue_token?: str`（跨轮状态续接）
  - header `Authorization`
- **响应**：`{ status, data: { planet, response, user_message, spirit_response, source("consultation_v2"|"consultation_v2_ai"), stage, dialogue_state{ stage, turn_count, theme_key, user_expressed }, dialogue_token, ai_access, memory_context{ recent_topics, recent_milestones } } }`。
- **功能**：咨询式星灵对话 V2——新架构。
- **业务**：五阶段状态机 **倾听 → 探索 → 反思 → 理解 → 结束**。核心理念：先倾听不急着分析；问问题多于给答案；把星盘翻译成感受/模式；引导觉察而非给建议。接入纵向记忆 `MemoryManager` 与成长信号分析。
- **用户效果**：用户感受到「星灵在一步步陪我理清自己」，而非一次性甩答案；跨轮记忆让星灵记得之前聊过什么。
- **引擎层**：**`ConsultationV2(report_data, planet, dialogue_state).chat(message, history)`** + `MemoryManager(report_id)` + `build_spirit_system_prompt_v2`（`life_kline.llm_client`）+ `LLMClient.chat_async`；`GrowthSignalAnalyzer` + `analyze_from_dialogue_state` + `memory_mgr.apply_growth_signals` + `memory_mgr.add_session_summary`；`_dao.insert_chat_message` + `_dao.increment_ai_usage`。

---

## 9. 行运（Transit）

### `GET /api/transit/now`  ·  `main.py:2656`
- **请求**：无。
- **响应**：`{ status, data: { timestamp, planets{ planet: { sign, degree, retrograde } }, interpretation } }`（默认用北京 39.9/116.4 计算当下星象）；服务未初始化返回 503。
- **功能**：获取当下实时星象。
- **用户效果**：用户看到此刻各行星所在星座/度数/是否逆行。
- **引擎层**：`service.engine.calculate_chart(now_utc, 39.9, 116.4)`（`EphemerisEngine`）。

### `GET /api/daily-transits/{report_id}`  ·  `main.py:2712`  · 需登录
- **请求**：path `report_id`；header `Authorization`。
- **响应**：`{ status, report_id, data: asdict(report) }`。
- **功能**：获取用户本命盘的分层每日行运报告。
- **业务**：4 层——月亮 / 快行星 / 逆行 / 慢行星背景。
- **用户效果**：用户看到今天行运对自己各层面的影响与高亮。
- **引擎层**：`_reconstruct_chart_from_user_info` → **`DailyTransitEngine(EphemerisEngine()).compute_daily_transits(chart)`**。

---

## 10. 花园（Garden · 分析工具集 / 咨询）

### `GET /api/garden/categories`  ·  `main.py:2763`
- **请求**：无。
- **响应**：`{ status, data: garden_catalog_dict() }`。
- **功能**：获取花园分类与抓手问题列表（7 大领域 + 运势专区）。
- **业务**：前端「花园入口」数据源；每个抓手问题映射到核心宫位/行星。
- **用户效果**：用户在花园里选择一个想聊的话题入口。
- **引擎层**：`life_kline.garden_catalog.to_dict()`。

### `GET /api/garden/checkin`  ·  `main.py:2769`  · 需登录
- **请求**：header `Authorization`。
- **响应**：`{ status, data: { checked_in: bool, streak_count, checkin_date } }`。
- **功能**：获取今日签到状态。
- **用户效果**：用户看到今天是否已签到、连续天数。
- **引擎层**：SQL 查 `checkins` 表。

### `POST /api/garden/checkin`  ·  `main.py:2813`  · 需登录
- **请求**：header `Authorization`。
- **响应**：`{ status, data: { checked_in, streak_count, checkin_date, message } }`。
- **功能**：执行每日签到（按昨日 streak+1）。
- **用户效果**：用户点击签到，连续天数 +1，得到一句反馈。
- **引擎层**：SQL `INSERT INTO checkins`。

### `POST /api/garden/consultation/{report_id}/start`  ·  `main.py:2879`  · 需登录  · 报告所有者
- **请求**：path `report_id`；body `GardenConsultStartInput`（`main.py:2754`：`category:str, question_key:str`）；header `Authorization`。
- **响应**：`{ status, data: state.to_dict() }`（`ConsultationState`）。
- **功能**：开始新咨询——星语者四步法 Step 1 锚定。
- **业务**：用户选定抓手问题后，启动「星语者」咨询会话（双层架构：引擎规则 + LLM 翻译，失败降级）。会话落 DB。
- **用户效果**：用户进入一次结构化咨询，星语者先锚定问题。
- **引擎层**：**`ConsultationEngine(report_data, _garden_llm_client).start_consultation(category, question_key)`**；`_garden_session_mgr.store` + DB `INSERT INTO consultation_sessions`。

### `POST /api/garden/consultation/{report_id}/continue`  ·  `main.py:2924`  · 需登录  · 报告所有者
- **请求**：path `report_id`；body `GardenConsultContinueInput`（`main.py:2758`：`session_id:str, user_response:str`）；header `Authorization`。
- **响应**：`{ status, data: state.to_dict() }`。
- **功能**：继续咨询——推进到下一步（场景定位 2-3 轮 → 星盘验证）。
- **用户效果**：用户多轮回答，星语者逐步定位场景并引入星盘验证。
- **引擎层**：**`ConsultationEngine(...).continue_consultation(state, user_response)`**；可从 DB 恢复 session。

### `POST /api/garden/consultation/{report_id}/report`  ·  `main.py:2986`  · 需登录  · 报告所有者
- **请求**：同 continue（`session_id`, `user_response`）；header `Authorization`。
- **响应**：`{ status, data: report.to_dict() }`。
- **功能**：生成最终咨询报告（含边界守护），并顺手写一条日记。
- **用户效果**：用户得到一份本次咨询的结论报告，沉淀到花园报告历史。
- **引擎层**：`engine._run_chart_verify(state)`（如未完成）→ **`ConsultationEngine.generate_report(state)`**；DB `INSERT INTO consultation_reports`；`DiaryEngine.extract_and_generate`。

### `GET /api/garden/reports`  ·  `main.py:3050`  · 需登录
- **请求**：query `category?: str`、`limit?: int=20`、`offset?: int=0`；header `Authorization`。
- **响应**：`{ status, data: { reports[{ id, category, category_label, question_key, question_label, summary, created_at }], total } }`。
- **功能**：获取花园咨询报告历史。
- **用户效果**：用户翻看历次咨询结论。
- **引擎层**：SQL `consultation_reports` + `garden_catalog.get_category`。

### `GET /api/garden/reports/{report_id}`  ·  `main.py:3099`  · 需登录
- **请求**：path `report_id`；header `Authorization`。
- **响应**：`{ status, data: report_json }`。
- **功能**：获取单份花园咨询报告。
- **引擎层**：SQL `SELECT * FROM consultation_reports WHERE id AND user_id`。

---

## 11. 认证 / 用户档案

### `POST /api/auth/send-code`  ·  `main.py:3145`
- **请求**：body `SendCodeInput`（`main.py:452`：`phone:str`）。
- **响应**：`{ status, message }`（开发模式打印验证码到控制台）。
- **功能**：发送手机验证码（6 位，5 分钟过期）。
- **引擎层**：SQL `INSERT INTO verify_codes`。

### `POST /api/auth/verify-code`  ·  `main.py:3162`
- **请求**：body `VerifyCodeInput`（`main.py:456`：`phone:str, code:str`）。
- **响应**：`{ status, token, user_id }`。
- **功能**：校验验证码并登录/注册，返回用户 token。
- **业务**：开发绕过——env `LIFE_KLINE_DEV_BYPASS_PHONE` + 验证码 `000000` 直登。
- **引擎层**：SQL 校验 `verify_codes` → 创建/更新 `users` → `_make_token(user_id)`。

### `GET /api/auth/check`  ·  `main.py:3211`
- **请求**：header `Authorization`。
- **响应**：`{ status, user_id }`；401 无效。
- **功能**：校验当前 token 是否有效。
- **引擎层**：`_parse_token`。

### `GET /api/me`  ·  `main.py:3221`  · 需登录
- **请求**：header `Authorization`。
- **响应**：`{ status, user: { id, nickname, role, created_at, last_login_at }, profiles[] }`。
- **功能**：获取当前用户信息 + 档案列表。
- **引擎层**：SQL `users` + `profiles`。

### `POST /api/profiles`  ·  `main.py:3270`  · 需登录
- **请求**：body `ProfileInput`（`main.py:461`：`name, gender, birth_time:str, lat:float, lon:float, timezone:float=8.0, birth_place:str, house_system:str="B", daylight_saving:bool, residence_place, residence_lat, residence_lon`）；header `Authorization`。
- **响应**：`{ status, profile_id, geocoded: bool, dst_auto: bool }`；409 已存在档案。
- **功能**：创建出生档案（一账户一 profile 限制）。
- **业务**：自动地理编码（`_geocode_place`）+ 中国 1986-1991 夏令时自动判定（`_auto_detect_dst`）。
- **用户效果**：用户输入出生地/时间，系统自动校正经纬度与夏令时。
- **引擎层**：`_geocode_place` + `_auto_detect_dst` + SQL INSERT。

### `GET /api/profiles`  ·  `main.py:3313`  · 需登录
- **请求**：header `Authorization`。
- **响应**：`{ status, profiles: [...] }`。
- **功能**：列出当前用户档案。

### `PUT /api/profiles/{profile_id}`  ·  `main.py:3324`  · 需登录
- **请求**：path `profile_id`；body `ProfileInput`（部分更新，`model_dump(exclude_unset=True)`）；header `Authorization`。
- **响应**：`{ status, profile_id, updated: list[str], profile }`。
- **功能**：更新档案（同 POST 的 geocode + DST 自动判定；动态构造 UPDATE SQL）。

---

## 12. 定价与权限

### `GET /api/pricing`  ·  `main.py:1994`
- **请求**：无。
- **响应**：`{ status, data: get_pricing_info() }`。
- **功能**：获取完整定价信息（VIP 订阅档位 + 星币包 + 免费额度 + 消耗规则）。
- **用户效果**：用户在付费页看到会员档位与星币购买选项。
- **引擎层**：`life_kline.pricing.get_pricing_info()`。

### `GET /api/access/{user_id}`  ·  `main.py:2001`
- **请求**：path `user_id`。
- **响应**：`{ status, data: { user_id, is_test_user, is_vip, coins, engine, ai, council } }`（各项含 `access` dict）。
- **功能**：获取用户当前权限状态（引擎/AI/议会各自的额度与可用性）。
- **用户效果**：前端据此显示「剩余免费次数 / 需付费」。
- **引擎层**：`load_user_state` → `AccessChecker(state).check_engine_chat("SUN")/check_ai_chat()/check_council()`。

---

## 13. 地理编码

### `POST /api/geocode`  ·  `main.py:2547`  · response_model=`GeocodeResult`
- **请求**：body `GeocodeInput`（`main.py:407`：`query:str`）。
- **响应**：`{ status, data: { lat, lon, label, ... } }`；404 未找到 / 504 超时 / 502 不可用。
- **功能**：地名 → 经纬度（多 provider 顺序尝试）。
- **业务**：provider 链——`amap`（需 `AMAP_KEY`）→ `nominatim_global` → `nominatim_cn` → `maps_co`；超时 `GEOCODE_TIMEOUT_SECONDS=4s`。
- **用户效果**：用户输入出生地名称，系统解析为坐标。
- **引擎层**：`_geocode_place` + `parse_amap_geocode_result` / `parse_public_geocode_result`。

---

## 14. Admin CMS（后台管理 API）

> 所有 admin 端点经 `Depends(_admin.require_admin)` 或 `require_super_admin` 鉴权，返回 `AdminContext` 供 `ctx.log()` 写审计日志。路由声明均在 `backend/main.py`，鉴权辅助在 `backend/admin.py`。

### 认证
| 方法 | 路径 | 行号 | 功能 |
|---|---|---|---|
| POST | `/api/admin/login` | 3592 | 管理员登录（`username, password` → `{ token, admin }`） |

### 数据看板
| 方法 | 路径 | 行号 | 功能 |
|---|---|---|---|
| GET | `/api/admin/stats` | 3619 | 数据统计面板 |

### 用户管理
| 方法 | 路径 | 行号 | 功能 |
|---|---|---|---|
| GET | `/api/admin/users` | 3626 | 用户列表（`keyword?, is_disabled?, limit=30, offset=0`） |
| GET | `/api/admin/users/{user_id}` | 3646 | 用户详情（含 report_count / diary_count） |
| PATCH | `/api/admin/users/{user_id}` | 3666 | 编辑用户（禁用/启用、改昵称）+ 审计 |
| DELETE | `/api/admin/users/{user_id}` | 3687 | 软删除用户（仅 super_admin）+ 审计 |

### 日记审核
| 方法 | 路径 | 行号 | 功能 |
|---|---|---|---|
| GET | `/api/admin/diary` | 3698 | 日记管理列表（`keyword?, status="all", spirit_planet?, user_id?, limit=30, offset=0`） |
| GET | `/api/admin/diary/{entry_id}` | 3729 | 日记详情（含 mod_status / mod_reason） |
| PATCH | `/api/admin/diary/{entry_id}` | 3755 | 日记审核（`status: visible/hidden/flagged`, `reason`）+ 审计 |
| DELETE | `/api/admin/diary/{entry_id}` | 3772 | 删除日记 + 审计 |

### 报告管理
| 方法 | 路径 | 行号 | 功能 |
|---|---|---|---|
| GET | `/api/admin/reports` | 3786 | 星语者报告列表（`keyword?, user_id?, analysis_type?, limit=30, offset=0`） |
| GET | `/api/admin/reports/{report_id}` | 3809 | 报告详情（含 JSON 文件内容） |
| DELETE | `/api/admin/reports/{report_id}` | 3853 | 删除报告（DB + JSON 双删）+ 审计 |

### 系统
| 方法 | 路径 | 行号 | 功能 |
|---|---|---|---|
| GET | `/api/admin/audit-logs` | 3879 | 审计日志（`admin_username?, action?, target_type?, limit=30, offset=0`） |
| GET | `/api/admin/settings` | 3904 | 系统设置列表 |
| PUT | `/api/admin/settings` | 3911 | 更新系统设置（`key, value`）+ 审计 |
| GET | `/api/admin/admins` | 3921 | 管理员列表 |
| POST | `/api/admin/admins` | 3928 | 新增管理员（仅 super_admin）+ 审计 |

---

## 附录 A · 引擎层调用速查表

| 引擎类/函数 | 来源模块 | 被哪些端点调用 |
|---|---|---|
| `run_analysis` | `life_kline.service` | `/api/analyses`, `/api/analyze` |
| `LifeKlineService.generate_report` | `life_kline.service` | `/api/users/chart` |
| `service.compute_transits` | `life_kline.service` | `/api/daily-question/{id}` |
| `service.engine.calculate_chart` | `EphemerisEngine` | `/api/transit/now`、多端点 `_reconstruct_chart_from_user_info` |
| `calculate_firdaria_periods` | `life_kline.firdaria` | `/api/natal-chart/{id}`, `/api/characters/{id}/daily`, `/api/users/chart` |
| `CharacterEngine` + `DailyAwakeningEngine.compute_daily_activation` | `life_kline.characters` / `awakening` | `/api/characters/{id}/daily` |
| **`EngineAstrologer.consult`** | `life_kline.engine_astrologer` | `/api/spirit-chat/{id}` |
| **`CouncilEngine.generate_council_response_async`** | `life_kline.council` | `/api/council/{id}` |
| `ThemeRecognizer.recognize` + `build_theme_narrative` | `life_kline.akg` | `/api/council/{id}` |
| **`TodayStarSpiritEngine.compute_today_star_spirit`** | `life_kline.today_engine` | `/api/today-star-spirit/{id}`, `/api/daily-question/{id}` |
| `DailyQuestionEngine.generate` | `life_kline.daily_question_engine` | `/api/daily-question/{id}` |
| **`ConsultationV2.chat`** | `life_kline.consultation` | `/api/spirit-chat-v2/{id}` |
| `MemoryManager` + `GrowthSignalAnalyzer` | `life_kline.memory` / `growth` | `/api/spirit-chat-v2/{id}` |
| **`ConsultationEngine.start/continue/generate_report`** | `life_kline.consultation_engine` | `/api/garden/consultation/{id}/start\|continue\|report` |
| `DiaryEngine.get_style_suggestions` / `extract_and_generate` / `get_timeline` | `life_kline.diary_engine` | `/api/spirit-diary/*`、`/api/garden/consultation/{id}/report` |
| `GrowthTracker.record_conversation` / `load` | `life_kline.growth.growth_tracker` | `/api/characters/{id}/chat`, `/api/spirit-chat/{id}`, `/api/characters/{id}/growth` |
| **`DailyTransitEngine.compute_daily_transits`** | `life_kline.transit_engine` | `/api/daily-transits/{id}` |
| `detect_crisis` | `life_kline.safety` | `/api/council/{id}`、`/api/spirit-chat/{id}`（经 `EngineAstrologer`） |
| `AccessChecker.check_*` | `life_kline.pricing` | `/api/spirit-chat/{id}`, `/api/spirit-chat-v2/{id}`, `/api/council/{id}`, `/api/access/{user_id}` |
| `LLMClient.chat_async` | `life_kline.llm_client` | council / spirit-chat / spirit-chat-v2 / garden consultation / daily-question |
| `garden_catalog.to_dict` / `get_category` | `life_kline.garden_catalog` | `/api/garden/categories`, `/api/garden/reports` |
| `_geocode_place` + amap/nominatim/maps_co | `backend/main.py` | `/api/geocode`, `/api/profiles`, `/api/profiles/{id}` |

---

## 附录 B · 已知工程隐患（待修，非 API 契约问题）

- `consultation_engine.py` 的 `_detect_timing` 引用 **不存在的 `.timing` 模块**，被 try/except 静默吞掉，法达时间推运实际失效。
- `companion/`、`counseling/` 是空目录，`perspectives/` 仅占位——三个 advertised 子系统未实现。
- `__init__.py` 把所有计算函数注释掉，包级 API 名实不符。
- 三套人格化系统并存（10 行星 / 12 星座 / 星语者），按 Product Bible 方向待统一为「Garden Keeper + 10 星灵」。
