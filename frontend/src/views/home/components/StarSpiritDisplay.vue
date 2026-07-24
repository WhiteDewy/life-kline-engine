<template>
  <div class="star-spirit-display" @click="$emit('chat')">
    <div class="spirit-ring" :style="ringStyle">
      <SpiritAvatar
        :planet="planet"
        :symbol="symbol"
        :color="color"
        :name="planetName"
        :gender="gender"
        size="sm"
      />
    </div>
    <div class="spirit-info">
      <span class="spirit-label">今日星灵</span>
      <span class="spirit-name">{{ planetName }} · {{ planetSign }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import SpiritAvatar from "@/components/garden/SpiritAvatar.vue";

const props = defineProps<{
  planet: string;
  planetName: string;
  planetSign: string;
  symbol: string;
  color: string;
  gender: string;
}>();

defineEmits<{
  chat: [];
}>();

const ringStyle = computed(() => ({
  "--ring-color": props.color,
}));
</script>

<style scoped lang="less">
.star-spirit-display {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-smooth);
  padding: 6px 16px 6px 8px;
  border-radius: var(--radius-full);
  background: var(--bg-card-glass);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.5);
  user-select: none;
}

.star-spirit-display:hover {
  background: var(--bg-card);
  transform: scale(1.02);
  box-shadow: var(--shadow-card);
}

.star-spirit-display:active {
  transform: scale(0.98);
}

.spirit-ring {
  position: relative;
  width: 34px;
  height: 34px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: ring-pulse 2.5s ease-in-out infinite;
  box-shadow: 0 0 0 0 var(--ring-color);
}

@keyframes ring-pulse {
  0% { box-shadow: 0 0 0 0 color-mix(in srgb, var(--ring-color) 35%, transparent); }
  50% { box-shadow: 0 0 0 8px color-mix(in srgb, var(--ring-color) 8%, transparent); }
  100% { box-shadow: 0 0 0 0 color-mix(in srgb, var(--ring-color) 35%, transparent); }
}

.spirit-info {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 1px;
}

.spirit-label {
  font-size: 10px;
  color: var(--text-tertiary);
  letter-spacing: 0.5px;
  font-weight: var(--font-medium);
}

.spirit-name {
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
  white-space: nowrap;
  letter-spacing: 0.3px;
}
</style>
