<template>
  <div class="portrait-section">
    <div class="portrait-header">
      <h2 class="portrait-title">🎨 灵魂画像</h2>
      <p class="portrait-desc">你的十颗行星内在能量分布——每一条光线都是一个维度的你</p>
    </div>

    <!-- SVG 星盘图 -->
    <div class="portrait-chart">
      <svg viewBox="0 0 360 360" class="portrait-svg">
        <defs>
          <radialGradient id="crystal-grad">
            <stop offset="0%" stop-color="rgba(255,255,255,0.9)" />
            <stop offset="50%" stop-color="rgba(255,245,238,0.5)" />
            <stop offset="100%" stop-color="rgba(255,240,245,0.2)" />
          </radialGradient>
          <filter id="glow-soft">
            <feGaussianBlur stdDeviation="2" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        <!-- 同心参考环 -->
        <circle cx="180" cy="180" r="40" fill="none" stroke="rgba(0,0,0,0.04)" stroke-width="0.5" />
        <circle cx="180" cy="180" r="80" fill="none" stroke="rgba(0,0,0,0.03)" stroke-width="0.5" />
        <circle cx="180" cy="180" r="120" fill="none" stroke="rgba(0,0,0,0.02)" stroke-width="0.5" />
        <circle cx="180" cy="180" r="155" fill="none" stroke="rgba(0,0,0,0.02)" stroke-width="0.5" />

        <!-- 中心水晶球 -->
        <circle cx="180" cy="180" r="36" fill="url(#crystal-grad)" stroke="rgba(0,0,0,0.06)" stroke-width="1" />
        <text x="180" y="176" text-anchor="middle" font-size="11" fill="#8b7355" font-weight="600">灵魂</text>
        <text x="180" y="192" text-anchor="middle" font-size="11" fill="#8b7355" font-weight="600">画像</text>

        <!-- 7 条射线 + 行星节点 -->
        <g v-for="ray in rays" :key="ray.planet">
          <!-- 射线 -->
          <line
            :x1="180" :y1="180"
            :x2="ray.endX" :y2="ray.endY"
            :stroke="ray.color"
            :stroke-opacity="ray.isActive ? 0.5 : 0.15"
            :stroke-width="ray.isActive ? 2.5 : 1"
            stroke-linecap="round"
            :filter="ray.isActive ? 'url(#glow-soft)' : 'none'"
            class="ray-line"
            :style="{ transition: 'all 0.6s ease' }"
          />

          <!-- 行星节点 -->
          <g
            class="ray-node"
            :class="{ 'ray-node--active': ray.isActive }"
            @click="activePlanet = ray.planet"
            style="cursor: pointer;"
          >
            <!-- 外环 -->
            <circle
              :cx="ray.endX" :cy="ray.endY"
              :r="ray.isActive ? 20 : 16"
              :fill="ray.isActive ? ray.color + '20' : 'rgba(255,255,255,0.6)'"
              :stroke="ray.color"
              :stroke-width="ray.isActive ? 2 : 1"
              :filter="ray.isActive ? 'url(#glow-soft)' : 'none'"
              style="transition: all 0.35s ease;"
            />
            <!-- 符号 -->
            <text
              :x="ray.endX" :y="ray.endY"
              text-anchor="middle"
              dominant-baseline="central"
              :font-size="ray.isActive ? 18 : 14"
              :fill="ray.isActive ? ray.color : '#8b7355'"
              font-weight="bold"
              style="transition: all 0.35s ease;"
            >{{ ray.symbol }}</text>
          </g>

          <!-- 强度百分比 -->
          <text
            :x="ray.labelX" :y="ray.labelY"
            text-anchor="middle"
            dominant-baseline="central"
            font-size="10"
            font-weight="600"
            :fill="ray.color"
            :opacity="ray.isActive ? 1 : 0.5"
          >
            {{ ray.strength }}%
          </text>
        </g>
      </svg>
    </div>

    <!-- 选中星灵信息 -->
    <div class="portrait-info" v-if="activePlanetInfo" :style="{ '--pi-color': activePlanetInfo.color }">
      <div class="pi-header">
        <span class="pi-symbol">{{ activePlanetInfo.symbol }}</span>
        <div class="pi-meta">
          <span class="pi-name">{{ activePlanetInfo.name }}</span>
          <span class="pi-archetype">{{ activePlanetInfo.archetype }}</span>
        </div>
        <span class="pi-strength" :style="{ color: activePlanetInfo.color }">
          {{ activePlanetInfo.strength }}%
        </span>
      </div>
      <p class="pi-essence">"{{ activePlanetInfo.essence }}"</p>
      <div class="pi-tags">
        <span class="pi-tag">{{ activePlanetInfo.signLabel }}</span>
        <span class="pi-tag">{{ activePlanetInfo.dignityLabel }}</span>
        <span class="pi-tag">{{ activePlanetInfo.roleTag }}</span>
      </div>
    </div>

    <!-- 图例 -->
    <p class="portrait-legend">
      💡 点击外层行星节点，查看每个维度的详细信息
    </p>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from "vue";
