<template>
  <transition name="modal-fade">
    <div v-if="visible" class="div-overlay" @click.self="$emit('close')">
      <div class="div-modal">
        <div class="div-icon">🔮</div>
        <h3 class="div-title">灵犀占卜</h3>
        <p class="div-desc">
          以星辰为据，为你解答心中所惑。
        </p>
        <div class="div-soon">即将上线，敬请期待 ✨</div>
        <button class="div-close-btn" @click="$emit('close')">知道了</button>
      </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
defineProps<{
  visible: boolean;
}>();

defineEmits<{
  close: [];
}>();
</script>

<style scoped lang="less">
.div-overlay {
  position: fixed; inset: 0; z-index: 200;
  background: rgba(0,0,0,0.2); backdrop-filter: blur(6px);
  display: flex; align-items: center; justify-content: center; padding: 20px;
}
.div-modal {
  width: 100%; max-width: 360px; text-align: center;
  padding: 40px 28px; border-radius: 28px;
  background: rgba(255,255,255,0.92); backdrop-filter: blur(20px);
}
.div-icon { font-size: 52px; margin-bottom: 12px; }
.div-title { font-size: 22px; font-weight: 700; color: #4a3728; margin: 0 0 8px; }
.div-desc { font-size: 14px; color: #8b7355; margin: 0 0 20px; line-height: 1.5; }
.div-soon { font-size: 15px; font-weight: 600; color: #ff9a8b; margin-bottom: 24px; }
.div-close-btn { padding: 10px 32px; border-radius: 16px; border: 1px solid rgba(0,0,0,0.1); background: rgba(255,255,255,0.8); font-size: 14px; font-weight: 600; color: #4a3728; cursor: pointer; font-family: inherit; }
.modal-fade-enter-active, .modal-fade-leave-active { transition: all 0.25s ease; }
.modal-fade-enter-from, .modal-fade-leave-to { opacity: 0; }
.modal-fade-enter-from .div-modal, .modal-fade-leave-to .div-modal { transform: scale(0.9); }
</style>
