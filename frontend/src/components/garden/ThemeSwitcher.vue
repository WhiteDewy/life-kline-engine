<template>
  <div class="theme-switcher">
    <button class="theme-toggle" @click="open = !open" title="切换花园主题">
      🎨
    </button>
    <transition name="theme-drop">
      <div class="theme-panel" v-if="open">
        <button
          v-for="t in themes"
          :key="t.key"
          class="theme-option"
          :class="{ 'theme-option--active': current === t.key }"
          @click="select(t.key)"
        >
          <span class="theme-dot" :style="{ background: t.dot }"></span>
          <span class="theme-label">{{ t.label }}</span>
          <span class="theme-check" v-if="current === t.key">✓</span>
        </button>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";

const props = defineProps<{ current: string }>();
const emit = defineEmits<{ select: [key: string] }>();

const open = ref(false);

const themes = [
  { key: "cream", label: "奶油治愈", dot: "linear-gradient(135deg, #FFF5EE, #FF9A8B)" },
  { key: "night", label: "星空夜幕", dot: "linear-gradient(135deg, #1a1a2e, #9B8EC4)" },
  { key: "sakura", label: "樱花春日", dot: "linear-gradient(135deg, #FFF0F5, #F4A7B9)" },
];

function select(key: string) {
  emit("select", key);
  open.value = false;
}
</script>

<style scoped>
.theme-switcher {
  position: relative;
  z-index: 10;
}
.theme-toggle {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: 1px solid rgba(0, 0, 0, 0.08);
  background: rgba(255, 255, 255, 0.7);
  font-size: 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}
.theme-toggle:hover {
  background: rgba(255, 255, 255, 0.9);
  transform: scale(1.1);
}

.theme-panel {
  position: absolute;
  top: 44px;
  right: 0;
  padding: 8px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.95);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(0, 0, 0, 0.06);
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 140px;
}
.theme-drop-enter-active { transition: all 0.25s cubic-bezier(0.25,0.46,0.45,0.94); }
.theme-drop-leave-active { transition: all 0.15s ease; }
.theme-drop-enter-from { opacity: 0; transform: translateY(-8px); }
.theme-drop-leave-to { opacity: 0; transform: translateY(-4px); }

.theme-option {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border-radius: 12px;
  border: none;
  background: transparent;
  cursor: pointer;
  font-family: inherit;
  font-size: 13px;
  color: #4a3728;
  transition: all 0.15s;
  text-align: left;
}
.theme-option:hover {
  background: rgba(0, 0, 0, 0.04);
}
.theme-option--active {
  background: rgba(255, 154, 139, 0.08);
  font-weight: 600;
}
.theme-dot {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  flex-shrink: 0;
  border: 1px solid rgba(0, 0, 0, 0.08);
}
.theme-label {
  flex: 1;
}
.theme-check {
  font-size: 12px;
  color: #ff9a8b;
}
</style>
