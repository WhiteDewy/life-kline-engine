<template>
  <div class="page">
    <div class="halo halo-a"></div>
    <div class="halo halo-b"></div>

    <div class="wrap">
      <section class="hero" v-if="report">
        <div class="heroMain">
          <div class="eyebrow">{{ analysis?.title || "占星人生报告" }}</div>
          <h1 class="heroTitle">{{ heroTitle }}</h1>
          <p class="heroSummary">{{ heroSummary }}</p>

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

        <div class="heroAside" v-if="showCurrentPhaseAside && currentPhase">
          <div class="scoreLabel">当前阶段</div>
          <div class="scoreValue">{{ currentPhase.score }}</div>
          <div class="scoreRange">{{ currentPhase.age_range }}</div>
          <p class="scoreSummary">{{ currentPhase.summary || currentPhase.feeling }}</p>
          <p v-if="currentPhaseMeaningLine" class="scoreNote">{{ currentPhaseMeaningLine }}</p>
          <div class="keywordRow">
            <span v-for="keyword in currentPhase.keywords || []" :key="keyword" class="keyword">
              {{ keyword }}
            </span>
          </div>
        </div>

        <div class="heroAside" v-else-if="showTimelineAside && timelineValidation?.events?.length">
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
              {{ item.date_label }} / {{ item.title }}
            </span>
          </div>
        </div>

        <div class="heroAside" v-else-if="showBlueprintAside && natalBlueprint">
          <div class="scoreLabel">用户六问</div>
          <div class="historyTitle">{{ blueprintHeroTitle }}</div>
          <div class="scoreRange">{{ blueprintMetaLine }}</div>
          <p class="scoreSummary">
            {{ blueprintHeroSummary }}
          </p>
          <div class="keywordRow">
            <span v-for="keyword in blueprintHeroKeywords" :key="keyword" class="keyword">
              {{ keyword }}
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
        <section v-if="showBlueprintGuide" class="focusGuide">
          <article class="guideIntro">
            <div class="panelEyebrow">阅读路径</div>
            <h2 class="panelTitle">先看什么，再看什么</h2>
            <p class="panelSummary">
              本命蓝图先直接回答六个用户问题，再把星盘、相位、飞宫和接纳这些底层依据留到后面核对。
            </p>
          </article>

          <article
            v-for="item in blueprintGuideCards"
            :key="item.step"
            class="guideStepCard"
          >
            <div class="guideStep">{{ item.step }}</div>
            <div class="guideStepTitle">{{ item.title }}</div>
            <h3 class="guideHeadline">{{ item.summary }}</h3>
            <p class="guideHint">{{ item.hint }}</p>
            <span class="guideBadge">{{ item.badge }}</span>
          </article>
        </section>

        <ReadingMethodPanel :analysis-key="analysisKey" />

        <section v-if="profileValidationAnchors.length" class="insightGrid secondary">
          <article class="panel panelWide">
            <div class="panelEyebrow">现实对照</div>
            <h2 class="panelTitle">{{ activeTestProfile?.name || "测试用户" }}的现实经历对照</h2>
            <p class="panelSummary">
              这些信息不是参与排盘计算的输入，而是用来回看这张盘有没有打中真实的人生路径。
              对夏天这类跨领域样例，尤其适合拿来校验职业路线、长期主轴和后续兴趣转向。
            </p>
            <div class="keywordRow" v-if="activeTestProfile?.tags?.length">
              <span v-for="item in activeTestProfile.tags" :key="item" class="keyword">{{ item }}</span>
            </div>
          </article>

          <article
            v-for="item in profileValidationAnchors"
            :key="item.title"
            class="panel"
          >
            <div class="panelEyebrow">关键经历</div>
            <h2 class="panelTitle">{{ item.title }}</h2>
            <p class="panelSummary">{{ item.summary }}</p>
            <div v-if="item.tags?.length" class="tagGrid">
              <span v-for="tag in item.tags" :key="tag" class="tag">{{ tag }}</span>
            </div>
          </article>
        </section>

        <section v-if="metricCards.length" class="metricGrid">
          <article v-for="item in metricCards" :key="item.label" class="metricCard">
            <div class="metricLabel">{{ item.label }}</div>
            <div class="metricValue">
              {{ item.value }}
              <span class="metricSub" v-if="item.subValue">/ {{ item.subValue }}</span>
            </div>
            <div class="metricHint">{{ item.hint }}</div>
          </article>
        </section>

        <template v-if="analysisKey === 'natal_blueprint'">
          <NatalBlueprintPanel v-if="showNatalBlueprintPanel" :blueprint="natalBlueprint" />
          <NatalChartPanel
            v-if="showNatalChartPanel"
            :natal-chart="natalChart"
            :advanced-patterns="advancedPatterns"
          />
        </template>
        <template v-else>
          <NatalChartPanel
            v-if="showNatalChartPanel"
            :natal-chart="natalChart"
            :advanced-patterns="advancedPatterns"
          />
          <NatalBlueprintPanel v-if="showNatalBlueprintPanel" :blueprint="natalBlueprint" />
        </template>
        <AdvancedPatternsPanel v-if="showAdvancedPatternsPanel" :advanced-patterns="advancedPatterns" />
        <CaseThemesPanel v-if="showCaseThemesPanel" :advanced-patterns="advancedPatterns" />
        <TimelineValidationPanel v-if="showTimelineValidationPanel" :timeline="timelineValidation" />

        <section v-if="showLifeModelSummary" class="insightGrid">
          <article class="panel panelWide">
            <div class="panelEyebrow">人生主轴</div>
            <h2 class="panelTitle">你的人生主轴</h2>
            <p class="panelSummary">{{ lifeModel?.summary || natalChart?.signature || "-" }}</p>
            <div class="tagGrid">
              <span v-for="theme in lifeModel?.core_themes || []" :key="theme" class="tag">
                {{ theme }}
              </span>
            </div>
          </article>

          <article class="panel">
            <div class="panelEyebrow">优势入口</div>
            <h2 class="panelTitle">你更容易发挥的优势</h2>
            <ul class="list">
              <li v-for="item in lifeModel?.strengths || []" :key="item">{{ item }}</li>
            </ul>
          </article>

          <article class="panel">
            <div class="panelEyebrow">关键课题</div>
            <h2 class="panelTitle">容易反复遇到的课题</h2>
            <ul class="list">
              <li v-for="item in lifeModel?.challenges || []" :key="item">{{ item }}</li>
            </ul>
          </article>
        </section>

        <section v-if="showNatalReferenceGrid" class="insightGrid secondary">
          <article class="panel">
            <div class="panelEyebrow">主导星体</div>
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
            <div class="panelEyebrow">重点宫位</div>
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
            <div class="panelEyebrow">关键相位</div>
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

        <section class="phaseBoard" v-if="showPhaseBoard && currentPhase">
          <article class="phaseHero">
            <div class="panelEyebrow">当前阶段</div>
            <h2 class="panelTitle">你现在正走到人生的哪一段</h2>
            <p class="panelSummary">{{ currentPhase.summary || currentPhase.feeling }}</p>
            <p v-if="currentPhaseMeaningLine" class="phaseMeaning">{{ currentPhaseMeaningLine }}</p>

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
            <div class="panelEyebrow">顺势方向</div>
            <h2 class="panelTitle">适合顺势推进的方向</h2>
            <ul class="list">
              <li v-for="item in currentPhase.opportunities || []" :key="item">{{ item }}</li>
            </ul>
          </article>

          <article class="panel">
            <div class="panelEyebrow">风险提醒</div>
            <h2 class="panelTitle">当前最需要留意的地方</h2>
            <ul class="list">
              <li v-for="item in currentPhase.cautions || []" :key="item">{{ item }}</li>
            </ul>
          </article>

          <article class="panel">
            <div class="panelEyebrow">行动重点</div>
            <h2 class="panelTitle">更适合你的行动方式</h2>
            <ul class="list">
              <li v-for="item in currentPhase.action_focus || []" :key="item">{{ item }}</li>
            </ul>
          </article>
        </section>

        <section v-if="showTimingWindows" class="timelineGrid">
          <article class="panel">
            <div class="panelEyebrow">发力窗口</div>
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
            <div class="panelEyebrow">调整窗口</div>
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
            <div class="panelEyebrow">长期走法</div>
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

        <template v-if="showTimingVisuals">
          <LifeStructureChart :report="report" @structure-updated="onStructureUpdated" />
          <LifeDomainsChart :domain-data="domainData" />
          <FirdariaTable :periods="report.kline_data.periods" />
        </template>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { apiClient } from "@/config/api";
