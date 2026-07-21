<template>
  <div class="garden-page" :data-theme="currentTheme">
    <!-- 背景 -->
    <GardenScene />

    <!-- ═══ 加载态 ═══ -->
    <section v-if="loading" class="garden-state">
      <div class="state-icon">🌱</div>
      <h2 class="state-title">星灵花园正在打开...</h2>
      <p class="state-sub">正在连接你的星盘，邀请星灵们登场</p>
      <div class="state-spinner">
        <span
          v-for="i in 10"
          :key="i"
          class="spinner-dot"
          :style="{ animationDelay: i * 0.1 + 's', background: planetColors[i - 1] }"
        ></span>
      </div>
    </section>

    <!-- ═══ 错误态 ═══ -->
    <section v-else-if="error" class="garden-state">
      <div class="state-icon">🪐</div>
      <h2 class="state-title">花园暂时打不开</h2>
      <p class="state-sub">{{ error }}</p>
      <el-button round size="large" class="retry-btn" @click="loadGarden">重新尝试</el-button>
    </section>

    <!-- ═══ 主内容 ═══ -->
    <template v-else-if="gardenReady">
      <!-- ── Tab 内容区 ── -->
      <div class="garden-content">
        <!-- 🌸 花园 Tab -->
        <transition name="tab-fade">
          <div v-if="activeTab === 'garden'" key="garden" class="tab-panel">
            <!-- 时间仪式：晨间/午后/夜晚 -->
            <GardenRitual
              :featured-planets="featuredPlanets"
              :daily-theme="dailyTheme"
            />

            <!-- 每日低语 -->
            <DailyWhisper
              :daily-theme="dailyTheme"
              :firdaria-note="firdariaNote"
              :lunar-note="lunarNote"
              :featured-planets="featuredPlanets"
              :main-character="mainCharacter"
            />

            <!-- 每日一问 -->
            <DailyQuestion :planet-profiles="planetProfiles" />

            <!-- 灵犀一刻：水晶球交互 -->
            <MomentOracle
              :planet-profiles="planetProfiles"
              :daily-activation="dailyActivation"
              :domains="domainsData"
              @chat-with="onOracleChat"
              @share="onOracleShare"
            />

            <!-- 灵魂画像内嵌 -->
            <SoulPortrait :planet-profiles="planetProfiles" />

            <div class="garden-header">
              <div class="garden-header-row">
                <button class="glossary-trigger" @click="showGlossary = true">📖 术语</button>
                <div class="dimension-toggle">
                  <button :class="{ active: viewDimension === 'planets' }" @click="viewDimension = 'planets'">🌌 行星</button>
                  <button :class="{ active: viewDimension === 'signs' }" @click="viewDimension = 'signs'">🎭 星座</button>
                </div>
                <ThemeSwitcher :current="currentTheme" @select="onThemeChange" />
              </div>
              <h1 class="garden-title">
                <span class="title-star">⭐</span>
                {{ viewDimension === 'planets' ? '你的星灵花园' : '你的星座角色' }}
              </h1>
              <p class="garden-desc">
                {{ viewDimension === 'planets' ? '十颗行星，十位星灵——点击任意一位，听听它想对你说什么' : '十二星座，十二种人格侧面——每个星座都在你星盘里扮演不同角色' }}
              </p>
            </div>

            <div class="spirit-grid" :class="{ 'spirit-grid--signs': viewDimension === 'signs' }">
              <!-- 行星维度：星灵卡片 -->
              <template v-if="viewDimension === 'planets'">
                <SpiritBuddy
                  v-for="(spirit, i) in activeSpiritList"
                  :key="spirit.planet"
                  :planet="spirit.planet"
                  :sign="spirit.sign"
                  :gender="userGender"
                  :symbol="spirit.symbol"
                  :name="spirit.name"
                  :archetype="spirit.archetype"
                  :color="spirit.color"
                  :sign-label="spirit.signLabel"
                  :dignity-label="spirit.dignityLabel"
                  :is-featured="spirit.isFeatured"
                  :is-main="spirit.isMain"
                  :is-active="spirit.planet === activePlanet"
                  :activation-score="spirit.activationScore"
                  :float-delay="i * 0.3"
                  @select="selectSpirit(spirit)"
                />
              </template>
              <!-- 星座维度：信息卡片 -->
              <template v-else>
                <SignInfoCard
                  v-for="(card, i) in signCardList"
                  :key="card.sign"
                  :sign="card.sign"
                  :symbol="card.symbol"
                  :name="card.name"
                  :archetype="card.archetype"
                  :color="card.color"
                  :essence="card.essence"
                  :presence-score="card.presenceScore"
                  :role-tag="card.roleTag"
                  :house-cusps="card.houseCusps"
                  :planets-here="card.planetsHere"
                  :is-ascendant="card.isAscendant"
                  @view-spirit="onViewSpirit"
                />
              </template>
            </div>
          </div>
        </transition>

        <!-- 📜 宝典 Tab -->
        <transition name="tab-fade">
          <div v-if="activeTab === 'codex'" key="codex" class="tab-panel">
            <SpiritCodex
              :planet-profiles="planetProfiles"
              :domains="domainsData"
              @chat-with="onCodexChat"
              @share="onCodexShare"
            />
          </div>
        </transition>

        <!-- 💎 日记 Tab -->
        <transition name="tab-fade">
          <div v-if="activeTab === 'journal'" key="journal" class="tab-panel">
            <WeeklyReport :planet-profiles="planetProfiles" :active-report-id="activeReportId" />
            <GardenJournal
              :planet-profiles="planetProfiles"
              :active-report-id="activeReportId"
            />
          </div>
        </transition>

        <!-- 🔮 议会 Tab -->
        <transition name="tab-fade">
          <div v-if="activeTab === 'council'" key="council" class="tab-panel">
            <SpiritCouncil
              :planet-profiles="planetProfiles"
              :domains="domainsData"
              :report-id="activeReportId"
            />
          </div>
        </transition>
      </div>

      <!-- ═══ Overlay: 星灵详情 / 聊天 ═══ -->
      <transition name="overlay-fade">
        <div class="overlay-backdrop" v-if="selectedSpirit" @click.self="closeOverlay">
          <div class="overlay-content">
            <SpiritDetailCard
              v-if="!isChatting"
              :visible="!!selectedSpirit"
              :planet="selectedSpirit.planet"
              :symbol="selectedSpirit.symbol"
              :name="selectedSpirit.name"
              :archetype="selectedSpirit.archetype"
              :color="selectedSpirit.color"
              :essence="selectedSpirit.essence"
              :greeting="selectedSpirit.greeting"
              :persona-description="selectedSpirit.personaDescription"
              :sign-label="selectedSpirit.signLabel"
              :sign-element="selectedSpirit.signElement"
              :sign-modality="selectedSpirit.signModality"
              :sign-voice="selectedSpirit.signVoice"
              :house="selectedSpirit.house"
              :house-label="selectedSpirit.houseLabel"
              :dignity-code="selectedSpirit.dignityCode"
              :dignity-label="selectedSpirit.dignityLabel"
              :role-tag="selectedSpirit.roleTag"
              :core-strength="selectedSpirit.coreStrength"
              :is-chart-ruler="selectedSpirit.isChartRuler"
              @close="closeOverlay"
              @chat="isChatting = true"
            />

            <SpiritChatBubble
              v-if="isChatting"
              :visible="isChatting"
              :symbol="selectedSpirit.symbol"
              :name="selectedSpirit.name"
              :archetype="selectedSpirit.archetype"
              :color="selectedSpirit.color"
              :greeting="selectedSpirit.greeting"
              :planet="selectedSpirit.planet"
              :report-id="activeReportId"
              :entry-context="chatEntryContext"
              @close="onChatClosed"
            />
          </div>
        </div>
      </transition>

      <!-- 底部 Tab 导航 -->
      <TabBar :active-tab="activeTab" @select="switchTab" />

      <!-- ═══ SpiritGlossary: 术语词典 ═══ -->
      <SpiritGlossary :visible="showGlossary" @close="showGlossary = false" />

      <!-- ═══ WelcomeGuide: 首次引导 ═══ -->
      <WelcomeGuide
        :planet-profiles="planetProfiles"
        @done="guideDone = true"
      />

      <!-- ═══ ShareCard: 分享卡片 ═══ -->
      <ShareCard
        v-if="shareData"
        :visible="!!shareData"
        :symbol="shareData.symbol"
        :name="shareData.name"
        :archetype="shareData.archetype"
        :color="shareData.color"
        :message="shareData.message"
        :sign-label="shareData.signLabel"
        :house-label="shareData.houseLabel"
        @close="shareData = null"
      />
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { apiClient } from "@/config/api";
import { FEATURED_EXAMPLES } from "@/config/examples";
import { SIGN_EMOJI_MAP, PLANET_COLORS_CLASSICAL, PLANET_LABELS, PLANET_COLORS_MAP, PLANET_SYMBOLS } from "@/config/zodiac";
import type {
  PlanetCharacterProfile,
  PlanetCharacterProfilesData,
  PlanetDailyActivation,
  FeaturedPlanet,
  DomainReport,
} from "@/utils/types";
import GardenScene from "./components/GardenScene.vue";
import GardenRitual from "./components/GardenRitual.vue";
import DailyWhisper from "./components/DailyWhisper.vue";
import MomentOracle from "./components/MomentOracle.vue";
import SoulPortrait from "./components/SoulPortrait.vue";
import SpiritBuddy from "./components/SpiritBuddy.vue";
import SignInfoCard from "./components/SignInfoCard.vue";
import SpiritDetailCard from "./components/SpiritDetailCard.vue";
import SpiritChatBubble from "./components/SpiritChatBubble.vue";
import SpiritCodex from "./components/SpiritCodex.vue";
import SpiritCouncil from "./components/SpiritCouncil.vue";
import GardenJournal from "./components/GardenJournal.vue";
import WelcomeGuide from "./components/WelcomeGuide.vue";
import DailyQuestion from "./components/DailyQuestion.vue";
import SpiritGlossary from "./components/SpiritGlossary.vue";
import WeeklyReport from "./components/WeeklyReport.vue";
import ShareCard from "./components/ShareCard.vue";
import ThemeSwitcher from "./components/ThemeSwitcher.vue";
import TabBar from "./components/TabBar.vue";

