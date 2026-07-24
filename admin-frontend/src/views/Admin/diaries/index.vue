<template>
  <div class="diaries-page">
    <DiaryTable @open-detail="goDetail" />
  </div>
</template>

<script setup lang="ts">
import { useRouter } from "vue-router";
import DiaryTable from "../components/DiaryTable.vue";

const router = useRouter();

function goDetail(id: string) {
  router.push(`/admin/diaries/${id}`);
}
</script>

<style scoped>
.diaries-page {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
</style>