import { DEFAULT_TEST_SUBJECT, FEATURED_NATAL_EXAMPLE } from "@/config/examples";
import {
  buildSubjectFromProfile,
  getTestUserProfileByKey,
  type TestUserProfile,
} from "@/config/testProfiles";
import { getPlanetMeaning } from "@/utils/planetMeaning";
import { getAnalysisByKey } from "@/utils/analysis";
import type { AnalysisDefinition, AnalysisResponse, DomainPoint, LifeReport } from "@/utils/types";
import AdvancedPatternsPanel from "./components/AdvancedPatternsPanel.vue";
import CaseThemesPanel from "./components/CaseThemesPanel.vue";
import FirdariaTable from "./components/FirdariaTable.vue";
import LifeDomainsChart from "./components/LifeDomainsChart.vue";
import LifeStructureChart from "./components/LifeStructureChart.vue";
import NatalBlueprintPanel from "./components/NatalBlueprintPanel.vue";
import NatalChartPanel from "./components/NatalChartPanel.vue";
import ReadingMethodPanel from "./components/ReadingMethodPanel.vue";
import TimelineValidationPanel from "./components/TimelineValidationPanel.vue";

interface MetricCardItem {
  label: string;
  value: string;
  hint: string;
  subValue?: string;
}

interface GuideCardItem {
  step: string;
  title: string;
  summary: string;
  hint: string;
  badge: string;
}

