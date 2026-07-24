<template>
  <div class="page">
    <div class="halo halo-a"></div>
    <div class="halo halo-b"></div>

    <div class="wrap">
      <!-- ═══ Hero 叙事 ═══ -->
      <section class="hero" v-if="report">
        <p class="heroWelcome">Hi 同学，我是你的占星解读师。接下来我们将一起探索你的星盘，解锁属于你的占星人生！</p>

        <div class="heroNarrative">
          <div
            v-for="p in classifiedParas"
            :key="p.index"
            :class="['heroBlock', `heroBlock--${p.type}`]"
          >
            <!-- 本命观察：左侧金线 + 首句高亮 -->
            <template v-if="p.type === 'observation'">
              <p class="heroPara heroPara--observe">
                <span class="heroObserveNum">{{ p.index + 1 }}</span>
                <span v-html="highlightEmotion(p.text)"></span>
              </p>
            </template>

            <!-- 行运高亮：发光卡片 -->
            <template v-else-if="p.type === 'transit'">
              <div class="heroTransitCard">
                <span class="heroTransitBadge">⚡ 此刻</span>
                <p class="heroPara heroPara--transit" v-html="highlightEmotion(p.text)"></p>
              </div>
            </template>

            <!-- 法达阶段：时间轴风格 -->
            <template v-else-if="p.type === 'phase'">
              <div class="heroPhaseCard">
                <div class="heroPhaseLine"></div>
                <div class="heroPhaseBody">
                  <span class="heroPhaseBadge">🧭 人生阶段</span>
                  <p class="heroPara heroPara--phase" v-html="highlightEmotion(p.text)"></p>
                </div>
              </div>
            </template>

            <!-- 悬念钩子：渐变 CTA -->
            <template v-else-if="p.type === 'hook'">
              <div class="heroHookCard">
                <p class="heroPara heroPara--hook" v-html="highlightEmotion(p.text)"></p>
                <span class="heroHookArrow">↓</span>
              </div>
            </template>
          </div>
        </div>

        <!-- 星盘速览条 -->
        <div class="snapshotBar" v-if="starSnapshot.length">
          <span class="snapshotItem" v-for="s in starSnapshot" :key="s.label">
            <span class="snapshotIcon">{{ s.icon }}</span>
            <span class="snapshotLabel">{{ s.label }}</span>
            <span class="snapshotValue">{{ s.value }}</span>
          </span>
        </div>
      </section>

      <!-- ═══ 本命蓝图 ═══ -->
      <section class="blueprintSection" v-if="report?.natal_blueprint">
        <NatalBlueprintPanel :blueprint="report.natal_blueprint" />
      </section>

      <!-- ═══ 星盘可视化 ═══ -->
      <section class="vizSection" v-if="report">
        <!-- 本命星盘图 -->
        <div class="chartCard">
          <div class="chartCardHead">
            <h3 class="chartCardTitle">🔭 你的本命星盘</h3>
            <span class="chartCardSub">上升{{ report.natal_chart?.ascendant?.sign_label || '未知' }} · {{ report.natal_chart?.chart_ruler_label || '' }}命主</span>
          </div>
          <NatalChartWheel
            :planets="report.natal_chart?.planets || {}"
            :houses="report.natal_chart?.houses || []"
            :ascendant="report.natal_chart?.ascendant"
            :aspects="aspectsForWheel"
            :size="360"
          />
        </div>

        <!-- 人生K线图 -->
        <LifeStructureChart :report="report" @structure-updated="onStructureUpdated" />

        <!-- 法达宫格时间线 -->
        <FirdariaTimeline
          :periods="report.kline_data?.periods || []"
          :currentAge="currentAge"
        />

        <!-- 领域分布曲线 -->
        <LifeDomainsChart :domainData="domainPoints" />

        <!-- 近期行运提醒 -->
        <FastTransitBar :transits="report._transits_fast || []" />

        <!-- 长期行运背景 -->
        <TransitPanel
          :transits="activeTransits"
          title="🪐 长期行运背景"
          subtitle="慢行星（木土天海冥）正在激活你本命盘的长期主题"
        />
      </section>

      <!-- ═══ 视图切换 ═══ -->
      <section class="viewModeBar" v-if="report">
        <button
          class="viewModeTab"
          :class="{ active: viewMode === 'domains' }"
          @click="switchView('domains')"
        >📋 领域报告</button>
        <button
          class="viewModeTab"
          :class="{ active: viewMode === 'characters' }"
          @click="switchView('characters')"
        >🎭 星座角色 {{ hasCharacters ? '· 新' : '' }}</button>
      </section>

      <!-- ═══ 加载 / 错误 ═══ -->
      <section v-if="loading" class="stateCard">
        <div class="stateTitle">正在生成你的占星报告</div>
        <p class="stateText">正在整理你的本命结构、阶段节奏与人生重点，请稍候。</p>
      </section>

      <section v-else-if="error" class="stateCard errorCard">
        <div class="stateTitle">报告加载失败</div>
        <p class="stateText">{{ error }}</p>
      </section>

      <!-- ═══ 领域探索 ═══ -->
      <template v-else-if="report">

        <!-- ── 角色视图 ── -->
        <template v-if="viewMode === 'characters'">
          <CharacterWheel
            v-if="characterProfiles"
            :characters="characterProfiles.characters"
            :sorted-by-presence="characterProfiles.sorted_by_presence"
            :featured="dailyActivation?.featured_characters"
            :activation-scores="dailyActivation?.activation_scores"
            :daily-theme="dailyActivation?.daily_theme"
            @select="selectCharacter"
          />

          <!-- 选中角色后的对话面板 -->
          <section v-if="activeCharacter && selectedCharacterPersona" class="characterChatSection">
            <div class="characterChatHeader">
              <span
                class="characterChatDot"
                :style="{ background: selectedCharacterPersona.visual_color }"
              ></span>
              <span class="characterChatName">
                与 {{ selectedCharacterPersona.name }} · {{ selectedCharacterPersona.archetype }} 对话中
              </span>
              <button class="characterChatClose" @click="activeCharacter = ''; chatOpen = false">✕</button>
            </div>
            <AIChatPanel
              :greeting="currentCharacter?.personalized_greeting || '嘿，我是你的' + selectedCharacterPersona.name + '角色。想聊聊什么？'"
              :free-messages="2"
              :has-unlimited="hasAllDomains()"
              :character-sign="activeCharacter"
              :character-name="selectedCharacterPersona.name"
              :character-color="selectedCharacterPersona.visual_color"
              :report-id="activeReportId"
              @upgrade="onSelectPlan('subscription')"
              @select-character="() => {}"
            />
          </section>

          <!-- 未选角色时的提示 -->
          <section v-else-if="hasCharacters" class="characterHint">
            <p>👆 点击上方轮盘中的星座符号，或下方登场角色卡片，开始与你的星座角色对话。</p>
          </section>
        </template>

        <!-- ── 领域视图 ── -->
        <template v-if="viewMode === 'domains'">
        <section class="exploreNav">
          <p class="exploreHint">想深入了解哪个方向？</p>
          <div class="exploreRow">
            <button
              v-for="rec in recommendations"
              :key="rec.key"
              class="exploreChip"
              :class="{ active: activeDomain === rec.key }"
              @click="toggleDomain(rec.key)"
            >
              {{ rec.icon }} {{ rec.label }}
            </button>
          </div>

          <!-- 展开的领域详情 -->
          <div class="domainExpanded" v-if="activeDomain && activeDomainData">
            <template v-if="hasAllDomains() || isDomainUnlocked(activeDomain)">
              <DomainPanel
                :domain="{ ...activeDomainData, domain: activeDomain }"
                @chat="onDomainChat"
              />
            </template>
            <template v-else>
              <DomainPreviewCard
                :domain="{ ...activeDomainData, domain: activeDomain }"
                @unlock-domain="onUnlockDomain"
                @unlock-all="onUnlockAll"
              />
            </template>
          </div>
        </section>

        <!-- ═══ 因为值得 ═══ -->
        <section class="exploreNav" v-if="!hasAllDomains() && activeDomain">
          <PricingCards @select="onSelectPlan" />
        </section>

        <!-- ═══ 技术解读：飞星链路与格局分析 ═══ -->
        <section class="techSection" v-if="report?.advanced_patterns">
          <details class="techFold">
            <summary class="techSummary">
              <span class="techSummaryIcon">🔬</span>
              <span>技术解读：飞星链路与格局分析</span>
              <span class="techSummaryHint">占星爱好者入口</span>
            </summary>
            <div class="techBody">
              <AdvancedPatternsPanel :advancedPatterns="report.advanced_patterns" />
            </div>
          </details>
        </section>

        <!-- ═══ AI 深度对话入口 ═══ -->
        <section class="aiCta">
          <div class="aiCtaInner" v-if="!chatOpen">
            <div class="aiCtaLeft">
              <h3 class="aiCtaTitle">💬 还有想聊的？</h3>
              <p class="aiCtaText">上面这些只是星盘告诉我的。你想问什么、想确认什么、觉得不准的——直接跟我说。未付费用户可免费发送 2 条消息体验。</p>
            </div>
            <el-button type="primary" size="large" round @click="onAIChat" class="aiCtaBtn">
              开始深度对话 <span class="aiPriceTag">· ¥29.9/次 或 ¥199/年无限</span>
            </el-button>
          </div>
          <AIChatPanel
            v-if="chatOpen"
            :greeting="`你好！我已经看过了你的完整星盘。你想先聊聊哪个方面？比如你的事业方向、感情模式、或者现在的人生阶段——我都会从星盘的角度帮你分析。`"
            :free-messages="2"
            :has-unlimited="hasAllDomains()"
            @upgrade="onSelectPlan('subscription')"
          />
        </section>
        </template>
        <!-- end 领域视图 -->
      </template>
    </div>

    <PaymentModal
      :visible="showPayment"
      :plan-key="paymentPlanKey"
      @close="showPayment = false"
      @confirm="onPaymentConfirm"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { apiClient } from "@/config/api";
