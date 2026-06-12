<template>
  <div class="page">
    <div class="aurora aurora-a"></div>
    <div class="aurora aurora-b"></div>

    <section class="hero">
      <div class="heroMain">
        <div class="eyebrow">Astrology Life Map</div>
        <h1 class="title">
          占星人生
          <span>先读懂你的天赋底盘，再看清你正走到哪一段</span>
        </h1>
        <p class="summary">
          这不是一个只给“吉凶结论”的占星工具。它会从本命结构出发，结合时间节奏，帮你理解现在的主题、机会，以及哪些地方更适合慢下来。
        </p>

        <div class="heroActions">
          <el-button class="primaryBtn" type="primary" round @click="scrollToCatalog">
            开始探索
          </el-button>
          <span class="transitHint" v-if="transitData">
            今日天象提示：{{ transitData.interpretation }}
          </span>
        </div>

        <div class="heroMetrics">
          <div class="metricCard">
            <span>当前可体验</span>
            <strong>阶段导航报告</strong>
          </div>
          <div class="metricCard">
            <span>当前解读方式</span>
            <strong>本命结构 + 阶段节奏</strong>
          </div>
          <div class="metricCard" v-if="transitData">
            <span>实时天象焦点</span>
            <strong>
              水星在 {{ transitData.planets?.MERCURY?.sign_label || transitData.planets?.MERCURY?.sign || "-" }}
            </strong>
          </div>
        </div>

        <article v-if="showHomepageExample" class="exampleEntry">
          <div class="exampleCopy">
            <div class="exampleEyebrow">Quick Example</div>
            <h3>直接查看示例命盘</h3>
            <p>
              用黄金荣的出生信息做查看例子，用户可以先直接打开，快速看我们现在的内容和结构。
            </p>
            <div class="exampleMeta">
              <span>{{ featuredExample.name }} · {{ featuredExample.gender }}</span>
              <span>{{ featuredExample.birthTimeLabel }}</span>
              <span>{{ featuredExample.birthPlace }}</span>
              <span>{{ featuredExample.longitudeLabel }} / {{ featuredExample.latitudeLabel }}</span>
            </div>
          </div>

          <div class="exampleActions">
            <el-button class="exampleBtn" type="primary" round @click="openFeaturedExample">
              查看示例
            </el-button>
            <el-button text @click="openDefaultAnalysis">填写我的信息</el-button>
          </div>
        </article>
      </div>

      <aside class="heroAside">
        <div class="panelEyebrow">Reading Logic</div>
        <h2 class="panelTitle">这套解读，会先回答你真正关心的问题</h2>
        <ul class="list">
          <li>先看你天生的底层结构，不用短期波动覆盖你的本命节奏。</li>
          <li>再看你正处在哪个阶段，分清现在更适合扩张、沉淀还是重组。</li>
          <li>最后给出可执行的提醒，让占星不是“看热闹”，而是能指导现实选择。</li>
        </ul>
      </aside>
    </section>

    <section id="analysis-catalog" class="catalogSection">
      <div class="sectionHead">
        <div>
          <div class="eyebrow">Reading Paths</div>
          <h2 class="sectionTitle">从你当下最关心的问题开始</h2>
          <p class="sectionText">
            每个入口都对应一种人生提问。当前已开放“阶段导航”，其余模块会沿用同一套解读逻辑逐步上线。
          </p>
        </div>
        <div class="legend">
          <span class="legendItem active">已开放</span>
          <span class="legendItem planned">即将上线</span>
        </div>
      </div>

      <div class="catalogGrid">
        <article
          v-for="item in catalog"
          :key="item.key"
          class="catalogCard"
          :class="item.status"
        >
          <div class="cardTop">
            <span class="category">{{ categoryLabel(item.category) }}</span>
            <span class="status" :class="item.status">
              {{ statusLabel(item.status) }}
            </span>
          </div>

          <h3>{{ item.title }}</h3>
          <p class="tagline">{{ item.tagline }}</p>
          <p class="description">{{ item.description }}</p>

          <div class="chipRow">
            <span class="chip">{{ subjectLabel(item.subjects_count) }}</span>
            <span class="chip">{{ item.modules.length }} 个结果模块</span>
          </div>

          <div class="moduleStack">
            <span v-for="module in item.modules.slice(0, 4)" :key="module" class="moduleChip">
              {{ module }}
            </span>
          </div>

          <div class="cardActions">
            <el-button
              type="primary"
              round
              :plain="item.status !== 'active'"
              @click="goToAnalysis(item)"
            >
              {{ item.primary_cta }}
            </el-button>
          </div>
        </article>
      </div>
    </section>

    <section class="featureGrid">
      <article class="featureCard">
        <div class="featureIndex">01</div>
        <h3>先回答问题，再展开方法</h3>
        <p>
          用户不需要先理解复杂技法，只需要从“我是谁”“我正处于什么阶段”“这段关系为什么会这样”这些真实问题出发。
        </p>
      </article>

      <article class="featureCard">
        <div class="featureIndex">02</div>
        <h3>同一份资料，多种解读入口</h3>
        <p>
          一次录入出生信息，后续可以进入不同主题的解读，不必为了每一种方法重复填写和重复理解。
        </p>
      </article>

      <article class="featureCard">
        <div class="featureIndex">03</div>
        <h3>报告不是结论堆砌，而是行动地图</h3>
        <p>
          我们关心的不只是“你会发生什么”，更是“你现在更适合怎么做，才能顺着自己的节奏前进”。
        </p>
      </article>
    </section>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { apiClient } from "@/config/api";
