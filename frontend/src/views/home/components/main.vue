<template>
  <div class="main-page" :data-theme="currentTheme">
    <!-- ═══ 视频全屏背景 ═══ -->
    <div class="video-layer">
      <transition name="video-cross" mode="out-in">
        <video
          v-if="homeData.currentSignVideo.value"
          ref="videoRef"
          :key="homeData.currentSignVideo.value"
          :src="homeData.currentSignVideo.value"
          class="bg-video"
          autoplay loop playsinline
          :muted="videoMuted"
        />
      </transition>
      <!-- 渐变遮罩 -->
      <div class="video-overlay-top"></div>
      <div class="video-overlay-bottom"></div>
      <!-- 声音切换 -->
      <button class="sound-toggle" @click="toggleSound" :title="videoMuted ? '开启声音' : '静音'">
        {{ videoMuted ? '🔇' : '🔊' }}
      </button>
    </div>

    <GardenScene transparent />

    <!-- ═══ 加载态 ═══ -->
    <section v-if="homeData.loading.value" class="garden-state">
      <div class="state-icon">🌸</div>
      <h2 class="state-title">星灵花园正在打开...</h2>
      <p class="state-sub">正在连接你的星盘，邀请星灵们登场</p>
      <div class="state-spinner">
        <span v-for="i in 10" :key="i" class="spinner-dot"
          :style="{ animationDelay: i * 0.12 + 's', background: planetColors[i - 1] }"
        ></span>
      </div>
    </section>

    <!-- ═══ 错误态 ═══ -->
    <section v-else-if="homeData.error.value" class="garden-state">
      <div class="state-icon">🪐</div>
      <h2 class="state-title">花园暂时打不开</h2>
      <p class="state-sub">{{ homeData.error.value }}</p>
      <el-button round size="large" class="retry-btn" @click="homeData.refreshData()">重新尝试</el-button>
    </section>

    <!-- ═══ 登录引导: 未登录且 demo 数据加载完成 ═══ -->
    <section v-else-if="!isLoggedIn && !homeData.loading.value" class="garden-state login-guide">
      <div class="state-icon">🔮</div>
      <h2 class="state-title">欢迎来到星灵花园</h2>
      <p class="state-sub">登录解锁专属星盘，与你的星灵对话</p>
      <el-button round size="large" class="login-guide-btn" @click="startLogin">登录</el-button>
      <p class="login-guide-hint">你也可以继续浏览 Demo 星盘</p>
    </section>

    <!-- ═══ 主内容 ═══ -->
    <template v-else>
      <!-- 顶栏：悬浮于视频之上 -->
      <div class="top-bar top-bar--three" v-if="homeData.hasProfile.value">
        <!-- 左：用户头像 -->
        <button class="avatar-trigger" @click="showProfile = true">
          <SpiritAvatar planet="SUN" :sign="homeData.sunSign.value" :gender="homeData.userGender.value" size="sm" />
        </button>

        <!-- 中：今日星灵 -->
        <StarSpiritDisplay
          v-if="homeData.todayStarSpirit.value"
          :planet="homeData.todayStarSpirit.value.planet"
          :planet-name="homeData.todayStarSpirit.value.planet_label"
          :planet-sign="homeData.todayStarSpirit.value.sign_label"
          :symbol="homeData.todayStarSpirit.value.symbol"
          :color="homeData.todaysPlanetProfile?.value?.persona?.visual_color || '#F2A900'"
          :gender="homeData.userGender.value"
          @chat="openStarSpiritChat"
        />

        <!-- 右：今日走向 -->
        <button class="direction-trigger" @click="openDirection">
          <span class="direction-icon">📡</span>
          <span class="direction-label">今日走向</span>
        </button>

        <ThemeSwitcher :current="currentTheme" @select="(k: string) => currentTheme = k" />
      </div>

      <!-- ═══ 底部导航栏 ═══ -->
      <HomeTabBar
        v-if="homeData.hasProfile.value"
        @garden="goGarden"
        @daily-question="openDailyQuestion"
        @council="openCouncil"
      />

      <!-- ═══ Profile 浮层 ═══ -->
      <ProfileOverlay
        :visible="showProfile"
        :display-name="homeData.userName.value"
        :sun-sign="homeData.sunSign.value"
        :sun-sign-emoji="homeData.sunSignEmoji.value"
        :sun-sign-label="homeData.sunSignLabel.value"
        :asc-sign-label="homeData.ascSignLabel.value"
        :moon-sign-label="homeData.moonSignLabel.value"
        :gender="homeData.userGender.value"
        @close="showProfile = false"
        @go-garden="goGarden"
        @go-history="goHistory"
        @go-onboarding="goOnboarding"
        @go-profile="goProfile"
        @go-diary="goDiary"
        @logout="doLogout"
      />

      <!-- ═══ 聊天浮层 ═══ -->
      <transition name="overlay-fade">
        <div v-if="chatVisible" class="overlay-backdrop" @click.self="handleBackdropClose">
          <div class="overlay-content">
            <SpiritChatBubble
              ref="chatBubbleRef"
              :visible="chatVisible"
              :planet="chatPlanet"
              :symbol="chatSymbol"
              :name="chatName"
              :archetype="chatArchetype"
              :color="chatColor"
              :greeting="chatGreeting"
              :report-id="homeData.reportId.value"
              :entry-context="chatEntryContext"
              @close="closeChatAndGenerateDiary"
            />
          </div>
        </div>
      </transition>

      <!-- ═══ 星灵议会 浮层 ═══ -->
      <HomeCouncil
        :visible="showCouncil"
        :planet-list="homeData.councilPlanetList.value"
        :sign-list="homeData.councilSignList.value"
        :gender="homeData.userGender.value"
        :active-planet="homeData.activePlanet.value"
        :active-sign="homeData.activeSign.value"
        @close="showCouncil = false"
        @chat-with-planet="onCouncilPlanetChat"
        @chat-with-sign="onCouncilSignChat"
        @select-planet="homeData.setActivePlanet"
        @select-sign="homeData.setActiveSign"
      />

      <!-- ═══ 灵犀一问 ═══ -->
      <SpiritOracle
        :visible="showDailyQuestion"
        :today-star-spirit="homeData.todayStarSpirit.value"
        :daily-question="homeData.dailyQuestion.value"
        :spirit-profile="homeData.todaysPlanetProfile?.value"
        :gender="homeData.userGender.value"
        @chat="openStarSpiritChat"
        @close="showDailyQuestion = false"
      />

      <!-- ═══ 星灵日记 ═══ -->
      <StarSpiritDiary
        :visible="showDiary"
        :entries="homeData.diaryEntries.value"
        :loading="false"
        @close="showDiary = false"
      />

      <!-- ═══ 今日走向 ═══ -->
      <TodayDirection
        :visible="showDirection"
        :transit-report="homeData.dailyTransitReport.value"
        :today-star-spirit="homeData.todayStarSpirit.value"
        :date-label="homeData.dateLabel.value"
        @close="showDirection = false"
        @chat-with-spirit="onTransitChat($event.planet, $event.detail)"
      />

      <!-- ═══ 新人引导 ═══ -->
      <OnboardingFlow
        :visible="showOnboarding"
        :today-star-spirit="homeData.todayStarSpirit.value"
        :todays-planet-profile="homeData.todaysPlanetProfile?.value"
        :daily-question="homeData.dailyQuestion.value?.question || ''"
        @close="showOnboarding = false"
      />
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick } from "vue";
import { useRouter } from "vue-router";
import { useHomeData } from "@/composables/useHomeData";
import { useAuth } from "@/utils/auth";
import { PLANET_COLORS } from "@/config/zodiac";
import { apiClient } from "@/config/api";
import GardenScene from "@/views/Wanxiang/components/GardenScene.vue";
import SpiritAvatar from "@/views/Wanxiang/components/SpiritAvatar.vue";
import SpiritChatBubble from "@/views/Wanxiang/components/SpiritChatBubble.vue";
import ThemeSwitcher from "@/views/Wanxiang/components/ThemeSwitcher.vue";
import HomeTabBar from "./HomeTabBar.vue";
import ProfileOverlay from "./ProfileOverlay.vue";
import HomeCouncil from "./HomeCouncil.vue";
import StarSpiritDisplay from "./StarSpiritDisplay.vue";
import SpiritOracle from "./SpiritOracle.vue";
import StarSpiritDiary from "./StarSpiritDiary.vue";
import TodayDirection from "./TodayDirection.vue";
import OnboardingFlow from "./OnboardingFlow.vue";

