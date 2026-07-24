<template>
  <transition name="sheet-backdrop">
    <div v-if="modelValue" class="app-sheet__backdrop" @click.self="close" />
  </transition>
  <transition :name="`sheet-${position}`">
    <div
      v-if="modelValue"
      class="app-sheet"
      :class="[`app-sheet--${position}`, { 'app-sheet--glass': glass }]"
      :style="sheetStyle"
    >
      <div v-if="showHandle" class="app-sheet__handle" @click="close" />
      <div v-if="$slots.header || title" class="app-sheet__header">
        <slot name="header">
          <h3 class="app-sheet__title">{{ title }}</h3>
        </slot>
        <button v-if="showClose" class="app-sheet__close" aria-label="关闭" @click="close">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M18 6L6 18M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div class="app-sheet__body">
        <slot />
      </div>

      <div v-if="$slots.footer" class="app-sheet__footer">
        <slot name="footer" />
      </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { computed } from "vue";

interface Props {
  modelValue: boolean;
  position?: "bottom" | "left" | "right";
  title?: string;
  showHandle?: boolean;
  showClose?: boolean;
  glass?: boolean;
  maxWidth?: string;
  maxHeight?: string;
}

const props = withDefaults(defineProps<Props>(), {
  position: "bottom",
  showHandle: true,
  showClose: true,
  glass: true,
  maxWidth: "480px",
  maxHeight: "85vh",
});

const emit = defineEmits<{
  (e: "update:modelValue", value: boolean): void;
  (e: "close"): void;
}>();

const sheetStyle = computed(() => ({
  maxWidth: ["left", "right"].includes(props.position) ? props.maxWidth : "100%",
  maxHeight: props.position === "bottom" ? props.maxHeight : "100%",
}));

function close() {
  emit("update:modelValue", false);
  emit("close");
}
</script>

<style scoped lang="less">
.app-sheet__backdrop {
  position: fixed;
  inset: 0;
  background: rgba(44, 38, 34, 0.25);
  backdrop-filter: blur(2px);
  -webkit-backdrop-filter: blur(2px);
  z-index: 190;
}

.app-sheet {
  position: fixed;
  z-index: 200;
  background: var(--bg-card);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.app-sheet--glass {
  background: var(--bg-card-glass);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
}

.app-sheet--bottom {
  left: 0;
  right: 0;
  bottom: 0;
  border-radius: var(--radius-xl) var(--radius-xl) 0 0;
  box-shadow: 0 -8px 32px rgba(44, 38, 34, 0.1);
  padding-bottom: env(safe-area-inset-bottom, 0px);
}

.app-sheet--left {
  left: 0;
  top: 0;
  bottom: 0;
  border-radius: 0 var(--radius-xl) var(--radius-xl) 0;
  box-shadow: 8px 0 32px rgba(44, 38, 34, 0.08);
}

.app-sheet--right {
  right: 0;
  top: 0;
  bottom: 0;
  border-radius: var(--radius-xl) 0 0 var(--radius-xl);
  box-shadow: -8px 0 32px rgba(44, 38, 34, 0.08);
}

.app-sheet__handle {
  display: flex;
  justify-content: center;
  padding: var(--space-3) 0 var(--space-2);
  cursor: pointer;
}

.app-sheet__handle::before {
  content: "";
  width: 36px;
  height: 4px;
  border-radius: 2px;
  background: var(--border-medium);
  transition: background var(--duration-fast) var(--ease-smooth);
}

.app-sheet__handle:hover::before {
  background: var(--border-dark);
}

.app-sheet__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-4) var(--space-5) var(--space-3);
  border-bottom: 1px solid var(--border-light);
  flex-shrink: 0;
}

.app-sheet__title {
  font-size: var(--text-lg);
  font-weight: var(--font-bold);
  color: var(--text-primary);
}

.app-sheet__close {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-full);
  color: var(--text-tertiary);
  transition: all var(--duration-fast) var(--ease-smooth);
}

.app-sheet__close:hover {
  background: var(--fill-color);
  color: var(--text-primary);
}

.app-sheet__body {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-4) var(--space-5);
}

.app-sheet__footer {
  padding: var(--space-3) var(--space-5) calc(var(--space-5) + env(safe-area-inset-bottom, 0px));
  border-top: 1px solid var(--border-light);
  flex-shrink: 0;
}

/* Transitions */
.sheet-backdrop-enter-active,
.sheet-backdrop-leave-active {
  transition: opacity var(--duration-normal) var(--ease-smooth);
}

.sheet-backdrop-enter-from,
.sheet-backdrop-leave-to {
  opacity: 0;
}

.sheet-bottom-enter-active,
.sheet-bottom-leave-active {
  transition: transform var(--duration-normal) var(--ease-emotional);
}

.sheet-bottom-enter-from,
.sheet-bottom-leave-to {
  transform: translateY(100%);
}

.sheet-left-enter-active,
.sheet-left-leave-active,
.sheet-right-enter-active,
.sheet-right-leave-active {
  transition: transform var(--duration-normal) var(--ease-emotional);
}

.sheet-left-enter-from,
.sheet-left-leave-to {
  transform: translateX(-100%);
}

.sheet-right-enter-from,
.sheet-right-leave-to {
  transform: translateX(100%);
}
</style>
