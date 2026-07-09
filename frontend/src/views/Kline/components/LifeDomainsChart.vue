<template>
  <section class="card">
    <div class="head">
      <div>
        <div class="eyebrow">领域分布</div>
        <h3 class="title">人生重点分布</h3>
        <p class="hint">
          把同一阶段拆成事业、财富、关系、健康、家庭五条线，帮助你看清哪一部分最值得你分配精力。
        </p>
      </div>
      <div class="chips">
        <button
          v-for="chip in chips"
          :key="chip.key"
          type="button"
          class="chip"
          :class="{ active: selected.has(chip.key) }"
          @click="toggle(chip.key)"
        >
          <span class="chipDot" :style="{ backgroundColor: DOMAIN_COLORS[chip.key] }"></span>
          {{ chip.label }}
        </button>
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
import type { DomainPoint } from "@/utils/types";

type DomainKey = "career" | "wealth" | "relationship" | "health" | "family";

const props = defineProps<{
  domainData?: DomainPoint[];
}>();

const chartEl = ref<HTMLDivElement | null>(null);
let chart: echarts.ECharts | null = null;

const DOMAIN_COLORS: Record<DomainKey, string> = {
  career: "#D4AF37",
  wealth: "#2AA7B8",
  relationship: "#F97316",
  health: "#10B981",
  family: "#6366F1",
};

const chips: Array<{ key: DomainKey; label: string }> = [
  { key: "career", label: "事业" },
  { key: "wealth", label: "财富" },
  { key: "relationship", label: "关系" },
  { key: "health", label: "健康" },
  { key: "family", label: "家庭" },
];

const selected = ref<Set<DomainKey>>(new Set(chips.map((chip) => chip.key)));
const activeDomainData = computed(() => props.domainData ?? []);

watch(
  activeDomainData,
  () => {
    render();
  },
  { deep: true }
);

function toggle(key: DomainKey) {
  const next = new Set(selected.value);
  if (next.has(key)) {
    next.delete(key);
  } else {
    next.add(key);
  }
  selected.value = next;
  render();
}

const option = computed(() => {
  const domainData = activeDomainData.value;
  const visible = chips.filter((chip) => selected.value.has(chip.key));
  const categories = domainData.map((item) => item.x);

  return {
    backgroundColor: "transparent",
    grid: {
      left: "4%",
      right: "4%",
      top: 20,
      bottom: 46,
      containLabel: true,
    },
    tooltip: {
      trigger: "axis",
      axisPointer: { type: "line" },
      backgroundColor: "rgba(2, 6, 23, 0.96)",
      borderColor: "rgba(255,255,255,0.1)",
      textStyle: { color: "#F8FAFC" },
      formatter: (params: any) => {
        const title = params?.[0]?.axisValue ?? "";
        const rows = (params ?? [])
          .map(
            (item: any) =>
              `<div style="display:flex;justify-content:space-between;gap:18px;margin-top:4px;">
                <span>${item.marker}${item.seriesName}</span>
                <strong>${Number(item.value).toFixed(1)}</strong>
              </div>`
          )
          .join("");
        return `<div><div style="font-weight:700;margin-bottom:6px;">${title}</div>${rows}</div>`;
      },
    },
    legend: {
      show: true,
      top: 0,
      right: 0,
      textStyle: { color: "#94A3B8" },
      data: visible.map((chip) => chip.label),
    },
    xAxis: {
      type: "category",
      boundaryGap: false,
      data: categories,
      axisLine: { lineStyle: { color: "rgba(255,255,255,0.12)" } },
      axisLabel: { color: "#94A3B8", fontSize: 11 },
      axisTick: { show: false },
    },
    yAxis: {
      type: "value",
      min: 0,
      max: 100,
      splitLine: {
        lineStyle: { color: "rgba(255,255,255,0.06)", type: "dashed" },
      },
      axisLabel: { color: "#94A3B8", fontSize: 11 },
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
        bottom: 10,
        height: 16,
        borderColor: "rgba(255,255,255,0.08)",
        backgroundColor: "rgba(255,255,255,0.02)",
        fillerColor: "rgba(99,102,241,0.15)",
        handleStyle: { color: "#6366F1" },
        textStyle: { color: "#94A3B8" },
      },
    ],
    series: visible.map((chip) => ({
      name: chip.label,
      type: "line",
      smooth: 0.25,
      showSymbol: false,
      data: domainData.map((item) => item.scores[chip.key]),
      lineStyle: {
        width: 2.4,
        color: DOMAIN_COLORS[chip.key],
      },
      itemStyle: {
        color: DOMAIN_COLORS[chip.key],
      },
      areaStyle: {
        opacity: 0.04,
        color: DOMAIN_COLORS[chip.key],
      },
    })),
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
.card {
  margin-top: 28px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 24px;
  background: rgba(15, 23, 42, 0.72);
  padding: 24px;
  backdrop-filter: blur(18px);
}

.head {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  align-items: flex-start;
  margin-bottom: 18px;
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
  color: var(--text);
  font-size: 24px;
}

.hint {
  max-width: 620px;
  margin: 10px 0 0;
  color: var(--text-secondary);
  line-height: 1.7;
}

.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: flex-end;
}

.chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.03);
  color: var(--text-secondary);
  cursor: pointer;
}

.chip.active {
  color: var(--text);
  background: rgba(255, 255, 255, 0.08);
}

.chipDot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
}

.chartWrap {
  height: 360px;
}

.chart {
  width: 100%;
  height: 100%;
}

@media (max-width: 900px) {
  .head {
    flex-direction: column;
  }
}
</style>
