<template>
  <div class="diary-table">
    <div class="toolbar">
      <input
        v-model="keyword"
        class="search"
        placeholder="搜索日记内容..."
        @keyup.enter="load"
      />
      <select v-model="status" class="select" @change="load">
        <option value="all">全部状态</option>
        <option value="visible">显示</option>
        <option value="hidden">已隐藏</option>
        <option value="flagged">已标记</option>
      </select>
      <button class="btn" @click="load">查询</button>
    </div>

    <div class="meta">
      <span>共 {{ total }} 条日记</span>
    </div>

    <div class="list">
      <div v-if="loading" class="empty">加载中...</div>
      <div v-else-if="entries.length === 0" class="empty">暂无日记</div>
      <div v-for="e in entries" :key="e.id" class="entry-card">
        <div class="entry-header">
          <div class="entry-meta">
            <span class="mood" v-if="e.mood_emoji">{{ e.mood_emoji }}</span>
            <span class="planet" v-if="e.spirit_planet">{{ e.spirit_planet }}</span>
            <span class="dim">{{ formatTime(e.created_at) }}</span>
          </div>
          <span :class="['status', e.mod_status || 'visible']">
            {{ statusLabel(e.mod_status || "visible") }}
          </span>
        </div>

        <div class="entry-text">{{ e.entry_text }}</div>

        <div class="entry-tags" v-if="e.keywords?.length">
          <span v-for="(kw, i) in e.keywords" :key="i" class="tag">{{ kw }}</span>
        </div>

        <div class="entry-actions">
          <button class="btn ghost" @click="emit('open-detail', e.id)">
            详情
          </button>
          <button
            v-if="(e.mod_status || 'visible') !== 'hidden'"
            class="btn ghost"
            @click="moderate(e, 'hidden')"
          >
            隐藏
          </button>
          <button
            v-if="(e.mod_status || 'visible') !== 'visible'"
            class="btn ghost ok"
            @click="moderate(e, 'visible')"
          >
            显示
          </button>
          <button
            v-if="(e.mod_status || 'visible') !== 'flagged'"
            class="btn ghost"
            @click="moderate(e, 'flagged')"
          >
            标记
          </button>
          <button class="btn danger" @click="confirmDelete(e)">删除</button>
        </div>
      </div>
    </div>

    <div class="pagination" v-if="total > pageSize">
      <button class="btn ghost" :disabled="page <= 1" @click="page--; load()">
        上一页
      </button>
      <span class="page-info">{{ page }} / {{ Math.ceil(total / pageSize) }}</span>
      <button
        class="btn ghost"
        :disabled="page >= Math.ceil(total / pageSize)"
        @click="page++; load()"
      >
        下一页
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import adminApi from "@/config/adminApi";

const emit = defineEmits<{
  (e: "open-detail", id: string): void;
}>();

const entries = ref<any[]>([]);
const total = ref(0);
const loading = ref(false);
const keyword = ref("");
const status = ref("all");
const page = ref(1);
const pageSize = 20;

async function load() {
  loading.value = true;
  try {
    const res = await adminApi.get("/diary", {
      params: {
        keyword: keyword.value,
        status: status.value,
        limit: pageSize,
        offset: (page.value - 1) * pageSize,
      },
    });
    if (res.data?.status === "success") {
      entries.value = res.data.data.entries || [];
      total.value = res.data.data.total || 0;
    }
  } catch {
    entries.value = [];
    total.value = 0;
  } finally {
    loading.value = false;
  }
}

async function moderate(entry: any, newStatus: string) {
  try {
    await adminApi.patch(`/diary/${entry.id}`, {
      status: newStatus,
      reason: newStatus === "hidden" ? "通过后台隐藏" : "",
    });
    await load();
  } catch (e: any) {
    alert(e?.response?.data?.detail || "审核失败");
  }
}

async function confirmDelete(entry: any) {
  if (!confirm(`确认删除这条日记吗？\n\n${entry.entry_text.slice(0, 60)}...`)) return;
  try {
    await adminApi.delete(`/diary/${entry.id}`);
    await load();
  } catch (e: any) {
    alert(e?.response?.data?.detail || "删除失败");
  }
}

function statusLabel(s: string) {
  return { visible: "显示", hidden: "已隐藏", flagged: "已标记" }[s] || s;
}

function formatTime(s: string) {
  return (s || "").slice(0, 16).replace("T", " ");
}

onMounted(load);
</script>

<style scoped>
.diary-table {
  background: #fff;
  border-radius: 18px;
  padding: 20px;
  border: 1px solid rgba(0, 0, 0, 0.04);
}
.toolbar {
  display: flex;
  gap: 8px;
  margin-bottom: 14px;
}
.search,
.select {
  padding: 8px 12px;
  border-radius: 10px;
  border: 1px solid rgba(0, 0, 0, 0.1);
  font-size: 13px;
  outline: none;
  background: #fff;
  font-family: inherit;
}
.search {
  flex: 1;
  max-width: 260px;
}
.select {
  min-width: 120px;
}
.btn {
  padding: 7px 14px;
  border-radius: 8px;
  border: none;
  background: #1f2937;
  color: #fff;
  cursor: pointer;
  font-family: inherit;
  font-size: 12px;
  transition: opacity 0.2s;
}
.btn.ghost {
  background: transparent;
  color: #6b7280;
  border: 1px solid rgba(0, 0, 0, 0.1);
}
.btn.ghost.ok {
  color: #16a34a;
}
.btn.danger {
  background: #dc2626;
}
.btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.meta {
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 12px;
}
.list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.entry-card {
  border-radius: 14px;
  padding: 16px;
  background: #f9fafb;
  border: 1px solid rgba(0, 0, 0, 0.04);
}
.entry-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}
.entry-meta {
  display: flex;
  gap: 8px;
  align-items: center;
}
.mood {
  font-size: 18px;
}
.planet {
  background: rgba(242, 169, 0, 0.1);
  color: #f2a900;
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 600;
}
.dim {
  font-size: 11px;
  color: #9ca3af;
}
.status {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 6px;
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
  font-size: 13px;
  color: #374151;
  line-height: 1.7;
  margin-bottom: 8px;
}
.entry-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 10px;
}
.tag {
  padding: 2px 8px;
  border-radius: 6px;
  background: rgba(0, 0, 0, 0.04);
  color: #6b7280;
  font-size: 11px;
}
.entry-actions {
  display: flex;
  gap: 6px;
}
.empty {
  text-align: center;
  color: #9ca3af;
  font-size: 13px;
  padding: 40px 0;
}
.pagination {
  display: flex;
  align-items: center;
  gap: 12px;
  justify-content: center;
  margin-top: 16px;
}
.page-info {
  font-size: 12px;
  color: #6b7280;
}
</style>
