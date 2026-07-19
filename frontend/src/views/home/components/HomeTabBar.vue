<template>
  <nav class="tab-bar">
    <button class="tab-btn" @click="$emit('garden')">
      <span class="tab-icon">🌸</span>
      <span class="tab-label">花园</span>
    </button>

    <button class="tab-btn tab-btn--chat" @click="$emit('chat')">
      <span class="tab-icon">💫</span>
      <span class="tab-label">{{ chatCtaText }}</span>
    </button>

    <button class="tab-btn" @click="$emit('council')">
      <span class="tab-icon">🔮</span>
      <span class="tab-label">星灵议会</span>
    </button>
  </nav>
</template>

<script setup lang="ts">
defineProps<{
  chatCtaText: string
}>()

defineEmits<{
  garden: []
  chat: []
  council: []
}>()
</script>

<style scoped>
.tab-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 100;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  gap: 0;
  padding: 0 32px calc(20px + env(safe-area-inset-bottom, 0px));
}

.tab-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: 8px 18px;
  border: none;
  background: transparent;
  cursor: pointer;
  font-family: inherit;
  -webkit-tap-highlight-color: transparent;
  transition: all 0.35s cubic-bezier(0.25, 0.1, 0.25, 1);
  user-select: none;
  opacity: 0.65;
}

.tab-btn:hover {
  opacity: 1;
}

.tab-btn:active {
  transform: scale(0.92);
  opacity: 1;
}

/* ── 中间按钮：更长、更高亮 ── */
.tab-btn--chat {
  padding: 8px 40px;
  opacity: 0.9;
}

.tab-icon {
  font-size: 20px;
  line-height: 1;
  transition: transform 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.tab-btn--chat .tab-icon {
  font-size: 24px;
}

.tab-btn:hover .tab-icon {
  transform: scale(1.12);
}

.tab-label {
  font-size: 10px;
  font-weight: 500;
  color: #fff;
  letter-spacing: 0.3px;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
}

.tab-btn--chat .tab-label {
  font-size: 12px;
  font-weight: 600;
}

/* 响应式 */
@media (max-width: 380px) {
  .tab-bar { padding: 0 20px calc(16px + env(safe-area-inset-bottom, 0px)); }
  .tab-btn { padding: 6px 14px; }
  .tab-btn--chat { padding: 6px 32px; }
  .tab-icon { font-size: 18px; }
  .tab-btn--chat .tab-icon { font-size: 22px; }
}
</style>
