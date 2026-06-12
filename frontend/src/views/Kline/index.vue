<template>
  <div class="page">
    <div class="halo halo-a"></div>
    <div class="halo halo-b"></div>

    <div class="wrap">
      <section class="hero" v-if="report">
        <div class="heroMain">
          <div class="eyebrow">{{ analysis?.title || "人生阶段报告" }}</div>
          <h1 class="heroTitle">{{ lifeModel?.title || analysis?.title || "占星人生" }}</h1>
          <p class="heroSummary">
            {{
              lifeModel?.summary ||
              natalChart?.signature ||
              analysis?.description ||
              "我们正在为你整理本命结构、阶段节奏与关键提醒。"
            }}
          </p>

          <div class="heroChips">
            <span class="chip">
              上升 {{ natalChart?.ascendant?.sign_label || natalChart?.ascendant?.sign || "-" }}
            </span>
            <span class="chip">
              命主星 {{ natalChart?.chart_ruler_label || natalChart?.chart_ruler || "-" }}
            </span>
            <span class="chip">
              {{ natalChart?.sect_label || (report.user_info.is_day_chart ? "日盘" : "夜盘") }}
            </span>
            <span class="chip">报告版本 {{ report.meta.engine_version }}</span>
          </div>
        </div>

        <div class="heroAside" v-if="currentPhase">
          <div class="scoreLabel">当前阶段</div>
          <div class="scoreValue">{{ currentPhase.score }}</div>
          <div class="scoreRange">{{ currentPhase.age_range }}</div>
          <p class="scoreSummary">{{ currentPhase.summary || currentPhase.feeling }}</p>
          <div class="keywordRow">
            <span v-for="keyword in currentPhase.keywords || []" :key="keyword" class="keyword">
              {{ keyword }}
            </span>
          </div>
        </div>

        <div class="heroAside" v-else-if="timelineValidation?.events?.length">
          <div class="scoreLabel">历史样例</div>
          <div class="historyTitle">{{ timelineValidation.title || "人生节点校验" }}</div>
          <div class="scoreRange">{{ timelineValidation.events.length }} 个关键节点</div>
          <p class="scoreSummary">{{ timelineValidation.summary }}</p>
          <div class="keywordRow">
            <span
              v-for="item in timelineValidation.events.slice(0, 3)"
              :key="`${item.date_label}-${item.title}`"
              class="keyword"
            >
              {{ item.date_label }} · {{ item.title }}
            </span>
          </div>
        </div>
      </section>

      <section v-if="loading" class="stateCard">
        <div class="stateTitle">正在生成你的占星报告</div>
        <p class="stateText">正在整理你的本命结构、阶段节奏与人生重点，请稍候。</p>
      </section>

      <section v-else-if="error" class="stateCard errorCard">
        <div class="stateTitle">报告加载失败</div>
        <p class="stateText">{{ error }}</p>
      </section>

      <template v-else-if="report">
        <section class="metricGrid">
          <article class="metricCard">
            <div class="metricLabel">太阳 / 月亮</div>
            <div class="metricValue">
              {{ natalChart?.planets?.SUN?.sign_label || natalChart?.planets?.SUN?.sign || "-" }}
              /
              {{ natalChart?.planets?.MOON?.sign_label || natalChart?.planets?.MOON?.sign || "-" }}
            </div>
            <div class="metricHint">你的驱动力与情绪底色</div>
          </article>

          <article class="metricCard">
            <div class="metricLabel">当前主运</div>
            <div class="metricValue">
              {{ phaseLeadText }}
              <span class="metricSub" v-if="phaseSubText">/ {{ phaseSubText }}</span>
            </div>
            <div class="metricHint">
              {{ currentPhase ? "这段时间最明显的人生主题" : "历史样例以人生节点校验替代实时阶段" }}
            </div>
          </article>

          <article class="metricCard">
            <div class="metricLabel">核心人生领域</div>
            <div class="metricValue">{{ natalChart?.house_emphasis?.[0]?.title || "-" }}</div>
            <div class="metricHint">这里最容易成为你长期投入的重心</div>
          </article>

          <article class="metricCard">
            <div class="metricLabel">当前趋势</div>
            <div class="metricValue">{{ trendLabel(currentPhase?.trend_type) }}</div>
            <div class="metricHint">{{ currentPhase?.description || "当前阶段的整体走向" }}</div>
          </article>
        </section>

        <NatalChartPanel :natal-chart="natalChart" />
        <NatalBlueprintPanel :blueprint="natalBlueprint" />
        <AdvancedPatternsPanel :advanced-patterns="advancedPatterns" />
        <CaseThemesPanel :advanced-patterns="advancedPatterns" />
        <TimelineValidationPanel :timeline="timelineValidation" />

        <section class="insightGrid">
          <article class="panel panelWide">
            <div class="panelEyebrow">Core Model</div>
            <h2 class="panelTitle">你的人生主轴</h2>
            <p class="panelSummary">{{ lifeModel?.summary || natalChart?.signature || "-" }}</p>
            <div class="tagGrid">
              <span v-for="theme in lifeModel?.core_themes || []" :key="theme" class="tag">
                {{ theme }}
              </span>
            </div>
          </article>

          <article class="panel">
            <div class="panelEyebrow">Strengths</div>
            <h2 class="panelTitle">你更容易发挥的优势</h2>
            <ul class="list">
              <li v-for="item in lifeModel?.strengths || []" :key="item">{{ item }}</li>
            </ul>
          </article>

          <article class="panel">
            <div class="panelEyebrow">Challenges</div>
            <h2 class="panelTitle">容易反复遇到的课题</h2>
            <ul class="list">
              <li v-for="item in lifeModel?.challenges || []" :key="item">{{ item }}</li>
            </ul>
          </article>
        </section>

        <section class="insightGrid secondary">
          <article class="panel">
            <div class="panelEyebrow">Dominant Planets</div>
            <h2 class="panelTitle">主导星体</h2>
            <div class="stack">
              <div
                v-for="item in natalChart?.dominant_planets || []"
                :key="item.planet"
                class="stackItem"
              >
                <div class="stackTop">
                  <strong>{{ item.label }}</strong>
                  <span>{{ item.score }}</span>
                </div>
                <p>{{ item.reason }}</p>
              </div>
            </div>
          </article>

          <article class="panel">
            <div class="panelEyebrow">House Focus</div>
            <h2 class="panelTitle">重点宫位</h2>
            <div class="stack">
              <div
                v-for="item in natalChart?.house_emphasis || []"
                :key="item.house"
                class="stackItem"
              >
                <div class="stackTop">
                  <strong>第{{ item.house }}宫 / {{ item.title }}</strong>
                  <span>{{ item.weight }}</span>
                </div>
                <p>{{ (item.keywords || []).join(" / ") }}</p>
              </div>
            </div>
          </article>

          <article class="panel">
            <div class="panelEyebrow">Aspect Field</div>
            <h2 class="panelTitle">关键相位</h2>
            <div class="stack">
              <div
                v-for="item in natalChart?.major_aspects || []"
                :key="item.title"
                class="stackItem"
              >
                <div class="stackTop">
                  <strong>{{ item.title }}</strong>
                  <span>{{ item.strength }}</span>
                </div>
                <p>{{ item.summary }}</p>
              </div>
            </div>
          </article>
        </section>

        <section class="phaseBoard" v-if="currentPhase">
          <article class="phaseHero">
            <div class="panelEyebrow">Current Phase</div>
            <h2 class="panelTitle">你现在正走到人生的哪一段</h2>
            <p class="panelSummary">{{ currentPhase.summary || currentPhase.feeling }}</p>

            <div class="phaseMeta">
              <span>{{ currentPhase.age_range }}</span>
              <span>
                {{ currentPhase.start_date?.slice(0, 10) }} - {{ currentPhase.end_date?.slice(0, 10) }}
              </span>
              <span>{{ currentPhase.description }}</span>
            </div>

            <div class="phaseDomains">
              <div
                v-for="domain in currentPhase.dominant_domains || []"
                :key="domain.key"
                class="phaseDomain"
              >
                <div class="domainName">{{ domain.label }}</div>
                <div class="domainScore">{{ domain.score }}</div>
              </div>
            </div>
          </article>

          <article class="panel">
            <div class="panelEyebrow">Opportunities</div>
            <h2 class="panelTitle">适合顺势推进的方向</h2>
            <ul class="list">
              <li v-for="item in currentPhase.opportunities || []" :key="item">{{ item }}</li>
            </ul>
          </article>

          <article class="panel">
            <div class="panelEyebrow">Cautions</div>
            <h2 class="panelTitle">当前最需要留意的地方</h2>
            <ul class="list">
              <li v-for="item in currentPhase.cautions || []" :key="item">{{ item }}</li>
            </ul>
          </article>

          <article class="panel">
            <div class="panelEyebrow">Action Focus</div>
            <h2 class="panelTitle">更适合你的行动方式</h2>
            <ul class="list">
              <li v-for="item in currentPhase.action_focus || []" :key="item">{{ item }}</li>
            </ul>
          </article>
        </section>

        <section class="timelineGrid">
          <article class="panel">
            <div class="panelEyebrow">Peak Windows</div>
            <h2 class="panelTitle">更容易发力的阶段</h2>
            <div class="stack">
              <div
                v-for="item in lifeModel?.peak_windows || []"
                :key="`${item.age_range}-${item.lords}`"
                class="stackItem"
              >
                <div class="stackTop">
                  <strong>{{ item.age_range }}</strong>
                  <span>{{ item.lords }}</span>
                </div>
                <p>{{ item.summary }}</p>
              </div>
            </div>
          </article>

          <article class="panel">
            <div class="panelEyebrow">Reset Windows</div>
            <h2 class="panelTitle">适合调整与重建的阶段</h2>
            <div class="stack">
              <div
                v-for="item in lifeModel?.reset_windows || []"
                :key="`${item.age_range}-${item.lords}`"
                class="stackItem"
              >
                <div class="stackTop">
                  <strong>{{ item.age_range }}</strong>
                  <span>{{ item.lords }}</span>
                </div>
                <p>{{ item.summary }}</p>
              </div>
            </div>
          </article>

          <article class="panel">
            <div class="panelEyebrow">Growth Path</div>
            <h2 class="panelTitle">长期走法</h2>
            <ul class="list">
              <li v-for="item in lifeModel?.growth_path || []" :key="item">{{ item }}</li>
            </ul>
            <div class="divider"></div>
            <ul class="list">
              <li v-for="item in lifeModel?.strategy || []" :key="item">{{ item }}</li>
            </ul>
          </article>
        </section>

        <LifeStructureChart :report="report" @structure-updated="onStructureUpdated" />
        <LifeDomainsChart :domain-data="domainData" />
        <FirdariaTable :periods="report.kline_data.periods" />
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useRoute } from "vue-router";
import { apiClient } from "@/config/api";
import { FEATURED_NATAL_EXAMPLE } from "@/config/examples";
import { getAnalysisByKey } from "@/utils/analysis";
import type { AnalysisDefinition, AnalysisResponse, DomainPoint, LifeReport } from "@/utils/types";
import AdvancedPatternsPanel from "./components/AdvancedPatternsPanel.vue";
import FirdariaTable from "./components/FirdariaTable.vue";
import LifeDomainsChart from "./components/LifeDomainsChart.vue";
import LifeStructureChart from "./components/LifeStructureChart.vue";
import CaseThemesPanel from "./components/CaseThemesPanel.vue";
import NatalChartPanel from "./components/NatalChartPanel.vue";
import NatalBlueprintPanel from "./components/NatalBlueprintPanel.vue";
import TimelineValidationPanel from "./components/TimelineValidationPanel.vue";

