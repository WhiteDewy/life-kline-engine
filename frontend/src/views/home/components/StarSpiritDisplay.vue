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
  planet: string
  planetName: string
  planetSign: string
  symbol: string
  color: string
  gender: string
}>()

defineEmits<{
  chat: []
}>()

const ringStyle = computed(() => ({
  '--ring-color': props.color,
}));
</script>

<style scoped>
.star-spirit-display {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  transition: all 0.25s ease;
  padding: 4px 14px 4px 6px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  user-select: none;
}
.star-spirit-display:hover {
  background: rgba(255, 255, 255, 0.25);
  transform: scale(1.03);
}
.star-spirit-display:active {
  transform: scale(0.97);
}

/* ── 呼吸光晕环 ── */
.spirit-ring {
  position: relative;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: ring-pulse 2.5s ease-in-out infinite;
  box-shadow: 0 0 0 0 var(--ring-color);
}

@keyframes ring-pulse {
  0% {
    box-shadow: 0 0 0 0 color-mix(in srgb, var(--ring-color) 40%, transparent);
  }
  50% {
    box-shadow: 0 0 0 8px color-mix(in srgb, var(--ring-color) 10%, transparent);
  }
  100% {
    box-shadow: 0 0 0 0 color-mix(in srgb, var(--ring-color) 40%, transparent);
  }
}

/* ── 信息 ── */
.spirit-info {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 1px;
}
.spirit-label {
  font-size: 9px;
  color: rgba(255, 255, 255, 0.6);
  letter-spacing: 0.5px;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}
.spirit-name {
  font-size: 12px;
  font-weight: 600;
  color: #fff;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
  white-space: nowrap;
  letter-spacing: 0.3px;
}
</style>
