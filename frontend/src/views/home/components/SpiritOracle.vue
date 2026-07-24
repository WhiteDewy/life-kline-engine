<template>
  <transition name="card-enter">
    <div
      v-if="visible"
      class="spirit-oracle"
      :style="{ '--spirit-color': spiritColor }"
    >
      <!-- ═══════════════════════════════════════════
        State 1: 水晶球等待态
      ═══════════════════════════════════════════ -->
      <div v-if="state === 'crystal'" class="crystal-stage">
        <div
          class="crystal-ball"
          :class="{ 'crystal-ball--tapped': isAnimating }"
          @click="revealQuestion()"
        >
          <div class="crystal-core">
            <span
              v-for="s in 6"
              :key="s"
              class="crystal-spark"
              :style="{ animationDelay: s * 0.5 + 's' }"
            ></span>
            <div class="crystal-center"></div>
          </div>
          <div class="crystal-aura"></div>
        </div>

        <p v-if="!isAnimating" class="hint-text">
          轻触水晶球，<br />今天有位星灵有话想对你说
        </p>
        <p v-else class="hint-text hint-text--loading">星灵正在接近...</p>

        <div class="oracle-actions">
          <button class="action-btn" :disabled="isAnimating" @click="revealQuestion()">
            <span class="action-icon">🔮</span>
            <span class="action-label">轻触水晶球</span>
          </button>
          <button class="action-btn action-btn--shake" :disabled="isAnimating" @click="revealQuestion()">
            <span class="action-icon">📱</span>
            <span class="action-label">摇一摇</span>
          </button>
        </div>
      </div>

      <!-- ═══════════════════════════════════════════
        State 2: 星灵登场 + 揭示问题
      ═══════════════════════════════════════════ -->
      <div v-else class="revealed-stage">
        <div class="revealed-content">
          <transition name="spirit-enter">
            <div key="spirit-revealed">
              <!-- Header -->
              <div class="card-header">
                <span class="card-icon">🌟</span>
                <span class="card-title">今日星灵登场</span>
                <button class="card-close" @click="handleClose">✕</button>
              </div>

              <!-- Spirit Avatar + breathing ring -->
              <div class="spirit-section">
                <div class="spirit-ring" :style="ringStyle">
                  <SpiritAvatar
                    :planet="todayStarSpirit?.planet"
                    :symbol="todayStarSpirit?.symbol"
                    :color="spiritColor"
                    :name="spiritName"
                    :gender="gender"
                    size="md"
                  />
                </div>
              </div>

              <!-- Spirit greeting -->
              <p class="spirit-greeting">我是今天的引路星灵——{{ spiritName }}</p>

              <!-- Daily question -->
              <div class="question-section">
                <p class="question-text">"{{ question }}"</p>
              </div>

              <!-- Context / astrological note -->
              <p v-if="contextNote" class="context-note">{{ contextNote }}</p>

              <!-- Action buttons -->
              <div class="card-actions">
                <div class="action-btn-wrapper">
                  <VoicePlayer :text="question" :style="'whisper'" showLabel />
                </div>
                <button class="action-btn action-btn--chat" @click="$emit('chat')">
                  <span class="action-icon">💬</span>
                  <span class="action-label">和{{ spiritName }}聊聊</span>
                </button>
              </div>

              <!-- History -->
              <div v-if="history.length > 0" class="history-section">
                <div class="history-title">── 历史灵犀 ──</div>
                <div
                  v-for="(entry, i) in history"
                  :key="i"
                  class="history-entry"
                >
                  <span class="history-date">📅 {{ entry.date }}</span>
                  <span class="history-body">{{ entry.spirit_planet_label }}：{{ entry.question }}</span>
                </div>
              </div>
            </div>
          </transition>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onBeforeUnmount } from "vue";
import SpiritAvatar from "@/components/garden/SpiritAvatar.vue";
import VoicePlayer from "./VoicePlayer.vue";