const route = useRoute();

const loading = ref(true);
const error = ref("");
const report = ref<LifeReport | null>(null);
const analysis = ref<AnalysisDefinition | null>(getAnalysisByKey("phase_navigation"));
const domainData = ref<DomainPoint[]>([]);

const natalChart = computed(() => report.value?.natal_chart ?? null);
const currentPhase = computed(() => report.value?.current_phase ?? null);
const lifeModel = computed(() => report.value?.life_model ?? null);
const natalBlueprint = computed(() => report.value?.natal_blueprint ?? null);
const advancedPatterns = computed(() => report.value?.advanced_patterns ?? null);
const timelineValidation = computed(() => report.value?.timeline_validation ?? null);
const phaseLeadText = computed(() => {
  if (currentPhase.value) return mapPlanet(currentPhase.value.major_lord) || "-";
  if (timelineValidation.value?.events?.length) return "历史样例";
  return "-";
});
const phaseSubText = computed(() => {
  if (!currentPhase.value) return "";
  return mapPlanet(currentPhase.value.sub_lord) || "无子运";
});

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

function mapPlanet(value?: string) {
  if (!value) return "";
  return PLANET_LABELS[value] || value;
}

function trendLabel(value?: string) {
  if (value === "bull") return "扩张";
  if (value === "bear") return "收缩";
  if (value === "stable") return "平稳";
  return "-";
}

