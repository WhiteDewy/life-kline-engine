<template>
  <div class="oracle-section">
    <!-- 标题 -->
    <div class="oracle-header">
      <h2 class="oracle-title">🔮 灵犀一刻</h2>
      <p class="oracle-sub">心里想一个问题，轻触水晶球——星灵会给你回应</p>
    </div>

    <!-- ═══ 初始态：水晶球 + 话题选择 ═══ -->
    <div class="oracle-stage" v-if="!oracleResult">
      <!-- 水晶球 -->
      <div class="crystal-ball" :class="{ 'crystal-ball--tapped': isAnimating }" @click="invokeOracle()">
        <div class="crystal-core">
          <!-- 内部光点 -->
          <span class="crystal-spark" v-for="s in 6" :key="s" :style="{ animationDelay: s * 0.5 + 's' }"></span>
          <!-- 中心光 -->
          <div class="crystal-center"></div>
        </div>
        <!-- 底部光晕 -->
        <div class="crystal-aura"></div>
      </div>

      <p class="tap-hint" v-if="!isAnimating">👆 轻触水晶球</p>
      <p class="tap-hint tap-hint--loading" v-else>星灵正在聆听...</p>

      <!-- 话题快捷 -->
      <div class="oracle-topics">
        <button
          v-for="t in quickTopics"
          :key="t.key"
          class="oracle-topic-btn"
          @click.stop="invokeOracle(t.key)"
        >
          {{ t.icon }} {{ t.label }}
        </button>
      </div>
    </div>

    <!-- ═══ 结果态：星灵回应卡片 ═══ -->
    <div class="oracle-result" v-else>
      <transition name="result-enter">
        <div class="result-card" :style="{ '--r-color': oracleResult.color }">
          <!-- 星灵头部 -->
          <div class="result-spirit-header">
            <SpiritAvatar :planet="oracleResult.planet" :symbol="oracleResult.symbol" :color="oracleResult.color" :name="oracleResult.name" size="md" />
            <div class="result-spirit-meta">
              <span class="result-spirit-name">{{ oracleResult.name }}</span>
              <span class="result-spirit-archetype">{{ oracleResult.archetype }}</span>
            </div>
            <span class="result-badge" :style="{ background: oracleResult.color + '15', color: oracleResult.color }">
              今日 {{ oracleResult.activationScore }}%
            </span>
          </div>

          <!-- 回应正文 -->
          <div class="result-body">
            <p class="result-message">"{{ oracleResult.message }}"</p>
            <div class="result-advice" v-if="oracleResult.advice">
              <span class="advice-icon">💡</span>
              <span>{{ oracleResult.advice }}</span>
            </div>
          </div>

          <!-- 操作 -->
          <div class="result-actions">
            <button class="result-btn result-btn--again" @click="invokeOracle()">
              🔄 再问一次
            </button>
            <button class="result-btn result-btn--chat" @click="$emit('chatWith', oracleResult.planet)">
              💬 和{{ oracleResult.name }}深聊
            </button>
            <button class="result-btn result-btn--share" @click="$emit('share', oracleResult)">
              📤 分享
            </button>
          </div>
        </div>
      </transition>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from "vue";
import SpiritAvatar from "./SpiritAvatar.vue";
import type {
  PlanetCharacterProfile,
  PlanetCharacterProfilesData,
  PlanetDailyActivation,
  DomainReport,
} from "@/utils/types";

const props = defineProps<{
  planetProfiles: PlanetCharacterProfilesData | null;
  dailyActivation: PlanetDailyActivation | null;
  domains: Record<string, DomainReport> | null;
}>();

const emit = defineEmits<{
  chatWith: [planet: string];
  share: [result: OracleResult];
}>();

const isAnimating = ref(false);
const oracleResult = ref<OracleResult | null>(null);
const shakeCooldown = ref(false);

const quickTopics = [
  { key: "romance", icon: "💛", label: "感情" },
  { key: "career", icon: "💼", label: "事业" },
  { key: "finance", icon: "💰", label: "财运" },
  { key: "family", icon: "🏠", label: "家庭" },
  { key: "health", icon: "🌿", label: "健康" },
  { key: "personal", icon: "🪐", label: "自我" },
];

interface OracleResult {
  planet: string;
  symbol: string;
  name: string;
  archetype: string;
  color: string;
  activationScore: number;
  message: string;
  advice: string;
}