const router = useRouter();
const homeData = useHomeData();
const { isLoggedIn } = useAuth();

function startLogin() { router.push("/login"); }

// ── 主题 ──
const currentTheme = ref(localStorage.getItem("spirit_garden_theme") || "cream");

// ── 视频声音 ──
const videoRef = ref<HTMLVideoElement | null>(null);
const videoMuted = ref(true); // 默认静音以兼容 autoplay 策略

function toggleSound() {
  videoMuted.value = !videoMuted.value;
  if (!videoMuted.value && videoRef.value) {
    videoRef.value.muted = false;
    videoRef.value.play().catch(() => {
      // 浏览器阻止有声播放，回退静音
      videoMuted.value = true;
    });
  }
}

// 视频切换后尝试有声播放
watch(() => homeData.currentSignVideo.value, () => {
  nextTick(() => {
    if (videoRef.value && !videoMuted.value) {
      videoRef.value.muted = false;
      videoRef.value.play().catch(() => {});
    }
  });
});

// 加载完成后检查是否显示新用户引导
watch(() => homeData.loading.value, (loading) => {
  if (!loading) {
    const profileDone = localStorage.getItem("spirit_profile_completed");
    if (!profileDone) {
      showOnboarding.value = true;
    }
  }
}, { immediate: true });