const route = useRoute();
const router = useRouter();

const loading = ref(true);
const error = ref("");
const activeReportId = ref("");
const activeTab = ref("garden");
const viewDimension = ref<"planets" | "signs">("planets");

const planetProfiles = ref<PlanetCharacterProfilesData | null>(null);
const characterProfiles = ref<any>(null); // 12 星座角色数据
const dailyActivation = ref<PlanetDailyActivation | null>(null);
const domainsData = ref<Record<string, DomainReport> | null>(null);

// 12 星座符号常量（从共享配置导入）
const SIGN_SYMBOLS = SIGN_EMOJI_MAP;

const activePlanet = ref("");
const selectedSpirit = ref<SpiritDisplay | null>(null);
const isChatting = ref(false);
const chatEntryContext = ref<Record<string, any> | undefined>(undefined);
const guideDone = ref(false);
const showGlossary = ref(false);
const currentTheme = ref(
  localStorage.getItem("spirit_garden_theme") || "cream"
);

// 用户星盘信息（用于匹配 24 张太阳星灵图片）
const sunSign = computed(() => {
  const sun = planetProfiles.value?.planet_characters?.["SUN"];
  return (sun as any)?.sign || "";
});
const userGender = computed(() => ""); // 从 report 的 user_info 获取，后续接入
const shareData = ref<{
  symbol: string; name: string; archetype: string; color: string;
  message: string; signLabel?: string; houseLabel?: string;
} | null>(null);

