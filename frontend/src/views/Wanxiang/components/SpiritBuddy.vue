<template>
  <div
    class="spirit-buddy"
    :class="{
      'spirit-buddy--featured': isFeatured,
      'spirit-buddy--asleep': !isFeatured && !isMain,
      'spirit-buddy--main': isMain,
      'spirit-buddy--active': isActive,
    }"
    :style="{
      animationDelay: floatDelay + 's',
      '--spirit-color': color,
      '--spirit-color-light': color + '22',
      '--spirit-color-soft': color + '18',
    }"
    @click="$emit('select')"
  >
    <!-- Q 版星灵头像区 -->
    <div class="buddy-avatar">
      <div class="avatar-ring" :style="{ borderColor: color }">
        <SpiritAvatar :planet="planet" :symbol="symbol" :color="color" :name="name" :sign="sign" :gender="gender" size="lg" />
      </div>
      <!-- 状态标记 -->
      <span v-if="isFeatured" class="buddy-badge buddy-badge--today">
        ✨ 今日
      </span>
      <span v-else class="buddy-badge buddy-badge--rest">
        💤
      </span>
    </div>

    <!-- 星灵信息 -->
    <div class="buddy-info">
      <div class="buddy-name">{{ name }}</div>
      <div class="buddy-archetype">{{ archetype }}</div>
      <div class="buddy-sign">{{ signLabel }} · {{ dignityLabel }}</div>
    </div>

    <!-- 疗愈标签 -->
    <span v-if="healingLabel" class="healing-tag">{{ healingLabel }}</span>

    <!-- 活跃度条 -->
    <div class="buddy-meter" v-if="activationScore !== null">
      <div class="meter-track">
        <div
          class="meter-fill"
          :style="{
            width: activationScore + '%',
            background: color,
          }"
        ></div>
      </div>
      <span class="meter-label">{{ Math.round(activationScore) }}%</span>
    </div>

    <!-- 点击提示 -->
    <div class="buddy-tap-hint">轻触对话</div>
  </div>
</template>

<script setup lang="ts">
import SpiritAvatar from "./SpiritAvatar.vue";

defineProps<{
  planet: string;
  sign?: string;
  gender?: string | null;
  symbol: string;
  name: string;
  archetype: string;
  color: string;
  signLabel: string;
  dignityLabel: string;
  isFeatured: boolean;
  isMain: boolean;
  isActive: boolean;
  activationScore: number | null;
  floatDelay: number;
  healingLabel?: string;
}>();

defineEmits<{
  select: [];
}>();
</script>

<style scoped>
.spirit-buddy {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 20px 16px 16px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(12px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05),
    0 1px 3px rgba(0, 0, 0, 0.04);
  border: 1.5px solid rgba(255, 255, 255, 0.8);
  cursor: pointer;
  transition: all 0.35s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  animation: buddy-float 3.5s ease-in-out infinite;
  user-select: none;
}
.spirit-buddy:hover {
  transform: translateY(-6px);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.08),
    0 2px 8px rgba(0, 0, 0, 0.04);
  border-color: var(--spirit-color);
  background: rgba(255, 255, 255, 0.88);
}
.spirit-buddy--active {
  border-color: var(--spirit-color);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05),
    0 0 0 3px var(--spirit-color-light);
}

/* 主星灵（太阳） */
.spirit-buddy--main {
  background: linear-gradient(
    135deg,
    rgba(255, 255, 255, 0.85) 0%,
    var(--spirit-color-soft) 100%
  );
  border-color: var(--spirit-color);
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.06),
    0 0 0 4px var(--spirit-color-light);
}

/* 今日激活 */
.spirit-buddy--featured {
  background: linear-gradient(
    135deg,
    rgba(255, 255, 255, 0.85) 0%,
    rgba(255, 215, 180, 0.3) 100%
  );
  border-color: rgba(240, 192, 96, 0.5);
  box-shadow: 0 4px 24px rgba(240, 192, 96, 0.12),
    0 0 0 2px rgba(240, 192, 96, 0.12);
}

/* 休眠 */
.spirit-buddy--asleep {
  opacity: 0.7;
}
.spirit-buddy--asleep:hover {
  opacity: 0.95;
}

/* ── 浮动动画 ── */
@keyframes buddy-float {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-6px);
  }
}

/* ── 头像 ── */
.buddy-avatar {
  position: relative;
}
.avatar-ring {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  border: 3px solid;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.6);
  transition: all 0.3s;
}
.spirit-buddy:hover .avatar-ring {
  transform: scale(1.08);
}
.avatar-symbol {
  font-size: 28px;
  line-height: 1;
  transition: transform 0.3s;
}
.spirit-buddy:hover .avatar-symbol {
  transform: scale(1.15);
}

/* ── 徽章 ── */
.buddy-badge {
  position: absolute;
  bottom: -6px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 11px;
  font-weight: 600;
  padding: 2px 10px;
  border-radius: 12px;
  white-space: nowrap;
  letter-spacing: 0.02em;
}
.buddy-badge--today {
  background: linear-gradient(135deg, #ffe0b2, #ffcc80);
  color: #e65100;
  box-shadow: 0 1px 4px rgba(255, 152, 0, 0.2);
}
.buddy-badge--main {
  background: linear-gradient(135deg, #fff9c4, #fff176);
  color: #f57f17;
  box-shadow: 0 1px 4px rgba(255, 193, 7, 0.2);
}
.buddy-badge--rest {
  background: rgba(0, 0, 0, 0.04);
  color: #bdbdbd;
  font-size: 14px;
  padding: 1px 8px;
}

/* ── 信息 ── */
.buddy-info {
  text-align: center;
  display: flex;
  flex-direction: column;
  gap: 3px;
}
.buddy-name {
  font-size: 16px;
  font-weight: 700;
  color: #4a3728;
  letter-spacing: 0.03em;
}
.buddy-archetype {
  font-size: 12px;
  color: #8b7355;
  font-weight: 500;
}
.buddy-sign {
  font-size: 11px;
  color: #a89880;
}

/* ── 疗愈标签 ── */
.healing-tag {
  font-size: 10px;
  font-weight: 600;
  color: rgba(74, 55, 40, 0.7);
  background: rgba(255, 200, 180, 0.35);
  border: 1px solid rgba(255, 180, 160, 0.3);
  padding: 2px 10px;
  border-radius: 12px;
  line-height: 1.4;
  letter-spacing: 0.03em;
}

/* ── 活跃度条 ── */
.buddy-meter {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 0 4px;
}
.meter-track {
  flex: 1;
  height: 4px;
  border-radius: 2px;
  background: rgba(0, 0, 0, 0.06);
  overflow: hidden;
}
.meter-fill {
  height: 100%;
  border-radius: 2px;
  transition: width 1s ease;
}
.meter-label {
  font-size: 10px;
  font-weight: 600;
  color: #8b7355;
  min-width: 28px;
  text-align: right;
}

/* ── 点击提示 ── */
.buddy-tap-hint {
  font-size: 11px;
  color: #c4b5a5;
  opacity: 0;
  transform: translateY(4px);
  transition: all 0.3s;
}
.spirit-buddy:hover .buddy-tap-hint {
  opacity: 1;
  transform: translateY(0);
}
</style>
