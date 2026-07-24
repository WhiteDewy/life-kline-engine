# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Life K-Line Engine is an astrological life analysis system (占星人生模型) that fuses classical (古占) and modern (现占) astrology. It computes natal charts, planetary dignities, aspects, houses, receptions, flystar chains, and Firdaria (法达) periods, then produces structured reports covering 8 life domains using a five-layer interpretation rule engine. Version 0.3.3 → in transition to v1.0.

## Development Commands

### Backend

```bash
pip install -r backend/requirements.txt
pip install -e .        # install the life-kline-engine package in dev mode
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev          # Vite dev server, proxies /api to backend
npm run build        # Type-check + production build
```

### Tests

```bash
python tests/run_all_tests.py        # all tests
python tests/test_basic.py           # constants, models, utils
python tests/test_dignities.py       # dignity calculations
python tests/test_integration.py     # full pipeline
pytest tests/ -v                     # if pytest installed
```

Tests use plain asserts. The `life_kline` package must be importable (`pip install -e .` or set `PYTHONPATH` to include `src/`).

### Environment Variables

Backend (`backend/.env` or `backend/.env.local`):
- `LIFE_KLINE_HOST` / `LIFE_KLINE_PORT` (default 0.0.0.0:8000)
- `LIFE_KLINE_CORS_ORIGINS` — comma-separated allowed origins
- `LIFE_KLINE_AMAP_KEY` — AMap (高德) API key for geocoding in China
- `LIFE_KLINE_GEOCODE_TIMEOUT` (default 4)

Frontend: `VITE_API_BASE_URL`, `VITE_DEV_PROXY_TARGET`, `VITE_SHOW_HOMEPAGE_EXAMPLE` (see `frontend/.env.example`).

## Architecture

### Engine: Five-Layer Interpretation Rules

```
行星 Planet（做什么的能力）
  ↓
星座 Sign（怎么做事的风格）
  ↓
宫位 House（在哪个舞台上演）
  ↓
飞星 Flystar（宫与宫之间的故事线）
  ↓
相位 Aspect（行星之间的对话）
  ↓
组合引擎 Composer → 8 大领域分析 → 报告
```

Each layer supports classical + modern dual-track interpretation. Classical answers "can this be done easily"; modern answers "how do you experience it psychologically."

### Directory Structure

```
src/life_kline/
  constants.py          # Enums + lookup tables (Planet, Sign, AspectType, dignities)
  models.py             # ChartData, PlanetFeature, PlanetInfo, Aspect, NodeScoreResult
  ephemeris.py          # Swiss Ephemeris wrapper (pyswisseph)
  dignities.py          # Essential/accidental dignities
  houses.py             # House systems and house power
  aspects.py            # Aspect detection
  receptions.py         # Mutual reception, dispositor chains
  features.py           # Composite per-planet feature aggregation
  scoring.py            # OHLC node scoring with time-level weights
  firdaria.py           # Firdaria (法达) 75-year period calculation
  flystar_catalog.py    # House ruler flight chain data
  analysis_catalog.py   # Static registry of analysis type definitions
  service.py            # Report generation (being refactored to thin orchestration layer)

  interpretation/       # [NEW] Five-layer rule definitions
    planet_rules.py     # Planet rules (classical + modern dual-track)
    sign_rules.py       # Sign rules + planet filter
    house_rules.py      # House rules (basic / adult / power meanings + triads)
    flystar_rules.py    # Flystar interpretation templates
    aspect_rules.py     # Aspect rules (classical + modern dual-track)

  domains/              # [NEW] Eight domain analyzers
    base.py             # DomainAnalyzer base class
    personal.py         # 1. Personal analysis
    finance.py          # 2. Finance (earned + unearned income)
    family.py           # 3. Parents & family
    romance.py          # 4. Romance & attraction
    marriage.py         # 5. Marriage & business partnership
    work_skill.py       # 6. Work skills & environment
    career.py           # 7. Career & social status
    education.py        # 8. Education & learning

  composer.py           # [NEW] Multi-dimension narrative synthesis engine

backend/
  main.py               # FastAPI server (+ GCJ-02→WGS84 conversion)
  data/                 # JSON file-based report storage

frontend/src/
  views/home/           # Analysis catalog landing page
  views/Analysis/       # Unified input form (/analysis/:type)
  views/Kline/          # Report page with modular panels
  views/MonthlyReturn/  # Lunar return report page
  config/               # API config, examples, methodology
  utils/                # Types, coordinates, planet meanings
  router/index.ts       # Routes: /, /analysis/:type, /reports/:id, /monthly-return/:id
```