interface BlueprintQuestionSection {
  key: string;
  question: string;
  answer: string;
}

const REPORT_LAYOUTS = {
  phase_navigation: {
    showCurrentPhaseAside: true,
    showTimelineAside: true,
    showBlueprintAside: false,
    showNatalChartPanel: true,
    showNatalBlueprintPanel: true,
    showAdvancedPatternsPanel: true,
    showCaseThemesPanel: true,
    showTimelineValidationPanel: true,
    showLifeModelSummary: true,
    showNatalReferenceGrid: true,
    showPhaseBoard: true,
    showTimingWindows: true,
    showTimingVisuals: true,
  },
  natal_blueprint: {
    showCurrentPhaseAside: false,
    showTimelineAside: false,
    showBlueprintAside: true,
    showNatalChartPanel: true,
    showNatalBlueprintPanel: true,
    showAdvancedPatternsPanel: true,
    showCaseThemesPanel: false,
    showTimelineValidationPanel: false,
    showLifeModelSummary: false,
    showNatalReferenceGrid: false,
    showPhaseBoard: false,
    showTimingWindows: false,
    showTimingVisuals: false,
  },
} as const;

const PLANET_LABELS: Record<string, string> = {
  SUN: "太阳",
  MOON: "月亮",
  MERCURY: "水星",
  VENUS: "金星",
  MARS: "火星",
  JUPITER: "木星",
  SATURN: "土星",
  URANUS: "天王星",
  NEPTUNE: "海王星",
  PLUTO: "冥王星",
  NORTH_NODE: "北交点",
  SOUTH_NODE: "南交点",
  CHIRON: "凯龙星",
  JUNO: "婚神星",
  CERES: "谷神星",
  PALLAS: "智神星",
  VESTA: "灶神星",
};

const route = useRoute();
const router = useRouter();

const loading = ref(true);
const error = ref("");
const report = ref<LifeReport | null>(null);
const analysis = ref<AnalysisDefinition | null>(getAnalysisByKey(currentAnalysisKey()));
const domainData = ref<DomainPoint[]>([]);

