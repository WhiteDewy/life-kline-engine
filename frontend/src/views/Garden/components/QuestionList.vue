<template>
  <div class="question-list">
    <div class="ql-header">
      <button class="back-btn" @click="$emit('back')">← 返回</button>
      <h3 class="ql-title">{{ category.icon }} {{ category.label }}</h3>
    </div>
    <p class="ql-desc">{{ category.description }}</p>
    <div class="ql-items">
      <div
        v-for="q in category.questions"
        :key="q.key"
        class="ql-item"
        :class="{ 'ql-item--active': selectedKey === q.key }"
        @click="$emit('select-question', q.key)"
      >
        <div class="ql-item-text">{{ q.label }}</div>
        <div class="ql-item-meta">
          {{ q.houses.map(h => q.house_labels?.[h] ? h + '宫(' + q.house_labels[h] + ')' : h + '宫').join(' · ') }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { GardenCategory } from "@/utils/types";

defineProps<{
  category: GardenCategory;
  selectedKey: string | null;
}>();

defineEmits<{
  "select-question": [key: string];
  back: [];
}>();
</script>

<style scoped>
.question-list {
  padding: 0 4px;
}
.ql-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}
.back-btn {
  padding: 6px 14px;
  border-radius: 14px;
  border: 1px solid rgba(0,0,0,0.08);
  background: rgba(255,255,255,0.6);
  font-size: 13px;
  font-weight: 600;
  color: #8b7355;
  cursor: pointer;
  font-family: inherit;
  transition: all 0.2s;
}
.back-btn:hover {
  background: rgba(255,255,255,0.9);
  color: #4a3728;
}
.ql-title {
  font-size: 20px;
  font-weight: 700;
  color: #4a3728;
  margin: 0;
}
.ql-desc {
  font-size: 13px;
  color: #8b7355;
  margin: 0 0 16px;
  line-height: 1.5;
}
.ql-items {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.ql-item {
  padding: 16px 18px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid rgba(0, 0, 0, 0.05);
  cursor: pointer;
  transition: all 0.25s;
}
.ql-item:hover {
  background: rgba(255, 255, 255, 0.9);
  border-color: rgba(255, 154, 139, 0.25);
  transform: translateX(4px);
}
.ql-item--active {
  border-color: rgba(255, 154, 139, 0.4) !important;
  background: rgba(255, 154, 139, 0.08) !important;
}
.ql-item-text {
  font-size: 15px;
  font-weight: 600;
  color: #4a3728;
  margin-bottom: 4px;
}
.ql-item-meta {
  font-size: 11px;
  color: #a89880;
}
</style>
