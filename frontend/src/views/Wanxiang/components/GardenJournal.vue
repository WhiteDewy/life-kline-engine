<template>
  <div class="journal-view">
    <!-- 标题 -->
    <div class="journal-header">
      <h2 class="journal-title">💎 花园日记</h2>
      <p class="journal-desc">记录你和星灵们的每一次对话与成长</p>
    </div>

    <!-- 概览卡片 -->
    <div class="overview-row">
      <div class="overview-card">
        <span class="ov-number">{{ stats.totalConversations }}</span>
        <span class="ov-label">次对话</span>
      </div>
      <div class="overview-card">
        <span class="ov-number">{{ stats.streakDays }}</span>
        <span class="ov-label">连续天数</span>
      </div>
      <div class="overview-card">
        <span class="ov-number">{{ stats.milestonesCount }}</span>
        <span class="ov-label">里程碑</span>
      </div>
    </div>

    <!-- 最亲密星灵 -->
    <div class="closest-spirit" v-if="closestSpirit">
      <span class="closest-label">你最亲密的星灵</span>
      <div class="closest-card" :style="{ '--c-color': closestSpirit.color }">
        <SpiritAvatar v-if="closestSpirit" :planet="closestSpirit.planet" :symbol="closestSpirit.symbol" :name="closestSpirit.name" :color="closestSpirit.color" size="lg" />
        <div class="closest-info">
          <span class="closest-name">{{ closestSpirit.name }}</span>
          <span class="closest-sub">最常聊天的星灵</span>
        </div>
        <span class="closest-hearts">💛</span>
      </div>
    </div>

    <!-- 星灵亲密度 -->
    <div class="affinity-section">
      <h3 class="section-subtitle">星灵亲密度</h3>
      <div class="affinity-list">
        <div
          v-for="a in affinityBars"
          :key="a.planet"
          class="affinity-row"
          @click="selectedSpirit = a.planet"
        >
          <SpiritAvatar :planet="a.planet" :symbol="a.symbol" :name="a.name" :color="a.color" size="sm" />
          <span class="aff-name">{{ a.name }}</span>
          <div class="aff-track">
            <div
              class="aff-fill"
              :style="{
                width: a.affinity * 10 + '%',
                background: a.color,
              }"
            ></div>
          </div>
          <span class="aff-score" :style="{ color: a.color }">
            {{ a.affinity.toFixed(1) }}
          </span>
        </div>
      </div>
    </div>

    <!-- 里程碑时间线 -->
    <div class="milestones-section">
      <h3 class="section-subtitle">成长里程碑</h3>
      <div class="milestone-list" v-if="milestones.length > 0">
        <div
          v-for="(m, i) in milestones"
          :key="i"
          class="milestone-item"
          :class="{ 'milestone-item--latest': i === 0 }"
        >
          <div class="ms-dot" :class="{ 'ms-dot--glow': i === 0 }"></div>
          <div class="ms-line" v-if="i < milestones.length - 1"></div>
          <div class="ms-content">
            <span class="ms-date">{{ m.date }}</span>
            <span class="ms-title">{{ m.title }}</span>
            <span class="ms-desc">{{ m.description }}</span>
          </div>
        </div>
      </div>
      <div class="milestone-empty" v-else>
        <p>🌱 你的花园日记才刚刚开始——多和星灵们聊天，这里会慢慢填满回忆。</p>
      </div>
    </div>

    <!-- 对话历史预览 -->
    <div class="history-section" v-if="recentChats.length > 0">
      <h3 class="section-subtitle">最近对话</h3>
      <div class="chat-preview-list">
        <div
          v-for="(chat, i) in recentChats"
          :key="i"
          class="chat-preview"
        >
          <SpiritAvatar :symbol="chat.symbol" :name="chat.spiritName" size="sm" />
          <div class="cp-body">
            <span class="cp-name">{{ chat.spiritName }}</span>
            <span class="cp-text">"{{ chat.snippet }}"</span>
          </div>
          <span class="cp-time">{{ chat.timeAgo }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { apiClient } from "@/config/api";
import SpiritAvatar from "./SpiritAvatar.vue";
import type { PlanetCharacterProfilesData, GrowthData } from "@/utils/types";

const props = defineProps<{
  planetProfiles: PlanetCharacterProfilesData | null;
  activeReportId: string;
}>();

const selectedSpirit = ref("");
const growthData = ref<GrowthData | null>(null);
const apiLoaded = ref(false);

// ── Mock 成长数据（localStorage 存储） ──
interface MockChat {
  planet: string;
  timestamp: number;
  snippet: string;
}

const mockChats = ref<MockChat[]>([]);

function loadMockData() {
  const key = `spirit_garden_${props.activeReportId}`;
  try {
    const raw = localStorage.getItem(key);
    if (raw) {
      const data = JSON.parse(raw);
      mockChats.value = data.chats || [];
    }
  } catch {
    mockChats.value = [];
  }
}

async function fetchGrowthData() {
  if (!props.activeReportId) return;
  try {
    const res = await apiClient.get(`/characters/${props.activeReportId}/growth`);
    if (res.data?.status === "success") {
      growthData.value = res.data.data;
      apiLoaded.value = true;
    }
  } catch {
    apiLoaded.value = false;
  }
}

onMounted(() => {
  loadMockData();
  fetchGrowthData();
});

// ── 统计 ──
const stats = computed(() => {
  // 优先使用 API 数据
  if (growthData.value?.summary) {
    const s = growthData.value.summary;
    return {
      totalConversations: s.total_conversations || mockChats.value.length,
      streakDays: s.streak_days || 0,
      milestonesCount: s.milestones_achieved || 0,
    };
  }

  // Fallback: localStorage
  const total = mockChats.value.length;

  // 连续天数
  let streak = 0;
  const dates = new Set(
    mockChats.value.map((c) => {
      const d = new Date(c.timestamp);
      return `${d.getFullYear()}-${d.getMonth() + 1}-${d.getDate()}`;
    })
  );
  let check = new Date();
  for (let i = 0; i < 365; i++) {
    const key = `${check.getFullYear()}-${check.getMonth() + 1}-${check.getDate()}`;
    if (dates.has(key)) {
      streak++;
      check.setDate(check.getDate() - 1);
    } else if (i === 0) {
      check.setDate(check.getDate() - 1); // 今天没对话，从昨天开始算
    } else {
      break;
    }
  }

  // 里程碑数
  let milestonesCount = 0;
  if (total >= 1) milestonesCount++;
  if (total >= 10) milestonesCount++;
  if (total >= 50) milestonesCount++;
  if (streak >= 7) milestonesCount++;

  return {
    totalConversations: total,
    streakDays: streak,
    milestonesCount,
  };
});

// ── 最亲密星灵 ──
const closestSpirit = computed(() => {
  if (!props.planetProfiles?.planet_characters) return null;
  const profiles = props.planetProfiles.planet_characters;

  const counts: Record<string, number> = {};
  mockChats.value.forEach((c) => {
    counts[c.planet] = (counts[c.planet] || 0) + 1;
  });

  let maxPlanet = Object.keys(profiles)[0] || "SUN";
  let maxCount = 0;
  for (const [p, c] of Object.entries(counts)) {
    if (c > maxCount) {
      maxCount = c;
      maxPlanet = p;
    }
  }

  const p = profiles[maxPlanet];
  if (!p && maxCount === 0) {
    const sun = profiles["SUN"];
    return sun
      ? {
          planet: "SUN",
          symbol: sun.persona?.symbol || "☉",
          name: sun.persona?.name_zh || "太阳",
          color: sun.persona?.visual_color || "#F2A900",
        }
      : null;
  }

  return p
    ? {
        planet: maxPlanet,
        symbol: p.persona?.symbol || "●",
        name: p.persona?.name_zh || "",
        color: p.persona?.visual_color || "#999",
      }
    : null;
});

// ── 亲密度条 ──
const affinityBars = computed(() => {
  if (!props.planetProfiles?.planet_characters) return [];
  const profiles = props.planetProfiles.planet_characters;
  const counts: Record<string, number> = {};
  mockChats.value.forEach((c) => {
    counts[c.planet] = (counts[c.planet] || 0) + 1;
  });

  const order = ["SUN", "MOON", "MERCURY", "VENUS", "MARS", "JUPITER", "SATURN"];
  return order.map((key) => {
    const p = profiles[key];
    if (!p) return null;
    const count = counts[key] || 0;
    return {
      planet: key,
      symbol: p.persona?.symbol || "●",
      name: p.persona?.name_zh || key,
      color: p.persona?.visual_color || "#999",
      affinity: Math.min(10, count * 0.5 + 0.5), // 0.5-10 scale
    };
  }).filter(Boolean) as Array<{
    planet: string; symbol: string; name: string; color: string; affinity: number;
  }>;
});

// ── 里程碑 ──
const milestones = computed(() => {
  const result: Array<{
    date: string;
    title: string;
    description: string;
  }> = [];

  const total = stats.value.totalConversations;
  const streak = stats.value.streakDays;
  const closest = closestSpirit.value;

  if (total >= 1) {
    result.push({
      date: "最近",
      title: "🎉 第一次对话",
      description: closest
        ? `你和${closest.name}完成了第一次对话——花园之旅正式开始。`
        : "你开始了第一次星灵对话。",
    });
  }
  if (total >= 10 && closest) {
    result.push({
      date: "最近",
      title: "⭐ 十次对话",
      description: `你和${closest.name}已经聊了10次——默契正在形成。`,
    });
  }
  if (streak >= 3) {
    result.push({
      date: "最近",
      title: "🔥 连续三天",
      description: `你已经连续${streak}天来到花园——星灵们每天都想见到你。`,
    });
  }
  if (streak >= 7) {
    result.push({
      date: "最近",
      title: "🌟 七日之约",
      description: "连续7天不缺席——你对内在探索的坚持，星灵们都看在眼里。",
    });
  }

  return result;
});

// ── 最近对话 ──
const recentChats = computed(() => {
  if (!props.planetProfiles?.planet_characters) return [];
  const profiles = props.planetProfiles.planet_characters;

  return mockChats.value
    .slice(-5)
    .reverse()
    .map((c) => {
      const p = profiles[c.planet];
      const diff = Date.now() - c.timestamp;
      const mins = Math.floor(diff / 60000);
      const hours = Math.floor(diff / 3600000);
      const days = Math.floor(diff / 86400000);

      return {
        symbol: p?.persona?.symbol || "●",
        spiritName: p?.persona?.name_zh || c.planet,
        snippet: c.snippet?.slice(0, 40) || "...",
        timeAgo: mins < 1
          ? "刚刚"
          : mins < 60
          ? `${mins}分钟前`
          : hours < 24
          ? `${hours}小时前`
          : `${days}天前`,
      };
    });
});
</script>

<style scoped>
.journal-view {
  display: flex;
  flex-direction: column;
  gap: 24px;
  padding-bottom: 100px;
}

/* ── 头部 ── */
.journal-header {
  text-align: center;
}
.journal-title {
  font-size: 24px;
  font-weight: 700;
  color: #4a3728;
  margin: 0 0 6px;
}
.journal-desc {
  font-size: 13px;
  color: #8b7355;
  margin: 0;
}

/* ── 概览 ── */
.overview-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}
.overview-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 18px 12px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.75);
  border: 1px solid rgba(0, 0, 0, 0.04);
}
.ov-number {
  font-size: 28px;
  font-weight: 800;
  color: #4a3728;
}
.ov-label {
  font-size: 12px;
  color: #8b7355;
}

