<template>
  <transition name="card-expand">
    <div class="detail-card" v-if="visible" :style="{ '--accent': color }">
      <!-- 关闭按钮 -->
      <button class="detail-close" @click="$emit('close')">✕</button>

      <!-- 头部：星灵大形象 -->
      <div class="detail-hero">
        <div class="detail-avatar-lg" :style="{ borderColor: color, background: color + '15' }">
          <SpiritAvatar :planet="planet" :symbol="symbol" :color="color" :name="name" size="xl" />
        </div>
        <div class="detail-hero-text">
          <h2 class="detail-name">{{ name }}</h2>
          <span class="detail-archetype-tag" :style="{ background: color + '20', color }">
            {{ archetype }}
          </span>
        </div>
        <div class="detail-essence">"{{ essence }}"</div>
      </div>

      <!-- 个性化开场白 -->
      <div class="detail-greeting">
        <div class="greeting-icon">💫</div>
        <p class="greeting-text">{{ greeting }}</p>
      </div>

      <!-- 三层信息卡 -->
      <div class="detail-layers">
        <div class="layer-card layer-card--planet">
          <span class="layer-icon">🪐</span>
          <span class="layer-label">行星本性</span>
          <span class="layer-value">{{ personaDescription }}</span>
        </div>
        <div class="layer-card layer-card--sign">
          <span class="layer-icon">✨</span>
          <span class="layer-label">星座风格</span>
          <span class="layer-value">
            落在<strong>{{ signLabel }}</strong
            >，{{ signElement }}象{{ signModality }}——{{ signVoice }}
          </span>
        </div>
        <div class="layer-card layer-card--house">
          <span class="layer-icon">🏠</span>
          <span class="layer-label">宫位舞台</span>
          <span class="layer-value">
            在第<strong>{{ house }}</strong>宫「{{ houseLabel }}」运作
          </span>
        </div>
      </div>

      <!-- 状态标签 -->
      <div class="detail-tags">
        <span class="tag tag--dignity" :class="'tag--dignity--' + dignityCode">
          {{ dignityLabel }}
        </span>
        <span class="tag tag--role">{{ roleTag }}</span>
        <span class="tag tag--strength">
          强度 {{ coreStrength }}
        </span>
        <span v-if="isChartRuler" class="tag tag--ruler">命主星</span>
      </div>

      <!-- 操作区 -->
      <div class="detail-actions">
        <button class="action-btn action-btn--chat" @click="$emit('chat')">
          💬 和{{ name }}聊聊
        </button>
        <button class="action-btn action-btn--back" @click="$emit('close')">
          回到花园
        </button>
      </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
import SpiritAvatar from "@/components/garden/SpiritAvatar.vue";

defineProps<{
  visible: boolean;
  planet?: string;
  symbol: string;
  name: string;
  archetype: string;
  color: string;
  essence: string;
  greeting: string;
  personaDescription: string;
  signLabel: string;
  signElement: string;
  signModality: string;
  signVoice: string;
  house: number;
  houseLabel: string;
  dignityCode: string;
  dignityLabel: string;
  roleTag: string;
  coreStrength: number;
  isChartRuler: boolean;
}>();

defineEmits<{
  close: [];
  chat: [];
}>();
</script>

<style scoped>
.detail-card {
  position: relative;
  padding: 28px 24px 24px;
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(20px);
  box-shadow: 0 8px 40px rgba(0, 0, 0, 0.08),
    0 2px 12px rgba(0, 0, 0, 0.04);
  border: 1.5px solid rgba(255, 255, 255, 0.9);
  max-width: 480px;
  margin: 0 auto;
}

/* ── 过渡动画 ── */
.card-expand-enter-active {
  transition: all 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}
.card-expand-leave-active {
  transition: all 0.25s ease-in;
}
.card-expand-enter-from {
  opacity: 0;
  transform: translateY(20px) scale(0.95);
}
.card-expand-leave-to {
  opacity: 0;
  transform: translateY(10px) scale(0.98);
}

