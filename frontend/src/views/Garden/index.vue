<template>
  <div class="garden-page" :data-theme="currentTheme">
    <!-- 背景 -->
    <div class="garden-bg">
      <GardenScene :transparent="true" />
    </div>

    <!-- ═══ 加载态 ═══ -->
    <section v-if="garden.loading.value" class="garden-state">
      <div class="state-icon">🌸</div>
      <h2 class="state-title">星灵花园正在打开...</h2>
      <p class="state-sub">正在准备你的分析工具</p>
    </section>

    <!-- ═══ 错误态 ═══ -->
    <section v-else-if="garden.error.value" class="garden-state">
      <div class="state-icon">🪐</div>
      <h2 class="state-title">花园暂时打不开</h2>
      <p class="state-sub">{{ garden.error.value }}</p>
      <el-button round size="large" class="retry-btn" @click="initGarden">重新尝试</el-button>
    </section>

    <!-- ═══ 主内容 ═══ -->
    <div v-else class="garden-content">
      <!-- 签到条 -->
      <CheckInBar
        v-if="!viewState.consulting && !viewState.report"
        :checked-in="garden.checkinStatus.value.checked_in"
        :streak-count="garden.checkinStatus.value.streak_count"
        @checkin="garden.doCheckin()"
      />

      <!-- 顶部操作栏 -->
      <div class="garden-top-bar">
        <ThemeSwitcher :current="currentTheme" @select="(k: string) => currentTheme = k" />
        <button class="history-btn" @click="showHistory = true">📜 历史报告</button>
      </div>

      <!-- ═══ 运势区 ═══ -->
      <FortuneSection v-if="!viewState.consulting && !viewState.report" :items="garden.fortuneItems.value" />

      <!-- ═══ 分类网格 ═══ -->
      <template v-if="!viewState.category">
        <h2 class="section-heading">🔍 选择你想探索的领域</h2>
        <CategoryGrid
          :categories="garden.categories.value"
          @select-category="onSelectCategory"
        />
      </template>

      <!-- ═══ 分类详情：问题列表 ═══ -->
      <template v-if="viewState.category && !viewState.consulting">
        <QuestionList
          :category="viewState.category"
          :selected-key="garden.selectedQuestion.value"
          @back="garden.clearCategory()"
          @select-question="onSelectQuestion"
        />
      </template>

      <!-- ═══ 咨询流程 ═══ -->
      <template v-if="viewState.consulting && garden.consultationState.value">
        <ConsultationFlow
          :state="garden.consultationState.value"
          @back="onBackFromConsultation"
          @send-response="onSendResponse"
          @generate-report="onGenerateReport"
        />
      </template>

      <!-- ═══ 报告展示 ═══ -->
      <template v-if="viewState.report && garden.consultationReport.value">
        <ReportDisplay
          :report="garden.consultationReport.value"
          @close="garden.clearCategory()"
          @save="onSaveReport"
        />
      </template>

      <!-- ═══ 日记入口 ═══ -->
      <div class="diary-entry" v-if="activeReportId && !viewState.consulting && !viewState.report">
        <GardenJournal
          :planet-profiles="null"
          :active-report-id="activeReportId"
        />
      </div>
    </div>

    <!-- ═══ 历史报告浮层 ═══ -->
    <transition name="overlay-fade">
      <div v-if="showHistory" class="overlay-backdrop" @click.self="showHistory = false">
        <div class="overlay-panel">
          <ReportHistoryPage
            :reports="garden.reports.value"
            :categories="garden.categories.value"
            :loading="garden.reportsLoading.value"
            :active-filter="historyFilter"
            @view-report="onViewHistoryReport"
            @close="showHistory = false"
            @update:activeFilter="historyFilter = $event"
          />
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch } from "vue";
import { apiClient } from "@/config/api";
import { useRoute } from "vue-router";
import { useGarden } from "@/composables/useGarden";
import GardenScene from "@/components/garden/GardenScene.vue";
import ThemeSwitcher from "@/components/garden/ThemeSwitcher.vue";
import GardenJournal from "@/components/garden/GardenJournal.vue";
import CheckInBar from "./components/CheckInBar.vue";
import CategoryGrid from "./components/CategoryGrid.vue";
import FortuneSection from "./components/FortuneSection.vue";
import QuestionList from "./components/QuestionList.vue";
import ConsultationFlow from "./components/ConsultationFlow.vue";
import ReportDisplay from "./components/ReportDisplay.vue";
import ReportHistoryPage from "./components/ReportHistoryPage.vue";
import type { GardenCategory } from "@/utils/types";

const route = useRoute();
const garden = useGarden();

const currentTheme = ref(localStorage.getItem("spirit_garden_theme") || "cream");
const showHistory = ref(false);
const historyFilter = ref("");
const activeReportId = ref("");
const savedScrollY = ref(0);

interface ViewState {
  category: GardenCategory | null;
  consulting: boolean;
  report: boolean;
}
const viewState = reactive<ViewState>({
  category: null,
  consulting: false,
  report: false,
});

async function initGarden() {
  let rid = (route.params.id || route.query.id) as string | undefined;

  // 如果没有 reportId，尝试从用户 profile 生成
  if (!rid) {
    try {
      const { profiles } = (await apiClient.get("/me")).data as any;
      if (profiles?.length > 0) {
        const p = profiles[0];
        const res = await apiClient.post("/analyses", {
          analysis_type: "natal_blueprint",
          subjects: [{
            name: p.name || "",
            gender: p.gender || "",
            birth_time: p.birth_time,
            lat: p.lat,
            lon: p.lon,
            timezone: p.timezone,
          }],
        });
        if (res.data?.status === "success") {
          rid = res.data.report_id;
        }
      }
    } catch (e) {
      console.warn("Failed to auto-create report:", e);
    }
  }

  if (rid) activeReportId.value = rid;
  await garden.init(rid);
}

