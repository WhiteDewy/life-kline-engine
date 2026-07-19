<template>
  <div class="ritual-card" :class="'ritual-card--' + timeMode">
    <!-- 时间氛围头部 -->
    <div class="ritual-atmo">
      <span class="ritual-emoji">{{ timeEmoji }}</span>
      <div class="ritual-greeting">
        <span class="ritual-hello">{{ greeting }}</span>
        <span class="ritual-phase">{{ phaseNote }}</span>
      </div>
    </div>

    <!-- 签到 + 心情 -->
    <div class="ritual-checkin" v-if="!checkedInToday">
      <div class="mood-picker" v-if="showMoodPicker">
        <p class="mood-prompt">今天的心情是？</p>
        <div class="mood-emojis">
          <button v-for="m in moods" :key="m.emoji" class="mood-btn" @click="doCheckIn(m.emoji)">
            <span class="mood-emoji">{{ m.emoji }}</span>
            <span class="mood-word">{{ m.label }}</span>
          </button>
        </div>
      </div>
      <button v-else class="checkin-btn" @click="showMoodPicker = true">
        {{ timeAction }}
      </button>
      <p class="checkin-streak" v-if="streak > 0 && !showMoodPicker">
        🔥 已连续签到 <strong>{{ streak }}</strong> 天
      </p>
    </div>
    <div class="ritual-checkin ritual-checkin--done" v-else>
      <div class="checked-badge">
        <span class="checked-icon">{{ todayMood || '✅' }}</span>
        <span>今日已签到 · 连续 {{ streak }} 天</span>
      </div>
      <div class="notify-prompt" v-if="notifySupported && !notifyDenied && !notifyScheduled">
        <button class="notify-btn" @click="requestNotify">
          🔔 明天提醒我来花园
        </button>
      </div>
      <div class="notify-prompt" v-else-if="notifyScheduled">
        <span class="notify-done">🔔 明天会提醒你~</span>
      </div>
    </div>

    <!-- 今日星灵寄语 -->
    <div class="ritual-blessing" v-if="featuredSpirit">
      <SpiritAvatar :planet="featuredSpirit.planet" :symbol="featuredSpirit.symbol" :name="featuredSpirit.name_zh" size="sm" />
      <span class="blessing-text">"{{ featuredSpiritMessage }}"</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import SpiritAvatar from "./SpiritAvatar.vue";
import type { FeaturedPlanet } from "@/utils/types";

const props = defineProps<{
  featuredPlanets: FeaturedPlanet[];
  dailyTheme: string;
}>();

const checkedInToday = ref(false);
const isChecking = ref(false);
const streak = ref(0);
const showMoodPicker = ref(false);
const todayMood = ref("");

const moods = [
  { emoji: "😊", label: "开心" },
  { emoji: "😌", label: "平静" },
  { emoji: "🤔", label: "思考" },
  { emoji: "😢", label: "低落" },
  { emoji: "😤", label: "烦躁" },
  { emoji: "✨", label: "期待" },
];

// ── 时间段检测 ──
const timeMode = computed(() => {
  const h = new Date().getHours();
  if (h >= 6 && h < 12) return "morning";
  if (h >= 12 && h < 18) return "afternoon";
  return "night";
});

const timeEmoji = computed(() => {
  return { morning: "🌅", afternoon: "☀️", night: "🌙" }[timeMode.value];
});

const greeting = computed(() => {
  return {
    morning: "早安，星灵们已经醒来",
    afternoon: "午后阳光正好",
    night: "夜深了，月亮在守护你",
  }[timeMode.value];
});

const phaseNote = computed(() => {
  return {
    morning: "新的一天，新的能量在流动",
    afternoon: "星灵们正在你身边低语",
    night: "安静下来，听听内心的回音",
  }[timeMode.value];
});

