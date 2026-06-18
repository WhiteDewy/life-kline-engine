<template>
  <footer class="siteFooter">
    <div class="content">
      <p class="meta">
        © {{ new Date().getFullYear() }} Life Kline Engine · 一个把占星翻译成现实决策语言的人生解读项目
      </p>
      <p class="core">先看天赋底盘，再看阶段节奏；要相信自己人生有无限可能性。</p>
    </div>
  </footer>
</template>

<script setup lang="ts">
defineEmits<{
  (e: "help"): void;
  (e: "history"): void;
}>();
</script>

<style scoped>
.siteFooter {
  margin-top: auto;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(2, 6, 23, 0.72);
  backdrop-filter: blur(10px);
}

.content {
  max-width: var(--page-shell-max);
  margin: 0 auto;
  padding: 18px 16px 22px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  text-align: center;
}

.content p {
  margin: 0;
}

.meta {
  color: var(--text-secondary);
  font-size: 11.5px;
  line-height: 1.5;
}

.core {
  color: var(--text);
  font-size: 12.5px;
  font-weight: 600;
  line-height: 1.6;
}

@media (max-width: 420px) {
  .core {
    font-size: 12px;
  }
}
</style>