// ── 色板 (spinner 用) ──
const planetColors = PLANET_COLORS;

// ── UI 浮层状态 ──
const showProfile = ref(false);
const showCouncil = ref(false);
const showDailyQuestion = ref(false);
const showDiary = ref(false);
const showDirection = ref(false);
const chatVisible = ref(false);
const showOnboarding = ref(false);

// ── 面板互斥：打开一个时关闭其他 ──
function openDailyQuestion() {
  showDirection.value = false;
  showCouncil.value = false;
  showDailyQuestion.value = true;
}

function openCouncil() {
  showDirection.value = false;
  showDailyQuestion.value = false;
  showCouncil.value = true;
}

function openDirection() {
  showDailyQuestion.value = false;
  showCouncil.value = false;
  showDirection.value = true;
}

// ── 聊天目标 ──
const chatPlanet = ref("SUN");
const chatSymbol = ref("☉");
const chatName = ref("太阳");
const chatArchetype = ref("");
const chatColor = ref("#F2A900");
const chatGreeting = ref("");

// ── 聊天入口上下文 & 计数 ──
const chatEntryContext = ref<{
  source: string;
  transit_planet?: string;
  transit_detail?: string;
  daily_question?: string;
  previous_spirit?: string;
  previous_chats_today?: number;
}>({ source: "" });
const todayChatCounts = ref<Record<string, number>>({});
const chatBubbleRef = ref<any>(null);

// ═══════════════════════════════════════
// 视频随星灵动态切换
// ═══════════════════════════════════════

function openChat() {
  const sp = homeData.sunProfile.value;
  chatPlanet.value = "SUN";
  chatSymbol.value = sp?.persona?.symbol || "☉";
  chatName.value = homeData.sunName.value;
  chatArchetype.value = homeData.sunArchetype.value;
  chatColor.value = homeData.sunColor.value;
  chatGreeting.value = sp?.personalized_greeting || "";
  homeData.setActivePlanet("SUN");
  chatVisible.value = true;
}