import type { PlanetCharacterProfile, PlanetCharacterProfilesData } from "@/utils/types";

const props = defineProps<{
  planetProfiles: PlanetCharacterProfilesData | null;
}>();

const activePlanet = ref("SUN");

const activePlanetInfo = computed(() => {
  const profile = props.planetProfiles?.planet_characters?.[activePlanet.value];
  if (!profile) return null;
  const p = profile as PlanetCharacterProfile;
  return {
    symbol: p.persona?.symbol || "●",
    name: p.persona?.name_zh || "",
    archetype: p.persona?.archetype_zh || "",
    color: p.persona?.visual_color || "#999",
    essence: p.persona?.essence || "",
    strength: Math.round(p.core_strength || 0),
    signLabel: p.sign_label || "",
    dignityLabel: p.dignity_label || "",
    roleTag: p.role_tag || "",
  };
});

// ── 7 条射线计算 ──
const rayOrder = ["SUN", "MOON", "MERCURY", "VENUS", "MARS", "JUPITER", "SATURN"];

const rays = computed(() => {
  const profiles = props.planetProfiles?.planet_characters || {};
  return rayOrder.map((planetKey, i) => {
    const profile = profiles[planetKey] as PlanetCharacterProfile | undefined;
    const persona = profile?.persona;
    const strength = profile?.core_strength || 30;
    // 角度：从 -90° (顶部) 顺时针，360/7 ≈ 51.4°
    const angle = -90 + i * (360 / 7);
    const rad = (angle * Math.PI) / 180;
    // 射线长度：根据强度，最小 30，最大 150
    const length = 40 + (strength / 100) * 110;
    const endX = 180 + length * Math.cos(rad);
    const endY = 180 + length * Math.sin(rad);
    // 标签位置：比射线末端稍远
    const labelR = length + 18;
    const labelX = 180 + labelR * Math.cos(rad);
    const labelY = 180 + labelR * Math.sin(rad);

    return {
      planet: planetKey,
      symbol: persona?.symbol || "●",
      color: persona?.visual_color || "#999",
      strength: Math.round(strength),
      endX: Math.round(endX),
      endY: Math.round(endY),
      labelX: Math.round(labelX),
      labelY: Math.round(labelY),
      isActive: activePlanet.value === planetKey,
    };
  });
});
</script>

<style scoped>
.portrait-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.portrait-header {
  text-align: center;
}
.portrait-title {
  font-size: 24px;
  font-weight: 700;
  color: #4a3728;
  margin: 0 0 6px;
}
.portrait-desc {
  font-size: 13px;
  color: #8b7355;
  margin: 0;
  max-width: 320px;
  margin: 0 auto;
  line-height: 1.5;
}

.portrait-chart {
  display: flex;
  justify-content: center;
}
.portrait-svg {
  width: 100%;
  max-width: 340px;
  height: auto;
}

/* ── 节点交互 ── */
.ray-node:hover circle {
  filter: brightness(1.2) !important;
}
.ray-node--active circle {
  animation: node-pulse 2.5s ease-in-out infinite;
}
@keyframes node-pulse {
  0%,
  100% {
    r: 20;
  }
  50% {
    r: 22;
  }
}

/* ── 信息卡片 ── */
.portrait-info {
  padding: 18px 20px;
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.8);
  border: 1.5px solid var(--pi-color);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
  transition: all 0.35s ease;
}
.pi-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}
.pi-symbol {
  font-size: 28px;
}
.pi-meta {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 1px;
}
.pi-name {
  font-size: 16px;
  font-weight: 700;
  color: #4a3728;
}
.pi-archetype {
  font-size: 11px;
  color: #8b7355;
}
.pi-strength {
  font-size: 22px;
  font-weight: 800;
}
.pi-essence {
  font-size: 13px;
  color: #5c4a3a;
  line-height: 1.6;
  margin: 0 0 10px;
  font-style: italic;
}
.pi-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.pi-tag {
  font-size: 11px;
  font-weight: 600;
  padding: 4px 12px;
  border-radius: 10px;
  background: rgba(0, 0, 0, 0.04);
  color: #6b5744;
}

.portrait-legend {
  text-align: center;
  font-size: 12px;
  color: #c4b5a5;
  margin: 0;
}
</style>