const planetColors = PLANET_COLORS_CLASSICAL

async function loadGarden() {
  loading.value = true;
  error.value = "";

  try {
    const reportId = (route.params.id || route.query.id) as string | undefined;
    const exampleKey = route.query.example as string | undefined;

    let data: any = null;

    if (reportId) {
      const res = await apiClient.get<any>(`/analyses/${reportId}`);
      if (res.data?.status === "success") {
        data = res.data.data;
        activeReportId.value = reportId;
      }
    }

    if (!data && exampleKey) {
      const ex = FEATURED_EXAMPLES.find((e) => e.key === exampleKey);
      if (ex) {
        const res = await apiClient.post<any>("/analyses", {
          analysis_type: "natal_blueprint",
          subjects: [
            {
              name: ex.name,
              gender: ex.gender,
              birth_time: ex.birthTime,
              lat: ex.latitude,
              lon: ex.longitude,
              timezone: ex.timezone,
            },
          ],
        });
        if (res.data?.status === "success") {
          data = res.data.data;
          activeReportId.value = res.data.report_id || "";
        }
      }
    }

    if (!data) {
      const fb = await apiClient.post<any>("/analyses", {
        analysis_type: "natal_blueprint",
        subjects: [
          {
            name: "夏天",
            gender: "女",
            birth_time: "1991-03-21T09:25:00",
            lat: 35.7,
            lon: 113.35,
            timezone: 8,
          },
        ],
      });
      if (fb.data?.status === "success") {
        data = fb.data.data;
        activeReportId.value = fb.data.report_id || "";
      }
    }

    if (!data) {
      error.value = "无法加载星盘数据，请稍后重试。";
      return;
    }

    planetProfiles.value = data.planet_characters || null;
    characterProfiles.value = data.characters || null;
    domainsData.value = data.domains || null;

    if (activeReportId.value) {
      try {
        const dailyRes = await apiClient.get(
          `/characters/${activeReportId.value}/daily`
        );
        if (dailyRes.data?.status === "success") {
          dailyActivation.value = dailyRes.data.data;
        }
      } catch {
        // 每日激活数据暂不可用
      }
    }
  } catch (err) {
    console.error(err);
    error.value = "无法加载星盘数据，请检查后端服务。";
  } finally {
    loading.value = false;
  }
}

