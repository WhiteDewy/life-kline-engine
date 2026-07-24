<template>
  <div class="main-page" :data-theme="currentTheme">
    <!-- ═══ 氛围背景层 ═══ -->
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
      <div class="video-overlay-top"></div>
      <div class="video-overlay-bottom"></div>
      <button class="sound-toggle" @click="toggleSound" :title="videoMuted ? '开启声音' : '静音'">
        <svg v-if="videoMuted" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M11 5L6 9H2v6h4l5 4V5z" />
          <path d="M23 9l-6 6M17 9l6 6" />
        </svg>
        <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M11 5L6 9H2v6h4l5 4V5z" />
          <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07" />
        </svg>
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
      <AppButton variant="secondary" size="lg" @click="homeData.refreshData()">重新尝试</AppButton>
    </section>

    <!-- ═══ 登录引导 ═══ -->
    <section v-else-if="!isLoggedIn && !homeData.loading.value" class="garden-state login-guide">
      <div class="state-icon">🔮</div>
      <h2 class="state-title">欢迎来到星灵花园</h2>
      <p class="state-sub">登录解锁专属星盘，与你的星灵对话</p>
      <AppButton size="lg" @click="startLogin">登录</AppButton>
      <p class="login-guide-hint" @click="enterDemo">你也可以继续浏览 Demo 星盘</p>
    </section>

    <!-- ═══ 主内容 ═══ -->
    <template v-else>
      <!-- 顶栏 -->
      <div class="top-bar" v-if="homeData.hasProfile.value">
        <button class="avatar-trigger" @click="showProfile = true" aria-label="打开个人菜单">
          <SpiritAvatar planet="SUN" :sign="homeData.sunSign.value" :gender="homeData.userGender.value" size="sm" />
        </button>

        <StarSpiritDisplay
          v-if="homeData.todayStarSpirit.value"
          :planet="homeData.todayStarSpirit.value.planet"
          :planet-name="homeData.todayStarSpirit.value.planet_label"
          :planet-sign="homeData.todayStarSpirit.value.sign_label"
          :symbol="homeData.todayStarSpirit.value.symbol"
          :color="homeData.todaysPlanetProfile?.value?.persona?.visual_color || '#D4A35A'"
          :gender="homeData.userGender.value"
          @chat="openStarSpiritChat"
        />

        <button class="direction-trigger" @click="openDirection">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M6.34 17.66l-2.83 2.83M19.07 4.93l-2.83 2.83" />
          </svg>
          <span class="direction-label">今日走向</span>
        </button>
      </div>

      <!-- 主体内容区 -->
      <div class="home-content" v-if="homeData.hasProfile.value">
        <div class="hero-card">
          <p class="hero-greeting">{{ greetingText }}</p>
          <h1 class="hero-title">今天，你的心境如何？</h1>
          <AppButton size="lg" class="hero-cta" @click="openChatPage">
            和 {{ homeData.todayStarSpirit.value?.planet_label || '星灵' }} 聊聊
          </AppButton>
        </div>

        <div class="quick-actions">
          <AppCard variant="soft" hover clickable class="quick-card" @click="goDiary">
            <template #header>
              <div class="quick-card__header">
                <span class="quick-card__icon">📖</span>
                <span class="quick-card__title">星灵日记</span>
              </div>
            </template>
            <p class="quick-card__desc">记录此刻，让星灵陪你沉淀情绪。</p>
          </AppCard>

          <AppCard variant="soft" hover clickable class="quick-card" @click="goGarden">
            <template #header>
              <div class="quick-card__header">
                <span class="quick-card__icon">🌸</span>
                <span class="quick-card__title">进入花园</span>
              </div>
            </template>
            <p class="quick-card__desc">拜访 22 位星灵，听听它们想对你说什么。</p>
          </AppCard>
        </div>
      </div>

      <!-- 底部导航 -->
      <HomeTabBar @garden="goGarden" @daily-question="openDailyQuestionPanel" @council="openCouncil" />

      <!-- Profile 浮层 -->
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
        @go-chart="goChart"
        @go-history="goHistory"
        @go-profile="goProfile"
        @go-diary="goDiary"
        @logout="doLogout"
      />

      <!-- 星灵议会 浮层 -->
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

      <!-- 灵犀一问 -->
      <SpiritOracle
        :visible="showDailyQuestion"
        :today-star-spirit="homeData.todayStarSpirit.value"
        :daily-question="homeData.dailyQuestion.value"
        :spirit-profile="homeData.todaysPlanetProfile?.value"
        :gender="homeData.userGender.value"
        @chat="openStarSpiritChat"
        @close="showDailyQuestion = false"
      />

      <!-- 星灵日记（兼容旧入口，主流程已跳转到 /diary） -->
      <StarSpiritDiary
        v-if="false"
        :visible="showDiary"
        :entries="homeData.diaryEntries.value"
        :loading="false"
        @close="showDiary = false"
      />

      <!-- 今日走向 -->
      <TodayDirection
        :visible="showDirection"
        :transit-report="homeData.dailyTransitReport.value"
        :today-star-spirit="homeData.todayStarSpirit.value"
        :date-label="homeData.dateLabel.value"
        @close="showDirection = false"
        @chat-with-spirit="onTransitChat($event)"
      />

      <!-- 新人引导 -->
      <OnboardingFlow
        :visible="showOnboarding"
        :today-star-spirit="homeData.todayStarSpirit.value"
        :todays-planet-profile="homeData.todaysPlanetProfile?.value"
        :daily-question="homeData.dailyQuestion.value?.question || ''"
        @close="onOnboardingClosed"
      />

      <!-- 灵犀占卜（占位） -->
      <DivinationPlaceholder
        :visible="showDivination"
        @close="showDivination = false"
      />
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, nextTick, computed } from "vue";
import { useRouter } from "vue-router";
import { useHomeData } from "@/composables/useHomeData";
import { useAuth } from "@/utils/auth";
import { PLANET_COLORS } from "@/config/zodiac";
import AppButton from "@/components/AppButton.vue";
import AppCard from "@/components/AppCard.vue";
import GardenScene from "@/components/garden/GardenScene.vue";
import SpiritAvatar from "@/components/garden/SpiritAvatar.vue";
import HomeTabBar from "./HomeTabBar.vue";
import ProfileOverlay from "./ProfileOverlay.vue";
import HomeCouncil from "./HomeCouncil.vue";
import StarSpiritDisplay from "./StarSpiritDisplay.vue";
import SpiritOracle from "./SpiritOracle.vue";
import StarSpiritDiary from "./StarSpiritDiary.vue";
import TodayDirection from "./TodayDirection.vue";
import OnboardingFlow from "./OnboardingFlow.vue";
import DivinationPlaceholder from "@/views/Garden/components/DivinationPlaceholder.vue";

