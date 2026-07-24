<template>
  <transition name="onboarding-fade">
    <div class="onboarding-overlay" v-if="visible">
      <div class="onboarding-card">
        <!-- Step 1: 欢迎 -->
        <div class="onboarding-step" v-if="currentStep === 0" key="step-0">
          <div class="step-icon">🌌</div>
          <h1 class="step-title">星灵花园</h1>
          <p class="step-tagline">以星辰为据，与心对话。</p>
          <p class="step-text">十位星灵，十面镜子。每一次对话，都是和自己的相遇。</p>
          <div class="step-dots">
            <span v-for="i in 6" :key="i" class="dot" :class="{ 'dot--active': i - 1 === currentStep }"></span>
          </div>
          <button class="step-btn step-btn--primary" @click="nextStep">开始 →</button>
        </div>

        <!-- Step 2: 认识今日星灵 -->
        <div class="onboarding-step" v-if="currentStep === 1" key="step-1">
          <div class="step-avatar-wrap">
            <SpiritAvatar
              v-if="todayStarSpirit"
              :planet="todayStarSpirit.planet"
              :symbol="todayStarSpirit.symbol"
              :color="avatarColor"
              :name="avatarName"
              size="xl"
            />
            <div v-else class="step-emoji-large">🌟</div>
          </div>
          <h2 class="step-title">认识今日星灵</h2>
          <p class="step-text">
            <template v-if="avatarName">这位是你今天的引路星灵 —— {{ avatarName }}</template>
            <template v-else>每天有一位星灵在等你。</template>
          </p>
          <p class="step-desc">星灵们是入驻你星盘的能量化身。每天有一位星灵带着你当下的能量信号，和你分享专属的洞察与启发。</p>
          <div class="step-dots">
            <span v-for="i in 6" :key="i" class="dot" :class="{ 'dot--active': i - 1 === currentStep }"></span>
          </div>
          <div class="step-nav">
            <button class="step-btn step-btn--ghost" @click="prevStep">← 返回</button>
            <button class="step-btn" @click="nextStep">继续 →</button>
          </div>
        </div>

        <!-- Step 3: 怎么用 -->
        <div class="onboarding-step" v-if="currentStep === 2" key="step-2">
          <div class="step-emoji">💡</div>
          <h2 class="step-title">怎么用</h2>
          <div class="step-illustrations">
            <div class="step-il-item">
              <span class="il-icon">💬</span>
              <span class="il-text">和星灵聊天</span>
            </div>
            <div class="step-il-arrow">→</div>
            <div class="step-il-item">
              <span class="il-icon">📝</span>
              <span class="il-text">自动生成日记</span>
            </div>
            <div class="step-il-arrow">→</div>
            <div class="step-il-item">
              <span class="il-icon">🌟</span>
              <span class="il-text">看见自己</span>
            </div>
          </div>
          <div class="step-dots">
            <span v-for="i in 6" :key="i" class="dot" :class="{ 'dot--active': i - 1 === currentStep }"></span>
          </div>
          <div class="step-nav">
            <button class="step-btn step-btn--ghost" @click="prevStep">← 返回</button>
            <button class="step-btn" @click="nextStep">继续 →</button>
          </div>
        </div>

        <!-- Step 4: 每日一问 -->
        <div class="onboarding-step" v-if="currentStep === 3" key="step-3">
          <div class="step-emoji">❓</div>
          <h2 class="step-title">每日一问</h2>
          <p class="step-text">每天，星灵会问你一个问题——不是为了答案，是为了让你停下来想一想。</p>
          <div class="step-question-bubble">
            {{ sampleQuestion }}
          </div>
          <div class="step-dots">
            <span v-for="i in 6" :key="i" class="dot" :class="{ 'dot--active': i - 1 === currentStep }"></span>
          </div>
          <div class="step-nav">
            <button class="step-btn step-btn--ghost" @click="prevStep">← 返回</button>
            <button class="step-btn" @click="nextStep">继续 →</button>
          </div>
        </div>

        <!-- Step 5: 星灵日记 -->
        <div class="onboarding-step" v-if="currentStep === 4" key="step-4">
          <div class="step-emoji">📔</div>
          <h2 class="step-title">星灵日记</h2>
          <p class="step-text">你和星灵的每一次对话，都会变成一篇日记。存得越久，你越了解自己。</p>
          <div class="step-diary-preview">
            <div class="diary-stack">
              <div class="diary-item" v-for="i in 3" :key="i" :style="{ transform: `rotate(${(i - 2) * 3}deg)` }">
                <span class="diary-date">{{ diaryDates[i - 1] }}</span>
                <span class="diary-snippet">今日星灵说...</span>
              </div>
            </div>
          </div>
          <div class="step-dots">
            <span v-for="i in 6" :key="i" class="dot" :class="{ 'dot--active': i - 1 === currentStep }"></span>
          </div>
          <div class="step-nav">
            <button class="step-btn step-btn--ghost" @click="prevStep">← 返回</button>
            <button class="step-btn" @click="nextStep">继续 →</button>
          </div>
        </div>

        <!-- Step 6: 完成 -->
        <div class="onboarding-step" v-if="currentStep === 5" key="step-5">
          <div class="step-emoji">✨</div>
          <h2 class="step-title">准备好了吗？</h2>
          <p class="step-text">星灵们已经就位，你的花园正等待着你。</p>
          <div class="step-dots">
            <span v-for="i in 6" :key="i" class="dot" :class="{ 'dot--active': i - 1 === currentStep }"></span>
          </div>
          <button class="step-btn step-btn--primary step-btn--large" @click="complete">进入星灵花园</button>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { ref, computed } from "vue";
