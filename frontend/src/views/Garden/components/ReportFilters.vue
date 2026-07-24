<template>
  <div class="report-filters">
    <button
      class="rf-chip"
      :class="{ 'rf-chip--active': !activeFilter }"
      @click="$emit('filter', '')"
    >
      全部
    </button>
    <button
      v-for="cat in categories"
      :key="cat.key"
      class="rf-chip"
      :class="{ 'rf-chip--active': activeFilter === cat.key }"
      @click="$emit('filter', cat.key)"
    >
      {{ cat.icon }} {{ cat.label }}
    </button>
  </div>
</template>

<script setup lang="ts">
import type { GardenCategory } from "@/utils/types";

defineProps<{
  categories: GardenCategory[];
  activeFilter: string;
}>();

defineEmits<{
  filter: [key: string];
}>();
</script>

<style scoped>
.report-filters {
  display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 16px;
}
.rf-chip {
  padding: 6px 14px; border-radius: 14px;
  border: 1px solid rgba(0,0,0,0.08);
  background: rgba(255,255,255,0.5);
  font-size: 12px; font-weight: 600; color: #8b7355;
  cursor: pointer; font-family: inherit; transition: all 0.2s;
}
.rf-chip:hover { background: rgba(255,255,255,0.8); }
.rf-chip--active {
  background: rgba(255,154,139,0.15); border-color: rgba(255,154,139,0.3); color: #4a3728;
}
</style>