const props = defineProps<{
  visible: boolean;
  todayStarSpirit?: any;
  dailyQuestion?: any;
  spiritProfile?: any;
  gender?: string;
}>();

const emit = defineEmits<{
  chat: [];
  close: [];
}>();

// ── State machine ──
const state = ref<"crystal" | "revealed">("crystal");
const isAnimating = ref(false);

// ── Computed ──

const spiritName = computed(() => {
  if (props.spiritProfile?.persona?.name_zh) return props.spiritProfile.persona.name_zh;
  if (props.todayStarSpirit?.planet_label) return props.todayStarSpirit.planet_label;
  if (props.dailyQuestion?.spirit_planet_label) return props.dailyQuestion.spirit_planet_label;
  return "星灵";
});

const spiritColor = computed(() => {
  if (props.spiritProfile?.persona?.visual_color) return props.spiritProfile.persona.visual_color;
  if (props.todayStarSpirit?.color) return props.todayStarSpirit.color;
  return "#8B7DBA";
});

const question = computed(() => props.dailyQuestion?.question || "");
const contextNote = computed(() => props.dailyQuestion?.context_note || "");

const ringStyle = computed(() => ({
  "--ring-color": spiritColor.value,
}));

// ── Shake detection ──

let lastX = 0;
let lastY = 0;
let lastZ = 0;
let shakeTimer: ReturnType<typeof setTimeout> | null = null;

function onDeviceMotion(e: DeviceMotionEvent) {
  if (isAnimating.value || state.value !== "crystal") return;
  const acc = e.accelerationIncludingGravity;
  if (!acc) return;
  const delta =
    Math.abs((acc.x || 0) - lastX) +
    Math.abs((acc.y || 0) - lastY) +
    Math.abs((acc.z || 0) - lastZ);
  if (delta > 15) {
    if (shakeTimer) return;
    shakeTimer = setTimeout(() => {
      shakeTimer = null;
    }, 2000);
    revealQuestion();
  }
  lastX = acc.x || 0;
  lastY = acc.y || 0;
  lastZ = acc.z || 0;
}

// ── Lifecycle ──

onMounted(() => {
  updateHistory();
  if (typeof window !== "undefined") {
    window.addEventListener("devicemotion", onDeviceMotion);
  }
});

onBeforeUnmount(() => {
  if (typeof window !== "undefined") {
    window.removeEventListener("devicemotion", onDeviceMotion);
  }
  if (shakeTimer) clearTimeout(shakeTimer);
});

// ── Reveal animation ──

async function revealQuestion() {
  if (isAnimating.value || state.value !== "crystal") return;
  isAnimating.value = true;
  await new Promise((r) => setTimeout(r, 1500));
  state.value = "revealed";
  isAnimating.value = false;
  saveToHistory();
}

function handleClose() {
  emit("close");
}

// Reset to crystal state when re-opened
watch(
  () => props.visible,
  (val) => {
    if (val) {
      state.value = "crystal";
      isAnimating.value = false;
    }
  }
);

// ── History (localStorage) ──

const HISTORY_KEY = "spirit_oracle_history";
const history = ref<any[]>([]);

interface HistoryEntry {
  date: string;
  question: string;
  spirit_planet: string;
  spirit_planet_label: string;
}

