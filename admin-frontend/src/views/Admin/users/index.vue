<template>
  <div class="users-page">
    <UsersTable @open-detail="goDetail" />
  </div>
</template>

<script setup lang="ts">
import { useRouter } from "vue-router";
import UsersTable from "../components/UsersTable.vue";

const router = useRouter();

function goDetail(userId: string) {
  router.push(`/admin/users/${userId}`);
}
</script>

<style scoped>
.users-page {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
</style>