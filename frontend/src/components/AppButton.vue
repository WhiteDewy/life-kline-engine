<template>
  <component
    :is="tag"
    :type="buttonType"
    class="app-button"
    :class="[
      `app-button--${variant}`,
      `app-button--${size}`,
      { 'app-button--block': block, 'app-button--loading': loading, 'app-button--disabled': disabled }
    ]"
    :disabled="disabled || loading"
    v-bind="$attrs"
  >
    <span v-if="loading" class="app-button__spinner" aria-hidden="true" />
    <span class="app-button__content" :class="{ 'is-hidden': loading }">
      <slot />
    </span>
  </component>
</template>

<script setup lang="ts">
import { computed } from "vue";

interface Props {
  variant?: "primary" | "secondary" | "ghost" | "text";
  size?: "sm" | "md" | "lg";
  block?: boolean;
  loading?: boolean;
  disabled?: boolean;
  href?: string;
  type?: "button" | "submit" | "reset";
}

const props = withDefaults(defineProps<Props>(), {
  variant: "primary",
  size: "md",
  block: false,
  loading: false,
  disabled: false,
  type: "button",
});

const tag = computed(() => (props.href ? "a" : "button"));
const buttonType = computed(() => (props.href ? undefined : props.type));
</script>

<style scoped lang="less">
.app-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  font-family: var(--font-sans);
  font-weight: var(--font-semibold);
  border-radius: var(--radius-full);
  transition: all var(--duration-fast) var(--ease-smooth);
  white-space: nowrap;
  user-select: none;
  text-decoration: none;
  position: relative;
}

.app-button:active:not(:disabled) {
  transform: scale(0.98);
}

.app-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Sizes */
.app-button--sm {
  height: 36px;
  padding: 0 16px;
  font-size: var(--text-sm);
}

.app-button--md {
  height: 44px;
  padding: 0 20px;
  font-size: var(--text-base);
}

.app-button--lg {
  height: 52px;
  padding: 0 28px;
  font-size: var(--text-md);
}

/* Variants */
.app-button--primary {
  background: var(--color-primary);
  color: #fff;
  box-shadow: var(--shadow-card);
}

.app-button--primary:hover:not(:disabled) {
  background: var(--color-primary-dark);
  box-shadow: var(--shadow-raised);
  transform: translateY(-1px);
}

.app-button--secondary {
  background: var(--bg-card);
  color: var(--text-primary);
  border: 1px solid var(--border-light);
  box-shadow: var(--shadow-sm);
}

.app-button--secondary:hover:not(:disabled) {
  background: var(--bg-elevated);
  border-color: var(--border-medium);
  color: var(--color-primary);
}

.app-button--ghost {
  background: transparent;
  color: var(--text-secondary);
  border: 1px solid transparent;
}

.app-button--ghost:hover:not(:disabled) {
  background: var(--fill-color);
  color: var(--text-primary);
}

.app-button--text {
  background: transparent;
  color: var(--color-primary);
  padding-left: var(--space-2);
  padding-right: var(--space-2);
}

.app-button--text:hover:not(:disabled) {
  color: var(--color-primary-dark);
}

/* Block */
.app-button--block {
  width: 100%;
}

/* Loading */
.app-button__spinner {
  position: absolute;
  width: 18px;
  height: 18px;
  border: 2px solid currentColor;
  border-right-color: transparent;
  border-radius: 50%;
  animation: button-spin 0.8s linear infinite;
}

.app-button__content.is-hidden {
  opacity: 0;
}

@keyframes button-spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