onMounted(() => loadGarden());

const gardenReady = computed(() => !loading.value && !error.value);
const dailyTheme = computed(() => dailyActivation.value?.daily_theme || "");
const firdariaNote = computed(() => dailyActivation.value?.firdaria_note || "");
const lunarNote = computed(() => dailyActivation.value?.lunar_note || "");
const featuredPlanets = computed<FeaturedPlanet[]>(
  () => dailyActivation.value?.featured_planets || []
);
const mainCharacter = computed<FeaturedPlanet | null>(
  () => dailyActivation.value?.main_character || null
);

// ── 星灵展示数据 ──

interface SpiritDisplay {
  planet: string;
  sign: string;  // 星座 key，如 "LEO"
  symbol: string;
  name: string;
  archetype: string;
  color: string;
  essence: string;
  greeting: string;
  personaDescription: string;
  signLabel: string;
  signElement: string;
  signModality: string;
  signVoice: string;
  house: number;
  houseLabel: string;
  dignityCode: string;
  dignityLabel: string;
  roleTag: string;
  coreStrength: number;
  isChartRuler: boolean;
  isFeatured: boolean;
  isMain: boolean;
  activationScore: number | null;
}

const spiritList = computed<SpiritDisplay[]>(() => {
  const profiles = planetProfiles.value?.planet_characters || {};
  const activationScores = dailyActivation.value?.activation_scores || {};
  const featured = new Set(
    (dailyActivation.value?.featured_planets || []).map((f) => f.planet)
  );

  const order = ["SUN", "MOON", "MERCURY", "VENUS", "MARS", "JUPITER", "SATURN"];

  return order
    .map((planetKey) => {
      const profile = profiles[planetKey] as PlanetCharacterProfile | undefined;
      if (!profile) return null;
      const persona = profile.persona;
      const signFlavor = profile.sign_flavor;
      const houseCtx = profile.house_context;

      return {
        planet: planetKey,
        sign: profile.sign || "",
        symbol: persona?.symbol || "●",
        name: persona?.name_zh || planetKey,
        archetype: persona?.archetype_zh || "",
        color: persona?.visual_color || "#999",
        essence: persona?.essence || "",
        greeting: profile.personalized_greeting || "",
        personaDescription: persona?.personality?.slice(0, 80) + "..." || "",
        signLabel: profile.sign_label || "",
        signElement: signFlavor?.element || "",
        signModality: signFlavor?.modality || "",
        signVoice: signFlavor?.voice_tone?.slice(0, 40) || "",
        house: profile.house || 1,
        houseLabel: houseCtx?.title || profile.house_label || "",
        dignityCode: profile.dignity_code || "",
        dignityLabel: profile.dignity_label || "",
        roleTag: profile.role_tag || "",
        coreStrength: Math.round(profile.core_strength || 0),
        isChartRuler: profile.is_chart_ruler || false,
        isFeatured: featured.has(planetKey),
        isMain: planetKey === "SUN",
        activationScore:
          activationScores[planetKey] !== undefined
            ? activationScores[planetKey]
            : null,
      };
    })
    .filter(Boolean) as SpiritDisplay[];
});