import { FEATURED_EXAMPLES } from "@/config/examples";
import { highlightEmotion } from "@/utils/textHighlight";
import type { DomainPoint, LifeReport } from "@/utils/types";
import DomainPanel from "./components/DomainPanel.vue";
import DomainPreviewCard from "./components/DomainPreviewCard.vue";
import PricingCards from "./components/PricingCards.vue";
import NatalChartWheel from "./components/NatalChartWheel.vue";
import LifeStructureChart from "./components/LifeStructureChart.vue";
import FirdariaTimeline from "./components/FirdariaTimeline.vue";
import LifeDomainsChart from "./components/LifeDomainsChart.vue";
import TransitPanel from "./components/TransitPanel.vue";
import FastTransitBar from "./components/FastTransitBar.vue";
import PaymentModal from "@/components/PaymentModal.vue";
import AIChatPanel from "./components/AIChatPanel.vue";
import CharacterWheel from "./components/CharacterWheel.vue";
import NatalBlueprintPanel from "./components/NatalBlueprintPanel.vue";
import AdvancedPatternsPanel from "./components/AdvancedPatternsPanel.vue";
import { usePayment } from "@/utils/payment";

// ── 12 领域定义 ──
const ALL_DOMAINS: Record<string, { icon: string; label: string }> = {
  personal:    { icon: "🪐", label: "性格" },
  career:      { icon: "💼", label: "事业" },
  finance:     { icon: "💰", label: "财运" },
  romance:     { icon: "💛", label: "感情" },
  marriage:    { icon: "💍", label: "婚姻" },
  family:      { icon: "🏠", label: "家庭" },
  partnership: { icon: "🤝", label: "合伙" },
  children:    { icon: "👶", label: "亲子" },
  work_skill:  { icon: "🔧", label: "工作" },
  education:   { icon: "📚", label: "学业" },
  appearance:  { icon: "✨", label: "气质" },
  health:      { icon: "🌿", label: "健康" },
};