const natalChart = computed(() => report.value?.natal_chart ?? null);
const currentPhase = computed(() => report.value?.current_phase ?? null);
const lifeModel = computed(() => report.value?.life_model ?? null);
const natalBlueprint = computed(() => report.value?.natal_blueprint ?? null);
const advancedPatterns = computed(() => report.value?.advanced_patterns ?? null);
const timelineValidation = computed(() => report.value?.timeline_validation ?? null);
const blueprintQuestionSections = computed<BlueprintQuestionSection[]>(() => {
  const source = natalBlueprint.value?.question_sections;
  return Array.isArray(source) ? (source as BlueprintQuestionSection[]) : [];
});
const analysisKey = computed(() => analysis.value?.key || currentAnalysisKey());
const activeTestProfile = computed<TestUserProfile | undefined>(() => {
  const profileKey = currentProfileKey();
  if (profileKey) return getTestUserProfileByKey(profileKey);
  if (!currentReportId() && !currentExampleKey()) {
    return getTestUserProfileByKey("xiatian");
  }
  return undefined;
});
const profileValidationAnchors = computed(() => activeTestProfile.value?.validationAnchors ?? []);
const activeLayout = computed(() => {
  const key = analysisKey.value as keyof typeof REPORT_LAYOUTS;
  return REPORT_LAYOUTS[key] || REPORT_LAYOUTS.phase_navigation;
});

const heroTitle = computed(() => {
  if (analysisKey.value === "natal_blueprint") {
    return natalBlueprint.value?.role_title || analysis.value?.title || "本命蓝图";
  }
  return lifeModel.value?.title || analysis.value?.title || "占星人生";
});

const heroSummary = computed(() => {
  if (analysisKey.value === "natal_blueprint") {
    if (blueprintQuestionSections.value.length) {
      return "这份本命蓝图会先直接回答你是谁、适合做什么、学业、事业、财富和感情，再把底层占星依据放到后面。";
    }
    return (
      natalBlueprint.value?.summary ||
      natalBlueprint.value?.signature ||
      natalChart.value?.signature ||
      analysis.value?.description ||
      "我们正在为你整理本命结构、社会角色与长期命题。"
    );
  }
  return (
    lifeModel.value?.summary ||
    natalChart.value?.signature ||
    analysis.value?.description ||
    "我们正在为你整理本命结构、阶段节奏与关键提醒。"
  );
});

const blueprintHeroTitle = computed(() => {
  if (blueprintQuestionSections.value.length) {
    return "你最关心的六个答案";
  }
  return natalBlueprint.value?.role_title || analysis.value?.title || "本命蓝图";
});

const blueprintHeroSummary = computed(() => {
  const firstQuestion = blueprintQuestionSections.value[0];
  if (firstQuestion?.answer) return firstQuestion.answer;
  return natalBlueprint.value?.signature || natalBlueprint.value?.summary || natalChart.value?.signature || heroSummary.value;
});

const blueprintHeroKeywords = computed(() => {
  if (blueprintQuestionSections.value.length) {
    return blueprintQuestionSections.value.slice(0, 6).map((item) => item.question);
  }
  return natalBlueprint.value?.keywords || [];
});

const blueprintMetaLine = computed(() => {
  if (blueprintQuestionSections.value.length) {
    return `${blueprintQuestionSections.value.length} 个核心问题 · 先给答案后看证据`;
  }
  const ruler = natalChart.value?.chart_ruler_label || natalChart.value?.chart_ruler;
  const house = natalChart.value?.house_emphasis?.[0];
  if (ruler && house?.title) {
    return `${ruler}命主 · 第${house.house}宫 ${house.title}`;
  }
  if (ruler) return `${ruler}命主`;
  if (house?.title) return `第${house.house}宫 ${house.title}`;
  return "结构与角色";
});

const phaseLeadText = computed(() => {
  if (currentPhase.value) return mapPlanet(currentPhase.value.major_lord) || "-";
  if (timelineValidation.value?.events?.length) return "历史样例";
  return "-";
});

const phaseSubText = computed(() => {
  if (!currentPhase.value) return "";
  return mapPlanet(currentPhase.value.sub_lord) || "无子运";
});