const router = useRouter();
const homeData = useHomeData();
const { isLoggedIn } = useAuth();

function startLogin() { router.push("/login"); }
function enterDemo() {
  // Demo 模式：继续展示首页（当前逻辑已支持未登录但 homeData 有 demo 数据）
  homeData.refreshData();
}

// ── 主题 ──
const currentTheme = ref(localStorage.getItem("spirit_garden_theme") || "cream");

// ── 视频声音 ──
const videoRef = ref<HTMLVideoElement | null>(null);
const videoMuted = ref(true);

function toggleSound() {
  videoMuted.value = !videoMuted.value;
  if (!videoMuted.value && videoRef.value) {
    videoRef.value.muted = false;
    videoRef.value.play().catch(() => {
      videoMuted.value = true;
    });
  }
}

watch(() => homeData.currentSignVideo.value, () => {
  nextTick(() => {
    if (videoRef.value && !videoMuted.value) {
      videoRef.value.muted = false;
      videoRef.value.play().catch(() => {});
    }
  });
});

watch(() => homeData.loading.value, (loading) => {
  if (!loading) {
    const profileDone = localStorage.getItem("spirit_profile_completed");
    if (!profileDone) {
      showOnboarding.value = true;
    }
  }
}, { immediate: true });

const planetColors = PLANET_COLORS;

const greetingText = computed(() => {
  const hour = new Date().getHours();
  if (hour < 6) return "夜深了，星灵还在陪着你。";
  if (hour < 11) return "早安，今天想从哪里开始？";
  if (hour < 14) return "午安，停下来和自己说句话吧。";
  if (hour < 19) return "下午好，今天有什么想被听见的？";
  return "晚上好，把今天交给星灵吧。";
});

