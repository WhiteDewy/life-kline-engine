<template>
  <div class="page-my-chart">
    <!-- ═══ Header ═══ -->
    <header class="chart-header">
      <button class="back-btn" @click="goBack">← 返回</button>
      <div class="header-info">
        <h1 class="header-title">我的星盘</h1>
        <p class="header-sub" v-if="profileName">{{ profileName }} · {{ sunSignLabel || '加载中...' }}</p>
      </div>
      <button class="edit-btn" @click="goEdit">编辑档案</button>
    </header>

    <!-- ═══ 加载 / 错误 ═══ -->
    <div class="loading" v-if="loading">正在加载星盘数据…</div>
    <div class="error" v-else-if="error">{{ error }}</div>

    <!-- ═══ 星盘图 ═══ -->
    <template v-else-if="payload">
      <section class="wheel-section">
        <NatalWheel
          :planets="natalChart.planets || {}"
          :houses="natalChart.houses || []"
          :ascendant="natalChart.ascendant"
          :aspects="natalChart.major_aspects || []"
        />
      </section>

      <!-- ═══ 四 Tab ═══ -->
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
          <div v-if="activeTab === 'state'" class="tab-pane">
            <h2 class="pane-title">黄道状态</h2>
            <p class="pane-desc">10 大星体落在黄道十二宫的庙旺、擢升、失势、落陷状态，及其影响解读。</p>
            <ZodiacStateTable :planets="natalChart.planets || {}" />
          </div>

          <div v-else-if="activeTab === 'aspects'" class="tab-pane">
            <h2 class="pane-title">相位列表</h2>
            <p class="pane-desc">星体之间的角度关系，决定能量的流动方式（柔和 / 挑战 / 中性）。</p>
            <AspectsTable :aspects="natalChart.major_aspects || []" />
          </div>

          <div v-else-if="activeTab === 'receptions'" class="tab-pane">
            <h2 class="pane-title">互溶与接纳</h2>
            <p class="pane-desc">星体落入对方守护的星座，形成相互借力或单向托举的关系。</p>
            <ReceptionsTable :receptions="payload.receptions || []" />
          </div>

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
import { useRouter } from "vue-router";
import { useAuth } from "@/utils/auth";
import { apiClient } from "@/config/api";
import NatalWheel from "@/views/NatalChart/components/NatalWheel.vue";
import ZodiacStateTable from "@/views/NatalChart/components/ZodiacStateTable.vue";
import AspectsTable from "@/views/NatalChart/components/AspectsTable.vue";
import ReceptionsTable from "@/views/NatalChart/components/ReceptionsTable.vue";
import FirdariaTable from "@/views/NatalChart/components/FirdariaTable.vue";

const router = useRouter();
const { profiles } = useAuth();

const loading = ref(true);
const error = ref<string | null>(null);
const payload = ref<any>(null);

const profileName = computed(() => profiles.value?.[0]?.name || "");
const sunSignLabel = computed(() => {
  const planets = payload.value?.natal_chart?.planets || {};
  return planets["SUN"]?.sign_label || "";
});

const tabs = [
  { key: "state", label: "黄道状态" },
  { key: "aspects", label: "相位列表" },
  { key: "receptions", label: "互溶接纳" },
  { key: "firdaria", label: "法达周期" },
];

const activeTab = ref<string>("state");

const natalChart = computed(() => payload.value?.natal_chart || {});

async function fetchData() {
  try {
    loading.value = true;
    error.value = null;
    const res = await apiClient.get("/users/chart");
    if (res.data?.status === "success" && res.data?.data) {
      payload.value = res.data.data;
    } else {
      error.value = "返回数据格式异常";
    }
  } catch (e: any) {
    if (e?.response?.status === 404) {
      error.value = "请先创建出生档案";
    } else {
      error.value = e?.response?.data?.detail || e?.message || "加载星盘数据失败";
    }
  } finally {
    loading.value = false;
  }
}

function goBack() {
  router.back();
}

function goEdit() {
  router.push("/profile");
}

onMounted(fetchData);
</script>

<style scoped lang="less">
.page-my-chart {
  max-width: 960px;
  margin: 0 auto;
  padding: 24px 16px 80px;
  font-family: -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif;
}

/* ── Header ── */
.chart-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 0 20px;
}

.back-btn {
  background: rgba(212, 175, 55, 0.12);
  border: 1px solid rgba(212, 175, 55, 0.3);
  color: #d4af37;
  padding: 6px 14px;
  border-radius: 999px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-family: inherit;
  white-space: nowrap;
}
.back-btn:hover {
  background: rgba(212, 175, 55, 0.22);
}

.header-info {
  flex: 1;
  min-width: 0;
}

.header-title {
  margin: 0;
  font-size: 22px;
  color: #1a1f35;
  letter-spacing: 0.04em;
  font-weight: 700;
}

.header-sub {
  margin: 4px 0 0;
  color: var(--text-tertiary);
  font-size: 13px;
}

.edit-btn {
  padding: 8px 18px;
  border-radius: 999px;
  border: 1px solid rgba(0, 0, 0, 0.1);
  background: var(--bg-card);
  color: var(--text-primary);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  font-family: inherit;
  transition: all 0.2s;
  white-space: nowrap;
}
.edit-btn:hover {
  background: #f8f8f8;
  border-color: rgba(0, 0, 0, 0.18);
}

/* ── Loading / Error ── */
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

/* ── Wheel ── */
.wheel-section {
  margin: 0 0 24px;
}

/* ── Tabs ── */
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
  font-family: inherit;
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
  .chart-header {
    flex-wrap: wrap;
  }
  .header-title {
    font-size: 18px;
  }
  .back-btn,
  .edit-btn {
    font-size: 12px;
    padding: 5px 12px;
  }
}
</style>