const currentPhaseMeaningLine = computed(() => {
  if (!currentPhase.value) return "";

  const majorLabel = mapPlanet(currentPhase.value.major_lord);
  const majorMeaning = getPlanetMeaning(currentPhase.value.major_lord);
  const subLabel = mapPlanet(currentPhase.value.sub_lord);
  const subMeaning = getPlanetMeaning(currentPhase.value.sub_lord);
  const parts: string[] = [];

  if (majorLabel && majorMeaning) {
    parts.push(`主运星${majorLabel}：${majorMeaning.focus}`);
  }

  if (subLabel && subLabel !== "无子运" && subMeaning) {
    parts.push(`子运星${subLabel}：${subMeaning.focus}`);
  }

  return parts.join(" ");
});

const metricCards = computed<MetricCardItem[]>(() => {
  const sun = natalChart.value?.planets?.SUN?.sign_label || natalChart.value?.planets?.SUN?.sign || "-";
  const moon =
    natalChart.value?.planets?.MOON?.sign_label || natalChart.value?.planets?.MOON?.sign || "-";
  const topHouse = natalChart.value?.house_emphasis?.[0];
  const topHouseValue = topHouse ? `第${topHouse.house}宫 / ${topHouse.title}` : "-";
  const primaryPressure = natalChart.value?.pressure_points?.[0];

  if (analysisKey.value === "natal_blueprint") {
    void sun;
    void moon;
    void topHouseValue;
    void primaryPressure;
    return [];
  }

  return [
    {
      label: "太阳 / 月亮",
      value: sun,
      subValue: moon,
      hint: "你的驱动力与情绪底色",
    },
    {
      label: "当前主运",
      value: phaseLeadText.value,
      subValue: phaseSubText.value || undefined,
      hint: currentPhase.value ? "这段时间最明显的人生主题" : "历史样例以人生节点校验替代实时阶段",
    },
    {
      label: "核心人生领域",
      value: natalChart.value?.house_emphasis?.[0]?.title || "-",
      hint: "这里最容易成为你长期投入的重心",
    },
    {
      label: "当前趋势",
      value: trendLabel(currentPhase.value?.trend_type),
      hint: currentPhase.value?.description || "当前阶段的整体走向",
    },
  ];
});

const showCurrentPhaseAside = computed(() => activeLayout.value.showCurrentPhaseAside);
const showTimelineAside = computed(() => activeLayout.value.showTimelineAside);
const showBlueprintAside = computed(() => activeLayout.value.showBlueprintAside);
const showNatalChartPanel = computed(() => activeLayout.value.showNatalChartPanel);
const showNatalBlueprintPanel = computed(() => activeLayout.value.showNatalBlueprintPanel);
const showAdvancedPatternsPanel = computed(() => activeLayout.value.showAdvancedPatternsPanel);
const showCaseThemesPanel = computed(() => activeLayout.value.showCaseThemesPanel);
const showTimelineValidationPanel = computed(() => activeLayout.value.showTimelineValidationPanel);
const showLifeModelSummary = computed(
  () => activeLayout.value.showLifeModelSummary && Boolean(lifeModel.value)
);
const showNatalReferenceGrid = computed(
  () => activeLayout.value.showNatalReferenceGrid && Boolean(natalChart.value)
);
const showPhaseBoard = computed(() => activeLayout.value.showPhaseBoard);
const showTimingWindows = computed(
  () => activeLayout.value.showTimingWindows && Boolean(lifeModel.value)
);
const showTimingVisuals = computed(() => activeLayout.value.showTimingVisuals);
const showBlueprintGuide = computed(() => false);

