<template>
  <transition name="council-slide">
    <div v-if="visible" class="council-screen">
      <button class="dismiss-bar" @click="$emit('close')">
        <span class="dismiss-line"></span>
      </button>

      <div class="council-body">
        <h2 class="council-title">⭐ 星灵议会</h2>

        <div class="dimension-toggle">
          <button :class="{ active: councilMode === 'planets' }" @click="councilMode = 'planets'">🌌 十位 · 星灵</button>
          <button :class="{ active: councilMode === 'signs' }" @click="councilMode = 'signs'">🎭 十二星座</button>
        </div>

        <p class="council-desc">
          {{ councilMode === 'planets'
            ? '选择一位星灵开始对话——每颗行星都是你内在的不同声音'
            : '以星座视角探索自己——无行星落座的星座也可探索潜在能量'
          }}
        </p>

        <!-- 星灵卡片网格 -->
        <div class="spirit-grid" v-if="councilMode === 'planets'">
          <div
            v-for="p in planetList" :key="p.planet"
            class="spirit-buddy"
            :class="{
              'spirit-buddy--featured': p.isFeatured,
              'spirit-buddy--asleep': !p.isFeatured && p.planet !== 'SUN',
              'spirit-buddy--main': p.planet === 'SUN',
              'spirit-buddy--active': p.planet === activePlanet,
            }"
            :style="{
              '--spirit-color': p.color,
              '--spirit-color-light': p.color + '22',
              '--spirit-color-soft': p.color + '18',
            }"
            @click="onSelectPlanet(p)"
          >
            <div class="buddy-avatar">
              <div class="avatar-ring" :style="{ borderColor: p.color }">
                <SpiritAvatar :planet="p.planet" :symbol="p.symbol" :color="p.color" :name="p.shortName" :sign="p.sign" :gender="gender" size="lg" />
              </div>
              <span v-if="p.isFeatured" class="buddy-badge buddy-badge--today">✨ 今日</span>
              <span v-else-if="p.planet !== 'SUN'" class="buddy-badge buddy-badge--rest">💤</span>
            </div>

            <div class="buddy-info">
              <div class="buddy-name">{{ p.shortName }}</div>
              <div class="buddy-archetype">{{ p.archetypeShort }}</div>
              <div class="buddy-sign">{{ p.signLabel }} · {{ p.dignityLabel || '' }}</div>
            </div>

            <span v-if="p.healingLabel" class="healing-tag">{{ p.healingLabel }}</span>

            <div v-if="p.activationScore !== null && p.activationScore !== undefined" class="buddy-meter">
              <div class="meter-track">
                <div class="meter-fill" :style="{ width: p.activationScore + '%', background: p.color }" />
              </div>
              <span class="meter-label">{{ Math.round(p.activationScore) }}%</span>
            </div>

            <div class="buddy-tap-hint">轻触对话</div>
          </div>
        </div>

        <!-- 星座卡片网格 -->
        <div class="spirit-grid spirit-grid--signs" v-else>
          <button
            v-for="s in signList" :key="s.key"
            class="sign-card"
            :class="{
              'sign-card--empty': !s.hasPlanets,
              'sign-card--active': s.key === activeSign,
            }"
            :style="{ '--sc': s.color }"
            @click="onSelectSign(s)"
          >
            <span class="sign-emoji">{{ s.emoji }}</span>
            <span class="sign-name">{{ s.name }}</span>
            <span v-if="s.hasPlanets" class="sign-planets">{{ s.planetsHere }}</span>
            <span v-else class="sign-planets sign-planets--none">暂无行星</span>
            <span class="sign-element">{{ s.element }}象</span>
          </button>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { ref } from "vue";
import SpiritAvatar from "@/components/garden/SpiritAvatar.vue";

defineProps<{
  visible: boolean;
  planetList: any[];
  signList: any[];
  gender: string;
  activePlanet: string;
  activeSign: string;
}>();

const emit = defineEmits<{
  (e: "close"): void;
  (e: "chat-with-planet", payload: any): void;
  (e: "chat-with-sign", payload: any): void;
  (e: "select-planet", planetKey: string): void;
  (e: "select-sign", signKey: string): void;
}>();

const councilMode = ref<"planets" | "signs">("planets");

function onSelectPlanet(p: any) {
  emit("select-planet", p.planet);
  emit("chat-with-planet", p);
}
function onSelectSign(s: any) {
  emit("select-sign", s.key);
  emit("chat-with-sign", s);
}
</script>

<style scoped lang="less">
/* ═══════════════ 容器 ═══════════════ */
.council-screen {
  position: fixed;
  inset: 0;
  z-index: 200;
  background: rgba(255, 255, 255, 0.97);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}

.council-screen::-webkit-scrollbar {
  width: 4px;
}
.council-screen::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.1);
  border-radius: 2px;
}

.council-slide-enter-active { transition: all 0.45s cubic-bezier(0.32, 0.02, 0, 1); }
.council-slide-leave-active { transition: all 0.35s cubic-bezier(0.32, 0.02, 0, 1); }
.council-slide-enter-from { transform: translateY(100%); }
.council-slide-leave-to { transform: translateY(100%); }

