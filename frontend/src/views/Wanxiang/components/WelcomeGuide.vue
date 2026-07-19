<template>
  <transition name="guide-fade">
    <div class="guide-overlay" v-if="visible">
      <div class="guide-card">
        <!-- Step 1: 认识星灵 -->
        <div class="guide-step" v-if="step === 1">
          <div class="guide-emoji">🌌</div>
          <h2 class="guide-title">欢迎来到<br />你的星灵花园</h2>
          <p class="guide-text">
            七颗行星，七位星灵<br />
            它们一直住在你的星盘里<br />
            今天，它们想正式认识你
          </p>
          <div class="guide-preview">
            <SpiritAvatar planet="SUN" :symbol="sunSymbol" :color="sunColor" :name="sunName" size="md" />
            <div class="preview-info">
              <span class="preview-name">{{ sunName }} · 你的主人格</span>
              <span class="preview-quote">"我是你想成为的那个人"</span>
            </div>
          </div>
          <div class="guide-dots">
            <span class="dot dot--active"></span>
            <span class="dot"></span>
            <span class="dot"></span>
          </div>
          <button class="guide-btn" @click="nextStep">开始探索 🌸</button>
        </div>

        <!-- Step 2: 水晶球 -->
        <div class="guide-step" v-if="step === 2">
          <div class="guide-emoji">🔮</div>
          <h2 class="guide-title">灵犀一刻</h2>
          <p class="guide-text">
            心里想一个问题<br />
            轻触水晶球——<br />
            星灵会给你专属的回应
          </p>
          <div class="guide-crystal-demo">
            <div class="mini-crystal"></div>
            <span class="tap-arrow">👆</span>
          </div>
          <div class="guide-dots">
            <span class="dot"></span>
            <span class="dot dot--active"></span>
            <span class="dot"></span>
          </div>
          <button class="guide-btn" @click="nextStep">我知道了 ✨</button>
          <button class="guide-skip" @click="dismiss">跳过引导</button>
        </div>

        <!-- Step 3: 签到 -->
        <div class="guide-step" v-if="step === 3">
          <div class="guide-emoji">🌅</div>
          <h2 class="guide-title">每天来花园坐坐</h2>
          <p class="guide-text">
            星灵们每天都在变化<br />
            签到打卡，记录你的内在旅程<br />
            连续天数越多，羁绊越深
          </p>
          <div class="guide-streak-preview">
            <span class="streak-fire">🔥</span>
            <span class="streak-label">连续签到 · 星灵们会记住你</span>
          </div>
          <div class="guide-dots">
            <span class="dot"></span>
            <span class="dot"></span>
            <span class="dot dot--active"></span>
          </div>
          <button class="guide-btn" @click="dismiss">进入花园 🌸</button>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import SpiritAvatar from "./SpiritAvatar.vue";
import type { PlanetCharacterProfilesData, PlanetCharacterProfile } from "@/utils/types";

const props = defineProps<{
  planetProfiles: PlanetCharacterProfilesData | null;
}>();

const emit = defineEmits<{
  done: [];
}>();

const visible = ref(false);
const step = ref(1);

const sunProfile = ref<PlanetCharacterProfile | null>(null);
const sunSymbol = ref("☉");
const sunColor = ref("#F2A900");
const sunName = ref("太阳");

onMounted(() => {
  // 检查是否已完成引导
  const guided = localStorage.getItem("spirit_garden_guided");
  if (guided === "1") {
    emit("done");
    return;
  }
  visible.value = true;

  // 读取太阳数据
  const sun = props.planetProfiles?.planet_characters?.["SUN"] as
    | PlanetCharacterProfile
    | undefined;
  if (sun) {
    sunProfile.value = sun;
    sunSymbol.value = sun.persona?.symbol || "☉";
    sunColor.value = sun.persona?.visual_color || "#F2A900";
    sunName.value = sun.persona?.name_zh || "太阳";
  }
});

function nextStep() {
  if (step.value < 3) {
    step.value++;
  } else {
    dismiss();
  }
}

function dismiss() {
  localStorage.setItem("spirit_garden_guided", "1");
  visible.value = false;
  emit("done");
}
</script>

<style scoped>
.guide-overlay {
  position: fixed;
  inset: 0;
  z-index: 500;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  background: rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(8px);
}
.guide-card {
  width: 100%;
  max-width: 360px;
  padding: 36px 28px 28px;
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.95);
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.12);
  text-align: center;
}

.guide-fade-enter-active { transition: all 0.4s ease; }
.guide-fade-leave-active { transition: all 0.3s ease; }
.guide-fade-enter-from { opacity: 0; }
.guide-fade-leave-to { opacity: 0; }

.guide-step {
  display: flex;
  flex-direction: column;
  align-items: center;
}
.guide-emoji {
  font-size: 48px;
  margin-bottom: 12px;
}
.guide-title {
  font-size: 22px;
  font-weight: 700;
  color: #4a3728;
  margin: 0 0 10px;
  line-height: 1.4;
}
.guide-text {
  font-size: 14px;
  color: #8b7355;
  line-height: 1.7;
  margin: 0 0 20px;
}

/* Step 1 preview */
.guide-preview {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  border-radius: 18px;
  background: rgba(242, 169, 0, 0.06);
  border: 1px solid rgba(242, 169, 0, 0.15);
  margin-bottom: 20px;
  width: 100%;
}
.preview-symbol {
  font-size: 32px;
}
.preview-info {
  display: flex;
  flex-direction: column;
  gap: 3px;
  text-align: left;
}
.preview-name {
  font-size: 15px;
  font-weight: 700;
  color: #4a3728;
}
.preview-quote {
  font-size: 12px;
  color: #8b7355;
  font-style: italic;
}

/* Step 2 crystal demo */
.guide-crystal-demo {
  position: relative;
  margin-bottom: 20px;
}
.mini-crystal {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: radial-gradient(circle at 35% 35%, rgba(255,255,255,0.7), rgba(180,150,220,0.3), rgba(100,60,150,0.2));
  box-shadow: 0 0 30px rgba(180,150,220,0.2);
  animation: orb-float 3s ease-in-out infinite;
}
@keyframes orb-float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-6px); }
}
.tap-arrow {
  position: absolute;
  bottom: -8px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 18px;
  animation: tap-bounce 1s ease-in-out infinite;
}
@keyframes tap-bounce {
  0%, 100% { transform: translateX(-50%) translateY(0); }
  50% { transform: translateX(-50%) translateY(-6px); }
}

/* Step 3 streak */
.guide-streak-preview {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 14px 20px;
  border-radius: 16px;
  background: rgba(255,154,139,0.06);
  margin-bottom: 20px;
}
.streak-fire { font-size: 24px; }
.streak-label { font-size: 14px; color: #6b5744; font-weight: 600; }

/* Dots */
.guide-dots {
  display: flex;
  gap: 8px;
  margin-bottom: 18px;
}
.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: rgba(0,0,0,0.08);
}
.dot--active {
  background: #ff9a8b;
  width: 24px;
  border-radius: 4px;
}

/* Buttons */
.guide-btn {
  width: 100%;
  padding: 16px;
  border-radius: 18px;
  border: none;
  background: linear-gradient(135deg, #ff9a8b, #ffb8a8);
  color: #fff;
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  font-family: inherit;
  transition: all 0.2s;
}
.guide-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 16px rgba(255,154,139,0.3);
}
.guide-skip {
  margin-top: 10px;
  padding: 8px;
  border: none;
  background: none;
  color: #a89880;
  font-size: 13px;
  cursor: pointer;
  font-family: inherit;
}
</style>
