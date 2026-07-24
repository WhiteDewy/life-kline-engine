<template>
  <div
    class="app-card"
    :class="[
      `app-card--${variant}`,
      { 'app-card--glass': glass, 'app-card--clickable': clickable, 'app-card--hover': hover }
    ]"
    v-bind="$attrs"
  >
    <div v-if="$slots.header" class="app-card__header">
      <slot name="header" />
    </div>
    <div class="app-card__body">
      <slot />
    </div>
    <div v-if="$slots.footer" class="app-card__footer">
      <slot name="footer" />
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  variant?: "default" | "elevated" | "soft" | "outline";
  glass?: boolean;
  clickable?: boolean;
  hover?: boolean;
}

withDefaults(defineProps<Props>(), {
  variant: "default",
  glass: false,
  clickable: false,
  hover: true,
});
</script>

<style scoped lang="less">
.app-card {
  border-radius: var(--radius-lg);
  overflow: hidden;
  transition: all var(--duration-fast) var(--ease-smooth);
}

.app-card--default {
  background: var(--bg-card);
  border: 1px solid var(--border-light);
  box-shadow: var(--shadow-sm);
}

.app-card--elevated {
  background: var(--bg-card);
  border: 1px solid var(--border-light);
  box-shadow: var(--shadow-card);
}

.app-card--soft {
  background: var(--bg-elevated);
  border: 1px solid var(--border-light);
}

.app-card--outline {
  background: transparent;
  border: 1px solid var(--border-medium);
}

.app-card--glass {
  background: var(--bg-card-glass);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
}

.app-card--hover:hover,
.app-card--clickable:hover {
  box-shadow: var(--shadow-raised);
  transform: translateY(-2px);
}

.app-card--clickable {
  cursor: pointer;
}

.app-card__header {
  padding: var(--space-5) var(--space-5) var(--space-3);
}

.app-card__body {
  padding: var(--space-5);
}

.app-card--default .app-card__body,
.app-card--elevated .app-card__body,
.app-card--soft .app-card__body,
.app-card--outline .app-card__body,
.app-card--glass .app-card__body {
  padding: var(--space-5);
}

.app-card__header + .app-card__body {
  padding-top: 0;
}

.app-card__footer {
  padding: var(--space-3) var(--space-5) var(--space-5);
}

.app-card__header + .app-card__body + .app-card__footer {
  padding-top: 0;
}
</style>
