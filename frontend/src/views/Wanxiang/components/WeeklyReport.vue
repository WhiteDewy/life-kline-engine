<template>
  <div class="wr-card">
    <div class="wr-header">
      <span class="wr-icon">📊</span>
      <span class="wr-title">本周总结</span>
      <span class="wr-date">{{ weekRange }}</span>
    </div>

    <div class="wr-stats">
      <div class="wr-stat">
        <span class="wr-stat-num">{{ weeklyMoods.length }}</span>
        <span class="wr-stat-label">签到天数</span>
      </div>
      <div class="wr-stat">
        <span class="wr-stat-num">{{ weeklyChats }}</span>
        <span class="wr-stat-label">对话次数</span>
      </div>
      <div class="wr-stat">
        <span class="wr-stat-num">{{ topMood }}</span>
        <span class="wr-stat-label">最常心情</span>
      </div>
    </div>

    <!-- 心情分布条 -->
    <div class="wr-mood-bar" v-if="weeklyMoods.length > 0">
      <p class="wr-mood-label">本周心情</p>
      <div class="mood-dots">
        <span v-for="(m, i) in weeklyMoods" :key="i" :title="m.date" class="mood-dot">{{ m.mood }}</span>
      </div>
    </div>

    <!-- 寄语 -->
    <p class="wr-message">{{ weeklyMessage }}</p>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{
  planetProfiles: any;
  activeReportId: string;
}>();

// 本周日期范围
const weekRange = computed(() => {
  const now = new Date();
  const dayOfWeek = now.getDay() || 7;
  const monday = new Date(now);
  monday.setDate(now.getDate() - dayOfWeek + 1);
  const sunday = new Date(monday);
  sunday.setDate(monday.getDate() + 6);
  const fmt = (d: Date) => `${d.getMonth() + 1}/${d.getDate()}`;
  return `${fmt(monday)} - ${fmt(sunday)}`;
});

// 本周心情数据
const weeklyMoods = computed(() => {
  try {
    const history = JSON.parse(localStorage.getItem("spirit_mood_history") || "[]");
    const now = new Date();
    const dayOfWeek = now.getDay() || 7;
    const monday = new Date(now);
    monday.setDate(now.getDate() - dayOfWeek + 1);
    monday.setHours(0, 0, 0, 0);
    return history.filter((h: any) => new Date(h.date) >= monday);
  } catch { return []; }
});

// 本周对话数
const weeklyChats = computed(() => {
  try {
    const key = `spirit_garden_${props.activeReportId}`;
    const raw = localStorage.getItem(key);
    if (!raw) return 0;
    const data = JSON.parse(raw);
    const chats = data.chats || [];
    const now = new Date();
    const dayOfWeek = now.getDay() || 7;
    const monday = new Date(now);
    monday.setDate(now.getDate() - dayOfWeek + 1);
    monday.setHours(0, 0, 0, 0);
    return chats.filter((c: any) => c.timestamp >= monday.getTime()).length;
  } catch { return 0; }
});

// 最常心情
const topMood = computed(() => {
  const moods = weeklyMoods.value;
  if (!moods.length) return "—";
  const counts: Record<string, number> = {};
  moods.forEach((m: any) => { counts[m.mood] = (counts[m.mood] || 0) + 1; });
  return Object.entries(counts).sort((a, b) => b[1] - a[1])[0]?.[0] ?? "—";
});

// 寄语
const weeklyMessage = computed(() => {
  const total = weeklyMoods.value.length + weeklyChats.value;
  if (total === 0) return "这周还没开始互动——去花园里坐坐吧，星灵们在等你 🌱";
  if (total < 3) return "这一周刚起了个头。万事不用急，星灵们一直在 🌿";
  if (total < 7) return "你和星灵们保持着温柔的节奏。这种细水长流的感觉，就很好 ✨";
  return "这一周你和星灵们有很多交流。每一段对话，都是你对自己的温柔探索 💫";
});
</script>

<style scoped>
.wr-card {
  padding: 20px; border-radius: 22px;
  background: rgba(255,255,255,0.7); border: 1px solid rgba(0,0,0,0.04);
}
.wr-header {
  display: flex; align-items: center; gap: 8px; margin-bottom: 14px; flex-wrap: wrap;
}
.wr-icon { font-size: 18px; }
.wr-title { font-size: 15px; font-weight: 700; color: #4a3728; }
.wr-date { font-size: 12px; color: #a89880; margin-left: auto; }

.wr-stats {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 14px;
}
.wr-stat {
  display: flex; flex-direction: column; align-items: center; gap: 3px;
  padding: 14px 10px; border-radius: 16px; background: rgba(0,0,0,0.02);
}
.wr-stat-num { font-size: 22px; font-weight: 800; color: #4a3728; }
.wr-stat-label { font-size: 11px; color: #8b7355; }

.wr-mood-bar { margin-bottom: 12px; }
.wr-mood-label { font-size: 12px; color: #8b7355; margin: 0 0 6px; font-weight: 600; }
.mood-dots { display: flex; gap: 4px; flex-wrap: wrap; }
.mood-dot { font-size: 16px; }

.wr-message {
  font-size: 13px; color: #6b5744; line-height: 1.6; margin: 0;
  padding: 10px 14px; border-radius: 14px; background: rgba(255,154,139,0.05);
}
</style>
