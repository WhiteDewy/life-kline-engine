<template>
  <div class="diary-page">
    <!-- 顶部导航 -->
    <header class="diary-header">
      <button class="diary-back" @click="goBack" aria-label="返回">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M19 12H5M12 19l-7-7 7-7" />
        </svg>
      </button>
      <h1 class="diary-header__title">星灵日记</h1>
      <button class="diary-add" @click="startNewEntry" aria-label="写日记">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="12" y1="5" x2="12" y2="19" />
          <line x1="5" y1="12" x2="19" y2="12" />
        </svg>
      </button>
    </header>

    <!-- 加载态 -->
    <div v-if="loading" class="diary-loading">
      <div class="loading-spinner">
        <span v-for="i in 6" :key="i" class="loading-dot" :style="{ animationDelay: i * 0.15 + 's' }"></span>
      </div>
      <p class="loading-text">正在读取星灵记忆...</p>
    </div>

    <!-- 空态 -->
    <div v-else-if="displayEntries.length === 0" class="diary-empty">
      <div class="empty-icon">✨</div>
      <p class="empty-title">还没有日记</p>
      <p class="empty-desc">去和星灵聊聊吧，每一次对话都会成为一颗星星。</p>
      <AppButton size="md" @click="goChat">和星灵聊聊</AppButton>
    </div>

    <!-- 日记时间线 -->
    <div v-else class="diary-timeline">
      <div v-for="entry in displayEntries" :key="entry.id || entry.created_at" class="timeline-item">
        <div class="timeline-marker">
          <span class="timeline-dot" />
          <span class="timeline-date">{{ formatDate(entry) }}</span>
        </div>

        <AppCard class="diary-card" :hover="false">
          <div class="diary-card__header">
            <div class="diary-card__spirit">
              <SpiritAvatar :planet="entry.spirit_planet" :name="entry.spirit_planet_label || entry.spirit_planet" size="sm" />
              <span class="diary-card__spirit-name">{{ entry.spirit_planet_label || entry.spirit_planet }}</span>
            </div>
            <div class="diary-card__mood" v-if="entry.mood_emoji">{{ entry.mood_emoji }}</div>
            <div v-if="editingId !== entry.id && entry.id" class="entry-actions">
              <button class="entry-action-btn" title="编辑" aria-label="编辑日记" @click="startEdit(entry)">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                  <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
                </svg>
              </button>
              <button class="entry-action-btn entry-action-btn--danger" title="删除" aria-label="删除日记" @click="confirmDelete(entry)">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="3 6 5 6 21 6" />
                  <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                </svg>
              </button>
            </div>
          </div>

          <!-- 查看态 -->
          <div v-if="editingId !== entry.id">
            <p class="diary-card__text">{{ entry.entry_text || entry.text || entry.chat_context || '...' }}</p>
            <div v-if="entry.keywords?.length" class="entry-tags">
              <span v-for="(kw, ki) in entry.keywords.slice(0, 4)" :key="ki" class="entry-tag" :style="{ background: tagColors[Number(ki) % tagColors.length] }">
                <span class="entry-tag-emoji">{{ emojiForKw(kw) }}</span>
                <span class="entry-tag-text">{{ kw }}</span>
              </span>
            </div>
          </div>

          <!-- 编辑态 -->
          <div v-else class="diary-card__edit">
            <textarea
              ref="editTextarea"
              v-model="editingText"
              class="entry-textarea"
              rows="5"
              maxlength="500"
              placeholder="写点什么吧..."
              @input="autoResize($event)"
            />

            <div class="entry-tags-edit">
              <div class="entry-tags-edit-row">
                <span v-for="(kw, ki) in editingKeywords" :key="`${kw}-${ki}`" class="entry-tag entry-tag--editable" :style="{ background: tagColors[Number(ki) % tagColors.length] }">
                  <span class="entry-tag-emoji">{{ emojiForKw(kw) }}</span>
                  <span class="entry-tag-text">{{ kw }}</span>
                  <button type="button" class="entry-tag-remove" aria-label="删除关键词" @click="removeKeyword(ki)">×</button>
                </span>
                <span v-if="!editingKeywords.length" class="entry-tags-empty">还没有关键词</span>
              </div>
              <div class="entry-tags-add">
                <input v-model="newKeyword" class="entry-tags-input" placeholder="添加关键词后回车" maxlength="12" @keydown.enter.prevent="addKeyword" />
                <button type="button" class="entry-tags-add-btn" @click="addKeyword">＋</button>
              </div>
            </div>

            <div class="entry-edit-actions">
              <AppButton variant="ghost" size="sm" :disabled="saving" @click="cancelEdit">取消</AppButton>
              <AppButton variant="primary" size="sm" :disabled="saving || !editingText.trim()" @click="saveEdit(entry)">
                {{ saving ? '保存中...' : '保存' }}
              </AppButton>
            </div>
            <p v-if="editError" class="entry-edit-error">{{ editError }}</p>
          </div>
        </AppCard>
      </div>
    </div>

    <!-- 删除确认弹窗 -->
    <transition name="confirm-fade">
      <div v-if="deletingEntry" class="confirm-mask" @click.self="cancelDelete">
        <AppCard class="confirm-card">
          <div class="confirm-icon">🗑</div>
          <p class="confirm-title">删除这条日记？</p>
          <p class="confirm-desc">删除后无法恢复，星灵也会记得你说的话。</p>
          <div class="confirm-actions">
            <AppButton variant="ghost" size="sm" :disabled="deleting" @click="cancelDelete">再想想</AppButton>
            <AppButton variant="primary" size="sm" :disabled="deleting" @click="executeDelete">
              {{ deleting ? '删除中...' : '确认删除' }}
            </AppButton>
          </div>
        </AppCard>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted } from "vue";