function onStructureUpdated(payload: DomainPoint[]) {
  domainData.value = payload ?? [];
}

function currentReportId() {
  const routeParam = route.params.id;
  if (typeof routeParam === "string" && routeParam) return routeParam;
  const queryId = route.query.id;
  return typeof queryId === "string" && queryId ? queryId : undefined;
}

function currentExampleKey() {
  const example = route.query.example;
  return typeof example === "string" && example ? example : undefined;
}

function buildExampleRequest(exampleKey: string) {
  if (exampleKey !== FEATURED_NATAL_EXAMPLE.key) {
    return null;
  }

  return {
    analysis_type: "phase_navigation",
    subjects: [
      {
        name: FEATURED_NATAL_EXAMPLE.name,
        birth_time: FEATURED_NATAL_EXAMPLE.birthTime,
        lat: FEATURED_NATAL_EXAMPLE.latitude,
        lon: FEATURED_NATAL_EXAMPLE.longitude,
        timezone: FEATURED_NATAL_EXAMPLE.timezone,
      },
    ],
  };
}

async function loadReport() {
  loading.value = true;
  error.value = "";

  try {
    const reportId = currentReportId();
    const exampleKey = currentExampleKey();

    if (reportId) {
      const response = await apiClient.get<AnalysisResponse<LifeReport>>(`/analyses/${reportId}`);
      if (response.data?.status === "success") {
        report.value = response.data.data;
        analysis.value = response.data.analysis || getAnalysisByKey("phase_navigation");
        return;
      }
    }

    if (exampleKey) {
      const payload = buildExampleRequest(exampleKey);
      if (payload) {
        const exampleResponse = await apiClient.post<AnalysisResponse<LifeReport>>("/analyses", payload);
        if (exampleResponse.data?.status === "success") {
          report.value = exampleResponse.data.data;
          analysis.value = exampleResponse.data.analysis || getAnalysisByKey("phase_navigation");
          return;
        }
      }
    }

    const fallback = await apiClient.post<AnalysisResponse<LifeReport>>("/analyses", {
      analysis_type: "phase_navigation",
      subjects: [
        {
          birth_time: "1991-03-21T12:00:00",
          lat: 39.9042,
          lon: 116.4074,
          timezone: 8.0,
        },
      ],
    });

    if (fallback.data?.status === "success") {
      report.value = fallback.data.data;
      analysis.value = fallback.data.analysis || getAnalysisByKey("phase_navigation");
      return;
    }

    error.value = "服务返回了不可用的报告结构。";
  } catch (err) {
    console.error(err);
    error.value = "无法加载占星报告，请检查后端服务与报告 ID。";
  } finally {
    loading.value = false;
  }
}

