# 星灵花园占星 AI Agent 架构

版本：v1.0  
更新日期：2026-07-31  
状态：目标架构与迁移基线

## 1. 目标

`src/life_kline` 的唯一目标，是成为星灵花园的垂直占星领域内核：

- 用确定性引擎计算星盘事实，不让 LLM 编造宫位、相位、尊贵或推运。
- 用结构化占星知识解释事实，明确区分古典事件判断与现代心理解释。
- 用 Agent 编排理解用户问题、选择工具、管理上下文、组织咨询过程。
- 用 10 颗行星星灵提供不同内在视角，但共享同一份用户事实与记忆。
- 把用户确认过的洞察和行动沉淀为成长记录，不把模型猜测写成事实。

## 2. 当前主链

生产前台 `/chat/:planet` 当前走这一条链路：

```text
Chat/index.vue
  -> useSpiritConsultation.ts
  -> POST /api/v2/spirit-consultations/{report_id}/{session_id}/turn
  -> SpiritConsultationService
  -> spirit_consultation.state_machine.resolve_turn
  -> build_spirit_dossier / ChartReader
  -> LLMClient.chat_stream（表达）
  -> Redis 会话状态 + SQLite 消息/确认洞察
```

其他对话链路均不是未来主链：

- `/api/spirit-chat/{report_id}`：V1 引擎占星师 + LLM，兼容期。
- `/api/spirit-chat-v2/{report_id}`：旧版五阶段咨询，待退役。
- `/api/characters/{report_id}/chat`：12 星座规则角色，待退役。
- `/api/garden/consultation/*`：星语者四步咨询，能力并入领域 Agent 后退役。
- `/api/council/{report_id}`：多行星议会，保留产品能力，改为主 Agent 的工具。

## 3. `src/life_kline` 现状盘点

### 3.1 确定性占星内核：保留

| 模块 | 职责 | 决策 |
|---|---|---|
| `constants.py` | 行星、星座、尊贵、相位常量 | 保留；拆分古典/现代常量 |
| `models.py` | 星盘核心数据模型 | 保留；后续迁入 `astrology/models.py` |
| `ephemeris.py` | 星历与行星位置 | 保留 |
| `houses.py` | 宫制与宫位计算 | 保留 |
| `dignities.py` | 本质/偶然尊贵 | 保留；外行星不得进入古典尊贵评分 |
| `aspects.py` | 相位计算 | 保留；按行星类别配置容许度 |
| `receptions.py` | 接纳、互溶 | 保留；仅传统守护体系参与古典接纳 |
| `firdaria.py` | 法达 | 保留 |
| `transit_engine.py` | 行运 | 保留；补事件时间与本命触发契约 |
| `today_engine.py` | 今日引路星灵 | 保留，作为 Agent 工具 |
| `features.py`、`scoring.py` | 特征与内部评分 | 保留；禁止把分数直接包装成命运结论 |
| `chart_structure.py` | 星盘结构摘要 | 保留，统一为工具输出格式 |

### 3.2 结构化知识与解释：保留并统一

| 模块 | 职责 | 决策 |
|---|---|---|
| `interpretation/*` | 行星/星座/宫位/飞星/相位规则 | 保留，作为知识事实源 |
| `domains/*` | 12 人生领域分析 | 保留，统一输入输出契约 |
| `analysis_catalog.py` | 分析类型目录 | 保留 |
| `flystar_catalog.py` | 飞星目录 | 保留 |
| `composer.py` | 多层叙事组合 | 保留；停止承担产品路由职责 |
| `guide_spirit_narrative.py` | 引路星灵叙事 | 合并到统一 narrative 层 |
| `akg/*` | 主题知识图谱 | 保留；从关键词排序升级为语义主题层 |

### 3.3 Agent 与咨询：当前重复最多，必须收敛

