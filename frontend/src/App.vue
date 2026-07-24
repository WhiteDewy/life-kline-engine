<template>
  <AppShell>
    <router-view v-slot="{ Component }">
      <transition name="page-fade" mode="out-in">
        <component :is="Component" />
      </transition>
    </router-view>
  </AppShell>
</template>

<script setup lang="ts">
import AppShell from "@/layouts/AppShell.vue";
</script>

<style>
/* ── 页面切换过渡 ── */
.page-fade-enter-active,
.page-fade-leave-active {
  transition: opacity 0.35s var(--ease-smooth), transform 0.35s var(--ease-smooth);
}
.page-fade-enter-from {
  opacity: 0;
  transform: translateY(12px);
}
.page-fade-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>