function loadHistory(): HistoryEntry[] {
  try {
    const raw = localStorage.getItem(HISTORY_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function updateHistory() {
  history.value = loadHistory().slice(0, 5);
}

function saveToHistory() {
  if (!props.dailyQuestion?.question) return;
  const d = new Date();
  const dateStr = `${d.getMonth() + 1}/${d.getDate()}`;
  const allHistory = loadHistory();

  // Don't duplicate today's entry for the same spirit
  const exists = allHistory.some(
    (h) =>
      h.date === dateStr &&
      h.spirit_planet === (props.todayStarSpirit?.planet || "")
  );
  if (exists) return;

  allHistory.unshift({
    date: dateStr,
    question: props.dailyQuestion.question.slice(0, 35),
    spirit_planet: props.todayStarSpirit?.planet || "",
    spirit_planet_label: spiritName.value,
  });

  localStorage.setItem(HISTORY_KEY, JSON.stringify(allHistory.slice(0, 20)));
  updateHistory();
}
</script>

<style scoped>
/* ═══════════════════════════════════════════════
   Card container — glassmorphism, fixed bottom
═══════════════════════════════════════════════ */
.spirit-oracle {
  position: fixed;
  bottom: 100px;
  left: 16px;
  right: 16px;
  z-index: 50;
  max-width: 480px;
  margin: 0 auto;
  padding: 24px 20px 20px;
  background: rgba(20, 20, 30, 0.85);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-radius: 24px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow:
    0 8px 40px rgba(0, 0, 0, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.06);
  max-height: 80vh;
  overflow-y: auto;
}

/* scrollbar */
.spirit-oracle::-webkit-scrollbar {
  width: 3px;
}
.spirit-oracle::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.15);
  border-radius: 2px;
}

/* ── 入场动画 ── */
.card-enter-enter-active {
  transition: all 0.5s cubic-bezier(0.32, 0.02, 0, 1);
}
.card-enter-leave-active {
  transition: all 0.3s ease;
}
.card-enter-enter-from {
  opacity: 0;
  transform: translateY(24px);
}
.card-enter-leave-to {
  opacity: 0;
  transform: translateY(16px);
}

/* ═══════════════════════════════════════════════
   State 1 — Crystal Ball
═══════════════════════════════════════════════ */
.crystal-stage {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

/* ── 水晶球 ── */
.crystal-ball {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  position: relative;
  cursor: pointer;
  background: radial-gradient(
    circle at 35% 35%,
    rgba(255, 255, 255, 0.7) 0%,
    rgba(200, 180, 220, 0.4) 25%,
    rgba(150, 130, 180, 0.25) 50%,
    rgba(100, 80, 150, 0.15) 75%,
    rgba(60, 40, 100, 0.2) 100%
  );
  box-shadow:
    0 0 30px color-mix(in srgb, var(--spirit-color, #8b7dba) 15%, transparent),
    0 0 60px color-mix(in srgb, var(--spirit-color, #8b7dba) 8%, transparent),
    inset 0 0 30px rgba(255, 255, 255, 0.2);
  transition: all 0.3s ease;
  animation: orb-float 4s ease-in-out infinite;
  flex-shrink: 0;
}
.crystal-ball:hover {
  box-shadow:
    0 0 40px color-mix(in srgb, var(--spirit-color, #8b7dba) 25%, transparent),
    0 0 80px color-mix(in srgb, var(--spirit-color, #8b7dba) 12%, transparent),
    inset 0 0 40px rgba(255, 255, 255, 0.3);
  transform: scale(1.05);
}
.crystal-ball--tapped {
  animation: orb-glow-reveal 1.5s ease-out forwards;
}

@keyframes orb-float {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-6px);
  }
}
@keyframes orb-glow-reveal {
  0% {
    box-shadow:
      0 0 30px color-mix(in srgb, var(--spirit-color, #8b7dba) 15%, transparent),
      0 0 60px color-mix(in srgb, var(--spirit-color, #8b7dba) 8%, transparent);
  }
  50% {
    box-shadow:
      0 0 80px color-mix(in srgb, var(--spirit-color, #8b7dba) 50%, transparent),
      0 0 120px color-mix(in srgb, var(--spirit-color, #8b7dba) 30%, transparent);
  }
  100% {
    box-shadow:
      0 0 100px color-mix(in srgb, var(--spirit-color, #8b7dba) 60%, transparent),
      0 0 160px color-mix(in srgb, var(--spirit-color, #8b7dba) 40%, transparent);
  }
}

/* 内部光点 */
.crystal-core {
  position: absolute;
  inset: 15%;
  border-radius: 50%;
  overflow: hidden;
}
.crystal-spark {
  position: absolute;
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.9);
  animation: spark-drift 3s ease-in-out infinite;
}
.crystal-spark:nth-child(1) {
  top: 20%;
  left: 30%;
  animation-delay: 0s;
}
.crystal-spark:nth-child(2) {
  top: 50%;
  left: 60%;
  animation-delay: 0.5s;
}
.crystal-spark:nth-child(3) {
  top: 70%;
  left: 25%;
  animation-delay: 1s;
}
.crystal-spark:nth-child(4) {
  top: 30%;
  left: 70%;
  animation-delay: 1.5s;
}
.crystal-spark:nth-child(5) {
  top: 55%;
  left: 15%;
  animation-delay: 2s;
}
.crystal-spark:nth-child(6) {
  top: 15%;
  left: 55%;
  animation-delay: 2.5s;
}
@keyframes spark-drift {
  0%,
  100% {
    opacity: 0.3;
    transform: translate(0, 0);
  }
  50% {
    opacity: 1;
    transform: translate(8px, -8px);
  }
}
.crystal-center {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.8);
  transform: translate(-50%, -50%);
  box-shadow: 0 0 12px rgba(255, 255, 255, 0.6);
}

/* 底部光晕 */
.crystal-aura {
  position: absolute;
  bottom: -20px;
  left: 50%;
  transform: translateX(-50%);
  width: 80px;
  height: 20px;
  border-radius: 50%;
  background: radial-gradient(
    ellipse,
    color-mix(in srgb, var(--spirit-color, #8b7dba) 20%, transparent),
    transparent
  );
}

/* ── 提示文字 ── */
.hint-text {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.75);
  margin: 0;
  text-align: center;
  line-height: 1.6;
  text-shadow: 0 1px 4px rgba(0, 0, 0, 0.2);
}
.hint-text--loading {
  animation: pulse-text 1s ease-in-out infinite;
  color: rgba(255, 255, 255, 0.5);
}
@keyframes pulse-text {
  0%,
  100% {
    opacity: 0.5;
  }
  50% {
    opacity: 1;
  }
}

/* ── 操作按钮 (水晶球状态下) ── */
.oracle-actions {
  display: flex;
  gap: 10px;
  width: 100%;
}
.oracle-actions .action-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 12px 14px;
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  background: rgba(255, 255, 255, 0.06);
  color: #fff;
  font-size: 13px;
  font-weight: 600;
  font-family: inherit;
  cursor: pointer;
  transition: all 0.25s ease;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(4px);
}
.oracle-actions .action-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.14);
  transform: translateY(-1px);
}
.oracle-actions .action-btn:active:not(:disabled) {
  transform: scale(0.97);
}
.oracle-actions .action-btn:disabled {
  opacity: 0.4;
  cursor: default;
}
.oracle-actions .action-icon {
  font-size: 16px;
  line-height: 1;
}

/* ═══════════════════════════════════════════════
   State 2 — Revealed
═══════════════════════════════════════════════ */
.revealed-stage {
  /* container for revealed content */
}
.revealed-content {
  display: flex;
  flex-direction: column;
  gap: 0;
}

/* 星灵登场入场动画 */
.spirit-enter-enter-active {
  transition: all 0.6s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}
.spirit-enter-enter-from {
  opacity: 0;
  transform: scale(0.85) translateY(20px);
}

/* ── Header ── */
.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
}
.card-icon {
  font-size: 20px;
  line-height: 1;
}
.card-title {
  flex: 1;
  font-size: 15px;
  font-weight: 700;
  color: #fff;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
  letter-spacing: 0.5px;
}
.card-close {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  border: none;
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.5);
  font-size: 11px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  flex-shrink: 0;
}
.card-close:hover {
  background: rgba(255, 255, 255, 0.18);
  color: #fff;
}

/* ── Spirit avatar section ── */
.spirit-section {
  display: flex;
  justify-content: center;
  margin-bottom: 14px;
}

/* 呼吸光晕环 (from StarSpiritDisplay) */
.spirit-ring {
  position: relative;
  width: 56px;
  height: 56px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: ring-pulse 2.5s ease-in-out infinite;
  box-shadow: 0 0 0 0 var(--ring-color, #8b7dba);
}
@keyframes ring-pulse {
  0% {
    box-shadow: 0 0 0 0 color-mix(in srgb, var(--ring-color, #8b7dba) 40%, transparent);
  }
  50% {
    box-shadow: 0 0 0 10px color-mix(in srgb, var(--ring-color, #8b7dba) 15%, transparent);
  }
  100% {
    box-shadow: 0 0 0 0 color-mix(in srgb, var(--ring-color, #8b7dba) 40%, transparent);
  }
}

/* ── Greeting ── */
.spirit-greeting {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.8);
  text-align: center;
  margin: 0 0 16px;
  line-height: 1.5;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.15);
  font-weight: 500;
}

/* ── Question ── */
.question-section {
  margin-bottom: 12px;
}
.question-text {
  font-size: 17px;
  font-weight: 600;
  color: #fff;
  line-height: 1.6;
  margin: 0;
  text-shadow: 0 1px 4px rgba(0, 0, 0, 0.15);
}

/* ── Context note ── */
.context-note {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.6);
  line-height: 1.5;
  margin: 0 0 16px;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
  padding: 10px 14px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.06);
}

/* ── Actions ── */
.card-actions {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
}
.card-actions .action-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px 14px;
  border-radius: 14px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  background: rgba(255, 255, 255, 0.06);
  color: #fff;
  font-size: 13px;
  font-weight: 600;
  font-family: inherit;
  cursor: pointer;
  transition: all 0.25s ease;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}
.card-actions .action-btn:hover {
  background: rgba(255, 255, 255, 0.14);
  transform: translateY(-1px);
}
.card-actions .action-btn:active {
  transform: scale(0.97);
}
.card-actions .action-btn--chat {
  background: linear-gradient(
    135deg,
    color-mix(in srgb, var(--spirit-color, #8b7dba) 25%, transparent) 0%,
    color-mix(in srgb, var(--spirit-color, #8b7dba) 10%, transparent) 100%
  );
  border-color: color-mix(in srgb, var(--spirit-color, #8b7dba) 25%, transparent);
}
.card-actions .action-btn--chat:hover {
  background: linear-gradient(
    135deg,
    color-mix(in srgb, var(--spirit-color, #8b7dba) 35%, transparent) 0%,
    color-mix(in srgb, var(--spirit-color, #8b7dba) 15%, transparent) 100%
  );
}
.action-btn-wrapper {
  flex: 1;
}
.action-icon {
  font-size: 16px;
  line-height: 1;
}
.action-label {
  white-space: nowrap;
}

/* ── History ── */
.history-section {
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  padding-top: 14px;
}
.history-title {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.35);
  letter-spacing: 1px;
  margin-bottom: 10px;
  text-align: center;
}
.history-entry {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 0;
  cursor: default;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
  line-height: 1.4;
  transition: color 0.2s;
}
.history-entry:hover {
  color: rgba(255, 255, 255, 0.7);
}
.history-date {
  flex-shrink: 0;
  font-size: 11px;
}
.history-body {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* ═══════════════════════════════════════════════
   Responsive
═══════════════════════════════════════════════ */
@media (min-width: 520px) {
  .spirit-oracle {
    left: 50%;
    transform: translateX(-50%);
    padding: 28px 24px 22px;
  }
  .crystal-ball {
    width: 130px;
    height: 130px;
  }
}
</style>