// ── 路由 ──
const route = useRoute();
const router = useRouter();
const { isPurchased, hasFullAccess, recordPurchase } = usePayment();

const loading = ref(true);
const error = ref("");
const report = ref<LifeReport | null>(null);
const activeReportId = ref("");

// ── 付费墙 ──
const showPayment = ref(false);
const paymentPlanKey = ref("full");
const chatOpen = ref(false);

// ── 角色系统 ──
const viewMode = ref<"domains" | "characters">("domains");
const activeCharacter = ref("");
const characterProfiles = computed(() => (report.value as any)?.characters || null);
const hasCharacters = computed(() => !!characterProfiles.value?.characters);
const dailyActivation = ref<any>(null);

const aspectsForWheel = computed(() => {
  const raw = (report.value?.natal_chart?.major_aspects || []) as Array<Record<string, any>>;
  return raw.map((item) => ({
    title: String(item.title || ""),
    strength: Number(item.strength || 0),
    nature: String(item.nature || "mixed"),
    summary: item.summary,
  }));
});

const currentCharacter = computed(() => {
  if (!activeCharacter.value || !characterProfiles.value?.characters) return null;
  return characterProfiles.value.characters[activeCharacter.value] || null;
});

const selectedCharacterPersona = computed(() => {
  return currentCharacter.value?.persona || null;
});

