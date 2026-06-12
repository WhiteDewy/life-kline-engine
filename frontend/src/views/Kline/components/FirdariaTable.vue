<template>
  <section class="card">
    <div class="head">
      <div>
        <div class="eyebrow">Phase Timeline</div>
        <h3 class="title">阶段时间表</h3>
      </div>
      <p class="hint">
        按主运与子运查看人生阶段切换，快速判断什么时候更适合推进，什么时候更适合收束与调整。
      </p>
    </div>

    <div class="tableWrap">
      <table class="table">
        <thead>
          <tr>
            <th>年龄段</th>
            <th>主运 / 子运</th>
            <th>星座 / 宫位</th>
            <th>趋势</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="period in periods" :key="period.index">
            <td>
              <div class="age">
                {{ Math.floor(period.timing.start_age) }} - {{ Math.floor(period.timing.end_age) }} 岁
              </div>
              <div class="date">
                {{ formatDate(period.timing.start_date) }} - {{ formatDate(period.timing.end_date) }}
              </div>
            </td>
            <td>
              <div class="lords">
                <span class="major">{{ mapPlanet(period.lords.major) }}</span>
                <span class="divider">/</span>
                <span class="sub">{{ period.lords.sub ? mapPlanet(period.lords.sub) : "无子运" }}</span>
              </div>
            </td>
            <td>
              <div class="location">
                {{ period.astrology.sign_label || period.astrology.sign }}
                /
                {{ period.astrology.house_title || `第${period.astrology.house}宫` }}
              </div>
              <div class="status">{{ period.astrology.dignity_label || period.astrology.dignity }}</div>
            </td>
            <td>
              <span class="trend" :class="period.trend.type">
                {{ trendLabel(period.trend.type) }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>

<script setup lang="ts">
import type { KlinePeriod } from "@/utils/types";

defineProps<{
  periods: KlinePeriod[];
}>();

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

function mapPlanet(value: string) {
  return PLANET_LABELS[value] || value;
}

function formatDate(value: string) {
  return value?.split("T")[0] ?? "";
}

function trendLabel(value: string) {
  if (value === "bull") return "扩张";
  if (value === "bear") return "收缩";
  return "平稳";
}
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
  margin-bottom: 16px;
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
  max-width: 520px;
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.7;
}

.tableWrap {
  overflow-x: auto;
}

.table {
  width: 100%;
  border-collapse: collapse;
}

.table th,
.table td {
  padding: 14px 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  text-align: left;
  vertical-align: top;
}

.table th {
  color: var(--text-secondary);
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.table td {
  color: var(--text);
  font-size: 14px;
}

.table tbody tr:hover {
  background: rgba(255, 255, 255, 0.03);
}

.age {
  font-weight: 700;
}

.date,
.status {
  color: var(--text-secondary);
  font-size: 12px;
  margin-top: 4px;
}

.lords {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}

.major {
  color: var(--gold);
}

.divider,
.sub {
  color: var(--text-secondary);
}

.location {
  line-height: 1.6;
}

.trend {
  display: inline-flex;
  align-items: center;
  padding: 5px 10px;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  font-size: 12px;
}

.trend.bull {
  color: #10b981;
  background: rgba(16, 185, 129, 0.1);
}

.trend.bear {
  color: #f97316;
  background: rgba(249, 115, 22, 0.1);
}

.trend.stable {
  color: #94a3b8;
  background: rgba(148, 163, 184, 0.1);
}

@media (max-width: 900px) {
  .head {
    flex-direction: column;
  }
}
</style>