import SpiritAvatar from "@/components/garden/SpiritAvatar.vue";

const props = defineProps<{
  visible: boolean;
  todayStarSpirit?: {
    planet: string;
    planet_label?: string;
    symbol?: string;
    [key: string]: any;
  } | null;
  todaysPlanetProfile?: {
    persona?: {
      name_zh?: string;
      visual_color?: string;
      [key: string]: any;
    };
    [key: string]: any;
  } | null;
  dailyQuestion?: string;
}>();

const emit = defineEmits<{
  close: [];
}>();

const currentStep = ref(0);

const avatarName = computed(() => {
  if (props.todaysPlanetProfile?.persona?.name_zh) return props.todaysPlanetProfile.persona.name_zh;
  if (props.todayStarSpirit?.planet_label) return props.todayStarSpirit.planet_label;
  return "";
});

const avatarColor = computed(() => {
  return props.todaysPlanetProfile?.persona?.visual_color || "#F2A900";
});

const sampleQuestion = computed(() => {
  return props.dailyQuestion || "今天，你允许自己感到快乐吗？";
});

const diaryDates = ["7月18日", "7月17日", "7月16日"];

function nextStep() {
  if (currentStep.value < 5) {
    currentStep.value++;
  }
}

function prevStep() {
  if (currentStep.value > 0) {
    currentStep.value--;
  }
}

function complete() {
  localStorage.setItem("spirit_profile_completed", "1");
  emit("close");
}
</script>

<style scoped>
.onboarding-overlay {
  position: fixed;
  inset: 0;
  z-index: 500;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  background: rgba(0, 0, 0, 0.35);
  backdrop-filter: blur(10px);
}

.onboarding-card {
  width: 100%;
  max-width: 420px;
  padding: 40px 32px 32px;
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.95);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
  text-align: center;
  position: relative;
}

/* ── Transition ── */
.onboarding-fade-enter-active { transition: all 0.4s ease; }
.onboarding-fade-leave-active { transition: all 0.3s ease; }
.onboarding-fade-enter-from { opacity: 0; }
.onboarding-fade-leave-to { opacity: 0; }

/* ── Step container ── */
.onboarding-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  animation: step-in 0.35s ease both;
}

@keyframes step-in {
  from { opacity: 0; transform: translateY(12px); }
  to   { opacity: 1; transform: translateY(0); }
}

/* ── Common elements ── */
.step-emoji {
  font-size: 52px;
  margin-bottom: 16px;
  line-height: 1;
}

.step-emoji-large {
  font-size: 72px;
  margin-bottom: 8px;
  line-height: 1;
}

.step-title {
  font-size: 24px;
  font-weight: 700;
  color: #4a3728;
  margin: 0 0 10px;
  line-height: 1.4;
}