// ── 摇一摇检测 ──
let lastShakeTime = 0;
function onDeviceMotion(e: DeviceMotionEvent) {
  if (shakeCooldown.value || isAnimating.value) return;
  const a = e.accelerationIncludingGravity;
  if (!a) return;
  const magnitude = Math.sqrt((a.x || 0) ** 2 + (a.y || 0) ** 2 + (a.z || 0) ** 2);
  if (magnitude > 18) {
    const now = Date.now();
    if (now - lastShakeTime > 2000) {
      lastShakeTime = now;
      invokeOracle();
    }
  }
}

onMounted(() => {
  if (typeof window !== "undefined") {
    window.addEventListener("devicemotion", onDeviceMotion);
  }
});
onBeforeUnmount(() => {
  if (typeof window !== "undefined") {
    window.removeEventListener("devicemotion", onDeviceMotion);
  }
});

async function invokeOracle(topicKey?: string) {
  if (isAnimating.value) return;
  isAnimating.value = true;
  oracleResult.value = null;

  // 水晶球响应延迟
  await new Promise((r) => setTimeout(r, 1000));

  const profiles = props.planetProfiles?.planet_characters || {};
  const activationScores = props.dailyActivation?.activation_scores || {};
  const featured = props.dailyActivation?.featured_planets || [];

  // 从今日激活度最高的 3 个中随机选 1 个（排除太阳，太阳太"稳定"）
  const candidates = featured.length >= 2
    ? featured.filter((f) => f.planet !== "SUN").slice(0, 2)
    : Object.entries(profiles)
        .filter(([k]) => k !== "SUN")
        .sort(
          (a, b) =>
            (activationScores[b[0]] || 0) - (activationScores[a[0]] || 0)
        )
        .slice(0, 2);

  if (candidates.length === 0) {
    isAnimating.value = false;
    return;
  }

  const picked = candidates[Math.floor(Math.random() * candidates.length)];
  const planetKey = typeof picked === "string" ? picked : picked.planet;
  const profile = profiles[planetKey] as PlanetCharacterProfile | undefined;
  if (!profile) {
    isAnimating.value = false;
    return;
  }

  // 确定话题
  const topic = topicKey || profile.persona?.expertise_domains?.[0] || "personal";
  const domain = props.domains?.[topic];
  const coreTheme = domain?.core_theme || "";
  const suggestion = domain?.suggestion || "";
  const structure = domain?.structure || "";

  // 生成回应
  const persona = profile.persona;
  const approach = persona?.advice_approach || "";
  const gift = persona?.gift_to_user || "";
  const voicePart = persona?.voice_tone?.slice(0, 50) || "";

  const greetings = [
    `让我看看...嗯，${coreTheme || "我看到了"}。`,
    `关于这件事——${voicePart}`,
    `你问到点子上了。${coreTheme || ""}`,
  ];

  const bodies = [
    `${structure?.slice(0, 180) || "你的星盘在这方面有很清晰的信号。"}`,
    `从我的位置看过去——${structure?.slice(0, 160) || "事情比你想的更简单，也比你想的更复杂。"}`,
    `${coreTheme || "这件事"}——你的星盘里藏着一个答案。${structure?.slice(0, 140) || ""}`,
  ];

  const adviceTexts = [
    suggestion?.slice(0, 120) || `${gift}`,
    `${approach?.slice(0, 100) || "跟着你的直觉走。"}`,
  ];

  oracleResult.value = {
    planet: planetKey,
    symbol: persona?.symbol || "●",
    name: persona?.name_zh || "",
    archetype: persona?.archetype_zh || "",
    color: persona?.visual_color || "#999",
    activationScore: Math.round(activationScores[planetKey] || 50),
    message: `${greetings[Math.floor(Math.random() * greetings.length)]} ${bodies[Math.floor(Math.random() * bodies.length)]}`.slice(0, 350),
    advice: adviceTexts[Math.floor(Math.random() * adviceTexts.length)],
  };

  isAnimating.value = false;
}
</script>

<style scoped>
.oracle-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.oracle-header {
  text-align: center;
}
.oracle-title {
  font-size: 20px;
  font-weight: 700;
  color: #4a3728;
  margin: 0 0 4px;
}
.oracle-sub {
  font-size: 13px;
  color: #8b7355;
  margin: 0;
}

