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
            v-for="entry in displayEntries"
            :key="entry.id || entry.created_at"
            class="diary-entry"
            :class="{ 'diary-entry--editing': editingId === entry.id }"
          >
            <!-- 顶部条：日期 / 情绪 / 星灵 / 操作按钮 -->
            <div class="entry-header">
              <span class="entry-date">{{ formatDate(entry) }}</span>
              <span class="entry-mood" v-if="entry.mood_emoji">{{ entry.mood_emoji }}</span>
              <span class="entry-planet" v-if="entry.spirit_planet">
                {{ entry.spirit_planet_label || entry.spirit_planet }}
              </span>

              <!-- 操作按钮组（编辑/删除）—— 仅在非编辑态可见 -->
              <div v-if="editingId !== entry.id && entry.id" class="entry-actions">
                <button
                  class="entry-action-btn"
                  title="编辑"
                  aria-label="编辑日记"
                  @click="startEdit(entry)"
                >
                  ✎
                </button>
                <button
                  class="entry-action-btn entry-action-btn--danger"
                  title="删除"
                  aria-label="删除日记"
                  @click="confirmDelete(entry)"
                >
                  🗑
                </button>
              </div>
            </div>

            <!-- 摘要（无 entry_text 时降级到 chat_context） -->
            <p class="entry-text" v-if="editingId !== entry.id">
              {{ entry.entry_text || entry.text || entry.chat_context || '...' }}
            </p>
            <textarea
              v-else
              ref="editTextarea"
              class="entry-textarea"
              v-model="editingText"
              rows="5"
              maxlength="500"
              placeholder="写点什么吧..."
              @input="autoResize($event)"
            ></textarea>

            <!-- 关键词标签 -->
            <div class="entry-tags" v-if="editingId !== entry.id && entry.keywords?.length">
              <span
                v-for="(kw, ki) in entry.keywords.slice(0, 4)"
                :key="ki"
                class="entry-tag"
                :style="{ background: tagColors[Number(ki) % tagColors.length] }"
              >
                <span class="entry-tag-emoji">{{ emojiForKw(kw) }}</span>
                <span class="entry-tag-text">{{ kw }}</span>
              </span>
            </div>

            <!-- 编辑态：关键词编辑 -->
            <div v-else class="entry-tags-edit">
              <div class="entry-tags-edit-row">
                <span
                  v-for="(kw, ki) in editingKeywords"
                  :key="`${kw}-${ki}`"
                  class="entry-tag entry-tag--editable"
                  :style="{ background: tagColors[Number(ki) % tagColors.length] }"
                >
                  <span class="entry-tag-emoji">{{ emojiForKw(kw) }}</span>
                  <span class="entry-tag-text">{{ kw }}</span>
                  <button
                    type="button"
                    class="entry-tag-remove"
                    aria-label="删除关键词"
                    @click="removeKeyword(ki)"
                  >×</button>
                </span>
                <span v-if="!editingKeywords.length" class="entry-tags-empty">还没有关键词</span>
              </div>
              <div class="entry-tags-add">
                <input
                  v-model="newKeyword"
                  class="entry-tags-input"
                  placeholder="添加关键词后回车"
                  maxlength="12"
                  @keydown.enter.prevent="addKeyword"
                />
                <button type="button" class="entry-tags-add-btn" @click="addKeyword">＋</button>
              </div>
            </div>

            <!-- 编辑态：底部按钮 -->
            <div v-if="editingId === entry.id" class="entry-edit-actions">
              <button
                class="entry-btn entry-btn--ghost"
                :disabled="saving"
                @click="cancelEdit"
              >
                取消
              </button>
              <button
                class="entry-btn entry-btn--primary"
                :disabled="saving || !editingText.trim()"
                @click="saveEdit(entry)"
              >
                {{ saving ? '保存中...' : '保存' }}
              </button>
            </div>

            <!-- 错误提示 -->
            <p v-if="editingId === entry.id && editError" class="entry-edit-error">
              {{ editError }}
            </p>
          </div>
        </div>
      </div>

      <!-- 删除确认弹窗 -->
      <transition name="confirm-fade">
        <div v-if="deletingEntry" class="confirm-mask" @click.self="cancelDelete">
          <div class="confirm-card">
            <div class="confirm-icon">🗑</div>
            <p class="confirm-title">删除这条日记？</p>
            <p class="confirm-desc">删除后无法恢复，星灵也会记得你说的话。</p>
            <div class="confirm-actions">
              <button class="entry-btn entry-btn--ghost" :disabled="deleting" @click="cancelDelete">
                再想想
              </button>
              <button class="entry-btn entry-btn--danger" :disabled="deleting" @click="executeDelete">
                {{ deleting ? '删除中...' : '确认删除' }}
              </button>
            </div>
          </div>
        </div>
      </transition>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { computed, nextTick, ref } from "vue";
import { apiClient } from "@/config/api";

const props = defineProps<{
  visible: boolean
  entries: any[]
  loading: boolean
}>()

const emit = defineEmits<{
  close: []
  refresh: []
}>()

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
  // 优先展示 YYYY-MM-DD
  if (/^\d{4}-\d{2}-\d{2}/.test(raw)) return raw.slice(0, 10);
  return raw;
}

const displayEntries = computed(() => {
  return props.entries && props.entries.length > 0 ? props.entries : [];
});

