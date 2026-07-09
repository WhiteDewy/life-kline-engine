<template>
  <div class="page">
    <div class="halo halo-a"></div>
    <div class="halo halo-b"></div>

    <div class="wrap">
      <section v-if="report" class="hero">
        <article class="heroMain">
          <div class="eyebrow">Monthly Lunar Return</div>
          <h1 class="heroTitle">{{ report.lunar_return.cycle_label }}</h1>
          <p class="heroSummary">
            本次月返从 {{ formatDateTime(report.lunar_return.cycle_start_local) }} 开始，
            到 {{ formatDateTime(report.lunar_return.cycle_end_local) }} 结束。
            下方列出这个周期里所有与月亮形成主相位前后 3° 的触发窗口。
          </p>
          <div class="heroChips">
            <span class="chip">月返时刻 {{ formatDateTime(report.lunar_return.return_time_local) }}</span>
            <span class="chip">窗口数量 {{ report.lunar_return.moon_windows.length }}</span>
            <span class="chip">{{ report.user_info.timezone }}</span>
            <span class="chip">引擎 {{ report.meta.engine_version }}</span>
          </div>
        </article>

        <article class="heroAside">
          <div class="scoreLabel">月返焦点</div>
          <div class="historyTitle">
            {{ strongestWindow ? formatWindowTitle(strongestWindow) : "本周期暂无 3° 内月亮相位" }}
          </div>
          <div class="scoreRange" v-if="strongestWindow">
            精确触发 {{ formatDateTime(strongestWindow.exact_time_local) }}
          </div>
          <p class="scoreSummary" v-if="strongestWindow">
            最紧的引动容许度为 {{ formatOrb(strongestWindow.exact_orb) }}，窗口覆盖
            {{ strongestWindow.daily_degrees.length }} 天。
          </p>
          <p class="scoreSummary" v-else>
            当前月返周期里，没有星体进入与月亮主相位前后 3° 的范围。
          </p>
        </article>
      </section>

      <section v-if="loading" class="stateCard">
        <div class="stateTitle">正在加载月返盘</div>
        <p class="stateText">正在计算当前月返时刻、月返盘和月亮引动相位，请稍候。</p>
      </section>

      <section v-else-if="error" class="stateCard errorCard">
        <div class="stateTitle">月返盘加载失败</div>
        <p class="stateText">{{ error }}</p>
      </section>

      <template v-else-if="report">
        <NatalChartPanel
          v-if="report.lunar_return.chart"
          :natal-chart="report.lunar_return.chart"
          :advanced-patterns="null"
        />

        <section class="windowSection">
          <article class="panel sectionIntro">
            <div class="panelEyebrow">Moon Aspect Table</div>
            <h2 class="panelTitle">当前月月亮引动的所有相位关系</h2>
            <p class="panelSummary">
              按窗口汇总月亮与各星体的主相位触发，便于直接查看相位类型、精确时刻和影响范围。
            </p>
          </article>

          <article class="panel tablePanel">
            <div class="tableScroll">
              <table class="dataTable">
                <thead>
                  <tr>
                    <th>月亮引动</th>
                    <th>精确相位</th>
                    <th>容许度</th>
                    <th>开始</th>
                    <th>精确时刻</th>
                    <th>结束</th>
                    <th>覆盖天数</th>
                  </tr>
                </thead>
                <tbody v-if="report.lunar_return.moon_windows.length">
                  <tr
                    v-for="window in report.lunar_return.moon_windows"
                    :key="`${window.aspect_key}-${window.planet}-${window.start_time_utc}`"
                  >
                    <td>{{ formatWindowTitle(window) }}</td>
                    <td>{{ formatAspect(window.exact_separation) }} / {{ formatAspect(window.aspect_angle) }}</td>
                    <td>{{ formatOrb(window.exact_orb) }}</td>
                    <td>{{ formatDateTime(window.start_time_local) }}</td>
                    <td>{{ formatDateTime(window.exact_time_local) }}</td>
                    <td>{{ formatDateTime(window.end_time_local) }}</td>
                    <td>{{ window.daily_degrees.length }} 天</td>
                  </tr>
                </tbody>
                <tbody v-else>
                  <tr>
                    <td class="emptyCell" colspan="7">当前月返周期内暂无月亮 3° 容许度内的主相位窗口。</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </article>
        </section>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useRoute } from "vue-router";
import { apiClient } from "@/config/api";
import NatalChartPanel from "@/views/Kline/components/NatalChartPanel.vue";
import type { AnalysisResponse, LunarReturnWindow, MonthlyLunarReturnReport } from "@/utils/types";

const route = useRoute();

const loading = ref(true);
const error = ref("");
const report = ref<MonthlyLunarReturnReport | null>(null);

const strongestWindow = computed(() => {
  const windows = report.value?.lunar_return.moon_windows || [];
  if (!windows.length) return null;
  return [...windows].sort((left, right) => left.exact_orb - right.exact_orb)[0];
});