async function fetchDailyActivation() {
  if (!activeReportId.value) return;
  try {
    const res = await apiClient.get(`/characters/${activeReportId.value}/daily`);
    if (res.data?.status === "success") {
      dailyActivation.value = res.data.data;
    }
  } catch {
    // 每日激活数据无妨
  }
}

function selectCharacter(sign: string) {
  activeCharacter.value = sign;
  viewMode.value = "characters";
  chatOpen.value = true;
}

function switchView(mode: "domains" | "characters") {
  viewMode.value = mode;
  if (mode === "characters" && !dailyActivation.value) {
    fetchDailyActivation();
  }
}

function isDomainUnlocked(domainKey: string) {
  if (!activeReportId.value) return true;
  return isPurchased(activeReportId.value, domainKey);
}
function hasAllDomains() {
  if (!activeReportId.value) return true;
  return hasFullAccess(activeReportId.value);
}
function onUnlockDomain(_key: string) {
  paymentPlanKey.value = "domain";
  showPayment.value = true;
}
function onUnlockAll() {
  paymentPlanKey.value = "full";
  showPayment.value = true;
}
function onSelectPlan(key: string) {
  paymentPlanKey.value = key;
  showPayment.value = true;
}
function onPaymentConfirm(key: string) {
  showPayment.value = false;
  if (!activeReportId.value) return;
  if (key === "full" || key === "subscription") {
    recordPurchase(activeReportId.value, key === "subscription" ? "subscription" : "full");
  }
}

// ── Hero ──
const hero = computed(() => (report.value as any)?.hero || {});

// ── 可视化数据 ──
const currentAge = computed(() => {
  const birth = report.value?.user_info?.birth_time_local;
  if (!birth) return undefined;
  const birthDate = new Date(birth);
  const now = new Date();
  let age = now.getFullYear() - birthDate.getFullYear();
  const m = now.getMonth() - birthDate.getMonth();
  if (m < 0 || (m === 0 && now.getDate() < birthDate.getDate())) age--;
  return age;
});

const activeTransits = computed(() => {
  return report.value?._transits_slow || [];
});

const heroParagraphs = computed(() => {
  const narrative = hero.value?.narrative || "";
  return narrative.split("\n\n").filter((p: string) => p.trim());
});

interface ClassifiedPara {
  text: string;
  type: "observation" | "transit" | "phase" | "hook";
  index: number;
}