// 12 星座角色列表（归一化为 SpiritDisplay）
const signSpiritList = computed<SpiritDisplay[]>(() => {
  const chars = characterProfiles.value?.characters || {};
  const activationScores = dailyActivation.value?.activation_scores || {};
  const featuredSet = new Set(
    (dailyActivation.value?.featured_characters || []).map((f: any) => f.sign)
  );

  const order = [
    "ARIES", "TAURUS", "GEMINI", "CANCER",
    "LEO", "VIRGO", "LIBRA", "SCORPIO",
    "SAGITTARIUS", "CAPRICORN", "AQUARIUS", "PISCES",
  ];

  return order
    .map((signKey) => {
      const ch = chars[signKey.toLowerCase()] || chars[signKey];
      if (!ch) return null;
      const p = ch.persona || {};
      const houseCusps = ch.house_cusps_here || [];
      const domains = ch.linked_domains || [];

      return {
        planet: signKey,
        sign: signKey,
        symbol: SIGN_SYMBOLS[signKey] || "◇",
        name: p.name || signKey,
        archetype: p.archetype || "",
        color: p.visual_color || "#999",
        essence: p.essence || "",
        greeting: ch.personalized_greeting || "",
        personaDescription: p.personality?.slice(0, 80) + "..." || "",
        signLabel: p.name || "",
        signElement: p.element || "",
        signModality: p.modality || "",
        signVoice: p.voice_tone?.slice(0, 40) || "",
        house: houseCusps[0] || 1,
        houseLabel: houseCusps.length ? `第${houseCusps[0]}宫` : domains[0] || "",
        dignityCode: "",
        dignityLabel: ch.role_tag || "",
        roleTag: ch.role_tag || "",
        coreStrength: Math.round(ch.presence_score || 0),
        isChartRuler: ch.is_ascendant || false,
        isFeatured: featuredSet.has(signKey),
        isMain: ch.is_ascendant || false,
        activationScore: activationScores[signKey] !== undefined ? activationScores[signKey] : null,
      };
    })
    .filter(Boolean) as SpiritDisplay[];
});

const activeSpiritList = computed(() => spiritList.value);

// 星座信息卡片列表（含落入星体详情）
const signCardList = computed(() => {
  const chars = characterProfiles.value?.characters || {};
  const order = [
    "ARIES", "TAURUS", "GEMINI", "CANCER",
    "LEO", "VIRGO", "LIBRA", "SCORPIO",
    "SAGITTARIUS", "CAPRICORN", "AQUARIUS", "PISCES",
  ];
  return order
    .map((signKey) => {
      const ch = chars[signKey.toLowerCase()] || chars[signKey];
      if (!ch) return null;
      const p = ch.persona || {};
      const houseCusps: number[] = ch.house_cusps_here || [];
      const planetsHereRaw: string[] = ch.planets_here || [];
      const planetsDignity: Record<string, string> = ch.planets_dignity || {};

      const planetsHere = planetsHereRaw.map((plKey: string) => ({
        planet: plKey,
        label: (PLANET_LABELS as Record<string, string>)[plKey] || plKey,
        symbol: (PLANET_SYMBOLS as Record<string, string>)[plKey] || "●",
        color: (PLANET_COLORS_MAP as Record<string, string>)[plKey] || "#999",
        dignity: planetsDignity[plKey] || "",
      }));

      return {
        sign: signKey,
        symbol: (SIGN_SYMBOLS as Record<string, string>)[signKey] || "◇",
        name: (p as any).name || signKey,
        archetype: (p as any).archetype || "",
        color: (p as any).visual_color || "#999",
        essence: (p as any).essence || "",
        presenceScore: Math.round(ch.presence_score || 0),
        roleTag: ch.role_tag || "",
        houseCusps,
        planetsHere,
        isAscendant: ch.is_ascendant || false,
      };
    })
    .filter(Boolean);
});

function onViewSpirit(planet: string) {
  // 从星座卡片跳转到对应的星灵 — 只展示详情卡，不自动对话
  viewDimension.value = "planets";
  const spirit = spiritList.value.find((s) => s.planet === planet);
  if (spirit) {
    selectSpirit(spirit);
    // 不设置 isChatting = true，用户看到详情卡后自主决定是否对话
  }
}