import { useRouter } from "vue-router";
import { apiClient } from "@/config/api";
import { useHomeData } from "@/composables/useHomeData";
import AppButton from "@/components/AppButton.vue";
import AppCard from "@/components/AppCard.vue";
import SpiritAvatar from "@/components/garden/SpiritAvatar.vue";

const router = useRouter();
const homeData = useHomeData();

const loading = ref(false);
const entries = ref<any[]>([]);

const tagColors = [
  "rgba(184, 125, 90, 0.12)",
  "rgba(138, 154, 122, 0.15)",
  "rgba(184, 169, 201, 0.15)",
  "rgba(201, 154, 90, 0.12)",
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

const displayEntries = computed(() => entries.value || []);

// 编辑态
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
  if (editingKeywords.value.includes(v)) {
    newKeyword.value = "";
    return;
  }
  if (editingKeywords.value.length >= 6) {
    editError.value = "最多 6 个关键词";
    return;
  }
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
      const idx = entries.value.findIndex((e: any) => e.id === entry.id);
      if (idx >= 0) {
        entries.value[idx] = {
          ...entries.value[idx],
          entry_text: editingText.value.trim(),
          keywords: [...editingKeywords.value],
          text: editingText.value.trim(),
        };
      }
      cancelEdit();
    } else {
      editError.value = res.data?.detail || "保存失败，请稍后再试";
    }
  } catch (e: any) {
    editError.value = e?.response?.data?.detail || e?.message || "保存失败";
  } finally {
    saving.value = false;
  }
}

// 删除态
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
      deletingEntry.value = null;
      await loadEntries();
    } else {
      editError.value = res.data?.detail || "删除失败";
    }
  } catch (e: any) {
    editError.value = e?.response?.data?.detail || e?.message || "删除失败";
  } finally {
    deleting.value = false;
  }
}

// 加载
async function loadEntries() {
  const reportId = homeData.reportId.value;
  if (!reportId) return;
  loading.value = true;
  try {
    const res = await apiClient.get(`/spirit-diary/${reportId}?limit=50&offset=0`);
    if (res.data?.status === "success") {
      entries.value = res.data.data?.entries || res.data.data || [];
    }
  } catch (e) {
    console.error("[Diary] 加载失败:", e);
  } finally {
    loading.value = false;
  }
}

function goBack() {
  router.back();
}

function goChat() {
  router.push({ name: "entry" });
}

function startNewEntry() {
  router.push({ name: "entry" });
}

onMounted(() => {
  homeData.refreshData().then(loadEntries);
});
</script>

<style scoped lang="less">
.diary-page {
  min-height: 100vh;
  min-height: 100dvh;
  background: var(--bg-main);
  padding-bottom: calc(var(--space-6) + env(safe-area-inset-bottom, 0px));
}

.diary-header {
  position: sticky;
  top: 0;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  padding-top: calc(var(--space-3) + env(safe-area-inset-top, 0px));
  background: var(--bg-card-glass);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-bottom: 1px solid var(--border-light);
}

.diary-back,
.diary-add {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  transition: all var(--duration-fast) var(--ease-smooth);
  flex-shrink: 0;
}

.diary-back:hover,
.diary-add:hover {
  background: var(--fill-color);
  color: var(--text-primary);
}

.diary-header__title {
  font-size: var(--text-lg);
  font-weight: var(--font-bold);
  color: var(--text-primary);
  flex: 1;
  text-align: center;
}

.diary-loading {
  text-align: center;
  padding: 80px 0;
}

.loading-spinner {
  display: flex;
  justify-content: center;
  gap: 8px;
  margin-bottom: 16px;
}

.loading-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-primary);
  animation: dot-bounce 1.2s ease-in-out infinite;
}

@keyframes dot-bounce {
  0%, 100% { transform: translateY(0); opacity: 0.4; }
  50% { transform: translateY(-12px); opacity: 1; }
}

.loading-text {
  font-size: var(--text-base);
  color: var(--text-secondary);
  margin: 0;
}

.diary-empty {
  text-align: center;
  padding: 100px var(--space-5);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-3);
}

.empty-icon {
  font-size: 48px;
  margin-bottom: var(--space-2);
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-8px); }
}

.empty-title {
  font-size: var(--text-xl);
  font-weight: var(--font-bold);
  color: var(--text-primary);
  margin: 0;
}

.empty-desc {
  font-size: var(--text-base);
  color: var(--text-secondary);
  margin: 0 0 var(--space-4);
  max-width: 280px;
}

