<template>
  <div class="reports-table">
    <div class="toolbar">
      <input
        v-model="keyword"
        class="search"
        placeholder="搜索报告摘要 / ID"
        @keyup.enter="load"
      />
      <button class="btn" @click="load">查询</button>
    </div>

    <div class="meta">
      <span>共 {{ total }} 份报告</span>
    </div>

    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>报告 ID</th>
            <th>类型</th>
            <th>用户</th>
            <th>摘要</th>
            <th>生成时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="6" class="muted">加载中...</td>
          </tr>
          <tr v-else-if="reports.length === 0">
            <td colspan="6" class="muted">暂无报告</td>
          </tr>
          <tr v-for="r in reports" :key="r.id" v-else>
            <td><code>{{ r.id.slice(0, 12) }}</code></td>
            <td>{{ r.analysis_type }}</td>
            <td>
              <span>{{ r.nickname || r.phone || r.user_id?.slice(0, 12) }}</span>
            </td>
            <td class="summary">{{ r.kline_summary || "--" }}</td>
            <td class="dim">{{ formatTime(r.created_at) }}</td>
            <td class="actions">
              <button class="btn ghost" @click="emit('open-detail', r.id)">详情</button>
              <button class="btn danger" @click="confirmDelete(r)">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
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

const reports = ref<any[]>([]);
const total = ref(0);
const loading = ref(false);
const keyword = ref("");
const page = ref(1);
const pageSize = 30;

async function load() {
  loading.value = true;
  try {
    const res = await adminApi.get("/reports", {
      params: {
        keyword: keyword.value,
        limit: pageSize,
        offset: (page.value - 1) * pageSize,
      },
    });
    if (res.data?.status === "success") {
      reports.value = res.data.data.reports || [];
      total.value = res.data.data.total || 0;
    }
  } catch {
    reports.value = [];
    total.value = 0;
  } finally {
    loading.value = false;
  }
}

async function confirmDelete(r: any) {
  if (!confirm(`确认删除报告 ${r.id.slice(0, 12)} 吗？此操作不可恢复！`)) return;
  try {
    await adminApi.delete(`/reports/${r.id}`);
    await load();
  } catch (e: any) {
    alert(e?.response?.data?.detail || "删除失败");
  }
}

function formatTime(s: string) {
  return (s || "").slice(0, 16).replace("T", " ");
}

onMounted(load);
</script>

<style scoped>
.reports-table {
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
.search {
  flex: 1;
  max-width: 320px;
  padding: 8px 12px;
  border-radius: 10px;
  border: 1px solid rgba(0, 0, 0, 0.1);
  font-size: 13px;
  outline: none;
}
.btn {
  padding: 8px 16px;
  border-radius: 10px;
  border: none;
  background: #1f2937;
  color: #fff;
  cursor: pointer;
  font-family: inherit;
  font-size: 13px;
}
.btn.ghost {
  background: transparent;
  color: #6b7280;
  border: 1px solid rgba(0, 0, 0, 0.1);
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
  margin-bottom: 10px;
}
.table-wrap {
  overflow-x: auto;
}
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
th,
td {
  text-align: left;
  padding: 10px 12px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}
th {
  font-weight: 600;
  color: #6b7280;
  font-size: 12px;
  background: #f9fafb;
}
.dim {
  color: #9ca3af;
}
.muted {
  text-align: center;
  color: #9ca3af;
  padding: 32px 0 !important;
}
.summary {
  max-width: 320px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.actions {
  display: flex;
  gap: 6px;
}
code {
  background: #f3f4f6;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 11px;
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