// ── 兼容保留的浮层状态（星灵议会 / 灵犀一问 / 今日走向 仍由浮层承载） ──
const showProfile = ref(false);
const showCouncil = ref(false);
const showDailyQuestion = ref(false);
const showDiary = ref(false);
const showDirection = ref(false);
const showOnboarding = ref(false);
const showDivination = ref(false);

function openDirection() {
  closeAllPanels();
  showDirection.value = true;
}

function openCouncil() {
  closeAllPanels();
  showCouncil.value = true;
}

function openDailyQuestionPanel() {
  closeAllPanels();
  showDailyQuestion.value = true;
}

function closeAllPanels() {
  showDirection.value = false;
  showCouncil.value = false;
  showDivination.value = false;
  showDailyQuestion.value = false;
}

// ── 路由跳转：进入全屏聊天页 ──

function openChatPage(planet?: string) {
  const target = planet || homeData.todayStarSpirit.value?.planet || "SUN";
  router.push({
    name: "spirit-chat",
    params: { planet: target },
    query: {
      source: planet ? "council" : "today",
      question: homeData.dailyQuestion.value?.question || "",
    },
  });
}

function openStarSpiritChat() {
  openChatPage();
}

function onCouncilPlanetChat(p: any) {
  homeData.setActivePlanet(p.planet);
  showCouncil.value = false;
  openChatPage(p.planet);
}

function onCouncilSignChat(s: any) {
  showCouncil.value = false;
  homeData.setActiveSign(s.key);
  router.push({ path: "/constellation-stories", query: { sign: s.key } });
}

function onTransitChat(payload: { planet: string; detail: string; transit?: any }) {
  const { planet: transitPlanet } = payload;
  homeData.setActivePlanet(transitPlanet);
  showDirection.value = false;
  openChatPage(transitPlanet);
}

// ═══════════════════════════════════════
// 导航
// ═══════════════════════════════════════

function goGarden() { router.push("/spirit-garden"); }
function goChart() { router.push("/my-chart"); }
function goHistory() { router.push("/history"); }
function goProfile() { router.push("/profile"); }
function onOnboardingClosed() {
  showOnboarding.value = false;
  const { profiles } = useAuth();
  if (!profiles.value?.length) {
    router.push("/onboarding");
  }
}
function goDiary() {
  showProfile.value = false;
  router.push({ name: "spirit-diary" });
}

function doLogout() {
  homeData.logout();
  homeData.clearData();
  showProfile.value = false;
  router.push("/login");
}

onMounted(() => homeData.refreshData());
</script>

<style scoped lang="less">
.main-page {
  min-height: 100vh;
  position: relative;
  overflow-x: hidden;
  background: var(--bg-main);
  transition: background var(--duration-slow) var(--ease-smooth);
  padding-bottom: calc(var(--h-tab-bar) + env(safe-area-inset-bottom, 0px));
}

/* ═══════════════ 氛围背景 ═══════════════ */
.video-layer {
  position: fixed;
  inset: 0;
  z-index: 0;
}

.bg-video {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  filter: saturate(0.85) brightness(1.05);
}

.video-overlay-top {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 40%;
  background: linear-gradient(to bottom, rgba(247, 244, 239, 0.55), transparent);
  pointer-events: none;
}

.video-overlay-bottom {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 55%;
  background: linear-gradient(to top, rgba(247, 244, 239, 0.92) 0%, rgba(247, 244, 239, 0.4) 50%, transparent 100%);
  pointer-events: none;
}

.sound-toggle {
  position: absolute;
  bottom: calc(var(--h-tab-bar) + var(--space-5) + env(safe-area-inset-bottom, 0px));
  right: var(--space-5);
  z-index: 10;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: 1px solid var(--border-light);
  background: var(--bg-card-glass);
  backdrop-filter: blur(12px);
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--duration-fast) var(--ease-smooth);
}

.sound-toggle:hover {
  background: var(--bg-card);
  color: var(--color-primary);
  transform: scale(1.05);
}

.video-cross-enter-active,
.video-cross-leave-active {
  transition: opacity var(--duration-slow) var(--ease-smooth);
}