const classifiedParas = computed<ClassifiedPara[]>(() => {
  const paras = heroParagraphs.value;
  const total = paras.length;
  return paras.map((text: string, i: number) => {
    let type: ClassifiedPara["type"] = "observation";
    if (text.includes("而且现在——")) {
      type = "transit";
    } else if (text.includes("正处于")) {
      type = "phase";
    } else if (i === total - 1 && (text.includes("往下翻") || text.includes("都在下面") || text.includes("值得你"))) {
      type = "hook";
    }
    return { text, type, index: i };
  });
});

// 星盘速览：上升 + 日月金火
const SNAPSHOT_PLANETS = [
  { key: "SUN",   icon: "☉", label: "太阳" },
  { key: "MOON",  icon: "☽", label: "月亮" },
  { key: "VENUS", icon: "♀", label: "金星" },
  { key: "MARS",  icon: "♂", label: "火星" },
];

const starSnapshot = computed(() => {
  const nc = report.value?.natal_chart;
  const planets = nc?.planets || {};
  const asc = nc?.ascendant;

  const items: { icon: string; label: string; value: string }[] = [];

  if (asc?.sign_label) {
    items.push({ icon: "⇧", label: "上升", value: asc.sign_label });
  }

  for (const p of SNAPSHOT_PLANETS) {
    const data = planets[p.key];
    if (data?.sign_label) {
      const house = data.house ? `${data.house}宫` : "";
      items.push({
        icon: p.icon,
        label: p.label,
        value: house ? `${data.sign_label}${house}` : data.sign_label,
      });
    }
  }

  return items;
});

// ── 领域导航 ──
const activeDomain = ref("");
const domainPoints = ref<DomainPoint[]>([]);

function onStructureUpdated(points: DomainPoint[]) {
  domainPoints.value = points;
}

const activeDomainData = computed(() => {
  const domains = (report.value as any)?.domains || {};
  return domains[activeDomain.value] || null;
});

const recommendations = computed(() => {
  const domains = (report.value as any)?.domains || {};
  return Object.keys(ALL_DOMAINS)
    .filter((k) => domains[k])
    .map((k) => ({ key: k, ...ALL_DOMAINS[k] }));
});

function toggleDomain(key: string) {
  activeDomain.value = activeDomain.value === key ? "" : key;
}

function onDomainChat(key: string) {
  console.log("[chat] domain:", key);
}

function onAIChat() {
  chatOpen.value = !chatOpen.value;
}

// ── 报告加载 ──
function currentReportId() {
  const id = route.params.id;
  return typeof id === "string" && id ? id : undefined;
}

function currentExampleKey() {
  const example = route.query.example;
  return typeof example === "string" && example ? example : undefined;
}

function currentAnalysisKey() {
  const a = route.query.analysis;
  return typeof a === "string" && a ? a : "natal_blueprint";
}

function buildExampleRequest(exampleKey: string) {
  const ex = FEATURED_EXAMPLES.find((e) => e.key === exampleKey);
  if (!ex) return null;
  return {
    analysis_type: currentAnalysisKey(),
    subjects: [{ name: ex.name, gender: ex.gender, birth_time: ex.birthTime, lat: ex.latitude, lon: ex.longitude, timezone: ex.timezone }],
  };
}

