<template>
  <div class="shell">
    <main class="content">
      <slot />
    </main>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  loggedIn?: boolean;
  userPhone?: string;
}>();

defineEmits<{
  login: [];
  history: [];
}>();
</script>

<style scoped>
.shell {
  min-height: 100vh;
  background: var(--bg);
}
.content {
  width: 100%;
}
</style>