function openStarSpiritChat() {
  const ss = homeData.todayStarSpirit.value;
  if (!ss) {
    openChat();
    return;
  }
  chatPlanet.value = ss.planet;
  chatSymbol.value = ss.symbol || "★";
  chatName.value = ss.planet_label || "星灵";
  chatArchetype.value = ss.sign_label || "";
  chatColor.value = homeData.todaysPlanetProfile?.value?.persona?.visual_color || "#F2A900";
  chatGreeting.value = "";
  chatEntryContext.value = {
    source: "today_star_spirit",
    daily_question: homeData.dailyQuestion.value?.question || "",
    previous_chats_today: todayChatCounts.value[ss.planet] || 0,
  };
  todayChatCounts.value[ss.planet] = (todayChatCounts.value[ss.planet] || 0) + 1;
  homeData.setActivePlanet(ss.planet);
  showDailyQuestion.value = false;
  chatVisible.value = true;
}

function onCouncilPlanetChat(p: any) {
  chatPlanet.value = p.planet;
  chatSymbol.value = p.symbol;
  chatName.value = p.shortName;
  chatArchetype.value = p.archetypeShort;
  chatColor.value = p.color;
  chatGreeting.value = p.greeting;
  chatEntryContext.value = {
    source: "council",
    previous_chats_today: todayChatCounts.value[p.planet] || 0,
  };
  todayChatCounts.value[p.planet] = (todayChatCounts.value[p.planet] || 0) + 1;
  // 切换视频到该星灵落座星座
  homeData.setActivePlanet(p.planet);
  showCouncil.value = false;
  chatVisible.value = true;
}

function onCouncilSignChat(s: any) {
  chatPlanet.value = "SUN";
  chatSymbol.value = s.emoji;
  chatName.value = s.name;
  chatArchetype.value = `${s.element}象 · ${s.hasPlanets ? '已有星体落座' : '潜在能量'}`;
  chatColor.value = s.color;
  chatGreeting.value = s.hasPlanets
    ? `你好呀，我是${s.name}——你的星盘里有一些行星落在我这里，让我跟你聊聊这意味着什么。`
    : `虽然你的星盘里暂时没有行星落在${s.name}，但这不代表你没有这份能量。让我告诉你${s.name}的本质，也许你会发现你早就拥有了它。`;
  homeData.setActiveSign(s.key);
  showCouncil.value = false;
  chatVisible.value = true;
}

async function closeChatAndGenerateDiary(msgs: Array<{ role: string; text: string }>) {
  if (msgs && msgs.length > 0 && chatPlanet.value && homeData.reportId.value) {
    try {
      const chatContext = msgs.map((m) => ({
        role: m.role,
        text: m.text,
      }));
      await apiClient.post(`/spirit-diary/${homeData.reportId.value}/entry`, {
        chat_context: JSON.stringify(chatContext),
        spirit_planet: chatPlanet.value,
        mood_emoji: "",
      });
    } catch {
      // silent fail
    }
  }
  chatVisible.value = false;
}

function handleBackdropClose() {
  const msgs = chatBubbleRef.value?.messages || [];
  closeChatAndGenerateDiary(msgs);
}

function onTransitChat(transitPlanet: string, transitDetail: string) {
  const profile = homeData.planetProfiles.value?.planet_characters?.[transitPlanet];
  chatPlanet.value = transitPlanet;
  chatSymbol.value = profile?.symbol || "";
  chatName.value = profile?.persona?.name_zh || transitPlanet;
  chatArchetype.value = profile?.persona?.archetype_zh || "";
  chatColor.value = profile?.persona?.visual_color || "#ccc";
  chatGreeting.value = profile?.personalized_greeting || "";
  chatEntryContext.value = {
    source: "transit",
    transit_planet: transitPlanet,
    transit_detail: transitDetail,
    previous_chats_today: todayChatCounts.value[transitPlanet] || 0,
  };
  todayChatCounts.value[transitPlanet] = (todayChatCounts.value[transitPlanet] || 0) + 1;
  homeData.setActivePlanet(transitPlanet);
  showCouncil.value = false;
  chatVisible.value = true;
}

