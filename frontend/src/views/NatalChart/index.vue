<template>
  <div class="page-natal-chart">
    <header class="hero">
      <button class="back-btn" @click="goBack">← 返回报告</button>
      <h1 class="hero-title">本命星盘</h1>
      <p class="hero-sub">查看你的 10 大星体落座、相位、接纳与互溶，以及 100 年法达周期。</p>
    </header>

    <div class="loading" v-if="loading">正在加载本命盘数据…</div>
    <div class="error" v-else-if="error">{{ error }}</div>

    <template v-else-if="payload">
      <!-- 上方：星盘图 -->
      <section class="wheel-section">
        <NatalWheel
          :planets="natalChart.planets || {}"
          :houses="natalChart.houses || []"
          :ascendant="natalChart.ascendant"
          :aspects="natalChart.major_aspects || []"
        />
      </section>

      <!-- 下方：四 Tab -->
      <section class="tabs-section">
        <nav class="tabs-nav">
          <button
            v-for="tab in tabs"
            :key="tab.key"
            :class="['tab-btn', { active: activeTab === tab.key }]"
            @click="activeTab = tab.key"
          >
            {{ tab.label }}
          </button>
        </nav>

        <div class="tabs-content">
          <!-- 状态 -->
          <div v-if="activeTab === 'state'" class="tab-pane">
            <h2 class="pane-title">黄道状态</h2>
            <p class="pane-desc">10 大星体落在黄道十二宫的庙旺、擢升、失势、落陷状态，及其影响解读。</p>
            <ZodiacStateTable :planets="natalChart.planets || {}" />
          </div>

          <!-- 相位 -->
          <div v-else-if="activeTab === 'aspects'" class="tab-pane">
            <h2 class="pane-title">相位列表</h2>
            <p class="pane-desc">星体之间的角度关系，决定能量的流动方式（柔和 / 挑战 / 中性）。</p>
            <AspectsTable :aspects="natalChart.major_aspects || []" />
          </div>

          <!-- 接纳 -->
          <div v-else-if="activeTab === 'receptions'" class="tab-pane">
            <h2 class="pane-title">互溶与接纳</h2>
            <p class="pane-desc">星体落入对方守护的星座，形成相互借力或单向托举的关系。</p>
            <ReceptionsTable :receptions="payload.receptions || []" />
          </div>

          <!-- 法达 -->
          <div v-else-if="activeTab === 'firdaria'" class="tab-pane">
            <h2 class="pane-title">100 年法达周期</h2>
            <p class="pane-desc">Firdaria（法达星限）：按主运→子运顺序划分人生主题周期。</p>
            <FirdariaTable
              :periods="payload.firdaria_periods || []"
              :current-age="payload.current_age || 0"
              :is-day-chart="payload.is_day_chart !== false"
            />
          </div>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { apiClient } from "@/config/api";
import type { NatalChartResponse } from "@/utils/natalChartTypes";
import NatalWheel from "./components/NatalWheel.vue";
import ZodiacStateTable from "./components/ZodiacStateTable.vue";
import AspectsTable from "./components/AspectsTable.vue";
import ReceptionsTable from "./components/ReceptionsTable.vue";
import FirdariaTable from "./components/FirdariaTable.vue";

const route = useRoute();
const router = useRouter();

const loading = ref(true);
const error = ref<string | null>(null);
const payload = ref<NatalChartResponse["data"] | null>(null);

const reportId = computed(() => String(route.params.reportId || ""));

const tabs = [
  { key: "state", label: "黄道状态" },
  { key: "aspects", label: "相位列表" },
  { key: "receptions", label: "互溶接纳" },
  { key: "firdaria", label: "法达周期" },
];

const activeTab = ref<string>("state");

const natalChart = computed(() => payload.value?.natal_chart || {});

async function fetchData() {
  if (!reportId.value) {
    error.value = "缺少报告 ID";
    loading.value = false;
    return;
  }
  try {
    loading.value = true;
    error.value = null;
    const res = await apiClient.get<NatalChartResponse>(`/natal-chart/${reportId.value}`);
    if (res.data?.status === "success" && res.data?.data) {
      payload.value = res.data.data;
    } else {
      error.value = "返回数据格式异常";
    }
  } catch (e: any) {
    error.value = e?.response?.data?.detail || e?.message || "加载本命盘数据失败";
  } finally {
    loading.value = false;
  }
}

function goBack() {
  router.push(`/reports/${reportId.value}`);
}

onMounted(fetchData);
</script>

<style scoped lang="less">
.page-natal-chart {
  max-width: 960px;
  margin: 0 auto;
  padding: 24px 16px 80px;
  font-family: -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif;
}

.hero {
  text-align: center;
  padding: 24px 16px 16px;
  position: relative;
}

.back-btn {
  position: absolute;
  left: 0;
  top: 24px;
  background: rgba(212, 175, 55, 0.12);
  border: 1px solid rgba(212, 175, 55, 0.3);
  color: #d4af37;
  padding: 6px 14px;
  border-radius: 999px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.back-btn:hover {
  background: rgba(212, 175, 55, 0.22);
}

.hero-title {
  margin: 8px 0 4px;
  font-size: 28px;
  color: #1a1f35;
  letter-spacing: 0.04em;
  font-weight: 700;
}

.hero-sub {
  margin: 0;
  color: var(--text-tertiary);
  font-size: 14px;
  line-height: 1.6;
}

.loading,
.error {
  text-align: center;
  padding: 60px 16px;
  color: var(--text-tertiary);
  font-size: 15px;
}

.error {
  color: #b91c1c;
}

.wheel-section {
  margin: 16px 0 24px;
}

.tabs-section {
  background: var(--bg-card);
  border-radius: 14px;
  border: 1px solid #e2e8f0;
  overflow: hidden;
}

.tabs-nav {
  display: flex;
  border-bottom: 1px solid #e2e8f0;
  background: #f8fafc;
  overflow-x: auto;
}

.tab-btn {
  flex: 1 1 auto;
  padding: 14px 16px;
  border: none;
  background: transparent;
  color: var(--text-tertiary);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.tab-btn:hover {
  color: #1e293b;
}

.tab-btn.active {
  color: #d4af37;
  border-bottom-color: #d4af37;
  background: var(--bg-card);
}

.tabs-content {
  padding: 24px 20px;
}

.pane-title {
  margin: 0 0 4px;
  font-size: 18px;
  color: #1a1f35;
  font-weight: 700;
}

.pane-desc {
  margin: 0 0 16px;
  color: var(--text-tertiary);
  font-size: 13px;
  line-height: 1.6;
}

@media (max-width: 640px) {
  .hero-title {
    font-size: 22px;
  }
  .back-btn {
    position: static;
    margin-bottom: 8px;
  }
}
</style>