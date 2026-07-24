<template>
  <div class="whisper-card">
    <div class="whisper-wave">
      <svg viewBox="0 0 400 40" preserveAspectRatio="none">
        <path d="M0,20 C80,40 120,0 200,20 C280,40 320,0 400,20 L400,40 L0,40 Z" fill="rgba(255,255,255,0.5)" />
      </svg>
    </div>
    <div class="whisper-body">
      <div class="whisper-moon">🌙</div>
      <h2 class="whisper-title">每日星语</h2>
      <p class="whisper-theme">{{ dailyTheme }}</p>
      <p class="whisper-date">{{ dateLabel }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  dailyTheme: string
  dateLabel: string
}>()
</script>

<style scoped lang="less">
.whisper-card {
  position: relative; border-radius: 28px; overflow: hidden;
  background: linear-gradient(135deg,
    rgba(255,255,255,0.85) 0%,
    rgba(255,245,238,0.8) 50%,
    rgba(255,240,245,0.7) 100%);
  box-shadow: 0 4px 24px rgba(0,0,0,0.04), 0 1px 4px rgba(0,0,0,0.03);
  border: 1px solid rgba(255,255,255,0.8);
}
.whisper-wave { width: 100%; height: 20px; overflow: hidden; }
.whisper-wave svg { width: 100%; height: 100%; }
.whisper-body { padding: 8px 24px 24px; text-align: center; }
.whisper-moon { font-size: 32px; margin-bottom: 8px; animation: moon-glow 2s ease-in-out infinite; }
@keyframes moon-glow { 0%,100%{filter:drop-shadow(0 0 4px rgba(240,192,96,0.3))} 50%{filter:drop-shadow(0 0 12px rgba(240,192,96,0.6))} }
.whisper-title { font-size: 20px; font-weight: 700; color: #4a3728; margin: 0 0 6px; }
.whisper-theme { font-size: 15px; color: #6b5744; margin: 0 0 4px; line-height: 1.6; font-style: italic; }
.whisper-date { font-size: 12px; color: #a89880; margin: 0; }
</style>