// ═══════════════════════════════════════
// 导航
// ═══════════════════════════════════════

function goGarden() {
  // 花园按钮当前已经处于主页（花园模式），无需跳转
  // 如果未来需要跳转具体视图，可以在这里修改
}
function goHistory() { router.push("/history"); }
function goOnboarding() { router.push("/onboarding"); }
function goProfile() { router.push("/profile"); }
function goDiary() {
  showProfile.value = false;
  showDiary.value = true;
}
function doLogout() {
  homeData.logout();
  homeData.clearData();
  showProfile.value = false;
  router.push("/login");
}

onMounted(() => homeData.refreshData());
</script>

<style scoped>
/* ═══════════════ 主题变量 ═══════════════ */
.main-page[data-theme="cream"] {
  --garden-bg-1: #FFF5EE;
  --garden-bg-2: #FFF0F5;
  --garden-card-bg: rgba(255,255,255,0.75);
  --garden-text: #4A3728;
  --garden-text-soft: #8B7355;
  --garden-accent: #FF9A8B;
}
.main-page[data-theme="night"] {
  --garden-bg-1: #1a1a2e;
  --garden-bg-2: #16213e;
  --garden-card-bg: rgba(30,30,60,0.75);
  --garden-text: #E8E0F0;
  --garden-text-soft: #A098B8;
  --garden-accent: #9B8EC4;
}
.main-page[data-theme="sakura"] {
  --garden-bg-1: #FFF0F5;
  --garden-bg-2: #FDE8EF;
  --garden-card-bg: rgba(255,255,255,0.75);
  --garden-text: #5C3D4A;
  --garden-text-soft: #9B7B8A;
  --garden-accent: #F4A7B9;
}

.main-page {
  min-height: 100vh;
  position: relative;
  overflow-x: hidden;
  background: var(--garden-bg-1);
  transition: background 0.6s ease;
}

/* ═══════════════ 视频全屏层 ═══════════════ */
.video-layer {
  position: fixed; inset: 0; z-index: 0;
}
.bg-video {
  position: absolute; inset: 0;
  width: 100%; height: 100%;
  object-fit: cover;
}
/* 渐变遮罩 — pointer-events: none 让点击穿透 */
.video-overlay-top {
  position: absolute; top: 0; left: 0; right: 0; height: 35%;
  background: linear-gradient(to bottom, rgba(0,0,0,0.45), transparent);
  pointer-events: none;
}
.video-overlay-bottom {
  position: absolute; bottom: 0; left: 0; right: 0; height: 40%;
  background: linear-gradient(to top, rgba(0,0,0,0.5), transparent);
  pointer-events: none;
}
/* 声音切换按钮 */
.sound-toggle {
  position: absolute; bottom: 120px; right: 20px; z-index: 10;
  width: 40px; height: 40px; border-radius: 50%;
  border: none; background: rgba(0,0,0,0.3); backdrop-filter: blur(8px);
  color: #fff; font-size: 18px; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: all 0.25s;
}
.sound-toggle:hover { background: rgba(0,0,0,0.5); transform: scale(1.08); }

/* 视频交叉淡入淡出 */
.video-cross-enter-active,
.video-cross-leave-active {
  transition: opacity 0.8s ease;
}
.video-cross-enter-from,
.video-cross-leave-to {
  opacity: 0;
}