/* ── 舞台 ── */
.oracle-stage {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 14px;
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
    0 0 30px rgba(180, 150, 220, 0.15),
    0 0 60px rgba(180, 150, 220, 0.08),
    inset 0 0 30px rgba(255, 255, 255, 0.2);
  transition: all 0.3s ease;
  animation: orb-float 4s ease-in-out infinite;
}
.crystal-ball:hover {
  box-shadow:
    0 0 40px rgba(200, 170, 240, 0.25),
    0 0 80px rgba(200, 170, 240, 0.12),
    inset 0 0 40px rgba(255, 255, 255, 0.3);
  transform: scale(1.05);
}
.crystal-ball--tapped {
  animation: orb-glow 0.6s ease-out;
}
@keyframes orb-float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-6px); }
}
@keyframes orb-glow {
  0% { box-shadow: 0 0 30px rgba(180, 150, 220, 0.15); }
  50% { box-shadow: 0 0 80px rgba(220, 200, 255, 0.5), 0 0 120px rgba(200, 170, 240, 0.3); }
  100% { box-shadow: 0 0 30px rgba(180, 150, 220, 0.15); }
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
.crystal-spark:nth-child(1) { top: 20%; left: 30%; animation-delay: 0s; }
.crystal-spark:nth-child(2) { top: 50%; left: 60%; animation-delay: 0.5s; }
.crystal-spark:nth-child(3) { top: 70%; left: 25%; animation-delay: 1s; }
.crystal-spark:nth-child(4) { top: 30%; left: 70%; animation-delay: 1.5s; }
.crystal-spark:nth-child(5) { top: 55%; left: 15%; animation-delay: 2s; }
.crystal-spark:nth-child(6) { top: 15%; left: 55%; animation-delay: 2.5s; }
@keyframes spark-drift {
  0%, 100% { opacity: 0.3; transform: translate(0, 0); }
  50% { opacity: 1; transform: translate(8px, -8px); }
}
.crystal-center {
  position: absolute;
  top: 50%; left: 50%;
  width: 12px; height: 12px;
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
  background: radial-gradient(ellipse, rgba(180, 150, 220, 0.2), transparent);
}

/* 提示文字 */
.tap-hint {
  font-size: 13px;
  color: #a89880;
  margin: 0;
  transition: all 0.3s;
}
.tap-hint--loading {
  color: #c4b5a5;
  animation: pulse-text 1s ease-in-out infinite;
}
@keyframes pulse-text {
  0%, 100% { opacity: 0.5; }
  50% { opacity: 1; }
}

/* ── 话题按钮 ── */
.oracle-topics {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 8px;
}
.oracle-topic-btn {
  padding: 8px 16px;
  border-radius: 16px;
  border: 1px solid rgba(0, 0, 0, 0.06);
  background: rgba(255, 255, 255, 0.7);
  font-size: 13px;
  color: #6b5744;
  cursor: pointer;
  font-family: inherit;
  transition: all 0.2s;
}
.oracle-topic-btn:hover {
  border-color: rgba(180, 150, 220, 0.3);
  background: rgba(255, 255, 255, 0.9);
  transform: translateY(-1px);
}

/* ── 结果卡片 ── */
.oracle-result {
  display: flex;
  justify-content: center;
}
.result-card {
  width: 100%;
  max-width: 400px;
  padding: 22px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.85);
  border: 1.5px solid var(--r-color);
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.05), 0 0 0 4px rgba(0, 0, 0, 0.02);
}

.result-enter-enter-active {
  transition: all 0.5s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}
.result-enter-enter-from {
  opacity: 0;
  transform: scale(0.9) translateY(16px);
}

.result-spirit-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 14px;
}
.result-symbol {
  font-size: 30px;
}
.result-spirit-meta {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 1px;
}
.result-spirit-name {
  font-size: 16px;
  font-weight: 700;
  color: #4a3728;
}
.result-spirit-archetype {
  font-size: 11px;
  color: #8b7355;
}
.result-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 10px;
}

.result-body {
  margin-bottom: 16px;
}
.result-message {
  font-size: 14px;
  color: #4a3728;
  line-height: 1.7;
  margin: 0 0 10px;
}
.result-advice {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 10px 14px;
  border-radius: 14px;
  background: rgba(240, 192, 96, 0.1);
  font-size: 13px;
  color: #6b5744;
  line-height: 1.5;
}
.advice-icon {
  flex-shrink: 0;
  font-size: 16px;
}

.result-actions {
  display: flex;
  gap: 10px;
}
.result-btn {
  flex: 1;
  padding: 12px 16px;
  border-radius: 16px;
  border: none;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  font-family: inherit;
  transition: all 0.2s;
}
.result-btn--again {
  background: rgba(0, 0, 0, 0.04);
  color: #8b7355;
}
.result-btn--again:hover {
  background: rgba(0, 0, 0, 0.07);
}
.result-btn--chat {
  background: var(--r-color);
  color: #fff;
}
.result-btn--chat:hover {
  filter: brightness(1.1);
}
.result-btn--share {
  background: rgba(240, 192, 96, 0.12);
  color: #8b7355;
  flex: 0;
  min-width: 60px;
}
.result-btn--share:hover {
  background: rgba(240, 192, 96, 0.2);
}
</style>
