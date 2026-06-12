<template>
  <section class="sectionCard">
    <div class="sectionHead">
      <div>
        <div class="eyebrow">Life Rhythm</div>
        <h2 class="title">人生阶段曲线</h2>
        <p class="hint">
          把人生拆成一个个阶段来看。你可以更直观地看到，什么时候适合推进，什么时候更适合沉淀、调整或重组。
        </p>
      </div>
      <div class="legend">
        <span class="legendItem">
          <i class="dot rise"></i>
          扩张
        </span>
        <span class="legendItem">
          <i class="dot flat"></i>
          平稳
        </span>
        <span class="legendItem">
          <i class="dot fall"></i>
          收缩
        </span>
      </div>
    </div>

    <div class="chartWrap">
      <div ref="chartEl" class="chart"></div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import * as echarts from "echarts";
import type { DomainPoint, KPoint, KlinePeriod, LifeReport } from "@/utils/types";

interface ChartPoint extends KPoint {
  rawPeriod?: KlinePeriod;
}

const props = defineProps<{
  report: LifeReport | null;
}>();

const emit = defineEmits<{
  (e: "structure-updated", payload: DomainPoint[]): void;
}>();

const chartEl = ref<HTMLDivElement | null>(null);
let chart: echarts.ECharts | null = null;

const COLOR_SCORE = "#D4AF37";
const COLOR_UP = "#10B981";
const COLOR_DOWN = "#F97316";
const COLOR_GRID = "rgba(255,255,255,0.06)";
const PLANET_LABELS: Record<string, string> = {
  SUN: "太阳",
  MOON: "月亮",
  MERCURY: "水星",
  VENUS: "金星",
  MARS: "火星",
  JUPITER: "木星",
  SATURN: "土星",
  NORTH_NODE: "北交点",
  SOUTH_NODE: "南交点",
};

const dataset = computed(() => transformReport(props.report));

watch(
  dataset,
  (value) => {
    emit("structure-updated", value.domainPoints);
    render();
  },
  { deep: true, immediate: true }
);

function clamp(n: number, min = 0, max = 100) {
  return Math.max(min, Math.min(max, n));
}

function mapPlanet(value: string) {
  return PLANET_LABELS[value] || value;
}

function transformReport(report: LifeReport | null): {
  lifePoints: ChartPoint[];
  domainPoints: DomainPoint[];
} {
  const periods = report?.kline_data?.periods ?? [];
  if (!periods.length) {
    return { lifePoints: [], domainPoints: [] };
  }

  const startAge = Math.floor(periods[0]!.timing.start_age);
  const endAge = Math.ceil(periods[periods.length - 1]!.timing.end_age);
  const lifePoints: ChartPoint[] = [];
  const domainPoints: DomainPoint[] = [];

  const getScoreAt = (age: number) => {
    const period = periods.find((item) => age >= item.timing.start_age && age < item.timing.end_age);
    return period ? 50 + period.trend.bonus_coefficient * 40 : 50;
  };

  for (let age = startAge; age < endAge; age++) {
    const windowStart = age;
    const windowEnd = age + 1;
    const overlapping = periods.filter(
      (item) => item.timing.start_age < windowEnd && item.timing.end_age > windowStart
    );
    if (!overlapping.length) continue;

    let totalWeight = 0;
    let weightedScore = 0;
    let maxScore = -Infinity;
    let minScore = Infinity;
    let dominantPeriod = overlapping[0]!;
    let dominantWeight = -1;

    for (const period of overlapping) {
      const overlapStart = Math.max(period.timing.start_age, windowStart);
      const overlapEnd = Math.min(period.timing.end_age, windowEnd);
      const weight = Math.max(0, overlapEnd - overlapStart);
      const score = 50 + period.trend.bonus_coefficient * 40;
      if (weight <= 0) continue;

      totalWeight += weight;
      weightedScore += score * weight;
      maxScore = Math.max(maxScore, score);
      minScore = Math.min(minScore, score);

      if (weight > dominantWeight) {
        dominantWeight = weight;
        dominantPeriod = period;
      }
    }

    const open = clamp(getScoreAt(windowStart));
    const close = clamp(getScoreAt(windowEnd - 0.0001));
    const average = clamp(totalWeight > 0 ? weightedScore / totalWeight : 50);
    const high = clamp(Math.max(open, close, maxScore) + 4.5);
    const low = clamp(Math.min(open, close, minScore) - 4.5);

    lifePoints.push({
      x: `${age}岁`,
      open: Number(open.toFixed(1)),
      close: Number(close.toFixed(1)),
      high: Number(high.toFixed(1)),
      low: Number(low.toFixed(1)),
      score: Number(average.toFixed(1)),
      title: dominantPeriod.title,
      summary: dominantPeriod.summary,
      themes: dominantPeriod.themes,
      opportunities: dominantPeriod.opportunities,
      cautions: dominantPeriod.cautions,
      action_focus: dominantPeriod.action_focus,
      rawPeriod: dominantPeriod,
      astrology: {
        sign: dominantPeriod.astrology.sign,
        sign_label: dominantPeriod.astrology.sign_label,
        house: dominantPeriod.astrology.house,
        house_title: dominantPeriod.astrology.house_title,
        dignity: dominantPeriod.astrology.dignity,
        dignity_label: dominantPeriod.astrology.dignity_label,
        major: dominantPeriod.lords.major,
        sub: dominantPeriod.lords.sub ?? "",
        major_score: dominantPeriod.astrology.major_score,
        sub_score: dominantPeriod.astrology.sub_score,
        aspect_signature: dominantPeriod.astrology.aspect_signature,
        dominant_trend: dominantPeriod.trend.type,
      },
    });

    domainPoints.push({
      x: `${age}岁`,
      scores: {
        overall: Number(average.toFixed(1)),
        career: dominantPeriod.domains.career,
        wealth: dominantPeriod.domains.wealth,
        relationship: dominantPeriod.domains.relationship,
        health: dominantPeriod.domains.health,
        family: dominantPeriod.domains.family,
      },
    });
  }

  return { lifePoints, domainPoints };
}