.dismiss-bar {
  display: flex;
  justify-content: center;
  padding: 12px 0 8px;
  border: none;
  background: transparent;
  cursor: pointer;
  flex-shrink: 0;
}
.dismiss-line {
  display: block;
  width: 36px;
  height: 4px;
  border-radius: 2px;
  background: rgba(0, 0, 0, 0.15);
  transition: background 0.2s;
}
.dismiss-bar:hover .dismiss-line { background: rgba(0, 0, 0, 0.3); }

.council-body {
  padding: 0 20px 40px;
  padding-bottom: calc(40px + env(safe-area-inset-bottom, 0px));
  max-width: 520px;
  width: 100%;
  margin: 0 auto;
}

.council-title {
  font-size: 22px;
  font-weight: 700;
  color: #4a3728;
  margin: 0 0 20px;
  text-align: center;
}

.dimension-toggle {
  display: flex;
  border-radius: 14px;
  overflow: hidden;
  border: 1px solid rgba(0, 0, 0, 0.06);
  background: rgba(0, 0, 0, 0.03);
  margin-bottom: 10px;
}
.dimension-toggle button {
  flex: 1;
  padding: 8px 14px;
  border: none;
  background: transparent;
  font-size: 13px;
  font-weight: 600;
  color: #a89880;
  cursor: pointer;
  font-family: inherit;
  transition: all 0.2s;
}
.dimension-toggle button.active {
  background: rgba(255, 154, 139, 0.15);
  color: #4a3728;
}

.council-desc {
  text-align: center;
  font-size: 13px;
  color: #8b7355;
  margin: 0 0 24px;
  line-height: 1.5;
}

/* ═══════════════ SpiritBuddy (内联版) ═══════════════ */
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
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05), 0 1px 3px rgba(0, 0, 0, 0.04);
  border: 1.5px solid rgba(255, 255, 255, 0.8);
  cursor: pointer;
  transition: all 0.35s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  animation: buddy-float 3.5s ease-in-out infinite;
  user-select: none;
}

.spirit-buddy:hover {
  transform: translateY(-6px);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.08), 0 2px 8px rgba(0, 0, 0, 0.04);
  border-color: var(--spirit-color);
  background: rgba(255, 255, 255, 0.88);
}

.spirit-buddy--active {
  border-color: var(--spirit-color);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05), 0 0 0 3px var(--spirit-color-light);
}

.spirit-buddy--main {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.85) 0%, var(--spirit-color-soft) 100%);
  border-color: var(--spirit-color);
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.06), 0 0 0 4px var(--spirit-color-light);
}

.spirit-buddy--featured {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.85) 0%, rgba(255, 215, 180, 0.3) 100%);
  border-color: rgba(240, 192, 96, 0.5);
  box-shadow: 0 4px 24px rgba(240, 192, 96, 0.12), 0 0 0 2px rgba(240, 192, 96, 0.12);
}

.spirit-buddy--asleep { opacity: 0.7; }
.spirit-buddy--asleep:hover { opacity: 0.95; }

@keyframes buddy-float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-6px); }
}

.buddy-avatar { position: relative; }

.avatar-ring {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  border: 3px solid;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.6);
  transition: transform 0.3s;
}

.spirit-buddy:hover .avatar-ring { transform: scale(1.08); }

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

.buddy-badge--rest {
  background: rgba(0, 0, 0, 0.04);
  color: #bdbdbd;
  font-size: 14px;
  padding: 1px 8px;
}

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

/* ═══════════════ 星座网格 ═══════════════ */
.spirit-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
}

.spirit-grid--signs { grid-template-columns: repeat(3, 1fr) !important; }

.sign-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 18px 10px;
  border-radius: 24px;
  border: 1.5px solid rgba(0, 0, 0, 0.04);
  background: rgba(0, 0, 0, 0.02);
  cursor: pointer;
  font-family: inherit;
  transition: all 0.35s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}

.sign-card:hover {
  transform: translateY(-4px);
  border-color: var(--sc);
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.06);
}

.sign-card--empty { opacity: 0.45; }
.sign-card--empty:hover { opacity: 0.75; }

.sign-card--active {
  border-color: var(--sc);
  background: rgba(255, 255, 255, 0.95);
  box-shadow: 0 0 0 2px var(--sc), 0 4px 20px rgba(0, 0, 0, 0.08);
  transform: scale(1.03);
}

.sign-emoji { font-size: 32px; line-height: 1; }
.sign-name { font-size: 13px; font-weight: 700; color: #4a3728; }
.sign-planets { font-size: 11px; font-weight: 600; color: #ff9a8b; }
.sign-planets--none { color: #c4b5a5; font-weight: 400; }
.sign-element { font-size: 10px; color: #a89880; }

/* ═══════════════ 响应式 ═══════════════ */
@media (max-width: 640px) {
  .council-body { padding: 0 16px 32px; }
  .spirit-grid { grid-template-columns: repeat(3, 1fr); gap: 10px; }
  .spirit-grid--signs { grid-template-columns: repeat(3, 1fr) !important; }
  .council-title { font-size: 20px; }
}
@media (max-width: 400px) {
  .spirit-grid { grid-template-columns: repeat(2, 1fr); }
  .spirit-grid--signs { grid-template-columns: repeat(2, 1fr) !important; }
}
</style>
