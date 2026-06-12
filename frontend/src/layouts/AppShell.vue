<template>
  <div class="shell">
    <SiteHeader @help="$emit('help')" @history="$emit('history')" />
    <main class="content">
      <slot />
    </main>
    <SiteFooter @help="$emit('help')" @history="$emit('history')" />
  </div>
</template>

<script setup lang="ts">
import SiteHeader from "@/components/SiteHeader.vue";
import SiteFooter from "@/components/SiteFooter.vue";

defineEmits<{
  (e: "help"): void;
  (e: "history"): void;
}>();
</script>

<style scoped>
.shell {
  min-height: 100vh;
  background: var(--bg);
}
.content {
  /* Remove width restriction for full-width landing page design */
  width: 100%;
  margin: 0;
  padding: calc(var(--h-header)) 0 0;
}
</style>
