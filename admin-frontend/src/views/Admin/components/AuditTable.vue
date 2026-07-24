<template>
  <div class="audit-table">
    <div class="toolbar">
      <input
        v-model="adminUsername"
        class="search"
        placeholder="管理员用户名"
        @keyup.enter="load"
      />
      <input
        v-model="action"
        class="search"
        placeholder="操作类型"
        @keyup.enter="load"
      />
      <button class="btn" @click="load">查询</button>
    </div>

    <div class="meta">
      <span>共 {{ total }} 条记录</span>
    </div>

    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>时间</th>
            <th>管理员</th>
            <th>操作</th>
            <th>对象类型</th>
            <th>对象 ID</th>
            <th>详情</th>
            <th>IP</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="7" class="muted">加载中...</td>
          </tr>
          <tr v-else-if="logs.length === 0">
            <td colspan="7" class="muted">暂无日志</td>
          </tr>
          <tr v-for="l in logs" :key="l.id" v-else>
            <td class="dim">{{ formatTime(l.created_at) }}</td>
            <td>
              <span class="admin-tag">{{ l.admin_username }}</span>
            </td>
            <td><code class="action-tag">{{ l.action }}</code></td>
            <td>{{ l.target_type }}</td>
            <td>
              <code class="dim">{{ (l.target_id || "").slice(0, 16) }}</code>
            </td>
            <td class="detail">{{ l.detail || "--" }}</td>
            <td class="dim">{{ l.ip || "--" }}</td>
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

const logs = ref<any[]>([]);
const total = ref(0);
const loading = ref(false);
const adminUsername = ref("");
const action = ref("");
const page = ref(1);
const pageSize = 30;

async function load() {
  loading.value = true;
  try {
    const res = await adminApi.get("/audit-logs", {
      params: {
        admin_username: adminUsername.value,
        action: action.value,
        limit: pageSize,
        offset: (page.value - 1) * pageSize,
      },
    });
    if (res.data?.status === "success") {
      logs.value = res.data.data.logs || [];
      total.value = res.data.data.total || 0;
    }
  } catch {
    logs.value = [];
    total.value = 0;
  } finally {
    loading.value = false;
  }
}

function formatTime(s: string) {
  return (s || "").slice(0, 19).replace("T", " ");
}

onMounted(load);
</script>

<style scoped>
.audit-table {
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
  max-width: 200px;
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
  font-size: 12px;
}
th,
td {
  text-align: left;
  padding: 8px 12px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}
th {
  font-weight: 600;
  color: #6b7280;
  font-size: 11px;
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
.admin-tag {
  background: rgba(242, 169, 0, 0.1);
  color: #f2a900;
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 600;
}
.action-tag {
  background: rgba(99, 102, 241, 0.1);
  color: #4f46e5;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 11px;
}
.detail {
  max-width: 240px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
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