// ── 编辑态状态 ──
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
      // 本地乐观更新
      const idx = props.entries.findIndex((e: any) => e.id === entry.id);
      if (idx >= 0) {
        const updated = {
          ...props.entries[idx],
          entry_text: editingText.value.trim(),
          keywords: [...editingKeywords.value],
          text: editingText.value.trim(),
        };
        const arr = [...props.entries];
        arr[idx] = updated;
        // 通过事件冒泡给父组件刷新
        emit("refresh");
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

// ── 删除态状态 ──
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
      emit("refresh");
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
.diary-entry--editing {
  border-color: rgba(242,169,0,0.4);
  box-shadow: 0 4px 24px rgba(242,169,0,0.12);
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
.entry-actions {
  display: flex; gap: 4px; margin-left: 6px;
}
.entry-action-btn {
  border: none; background: transparent; cursor: pointer;
  width: 26px; height: 26px; border-radius: 8px;
  font-size: 13px; line-height: 1;
  display: inline-flex; align-items: center; justify-content: center;
  color: #8b7355; transition: all 0.15s;
}
.entry-action-btn:hover {
  background: rgba(0,0,0,0.05);
  color: #4a3728;
}
.entry-action-btn--danger:hover {
  background: rgba(232,160,191,0.25);
  color: #c0392b;
}

.entry-text {
  font-size: 14px; color: #4a3728; line-height: 1.7;
  margin: 0 0 10px;
  white-space: pre-wrap;
  word-break: break-word;
}

.entry-textarea {
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
  margin-bottom: 10px;
}
.entry-textarea:focus {
  border-color: rgba(242,169,0,0.5);
}

.entry-tags {
  display: flex; flex-wrap: wrap; gap: 6px;
}
.entry-tag {
  display: inline-flex; align-items: center; gap: 4px;
  font-size: 11px; font-weight: 500; color: #5c4a3a;
  padding: 3px 10px; border-radius: 8px;
  letter-spacing: 0.3px;
}
.entry-tag-emoji { font-size: 12px; }
.entry-tag-text { line-height: 1; }

/* 编辑态关键词 */
.entry-tags-edit {
  display: flex; flex-direction: column; gap: 8px;
  margin-bottom: 4px;
}
.entry-tags-edit-row {
  display: flex; flex-wrap: wrap; gap: 6px; min-height: 22px;
}
.entry-tag--editable {
  padding-right: 4px;
}
.entry-tag-remove {
  border: none; background: transparent; cursor: pointer;
  color: #8b7355; font-size: 14px; line-height: 1;
  padding: 0 2px; border-radius: 4px;
  margin-left: 2px;
}
.entry-tag-remove:hover { color: #c0392b; }
.entry-tags-empty {
  font-size: 12px; color: #a89880;
  align-self: center;
}
.entry-tags-add {
  display: flex; gap: 6px;
}
.entry-tags-input {
  flex: 1;
  font-size: 12px;
  padding: 6px 10px;
  border-radius: 10px;
  border: 1px solid rgba(0,0,0,0.08);
  background: rgba(255,255,255,0.7);
  outline: none;
  color: #4a3728;
}
.entry-tags-input:focus {
  border-color: rgba(242,169,0,0.4);
}
.entry-tags-add-btn {
  border: none;
  background: rgba(242,169,0,0.15);
  color: #b67c00;
  font-size: 16px;
  width: 30px;
  border-radius: 10px;
  cursor: pointer;
  line-height: 1;
}
.entry-tags-add-btn:hover { background: rgba(242,169,0,0.25); }

/* 底部按钮 */
.entry-edit-actions {
  display: flex; justify-content: flex-end; gap: 8px;
  margin-top: 12px;
}
.entry-btn {
  font-size: 13px; font-weight: 600;
  padding: 8px 18px;
  border-radius: 12px;
  border: none;
  cursor: pointer;
  transition: all 0.15s;
}
.entry-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.entry-btn--ghost {
  background: rgba(0,0,0,0.04);
  color: #8b7355;
}
.entry-btn--ghost:hover:not(:disabled) {
  background: rgba(0,0,0,0.08);
}
.entry-btn--primary {
  background: linear-gradient(135deg, #f2a900, #ff9a8b);
  color: #fff;
  box-shadow: 0 2px 8px rgba(242,169,0,0.25);
}
.entry-btn--primary:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(242,169,0,0.35);
}
.entry-btn--danger {
  background: linear-gradient(135deg, #e8a0bf, #c0392b);
  color: #fff;
  box-shadow: 0 2px 8px rgba(192,57,43,0.25);
}
.entry-btn--danger:hover:not(:disabled) {
  transform: translateY(-1px);
}

.entry-edit-error {
  font-size: 12px; color: #c0392b;
  margin: 8px 0 0;
}

/* 删除确认弹窗 */
.confirm-mask {
  position: fixed; inset: 0; z-index: 300;
  background: rgba(0,0,0,0.4);
  display: flex; align-items: center; justify-content: center;
  padding: 20px;
}
.confirm-fade-enter-active, .confirm-fade-leave-active {
  transition: opacity 0.2s;
}
.confirm-fade-enter-from, .confirm-fade-leave-to { opacity: 0; }

.confirm-card {
  background: #fff;
  border-radius: 20px;
  padding: 28px 24px 22px;
  max-width: 320px;
  width: 100%;
  text-align: center;
  box-shadow: 0 10px 40px rgba(0,0,0,0.18);
}
.confirm-icon {
  font-size: 36px;
  margin-bottom: 8px;
}
.confirm-title {
  font-size: 17px; font-weight: 700; color: #4a3728;
  margin: 0 0 6px;
}
.confirm-desc {
  font-size: 13px; color: #8b7355;
  margin: 0 0 20px;
  line-height: 1.5;
}
.confirm-actions {
  display: flex; gap: 10px; justify-content: center;
}

@media (max-width: 400px) {
  .diary-body { padding: 0 16px 32px; }
  .diary-entry { padding: 14px; }
}
</style>