/* ── 最亲密星灵 ── */
.closest-spirit {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.closest-label {
  font-size: 13px;
  color: #8b7355;
  font-weight: 600;
}
.closest-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.8);
  border: 2px solid var(--c-color);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}
.closest-symbol {
  font-size: 32px;
}
.closest-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.closest-name {
  font-size: 17px;
  font-weight: 700;
  color: #4a3728;
}
.closest-sub {
  font-size: 12px;
  color: #8b7355;
}
.closest-hearts {
  font-size: 24px;
}

/* ── 亲密度 ── */
.section-subtitle {
  font-size: 15px;
  font-weight: 700;
  color: #4a3728;
  margin: 0;
}
.affinity-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.affinity-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.6);
  cursor: pointer;
  transition: all 0.2s;
}
.affinity-row:hover {
  background: rgba(255, 255, 255, 0.85);
}
.aff-symbol {
  font-size: 20px;
  width: 30px;
  text-align: center;
  flex-shrink: 0;
}
.aff-name {
  font-size: 13px;
  font-weight: 600;
  color: #4a3728;
  min-width: 36px;
  flex-shrink: 0;
}
.aff-track {
  flex: 1;
  height: 8px;
  border-radius: 4px;
  background: rgba(0, 0, 0, 0.05);
  overflow: hidden;
}
.aff-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 1s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}
.aff-score {
  font-size: 13px;
  font-weight: 700;
  min-width: 32px;
  text-align: right;
  flex-shrink: 0;
}