/* ── 关闭按钮 ── */
.detail-close {
  position: absolute;
  top: 16px;
  right: 16px;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: none;
  background: rgba(0, 0, 0, 0.04);
  color: #8b7355;
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}
.detail-close:hover {
  background: rgba(0, 0, 0, 0.08);
  color: #4a3728;
}

/* ── Hero ── */
.detail-hero {
  text-align: center;
  margin-bottom: 20px;
}
.detail-avatar-lg {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  border: 3px solid;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 12px;
}
.detail-symbol-lg {
  font-size: 36px;
}
.detail-hero-text {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  margin-bottom: 8px;
}
.detail-name {
  font-size: 22px;
  font-weight: 700;
  color: #4a3728;
  margin: 0;
}
.detail-archetype-tag {
  font-size: 12px;
  font-weight: 600;
  padding: 3px 12px;
  border-radius: 12px;
}
.detail-essence {
  font-size: 14px;
  color: #8b7355;
  font-style: italic;
  max-width: 340px;
  margin: 0 auto;
  line-height: 1.6;
}

/* ── 个性化开场白 ── */
.detail-greeting {
  display: flex;
  gap: 12px;
  padding: 16px 20px;
  border-radius: 20px;
  background: linear-gradient(135deg, rgba(255, 245, 238, 0.8), rgba(255, 240, 245, 0.5));
  margin-bottom: 20px;
  border: 1px solid rgba(0, 0, 0, 0.04);
}
.greeting-icon {
  font-size: 20px;
  flex-shrink: 0;
  margin-top: 2px;
}
.greeting-text {
  font-size: 13.5px;
  color: #5c4a3a;
  line-height: 1.7;
  margin: 0;
}

/* ── 三层信息卡 ── */
.detail-layers {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 18px;
}
.layer-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  border-radius: 16px;
  font-size: 13px;
  line-height: 1.5;
}
.layer-card--planet {
  background: rgba(255, 154, 139, 0.08);
}
.layer-card--sign {
  background: rgba(155, 196, 208, 0.08);
}
.layer-card--house {
  background: rgba(240, 192, 96, 0.08);
}
.layer-icon {
  font-size: 18px;
  flex-shrink: 0;
}
.layer-label {
  font-size: 11px;
  font-weight: 600;
  color: #a89880;
  min-width: 56px;
  flex-shrink: 0;
}
.layer-value {
  color: #4a3728;
}
.layer-value strong {
  color: #3a2718;
  font-weight: 600;
}

/* ── 标签 ── */
.detail-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 22px;
}
.tag {
  font-size: 12px;
  font-weight: 600;
  padding: 5px 14px;
  border-radius: 12px;
}
.tag--dignity {
  background: rgba(0, 0, 0, 0.04);
  color: #8b7355;
}
.tag--dignity--domicile,
.tag--dignity--exaltation {
  background: rgba(76, 175, 80, 0.1);
  color: #388e3c;
}
.tag--dignity--detriment,
.tag--dignity--fall {
  background: rgba(244, 67, 54, 0.08);
  color: #d32f2f;
}
.tag--role {
  background: rgba(240, 192, 96, 0.12);
  color: #e65100;
}
.tag--strength {
  background: rgba(99, 102, 241, 0.08);
  color: #4a3f7a;
}
.tag--ruler {
  background: rgba(240, 192, 96, 0.18);
  color: #c79100;
}

/* ── 操作按钮 ── */
.detail-actions {
  display: flex;
  gap: 12px;
}
.action-btn {
  flex: 1;
  padding: 14px 20px;
  border-radius: 18px;
  border: none;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.25s;
  font-family: inherit;
}
.action-btn--chat {
  background: var(--accent);
  color: #fff;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.1);
}
.action-btn--chat:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.14);
}
.action-btn--back {
  background: rgba(0, 0, 0, 0.04);
  color: #8b7355;
}
.action-btn--back:hover {
  background: rgba(0, 0, 0, 0.07);
  color: #4a3728;
}
</style>