| 模块 | 当前职责 | 决策 |
|---|---|---|
| `spirit_consultation/*` | 当前深度咨询状态机、证据档案 | 作为主咨询内核保留 |
| `engine_astrologer.py` | V1 意图、读盘、模板回应 | 拆出 `ChartReader`，其余兼容后退役 |
| `consultation.py` | 早期咨询实现 | 退役 |
| `consultation_engine.py` | 花园四步咨询 | 能力合并后退役 |
| `council/*` | 多行星视角 | 保留为 Agent tool，不单独拥有记忆 |
| `llm_client.py` | Provider、Prompt、流式、旧状态存储混合 | 拆成 provider / prompts / structured output |
| `acp.py` | Agent 宪法与反宿命规则 | 保留，升级为输入/输出双重护栏 |
| `safety.py` | 危机检测 | 保留，所有入口最前置执行 |

### 3.4 星灵人格：保留 10 行星，退役 12 星座角色

| 模块 | 决策 |
|---|---|
| `characters/planet_personas.py` | 保留，缩短静态文案，增强可执行 voice spec |
| `characters/planet_character_engine.py` | 保留，修正外行星尊贵与强度逻辑 |
| `characters/sign_personas.py` | 仅作为星座表达风格知识，不再是可聊天角色 |
| `characters/character_engine.py` | 12 星座角色兼容期后退役 |
| `characters/spirit_triggers.py` | 合并到今日星灵/Agent router |

### 3.5 记忆与成长：重建，不沿用多套状态

| 模块 | 当前问题 | 决策 |
|---|---|---|
| `memory.py` | 进程缓存、导入路径错误、与当前主链未连接 | 重写为持久化 Memory Service |
| `growth/growth_tracker.py` | JSON/SQLite 双轨、偏互动次数 | 退役计数式“成长”，保留数据迁移 |
| `growth/signal_analyzer.py` | 关键词推断成长，误判风险高 | 仅作候选信号，不直接写成长结论 |
| `growth/detector.py` | 多套状态模型 | 合并为确认洞察与行动回访模型 |
| `diary_engine.py` | 日记生成 | 保留；只消费用户确认内容 |

### 3.6 产品辅助能力

`garden_catalog.py`、`daily_question_engine.py`、`awakening/*`、`pricing.py`、
`flight_fortune.py` 属于产品能力，不应反向依赖具体页面或旧对话状态。

## 4. 目标包结构

先通过适配层迁移，不进行一次性大搬家：

```text
src/life_kline/
  astrology/                 # 确定性计算
    models.py
    ephemeris.py
    natal.py
    dignity.py
    aspect.py
    reception.py
    timing.py
  knowledge/                 # 版本化解释知识
    classical/
    modern/
    domains/
    themes/
  agent/                     # 唯一 Agent 编排层
    orchestrator.py
    router.py
    contracts.py
    context_builder.py
    response_planner.py
    tools/
      natal.py
      domain.py
      timing.py
      memory.py
      council.py
    consultation/
      state.py
      planner.py
      insight.py
    prompts/
  personas/                  # Garden Keeper + 10 星灵 voice spec
  memory/                    # working / episodic / semantic / growth
  safety/                    # crisis / scope / output guard
  providers/                 # LLM、embedding、TTS 的供应商适配
```

迁移期间，旧导入路径继续导出兼容符号；每次迁移一个垂直切片并补回归测试。

## 5. Agent 运行模型

### 5.1 一轮请求

```text
输入安全检查
  -> 对话理解（用户行为、目标、领域、情绪、时间范围、实体、置信度）
  -> 模式选择（陪伴 / 快问 / 深度咨询 / 领域探索 / 议会）
  -> 上下文构建（当前会话 + 用户确认记忆 + 星盘摘要）
  -> 工具规划与执行
  -> 证据图合并
  -> 回复计划（回应、解释、证据、问题/行动）
  -> 星灵 voice 渲染
  -> 输出安全检查
  -> 消息落库 + 候选洞察
```

### 5.2 对话理解契约

当前 `TurnIntent` 只描述状态机动作，不能承担完整自然语言理解。目标结构：

```json
{
  "user_act": "share|ask|correct|decide|command|crisis",
  "goal": "understand|timing|choice|comfort|plan|reflect",
  "mode": "companion|quick_reading|consultation|domain|council",
  "domain": "career|romance|...",
  "emotion": {"label": "anxious", "intensity": 0.7},
  "time_scope": "now|month|year|natal|unknown",
  "entities": [],
  "state_action": "continue|confirm|reject|switch_topic|pause|close",
  "confidence": 0.86
}
```

