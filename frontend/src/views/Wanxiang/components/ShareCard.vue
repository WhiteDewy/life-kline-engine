<template>
  <transition name="share-fade">
    <div class="share-overlay" v-if="visible" @click.self="$emit('close')">
      <div class="share-panel">
        <!-- 卡片预览 -->
        <div class="card-preview" ref="cardEl" :style="{ '--s-color': color }">
          <div class="card-header">
            <span class="card-brand">✨ 星灵花园 · 今日寄语</span>
          </div>
          <div class="card-spirit">
            <span class="card-symbol">{{ symbol }}</span>
          </div>
          <div class="card-quote">
            "{{ message }}"
          </div>
          <div class="card-meta">
            <span class="card-from">─ {{ name }} · {{ archetype }}</span>
            <span class="card-sign" v-if="signLabel">{{ signLabel }} · {{ houseLabel }}</span>
          </div>
          <div class="card-footer">
            <span>星灵花园 · life-kline</span>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="share-actions">
          <button class="share-btn share-btn--native" @click="nativeShare" v-if="canNativeShare">
            📤 分享给朋友
          </button>
          <button class="share-btn share-btn--copy" @click="copyText">
            📋 复制寄语
          </button>
          <button class="share-btn share-btn--save" @click="saveImage" v-if="!canNativeShare">
            💾 保存图片
          </button>
          <button class="share-btn share-btn--close" @click="$emit('close')">
            关闭
          </button>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";

const props = defineProps<{
  visible: boolean;
  symbol: string;
  name: string;
  archetype: string;
  color: string;
  message: string;
  signLabel?: string;
  houseLabel?: string;
}>();

defineEmits<{ close: [] }>();

const cardEl = ref<HTMLElement | null>(null);

onMounted(() => {
  void cardEl.value;
});
const canNativeShare = ref(
  typeof navigator !== "undefined" && !!navigator.share
);

async function nativeShare() {
  const text = `${props.symbol} ${props.name} · ${props.archetype}\n\n"${props.message}"\n\n── 来自星灵花园 ✨`;
  try {
    await navigator.share({ title: "星灵花园 · 今日寄语", text });
  } catch {
    // user cancelled
  }
}

async function copyText() {
  const text = `${props.symbol} ${props.name} · ${props.archetype}\n\n"${props.message}"\n\n── 来自星灵花园 ✨`;
  try {
    await navigator.clipboard.writeText(text);
    // brief feedback
  } catch {
    // fallback
  }
}

function saveImage() {
  // 简单方案：打开新窗口打印 / 提示截图
  alert("💡 请使用截图工具（或按 Print Screen）保存这张卡片。移动端可长按截图。");
}
</script>

<style scoped>
.share-overlay {
  position: fixed;
  inset: 0;
  z-index: 500;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  background: rgba(0, 0, 0, 0.35);
  backdrop-filter: blur(6px);
}
.share-panel {
  width: 100%;
  max-width: 360px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.share-fade-enter-active { transition: all 0.35s cubic-bezier(0.25,0.46,0.45,0.94); }
.share-fade-leave-active { transition: all 0.2s ease; }
.share-fade-enter-from { opacity: 0; transform: scale(0.95) translateY(12px); }
.share-fade-leave-to { opacity: 0; }

/* ── 卡片 ── */
.card-preview {
  padding: 28px 24px 20px;
  border-radius: 24px;
  background: linear-gradient(
    160deg,
    rgba(255, 255, 255, 0.98) 0%,
    rgba(255, 250, 245, 0.95) 100%
  );
  border: 2px solid var(--s-color);
  box-shadow: 0 8px 40px rgba(0, 0, 0, 0.1);
  text-align: center;
}
.card-header {
  margin-bottom: 18px;
}
.card-brand {
  font-size: 13px;
  font-weight: 600;
  color: #a89880;
  letter-spacing: 0.05em;
}
.card-spirit {
  margin-bottom: 14px;
}
.card-symbol {
  font-size: 56px;
  color: var(--s-color);
  display: inline-block;
  animation: symbol-float 2s ease-in-out infinite;
}
@keyframes symbol-float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-6px); }
}
.card-quote {
  font-size: 15px;
  color: #4a3728;
  line-height: 1.7;
  margin-bottom: 16px;
  padding: 0 8px;
}
.card-meta {
  display: flex;
  flex-direction: column;
  gap: 3px;
  margin-bottom: 18px;
}
.card-from {
  font-size: 13px;
  font-weight: 600;
  color: #6b5744;
}
.card-sign {
  font-size: 12px;
  color: #a89880;
}
.card-footer {
  padding-top: 14px;
  border-top: 1px solid rgba(0, 0, 0, 0.05);
  font-size: 11px;
  color: #c4b5a5;
}

/* ── 操作 ── */
.share-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.share-btn {
  flex: 1;
  min-width: 100px;
  padding: 14px 16px;
  border-radius: 16px;
  border: none;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  font-family: inherit;
  transition: all 0.2s;
}
.share-btn--native {
  background: linear-gradient(135deg, #ff9a8b, #ffb8a8);
  color: #fff;
  flex: 2;
}
.share-btn--copy {
  background: rgba(0, 0, 0, 0.04);
  color: #6b5744;
}
.share-btn--save {
  background: rgba(240, 192, 96, 0.15);
  color: #6b5744;
}
.share-btn--close {
  background: rgba(0, 0, 0, 0.04);
  color: #a89880;
  min-width: 60px;
  flex: 0;
}
.share-btn:hover {
  filter: brightness(1.05);
  transform: translateY(-1px);
}
</style>
