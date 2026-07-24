<template>
  <div>
    <StatsPanel :stats="stats" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import adminApi from "@/config/adminApi";
import StatsPanel from "./components/StatsPanel.vue";

const stats = ref<any>(null);

async function loadStats() {
  try {
    const res = await adminApi.get("/stats");
    if (res.data?.status === "success") {
      stats.value = res.data.data;
    }
  } catch {
    // ignore
  }
}

onMounted(loadStats);
</script>