const timeAction = computed(() => {
  return {
    morning: "🌞 开始今天的探索",
    afternoon: "🌟 记录此刻的感受",
    night: "🌙 给今天的自己一个拥抱",
  }[timeMode.value];
});

// ── 今日星灵寄语 ──
const featuredSpirit = computed(() => {
  return props.featuredPlanets?.[0] || null;
});

const featuredSpiritMessage = computed(() => {
  const spirit = featuredSpirit.value;
  if (!spirit) return "每一天，你的星灵都在用不同的方式陪你成长。";
  const msg = spirit.daily_message || "";
  return msg.slice(0, 80) || `我是${spirit.name_zh}，今天让我陪着你。`;
});

// ── 签到逻辑 ──
function loadCheckIn() {
  try {
    const today = new Date().toISOString().slice(0, 10);
    const data = JSON.parse(localStorage.getItem("spirit_checkin") || "{}");
    if (data.date === today) {
      checkedInToday.value = true;
      todayMood.value = data.mood || "";
    }
    streak.value = data.streak || 0;
  } catch { /* ignore */ }
}

function doCheckIn(mood: string) {
  if (isChecking.value) return;
  isChecking.value = true;
  showMoodPicker.value = false;
  todayMood.value = mood;

  const today = new Date().toISOString().slice(0, 10);
  let currentStreak = streak.value;

  try {
    const data = JSON.parse(localStorage.getItem("spirit_checkin") || "{}");
    const lastDate = data.date || "";
    const yesterday = new Date(Date.now() - 86400000).toISOString().slice(0, 10);
    if (lastDate === yesterday) { currentStreak = (data.streak || 0) + 1; }
    else if (lastDate !== today) { currentStreak = 1; }
  } catch { currentStreak = 1; }

  streak.value = currentStreak;
  localStorage.setItem("spirit_checkin", JSON.stringify({ date: today, streak: currentStreak, mood }));

  // 存入 mood 历史
  saveMoodHistory(today, mood);

  setTimeout(() => { checkedInToday.value = true; isChecking.value = false; }, 600);
}

function saveMoodHistory(date: string, mood: string) {
  try {
    const raw = localStorage.getItem("spirit_mood_history") || "[]";
    const history = JSON.parse(raw);
    history.push({ date, mood });
    if (history.length > 90) history.splice(0, history.length - 90);
    localStorage.setItem("spirit_mood_history", JSON.stringify(history));
  } catch { /* ignore */ }
}

// ── 通知 ──
const notifySupported = ref(typeof Notification !== "undefined");
const notifyDenied = ref(Notification?.permission === "denied");
const notifyScheduled = ref(false);

async function requestNotify() {
  try {
    const perm = await Notification.requestPermission();
    if (perm === "granted") {
      notifyScheduled.value = true;
      localStorage.setItem("spirit_notify", "granted");
      // 明天同一时间提醒
      const msUntilTomorrow = 24 * 60 * 60 * 1000;
      setTimeout(() => {
        new Notification("🌸 星灵花园", {
          body: "星灵们想你了——今天来花园坐坐吧 ✨",
          icon: "/favicon.ico",
        });
      }, msUntilTomorrow);
    } else {
      notifyDenied.value = true;
    }
  } catch {
    notifyDenied.value = true;
  }
}

onMounted(() => {
  loadCheckIn();
  if (localStorage.getItem("spirit_notify") === "granted") {
    notifyScheduled.value = true;
  }
});
</script>

<style scoped>
.ritual-card {
  border-radius: 24px;
  padding: 20px 22px;
  transition: all 0.5s ease;
  border: 1px solid rgba(0, 0, 0, 0.04);
}