.step-tagline {
  font-size: 16px;
  font-weight: 600;
  color: #ff9a8b;
  margin: 0 0 8px;
  line-height: 1.4;
}

.step-text {
  font-size: 14px;
  color: #8b7355;
  line-height: 1.7;
  margin: 0 0 8px;
  max-width: 320px;
}

.step-desc {
  font-size: 13px;
  color: #a89880;
  line-height: 1.6;
  margin: 0 0 20px;
  max-width: 300px;
}

/* ── Avatar (Step 2) ── */
.step-avatar-wrap {
  margin-bottom: 12px;
}

/* ── Dots ── */
.step-dots {
  display: flex;
  gap: 8px;
  margin: 20px 0 18px;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
}

.dot--active {
  width: 24px;
  border-radius: 4px;
  background: #ff9a8b;
}

/* ── Buttons ── */
.step-btn {
  width: 100%;
  padding: 14px 24px;
  border-radius: 18px;
  border: none;
  background: rgba(255, 154, 139, 0.15);
  color: #6b5744;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  font-family: inherit;
  transition: all 0.25s;
}

.step-btn:hover {
  background: rgba(255, 154, 139, 0.25);
  transform: translateY(-1px);
}

.step-btn--primary {
  background: linear-gradient(135deg, #ff9a8b, #ffb8a8);
  color: #fff;
  font-weight: 700;
}

.step-btn--primary:hover {
  box-shadow: 0 4px 16px rgba(255, 154, 139, 0.35);
}

.step-btn--large {
  padding: 16px 24px;
  font-size: 17px;
}

.step-btn--ghost {
  background: transparent;
  color: #a89880;
  font-weight: 500;
  padding: 10px 16px;
  flex: 0 0 auto;
  width: auto;
}

.step-btn--ghost:hover {
  background: rgba(0, 0, 0, 0.04);
  transform: none;
}

/* ── Nav row ── */
.step-nav {
  display: flex;
  gap: 12px;
  width: 100%;
}

.step-nav .step-btn {
  flex: 1;
}

/* ── Illustrations (Step 3) ── */
.step-illustrations {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 12px 0 8px;
  padding: 16px 12px;
  border-radius: 18px;
  background: rgba(242, 169, 0, 0.05);
  border: 1px solid rgba(242, 169, 0, 0.1);
  width: 100%;
  max-width: 340px;
}

.step-il-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  flex: 1;
}

.il-icon {
  font-size: 28px;
  line-height: 1;
}

.il-text {
  font-size: 11px;
  font-weight: 600;
  color: #6b5744;
  white-space: nowrap;
}

.step-il-arrow {
  font-size: 16px;
  color: #c4b4a0;
  line-height: 1;
}

/* ── Question bubble (Step 4) ── */
.step-question-bubble {
  margin: 12px 0 4px;
  padding: 16px 20px;
  border-radius: 18px;
  background: rgba(242, 169, 0, 0.06);
  border: 1px solid rgba(242, 169, 0, 0.12);
  font-size: 14px;
  color: #4a3728;
  line-height: 1.6;
  font-style: italic;
  width: 100%;
  max-width: 320px;
}

/* ── Diary preview (Step 5) ── */
.step-diary-preview {
  margin: 12px 0 4px;
  width: 100%;
  max-width: 300px;
}

.diary-stack {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.diary-item {
  display: flex;
  justify-content: space-between;
  padding: 12px 16px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.8);
  border: 1px solid rgba(0, 0, 0, 0.06);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.diary-date {
  font-size: 12px;
  color: #a89880;
  font-weight: 500;
}

.diary-snippet {
  font-size: 12px;
  color: #8b7355;
  font-style: italic;
}

/* ── Step icon override for step 1 ── */
.step-icon {
  font-size: 56px;
  margin-bottom: 12px;
  line-height: 1;
}

/* ── Responsive ── */
@media (max-width: 480px) {
  .onboarding-card {
    padding: 32px 24px 28px;
  }
  .step-title {
    font-size: 21px;
  }
  .step-illustrations {
    gap: 4px;
    padding: 12px 8px;
  }
  .il-icon {
    font-size: 24px;
  }
}
</style>
