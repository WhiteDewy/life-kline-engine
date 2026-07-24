<template>
  <div class="fast-transit-bar" v-if="items.length">
    <div class="ftb-header">
      <span class="ftb-title">⚡ 近期行运提醒</span>
      <span class="ftb-sub">快行星（日月水金火）未来几天的触发</span>
    </div>
    <div class="ftb-scroll">
      <div class="ftb-card" v-for="t in items" :key="t.key">
        <span class="ftb-planet">{{ t.transitingLabel }}</span>
        <span class="ftb-aspect" :class="t.aspectClass">{{ t.aspectLabel }}</span>
        <span class="ftb-target">{{ t.natalLabel }}</span>
        <span class="ftb-highlight">{{ t.highlight }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { TransitItem } from "@/utils/types";

const props = defineProps<{
  transits: TransitItem[];
}>();

const PLANET_SHORT: Record<string, string> = {
  sun: "太阳",
  moon: "月亮",
  mercury: "水星",
  venus: "金星",
  mars: "火星",
  jupiter: "木星",
  saturn: "土星",
  uranus: "天王星",
  neptune: "海王星",
  pluto: "冥王星",
};

const ASPECT_CLASS: Record<string, string> = {
  conjunction: "asp-conj",
  sextile: "asp-sext",
  square: "asp-sq",
  trine: "asp-tri",
  opposition: "asp-opp",
};

const items = computed(() =>
  props.transits.slice(0, 6).map((t, i) => ({
    key: `${t.transiting_label}-${t.natal_label}-${i}`,
    transitingLabel: PLANET_SHORT[t.transiting_label?.toLowerCase()] || t.transiting_label,
    natalLabel: PLANET_SHORT[t.natal_label?.toLowerCase()] || t.natal_label,
    aspectLabel: t.aspect_label || t.aspect_type,
    aspectClass: ASPECT_CLASS[t.aspect_type || ""] || "",
    highlight: t.highlight || "",
  }))
);
</script>

<style scoped lang="less">
.fast-transit-bar {
  margin: 14px 0;
  padding: 16px 18px;
  border-radius: 16px;
  border: 1px solid rgba(0,0,0,0.06);
  background: rgba(255,255,255, 0.40);
}
.ftb-header {
  display: flex;
  align-items: baseline;
  gap: 10px;
  margin-bottom: 12px;
}
.ftb-title {
  color: #4a3728;
  font-size: 14px;
  font-weight: 600;
}
.ftb-sub {
  color: #a89880;
  font-size: 12px;
}
.ftb-scroll {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding-bottom: 4px;
}
.ftb-scroll::-webkit-scrollbar { height: 3px; }
.ftb-scroll::-webkit-scrollbar-thumb { background: #334155; border-radius: 2px; }
.ftb-card {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border-radius: 999px;
  border: 1px solid rgba(255,255,255,0.06);
  background: rgba(255,255,255,0.02);
  white-space: nowrap;
  flex-shrink: 0;
}
.ftb-planet {
  color: #4a3728;
  font-size: 13px;
  font-weight: 600;
}
.ftb-aspect {
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 999px;
}
.asp-conj { background: rgba(212,175,55,0.15); color: #ff9a8b; }
.asp-sext { background: rgba(99,102,241,0.12); color: #a5b4fc; }
.asp-sq  { background: rgba(244,63,94,0.12); color: #fca5a5; }
.asp-tri { background: rgba(16,185,129,0.12); color: #6ee7b7; }
.asp-opp { background: rgba(251,191,36,0.12); color: #fbbf24; }
.ftb-target {
  color: #8b7355;
  font-size: 13px;
}
.ftb-highlight {
  color: #a89880;
  font-size: 12px;
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