/* 晨间 */
.ritual-card--morning {
  background: linear-gradient(
    135deg,
    rgba(255, 245, 225, 0.8) 0%,
    rgba(255, 235, 210, 0.6) 50%,
    rgba(255, 240, 230, 0.7) 100%
  );
}
/* 午后 */
.ritual-card--afternoon {
  background: linear-gradient(
    135deg,
    rgba(255, 250, 240, 0.8) 0%,
    rgba(255, 245, 230, 0.6) 50%,
    rgba(255, 248, 235, 0.7) 100%
  );
}
/* 夜晚 */
.ritual-card--night {
  background: linear-gradient(
    135deg,
    rgba(240, 240, 255, 0.8) 0%,
    rgba(235, 235, 250, 0.6) 50%,
    rgba(245, 240, 255, 0.7) 100%
  );
}

/* ── 氛围头 ── */
.ritual-atmo {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}
.ritual-emoji {
  font-size: 32px;
  animation: float-emoji 3s ease-in-out infinite;
}
@keyframes float-emoji {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-4px); }
}
.ritual-greeting {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.ritual-hello {
  font-size: 17px;
  font-weight: 700;
  color: #4a3728;
}
.ritual-phase {
  font-size: 12px;
  color: #8b7355;
}

/* ── 签到 ── */
.ritual-checkin {
  text-align: center;
  margin-bottom: 14px;
}
.checkin-btn {
  padding: 14px 32px;
  border-radius: 20px;
  border: none;
  font-size: 15px;
  font-weight: 700;
  cursor: pointer;
  font-family: inherit;
  background: linear-gradient(135deg, #ff9a8b, #ffb8a8);
  color: #fff;
  box-shadow: 0 4px 16px rgba(255, 154, 139, 0.25);
  transition: all 0.3s;
}
.checkin-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(255, 154, 139, 0.35);
}
.checkin-btn--done {
  background: #c4e0c4 !important;
  box-shadow: none !important;
  pointer-events: none;
}
.checkin-streak {
  font-size: 13px;
  color: #8b7355;
  margin: 8px 0 0;
}
.checkin-streak strong {
  color: #ff9a8b;
}

.checked-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 10px 18px;
  border-radius: 16px;
  background: rgba(76, 175, 80, 0.08);
  font-size: 13px;
  color: #6b5744;
  font-weight: 600;
}
.checked-icon {
  font-size: 16px;
}

/* 心情选择器 */
.mood-picker {
  text-align: center;
}
.mood-prompt {
  font-size: 14px; color: #6b5744; margin: 0 0 10px; font-weight: 600;
}
.mood-emojis {
  display: flex; justify-content: center; gap: 8px; flex-wrap: wrap;
}
.mood-btn {
  display: flex; flex-direction: column; align-items: center; gap: 4px;
  padding: 10px 14px; border-radius: 16px; border: 1px solid rgba(0,0,0,0.06);
  background: rgba(255,255,255,0.7); cursor: pointer; font-family: inherit;
  transition: all 0.2s;
}
.mood-btn:hover { border-color: #ff9a8b; background: rgba(255,255,255,0.9); transform: translateY(-2px); }
.mood-emoji { font-size: 24px; }
.mood-word { font-size: 11px; color: #8b7355; font-weight: 600; }

.notify-prompt { text-align: center; margin-top: 10px; }
.notify-btn {
  padding: 8px 18px; border-radius: 14px; border: 1px solid rgba(0,0,0,0.08);
  background: rgba(255,255,255,0.7); font-size: 12px; font-weight: 600;
  color: #6b5744; cursor: pointer; font-family: inherit; transition: all 0.2s;
}
.notify-btn:hover { background: rgba(255,255,255,0.9); border-color: #ff9a8b; }
.notify-done { font-size: 12px; color: #8b7355; }

/* ── 星灵寄语 ── */
.ritual-blessing {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 12px 16px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.5);
  border: 1px solid rgba(0, 0, 0, 0.04);
}
.blessing-symbol {
  font-size: 24px;
  flex-shrink: 0;
}
.blessing-text {
  font-size: 13px;
  color: #5c4a3a;
  line-height: 1.6;
  font-style: italic;
}
</style>