/* ── 里程碑 ── */
.milestone-list {
  display: flex;
  flex-direction: column;
  position: relative;
  padding-left: 24px;
}
.milestone-item {
  position: relative;
  padding: 12px 0 12px 20px;
}
.milestone-item--latest {
  background: rgba(255, 154, 139, 0.04);
  border-radius: 14px;
}
.ms-dot {
  position: absolute;
  left: -18px;
  top: 18px;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #c4b5a5;
  border: 2px solid rgba(255, 255, 255, 0.8);
}
.ms-dot--glow {
  background: #ff9a8b;
  box-shadow: 0 0 8px rgba(255, 154, 139, 0.4);
}
.ms-line {
  position: absolute;
  left: -13px;
  top: 34px;
  bottom: -4px;
  width: 2px;
  background: rgba(0, 0, 0, 0.06);
}
.ms-content {
  display: flex;
  flex-direction: column;
  gap: 3px;
}
.ms-date {
  font-size: 11px;
  color: #a89880;
}
.ms-title {
  font-size: 14px;
  font-weight: 600;
  color: #4a3728;
}
.ms-desc {
  font-size: 12px;
  color: #8b7355;
  line-height: 1.5;
}
.milestone-empty {
  text-align: center;
  padding: 30px 20px;
  color: #a89880;
  font-size: 14px;
  line-height: 1.6;
}

/* ── 最近对话 ── */
.history-section {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.chat-preview-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.chat-preview {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.6);
  transition: all 0.2s;
}
.chat-preview:hover {
  background: rgba(255, 255, 255, 0.85);
}
.cp-symbol {
  font-size: 20px;
  width: 30px;
  text-align: center;
  flex-shrink: 0;
}
.cp-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}
.cp-name {
  font-size: 13px;
  font-weight: 600;
  color: #4a3728;
}
.cp-text {
  font-size: 12px;
  color: #8b7355;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.cp-time {
  font-size: 11px;
  color: #c4b5a5;
  flex-shrink: 0;
}
</style>
