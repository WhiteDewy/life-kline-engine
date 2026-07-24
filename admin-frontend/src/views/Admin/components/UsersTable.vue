<template>
  <div class="users-table">
    <div class="toolbar">
      <input
        v-model="keyword"
        class="search"
        placeholder="搜索 手机号 / 昵称"
        @keyup.enter="load"
      />
      <select v-model="filterDisabled" class="select" @change="load">
        <option :value="-1">全部状态</option>
        <option :value="0">正常</option>
        <option :value="1">已禁用</option>
      </select>
      <button class="btn" @click="load">查询</button>
    </div>

    <div class="meta">
      <span>共 {{ total }} 个用户</span>
    </div>

    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>手机号</th>
            <th>昵称</th>
            <th>档案</th>
            <th>报告</th>
            <th>日记</th>
            <th>状态</th>
            <th>注册时间</th>
            <th>最后登录</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="9" class="muted">加载中...</td>
          </tr>
          <tr v-else-if="users.length === 0">
            <td colspan="9" class="muted">暂无用户</td>
          </tr>
          <tr v-for="u in users" :key="u.id" v-else>
            <td>{{ u.phone }}</td>
            <td>{{ u.nickname || "--" }}</td>
            <td>{{ profileCount(u.id) }}</td>
            <td>{{ u.report_count || 0 }}</td>
            <td>{{ u.diary_count || 0 }}</td>
            <td>
              <span :class="['status', statusOf(u)]">{{ statusLabel(u) }}</span>
            </td>
            <td class="dim">{{ formatTime(u.created_at) }}</td>
            <td class="dim">{{ formatTime(u.last_login_at) }}</td>
            <td class="actions">
              <button class="link" @click="emit('open-detail', u.id)">
                详情
              </button>
              <button
                v-if="!isDisabled(u)"
                class="link danger"
                @click="confirmAction('disable', u)"
              >
                禁用
              </button>
              <button
                v-else
                class="link ok"
                @click="confirmAction('enable', u)"
              >
                启用
              </button>
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
  (e: "open-detail", userId: string): void;
}>();

const users = ref<any[]>([]);
const total = ref(0);
const loading = ref(false);
const keyword = ref("");
const filterDisabled = ref(-1);
const page = ref(1);
const pageSize = 30;

const profileCounts = ref<Record<string, number>>({});

async function load() {
  loading.value = true;
  try {
    const res = await adminApi.get("/users", {
      params: {
        keyword: keyword.value,
        is_disabled: filterDisabled.value,
        limit: pageSize,
        offset: (page.value - 1) * pageSize,
      },
    });
    if (res.data?.status === "success") {
      users.value = res.data.data.users || [];
      total.value = res.data.data.total || 0;
    }
  } catch {
    users.value = [];
    total.value = 0;
  } finally {
    loading.value = false;
  }
}

function profileCount(userId: string) {
  return profileCounts.value[userId] ?? "—";
}

function isDisabled(u: any) {
  return !!u.is_disabled;
}

function statusOf(u: any) {
  if (u.deleted_at) return "deleted";
  if (u.is_disabled) return "disabled";
  return "active";
}

function statusLabel(u: any) {
  if (u.deleted_at) return "已删除";
  if (u.is_disabled) return "禁用";
  return "正常";
}

function formatTime(s: string | null | undefined) {
  if (!s) return "—";
  return s.slice(0, 16).replace("T", " ");
}

async function confirmAction(action: "enable" | "disable", u: any) {
  const verb = action === "disable" ? "禁用" : "启用";
  if (!confirm(`确认要${verb}用户 ${u.phone} 吗？`)) return;
  try {
    await adminApi.patch(`/users/${u.id}`, { disabled: action === "disable" });
    await load();
  } catch (e: any) {
    alert(e?.response?.data?.detail || `${verb}失败`);
  }
}

onMounted(load);
</script>

<style scoped>
.users-table {
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
  padding: 8px 16px;
  border-radius: 10px;
  border: none;
  background: #1f2937;
  color: #fff;
  cursor: pointer;
  font-family: inherit;
  font-size: 13px;
  transition: opacity 0.2s;
}
.btn:hover {
  opacity: 0.9;
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
.status {
  font-size: 11px;
  padding: 3px 10px;
  border-radius: 8px;
  font-weight: 600;
}
.status.active {
  background: rgba(34, 197, 94, 0.1);
  color: #16a34a;
}
.status.disabled,
.status.deleted {
  background: rgba(239, 68, 68, 0.1);
  color: #dc2626;
}
.actions {
  display: flex;
  gap: 8px;
}
.link {
  background: transparent;
  border: none;
  cursor: pointer;
  font-size: 13px;
  text-decoration: underline;
  font-family: inherit;
  color: #4f46e5;
}
.link.danger {
  color: #dc2626;
}
.link.ok {
  color: #16a34a;
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