function currentReportId() {
  const routeParam = route.params.id;
  if (typeof routeParam === "string" && routeParam) return routeParam;
  const queryId = route.query.id;
  return typeof queryId === "string" && queryId ? queryId : undefined;
}

function formatDateTime(value?: string) {
  if (!value) return "-";
  const normalized = value.replace("T", " ");
  return normalized.slice(0, 16);
}

function formatOrb(value?: number) {
  if (typeof value !== "number" || Number.isNaN(value)) return "-";
  return `${value.toFixed(2)}°`;
}

function formatAspect(value?: number) {
  if (typeof value !== "number" || Number.isNaN(value)) return "-";
  return `${value.toFixed(1)}°`;
}

function formatWindowTitle(window: LunarReturnWindow) {
  return `月亮 ${window.aspect_label} ${window.planet_label}`;
}

async function loadReport() {
  loading.value = true;
  error.value = "";
  report.value = null;

  try {
    const reportId = currentReportId();
    if (!reportId) {
      error.value = "缺少月返报告 ID。请从首页重新进入月返入口。";
      return;
    }

    const response = await apiClient.get<AnalysisResponse<MonthlyLunarReturnReport>>(`/analyses/${reportId}`);
    if (response.data?.status === "success") {
      report.value = response.data.data;
      return;
    }

    error.value = "服务返回了不可用的月返报告。";
  } catch (err) {
    console.error(err);
    error.value = "无法加载月返报告，请检查后端服务与报告 ID。";
  } finally {
    loading.value = false;
  }
}

watch(
  () => [route.params.id, route.query.id],
  () => {
    loadReport();
  },
  { immediate: true }
);
</script>

<style scoped>
.page {
  min-height: 100vh;
  position: relative;
  overflow: hidden;
  background:
    radial-gradient(circle at top left, rgba(212, 175, 55, 0.08), transparent 24%),
    radial-gradient(circle at 80% 20%, rgba(56, 189, 248, 0.12), transparent 22%),
    linear-gradient(180deg, #020617 0%, #07111f 100%);
}

.halo {
  position: absolute;
  border-radius: 50%;
  filter: blur(90px);
  opacity: 0.6;
  pointer-events: none;
}

.halo-a {
  width: 320px;
  height: 320px;
  top: 40px;
  left: -60px;
  background: rgba(212, 175, 55, 0.12);
}

.halo-b {
  width: 420px;
  height: 420px;
  right: -120px;
  top: 180px;
  background: rgba(56, 189, 248, 0.16);
}

.wrap {
  position: relative;
  z-index: 1;
  max-width: var(--report-shell-max);
  margin: 0 auto;
  padding: 56px 20px 80px;
}

.hero {
  display: grid;
  grid-template-columns: minmax(0, 1.3fr) minmax(280px, 0.7fr);
  gap: 24px;
  margin-bottom: 24px;
}

.heroMain,
.heroAside,
.panel,
.stateCard {
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(15, 23, 42, 0.72);
  backdrop-filter: blur(18px);
  border-radius: 24px;
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.24);
}

.heroMain,
.heroAside,
.panel,
.stateCard {
  padding: 24px;
}

.eyebrow,
.panelEyebrow,
.scoreLabel {
  font-size: 12px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--gold);
}

.heroTitle {
  margin: 12px 0 0;
  font-size: 42px;
  line-height: 1.06;
  color: var(--text);
}

.heroSummary,
.panelSummary,
.scoreSummary,
.stateText,
.windowExact {
  margin: 14px 0 0;
  color: var(--text-secondary);
  line-height: 1.8;
}

.heroChips,
.windowMeta {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.heroChips {
  margin-top: 18px;
}

.chip,
.tag {
  display: inline-flex;
  align-items: center;
  padding: 7px 12px;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.04);
  color: var(--text-secondary);
  font-size: 12px;
}

.historyTitle {
  margin-top: 10px;
  color: var(--text);
  font-size: 28px;
  line-height: 1.15;
  font-weight: 700;
}

.scoreRange {
  margin-top: 10px;
  color: var(--text);
  font-weight: 600;
}

.stateTitle,
.panelTitle,
.windowTitle {
  color: var(--text);
}

.stateTitle {
  font-size: 22px;
}

.panelTitle {
  margin: 10px 0 0;
  font-size: 28px;
}

.windowSection {
  display: grid;
  gap: 18px;
}

.tablePanel {
  padding-top: 18px;
}

.tableScroll {
  overflow-x: auto;
}

.dataTable {
  width: 100%;
  border-collapse: collapse;
  min-width: 560px;
}

.dataTable th,
.dataTable td {
  padding: 12px 14px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  text-align: left;
}

.dataTable th {
  color: rgba(248, 250, 252, 0.68);
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.dataTable td {
  color: var(--text-secondary);
}

.emptyCell {
  text-align: center;
}

.errorCard {
  border-color: rgba(244, 63, 94, 0.2);
}

@media (max-width: 1100px) {
  .hero {
    grid-template-columns: 1fr;
  }

  .heroTitle {
    font-size: 34px;
  }
}
</style>