低置信度时先澄清；不得用一个默认 `personal` 答案掩盖没听懂。

### 5.3 Agent 工具边界

| 工具 | 输入 | 输出 |
|---|---|---|
| `get_natal_structure` | report_id、行星/主题 | 结构化本命事实与 evidence_id |
| `get_domain_reading` | report_id、领域 | 古典/现代双轨解释与证据 |
| `get_timing_context` | report_id、时间范围 | 法达/行运/月返信号与不确定性 |
| `get_memory_context` | user_id、主题 | 用户确认洞察、行动、回访时间 |
| `get_council_views` | 问题、候选行星 | 多视角计划，单次合成 |
| `save_confirmed_insight` | 用户确认对象 | 可追溯持久化记录 |

每个工具必须返回 `source`、`evidence_id`、`fact`、`interpretation_scope`、
`confidence`。LLM 只能解释工具结果，不能补造事实。

## 6. 记忆模型

| 层 | 内容 | 存储 | 生命周期 |
|---|---|---|---|
| Working | 当前咨询状态、最近原文 | Redis | 7 天 |
| Conversation | 完整消息与会话摘要 | 关系数据库 | 用户可删除 |
| Semantic | 用户明确确认的模式、偏好、边界 | 关系数据库 | 可编辑/删除 |
| Growth | 行动实验、回访、前后变化 | 关系数据库 | 长期 |

记忆写入规则：

- 模型推测不能直接成为长期记忆。
- `confirmed`、`partial`、`rejected`、`uncertain` 都要保留来源。
- 敏感原文默认不进入摘要；摘要必须可让用户查看、修改和删除。
- 不用“亲密度”和聊天次数冒充成长。

## 7. RAG 决策

现在不应先上一个通用向量知识库。

优先顺序：

1. 星盘计算：只调用确定性工具，禁止 RAG。
2. 占星解释：先检索版本化结构化规则/AKG，返回明确来源。
3. 用户记忆：按用户、主题、时间和确认状态做混合检索，与占星知识分库。
4. 案例库：只有经过脱敏、人工审核和流派标注后才可加入，用于取象候选，不作为事实。

当结构化规则无法覆盖长尾概念、文献量足够且有评测集时，再增加 hybrid RAG
（metadata filter + BM25 + vector + rerank）。RAG 解决知识取回，不解决意图识别、状态管理或人格温度。

## 8. 占星方法边界

- 古典轨：七曜、传统守护、尊贵、接纳、飞星、法达，回答条件、资源与时间背景。
- 现代轨：十行星、相位模式、心理动力，回答体验、模式和自我探索。
- 天王、海王、冥王可作为现代心理/世代因素，不参与古典本质尊贵和接纳评分。
- 同一结论必须标记来自古典、现代或两者交叉，不能把有争议规则写成唯一标准。
- 健康、投资、法律、生死等领域只做倾向与自我观察，不做诊断和确定预测。

## 9. 质量评估

Agent 发布必须有版本化黄金集，至少覆盖：

- 10 种自然语言表达同一意图。
- 陈述、提问、纠正、否定、插话、换题、回到旧话题。
- 无 LLM、超时、中途断流、工具失败。
- 星盘事实一致性与外行星流派边界。
- 自伤危机、医疗/投资越界、宿命表达、依赖诱导。
- 跨轮记忆、跨会话恢复、用户删除记忆。
- 10 星灵在内容一致的前提下保持可辨识声音。

核心指标：意图宏平均 F1、话题路由准确率、事实幻觉率、重复率、用户纠正率、
洞察确认率、行动回访率、降级率、首 token 延迟和每轮成本。

## 10. 迁移顺序

1. 修通当前 v2 主链：意图、标准历史角色、消息持久化、恢复、安全资源。
2. 建立 Agent contracts 与黄金集，把关键词路由降为 fallback。
3. 把 `ChartReader`、领域分析、时间法封装成工具。
4. 将陪伴、快问、深度咨询从一个强制状态机拆成可路由模式。
5. 重建确认式记忆与成长回访。
6. 把 Council 变成工具，统一 10 星灵共享上下文。
7. 退役 12 星座角色、旧 V1/V2 对话和星语者链路。
8. 在评测证明需要后再引入 hybrid RAG。
