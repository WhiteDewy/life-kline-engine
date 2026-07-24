<template>
  <div class="fortune-section">
    <h3 class="section-title">🌌 运势导航</h3>
    <div class="fortune-chips">
      <div
        v-for="item in items"
        :key="item.key"
        class="fortune-chip"
        :class="{ 'fortune-chip--planned': item.status === 'planned' }"
      >
        <span class="chip-icon">{{ item.icon }}</span>
        <span class="chip-label">{{ item.label }}</span>
        <span v-if="item.status === 'planned'" class="chip-badge">即将</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { FortuneItem } from "@/utils/types";

defineProps<{
  items: FortuneItem[];
}>();
</script>

<style scoped lang="less">
.fortune-section {
  padding: 12px 0;
}
.section-title {
  font-size: 16px;
  font-weight: 700;
  color: #4a3728;
  margin: 0 0 12px;
}
.fortune-chips {
  display: flex;
  gap: 10px;
  overflow-x: auto;
  padding-bottom: 4px;
  scrollbar-width: none;
}
.fortune-chips::-webkit-scrollbar {
  display: none;
}
.fortune-chip {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 18px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.65);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(0, 0, 0, 0.06);
  cursor: pointer;
  transition: all 0.25s;
}
.fortune-chip:hover {
  background: rgba(255, 255, 255, 0.85);
  transform: translateY(-2px);
}
.fortune-chip--planned {
  opacity: 0.5;
  cursor: default;
  pointer-events: none;
}
.chip-icon {
  font-size: 18px;
}
.chip-label {
  font-size: 13px;
  font-weight: 600;
  color: #4a3728;
  white-space: nowrap;
}
.chip-badge {
  font-size: 10px;
  padding: 2px 8px;
  border-radius: 8px;
  background: rgba(255, 154, 139, 0.15);
  color: #8b7355;
  font-weight: 600;
}
</style>