import { FEATURED_NATAL_EXAMPLE, HOMEPAGE_EXAMPLE_VISIBLE } from "@/config/examples";
import { ANALYSIS_CATEGORY_LABELS, FALLBACK_ANALYSIS_TYPES } from "@/utils/analysis";
import type { AnalysisDefinition, AnalysisStatus } from "@/utils/types";

const router = useRouter();

const catalog = ref<AnalysisDefinition[]>([...FALLBACK_ANALYSIS_TYPES]);
const transitData = ref<any>(null);
const featuredExample = FEATURED_NATAL_EXAMPLE;
const showHomepageExample = HOMEPAGE_EXAMPLE_VISIBLE;

function scrollToCatalog() {
  document.getElementById("analysis-catalog")?.scrollIntoView({ behavior: "smooth", block: "start" });
}

function categoryLabel(value: string) {
  return ANALYSIS_CATEGORY_LABELS[value] || "未分类";
}

function statusLabel(status: AnalysisStatus) {
  return status === "active" ? "已开放" : "即将上线";
}

function subjectLabel(count: number) {
  return count > 1 ? `${count} 人解读` : "1 人解读";
}

function goToAnalysis(item: AnalysisDefinition) {
  router.push({
    name: "analysis",
    params: { type: item.key },
  });
}

function openDefaultAnalysis() {
  router.push({
    name: "analysis",
    params: { type: "phase_navigation" },
  });
}

function openFeaturedExample() {
  router.push({
    name: "report",
    query: {
      example: featuredExample.key,
    },
  });
}

async function loadCatalog() {
  try {
    const response = await apiClient.get<{ status: string; data: AnalysisDefinition[] }>(
      "/analysis-types"
    );
    if (response.data?.status === "success" && response.data.data?.length) {
      catalog.value = response.data.data;
    }
  } catch (error) {
    console.error("Failed to load analysis catalog", error);
  }
}

onMounted(async () => {
  loadCatalog();
  try {
    const response = await apiClient.get("/transit/now");
    if (response.data?.status === "success") {
      transitData.value = response.data.data;
    }
  } catch (error) {
    console.error("Failed to fetch transit data", error);
  }
});
</script>

<style scoped lang="less">
.page {
  position: relative;
  min-height: calc(100vh - var(--h-footer));
  overflow: hidden;
  padding: 40px 20px 80px;
  background:
    radial-gradient(circle at 8% 10%, rgba(212, 175, 55, 0.08), transparent 24%),
    radial-gradient(circle at 88% 16%, rgba(99, 102, 241, 0.16), transparent 22%),
    linear-gradient(180deg, #020617 0%, #07111f 100%);
}

.aurora {
  position: absolute;
  border-radius: 50%;
  filter: blur(96px);
  opacity: 0.5;
  pointer-events: none;
}

.aurora-a {
  width: 320px;
  height: 320px;
  top: 40px;
  left: -80px;
  background: rgba(212, 175, 55, 0.14);
}

.aurora-b {
  width: 420px;
  height: 420px;
  right: -140px;
  top: 200px;
  background: rgba(42, 167, 184, 0.18);
}

.hero,
.catalogSection,
.featureGrid {
  position: relative;
  z-index: 1;
  max-width: 1240px;
  margin: 0 auto;
}

.hero {
  display: grid;
  grid-template-columns: minmax(0, 1.3fr) minmax(320px, 0.7fr);
  gap: 24px;
  align-items: stretch;
}

.heroMain,
.heroAside,
.catalogCard,
.featureCard {
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(15, 23, 42, 0.74);
  backdrop-filter: blur(18px);
  border-radius: 28px;
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.24);
}

.heroMain,
.heroAside,
.featureCard {
  padding: 30px;
}

.eyebrow,
.panelEyebrow {
  font-size: 12px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--gold);
}

.title {
  margin: 16px 0 0;
  color: var(--text);
  font-size: 58px;
  line-height: 1.02;
  letter-spacing: -0.05em;
  font-family: "Georgia", "Times New Roman", serif;
}

.title span {
  display: block;
  margin-top: 8px;
  color: #f8fafc;
  font-size: 30px;
  line-height: 1.2;
}

.summary,
.sectionText,
.description,
.featureCard p {
  color: var(--text-secondary);
  line-height: 1.8;
}

