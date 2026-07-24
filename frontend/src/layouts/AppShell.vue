<template>
  <div class="app-shell">
    <slot name="header" />
    <main class="app-shell__main">
      <slot />
    </main>
    <slot name="footer" />
  </div>
</template>

<script setup lang="ts">
// AppShell 提供基础布局容器，页眉/页脚/底部导航由各页面自行注入
</script>

<style scoped lang="less">
.app-shell {
  min-height: 100vh;
  min-height: 100dvh;
  display: flex;
  flex-direction: column;
  background: var(--bg-main);
  color: var(--text-primary);
}

.app-shell__main {
  flex: 1;
  width: 100%;
  position: relative;
}
</style>