watch(
  () => [route.params.id, route.query.id, route.query.example],
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
    radial-gradient(circle at 80% 20%, rgba(99, 102, 241, 0.14), transparent 22%),
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
  background: rgba(99, 102, 241, 0.18);
}

.wrap {
  position: relative;
  z-index: 1;
  max-width: 1280px;
  margin: 0 auto;
  padding: 56px 20px 80px;
}

.hero {
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(300px, 0.8fr);
  gap: 24px;
  margin-bottom: 28px;
}

.heroMain,
.heroAside,
.panel,
.metricCard,
.stateCard,
.phaseHero {
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(15, 23, 42, 0.72);
  backdrop-filter: blur(18px);
  border-radius: 24px;
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.24);
}

.heroMain {
  padding: 28px;
}

.heroAside {
  padding: 24px;
  background:
    radial-gradient(circle at top left, rgba(212, 175, 55, 0.12), transparent 30%),
    rgba(15, 23, 42, 0.82);
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
  font-size: 46px;
  line-height: 1.04;
  letter-spacing: -0.04em;
  color: var(--text);
}

.heroSummary {
  max-width: 760px;
  margin: 16px 0 0;
  color: var(--text-secondary);
  line-height: 1.85;
  font-size: 15px;
}

.heroChips,
.keywordRow,
.tagGrid {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.heroChips {
  margin-top: 20px;
}

.chip,
.keyword,
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

.scoreValue {
  margin-top: 10px;
  font-size: 56px;
  line-height: 1;
  font-weight: 800;
  color: var(--gold);
}

.scoreRange {
  margin-top: 8px;
  color: var(--text);
  font-weight: 600;
}

.historyTitle {
  margin-top: 12px;
  color: var(--text);
  font-size: 28px;
  line-height: 1.15;
  font-weight: 700;
}

.scoreSummary {
  margin: 16px 0 0;
  color: var(--text-secondary);
  line-height: 1.8;
}

.keywordRow {
  margin-top: 16px;
}

.stateCard {
  padding: 28px;
}

.errorCard {
  border-color: rgba(244, 63, 94, 0.2);
}

.stateTitle {
  font-size: 22px;
  color: var(--text);
}

.stateText {
  margin: 12px 0 0;
  color: var(--text-secondary);
}

.metricGrid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 18px;
  margin-bottom: 22px;
}