/* ═══════════════ 加载/错误态 ═══════════════ */
.garden-state { position: relative; z-index: 1; text-align: center; padding: 120px 20px; }
.state-icon { font-size: 52px; margin-bottom: 16px; animation: float 3s ease-in-out infinite; }
@keyframes float { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-10px)} }
.state-title { font-size: 22px; font-weight: 700; color: #4a3728; margin: 0 0 8px; }
.state-sub { font-size: 14px; color: #8b7355; margin: 0 0 24px; }
.state-spinner { display: flex; justify-content: center; gap: 10px; }
.spinner-dot { width: 10px; height: 10px; border-radius: 50%; animation: dot-bounce 1.2s ease-in-out infinite; }
@keyframes dot-bounce { 0%,100%{transform:translateY(0);opacity:0.4} 50%{transform:translateY(-16px);opacity:1} }
.retry-btn { background: rgba(255,154,139,0.2) !important; border-color: rgba(255,154,139,0.3) !important; color: #4a3728 !important; }
.login-guide { padding: 160px 20px 100px !important; }
.login-guide-btn { background: linear-gradient(135deg, #f0b8a0, #e8a890, #f0c0b0) !important; border: none !important; color: #fff !important; font-weight: 600 !important; letter-spacing: 2px !important; padding: 14px 40px !important; border-radius: 18px !important; box-shadow: 0 4px 20px rgba(220,150,120,0.18) !important; }
.login-guide-btn:hover { transform: translateY(-2px) !important; box-shadow: 0 10px 32px rgba(220,150,120,0.28) !important; }
.login-guide-hint { font-size: 12px; color: #b8a090; margin-top: 12px; cursor: pointer; }

/* ═══════════════ 顶栏：悬浮于视频之上 ═══════════════ */
.top-bar {
  position: fixed; top: 0; left: 0; right: 0; z-index: 10;
  display: flex; justify-content: space-between; align-items: center;
  padding: 16px 20px;
  padding-top: calc(16px + env(safe-area-inset-top, 0px));
}
.avatar-trigger {
  width: 40px; height: 40px; border-radius: 50%; border: 2px solid rgba(255,255,255,0.3);
  background: rgba(255,255,255,0.25); cursor: pointer; padding: 0; overflow: hidden;
  transition: all 0.2s; display: flex; align-items: center; justify-content: center;
  backdrop-filter: blur(8px);
}
.avatar-trigger:hover { border-color: rgba(255,255,255,0.6); background: rgba(255,255,255,0.4); transform: scale(1.05); }

/* ── 三栏顶栏布局 ── */
.top-bar--three {
  display: grid;
  grid-template-columns: 40px 1fr auto auto;
  gap: 10px;
  align-items: center;
}
.top-bar--three > .avatar-trigger {
  grid-column: 1;
}
.top-bar--three > .star-spirit-display {
  grid-column: 2;
  justify-self: center;
}
.top-bar--three > .direction-trigger {
  grid-column: 3;
}
.top-bar--three > .theme-switcher {
  grid-column: 4;
}

/* ── 今日走向按钮 ── */
.direction-trigger {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  border-radius: 16px;
  border: 1px solid rgba(255,255,255,0.2);
  background: rgba(255,255,255,0.15);
  backdrop-filter: blur(8px);
  cursor: pointer;
  transition: all 0.2s;
  font-family: inherit;
}
.direction-trigger:hover {
  background: rgba(255,255,255,0.25);
  transform: scale(1.04);
}
.direction-icon {
  font-size: 14px;
  line-height: 1;
}
.direction-label {
  font-size: 11px;
  font-weight: 600;
  color: #fff;
  text-shadow: 0 1px 2px rgba(0,0,0,0.2);
  white-space: nowrap;
}

/* ═══════════════ Chat Overlay ═══════════════ */
.overlay-backdrop {
  position: fixed; inset: 0; z-index: 200;
  background: rgba(0,0,0,0.3); backdrop-filter: blur(6px);
  display: flex; align-items: center; justify-content: center; padding: 20px;
}
.overlay-content {
  width: 100%; max-width: 500px; max-height: 90vh; overflow-y: auto;
  border-radius: 28px;
}
.overlay-content::-webkit-scrollbar { width: 4px; }
.overlay-fade-enter-active { transition: all 0.3s ease; }
.overlay-fade-leave-active { transition: all 0.2s ease; }
.overlay-fade-enter-from { opacity: 0; }
.overlay-fade-enter-from .overlay-content { transform: scale(0.95) translateY(20px); }
.overlay-fade-leave-to { opacity: 0; }

</style>