function selectSpirit(spirit: SpiritDisplay) {
  activePlanet.value = spirit.planet;
  selectedSpirit.value = spirit;
  isChatting.value = false;
  chatEntryContext.value = { source: "garden" };
  // 记录到 localStorage（花园日记用）
  recordChatHistory(spirit.planet);
}

function closeOverlay() {
  selectedSpirit.value = null;
  isChatting.value = false;
}

async function onChatClosed(messages: Array<{ role: "user" | "spirit"; text: string }>) {
  // 写入星灵日记
  if (messages.length > 0 && activeReportId.value && selectedSpirit.value) {
    try {
      // 将对话拼接为 chat_context 字符串
      const chatContext = messages
        .map((m) => `${m.role === "user" ? "用户" : selectedSpirit.value!.name}：${m.text.slice(0, 300)}`)
        .join("\n");
      await apiClient.post(`/spirit-diary/${activeReportId.value}/entry`, {
        chat_context: chatContext,
        spirit_planet: selectedSpirit.value.planet,
        mood_emoji: "",
      });
    } catch {
      // 日记保存失败不阻塞
    }
  }
  isChatting.value = false;
}

function onOracleChat(planet: string) {
  const spirit = spiritList.value.find((s) => s.planet === planet);
  if (spirit) {
    selectSpirit(spirit);
    isChatting.value = true;
  }
}

function onCodexChat(planet: string) {
  const spirit = spiritList.value.find((s) => s.planet === planet);
  if (spirit) {
    selectSpirit(spirit);
    isChatting.value = true;
  }
}

function onOracleShare(result: any) {
  const spirit = spiritList.value.find((s) => s.planet === result.planet);
  shareData.value = {
    symbol: result.symbol,
    name: result.name,
    archetype: result.archetype,
    color: result.color,
    message: result.message,
    signLabel: spirit?.signLabel || "",
    houseLabel: spirit?.houseLabel || "",
  };
}

function onCodexShare(data: { symbol: string; name: string; archetype: string; color: string; message: string }) {
  shareData.value = { ...data, signLabel: "", houseLabel: "" };
}

function onThemeChange(key: string) {
  currentTheme.value = key;
  localStorage.setItem("spirit_garden_theme", key);
}

function switchTab(key: string) {
  activeTab.value = key;
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function recordChatHistory(planet: string) {
  try {
    const key = `spirit_garden_${activeReportId.value}`;
    const raw = localStorage.getItem(key);
    const data = raw ? JSON.parse(raw) : { chats: [] };
    data.chats.push({
      planet,
      timestamp: Date.now(),
      snippet: `和${planet}的对话`,
    });
    if (data.chats.length > 100) {
      data.chats = data.chats.slice(-100);
    }
    localStorage.setItem(key, JSON.stringify(data));
  } catch {
    // ignore storage errors
  }
}
</script>

<style scoped>
.garden-page {
  min-height: calc(100vh - var(--h-header));
  position: relative;
  overflow-x: hidden;
  scroll-behavior: smooth;
}

/* ── 加载/错误态 ── */
.garden-state {
  position: relative;
  z-index: 1;
  text-align: center;
  padding: 80px 20px;
}
.state-icon {
  font-size: 52px;
  margin-bottom: 16px;
  animation: float 3s ease-in-out infinite;
}
@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}
.state-title {
  font-size: 22px;
  font-weight: 700;
  color: #4a3728;
  margin: 0 0 8px;
}
.state-sub {
  font-size: 14px;
  color: #8b7355;
  margin: 0 0 24px;
}
.state-spinner {
  display: flex;
  justify-content: center;
  gap: 10px;
}
.spinner-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  animation: dot-bounce 1.2s ease-in-out infinite;
}
@keyframes dot-bounce {
  0%, 100% { transform: translateY(0); opacity: 0.4; }
  50% { transform: translateY(-16px); opacity: 1; }
}
.retry-btn {
  background: rgba(255, 154, 139, 0.2) !important;
  border-color: rgba(255, 154, 139, 0.3) !important;
  color: #4a3728 !important;
}

/* ── 内容区 ── */
.garden-content {
  position: relative;
  z-index: 1;
  max-width: 680px;
  margin: 0 auto;
  padding: 36px 20px 100px;
}

