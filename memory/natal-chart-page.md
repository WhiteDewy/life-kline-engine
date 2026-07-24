---
name: natal-chart-page
description: 本命盘页面 /natal-chart/:reportId 的实现要点
metadata:
  type: feature
---

# 本命盘页面 (2026-07-23)

## 路由
- 前端：`/natal-chart/:reportId`（已注册到 `frontend/src/router/index.ts`）
- 鉴权：需要登录 token（meta.requiresAuth = true）
- 页面：`frontend/src/views/NatalChart/index.vue`

## 后端契约
新增端点：`GET /api/natal-chart/{report_id}`

返回 `data` 字段：
```ts
{
  natal_chart: { ascendant, houses, planets, major_aspects, dominant_planets, ... }
  firdaria_periods: [{ start_age, end_age, lord, lord_zh, sub_lord, sub_lord_zh, is_node }]
  receptions: [{ from, from_zh, to, to_zh, type: 'reception'|'mutual_reception', type_zh, description }]
  is_day_chart: boolean
  current_age: number
}
```

依赖：`life_kline.firdaria.calculate_firdaria_periods`、`life_kline.service.planet_label`、
`advanced_patterns.reception_groups` + `mutual_receptions`。

## 前端组件结构
```
frontend/src/views/NatalChart/
├── index.vue              # 主页面，上方星盘 + 下方 Tab
└── components/
    ├── NatalWheel.vue     # 深色背景 + 金色符号，可切换相位线
    ├── ZodiacStateTable.vue   # 10 大星体状态 (庙旺/擢升/失势/落陷/弱势)
    ├── AspectsTable.vue       # 相位列表 (柔和/挑战/中性)
    ├── ReceptionsTable.vue    # 互溶/接纳
    └── FirdariaTable.vue      # 100 年法达周期，高亮当前
```

类型定义：`frontend/src/utils/natalChartTypes.ts`

## 设计要点
- 主色调：深色背景（#0a0e1a）+ 金色符号（#d4af37），对标宫神星网
- 表格：浅色背景 + 深色表头，保持阅读舒适
- Tab 切换：状态 / 相位 / 接纳 / 法达
- 法达表：当前周期金色高亮，子运顺序用「土木火日金水月」标签，当前子运特殊标记

**Why:** 用户可在一个页面查看完整本命盘数据 + 100 年时间轴
**How to apply:** 修改页面时同步更新 `natalChartTypes.ts`；后端契约变更需同步调整 5 个组件