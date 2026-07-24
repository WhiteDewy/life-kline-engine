<template>
  <div class="report-detail">
    <div class="breadcrumb">
      <router-link to="/admin/reports" class="back">← 返回报告列表</router-link>
    </div>

    <div v-if="loading" class="loading">加载中...</div>

    <div v-else-if="error" class="error">{{ error }}</div>

    <article v-else-if="meta" class="detail-card">
      <header class="detail-header">
        <div class="info">
          <h2 class="title">{{ meta.analysis_type }} 报告</h2>
          <p class="sub">
            用户：{{ meta.nickname || meta.phone || meta.user_id || "—" }}
          </p>
          <p class="dim">{{ formatTime(meta.created_at) }}</p>
        </div>
        <div class="actions">
          <button class="btn danger" @click="confirmDelete">删除</button>
        </div>
      </header>

      <section class="meta-grid">
        <div class="stat">
          <span class="label">报告 ID</span>
          <code class="value-mono">{{ meta.id }}</code>
        </div>
        <div class="stat">
          <span class="label">用户 ID</span>
          <code class="value-mono">{{ meta.user_id || "—" }}</code>
        </div>
        <div class="stat">
          <span class="label">档案 ID</span>
          <code class="value-mono">{{ meta.profile_id || "—" }}</code>
        </div>
        <div class="stat">
          <span class="label">类型</span>
          <span class="value">{{ meta.analysis_type }}</span>
        </div>
      </section>

      <section v-if="meta.kline_summary" class="block">
        <h3>报告摘要</h3>
        <p class="summary">{{ meta.kline_summary }}</p>
      </section>

      <section class="block">
        <h3>报告内容预览</h3>
        <div v-if="reportJson" class="json-preview">
          <pre>{{ reportJson }}</pre>
        </div>
        <div v-else class="empty">无详细报告内容（可能为概要记录或已删除 JSON 文件）</div>
      </section>
    </article>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import adminApi from "@/config/adminApi";

const route = useRoute();
const router = useRouter();

const meta = ref<any | null>(null);
const reportBody = ref<any | null>(null);
const loading = ref(false);
const error = ref("");

const reportJson = computed(() => {
  if (!reportBody.value) return "";
  try {
    return JSON.stringify(reportBody.value, null, 2);
  } catch {
    return String(reportBody.value);
  }
});

async function load() {
  const id = route.params.id as string;
  if (!id) {
    error.value = "缺少报告 ID";
    return;
  }
  loading.value = true;
  error.value = "";
  meta.value = null;
  reportBody.value = null;
  try {
    const res = await adminApi.get(`/reports/${id}`);
    if (res.data?.status === "success") {
      meta.value = res.data.data?.meta || res.data.data;
      reportBody.value = res.data.data?.report || res.data.data?.report_data || null;
    } else {
      error.value = res.data?.detail || "未找到该报告";
    }
  } catch (e: any) {
    if (e?.response?.status === 404) {
      error.value = "报告不存在";
    } else {
      error.value = e?.response?.data?.detail || "加载失败";
    }
  } finally {
    loading.value = false;
  }
}

function formatTime(s: string) {
  return (s || "").slice(0, 19).replace("T", " ");
}

async function confirmDelete() {
  if (!meta.value) return;
  if (!confirm(`确认删除报告 ${meta.value.id.slice(0, 12)} 吗？此操作不可恢复！`))
    return;
  try {
    await adminApi.delete(`/reports/${meta.value.id}`);
    router.push("/admin/reports");
  } catch (e: any) {
    alert(e?.response?.data?.detail || "删除失败");
  }
}

watch(() => route.params.id, load);
onMounted(load);
</script>

<style scoped>
.report-detail {
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
.detail-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}
.title {
  font-size: 18px;
  font-weight: 700;
  color: #1f2937;
  margin: 0 0 6px;
}
.sub {
  font-size: 13px;
  color: #4b5563;
  margin: 0 0 4px;
}
.dim {
  font-size: 12px;
  color: #9ca3af;
  margin: 0;
}
.actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
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
.meta-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 12px;
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
.value {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
}
.block h3 {
  font-size: 13px;
  font-weight: 700;
  color: #1f2937;
  margin: 0 0 8px;
}
.summary {
  font-size: 14px;
  color: #374151;
  line-height: 1.7;
  margin: 0;
}
.json-preview {
  background: #f9fafb;
  border-radius: 12px;
  padding: 14px;
  max-height: 480px;
  overflow: auto;
}
.json-preview pre {
  margin: 0;
  font-family: monospace;
  font-size: 12px;
  color: #1f2937;
  white-space: pre-wrap;
  word-break: break-word;
}
.empty {
  padding: 16px;
  background: #f9fafb;
  border-radius: 10px;
  font-size: 13px;
  color: #6b7280;
  text-align: center;
}
</style>