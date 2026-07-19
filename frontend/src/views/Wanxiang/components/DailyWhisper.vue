<template>
  <div class="daily-whisper">
    <!-- 波浪装饰 -->
    <div class="whisper-wave">
      <svg viewBox="0 0 400 40" preserveAspectRatio="none">
        <path
          d="M0,20 C80,40 120,0 200,20 C280,40 320,0 400,20 L400,40 L0,40 Z"
          fill="rgba(255,255,255,0.5)"
        />
      </svg>
    </div>

    <!-- 主体内容 -->
    <div class="whisper-body">
      <div class="whisper-moon">🌙</div>
      <h2 class="whisper-title">每日星语</h2>
      <p class="whisper-theme" v-if="dailyTheme">{{ dailyTheme }}</p>
      <p class="whisper-date">{{ dateLabel }}</p>

      <!-- 法达阶段提示 -->
      <div class="whisper-phase" v-if="firdariaNote">
        <span class="phase-dot"></span>
        {{ firdariaNote }}
      </div>

      <!-- 今日登场星灵 -->
      <div class="whisper-featured" v-if="featuredPlanets.length > 0">
        <p class="featured-label">今天陪在你身边的是——</p>
        <div class="featured-row">
          <div
            v-for="fp in featuredPlanets"
            :key="fp.planet"
            class="featured-mini"
            :style="{ '--fp-color': fp.visual_color }"
          >
            <SpiritAvatar :planet="fp.planet" :symbol="fp.symbol" :name="fp.name_zh" :color="fp.visual_color" size="md" />
            <div class="featured-meta">
              <span class="featured-name">{{ fp.name_zh }}</span>
              <span class="featured-score">{{ Math.round(fp.activation_score) }}%</span>
            </div>
            <span class="featured-msg">{{ fp.daily_message?.slice(0, 40) }}...</span>
          </div>
        </div>
      </div>

      <!-- 主星灵（太阳）常驻提示 -->
      <div class="whisper-sun" v-if="mainCharacter">
        <SpiritAvatar planet="SUN" :symbol="mainCharacter.symbol" :name="mainCharacter.name_zh" size="sm" />
        <span>{{ mainCharacter.name_zh }}始终在线——</span>
        <span class="sun-note">你的核心从未离开</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import SpiritAvatar from "./SpiritAvatar.vue";
import type { FeaturedPlanet } from "@/utils/types";

const props = defineProps<{
  dailyTheme: string;
  firdariaNote: string;
  lunarNote: string;
  featuredPlanets: FeaturedPlanet[];
  mainCharacter: FeaturedPlanet | null;
}>();

const dateLabel = computed(() => {
  const now = new Date();
  const weekdays = ["日", "一", "二", "三", "四", "五", "六"];
  return `${now.getFullYear()}年${now.getMonth() + 1}月${now.getDate()}日 · 星期${weekdays[now.getDay()]}`;
});
</script>

<style scoped>
.daily-whisper {
  position: relative;
  border-radius: 28px;
  overflow: hidden;
  background: linear-gradient(
    135deg,
    rgba(255, 255, 255, 0.85) 0%,
    rgba(255, 245, 238, 0.8) 50%,
    rgba(255, 240, 245, 0.7) 100%
  );
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.04),
    0 1px 4px rgba(0, 0, 0, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.8);
}

/* ── 波浪装饰 ── */
.whisper-wave {
  width: 100%;
  height: 20px;
  overflow: hidden;
}
.whisper-wave svg {
  width: 100%;
  height: 100%;
}

/* ── 主体 ── */
.whisper-body {
  padding: 8px 24px 24px;
  text-align: center;
}
.whisper-moon {
  font-size: 32px;
  margin-bottom: 8px;
  animation: moon-glow 2s ease-in-out infinite;
}
@keyframes moon-glow {
  0%,
  100% {
    filter: drop-shadow(0 0 4px rgba(240, 192, 96, 0.3));
  }
  50% {
    filter: drop-shadow(0 0 12px rgba(240, 192, 96, 0.6));
  }
}
.whisper-title {
  font-size: 20px;
  font-weight: 700;
  color: #4a3728;
  margin: 0 0 6px;
}
.whisper-theme {
  font-size: 15px;
  color: #6b5744;
  margin: 0 0 4px;
  line-height: 1.6;
  font-style: italic;
}
.whisper-date {
  font-size: 12px;
  color: #a89880;
  margin: 0 0 12px;
}

/* ── 法达阶段 ── */
.whisper-phase {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 18px;
  border-radius: 16px;
  background: rgba(240, 192, 96, 0.1);
  font-size: 13px;
  color: #6b5744;
  margin-bottom: 16px;
}
.phase-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #f0c060;
  animation: twinkle 1.5s ease-in-out infinite;
}
@keyframes twinkle {
  0%,
  100% {
    opacity: 0.5;
  }
  50% {
    opacity: 1;
  }
}

/* ── 今日登场 ── */
.whisper-featured {
  text-align: left;
  margin-bottom: 16px;
}
.featured-label {
  font-size: 13px;
  color: #8b7355;
  margin: 0 0 10px;
  text-align: center;
}
.featured-row {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.featured-mini {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.6);
  border: 1px solid rgba(0, 0, 0, 0.04);
  transition: all 0.2s;
  cursor: default;
}
.featured-mini:hover {
  background: rgba(255, 255, 255, 0.85);
  border-color: var(--fp-color);
}
.featured-symbol {
  font-size: 24px;
  width: 36px;
  text-align: center;
  flex-shrink: 0;
}
.featured-meta {
  display: flex;
  flex-direction: column;
  gap: 1px;
  min-width: 50px;
  flex-shrink: 0;
}
.featured-name {
  font-size: 14px;
  font-weight: 600;
  color: #4a3728;
}
.featured-score {
  font-size: 11px;
  font-weight: 700;
  color: var(--fp-color);
}
.featured-msg {
  font-size: 12px;
  color: #8b7355;
  line-height: 1.4;
}

/* ── 太阳常驻 ── */
.whisper-sun {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 16px;
  background: rgba(242, 169, 0, 0.08);
  font-size: 13px;
  color: #6b5744;
}
.sun-icon {
  font-size: 18px;
}
.sun-note {
  color: #c79100;
  font-weight: 600;
}
</style>