const blueprintGuideCards = computed<GuideCardItem[]>(() => {
  const questions = blueprintQuestionSections.value;
  if (questions.length >= 4) {
    return [
      {
        step: "01",
        title: "先看你是谁",
        summary: questions[0]?.answer || questions[0]?.question || "先确认你的底层角色",
        hint: "先确认这张盘最核心的自我定位，不要一上来就掉进术语和细节。",
        badge: "看第 1 问",
      },
      {
        step: "02",
        title: "再看适配方向",
        summary: questions[1]?.answer || questions[1]?.question || "再看你适合把哪条路做成主轴",
        hint: "把适合做什么和能长期承担什么分开看，职业判断才会稳。",
        badge: "看第 2 问",
      },
      {
        step: "03",
        title: "抓事业与财富",
        summary: questions[3]?.answer || questions[4]?.answer || "看事业和财富怎么落地",
        hint: "先确认职业主轴，再看钱从哪里来、怎么放大、哪里会漏。",
        badge: "看第 4 / 5 问",
      },
      {
        step: "04",
        title: "最后看关系",
        summary: questions[5]?.answer || questions[5]?.question || "看感情和伴侣怎么参与人生结构",
        hint: "感情不是孤立题，它往往和合作、资源、现实结构绑在一起。",
        badge: "看第 6 问",
      },
    ];
  }

  const layers = Array.isArray(natalBlueprint.value?.layers) ? natalBlueprint.value?.layers : [];
  const roleLayer = layers.find((item: Record<string, any>) => item?.key === "role") || layers[2];
  const structureLayer =
    layers.find((item: Record<string, any>) => item?.key === "structure") || layers[0];
  const powerLayer = layers.find((item: Record<string, any>) => item?.key === "power") || layers[1];
  const costLayer = layers.find((item: Record<string, any>) => item?.key === "cost") || layers[3];

  return [
    {
      step: "01",
      title: "先看你是谁",
      summary:
        natalBlueprint.value?.role_title ||
        roleLayer?.headline ||
        "你在社会中更像什么人",
      hint:
        "先确认这张盘最像哪一种社会角色，不要一开始就掉进细节。",
      badge: "先看本命蓝图顶部",
    },
    {
      step: "02",
      title: "再看你适合什么",
      summary:
        structureLayer?.headline ||
        natalChart.value?.signature ||
        "这张盘最适合把什么方向做成长期主轴",
      hint:
        "先把长期主轴看清，再决定什么事情值得你长期投入。",
      badge: "看主轴",
    },
    {
      step: "03",
      title: "再看事业和资源",
      summary:
        powerLayer?.headline ||
        "你通过什么入口做事业、拿资源、形成影响力",
      hint:
        "事业和财富不是分开的，要一起看你通过什么场景拿结果。",
      badge: "看事业/财富",
    },
    {
      step: "04",
      title: "最后看风险和关系",
      summary:
        costLayer?.headline ||
        "你的强项会从哪里反噬，关系又会怎么参与人生结构",
      hint:
        "最后再看风险点和关系牵动，判断怎么守住优势、不让能力变负担。",
      badge: "看风险/关系",
    },
  ];
});

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

function currentProfileKey() {
  const profile = route.query.profile;
  return typeof profile === "string" && profile ? profile : undefined;
}

function currentAnalysisKey() {
  const queryAnalysis = route.query.analysis;
  if (typeof queryAnalysis === "string" && getAnalysisByKey(queryAnalysis)) {
    return queryAnalysis;
  }
  return "phase_navigation";
}

function buildExampleRequest(exampleKey: string) {
  if (exampleKey !== FEATURED_NATAL_EXAMPLE.key) {
    return null;
  }

  return {
    analysis_type: currentAnalysisKey(),
    subjects: [
      {
        name: FEATURED_NATAL_EXAMPLE.name,
        gender: FEATURED_NATAL_EXAMPLE.gender,
        birth_time: FEATURED_NATAL_EXAMPLE.birthTime,
        lat: FEATURED_NATAL_EXAMPLE.latitude,
        lon: FEATURED_NATAL_EXAMPLE.longitude,
        timezone: FEATURED_NATAL_EXAMPLE.timezone,
      },
    ],
  };
}

function buildProfileRequest(profileKey: string) {
  const profile = getTestUserProfileByKey(profileKey);
  if (!profile) return null;

  return {
    analysis_type: currentAnalysisKey(),
    subjects: [buildSubjectFromProfile(profile)],
  };
}