.video-cross-enter-from,
.video-cross-leave-to {
  opacity: 0;
}

/* ═══════════════ 状态页 ═══════════════ */
.garden-state {
  position: relative;
  z-index: 1;
  text-align: center;
  padding: 120px var(--space-5);
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-3);
}

.state-icon {
  font-size: 52px;
  margin-bottom: var(--space-2);
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

.state-title {
  font-size: var(--text-xl);
  font-weight: var(--font-bold);
  color: var(--text-primary);
  margin: 0;
}

.state-sub {
  font-size: var(--text-base);
  color: var(--text-secondary);
  margin: 0 0 var(--space-4);
  max-width: 280px;
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

.login-guide {
  padding-top: 160px;
}

.login-guide-hint {
  font-size: var(--text-sm);
  color: var(--text-tertiary);
  margin-top: var(--space-4);
  cursor: pointer;
  transition: color var(--duration-fast) var(--ease-smooth);
}

.login-guide-hint:hover {
  color: var(--color-primary);
}

/* ═══════════════ 顶栏 ═══════════════ */
.top-bar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 10;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-3) var(--space-4);
  padding-top: calc(var(--space-3) + env(safe-area-inset-top, 0px));
}

.avatar-trigger {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: 2px solid rgba(255, 255, 255, 0.5);
  background: var(--bg-card-glass);
  backdrop-filter: blur(8px);
  cursor: pointer;
  padding: 0;
  overflow: hidden;
  transition: all var(--duration-fast) var(--ease-smooth);
  display: flex;
  align-items: center;
  justify-content: center;
}

.avatar-trigger:hover {
  border-color: var(--color-primary-light);
  transform: scale(1.05);
}

.direction-trigger {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border-radius: var(--radius-full);
  border: 1px solid rgba(255, 255, 255, 0.4);
  background: var(--bg-card-glass);
  backdrop-filter: blur(8px);
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-smooth);
  color: var(--text-primary);
  font-family: inherit;
}

.direction-trigger:hover {
  background: var(--bg-card);
  border-color: var(--color-primary-light);
}

.direction-trigger svg {
  color: var(--color-primary);
}

.direction-label {
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
  white-space: nowrap;
}

/* ═══════════════ 主内容 ═══════════════ */
.home-content {
  position: relative;
  z-index: 1;
  max-width: var(--content-max);
  margin: 0 auto;
  padding: calc(var(--h-header) + env(safe-area-inset-top, 0px) + var(--space-8)) var(--space-5) var(--space-10);
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}

.hero-card {
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-8) var(--space-5);
}

.hero-greeting {
  font-size: var(--text-sm);
  color: var(--text-tertiary);
  font-weight: var(--font-medium);
  letter-spacing: 0.04em;
}

.hero-title {
  font-size: var(--text-2xl);
  font-weight: var(--font-bold);
  color: var(--text-primary);
  line-height: var(--leading-tight);
  max-width: 280px;
}

.hero-cta {
  margin-top: var(--space-2);
}

.quick-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-4);
}

.quick-card {
  --card-padding: var(--space-4);
}

.quick-card :deep(.app-card__body) {
  padding: var(--space-4);
}

.quick-card__header {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-bottom: var(--space-2);
}

.quick-card__icon {
  font-size: var(--text-lg);
}

.quick-card__title {
  font-size: var(--text-base);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
}

.quick-card__desc {
  font-size: var(--text-sm);
  color: var(--text-secondary);
  line-height: var(--leading-normal);
  margin: 0;
}

/* ═══════════════ Chat Overlay ═══════════════ */
.overlay-backdrop {
  position: fixed;
  inset: 0;
  z-index: 200;
  background: rgba(44, 38, 34, 0.2);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-5);
}

.overlay-content {
  width: 100%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
  border-radius: var(--radius-2xl);
}

.overlay-content::-webkit-scrollbar {
  width: 4px;
}

.overlay-fade-enter-active {
  transition: all var(--duration-normal) var(--ease-smooth);
}

.overlay-fade-leave-active {
  transition: all var(--duration-fast) var(--ease-smooth);
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

@media (max-width: 380px) {
  .hero-title {
    font-size: var(--text-xl);
  }
  .quick-actions {
    grid-template-columns: 1fr;
  }
}
</style>