const option = computed(() => {
  const points = dataset.value.lifePoints;
  if (!points.length) return {};

  return {
    backgroundColor: "transparent",
    animationDuration: 500,
    grid: {
      left: "4%",
      right: "4%",
      top: 28,
      bottom: 60,
      containLabel: true,
    },
    tooltip: {
      trigger: "axis",
      axisPointer: { type: "cross" },
      backgroundColor: "rgba(2, 6, 23, 0.96)",
      borderColor: "rgba(255,255,255,0.1)",
      textStyle: { color: "#F8FAFC" },
      extraCssText:
        "box-shadow: 0 20px 40px rgba(0,0,0,.45); border-radius: 16px; max-width: 360px;",
      formatter: (params: any) => {
        const item = points[params?.[0]?.dataIndex ?? 0];
        if (!item) return "";
        const astro = item.astrology;
        const themeHtml = (item.themes ?? [])
          .slice(0, 3)
          .map(
            (theme) =>
              `<span style="display:inline-block;margin:4px 6px 0 0;padding:3px 8px;border-radius:999px;background:rgba(212,175,55,.12);color:#F8FAFC;font-size:11px;">${theme}</span>`
          )
          .join("");
        const aspectHtml = (astro?.aspect_signature ?? [])
          .slice(0, 2)
          .map((line) => `<div style="margin-top:4px;color:#CBD5E1;">${line}</div>`)
          .join("");

        const houseText = astro?.house_title ?? `第${astro?.house ?? "-"}宫`;
        const majorText = astro?.major ? mapPlanet(astro.major) : "-";
        const subText = astro?.sub ? mapPlanet(astro.sub) : "无";

        return `
          <div style="line-height:1.55;">
            <div style="display:flex;justify-content:space-between;gap:12px;align-items:flex-start;">
              <div>
                <div style="font-size:12px;color:#94A3B8;">${item.x}</div>
                <div style="font-size:15px;font-weight:700;margin-top:2px;">${item.title ?? "阶段"}</div>
              </div>
              <div style="font-size:20px;font-weight:800;color:${COLOR_SCORE};">${item.score}</div>
            </div>
            <div style="margin-top:8px;color:#CBD5E1;">${item.summary ?? ""}</div>
            <div style="margin-top:8px;font-size:12px;color:#94A3B8;">
              主运：${majorText} / 子运：${subText}<br/>
              落点：${astro?.sign_label ?? astro?.sign ?? "-"} / ${houseText}<br/>
              先天状态：${astro?.dignity_label ?? astro?.dignity ?? "-"}
            </div>
            ${themeHtml ? `<div style="margin-top:8px;">${themeHtml}</div>` : ""}
            ${aspectHtml ? `<div style="margin-top:8px;font-size:12px;">${aspectHtml}</div>` : ""}
          </div>
        `;
      },
    },
    xAxis: {
      type: "category",
      data: points.map((item) => item.x),
      boundaryGap: false,
      axisLine: { lineStyle: { color: "rgba(255,255,255,0.12)" } },
      axisLabel: { color: "#94A3B8", fontSize: 11 },
      axisTick: { show: false },
      splitLine: { show: false },
    },
    yAxis: {
      type: "value",
      min: 0,
      max: 100,
      splitNumber: 5,
      axisLabel: { color: "#94A3B8", fontSize: 11 },
      axisLine: { show: false },
      splitLine: { lineStyle: { color: COLOR_GRID, type: "dashed" } },
    },
    dataZoom: [
      {
        type: "inside",
        start: 0,
        end: 100,
      },
      {
        type: "slider",
        show: true,
        bottom: 14,
        height: 18,
        borderColor: "rgba(255,255,255,0.08)",
        backgroundColor: "rgba(255,255,255,0.02)",
        fillerColor: "rgba(212,175,55,0.16)",
        handleStyle: { color: COLOR_SCORE },
        textStyle: { color: "#94A3B8" },
      },
    ],
    series: [
      {
        type: "candlestick",
        data: points.map((item) => [item.open, item.close, item.low, item.high]),
        itemStyle: {
          color: COLOR_UP,
          color0: COLOR_DOWN,
          borderColor: COLOR_UP,
          borderColor0: COLOR_DOWN,
        },
        barWidth: "62%",
      },
      {
        name: "阶段分数",
        type: "line",
        data: points.map((item) => item.score),
        smooth: 0.32,
        showSymbol: false,
        lineStyle: {
          width: 2.5,
          color: COLOR_SCORE,
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: "rgba(212,175,55,0.28)" },
            { offset: 1, color: "rgba(212,175,55,0.02)" },
          ]),
        },
      },
    ],
  };
});

