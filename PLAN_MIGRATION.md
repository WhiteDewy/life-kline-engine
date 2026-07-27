# ACI Monorepo Migration Plan

## 迁移目标

将 src/life_kline/ 重构为 ACI (Astrological Counseling Intelligence) monorepo 架构。

**当前版本**: v0.3.3 (过渡层已部分定义，但 packages/ 目录不存在)
**目标架构**: packages/ + apps/web/ + src/life_kline/ (向后兼容垫片)

---

## 现状分析

### 严重问题

1. **packages/ 目录不存在** - 迁移尚未开始
2. **domains/ 文件夹为空** - composer.py 等文件引用 PersonalAnalyzer, FinanceAnalyzer 等类，但这些文件不存在
3. **domains/helpers.py 不存在** - chart_structure.py, consultation_engine.py, engine_astrologer.py 都引用它
4. **interpretation/ 文件夹几乎为空** - 只有 __init__.py，缺少 planet_rules.py, sign_rules.py, house_rules.py 等
5. **src/life_kline/__init__.py 已定义 packages/ 导入** - 但 packages/ 不存在，会导致 ImportError

---

## 目标架构详细映射

### packages/engine/ — 占星计算核心

packages/engine/src/
- __init__.py
- _constants.py (从 constants.py 拆分)
- models.py (ChartData, PlanetInfo, Aspect 等数据类)
- ephemeris.py, dignities.py, houses.py, aspects.py, receptions.py
- flystar_catalog.py, flight_fortune.py
- firdaria.py, transit_engine.py, today_engine.py
- scoring.py, features.py, chart_structure.py, garden_catalog.py

### packages/akg/ — 占星知识图谱

packages/akg/src/
- __init__.py
- core/nodes.py (ThemeNode, ChartEvidence)
- ontology/theme_catalog.py (12个核心Theme定义)
- relation/semantic_mapper.py, relation/intent_router.py
- classical/dignity_rules.py, classical/house_meanings.py, classical/flystar_rules.py
- modern/aspect_rules.py, modern/planet_personality.py
- repository/interpretation/ (planet_rules.py, sign_rules.py, house_rules.py, aspect_rules.py)
- repository/narrative_engine.py
- recognition/recognizer.py, recognition/analyzer.py

### packages/reasoning/ — 推理引擎

packages/reasoning/src/
- __init__.py
- theme_recognizer.py (ThemeRecognizer)
- evidence_collector.py, evidence_ranker.py
- narrative_builder.py, interpreter.py
- timing/detector.py, timing/firdaria_engine.py, timing/transit_analyzer.py, timing/lunar_return.py

### packages/counseling/ — 咨询技术

packages/counseling/src/
- __init__.py, base.py
- reflection.py, act.py, ifs.py, cbt.py, mi.py

### packages/companion/ — 陪伴系统

packages/companion/src/
- __init__.py, base.py, spirit_registry.py (22位星灵注册表)
- planet_companions/ (10行星灵), sign_companions/ (12星座灵)

### packages/memory/ — 记忆系统

packages/memory/src/
- __init__.py, story.py, timeline.py, growth.py, theme_state.py

### packages/sdk/ — 开发SDK

packages/sdk/src/
- __init__.py, chart_sdk.py, consultation_sdk.py, client.py

---

## 迁移顺序

### Phase 1: 创建缺失的基础文件 (CRITICAL)

必须创建：
- src/life_kline/constants.py (Planet, Sign, AspectType 枚举, DOMICILE_SIGNS, EXALTATION_SIGNS等)
- src/life_kline/models.py (ChartData, PlanetInfo, Aspect, PlanetFeature, NodeScoreResult)

### Phase 2: 创建缺失的 domains/ 文件 (CRITICAL - 当前为空)

必须创建：
- src/life_kline/domains/helpers.py - plabel(), slabel(), house_title(), dlabel()等
- src/life_kline/domains/base.py - DomainAnalyzer 基类
- 12个 DomainAnalyzer 子类: personal.py, finance.py, family.py, romance.py, marriage.py, partnership.py, children.py, work_skill.py, career.py, education.py, appearance.py, health.py

### Phase 3: 创建缺失的 interpretation/ 文件

必须创建：
- planet_rules.py, sign_rules.py, house_rules.py
- aspect_rules.py, flystar_rules.py, narrative_engine.py

### Phase 4: 迁移核心计算模块到 packages/engine/

迁移：ephemeris.py, dignities.py, houses.py, aspects.py, receptions.py, features.py, scoring.py, firdaria.py, transit_engine.py, today_engine.py, flystar_catalog.py, flight_fortune.py, chart_structure.py, garden_catalog.py

### Phase 5: 迁移其他模块

- interpretation/ → packages/akg/src/repository/interpretation/
- characters/ → packages/companion/src/
- council/ → packages/reasoning/src/
- growth/ → packages/memory/src/
- awakening/ → packages/counseling/src/

### Phase 6: 创建向后兼容垫片

更新 src/life_kline/__init__.py 和所有重导出文件。

---

## 依赖链分析

Level 0: constants.py, models.py, garden_catalog.py, analysis_catalog.py
Level 1: ephemeris.py, dignities.py, aspects.py, receptions.py, firdaria.py
Level 2: houses.py, features.py, scoring.py, transit_engine.py, flystar_catalog.py, flight_fortune.py
Level 3: chart_structure.py, today_engine.py
Level 4: engine_astrologer.py, consultation_engine.py, composer.py
Level 5: consultation.py, pricing.py, safety.py

---

## 循环依赖风险

### 已识别的循环依赖

1. dignities.py ↔ receptions.py - 已在函数内动态导入缓解
2. dignities.py ↔ aspects.py - 已在函数内动态导入缓解

---

## 迁移检查清单

### Phase 1: 基础修复
- [ ] 创建 src/life_kline/constants.py
- [ ] 创建 src/life_kline/models.py
- [ ] 验证 import life_kline 不报错

### Phase 2: 创建 domains/
- [ ] 创建 src/life_kline/domains/helpers.py
- [ ] 创建 src/life_kline/domains/base.py
- [ ] 创建 12 个 DomainAnalyzer 子类

### Phase 3: 创建 interpretation/
- [ ] 创建 src/life_kline/interpretation/*.py

### Phase 4: 创建 packages/ 骨架
- [ ] 创建 packages/engine/src/, packages/akg/src/, packages/reasoning/src/
- [ ] 创建 packages/counseling/src/, packages/companion/src/, packages/memory/src/, packages/sdk/src/

### Phase 5-7: 迁移文件、向后兼容、测试

---

*Plan version: 1.0*
*Created: 2026-07-27*
