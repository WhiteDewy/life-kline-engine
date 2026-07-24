<template>
  <div class="category-card" @click="$emit('select')">
    <div class="card-icon">{{ category.icon }}</div>
    <div class="card-label">{{ category.label }}</div>
    <div class="card-desc">{{ category.description }}</div>
    <div class="card-count">{{ category.question_count }} 个入口</div>
  </div>
</template>

<script setup lang="ts">
import type { GardenCategory } from "@/utils/types";

defineProps<{
  category: GardenCategory;
}>();

defineEmits<{
  select: [];
}>();
</script>

<style scoped>
.category-card {
  padding: 20px 16px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(0, 0, 0, 0.05);
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.25, 0.1, 0.25, 1);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  text-align: center;
}
.category-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.08);
  border-color: rgba(255, 154, 139, 0.3);
  background: rgba(255, 255, 255, 0.9);
}
.category-card:active {
  transform: scale(0.96);
}
.card-icon {
  font-size: 32px;
  line-height: 1;
}
.card-label {
  font-size: 15px;
  font-weight: 700;
  color: #4a3728;
}
.card-desc {
  font-size: 12px;
  color: #8b7355;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.card-count {
  font-size: 11px;
  font-weight: 600;
  color: #a89880;
  background: rgba(255, 154, 139, 0.1);
  padding: 4px 12px;
  border-radius: 10px;
}
</style>