function render() {
  if (!chart) return;
  chart.setOption(option.value, true);
}

function resize() {
  chart?.resize();
}

onMounted(() => {
  if (!chartEl.value) return;
  chart = echarts.init(chartEl.value);
  render();
  window.addEventListener("resize", resize);
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", resize);
  chart?.dispose();
  chart = null;
});
</script>

<style scoped>
.sectionCard {
  border: 1px solid rgba(255, 255, 255, 0.08);
  background:
    radial-gradient(circle at top left, rgba(212, 175, 55, 0.08), transparent 34%),
    rgba(15, 23, 42, 0.72);
  border-radius: 24px;
  padding: 24px;
  backdrop-filter: blur(18px);
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.24);
}

.sectionHead {
  display: flex;
  justify-content: space-between;
  gap: 24px;
  align-items: flex-start;
  margin-bottom: 20px;
}

.eyebrow {
  font-size: 12px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--gold);
  margin-bottom: 8px;
}

.title {
  margin: 0;
  font-size: 30px;
  font-weight: 700;
  color: var(--text);
  letter-spacing: -0.03em;
}

.hint {
  max-width: 640px;
  margin: 10px 0 0;
  color: var(--text-secondary);
  line-height: 1.7;
}

.legend {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.legendItem {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 999px;
  color: var(--text-secondary);
  font-size: 12px;
  background: rgba(255, 255, 255, 0.03);
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
}

.dot.rise {
  background: #10b981;
}

.dot.flat {
  background: #94a3b8;
}

.dot.fall {
  background: #f97316;
}

.chartWrap {
  height: 560px;
}

.chart {
  width: 100%;
  height: 100%;
}

@media (max-width: 900px) {
  .sectionHead {
    flex-direction: column;
  }

  .chartWrap {
    height: 460px;
  }
}
</style>
