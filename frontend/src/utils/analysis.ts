import type { AnalysisDefinition } from "./types";

export const FALLBACK_ANALYSIS_TYPES: AnalysisDefinition[] = [
  {
    key: "natal_blueprint",
    title: "本命蓝图",
    tagline: "直接回答你是谁、适合做什么、学业事业财富感情会怎么展开。",
    description:
      "从星体、星座、宫位、相位与互溶接纳出发，把复杂盘面翻译成用户最关心的六个问题，再补充底层结构和占星证据。",
    category: "structure",
    status: "active",
    subjects_count: 1,
    required_inputs: ["birth_time", "lat", "lon", "timezone"],
    engines: ["natal_core"],
    modules: ["我是谁", "适合做什么", "学业", "事业", "财富", "感情", "本命星盘", "底层依据"],
    primary_cta: "进入体验",
    output_route: "/reports/:id",
  },
  {
    key: "phase_navigation",
    title: "阶段导航",
    tagline: "帮你看清此刻正处于哪一段，以及现在最值得推进什么。",
    description:
      "从本命结构与法达阶段出发，识别你当下的人生主题、机会窗口、风险点和更适合你的行动方式。",
    category: "timing",
    status: "active",
    subjects_count: 1,
    required_inputs: ["birth_time", "lat", "lon", "timezone"],
    engines: ["natal_core", "firdaria"],
    modules: ["阶段总览", "本命星盘", "本命蓝图", "高级规则", "样例校验", "当前阶段", "人生主轴", "人生曲线", "领域投射", "阶段时间表"],
    primary_cta: "开始解读",
    output_route: "/reports/:id",
  },
  {
    key: "monthly_lunar_return",
    title: "月返盘",
    tagline: "看当前月返周期里，哪些合月亮窗口正在被点亮。",
    description:
      "计算当前月返时刻与月返盘，列出本月所有行星合月亮前后 3° 的时间区间，并展开显示区间内每天的相位度数。",
    category: "timing",
    status: "active",
    subjects_count: 1,
    required_inputs: ["birth_time", "lat", "lon", "timezone"],
    engines: ["natal_core", "lunar_return"],
    modules: ["月返盘", "月返周期", "合月亮窗口", "每日相位度数"],
    primary_cta: "进入月返",
    output_route: "/monthly-return/:id",
  },
  {
    key: "annual_profection",
    title: "年度节奏",
    tagline: "把每一年龄年的主轴、方向与课题提炼出来。",
    description:
      "通过年度主星与主题宫位，帮助你判断这一年最值得把精力放在哪些领域。",
    category: "timing",
    status: "planned",
    subjects_count: 1,
    required_inputs: ["birth_time", "lat", "lon", "timezone"],
    engines: ["natal_core", "profection"],
    modules: ["年度主题", "年度主星", "重点领域"],
    primary_cta: "即将上线",
    output_route: "/reports/:id",
  },
  {
    key: "secondary_progression",
    title: "内在演化",
    tagline: "看见你的内在心理节奏，理解自己为什么正在悄悄变化。",
    description:
      "从次限月亮、次限太阳与重要次限相位出发，解释心理成熟、情绪变化与生命阶段的内在演化。",
    category: "timing",
    status: "planned",
    subjects_count: 1,
    required_inputs: ["birth_time", "lat", "lon", "timezone"],
    engines: ["natal_core", "secondary_progression"],
    modules: ["内在节奏", "关键变化", "阶段提醒"],
    primary_cta: "即将上线",
    output_route: "/reports/:id",
  },
  {
    key: "synastry",
    title: "关系合盘",
    tagline: "分析两个人为什么会靠近、摩擦，以及这段关系如何成长。",
    description:
      "从吸引机制、冲突模式、关系边界与长期协同出发，帮助你理解一段关系真正的运行方式。",
    category: "relationship",
    status: "planned",
    subjects_count: 2,
    required_inputs: ["birth_time", "lat", "lon", "timezone"],
    engines: ["natal_core", "synastry"],
    modules: ["关系总览", "吸引点", "摩擦点", "成长建议"],
    primary_cta: "即将上线",
    output_route: "/reports/:id",
  },
];

export const ANALYSIS_CATEGORY_LABELS: Record<string, string> = {
  structure: "认识自己",
  timing: "阶段判断",
  relationship: "关系互动",
  topic: "专题解读",
};

export function getAnalysisByKey(key?: string) {
  return FALLBACK_ANALYSIS_TYPES.find((item) => item.key === key) ?? null;
}
