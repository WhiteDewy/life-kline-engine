<template>
  <div class="reports-page">
    <ReportsTable @open-detail="goDetail" />
  </div>
</template>

<script setup lang="ts">
import { useRouter } from "vue-router";
import ReportsTable from "../components/ReportsTable.vue";

const router = useRouter();

function goDetail(id: string) {
  router.push(`/admin/reports/${id}`);
}
</script>

<style scoped>
.reports-page {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
</style>