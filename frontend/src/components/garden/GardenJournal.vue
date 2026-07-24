<template>
  <div class="journal-view">
    <!-- 标题 -->
    <div class="journal-header">
      <h2 class="journal-title">💎 花园日记</h2>
      <p class="journal-desc">记录你和星灵们的每一次对话与成长</p>
    </div>

    <!-- 概览卡片 -->
    <div class="overview-row" v-if="hasActivity">
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
    <div class="journal-empty-hint" v-else>
      <p>🌱 和星灵聊天、完成一次星语者咨询后，这里会慢慢长出你的花园。每一次对话都是一颗种子。</p>
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

    <!-- 日记时间线 -->
    <div class="diary-section" v-if="diaryEntries.length > 0">
      <h3 class="section-subtitle">星灵日记</h3>
      <div class="diary-card-list">
        <div
          v-for="entry in diaryEntries"
          :key="entry.id || entry.created_at"
          class="diary-card"
          :class="{ 'diary-card--editing': editingId === entry.id }"
        >
          <div class="dc-header">
            <span class="dc-date">{{ formatDate(entry) }}</span>
            <span class="dc-mood" v-if="entry.mood_emoji">{{ entry.mood_emoji }}</span>
            <span class="dc-planet" v-if="entry.spirit_planet">
              {{ entry.spirit_planet_label || entry.spirit_planet }}
            </span>
            <div v-if="editingId !== entry.id && entry.id" class="dc-actions">
              <button class="dc-action-btn" title="编辑" aria-label="编辑" @click="startEdit(entry)">✎</button>
              <button class="dc-action-btn dc-action-btn--danger" title="删除" aria-label="删除" @click="confirmDelete(entry)">🗑</button>
            </div>
          </div>

          <p v-if="editingId !== entry.id" class="dc-text">{{ entry.entry_text || entry.text || entry.chat_context || '...' }}</p>
          <textarea
            v-else
            ref="editTextarea"
            class="dc-textarea"
            v-model="editingText"
            rows="5"
            maxlength="500"
            placeholder="写点什么吧..."
            @input="autoResize($event)"
          ></textarea>

          <div v-if="editingId !== entry.id && entry.keywords?.length" class="dc-tags">
            <span
              v-for="(kw, ki) in entry.keywords.slice(0, 4)"
              :key="ki"
              class="dc-tag"
              :style="{ background: tagColors[Number(ki) % tagColors.length] }"
            >
              <span class="dc-tag-emoji">{{ emojiForKw(kw) }}</span>
              <span>{{ kw }}</span>
            </span>
          </div>

          <div v-else class="dc-tags-edit">
            <div class="dc-tags-row">
              <span
                v-for="(kw, ki) in editingKeywords"
                :key="`${kw}-${ki}`"
                class="dc-tag"
                :style="{ background: tagColors[ki % tagColors.length] }"
              >
                <span class="dc-tag-emoji">{{ emojiForKw(kw) }}</span>
                <span>{{ kw }}</span>
                <button class="dc-tag-remove" aria-label="删除关键词" @click="removeKeyword(ki)">×</button>
              </span>
              <span v-if="!editingKeywords.length" class="dc-tags-empty">还没有关键词</span>
            </div>
            <div class="dc-tags-add">
              <input
                v-model="newKeyword"
                class="dc-tags-input"
                placeholder="添加关键词后回车"
                maxlength="12"
                @keydown.enter.prevent="addKeyword"
              />
              <button type="button" class="dc-tags-add-btn" @click="addKeyword">＋</button>
            </div>
          </div>

          <div v-if="editingId === entry.id" class="dc-edit-actions">
            <button class="dc-btn dc-btn--ghost" :disabled="saving" @click="cancelEdit">取消</button>
            <button
              class="dc-btn dc-btn--primary"
              :disabled="saving || !editingText.trim()"
              @click="saveEdit(entry)"
            >{{ saving ? '保存中...' : '保存' }}</button>
          </div>
          <p v-if="editingId === entry.id && editError" class="dc-error">{{ editError }}</p>
        </div>
      </div>
    </div>

    <!-- 删除确认 -->
    <transition name="gj-confirm-fade">
      <div v-if="deletingEntry" class="gj-confirm-mask" @click.self="cancelDelete">
        <div class="gj-confirm-card">
          <div class="gj-confirm-icon">🗑</div>
          <p class="gj-confirm-title">删除这条日记？</p>
          <p class="gj-confirm-desc">删除后无法恢复。</p>
          <div class="gj-confirm-actions">
            <button class="dc-btn dc-btn--ghost" :disabled="deleting" @click="cancelDelete">再想想</button>
            <button class="dc-btn dc-btn--danger" :disabled="deleting" @click="executeDelete">
              {{ deleting ? '删除中...' : '确认删除' }}
            </button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted } from "vue";
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
const diaryEntries = ref<any[]>([]);