/* ── Tab 过渡 ── */
.tab-fade-enter-active,
.tab-fade-leave-active {
  transition: all 0.25s ease;
}
.tab-fade-enter-from {
  opacity: 0;
  transform: translateY(8px);
}
.tab-fade-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

.tab-panel {
  display: flex;
  flex-direction: column;
  gap: 28px;
}

/* ── 花园 Tab ── */
.garden-header {
  text-align: center;
}
.garden-header-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}
.glossary-trigger {
  padding: 6px 14px; border-radius: 14px; border: 1px solid rgba(0,0,0,0.08);
  background: rgba(255,255,255,0.6); font-size: 12px; font-weight: 600;
  color: #8b7355; cursor: pointer; font-family: inherit; transition: all 0.2s;
}
.glossary-trigger:hover { background: rgba(255,255,255,0.9); color: #4a3728; }

/* 维度切换 */
.dimension-toggle {
  display: flex; border-radius: 14px; overflow: hidden;
  border: 1px solid rgba(0,0,0,0.06); background: rgba(255,255,255,0.5);
}
.dimension-toggle button {
  padding: 6px 14px; border: none; background: transparent;
  font-size: 12px; font-weight: 600; color: #a89880;
  cursor: pointer; font-family: inherit; transition: all 0.2s;
}
.dimension-toggle button.active {
  background: rgba(255,154,139,0.15); color: #4a3728;
}

/* ── 主题变量 ── */
.garden-page[data-theme="cream"] {
  --garden-bg-1: #FFF5EE;
  --garden-bg-2: #FFF0F5;
  --garden-card-bg: rgba(255,255,255,0.75);
  --garden-text: #4A3728;
  --garden-text-soft: #8B7355;
  --garden-accent: #FF9A8B;
}
.garden-page[data-theme="night"] {
  --garden-bg-1: #1a1a2e;
  --garden-bg-2: #16213e;
  --garden-card-bg: rgba(30,30,60,0.75);
  --garden-text: #E8E0F0;
  --garden-text-soft: #A098B8;
  --garden-accent: #9B8EC4;
}
.garden-page[data-theme="sakura"] {
  --garden-bg-1: #FFF0F5;
  --garden-bg-2: #FDE8EF;
  --garden-card-bg: rgba(255,255,255,0.75);
  --garden-text: #5C3D4A;
  --garden-text-soft: #9B7B8A;
  --garden-accent: #F4A7B9;
}
.garden-title {
  font-size: 26px;
  font-weight: 700;
  color: #4a3728;
  margin: 0 0 8px;
}
.title-star {
  display: inline-block;
  animation: star-spin 3s linear infinite;
}
@keyframes star-spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
.garden-desc {
  font-size: 14px;
  color: #8b7355;
  margin: 0;
}

.spirit-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}
.spirit-grid > :first-child {
  grid-column: 1 / -1;
  max-width: 260px;
  justify-self: center;
}
/* 12 星座用 3 列网格 */
.spirit-grid--signs {
  grid-template-columns: repeat(3, 1fr) !important;
}
.spirit-grid--signs > :first-child {
  grid-column: auto;
  max-width: none;
  justify-self: auto;
}

/* ── Overlay ── */
.overlay-backdrop {
  position: fixed;
  inset: 0;
  z-index: 200;
  background: rgba(0, 0, 0, 0.15);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}
.overlay-content {
  width: 100%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
  border-radius: 28px;
}
.overlay-content::-webkit-scrollbar {
  width: 4px;
}
.overlay-fade-enter-active {
  transition: all 0.3s ease;
}
.overlay-fade-leave-active {
  transition: all 0.2s ease;
}
.overlay-fade-enter-from {
  opacity: 0;
}
.overlay-fade-enter-from .overlay-content {
  transform: scale(0.95) translateY(20px);
}
.overlay-fade-leave-to {
  opacity: 0;
}

/* ── 响应式 ── */
@media (max-width: 640px) {
  .spirit-grid {
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
  }
  .spirit-grid > :first-child {
    grid-column: 1 / -1;
    max-width: 220px;
  }
  .garden-content {
    padding: 24px 14px 100px;
  }
  .garden-title {
    font-size: 22px;
  }
}

@media (max-width: 400px) {
  .spirit-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
  }
}
</style>