.diary-timeline {
  max-width: var(--content-max);
  margin: 0 auto;
  padding: var(--space-5);
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.timeline-item {
  display: flex;
  gap: var(--space-4);
}

.timeline-marker {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-2);
  padding-top: var(--space-4);
  flex-shrink: 0;
}

.timeline-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--color-primary);
  box-shadow: 0 0 0 4px var(--color-primary-soft);
}

.timeline-date {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  writing-mode: vertical-rl;
  letter-spacing: 1px;
  font-weight: var(--font-medium);
}

.diary-card {
  flex: 1;
}

.diary-card__header {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  margin-bottom: var(--space-3);
}

.diary-card__spirit {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex: 1;
}

.diary-card__spirit-name {
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
}

.diary-card__mood {
  font-size: var(--text-lg);
}

.entry-actions {
  display: flex;
  gap: var(--space-1);
}

.entry-action-btn {
  width: 28px;
  height: 28px;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-tertiary);
  transition: all var(--duration-fast) var(--ease-smooth);
}

.entry-action-btn:hover {
  background: var(--fill-color);
  color: var(--text-primary);
}

.entry-action-btn--danger:hover {
  background: rgba(184, 92, 92, 0.08);
  color: var(--color-danger);
}

.diary-card__text {
  font-size: var(--text-base);
  color: var(--text-primary);
  line-height: var(--leading-relaxed);
  margin: 0 0 var(--space-3);
  white-space: pre-wrap;
  word-break: break-word;
}

.entry-tags {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.entry-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: var(--text-xs);
  font-weight: var(--font-medium);
  color: var(--text-secondary);
  padding: 4px 10px;
  border-radius: var(--radius-full);
  letter-spacing: 0.3px;
}

.entry-tag-emoji {
  font-size: var(--text-sm);
}

.entry-tag-text {
  line-height: 1;
}

/* Edit mode */
.diary-card__edit {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.entry-textarea {
  width: 100%;
  box-sizing: border-box;
  font-size: var(--text-base);
  line-height: var(--leading-relaxed);
  color: var(--text-primary);
  padding: var(--space-3);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-light);
  background: var(--bg-elevated);
  resize: none;
  outline: none;
  font-family: inherit;
}

.entry-textarea:focus {
  border-color: var(--color-primary);
  box-shadow: var(--shadow-glow);
}

.entry-tags-edit {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.entry-tags-edit-row {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  min-height: 28px;
}

.entry-tag--editable {
  padding-right: 4px;
}

.entry-tag-remove {
  border: none;
  background: transparent;
  cursor: pointer;
  color: var(--text-tertiary);
  font-size: 14px;
  line-height: 1;
  padding: 0 2px;
  border-radius: 4px;
  margin-left: 2px;
}

.entry-tag-remove:hover {
  color: var(--color-danger);
}

.entry-tags-empty {
  font-size: var(--text-sm);
  color: var(--text-tertiary);
  align-self: center;
}

.entry-tags-add {
  display: flex;
  gap: var(--space-2);
}

.entry-tags-input {
  flex: 1;
  font-size: var(--text-sm);
  padding: 6px 10px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-light);
  background: var(--bg-elevated);
  outline: none;
  color: var(--text-primary);
}

.entry-tags-input:focus {
  border-color: var(--color-primary);
}

.entry-tags-add-btn {
  border: none;
  background: var(--color-primary-soft);
  color: var(--color-primary-dark);
  font-size: 16px;
  width: 32px;
  border-radius: var(--radius-md);
  cursor: pointer;
  line-height: 1;
  transition: all var(--duration-fast) var(--ease-smooth);
}

.entry-tags-add-btn:hover {
  background: var(--color-primary-light);
  color: #fff;
}

.entry-edit-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-2);
  margin-top: var(--space-2);
}

.entry-edit-error {
  font-size: var(--text-sm);
  color: var(--color-danger);
  margin: var(--space-1) 0 0;
}

/* Confirm modal */
.confirm-mask {
  position: fixed;
  inset: 0;
  z-index: 300;
  background: rgba(44, 38, 34, 0.25);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-5);
}

.confirm-fade-enter-active,
.confirm-fade-leave-active {
  transition: opacity var(--duration-fast) var(--ease-smooth);
}

.confirm-fade-enter-from,
.confirm-fade-leave-to {
  opacity: 0;
}

.confirm-card {
  max-width: 320px;
  width: 100%;
  text-align: center;
}

.confirm-icon {
  font-size: 36px;
  margin-bottom: var(--space-2);
}

.confirm-title {
  font-size: var(--text-lg);
  font-weight: var(--font-bold);
  color: var(--text-primary);
  margin: 0 0 var(--space-1);
}

.confirm-desc {
  font-size: var(--text-base);
  color: var(--text-secondary);
  margin: 0 0 var(--space-5);
  line-height: var(--leading-normal);
}

.confirm-actions {
  display: flex;
  gap: var(--space-3);
  justify-content: center;
}

@media (max-width: 380px) {
  .diary-timeline {
    padding: var(--space-4);
  }
  .timeline-marker {
    display: none;
  }
}
</style>
