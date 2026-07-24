<template>
  <div
    class="checkin-bar"
    :class="{ 'checkin-bar--done': checkedIn }"
    @click="!checkedIn && $emit('checkin')"
  >
    <div class="checkin-inner">
      <span class="checkin-icon">{{ checkedIn ? '🌸' : '🌱' }}</span>
      <span class="checkin-text" v-if="checkedIn">
        已签到 · 连续 {{ streakCount }} 天
      </span>
      <span class="checkin-text" v-else>
        今日签到 · 连续 {{ streakCount }} 天
      </span>
      <span class="checkin-streak" v-if="streakCount >= 7">🔥</span>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  checkedIn: boolean;
  streakCount: number;
}>();

defineEmits<{
  checkin: [];
}>();
</script>

<style scoped>
.checkin-bar {
  width: 100%;
  padding: 12px 20px;
  cursor: pointer;
  transition: all 0.3s ease;
}
.checkin-bar:hover {
  transform: scale(1.02);
}
.checkin-bar--done {
  cursor: default;
}
.checkin-bar--done:hover {
  transform: none;
}
.checkin-inner {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 24px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 154, 139, 0.15);
}
.checkin-icon {
  font-size: 18px;
}
.checkin-text {
  font-size: 14px;
  font-weight: 600;
  color: #4a3728;
}
.checkin-streak {
  font-size: 16px;
}
</style>
