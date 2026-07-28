# CLAUDE.md

本文件为 Claude Code 提供项目指引。详细工程规范见 `docs/ENGINEERING_STANDARD.md`,拆出的开发细节见 `docs/developer-reference.md`,HTTP API 总览见 `docs/api-reference.md`。

## ⚠️ 最高开发准则

本项目是企业级工程化项目,需落地、承接高并发。所有开发(主 agent 与全部 subagent)在写任何代码前,必须先读取并严格执行 `docs/ENGINEERING_STANDARD.md`。

- 规范采用 MUST / SHOULD / MAY 分级;违反 MUST 项即阻断合并。
- 提交前必须逐条走规范附录 A 的《PR 自检清单》。
- 规范 §0 维护着项目技术债审计表(D1–D10),新代码零豁免、不得加重任何既有债务。
- subagent 被派发任务时,必须将本节与 `docs/ENGINEERING_STANDARD.md` 视为不可协商的约束。

## Project Overview

Life K-Line Engine 是融合古占与现占的占星人生分析系统。计算本命盘、行星禀赋、相位、宫位、接纳、飞星链、法达周期,再用五层规则引擎产出 8 大领域结构化报告。Version 0.3.3 → 过渡到 v1.0。

## Development Commands

### Backend
```bash
pip install -e .
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd frontend && npm install && npm run dev   # Vite, proxy /api → backend
npm run build                                # type-check + 生产构建
```

### Tests
```bash
python tests/run_all_tests.py
pytest tests/ -v
```
`life_kline` 包必须可导入(`pip install -e .` 或 `PYTHONPATH` 指向 `src/`)。

### Environment Variables
- Backend: `LIFE_KLINE_HOST/PORT`, `LIFE_KLINE_CORS_ORIGINS`, `LIFE_KLINE_AMAP_KEY`(高德地理编码), `LIFE_KLINE_GEOCODE_TIMEOUT`
- Frontend: `VITE_API_BASE_URL`, `VITE_DEV_PROXY_TARGET`, `VITE_SHOW_HOMEPAGE_EXAMPLE`(见 `frontend/.env.example`)

## Architecture

### 五层解释规则引擎
```
行星 → 星座 → 宫位 → 飞星 → 相位 → Composer → 8 大领域 → 报告
```
每层支持古占+现占双轨:古占断"容不容易成",现占描"心理怎么处理"。

### 目录结构
```
src/life_kline/
  constants.py models.py ephemeris.py dignities.py houses.py aspects.py
  receptions.py features.py scoring.py firdaria.py flystar_catalog.py
  analysis_catalog.py service.py
  interpretation/   # 五层规则(planet/sign/house/flystar/aspect_rules)
  domains/          # 8 领域分析器(base/personal/finance/family/romance/marriage/work_skill/career/education)
  composer.py       # 多维叙事合成引擎
backend/main.py     # FastAPI(+ GCJ-02→WGS84)
frontend/src/views/ # home / Analysis / Kline / MonthlyReturn
```

### 核心数据流
输入(生时/经纬度/时区)→ Ephemeris → 特征计算(dignities+houses+aspects+receptions)→ Firdaria → 8 领域分析(古现占按权重融合)→ Composer 五层优先级链 → 报告 JSON → 存储 → Vue 渲染。

领域权重表、OHLC 评分公式、分析类型系统、地理编码 provider 链等细节见 `docs/developer-reference.md`。

## Key Conventions

- 中文占星术语贯穿(庙旺/失势/落陷, 法达, 飞星 等)。
- PRD(`PRD.md`, v1.0)是基线 —— 任何分析类型/路由/API/领域/规则模型变更须同步更新。
- **所有引擎逻辑必须规则驱动、通用化,禁止针对具体人物硬编码分支。**
- Legacy API: `POST /api/analyze`、`GET /api/report/{id}` 转发到新统一端点;前端 `/kline` 是 `/reports/:id` 的旧别名。
- `docs/` 为参考资料(case study / 策略 / 占星笔记),非生产代码。
- `backend/data/` 在 `.gitignore`(新数据);既有 tracked 文件保留为样本。
- 注释从简,仅注释复杂逻辑。

## Agent Memory

记忆目录(全局生效):`C:\Users\PC\.claude\projects\C--Users-PC-Desktop-red-life-kline-engine\memory\`

- 索引 `MEMORY.md` 每次会话注入;单个 memory 文件按需召回,不会全量加载。
- 重要决策/产品方向/架构变更 → 写入该目录,并在 `MEMORY.md` 加一行索引。
- 文件 frontmatter 格式与类型定义见 `docs/developer-reference.md`。
- subagent spawn 时先读 `MEMORY.md` 获取索引,任务完成后按需写入。