async function loadReport() {
  loading.value = true;
  error.value = "";

  try {
    const reportId = currentReportId();
    const exampleKey = currentExampleKey();
    const profileKey = currentProfileKey();

    if (reportId) {
      const response = await apiClient.get<AnalysisResponse<LifeReport>>(`/analyses/${reportId}`);
      if (response.data?.status === "success") {
        if (response.data.analysis?.key === "monthly_lunar_return") {
          router.replace({
            name: "monthly-return",
            params: { id: reportId },
          });
          return;
        }
        report.value = response.data.data;
        analysis.value = response.data.analysis || getAnalysisByKey(currentAnalysisKey());
        return;
      }
    }

    if (exampleKey) {
      const payload = buildExampleRequest(exampleKey);
      if (payload) {
        const exampleResponse = await apiClient.post<AnalysisResponse<LifeReport>>("/analyses", payload);
        if (exampleResponse.data?.status === "success") {
          report.value = exampleResponse.data.data;
          analysis.value = exampleResponse.data.analysis || getAnalysisByKey(currentAnalysisKey());
          return;
        }
      }
    }

    if (profileKey) {
      const payload = buildProfileRequest(profileKey);
      if (payload) {
        const profileResponse = await apiClient.post<AnalysisResponse<LifeReport>>("/analyses", payload);
        if (profileResponse.data?.status === "success") {
          report.value = profileResponse.data.data;
          analysis.value = profileResponse.data.analysis || getAnalysisByKey(currentAnalysisKey());
          return;
        }
      }
    }

    const fallback = await apiClient.post<AnalysisResponse<LifeReport>>("/analyses", {
      analysis_type: currentAnalysisKey(),
      subjects: [
        {
          name: "夏天",
          gender: "女",
          birth_time: DEFAULT_TEST_SUBJECT.birthTime,
          lat: DEFAULT_TEST_SUBJECT.lat,
          lon: DEFAULT_TEST_SUBJECT.lon,
          timezone: DEFAULT_TEST_SUBJECT.timezone,
        },
      ],
    });

    if (fallback.data?.status === "success") {
      report.value = fallback.data.data;
      analysis.value = fallback.data.analysis || getAnalysisByKey(currentAnalysisKey());
      return;
    }

    error.value = "服务返回了不可用的报告结果。";
  } catch (err) {
    console.error(err);
    error.value = "无法加载占星报告，请检查后端服务与报告 ID。";
  } finally {
    loading.value = false;
  }
}

watch(
  () => [route.params.id, route.query.id, route.query.example, route.query.analysis, route.query.profile],
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
  max-width: var(--report-shell-max);
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

.scoreNote,
.phaseMeaning {
  margin: 12px 0 0;
  color: rgba(248, 250, 252, 0.86);
  line-height: 1.8;
  font-size: 13px;
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

.focusGuide {
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) repeat(4, minmax(0, 0.8fr));
  gap: 18px;
  margin-bottom: 22px;
}

.guideIntro,
.guideStepCard {
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(15, 23, 42, 0.72);
  backdrop-filter: blur(18px);
  border-radius: 24px;
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.24);
}

.guideIntro {
  padding: 24px;
}

.guideStepCard {
  position: relative;
  overflow: hidden;
  padding: 20px;
}

.guideStepCard::before {
  content: "";
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  background: linear-gradient(180deg, rgba(212, 175, 55, 0.9), rgba(212, 175, 55, 0.14));
}

.guideStep {
  color: var(--gold);
  font-size: 12px;
  letter-spacing: 0.18em;
  font-weight: 700;
}

.guideStepTitle {
  margin-top: 10px;
  color: rgba(248, 250, 252, 0.72);
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.guideHeadline {
  margin: 10px 0 0;
  color: var(--text);
  font-size: 20px;
  line-height: 1.35;
}

.guideHint {
  margin: 12px 0 0;
  color: var(--text-secondary);
  line-height: 1.7;
  font-size: 13px;
}

.guideBadge {
  display: inline-flex;
  align-items: center;
  margin-top: 16px;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: rgba(248, 250, 252, 0.76);
  font-size: 12px;
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
  .focusGuide,
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
