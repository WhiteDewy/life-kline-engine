<template>
  <div class="welcome-card" @click="$emit('go-login')">
    <div class="wc-icon">🌸</div>
    <h1 class="wc-title">星灵花园</h1>
    <p class="wc-desc">
      十颗行星住在你的星盘里<br />
      每颗星灵都有不同的性格和故事
    </p>
    <span class="wc-cta">开始探索你的内在宇宙 →</span>
  </div>
</template>

<script setup lang="ts">
defineEmits<{ 'go-login': [] }>()
</script>

<style scoped lang="less">
.welcome-card {
  text-align: center; padding: 56px 28px; border-radius: 28px; cursor: pointer;
  background: linear-gradient(135deg,
    rgba(255,255,255,0.85) 0%,
    rgba(255,245,238,0.8) 50%,
    rgba(255,240,245,0.7) 100%);
  box-shadow: 0 4px 24px rgba(0,0,0,0.04), 0 1px 4px rgba(0,0,0,0.03);
  border: 1px solid rgba(255,255,255,0.8); transition: all 0.4s;
}
.welcome-card:hover { transform: translateY(-3px); box-shadow: 0 12px 32px rgba(0,0,0,0.08); }
.wc-icon { font-size: 56px; margin-bottom: 16px; animation: float 3s ease-in-out infinite; }
@keyframes float { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-10px)} }
.wc-title { font-size: 28px; font-weight: 700; color: #4a3728; margin: 0 0 10px; letter-spacing: 3px; }
.wc-desc { font-size: 15px; color: #8b7355; margin: 0 0 22px; line-height: 1.7; }
.wc-cta { font-size: 15px; font-weight: 600; color: #ff9a8b; }
</style>