.summary {
  max-width: 760px;
  margin: 18px 0 0;
  font-size: 15px;
}

.heroActions {
  display: flex;
  align-items: center;
  gap: 18px;
  flex-wrap: wrap;
  margin-top: 26px;
}

.primaryBtn {
  min-width: 168px;
  font-weight: 700;
}

.transitHint {
  color: var(--text-secondary);
}

.heroMetrics {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-top: 24px;
}

.exampleEntry {
  margin-top: 18px;
  padding: 18px;
  border-radius: 24px;
  border: 1px solid rgba(212, 175, 55, 0.18);
  background:
    radial-gradient(circle at top left, rgba(212, 175, 55, 0.14), transparent 40%),
    rgba(255, 255, 255, 0.03);
  display: flex;
  justify-content: space-between;
  gap: 18px;
  align-items: flex-end;
}

.exampleEyebrow {
  color: var(--gold);
  font-size: 12px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
}

.exampleCopy h3 {
  margin: 10px 0 0;
  color: var(--text);
  font-size: 24px;
}

.exampleCopy p {
  margin: 10px 0 0;
  color: var(--text-secondary);
  line-height: 1.8;
}

.exampleMeta {
  margin-top: 14px;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.exampleMeta span {
  display: inline-flex;
  align-items: center;
  padding: 7px 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.06);
  color: var(--text-secondary);
  font-size: 12px;
}

.exampleActions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.exampleBtn {
  min-width: 140px;
}

.metricCard {
  padding: 14px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.metricCard span,
.category,
.status {
  color: var(--text-secondary);
  font-size: 12px;
}

.metricCard strong {
  display: block;
  margin-top: 8px;
  color: var(--text);
  line-height: 1.5;
}

.panelTitle,
.sectionTitle {
  margin: 10px 0 0;
  color: var(--text);
}

.panelTitle {
  font-size: 28px;
  line-height: 1.2;
}

.sectionHead {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  align-items: flex-end;
}

.sectionTitle {
  font-size: 42px;
  line-height: 1.08;
  font-family: "Georgia", "Times New Roman", serif;
}

.list {
  margin: 18px 0 0;
  padding: 0;
  list-style: none;
  display: grid;
  gap: 12px;
}

.list li {
  position: relative;
  padding-left: 18px;
  color: var(--text-secondary);
  line-height: 1.7;
}

.list li::before {
  content: "";
  position: absolute;
  left: 0;
  top: 11px;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--gold);
}

.catalogSection {
  margin-top: 34px;
}

.legend {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.legendItem {
  display: inline-flex;
  align-items: center;
  padding: 7px 12px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
}

.legendItem.active {
  color: #10b981;
  background: rgba(16, 185, 129, 0.12);
}

.legendItem.planned {
  color: #f59e0b;
  background: rgba(245, 158, 11, 0.12);
}

.catalogGrid {
  margin-top: 22px;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 18px;
}

.catalogCard {
  padding: 24px;
}

.catalogCard.active {
  background:
    radial-gradient(circle at top left, rgba(212, 175, 55, 0.12), transparent 34%),
    rgba(15, 23, 42, 0.8);
}

.catalogCard.planned {
  opacity: 0.92;
}

.cardTop {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.status.active {
  color: #10b981;
}

.status.planned {
  color: #f59e0b;
}

.catalogCard h3,
.featureCard h3 {
  margin: 14px 0 0;
  color: var(--text);
  line-height: 1.2;
}

.catalogCard h3 {
  font-size: 26px;
}

.tagline {
  margin: 10px 0 0;
  color: #f8fafc;
  line-height: 1.7;
  font-weight: 600;
}

.description {
  margin: 12px 0 0;
}

.chipRow,
.moduleStack {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.chipRow {
  margin-top: 16px;
}

.moduleStack {
  margin-top: 14px;
}

.chip,
.moduleChip {
  display: inline-flex;
  align-items: center;
  padding: 7px 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.06);
  color: var(--text-secondary);
  font-size: 12px;
}

.cardActions {
  margin-top: 22px;
}

.featureGrid {
  margin-top: 22px;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 18px;
}

.featureIndex {
  color: var(--gold);
  font-size: 13px;
  letter-spacing: 0.18em;
}

.featureCard h3 {
  font-size: 24px;
}

@media (max-width: 1100px) {
  .hero,
  .catalogGrid,
  .featureGrid,
  .heroMetrics {
    grid-template-columns: 1fr;
  }

  .exampleEntry {
    flex-direction: column;
    align-items: flex-start;
  }

  .title {
    font-size: 46px;
  }

  .title span {
    font-size: 24px;
  }

  .sectionHead {
    align-items: flex-start;
    flex-direction: column;
  }
}

@media (max-width: 720px) {
  .page {
    padding-inline: 14px;
  }

  .heroActions {
    align-items: flex-start;
    flex-direction: column;
  }

  .exampleActions {
    width: 100%;
  }

  .sectionTitle {
    font-size: 34px;
  }
}
</style>
