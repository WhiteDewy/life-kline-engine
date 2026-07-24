<template>
  <nav class="tab-bar">
    <button
      v-for="tab in tabs"
      :key="tab.key"
      class="tab-btn"
      :class="{ 'tab-btn--active': activeTab === tab.key }"
      @click="$emit('select', tab.key)"
    >
      <span class="tab-icon">{{ tab.icon }}</span>
      <span class="tab-label">{{ tab.label }}</span>
      <span v-if="tab.badge" class="tab-badge">{{ tab.badge }}</span>
    </button>
  </nav>
</template>

<script setup lang="ts">
defineProps<{
  activeTab: string;
}>();

defineEmits<{
  select: [key: string];
}>();

const tabs: Array<{ key: string; icon: string; label: string; badge?: string }> = [
  { key: "garden", icon: "🌸", label: "花园" },
  { key: "codex", icon: "📜", label: "宝典" },
  { key: "journal", icon: "💎", label: "日记" },
  { key: "council", icon: "🔮", label: "议会" },
];
</script>

<style scoped>
.tab-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 100;
  display: flex;
  justify-content: center;
  gap: 8px;
  padding: 8px 16px calc(8px + env(safe-area-inset-bottom, 0px));
  background: rgba(255, 255, 255, 0.82);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-top: 1px solid rgba(0, 0, 0, 0.05);
}

.tab-btn {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: 8px 28px;
  border: none;
  border-radius: 20px;
  background: transparent;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  font-family: inherit;
  -webkit-tap-highlight-color: transparent;
}

.tab-btn--active {
  background: rgba(255, 154, 139, 0.12);
}

.tab-icon {
  font-size: 22px;
  transition: transform 0.3s;
  line-height: 1;
}
.tab-btn--active .tab-icon {
  transform: scale(1.15);
}

.tab-label {
  font-size: 11px;
  font-weight: 600;
  color: #a89880;
  transition: color 0.3s;
}
.tab-btn--active .tab-label {
  color: #4a3728;
}

.tab-badge {
  position: absolute;
  top: 2px;
  right: 14px;
  min-width: 16px;
  height: 16px;
  padding: 0 5px;
  border-radius: 8px;
  background: #ff9a8b;
  color: #fff;
  font-size: 10px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