.metricCard {
  padding: 20px;
}

.metricLabel {
  color: var(--text-secondary);
  font-size: 12px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.metricValue {
  margin-top: 10px;
  color: var(--text);
  font-size: 24px;
  font-weight: 700;
  line-height: 1.25;
}

.metricSub {
  color: var(--text-secondary);
  font-size: 16px;
  font-weight: 500;
}

.metricHint {
  margin-top: 10px;
  color: var(--text-secondary);
  line-height: 1.6;
  font-size: 13px;
}

.insightGrid,
.timelineGrid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 18px;
  margin-bottom: 22px;
}

.insightGrid.secondary {
  margin-bottom: 26px;
}

.panel,
.phaseHero {
  padding: 24px;
}

.panelWide {
  grid-column: span 1;
}

.panelTitle {
  margin: 10px 0 0;
  color: var(--text);
  font-size: 26px;
  line-height: 1.2;
}

.panelSummary {
  margin: 14px 0 0;
  color: var(--text-secondary);
  line-height: 1.8;
}

.list {
  margin: 14px 0 0;
  padding: 0;
  list-style: none;
  display: grid;
  gap: 10px;
}

.list li {
  color: var(--text-secondary);
  line-height: 1.7;
  padding-left: 18px;
  position: relative;
}

.list li::before {
  content: "";
  position: absolute;
  left: 0;
  top: 10px;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--gold);
  box-shadow: 0 0 18px rgba(212, 175, 55, 0.35);
}

.stack {
  margin-top: 14px;
  display: grid;
  gap: 12px;
}

.stackItem {
  padding: 14px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.stackTop {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  color: var(--text);
}

.stackItem p {
  margin: 8px 0 0;
  color: var(--text-secondary);
  line-height: 1.7;
}

.phaseBoard {
  display: grid;
  grid-template-columns: minmax(0, 1.25fr) repeat(3, minmax(0, 1fr));
  gap: 18px;
  margin-bottom: 24px;
}

.phaseMeta {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-top: 16px;
}

.phaseMeta span {
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.05);
  color: var(--text-secondary);
  font-size: 12px;
}

.phaseDomains {
  margin-top: 18px;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.phaseDomain {
  padding: 12px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.domainName {
  color: var(--text-secondary);
  font-size: 12px;
}

.domainScore {
  margin-top: 8px;
  color: var(--gold);
  font-size: 28px;
  font-weight: 700;
}

.divider {
  height: 1px;
  margin: 16px 0;
  background: rgba(255, 255, 255, 0.08);
}

@media (max-width: 1100px) {
  .hero,
  .phaseBoard,
  .metricGrid,
  .insightGrid,
  .timelineGrid {
    grid-template-columns: 1fr;
  }

  .heroTitle {
    font-size: 36px;
  }

  .phaseDomains {
    grid-template-columns: 1fr;
  }
}
</style>
