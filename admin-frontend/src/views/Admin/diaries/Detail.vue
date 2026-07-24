<template>
  <div class="diary-detail">
    <div class="breadcrumb">
      <router-link to="/admin/diaries" class="back">← 返回日记列表</router-link>
    </div>

    <div v-if="loading" class="loading">加载中...</div>

    <div v-else-if="error" class="error">{{ error }}</div>

    <article v-else-if="entry" class="detail-card">
      <header class="entry-header">
        <div class="entry-meta">
          <span class="mood" v-if="entry.mood_emoji">{{ entry.mood_emoji }}</span>
          <span class="planet" v-if="entry.spirit_planet">{{ entry.spirit_planet }}</span>
          <span class="dim">{{ formatTime(entry.created_at) }}</span>
        </div>
        <span :class="['status', entry.mod_status || 'visible']">
          {{ statusLabel(entry.mod_status || "visible") }}
        </span>
      </header>

      <section class="entry-text">{{ entry.entry_text }}</section>

      <section v-if="entry.keywords?.length" class="block">
        <h3>关键词</h3>
        <div class="tags">
          <span v-for="(kw, i) in entry.keywords" :key="i" class="tag">{{ kw }}</span>
        </div>
      </section>

      <section v-if="entry.chat_context" class="block">
        <h3>对话上下文</h3>
        <pre class="context">{{ entry.chat_context }}</pre>
      </section>

      <section class="meta-grid">
        <div class="stat">
          <span class="label">日记 ID</span>
          <code class="value-mono">{{ entry.id }}</code>
        </div>
        <div class="stat">
          <span class="label">用户 ID</span>
          <code class="value-mono">{{ entry.user_id }}</code>
        </div>
        <div v-if="entry.profile_id" class="stat">
          <span class="label">档案 ID</span>
          <code class="value-mono">{{ entry.profile_id }}</code>
        </div>
      </section>

      <footer class="actions">
        <button
          v-if="(entry.mod_status || 'visible') !== 'visible'"
          class="btn ok"
          @click="moderate('visible')"
        >
          设为显示
        </button>
        <button
          v-if="(entry.mod_status || 'visible') !== 'hidden'"
          class="btn warn"
          @click="moderate('hidden')"
        >
          隐藏
        </button>
        <button
          v-if="(entry.mod_status || 'visible') !== 'flagged'"
          class="btn flag"
          @click="moderate('flagged')"
        >
          标记
        </button>
        <button class="btn danger" @click="confirmDelete">删除</button>
      </footer>
    </article>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import adminApi from "@/config/adminApi";

const route = useRoute();
const router = useRouter();
const entry = ref<any | null>(null);
const loading = ref(false);
const error = ref("");

async function load() {
  const id = route.params.id as string;
  if (!id) {
    error.value = "缺少日记 ID";
    return;
  }
  loading.value = true;
  error.value = "";
  entry.value = null;
  try {
    const res = await adminApi.get(`/diary/${id}`);
    if (res.data?.status === "success") {
      entry.value = res.data.data;
    } else {
      error.value = res.data?.detail || "未找到该日记";
    }
  } catch (e: any) {
    if (e?.response?.status === 404) {
      error.value = "日记不存在";
    } else {
      error.value = e?.response?.data?.detail || "加载失败";
    }
  } finally {
    loading.value = false;
  }
}

function statusLabel(s: string) {
  return { visible: "显示", hidden: "已隐藏", flagged: "已标记" }[s] || s;
}

function formatTime(s: string) {
  return (s || "").slice(0, 19).replace("T", " ");
}

async function moderate(newStatus: string) {
  if (!entry.value) return;
  try {
    await adminApi.patch(`/diary/${entry.value.id}`, {
      status: newStatus,
      reason: newStatus === "hidden" ? "通过后台隐藏" : "",
    });
    await load();
  } catch (e: any) {
    alert(e?.response?.data?.detail || "审核失败");
  }
}

async function confirmDelete() {
  if (!entry.value) return;
  if (!confirm(`确认删除这条日记吗？\n\n${(entry.value.entry_text || "").slice(0, 60)}...`))
    return;
  try {
    await adminApi.delete(`/diary/${entry.value.id}`);
    router.push("/admin/diaries");
  } catch (e: any) {
    alert(e?.response?.data?.detail || "删除失败");
  }
}

watch(() => route.params.id, load);
onMounted(load);
</script>

<style scoped>
.diary-detail {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.breadcrumb {
  font-size: 13px;
}
.back {
  color: #4f46e5;
  text-decoration: none;
}
.back:hover {
  text-decoration: underline;
}
.loading,
.error {
  background: #fff;
  border-radius: 18px;
  padding: 32px;
  text-align: center;
  font-size: 13px;
  color: #6b7280;
}
.error {
  color: #dc2626;
}
.detail-card {
  background: #fff;
  border-radius: 18px;
  padding: 24px;
  border: 1px solid rgba(0, 0, 0, 0.04);
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.entry-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}
.entry-meta {
  display: flex;
  gap: 8px;
  align-items: center;
}
.mood {
  font-size: 22px;
}
.planet {
  background: rgba(242, 169, 0, 0.1);
  color: #f2a900;
  padding: 3px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
}
.dim {
  font-size: 12px;
  color: #9ca3af;
}
.status {
  font-size: 11px;
  padding: 3px 10px;
  border-radius: 8px;
  font-weight: 600;
}
.status.visible {
  background: rgba(34, 197, 94, 0.1);
  color: #16a34a;
}
.status.hidden {
  background: rgba(239, 68, 68, 0.1);
  color: #dc2626;
}
.status.flagged {
  background: rgba(234, 179, 8, 0.1);
  color: #ca8a04;
}
.entry-text {
  font-size: 15px;
  color: #1f2937;
  line-height: 1.8;
  white-space: pre-wrap;
  word-break: break-word;
}
.block h3 {
  font-size: 13px;
  font-weight: 700;
  color: #1f2937;
  margin: 0 0 8px;
}
.tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.tag {
  padding: 3px 10px;
  border-radius: 8px;
  background: rgba(0, 0, 0, 0.04);
  color: #4b5563;
  font-size: 12px;
}
.context {
  background: #f9fafb;
  padding: 14px;
  border-radius: 10px;
  font-size: 12px;
  color: #374151;
  font-family: monospace;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 320px;
  overflow-y: auto;
}
.meta-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 12px;
  padding-top: 8px;
  border-top: 1px solid rgba(0, 0, 0, 0.06);
}
.stat {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.stat .label {
  font-size: 11px;
  color: #6b7280;
}
.value-mono {
  font-family: monospace;
  font-size: 12px;
  color: #1f2937;
  background: #f3f4f6;
  padding: 4px 8px;
  border-radius: 6px;
  word-break: break-all;
}
.actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  padding-top: 12px;
  border-top: 1px solid rgba(0, 0, 0, 0.06);
}
.btn {
  padding: 8px 18px;
  border-radius: 10px;
  border: none;
  cursor: pointer;
  font-family: inherit;
  font-size: 13px;
  font-weight: 600;
  transition: opacity 0.2s;
}
.btn:hover {
  opacity: 0.9;
}
.btn.ok {
  background: #16a34a;
  color: #fff;
}
.btn.warn {
  background: #6b7280;
  color: #fff;
}
.btn.flag {
  background: #ca8a04;
  color: #fff;
}
.btn.danger {
  background: #dc2626;
  color: #fff;
}
</style>