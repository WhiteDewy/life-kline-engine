<template>
  <div
    class="sign-card"
    :style="{ '--sign-color': color, '--sign-color-light': color + '18' }"
  >
    <!-- 头部：符号 + 名字 + 原型 -->
    <div class="sign-header">
      <span class="sign-symbol">{{ symbol }}</span>
      <div class="sign-meta">
        <span class="sign-name">{{ name }}</span>
        <span class="sign-archetype">{{ archetype }}</span>
      </div>
      <span class="sign-presence" :style="{ color }">
        {{ presenceScore }}%
      </span>
    </div>

    <!-- 角色标签 -->
    <span class="sign-role-tag" v-if="roleTag">{{ roleTag }}</span>

    <!-- 宫位覆盖 -->
    <div class="sign-section" v-if="houseCusps.length > 0">
      <span class="section-label">🏛 所在宫位</span>
      <div class="house-chips">
        <span
          v-for="h in houseCusps"
          :key="h"
          class="house-chip"
          :style="{ borderColor: color + '44' }"
        >
          第{{ h }}宫
        </span>
      </div>
      <p class="section-note" v-if="houseCusps.length > 0">
        此星座的风格在你星盘的这些领域发挥作用
      </p>
    </div>

    <!-- 落入星体 -->
    <div class="sign-section">
      <span class="section-label">🪐 落入星体</span>
      <div v-if="planetsHere.length > 0" class="planet-chips">
        <span
          v-for="pl in planetsHere"
          :key="pl.planet"
          class="planet-chip"
          :style="{ background: pl.color + '22', borderColor: pl.color + '44' }"
        >
          {{ pl.symbol }} {{ pl.label }}
          <span class="planet-dignity" v-if="pl.dignity">{{ pl.dignity }}</span>
        </span>
      </div>
      <p v-else class="section-empty">
        无星体落入——但此星座的特质仍通过宫头守护星和相位网络表达。
        没有星体落入不代表你没有这个星座的特质。
      </p>
    </div>

    <!-- 守护星 + 飞星线索 -->
    <div class="sign-section" v-if="rulingPlanet">
      <span class="section-label">🔗 守护星</span>
      <button
        class="ruler-link"
        :style="{ color: rulingPlanet.color }"
        @click="$emit('view-spirit', rulingPlanet.planet)"
      >
        {{ rulingPlanet.symbol }} {{ rulingPlanet.label }}
        <span class="link-arrow">→</span>
      </button>
      <p class="section-note">
        此星座的风格由{{ rulingPlanet.label }}掌管——查看{{ rulingPlanet.label }}灵可了解这个星座能量如何在你星盘中运作
      </p>
    </div>

    <!-- 一句话 -->
    <p class="sign-essence" v-if="essence">"{{ essence }}"</p>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { PLANET_LABELS, PLANET_COLORS_MAP, PLANET_SYMBOLS, SIGN_RULER_MAP } from "@/config/zodiac";

const props = defineProps<{
  sign: string;
  symbol: string;
  name: string;
  archetype: string;
  color: string;
  essence: string;
  presenceScore: number;
  roleTag: string;
  houseCusps: number[];
  planetsHere: Array<{ planet: string; label: string; symbol: string; color: string; dignity: string }>;
  isAscendant: boolean;
}>();

defineEmits<{
  "view-spirit": [planet: string];
}>();

const rulingPlanet = computed(() => {
  const rulerKey = (SIGN_RULER_MAP as Record<string, string>)[props.sign];
  if (!rulerKey) return null;
  return {
    planet: rulerKey,
    label: (PLANET_LABELS as Record<string, string>)[rulerKey] || rulerKey,
    symbol: (PLANET_SYMBOLS as Record<string, string>)[rulerKey] || "●",
    color: PLANET_COLORS_MAP[rulerKey] || "#999",
  };
});
</script>

<style scoped>
.sign-card {
  padding: 20px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.75);
  backdrop-filter: blur(10px);
  border: 1px solid var(--sign-color-light);
  box-shadow: 0 2px 16px rgba(0, 0, 0, 0.04);
  display: flex;
  flex-direction: column;
  gap: 14px;
  transition: all 0.25s;
}
.sign-card:hover {
  border-color: var(--sign-color);
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.06);
}

/* 头部 */
.sign-header {
  display: flex;
  align-items: center;
  gap: 12px;
}
.sign-symbol {
  font-size: 32px;
  width: 44px;
  text-align: center;
  flex-shrink: 0;
}
.sign-meta {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.sign-name {
  font-size: 17px;
  font-weight: 700;
  color: #4a3728;
}
.sign-archetype {
  font-size: 12px;
  color: #8b7355;
}
.sign-presence {
  font-size: 14px;
  font-weight: 700;
  flex-shrink: 0;
}

/* 角色标签 */
.sign-role-tag {
  display: inline-block;
  font-size: 11px;
  font-weight: 600;
  padding: 3px 12px;
  border-radius: 10px;
  background: rgba(255, 200, 160, 0.25);
  color: #8b5a3a;
  align-self: flex-start;
}

/* 通用区块 */
.sign-section {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.section-label {
  font-size: 13px;
  font-weight: 600;
  color: #6b5744;
}
.section-note {
  font-size: 11px;
  color: #a89880;
  margin: 0;
}
.section-empty {
  font-size: 12px;
  color: #8b7355;
  margin: 0;
  line-height: 1.6;
  padding: 8px 12px;
  background: rgba(0, 0, 0, 0.02);
  border-radius: 10px;
  border-left: 3px solid var(--sign-color);
}

/* 宫位 chips */
.house-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.house-chip {
  font-size: 12px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 10px;
  border: 1px solid;
  color: #6b5744;
}

/* 行星 chips */
.planet-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.planet-chip {
  font-size: 12px;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 10px;
  border: 1px solid;
  color: #4a3728;
  display: flex;
  align-items: center;
  gap: 4px;
}
.planet-dignity {
  font-size: 10px;
  color: #8b7355;
  font-weight: 400;
}

/* 守护星链接 */
.ruler-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 600;
  padding: 6px 14px;
  border-radius: 12px;
  border: 1px solid;
  border-color: currentColor;
  background: transparent;
  cursor: pointer;
  font-family: inherit;
  transition: all 0.2s;
  align-self: flex-start;
}
.ruler-link:hover {
  background: currentColor;
  color: #fff !important;
}
.link-arrow {
  font-size: 12px;
  opacity: 0.6;
}

/* 一句话 */
.sign-essence {
  font-size: 12px;
  color: #a89880;
  font-style: italic;
  text-align: center;
  margin: 0;
  padding-top: 4px;
  border-top: 1px solid rgba(0, 0, 0, 0.04);
}
</style>
