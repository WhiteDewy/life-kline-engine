<template>
  <div class="user-detail">
    <div class="breadcrumb">
      <router-link to="/admin/users" class="back">← 返回用户列表</router-link>
    </div>

    <div v-if="loading" class="loading">加载中...</div>

    <div v-else-if="error" class="error">
      {{ error }}
    </div>

    <div v-else-if="user" class="detail-card">
      <header class="detail-header">
        <div class="avatar">{{ avatarChar }}</div>
        <div class="info">
          <h2 class="name">{{ user.nickname || user.phone || "未命名用户" }}</h2>
          <p class="phone">{{ user.phone || "—" }}</p>
          <span :class="['status', statusOf(user)]">{{ statusLabel(user) }}</span>
        </div>
        <div class="actions">
          <button
            v-if="!isDisabled(user)"
            class="btn danger"
            @click="confirmAction('disable')"
          >
            禁用
          </button>
          <button v-else class="btn ok" @click="confirmAction('enable')">
            启用
          </button>
        </div>
      </header>

      <section class="detail-grid">
        <div class="stat-card">
          <span class="label">报告数</span>
          <span class="value">{{ user.report_count || 0 }}</span>
        </div>
        <div class="stat-card">
          <span class="label">日记数</span>
          <span class="value">{{ user.diary_count || 0 }}</span>
        </div>
        <div class="stat-card">
          <span class="label">注册时间</span>
          <span class="value-sm">{{ formatTime(user.created_at) }}</span>
        </div>
        <div class="stat-card">
          <span class="label">最后登录</span>
          <span class="value-sm">{{ formatTime(user.last_login_at) }}</span>
        </div>
      </section>

      <section class="block">
        <h3>用户 ID</h3>
        <code class="user-id">{{ user.id }}</code>
      </section>

      <section class="block" v-if="user.openid">
        <h3>OpenID</h3>
        <code class="user-id">{{ user.openid }}</code>
      </section>

      <section class="block" v-if="user.deleted_at">
        <h3>删除时间</h3>
        <p>{{ formatTime(user.deleted_at) }}</p>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from "vue";
import { useRoute } from "vue-router";
import adminApi from "@/config/adminApi";

const route = useRoute();
const user = ref<any | null>(null);
const loading = ref(false);
const error = ref("");

const avatarChar = computed(() => {
  const u = user.value;
  if (!u) return "👤";
  if (u.nickname) return u.nickname.charAt(0).toUpperCase();
  if (u.phone) return u.phone.slice(-2);
  return "👤";
});

async function load() {
  const id = route.params.id as string;
  if (!id) {
    error.value = "缺少用户 ID";
    return;
  }
  loading.value = true;
  error.value = "";
  user.value = null;
  try {
    const res = await adminApi.get(`/users/${id}`);
    if (res.data?.status === "success") {
      user.value = res.data.data;
    } else {
      error.value = res.data?.detail || "未找到该用户";
    }
  } catch (e: any) {
    if (e?.response?.status === 404) {
      error.value = "用户不存在";
    } else {
      error.value = e?.response?.data?.detail || "加载失败";
    }
  } finally {
    loading.value = false;
  }
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
  return s.slice(0, 19).replace("T", " ");
}

async function confirmAction(action: "enable" | "disable") {
  const verb = action === "disable" ? "禁用" : "启用";
  if (!confirm(`确认要${verb}该用户吗？`)) return;
  try {
    await adminApi.patch(`/users/${user.value.id}`, {
      disabled: action === "disable",
    });
    await load();
  } catch (e: any) {
    alert(e?.response?.data?.detail || `${verb}失败`);
  }
}

watch(() => route.params.id, load);
onMounted(load);
</script>

<style scoped>
.user-detail {
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
  gap: 22px;
}
.detail-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding-bottom: 18px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}
.avatar {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: linear-gradient(135deg, #f2a900, #ff9a8b);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 22px;
  font-weight: 700;
  flex-shrink: 0;
}
.info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.name {
  font-size: 18px;
  font-weight: 700;
  color: #1f2937;
  margin: 0;
}
.phone {
  font-size: 13px;
  color: #6b7280;
  margin: 0;
}
.status {
  align-self: flex-start;
  font-size: 11px;
  padding: 3px 10px;
  border-radius: 8px;
  font-weight: 600;
  margin-top: 4px;
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
.btn.danger {
  background: #dc2626;
  color: #fff;
}
.btn.ok {
  background: #16a34a;
  color: #fff;
}
.detail-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
}
.stat-card {
  background: #f9fafb;
  border-radius: 14px;
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.stat-card .label {
  font-size: 11px;
  color: #6b7280;
}
.stat-card .value {
  font-size: 22px;
  font-weight: 700;
  color: #1f2937;
}
.stat-card .value-sm {
  font-size: 13px;
  font-weight: 600;
  color: #1f2937;
}
.block h3 {
  font-size: 13px;
  font-weight: 700;
  color: #1f2937;
  margin: 0 0 8px;
}
.block p {
  font-size: 13px;
  color: #4b5563;
  margin: 0;
}
.user-id {
  display: inline-block;
  background: #f3f4f6;
  padding: 6px 10px;
  border-radius: 6px;
  font-family: monospace;
  font-size: 12px;
  color: #1f2937;
  word-break: break-all;
}
</style>