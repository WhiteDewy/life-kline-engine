<template>
  <div class="planet-wheel-section">
    <div class="section-header">
      <h3>你的行星人格</h3>
      <span class="section-hint">太阳是你的核心 · 六颗行星是你的不同侧面</span>
    </div>

    <!-- 行星轮盘 SVG -->
    <div class="wheel-container">
      <svg viewBox="0 0 400 400" class="planet-wheel-svg">
        <defs>
          <!-- 光晕滤镜 -->
          <filter id="glow-gold">
            <feGaussianBlur stdDeviation="4" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          <filter id="glow-featured">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        <!-- 外环背景 -->
        <circle cx="200" cy="200" r="180" fill="none" stroke="rgba(255,255,255,0.04)" stroke-width="80" />

        <!-- 6 颗次人格行星 -->
        <g v-for="seg in ringPlanets" :key="seg.planet">
          <!-- 轨道连接线 -->
          <line
            :x1="seg.cx" :y1="seg.cy"
            x2="200" y2="200"
            stroke="rgba(255,255,255,0.06)"
            stroke-width="0.5"
          />
          <!-- 行星圆 -->
          <circle
            :cx="seg.cx" :cy="seg.cy" r="29"
            :fill="seg.fillColor"
            :opacity="seg.isFeatured ? 0.85 : 0.45"
            :stroke="seg.isFeatured ? 'rgba(212,175,55,0.6)' : 'rgba(255,255,255,0.1)'"
            :stroke-width="seg.isFeatured ? 2 : 0.5"
            :filter="seg.isFeatured ? 'url(#glow-featured)' : 'none'"
            class="planet-circle"
            @click="$emit('selectPlanet', seg.planet)"
            style="cursor: pointer; transition: all 0.3s ease;"
          />
          <!-- 行星符号 -->
          <text
            :x="seg.cx" :y="seg.cy - 4"
            :fill="seg.isFeatured ? '#fff' : 'rgba(255,255,255,0.7)'"
            font-size="20"
            text-anchor="middle"
            dominant-baseline="central"
            class="planet-symbol"
            @click="$emit('selectPlanet', seg.planet)"
            style="cursor: pointer;"
          >
            {{ seg.symbol }}
          </text>
          <!-- 星座标签 -->
          <text
            :x="seg.cx" :y="seg.cy + 16"
            :fill="seg.isFeatured ? 'rgba(255,255,255,0.7)' : 'rgba(255,255,255,0.4)'"
            font-size="9"
            text-anchor="middle"
            class="planet-sign-label"
            @click="$emit('selectPlanet', seg.planet)"
            style="cursor: pointer;"
          >
            {{ seg.signLabel }}
          </text>
          <!-- 激活标记 -->
          <text
            v-if="seg.isFeatured && seg.activationScore"
            :x="seg.cx" :y="seg.cy - 24"
            fill="#d4af37"
            font-size="9"
            text-anchor="middle"
            font-weight="bold"
          >
            {{ Math.round(seg.activationScore) }}%
          </text>
        </g>

        <!-- 中心太阳 -->
        <circle
          cx="200" cy="200" r="48"
          fill="url(#sunGrad)"
          opacity="1"
          stroke="rgba(212,175,55,0.4)"
          stroke-width="2"
          filter="url(#glow-gold)"
          class="sun-core"
          @click="$emit('selectPlanet', 'SUN')"
          style="cursor: pointer;"
        />
        <radialGradient id="sunGrad">
          <stop offset="0%" stop-color="#F2A900" stop-opacity="1" />
          <stop offset="70%" stop-color="#F2A900" stop-opacity="0.9" />
          <stop offset="100%" stop-color="#C48800" stop-opacity="0.7" />
        </radialGradient>
        <!-- 太阳符号 -->
        <text
          x="200" y="194"
          fill="#fff"
          font-size="26"
          font-weight="bold"
          text-anchor="middle"
          dominant-baseline="central"
          class="sun-symbol"
          @click="$emit('selectPlanet', 'SUN')"
          style="cursor: pointer;"
        >☉</text>
        <!-- 太阳标签 -->
        <text
          x="200" y="216"
          fill="rgba(255,255,255,0.85)"
          font-size="11"
          font-weight="bold"
          text-anchor="middle"
          class="sun-label"
          @click="$emit('selectPlanet', 'SUN')"
          style="cursor: pointer;"
        >主人格</text>
      </svg>
    </div>

    <!-- 每日登场 -->
    <div v-if="dailyTheme" class="daily-section">
      <div class="daily-header">{{ dailyTheme }}</div>
      <div class="daily-cards">
        <!-- 太阳常驻卡片 -->
        <div
          v-if="sunCharacter"
          class="daily-card daily-card--sun"
          :style="{ borderLeftColor: sunCharacter.visual_color }"
          @click="$emit('selectPlanet', 'SUN')"
        >
          <div class="dc-rank dc-rank--sun">常驻</div>
          <div class="dc-info">
            <div class="dc-name">
              {{ sunCharacter.symbol }} {{ sunCharacter.name_zh }}
              <span class="dc-archetype">{{ sunCharacter.archetype_zh }}</span>
            </div>
            <div class="dc-message">{{ sunCharacter.personalized_greeting?.slice(0, 80) }}...</div>
            <div class="dc-meta">
              {{ sunCharacter.sign_label }}{{ sunCharacter.house }}宫 · {{ sunCharacter.dignity_label }}
            </div>
          </div>
        </div>

        <!-- 次人格登场卡片 -->
        <div
          v-for="(fc, i) in featuredPlanets"
          :key="fc.planet"
          class="daily-card"
          :style="{ borderLeftColor: fc.visual_color }"
          @click="$emit('selectPlanet', fc.planet)"
        >
          <div class="dc-rank">#{{ i + 1 }}</div>
          <div class="dc-info">
            <div class="dc-name">
              {{ fc.symbol }} {{ fc.name_zh }}
              <span class="dc-archetype">{{ fc.archetype_zh }}</span>
              <span class="dc-score" :style="{ color: fc.visual_color }">
                {{ Math.round(fc.activation_score) }}%
              </span>
            </div>
            <div class="dc-message">{{ fc.daily_message }}</div>
            <div class="dc-reason">{{ fc.reason }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 提示 -->
    <div v-if="!activePlanet" class="planet-hint">
      👆 点击上方太阳或任一行星，开始与你的内在角色对话。
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type {
  PlanetCharacterProfile,
  PlanetCharacterProfilesData,
  FeaturedPlanet,
} from "@/utils/types";

const props = defineProps<{
  planetProfiles?: PlanetCharacterProfilesData | null;
  dailyActivation?: {
    activation_scores?: Record<string, number>;
    featured_planets?: FeaturedPlanet[];
    main_character?: FeaturedPlanet;
    daily_theme?: string;
  } | null;
  activePlanet?: string;
}>();

defineEmits<{
  selectPlanet: [planet: string];
}>();

// 6 颗次人格行星在环上的位置（60° 间隔，从顶部顺时针）
const RING_RADIUS = 125;
const PLANET_ORDER = ["MOON", "MERCURY", "VENUS", "MARS", "JUPITER", "SATURN"];

const ringPlanets = computed(() => {
  const profiles = props.planetProfiles?.planet_characters || {};
  const activationScores = props.dailyActivation?.activation_scores || {};
  const featured = new Set(
    (props.dailyActivation?.featured_planets || []).map((f) => f.planet)
  );

  return PLANET_ORDER.map((planetKey, i) => {
    const profile = profiles[planetKey] as PlanetCharacterProfile | undefined;
    const angle = -90 + i * 60;
    const rad = (angle * Math.PI) / 180;
    const cx = 200 + RING_RADIUS * Math.cos(rad);
    const cy = 200 + RING_RADIUS * Math.sin(rad);
    const score = activationScores[planetKey];

    return {
      planet: planetKey,
      cx: Math.round(cx),
      cy: Math.round(cy),
      symbol: profile?.persona?.symbol || "●",
      signLabel: profile?.sign_label?.slice(0, 2) || "?",
      fillColor: profile?.persona?.visual_color || "#666",
      isFeatured: featured.has(planetKey),
      activationScore: score,
    };
  });
});

const featuredPlanets = computed(() => {
  return props.dailyActivation?.featured_planets || [];
});

const dailyTheme = computed(() => {
  return props.dailyActivation?.daily_theme || "";
});

const sunCharacter = computed(() => {
  if (props.dailyActivation?.main_character) {
    return props.dailyActivation.main_character;
  }
  const main = props.planetProfiles?.main_character;
  if (!main) return null;
  return {
    symbol: main.persona?.symbol || "☉",
    name_zh: main.persona?.name_zh || "太阳",
    archetype_zh: main.persona?.archetype_zh || "",
    visual_color: main.persona?.visual_color || "#F2A900",
    sign_label: main.sign_label || "",
    house: main.house || 1,
    dignity_label: main.dignity_label || "",
    personalized_greeting: main.personalized_greeting || "",
  };
});
</script>

<style scoped lang="less">
.planet-wheel-section {
  padding: 24px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.section-header {
  text-align: center;
  margin-bottom: 20px;
}
.section-header h3 {
  margin: 0;
  font-size: 18px;
  color: rgba(255, 255, 255, 0.9);
  font-weight: 600;
}
.section-hint {
  display: block;
  margin-top: 4px;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.4);
}

.wheel-container {
  display: flex;
  justify-content: center;
  margin-bottom: 24px;
}
.planet-wheel-svg {
  max-width: 380px;
  width: 100%;
}

/* 太阳脉冲动画 */
.sun-core {
  animation: sun-pulse 3s ease-in-out infinite;
}
@keyframes sun-pulse {
  0%, 100% { r: 48; }
  50% { r: 50; }
}

/* 行星 hover 效果 */
.planet-circle:hover {
  opacity: 1 !important;
  filter: brightness(1.3) !important;
}
.planet-symbol:hover {
  fill: #fff !important;
}

/* 每日登场 */
.daily-section {
  margin-top: 20px;
}
.daily-header {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.7);
  text-align: center;
  margin-bottom: 14px;
  font-style: italic;
}
.daily-cards {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.daily-card {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 14px 16px;
  border-radius: 12px;
  border-left: 3px solid;
  background: rgba(255, 255, 255, 0.03);
  cursor: pointer;
  transition: background 0.2s;
}
.daily-card:hover {
  background: rgba(255, 255, 255, 0.06);
}
.daily-card--sun {
  background: rgba(242, 169, 0, 0.06);
  border-left-color: #F2A900 !important;
}

.dc-rank {
  flex-shrink: 0;
  width: 36px;
  font-size: 14px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.35);
  text-align: center;
  padding-top: 2px;
}
.dc-rank--sun {
  font-size: 12px;
  color: #F2A900;
  background: rgba(242, 169, 0, 0.12);
  border-radius: 8px;
  padding: 2px 6px;
}

.dc-info {
  flex: 1;
  min-width: 0;
}
.dc-name {
  font-size: 14px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  margin-bottom: 4px;
  display: flex;
  align-items: center;
  gap: 6px;
}
.dc-archetype {
  font-size: 11px;
  font-weight: 400;
  color: rgba(255, 255, 255, 0.4);
}
.dc-score {
  margin-left: auto;
  font-size: 14px;
  font-weight: 700;
}
.dc-message {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.7);
  line-height: 1.5;
  margin-bottom: 2px;
}
.dc-reason {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.35);
}
.dc-meta {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.4);
  margin-top: 2px;
}

.planet-hint {
  margin-top: 20px;
  padding: 20px;
  text-align: center;
  color: rgba(255, 255, 255, 0.35);
  font-size: 14px;
  border: 1px dashed rgba(255, 255, 255, 0.08);
  border-radius: 16px;
}
</style>