function onSelectCategory(cat: GardenCategory) {
  garden.selectCategory(cat);
  viewState.category = cat;
  viewState.consulting = false;
  viewState.report = false;
}

function onSelectQuestion(questionKey: string) {
  savedScrollY.value = window.scrollY;
  garden.selectQuestion(questionKey);
  viewState.consulting = true;
  viewState.report = false;

  const rid = activeReportId.value || route.query.id as string || "";
  if (viewState.category && rid) {
    garden.startConsultation(rid, viewState.category.key, questionKey);
  }
}

async function onSendResponse(text: string) {
  const rid = activeReportId.value || "";
  const state = garden.consultationState.value;
  if (!state || !rid) return;
  await garden.continueConsultation(rid, state.session_id, text);
}

async function onGenerateReport() {
  const rid = activeReportId.value || "";
  const state = garden.consultationState.value;
  if (!state || !rid) return;
  await garden.generateReport(rid, state.session_id);
  viewState.consulting = false;
  viewState.report = true;
}

function onBackFromConsultation() {
  viewState.consulting = false;
  viewState.report = false;
  garden.consultationState.value = null;
  garden.consultationReport.value = null;
  setTimeout(() => window.scrollTo({ top: savedScrollY.value, behavior: "instant" }), 50);
}

function onSaveReport() {
  garden.clearCategory();
  viewState.category = null;
  viewState.consulting = false;
  viewState.report = false;
  setTimeout(() => window.scrollTo({ top: savedScrollY.value, behavior: "instant" }), 50);
}

async function onViewHistoryReport(reportId: string) {
  await garden.loadReportDetail(reportId);
  viewState.report = true;
  viewState.category = garden.categories.value.find(
    (c) => c.key === garden.consultationReport.value?.category,
  ) || null;
  showHistory.value = false;
}

// 查看历史时加载
watch(showHistory, (v) => {
  if (v) garden.loadReports(historyFilter.value || undefined);
});
watch(historyFilter, (f) => {
  garden.loadReports(f || undefined);
});

onMounted(() => initGarden());
</script>

<style scoped lang="less">
.garden-page {
  min-height: 100vh;
  position: relative;
  overflow-x: hidden;
}
.garden-bg {
  position: fixed; inset: 0; z-index: 0;
}
.garden-page[data-theme="cream"] { --garden-bg-1: #FFF5EE; --garden-accent: #FF9A8B; }
.garden-page[data-theme="night"] { --garden-bg-1: #1a1a2e; --garden-accent: #9B8EC4; }
.garden-page[data-theme="sakura"] { --garden-bg-1: #FFF0F5; --garden-accent: #F4A7B9; }

/* 加载/错误 */
.garden-state { position: relative; z-index: 1; text-align: center; padding: 120px 20px; }
.state-icon { font-size: 52px; margin-bottom: 16px; animation: float 3s ease-in-out infinite; }
@keyframes float { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-10px)} }
.state-title { font-size: 22px; font-weight: 700; color: var(--text-primary); margin: 0 0 8px; }
.state-sub { font-size: 14px; color: var(--text-secondary); margin: 0 0 24px; }
.retry-btn { background: rgba(255,154,139,0.2) !important; border-color: rgba(255,154,139,0.3) !important; color: #4a3728 !important; }

/* 内容区 */
.garden-content {
  position: relative;
  z-index: 1;
  max-width: 680px;
  margin: 0 auto;
  padding: 24px 20px 100px;
  display: flex;
  flex-direction: column;
  gap: 28px;
}

.garden-top-bar {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 10px;
}
.history-btn {
  padding: 6px 14px; border-radius: 14px;
  border: 1px solid var(--border-light);
  background: var(--bg-card-glass);
  font-size: 12px; font-weight: 600; color: var(--text-secondary);
  cursor: pointer; font-family: inherit; transition: all 0.2s;
  min-height: 44px;
}
.history-btn:hover { background: rgba(255,255,255,0.8); color: var(--text-primary); }

.section-heading {
  font-size: 18px; font-weight: 700; color: var(--text-primary); margin: 0;
}

.diary-entry {
  margin-top: 16px;
  padding-top: 24px;
  border-top: 1px solid rgba(0,0,0,0.06);
}

/* 历史浮层 */
.overlay-backdrop {
  position: fixed; inset: 0; z-index: 200;
  background: rgba(0,0,0,0.15); backdrop-filter: blur(4px);
}
.overlay-panel {
  position: absolute; right: 0; top: 0; bottom: 0;
  width: 100%; max-width: 420px;
  padding: 24px 20px;
  background: rgba(255,248,240,0.95); backdrop-filter: blur(20px);
  overflow-y: auto;
}
.overlay-fade-enter-active { transition: all 0.25s ease; }
.overlay-fade-leave-active { transition: all 0.2s ease; }
.overlay-fade-enter-from, .overlay-fade-leave-to { opacity: 0; }
.overlay-fade-enter-from .overlay-panel { transform: translateX(40px); }

@media (max-width: 640px) {
  .garden-content { padding: 16px 14px 100px; }
  .overlay-panel { max-width: 100%; }
}
</style>
