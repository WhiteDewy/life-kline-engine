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

        <div class="spirit-grid" v-if="councilMode === 'planets'">
          <SpiritBuddy
            v-for="p in planetList" :key="p.planet"
            :planet="p.planet" :sign="p.sign"
            :gender="gender"
            :symbol="p.symbol" :name="p.shortName"
            :archetype="p.archetypeShort" :color="p.color"
            :sign-label="p.signLabel" :dignity-label="p.dignityLabel || ''"
            :is-featured="p.isFeatured" :is-main="p.planet === 'SUN'"
            :is-active="p.planet === activePlanet"
            :activation-score="p.activationScore"
            :float-delay="0"
            :healing-label="p.healingLabel || ''"
            @select="onSelectPlanet(p)"
          />
        </div>

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
            <span class="sign-planets" v-if="s.hasPlanets">{{ s.planetsHere }}</span>
            <span class="sign-planets sign-planets--none" v-else>暂无行星</span>
            <span class="sign-element">{{ s.element }}象</span>
          </button>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { ref } from "vue";
import SpiritBuddy from "@/views/Wanxiang/components/SpiritBuddy.vue";

defineProps<{
  visible: boolean
  planetList: any[]
  signList: any[]
  gender: string
  activePlanet: string
  activeSign: string
}>()

const emit = defineEmits<{
  close: []
  'chat-with-planet': [payload: any]
  'chat-with-sign': [payload: any]
  'select-planet': [planetKey: string]
  'select-sign': [signKey: string]
}>()

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

<style scoped>
.council-screen {
  position: fixed; inset: 0; z-index: 200;
  background: rgba(255, 255, 255, 0.97);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  display: flex; flex-direction: column;
  overflow-y: auto;
}

.council-screen::-webkit-scrollbar { width: 4px; }
.council-screen::-webkit-scrollbar-thumb { background: rgba(0,0,0,0.1); border-radius: 2px; }

.council-slide-enter-active { transition: all 0.45s cubic-bezier(0.32, 0.02, 0, 1); }
.council-slide-leave-active { transition: all 0.35s cubic-bezier(0.32, 0.02, 0, 1); }
.council-slide-enter-from { transform: translateY(100%); }
.council-slide-leave-to { transform: translateY(100%); }

.dismiss-bar {
  display: flex; justify-content: center; padding: 12px 0 8px;
  border: none; background: transparent; cursor: pointer; flex-shrink: 0;
}
.dismiss-line {
  display: block; width: 36px; height: 4px; border-radius: 2px;
  background: rgba(0, 0, 0, 0.15); transition: background 0.2s;
}
.dismiss-bar:hover .dismiss-line { background: rgba(0, 0, 0, 0.3); }

.council-body {
  padding: 0 20px 40px;
  padding-bottom: calc(40px + env(safe-area-inset-bottom, 0px));
  max-width: 520px; width: 100%; margin: 0 auto;
}

.council-title { font-size: 22px; font-weight: 700; color: #4a3728; margin: 0 0 20px; text-align: center; }

.dimension-toggle {
  display: flex; border-radius: 14px; overflow: hidden;
  border: 1px solid rgba(0,0,0,0.06); background: rgba(0,0,0,0.03);
  margin-bottom: 10px;
}
.dimension-toggle button {
  flex: 1; padding: 8px 14px; border: none; background: transparent;
  font-size: 13px; font-weight: 600; color: #a89880;
  cursor: pointer; font-family: inherit; transition: all 0.2s;
}
.dimension-toggle button.active { background: rgba(255,154,139,0.15); color: #4a3728; }

.council-desc { text-align: center; font-size: 13px; color: #8b7355; margin: 0 0 24px; line-height: 1.5; }

.spirit-grid {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px;
}
.spirit-grid--signs { grid-template-columns: repeat(3, 1fr) !important; }

.sign-card {
  display: flex; flex-direction: column; align-items: center; gap: 4px;
  padding: 18px 10px; border-radius: 24px; border: 1.5px solid rgba(0,0,0,0.04);
  background: rgba(0,0,0,0.02); cursor: pointer; font-family: inherit;
  transition: all 0.35s cubic-bezier(0.25,0.46,0.45,0.94);
}
.sign-card:hover {
  transform: translateY(-4px);
  border-color: var(--sc);
  background: rgba(255,255,255,0.9);
  box-shadow: 0 8px 24px rgba(0,0,0,0.06);
}
.sign-card--empty { opacity: 0.45; }
.sign-card--empty:hover { opacity: 0.75; }

/* 高亮当前选中的星座 */
.sign-card--active {
  border-color: var(--sc);
  background: rgba(255,255,255,0.95);
  box-shadow: 0 0 0 2px var(--sc), 0 4px 20px rgba(0,0,0,0.08);
  transform: scale(1.03);
}

.sign-emoji { font-size: 32px; line-height: 1; }
.sign-name { font-size: 13px; font-weight: 700; color: #4a3728; }
.sign-planets { font-size: 11px; font-weight: 600; color: #ff9a8b; }
.sign-planets--none { color: #c4b5a5; font-weight: 400; }
.sign-element { font-size: 10px; color: #a89880; }

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
