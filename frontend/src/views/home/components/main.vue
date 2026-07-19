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

    <!-- ═══ 主内容 ═══ -->
    <template v-else>
      <!-- 顶栏：悬浮于视频之上 -->
      <div class="top-bar" v-if="homeData.hasProfile.value">
        <button class="avatar-trigger" @click="showProfile = true">
          <SpiritAvatar planet="SUN" :sign="homeData.sunSign.value" :gender="homeData.userGender.value" size="sm" />
        </button>
        <ThemeSwitcher :current="currentTheme" @select="(k: string) => currentTheme = k" />
      </div>

      <!-- ═══ 底部导航栏 ═══ -->
      <HomeTabBar
        v-if="homeData.hasProfile.value"
        :chat-cta-text="homeData.chatCtaText.value"
        @garden="goGarden"
        @chat="openChat"
        @council="showCouncil = true"
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
        @logout="doLogout"
      />

      <!-- ═══ 聊天浮层 ═══ -->
      <transition name="overlay-fade">
        <div v-if="chatVisible" class="overlay-backdrop" @click.self="chatVisible = false">
          <div class="overlay-content">
            <SpiritChatBubble
              :visible="chatVisible"
              :planet="chatPlanet"
              :symbol="chatSymbol"
              :name="chatName"
              :archetype="chatArchetype"
              :color="chatColor"
              :greeting="chatGreeting"
              :report-id="homeData.reportId.value"
              @close="chatVisible = false"
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
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, nextTick } from "vue";
import { useRouter } from "vue-router";
import { useHomeData } from "@/composables/useHomeData";
import { PLANET_COLORS } from "@/config/zodiac";
import GardenScene from "@/views/Wanxiang/components/GardenScene.vue";
import SpiritAvatar from "@/views/Wanxiang/components/SpiritAvatar.vue";
import SpiritChatBubble from "@/views/Wanxiang/components/SpiritChatBubble.vue";
import ThemeSwitcher from "@/views/Wanxiang/components/ThemeSwitcher.vue";
import HomeTabBar from "./HomeTabBar.vue";
import ProfileOverlay from "./ProfileOverlay.vue";
import HomeCouncil from "./HomeCouncil.vue";

const router = useRouter();
const homeData = useHomeData();

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

// ── 色板 (spinner 用) ──
const planetColors = PLANET_COLORS;

// ── UI 浮层状态 ──
const showProfile = ref(false);
const showCouncil = ref(false);
const chatVisible = ref(false);

// ── 聊天目标 ──
const chatPlanet = ref("SUN");
const chatSymbol = ref("☉");
const chatName = ref("太阳");
const chatArchetype = ref("");
const chatColor = ref("#F2A900");
const chatGreeting = ref("");

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

function onCouncilPlanetChat(p: any) {
  chatPlanet.value = p.planet;
  chatSymbol.value = p.symbol;
  chatName.value = p.shortName;
  chatArchetype.value = p.archetypeShort;
  chatColor.value = p.color;
  chatGreeting.value = p.greeting;
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

// ═══════════════════════════════════════
// 导航
// ═══════════════════════════════════════

function goGarden() {
  const rid = homeData.reportId.value || "";
  router.push({ name: "spirit-garden", query: rid ? { id: rid } : {} });
}
function goHistory() { router.push("/history"); }
function goOnboarding() { router.push("/onboarding"); }
function doLogout() {
  homeData.logout();
  homeData.clearData();
  showProfile.value = false;
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
/* 渐变遮罩 */
.video-overlay-top {
  position: absolute; top: 0; left: 0; right: 0; height: 35%;
  background: linear-gradient(to bottom, rgba(0,0,0,0.45), transparent);
}
.video-overlay-bottom {
  position: absolute; bottom: 0; left: 0; right: 0; height: 40%;
  background: linear-gradient(to top, rgba(0,0,0,0.5), transparent);
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
