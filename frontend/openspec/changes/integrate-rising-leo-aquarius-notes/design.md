# Design: integrate-rising-leo-aquarius-notes

## Overview

这次变更不触碰后端引擎，重点是把现有笔记整理成前端可消费的内容模型，并挂到两个已经存在的内容入口：

1. 方法论入口
2. 报告页入口

目标不是“把笔记贴出来”，而是把它变成：

- 用户可读的结构化专题
- 占星师可复用的解释模板
- 后续可扩展的新内容基座

## Content Model

建议新增独立配置文件，而不是继续挤进 `methodology.ts`。

### Proposed files

- `frontend/src/config/teachingNotes.ts`
- 可选拆分：
  - `frontend/src/config/teachingNotes/relationshipPrimer.ts`
  - `frontend/src/config/teachingNotes/risingSignNotes.ts`

### Proposed shape

```ts
interface RelationshipPrimer {
  key: string;
  title: string;
  summary: string;
  points: string[];
  astrologerNotes?: string[];
}

interface RisingPlanetLens {
  key: string;
  title: string;
  summary: string;
  userPoints: string[];
  astrologerNotes?: string[];
}

interface RisingSignGuide {
  sign: "LEO" | "AQUARIUS";
  title: string;
  oneLiner: string;
  socialMask: string;
  growthTask: string;
  relationshipCaution: string;
  healthOrBodyCaution?: string;
  lenses: RisingPlanetLens[];
  tags: string[];
}
```

### Why this shape

- `summary / userPoints` 负责用户可读层。
- `astrologerNotes` 负责专业提醒层。
- `lenses` 可以按“太阳、月亮、土星、金星、火星、水星与木星”拆解，避免一大段 prose 难维护。
- `sign` 明确绑定上升星座，后续新增其他上升时不需要改组件结构。

## UI Integration

### 1. Homepage methodology section

文件：

- `frontend/src/views/home/components/main.vue`

变更方式：

- 在现有 `Methodology` 区下方增加一个新的默认折叠专题区。
- 专题区先展示：
  - “别人先看到上升，熟悉后看到太阳，亲近后看到月亮”
  - “关系舒适度优先看月亮”
- 展开后展示：
  - 上升狮子卡
  - 上升水瓶卡

这里的定位是“产品如何看人”，不是完整报告，所以内容应更短、更像导览。

### 2. ReadingMethodPanel

文件：

- `frontend/src/views/Kline/components/ReadingMethodPanel.vue`

变更方式：

- 在现有 `Methodology` 折叠区内新增 `专题笔记` 子区块。
- 子区块按两层展示：
  - 通用认知卡：上升 / 太阳 / 月亮层级，月亮在关系中的优先级
  - 上升专题卡：狮子 / 水瓶

这样能让报告页用户先理解“阅读逻辑”，再进入自己的具体星盘。

### 3. Report-level ascendant spotlight

建议落点：

- `frontend/src/views/Kline/components/NatalBlueprintPanel.vue`
  - 或新建 `AscendantSpotlightPanel.vue` 后挂在 `index.vue`

原因：

- 这是“本命蓝图的现实翻译”，比放在纯技术性的 `NatalChartPanel` 更合适。
- 组件需要读取 `natalChart.ascendant.sign`，并在命中 `LEO` 或 `AQUARIUS` 时显示专题卡。

卡片内容建议固定四段：

1. 社会化外显
2. 人生补课课题
3. 关系与情绪提醒
4. 资源 / 行动 / 事业倾向

专业内容不要默认铺开，可用折叠或次级段落承载。

## Content Translation Rules

原始笔记里有不少强判断和咨询现场口语，需要在产品里做两层翻译：

### User-facing

- 语言要保留方向感，但避免绝对化断言。
- 例如：
  - “容易被背刺” -> “在情绪依赖或隐性关系里更容易受伤”
  - “伴侣地位不如自己” -> “关系中容易形成一方更承担琐事或服务性角色”

### Astrologer-facing

- 保留判断来源与技术关键词。
- 例如：
  - “月亮受克时，舒适度问题优先级高于太阳一致性”
  - “上升水瓶的命主星土星若与 12 宫强关联，需要强调自我怀疑与边界课题”

## Risks

### 1. Raw note overload

如果直接照抄原始笔记，页面会重新变成“信息很多但无从下手”。

应对：

- 用户层只保留短摘要与 3-4 条关键点
- 专业层默认折叠

### 2. Scope drift into synastry

“月亮受克”很容易把需求带进合盘模块。

应对：

- 本次只做“关系阅读原则”提示
- 不做双人计算、不做相位自动判定

### 3. Hardcoded sign logic in components

如果组件里直接 `if ascendant === "LEO"` 写死文案，后续会很难扩展。

应对：

- 所有专题内容走配置
- 组件只负责“选择专题并渲染”

## Rollout Notes

推荐实施顺序：

1. 先建内容配置文件
2. 先接 `ReadingMethodPanel`
3. 再接首页方法论区
4. 最后补报告页上升专题聚焦卡

这样即使只完成前两步，也已经有稳定的内容入口，不会浪费整理工作。
