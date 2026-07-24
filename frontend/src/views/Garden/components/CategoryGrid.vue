<template>
  <div class="category-grid">
    <CategoryCard
      v-for="cat in categories"
      :key="cat.key"
      :category="cat"
      @select="$emit('select-category', cat)"
    />
  </div>
</template>

<script setup lang="ts">
import type { GardenCategory } from "@/utils/types";
import CategoryCard from "./CategoryCard.vue";

defineProps<{
  categories: GardenCategory[];
}>();

defineEmits<{
  "select-category": [cat: GardenCategory];
}>();
</script>

<style scoped>
.category-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 16px;
  padding: 0 4px;
}

@media (max-width: 480px) {
  .category-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  }
}
</style>
