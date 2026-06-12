<template>
  <AppShell @help="onHelp" @history="onHistory"> <router-view /></AppShell>
</template>
<script setup lang="ts">
import AppShell from "@/layouts/AppShell.vue";

function onHelp() {
  // 打开 Element Plus Dialog / Drawer
}
function onHistory() {
  // 打开历史记录页 / Drawer
}
</script>
<style></style>
