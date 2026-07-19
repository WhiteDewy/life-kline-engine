<template>
  <div class="transit-panel" v-if="transits.length">
    <div class="transit-header">
      <h3 class="transit-title">{{ title }}</h3>
      <span class="transit-sub">{{ subtitle }}</span>
    </div>

    <div class="transit-cards">
      <div
        v-for="(t, i) in displayTransits"
        :key="'transit-' + i"
        class="transit-card"
        :class="t.intensity"
      >
        <div class="transit-top">
          <span class="transit-planets">
            <strong>{{ t.transiting_label }}</strong>
            <span class="transit-aspect">{{ t.aspect_label }}</span>
            <strong>{{ t.natal_label }}</strong>
          </span>
          <span class="transit-orb">容许 {{ t.orb }}°</span>
        </div>
        <p class="transit-text">{{ t.highlight }}</p>
        <div class="transit-bar-wrap">
          <div class="transit-bar" :style="{ width: t.strengthPct + '%' }"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";

interface TransitItem {
  transiting_planet?: string;
  transiting_label: string;
  natal_planet?: string;
  natal_label: string;
  aspect_type?: string;
  aspect_label: string;
  orb: number;
  strength: number;
  is_applying: boolean;
  highlight: string;
}

const props = withDefaults(defineProps<{
  transits: TransitItem[];
  title?: string;
  subtitle?: string;
}>(), {
  title: "⚡ 此刻行运",
  subtitle: "当前天空行星与你本命盘的互动",
});

const displayTransits = computed(() => {
  // Show top 4, skip self-aspects (transiting planet same as natal)
  return props.transits
    .filter((t) => t.transiting_planet !== t.natal_planet)
    .slice(0, 4)
    .map((t) => ({
      ...t,
      strengthPct: Math.round(t.strength * 100),
      intensity: t.strength > 0.6 ? "high" : t.strength > 0.4 ? "mid" : "low",
    }));
});
</script>

<style scoped lang="less">
.transit-panel {
  margin: 32px 0;
  padding: 24px 0 16px;
  border-top: 1px solid rgba(0,0,0,0.06);
}

.transit-header {
  display: flex;
  align-items: baseline;
  gap: 10px;
  margin-bottom: 16px;
}

.transit-title {
  margin: 0;
  color: #4a3728;
  font-size: 18px;
}

.transit-sub {
  color: #a89880;
  font-size: 12px;
}

.transit-cards {
  display: grid;
  gap: 10px;
}

.transit-card {
  padding: 14px 16px;
  border-radius: 14px;
  border: 1px solid rgba(0,0,0,0.06);
  background: rgba(255,255,255, 0.5);

  &.high {
    border-color: rgba(255,154,139, 0.2);
    background: rgba(255,154,139, 0.06);
  }
}

.transit-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.transit-planets {
  font-size: 14px;
  color: #4a3728;
}

.transit-planets strong {
  color: #4a3728;
}

.transit-aspect {
  margin: 0 6px;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 11px;
  background: rgba(0,0,0,0.06);
  color: #8b7355;
}

.transit-orb {
  font-size: 11px;
  color: #a89880;
}

.transit-text {
  margin: 0 0 10px;
  font-size: 13px;
  color: #8b7355;
  line-height: 1.7;
}

.transit-bar-wrap {
  height: 3px;
  border-radius: 2px;
  background: rgba(0,0,0,0.06);
  overflow: hidden;
}

.transit-bar {
  height: 100%;
  border-radius: 2px;
  background: linear-gradient(90deg, rgba(255,154,139, 0.5), rgba(255,154,139, 0.9));
  transition: width 0.4s;
}
</style>