async function fetchDiaryEntries() {
  if (!props.activeReportId) return;
  try {
    const res = await apiClient.get(`/spirit-diary/${props.activeReportId}?limit=30`);
    if (res.data?.status === "success") {
      diaryEntries.value = res.data.data?.entries || [];
    }
  } catch {
    diaryEntries.value = [];
  }
}

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
  fetchDiaryEntries();
});

// Activity check: any conversations or diary entries
const hasActivity = computed(() => {
  return stats.value.totalConversations > 0 || diaryEntries.value.length > 0;
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

// ═══════════════════════════════════════
// 日记编辑 & 删除
// ═══════════════════════════════════════

const tagColors = [
  'rgba(242,169,0,0.15)',
  'rgba(155,196,208,0.15)',
  'rgba(123,141,111,0.15)',
  'rgba(232,160,191,0.15)',
];

const KEYWORD_EMOJI: Record<string, string> = {
  "委屈": "😞", "不甘": "😤", "期待": "🥰", "害怕": "😨",
  "勇敢": "💪", "迷茫": "😶", "坚定": "🔥", "温暖": "☀️",
  "孤独": "💔", "渴望": "🌟", "释然": "😌", "困惑": "🤔",
  "感动": "🥹", "疲惫": "😮‍💨", "充实": "✨", "放松": "🌿",
};

function emojiForKw(kw: string): string {
  return KEYWORD_EMOJI[kw] || "🏷";
}

function formatDate(entry: any): string {
  const raw = entry.entry_date || entry.date || entry.created_at || "";
  if (!raw) return "未知日期";
  if (/^\d{4}-\d{2}-\d{2}/.test(raw)) return raw.slice(0, 10);
  return raw;
}

const editingId = ref<string | null>(null);
const editingText = ref("");
const editingKeywords = ref<string[]>([]);
const newKeyword = ref("");
const saving = ref(false);
const editError = ref("");
const editTextarea = ref<HTMLTextAreaElement[] | null>(null);

function startEdit(entry: any) {
  if (!entry.id) {
    editError.value = "该条目暂不支持编辑（缺少 ID）";
    return;
  }
  editError.value = "";
  editingId.value = entry.id;
  editingText.value = entry.entry_text || entry.text || entry.chat_context || "";
  editingKeywords.value = Array.isArray(entry.keywords) ? [...entry.keywords] : [];
  nextTick(() => {
    const ta = Array.isArray(editTextarea.value) ? editTextarea.value[0] : null;
    if (ta) {
      ta.focus();
      autoResize({ target: ta } as any);
    }
  });
}

function cancelEdit() {
  editingId.value = null;
  editingText.value = "";
  editingKeywords.value = [];
  newKeyword.value = "";
  editError.value = "";
}

function addKeyword() {
  const v = newKeyword.value.trim();
  if (!v) return;
  if (editingKeywords.value.includes(v)) { newKeyword.value = ""; return; }
  if (editingKeywords.value.length >= 6) { editError.value = "最多 6 个关键词"; return; }
  editingKeywords.value.push(v);
  newKeyword.value = "";
  editError.value = "";
}

function removeKeyword(idx: number) {
  editingKeywords.value.splice(idx, 1);
}

function autoResize(e: any) {
  const ta = e.target as HTMLTextAreaElement;
  if (!ta) return;
  ta.style.height = "auto";
  ta.style.height = `${ta.scrollHeight}px`;
}

async function saveEdit(entry: any) {
  if (!entry.id) return;
  saving.value = true;
  editError.value = "";
  try {
    const res = await apiClient.patch(`/spirit-diary/${entry.id}`, {
      entry_text: editingText.value.trim(),
      keywords: editingKeywords.value,
    });
    if (res.data?.status === "success") {
      const idx = diaryEntries.value.findIndex((e: any) => e.id === entry.id);
      if (idx >= 0) {
        const arr = [...diaryEntries.value];
        arr[idx] = {
          ...arr[idx],
          entry_text: editingText.value.trim(),
          keywords: [...editingKeywords.value],
          text: editingText.value.trim(),
        };
        diaryEntries.value = arr;
      }
      cancelEdit();
    } else {
      editError.value = res.data?.detail || "保存失败";
    }
  } catch (e: any) {
    editError.value = e?.response?.data?.detail || e?.message || "保存失败";
  } finally {
    saving.value = false;
  }
}

const deletingEntry = ref<any | null>(null);
const deleting = ref(false);

function confirmDelete(entry: any) {
  if (!entry.id) {
    editError.value = "该条目暂不支持删除（缺少 ID）";
    return;
  }
  deletingEntry.value = entry;
}

function cancelDelete() {
  deletingEntry.value = null;
}

async function executeDelete() {
  if (!deletingEntry.value?.id) return;
  deleting.value = true;
  try {
    const res = await apiClient.delete(`/spirit-diary/${deletingEntry.value.id}`);
    if (res.data?.status === "success") {
      diaryEntries.value = diaryEntries.value.filter((e: any) => e.id !== deletingEntry.value.id);
      deletingEntry.value = null;
    } else {
      editError.value = res.data?.detail || "删除失败";
    }
  } catch (e: any) {
    editError.value = e?.response?.data?.detail || e?.message || "删除失败";
  } finally {
    deleting.value = false;
  }
}
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
.journal-empty-hint {
  text-align: center;
  padding: 24px 20px;
  border-radius: 18px;
  background: rgba(255,255,255,0.5);
  border: 1px dashed rgba(0,0,0,0.06);
}
.journal-empty-hint p {
  font-size: 14px;
  color: #8b7355;
  line-height: 1.7;
  margin: 0;
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

/* ── 日记卡片 ── */
.diary-section {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.diary-card-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.diary-card {
  padding: 16px;
  border-radius: 16px;
  background: rgba(255,255,255,0.8);
  border: 1px solid rgba(0,0,0,0.06);
  transition: all 0.2s;
}
.diary-card:hover {
  box-shadow: 0 4px 18px rgba(0,0,0,0.06);
}
.diary-card--editing {
  border-color: rgba(242,169,0,0.4);
  box-shadow: 0 4px 24px rgba(242,169,0,0.12);
}
.dc-header {
  display: flex; align-items: center; gap: 8px; margin-bottom: 8px;
}
.dc-date { font-size: 12px; color: #a89880; font-weight: 500; }
.dc-mood { font-size: 16px; line-height: 1; }
.dc-planet {
  margin-left: auto;
  font-size: 11px; font-weight: 600; color: #8b7355;
  padding: 2px 10px; border-radius: 10px;
  background: rgba(0,0,0,0.03);
}
.dc-actions {
  display: flex; gap: 4px; margin-left: 6px;
}
.dc-action-btn {
  border: none; background: transparent; cursor: pointer;
  width: 24px; height: 24px; border-radius: 8px;
  font-size: 12px; line-height: 1;
  display: inline-flex; align-items: center; justify-content: center;
  color: #8b7355; transition: all 0.15s;
}
.dc-action-btn:hover { background: rgba(0,0,0,0.05); color: #4a3728; }
.dc-action-btn--danger:hover { background: rgba(232,160,191,0.25); color: #c0392b; }

.dc-text {
  font-size: 14px; color: #4a3728; line-height: 1.7;
  margin: 0 0 8px;
  white-space: pre-wrap;
  word-break: break-word;
}
.dc-textarea {
  width: 100%;
  box-sizing: border-box;
  font-size: 14px;
  line-height: 1.7;
  color: #4a3728;
  padding: 10px 12px;
  border-radius: 12px;
  border: 1px solid rgba(0,0,0,0.1);
  background: rgba(255,255,255,0.9);
  resize: none;
  outline: none;
  font-family: inherit;
  margin-bottom: 8px;
}
.dc-textarea:focus { border-color: rgba(242,169,0,0.5); }

.dc-tags {
  display: flex; flex-wrap: wrap; gap: 6px;
}
.dc-tag {
  display: inline-flex; align-items: center; gap: 4px;
  font-size: 11px; font-weight: 500; color: #5c4a3a;
  padding: 3px 10px; border-radius: 8px;
  letter-spacing: 0.3px;
}
.dc-tag-emoji { font-size: 12px; }

.dc-tags-edit { display: flex; flex-direction: column; gap: 8px; }
.dc-tags-row { display: flex; flex-wrap: wrap; gap: 6px; min-height: 22px; }
.dc-tag-remove {
  border: none; background: transparent; cursor: pointer;
  color: #8b7355; font-size: 13px; line-height: 1;
  padding: 0 2px; border-radius: 4px; margin-left: 2px;
}
.dc-tag-remove:hover { color: #c0392b; }
.dc-tags-empty { font-size: 12px; color: #a89880; align-self: center; }
.dc-tags-add { display: flex; gap: 6px; }
.dc-tags-input {
  flex: 1; font-size: 12px;
  padding: 6px 10px; border-radius: 10px;
  border: 1px solid rgba(0,0,0,0.08);
  background: rgba(255,255,255,0.7);
  outline: none; color: #4a3728;
}
.dc-tags-input:focus { border-color: rgba(242,169,0,0.4); }
.dc-tags-add-btn {
  border: none; background: rgba(242,169,0,0.15); color: #b67c00;
  font-size: 16px; width: 30px; border-radius: 10px; cursor: pointer;
}
.dc-tags-add-btn:hover { background: rgba(242,169,0,0.25); }

.dc-edit-actions {
  display: flex; justify-content: flex-end; gap: 8px;
  margin-top: 10px;
}
.dc-btn {
  font-size: 13px; font-weight: 600;
  padding: 7px 16px; border-radius: 12px;
  border: none; cursor: pointer; transition: all 0.15s;
}
.dc-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.dc-btn--ghost { background: rgba(0,0,0,0.04); color: #8b7355; }
.dc-btn--ghost:hover:not(:disabled) { background: rgba(0,0,0,0.08); }
.dc-btn--primary {
  background: linear-gradient(135deg, #f2a900, #ff9a8b);
  color: #fff; box-shadow: 0 2px 8px rgba(242,169,0,0.25);
}
.dc-btn--primary:hover:not(:disabled) { transform: translateY(-1px); }
.dc-btn--danger {
  background: linear-gradient(135deg, #e8a0bf, #c0392b);
  color: #fff; box-shadow: 0 2px 8px rgba(192,57,43,0.25);
}
.dc-btn--danger:hover:not(:disabled) { transform: translateY(-1px); }
.dc-error { font-size: 12px; color: #c0392b; margin: 8px 0 0; }

/* 删除确认弹窗 */
.gj-confirm-mask {
  position: fixed; inset: 0; z-index: 300;
  background: rgba(0,0,0,0.4);
  display: flex; align-items: center; justify-content: center;
  padding: 20px;
}
.gj-confirm-fade-enter-active, .gj-confirm-fade-leave-active { transition: opacity 0.2s; }
.gj-confirm-fade-enter-from, .gj-confirm-fade-leave-to { opacity: 0; }
.gj-confirm-card {
  background: #fff;
  border-radius: 20px;
  padding: 28px 24px 22px;
  max-width: 320px; width: 100%;
  text-align: center;
  box-shadow: 0 10px 40px rgba(0,0,0,0.18);
}
.gj-confirm-icon { font-size: 36px; margin-bottom: 8px; }
.gj-confirm-title { font-size: 17px; font-weight: 700; color: #4a3728; margin: 0 0 6px; }
.gj-confirm-desc { font-size: 13px; color: #8b7355; margin: 0 0 20px; line-height: 1.5; }
.gj-confirm-actions { display: flex; gap: 10px; justify-content: center; }
</style>
