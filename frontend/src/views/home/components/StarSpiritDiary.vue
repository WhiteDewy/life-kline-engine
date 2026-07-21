<template>
  <transition name="diary-slide">
    <div v-if="visible" class="diary-screen">
      <button class="dismiss-bar" @click="$emit('close')">
        <span class="dismiss-line"></span>
      </button>

      <div class="diary-body">
        <h2 class="diary-title">📖 星灵日记</h2>

        <!-- 加载态 -->
        <div v-if="loading" class="diary-loading">
          <div class="loading-spinner">
            <span v-for="i in 6" :key="i" class="loading-dot"
              :style="{ animationDelay: i * 0.15 + 's' }"
            ></span>
          </div>
          <p class="loading-text">正在读取星灵记忆...</p>
        </div>

        <!-- 空态 -->
        <div v-else-if="displayEntries.length === 0" class="diary-empty">
          <div class="empty-icon">✨</div>
          <p class="empty-title">还没有日记</p>
          <p class="empty-desc">去和星灵聊聊吧</p>
        </div>

        <!-- 条目列表 -->
        <div v-else class="diary-list">
          <div
            v-for="(entry, idx) in displayEntries"
            :key="idx"
            class="diary-entry"
          >
            <div class="entry-header">
              <span class="entry-date">{{ entry.date || entry.created_at || '未知日期' }}</span>
              <span class="entry-mood" v-if="entry.mood_emoji">{{ entry.mood_emoji }}</span>
              <span class="entry-planet" v-if="entry.spirit_planet">
                {{ entry.spirit_planet_label || entry.spirit_planet }}
              </span>
            </div>

            <p class="entry-text">{{ entry.chat_context || entry.text || '...' }}</p>

            <div class="entry-tags" v-if="entry.keywords?.length">
              <span
                v-for="(kw, ki) in entry.keywords.slice(0, 4)"
                :key="ki"
                class="entry-tag"
                :style="{ background: tagColors[ki % tagColors.length] }"
              >
                {{ kw }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{
  visible: boolean
  entries: any[]
  loading: boolean
}>()

defineEmits<{
  close: []
}>()

const tagColors = [
  'rgba(242,169,0,0.15)',
  'rgba(155,196,208,0.15)',
  'rgba(123,141,111,0.15)',
  'rgba(232,160,191,0.15)',
];

const MOCK_ENTRIES = [
  {
    date: '2026-07-19',
    mood_emoji: '🌞',
    spirit_planet: 'SUN',
    spirit_planet_label: '太阳',
    chat_context: '今天感受到了强烈的创作冲动，太阳的能量让我充满自信。决定开始写一本关于占星与自我成长的书。',
    keywords: ['创造力', '自信', '写作'],
  },
  {
    date: '2026-07-18',
    mood_emoji: '🌙',
    spirit_planet: 'MOON',
    spirit_planet_label: '月亮',
    chat_context: '晚上情绪有些起伏，和月亮星灵聊了聊，明白了这种敏感是我感知世界的礼物。',
    keywords: ['情绪', '敏感', '接纳'],
  },
  {
    date: '2026-07-17',
    mood_emoji: '💫',
    spirit_planet: 'MERCURY',
    spirit_planet_label: '水星',
    chat_context: '今天和同事的沟通格外顺畅，水星给了我清晰的表达力。下午的会议提案一次通过！',
    keywords: ['沟通', '表达', '工作'],
  },
];

const displayEntries = computed(() => {
  if (props.entries && props.entries.length > 0) return props.entries;
  // 开发阶段显示 mock 数据
  return MOCK_ENTRIES;
});
</script>

<style scoped>
.diary-screen {
  position: fixed; inset: 0; z-index: 200;
  background: rgba(255, 255, 255, 0.97);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  display: flex; flex-direction: column;
  overflow-y: auto;
}

.diary-screen::-webkit-scrollbar { width: 4px; }
.diary-screen::-webkit-scrollbar-thumb { background: rgba(0,0,0,0.1); border-radius: 2px; }

.diary-slide-enter-active { transition: all 0.45s cubic-bezier(0.32, 0.02, 0, 1); }
.diary-slide-leave-active { transition: all 0.35s cubic-bezier(0.32, 0.02, 0, 1); }
.diary-slide-enter-from { transform: translateY(100%); }
.diary-slide-leave-to { transform: translateY(100%); }

.dismiss-bar {
  display: flex; justify-content: center; padding: 12px 0 8px;
  border: none; background: transparent; cursor: pointer; flex-shrink: 0;
}
.dismiss-line {
  display: block; width: 36px; height: 4px; border-radius: 2px;
  background: rgba(0, 0, 0, 0.15); transition: background 0.2s;
}
.dismiss-bar:hover .dismiss-line { background: rgba(0, 0, 0, 0.3); }

.diary-body {
  padding: 0 20px 40px;
  padding-bottom: calc(40px + env(safe-area-inset-bottom, 0px));
  max-width: 520px; width: 100%; margin: 0 auto;
}

.diary-title {
  font-size: 22px; font-weight: 700; color: #4a3728;
  margin: 0 0 24px; text-align: center;
}

/* ── 加载态 ── */
.diary-loading {
  text-align: center; padding: 60px 0;
}
.loading-spinner {
  display: flex; justify-content: center; gap: 8px; margin-bottom: 16px;
}
.loading-dot {
  width: 8px; height: 8px; border-radius: 50%;
  background: linear-gradient(135deg, #ff9a8b, #f2a900);
  animation: dot-bounce 1.2s ease-in-out infinite;
}
@keyframes dot-bounce {
  0%,100%{transform:translateY(0);opacity:0.4}
  50%{transform:translateY(-12px);opacity:1}
}
.loading-text {
  font-size: 14px; color: #8b7355; margin: 0;
}

/* ── 空态 ── */
.diary-empty {
  text-align: center; padding: 80px 0;
}
.empty-icon {
  font-size: 48px; margin-bottom: 16px;
  animation: float 3s ease-in-out infinite;
}
@keyframes float {
  0%,100%{transform:translateY(0)}
  50%{transform:translateY(-8px)}
}
.empty-title {
  font-size: 18px; font-weight: 700; color: #4a3728; margin: 0 0 6px;
}
.empty-desc {
  font-size: 14px; color: #8b7355; margin: 0;
}

/* ── 条目列表 ── */
.diary-list {
  display: flex; flex-direction: column; gap: 14px;
}

.diary-entry {
  padding: 18px;
  border-radius: 18px;
  background: rgba(255,255,255,0.8);
  border: 1px solid rgba(0,0,0,0.06);
  box-shadow: 0 2px 12px rgba(0,0,0,0.04);
  transition: all 0.2s;
}
.diary-entry:hover {
  box-shadow: 0 4px 20px rgba(0,0,0,0.06);
  transform: translateY(-1px);
}

.entry-header {
  display: flex; align-items: center; gap: 8px; margin-bottom: 10px;
}
.entry-date {
  font-size: 12px; color: #a89880; font-weight: 500;
}
.entry-mood {
  font-size: 16px; line-height: 1;
}
.entry-planet {
  margin-left: auto;
  font-size: 11px; font-weight: 600; color: #8b7355;
  padding: 2px 10px; border-radius: 10px;
  background: rgba(0,0,0,0.03);
}

.entry-text {
  font-size: 14px; color: #4a3728; line-height: 1.6;
  margin: 0 0 10px;
}

.entry-tags {
  display: flex; flex-wrap: wrap; gap: 6px;
}
.entry-tag {
  font-size: 11px; font-weight: 500; color: #5c4a3a;
  padding: 3px 10px; border-radius: 8px;
  letter-spacing: 0.3px;
}

@media (max-width: 400px) {
  .diary-body { padding: 0 16px 32px; }
  .diary-entry { padding: 14px; }
}
</style>