### Core Data Flow

1. **Input**: Birth time (ISO 8601), lat/lon, timezone → `AnalysisRequest`
2. **Ephemeris**: `EphemerisEngine.calculate_chart()` → real planetary positions
3. **Feature computation**: `features.py` orchestrates dignities + houses + aspects + receptions → per-planet `PlanetFeature`
4. **Firdaria**: `firdaria.py` calculates life periods (day/night chart)
5. **Domain analysis**: 8 `DomainAnalyzer` instances run classical + modern logic, fused by weight
6. **Composer**: `composer.py` applies the five-layer priority chain to synthesize narratives
7. **Report assembly**: `service.py` (thin orchestration) builds final JSON
8. **Storage**: `backend/data/{report_id}.json`
9. **Frontend**: Vue 3 renders report modules from JSON

### Domain Weights (Classical vs Modern)

| Domain | Classical | Modern | Rationale |
|:---|:---|:---|:---|
| Personal | 40% | 60% | Self-understanding is psychological |
| Finance | 70% | 30% | Money is objective |
| Family | 50% | 50% | Equal parts circumstance + feeling |
| Romance | 30% | 70% | Love is experiential |
| Marriage | 60% | 40% | Marriage has contractual weight |
| Work Skill | 40% | 60% | Skills are personal development |
| Career | 60% | 40% | Career needs objective judgment |
| Education | 50% | 50% | Learning style + academic potential |

### Analysis Type System

Registered in `analysis_catalog.py`. Active: `natal_blueprint`, `phase_navigation`, `monthly_lunar_return`. Paused (timing system being redesigned): `annual_profection`, `secondary_progression`, `synastry`.

### OHLC Scoring

Life phases scored as financial candlesticks:
- **Open**: 0.6 × dignity + 0.4 × house_power
- **High**: support_resources + benefic aspects + positive dignity
- **Low**: load_pressure + malefic aspects + negative dignity
- **Close**: theme_coherence + reception + net support

### Geocoding

Provider chain: AMap (if key set) → Nominatim global → Nominatim CN → maps.co. AMap GCJ-02 coordinates are converted back to WGS84.

## Agent Memory Management

所有 subagent 必须遵循的内存读写规范：

### 1. Spawn 时自动读取相关 memory
- Agent 启动时，先读取 `memory/MEMORY.md` 获取索引
- 根据任务类型读取相关 memory 文件（如 product-positioning.md、main-page-architecture.md 等）
- 将 relevant memory 内容注入 prompt 上下文

### 2. 任务完成后自动写入 memory
- 重要决策、产品方向、技术架构变更 → 写入 memory
- 使用 Write 工具，文件放 `memory/` 目录
- 更新 `memory/MEMORY.md` 的索引

### 3. Memory 文件格式
```markdown
---
name: <short-kebab-case-slug>
description: <one-line summary>
metadata:
  type: user | feedback | project | reference
---

<content>

**Why:** <why this matters>
**How to apply:** <how to use this fact>
```

### 4. memory/MEMORY.md 索引格式
```markdown
- [Title](file.md) — hook
```

### 5. Types of memory
- `user` — 用户角色，专业度、偏好
- `feedback` — 用户对工作的反馈
- `project` — 进行中的工作、目标、约束
- `reference` — 外部资源、文档链接

## Key Conventions

- Chinese astrological terminology throughout (庙旺/失势/落陷, 法达, 飞星, etc.)
- PRD (`PRD.md`, v1.0) is the baseline — must be updated for any analysis type, route, API, domain, or rule model change
- **All engine logic must be rule-driven and generalized. No hardcoded branches for specific people.**
- Legacy API: `POST /api/analyze` and `GET /api/report/{id}` forward to new unified endpoints
- Frontend route `/kline` is a legacy alias for `/reports/:id`
- `docs/` contains reference material (case studies, strategy docs, astrology notes) — not production code
- `backend/data/` is in `.gitignore` for new data; existing tracked files remain as samples
- Use comments sparingly — only comment complex code