async function loadReport() {
  loading.value = true;
  error.value = "";

  try {
    const reportId = currentReportId();
    const exampleKey = currentExampleKey();

    if (reportId) {
      const res = await apiClient.get<any>(`/analyses/${reportId}`);
      if (res.data?.status === "success") {
        if (res.data.analysis?.key === "monthly_lunar_return") {
          router.replace({ name: "monthly-return", params: { id: reportId } });
          return;
        }
        report.value = res.data.data;
        activeReportId.value = reportId;
        return;
      }
    }

    if (exampleKey) {
      const payload = buildExampleRequest(exampleKey);
      if (payload) {
        const res = await apiClient.post<any>("/analyses", payload);
        if (res.data?.status === "success") {
          report.value = res.data.data;
          activeReportId.value = res.data.report_id || "";
          return;
        }
      }
    }

    // fallback
    const fb = await apiClient.post<any>("/analyses", {
      analysis_type: currentAnalysisKey(),
      subjects: [{ name: "夏天", gender: "女", birth_time: "1991-03-21T09:25:00", lat: 35.7, lon: 113.35, timezone: 8 }],
    });
    if (fb.data?.status === "success") {
      report.value = fb.data.data;
      activeReportId.value = fb.data.report_id || "";
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
  () => loadReport(),
  { immediate: true },
);
</script>

<style scoped>
/* ── 背景 ── */
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
.halo-a { width: 320px; height: 320px; top: 40px; left: -60px; background: rgba(212, 175, 55, 0.12); }
.halo-b { width: 420px; height: 420px; right: -120px; top: 180px; background: rgba(99, 102, 241, 0.18); }

.wrap {
  position: relative;
  z-index: 1;
  max-width: 800px;
  margin: 0 auto;
  padding: 56px 20px 80px;
}

/* ── Hero ── */
.hero {
  margin-bottom: 48px;
}
.heroWelcome {
  text-align: center;
  color: #94a3b8;
  font-size: 15px;
  margin: 0 0 32px;
  line-height: 1.7;
}
.heroNarrative {
  max-width: 720px;
  margin: 0 auto;
}

/* ── Hero Block 基础 ── */
.heroBlock { margin-bottom: 14px; }

.heroPara {
  margin: 0;
  color: #e2e8f0;
  font-size: 16px;
  line-height: 2.1;
}

/* ── 本命观察：编号 + 左侧金线 ── */
.heroBlock--observation {
  position: relative;
  padding: 14px 16px 14px 38px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.015);
  border-left: 2px solid rgba(212, 175, 55, 0.25);
  transition: border-color 0.3s;
}
.heroBlock--observation:hover {
  border-left-color: rgba(212, 175, 55, 0.5);
}
.heroObserveNum {
  position: absolute;
  left: 10px;
  top: 14px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: rgba(212, 175, 55, 0.15);
  color: #d4af37;
  font-size: 10px;
  font-weight: 700;
  line-height: 1;
}

/* ── 行运高亮：发光卡片 ── */
.heroBlock--transit {
  margin: 18px 0;
}
.heroTransitCard {
  position: relative;
  padding: 16px 18px;
  border-radius: 14px;
  background: rgba(99, 102, 241, 0.08);
  border: 1px solid rgba(99, 102, 241, 0.18);
  box-shadow: 0 0 24px rgba(99, 102, 241, 0.06);
}
.heroTransitBadge {
  display: inline-block;
  margin-bottom: 8px;
  padding: 3px 10px;
  border-radius: 999px;
  background: rgba(99, 102, 241, 0.2);
  color: #a5b4fc;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.04em;
}

/* ── 法达阶段：时间轴风格 ── */
.heroBlock--phase {
  margin: 18px 0;
}
.heroPhaseCard {
  display: flex;
  gap: 14px;
  padding: 16px 18px;
  border-radius: 14px;
  background: rgba(16, 185, 129, 0.05);
  border: 1px solid rgba(16, 185, 129, 0.12);
}
.heroPhaseLine {
  flex-shrink: 0;
  width: 2px;
  border-radius: 1px;
  background: linear-gradient(180deg, rgba(16, 185, 129, 0.6), rgba(16, 185, 129, 0.1));
}
.heroPhaseBadge {
  display: inline-block;
  margin-bottom: 8px;
  padding: 3px 10px;
  border-radius: 999px;
  background: rgba(16, 185, 129, 0.15);
  color: #6ee7b7;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.04em;
}

/* ── 悬念钩子：渐变 CTA ── */
.heroBlock--hook {
  margin: 22px 0 8px;
}
.heroHookCard {
  position: relative;
  padding: 20px 22px;
  border-radius: 14px;
  text-align: center;
  background: linear-gradient(135deg, rgba(212, 175, 55, 0.08), rgba(212, 175, 55, 0.02));
  border: 1px solid rgba(212, 175, 55, 0.15);
}
.heroHookArrow {
  display: block;
  margin-top: 10px;
  color: #d4af37;
  font-size: 20px;
  animation: bounce-down 1.5s ease infinite;
}
@keyframes bounce-down {
  0%, 100% { transform: translateY(0); opacity: 0.6; }
  50% { transform: translateY(6px); opacity: 1; }
}

/* ── 情绪高亮标记 ── */
:deep(mark.hl-pain) {
  background: linear-gradient(180deg, transparent 55%, rgba(248, 113, 113, 0.2) 55%);
  color: #fca5a5;
}
:deep(mark.hl-need) {
  background: linear-gradient(180deg, transparent 55%, rgba(167, 139, 250, 0.2) 55%);
  color: #c4b5fd;
}
:deep(mark.hl-gift) {
  background: linear-gradient(180deg, transparent 55%, rgba(212, 175, 55, 0.25) 55%);
  color: #f8fafc;
}
:deep(mark.hl-honest) {
  background: linear-gradient(180deg, transparent 55%, rgba(148, 163, 184, 0.15) 55%);
  color: #cbd5e1;
  font-style: italic;
}
:deep(mark.hl-correct) {
  color: #a5b4fc;
  font-weight: 500;
}
:deep(mark.hl-insight) {
  color: #d4af37;
  font-weight: 500;
}
:deep(mark.hl-contrast) {
  background: linear-gradient(180deg, transparent 55%, rgba(212, 175, 55, 0.12) 55%);
}
:deep(mark.hl-ease) {
  color: #6ee7b7;
}
:deep(mark.hl-warn) {
  color: #fbbf24;
  border-bottom: 1px dashed rgba(251, 191, 36, 0.3);
}
:deep(mark.hl-action) {
  color: #f8fafc;
  font-weight: 600;
}

mark {
  background: transparent;
  border-radius: 2px;
  padding: 0 2px;
}

/* ── 星盘速览条 ── */
.snapshotBar {
  margin-top: 32px;
  display: flex;
  justify-content: center;
  gap: 6px;
  flex-wrap: wrap;
}
.snapshotItem {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 6px 14px;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  background: rgba(255, 255, 255, 0.03);
  font-size: 13px;
}
.snapshotIcon { color: #d4af37; font-size: 14px; }
.snapshotLabel { color: #64748b; margin-right: 2px; }
.snapshotValue { color: #cbd5e1; }

/* ── 加载 / 错误 ── */
.stateCard {
  padding: 28px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(15, 23, 42, 0.72);
  backdrop-filter: blur(18px);
  border-radius: 24px;
}
.errorCard { border-color: rgba(244, 63, 94, 0.2); }
.stateTitle { font-size: 22px; color: #f8fafc; }
.stateText { margin: 12px 0 0; color: #94a3b8; }

/* ── 领域导航 ── */
.exploreNav {
  text-align: center;
}
.exploreHint {
  color: #94a3b8;
  font-size: 15px;
  margin: 0 0 14px;
}
.exploreRow {
  display: flex;
  justify-content: center;
  gap: 8px;
  flex-wrap: wrap;
}
.exploreChip {
  padding: 9px 16px;
  border-radius: 999px;
  border: 1px solid rgba(255,255,255,0.08);
  background: rgba(15,23,42,0.55);
  color: #cbd5e1;
  font-size: 14px;
  cursor: pointer;
  transition: all .2s;
}
.exploreChip:hover,
.exploreChip.active {
  border-color: rgba(212,175,55,0.3);
  background: rgba(212,175,55,0.08);
  color: #f8fafc;
}

.domainExpanded {
  margin: 24px auto 0;
  max-width: 680px;
  text-align: left;
}

/* ── AI CTA ── */
.aiCta {
  margin-top: 48px;
}
.aiCtaInner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  padding: 28px 32px;
  border-radius: 20px;
  border: 1px solid rgba(99,102,241,0.15);
  background: rgba(99,102,241,0.06);
}
.aiCtaTitle {
  margin: 0 0 6px;
  color: #f8fafc;
  font-size: 18px;
}
.aiCtaText {
  margin: 0;
  color: #94a3b8;
  font-size: 14px;
  line-height: 1.7;
}
.aiCtaBtn {
  flex-shrink: 0;
}
.aiPriceTag {
  font-size: 12px;
  opacity: 0.8;
  font-weight: 400;
}

/* ── 本命蓝图 ── */
.blueprintSection {
  margin-top: 40px;
}

/* ── 可视化区块 ── */
.vizSection {
  margin-top: 10px;
}

/* ── 技术解读折叠区 ── */
.techSection {
  margin-top: 32px;
}
.techFold {
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  background: rgba(15, 23, 42, 0.40);
  overflow: hidden;
}
.techSummary {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 16px 20px;
  cursor: pointer;
  color: #94a3b8;
  font-size: 14px;
  user-select: none;
  transition: background 0.2s;
}
.techSummary:hover {
  background: rgba(255,255,255,0.02);
}
.techSummaryIcon {
  font-size: 16px;
}
.techSummaryHint {
  margin-left: auto;
  font-size: 11px;
  color: #475569;
  letter-spacing: 0.04em;
}
.techBody {
  padding: 0 20px 20px;
}

.chartCard {
  margin: 14px 0 0;
  padding: 24px 20px;
  border-radius: 24px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(15, 23, 42, 0.55);
  backdrop-filter: blur(12px);
  text-align: center;
}

.chartCardHead {
  margin-bottom: 12px;
}

.chartCardTitle {
  margin: 0;
  color: #f8fafc;
  font-size: 18px;
}

.chartCardSub {
  display: block;
  margin-top: 4px;
  color: #64748b;
  font-size: 12px;
}

@media (max-width: 640px) {
  .aiCtaInner {
    flex-direction: column;
    text-align: center;
  }
  .snapshotBar {
    gap: 4px;
  }
  .snapshotItem {
    font-size: 12px;
    padding: 5px 10px;
  }
}

/* ── 视图切换栏 ── */
.viewModeBar {
  display: flex;
  gap: 8px;
  margin: 24px 0 16px;
  padding: 4px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 12px;
  max-width: 360px;
}
.viewModeTab {
  flex: 1;
  padding: 10px 16px;
  border: none;
  border-radius: 10px;
  background: transparent;
  color: rgba(255, 255, 255, 0.5);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}
.viewModeTab.active {
  background: rgba(99, 102, 241, 0.15);
  color: rgba(255, 255, 255, 0.9);
  font-weight: 600;
}
.viewModeTab:hover:not(.active) {
  color: rgba(255, 255, 255, 0.7);
  background: rgba(255, 255, 255, 0.03);
}
.characterChatSection { margin: 24px 0; }
.characterChatHeader {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.04);
  border-radius: 12px 12px 0 0;
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-bottom: none;
}
.characterChatDot { width: 10px; height: 10px; border-radius: 50%; }
.characterChatName {
  flex: 1;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.8);
  font-weight: 500;
}
.characterChatClose {
  background: none;
  border: none;
  color: rgba(255, 255, 255, 0.4);
  cursor: pointer;
  font-size: 16px;
  padding: 4px 8px;
  border-radius: 6px;
}
.characterChatClose:hover {
  color: rgba(255, 255, 255, 0.8);
  background: rgba(255, 255, 255, 0.06);
}
.characterHint {
  margin: 32px 0;
  padding: 32px;
  text-align: center;
  color: rgba(255, 255, 255, 0.4);
  font-size: 14px;
  border: 1px dashed rgba(255, 255, 255, 0.08);
  border-radius: 16px;
}
</style>
