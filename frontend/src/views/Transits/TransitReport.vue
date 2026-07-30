<template>
  <div class="transit-page">
    <button class="back-btn" @click="$router.back()">← 返回</button>
    <h1 class="page-title">{{ title }}</h1>
    <p class="page-desc">{{ desc }}</p>

    <div v-if="loading" class="loading">⏳ 星语者正在解读行运...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="report" class="report markdown-body" v-html="renderedReport"></div>
    <div v-else class="empty">
      <p>需要星盘报告才能生成行运解读。</p>
      <button class="btn" @click="$router.push('/')">去创建星盘</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import { apiClient } from "@/config/api";

const props = defineProps<{ period: "yearly" | "monthly" | "weekly" }>();

const labels: Record<string, { title: string; desc: string }> = {
  yearly: { title: "年运报告", desc: "星语者基于当前行运解读你未来一年的关键主题" },
  monthly: { title: "月运报告", desc: "星语者基于月返+行运解读你未来一个月的节奏" },
  weekly: { title: "周运报告", desc: "星语者基于本周行运给你一周的提醒" },
};

const info = labels[props.period] || { title: "行运报告", desc: "" };
const { title, desc } = info;

const route = useRoute();
const report = ref("");
const loading = ref(false);
const error = ref("");

const renderedReport = computed(() =>
  report.value.replace(/\n/g, "<br>").replace(/## (.+)/g, "<h3>$1</h3>").replace(/- (.+)/g, "· $1")
);

onMounted(async () => {
  const rid = (route.params.reportId as string) || (route.query.rid as string);
  if (!rid) return;
  loading.value = true;
  try {
    const res = await apiClient.post(`/transits/${rid}/report`, { period: props.period });
    report.value = res.data?.data?.report || "";
  } catch (e: any) {
    error.value = e?.response?.data?.detail || "加载失败";
  }
  loading.value = false;
});
</script>

<style scoped>
.transit-page { max-width: 720px; margin: 0 auto; padding: 40px 20px; color: #e8e0d0; }
.page-title { font-size: 28px; margin: 16px 0 8px; }
.page-desc { color: #a89880; margin-bottom: 24px; }
.loading, .error, .empty { text-align: center; padding: 60px 20px; color: #a89880; }
.back-btn { background: none; border: none; color: var(--gold); cursor: pointer; font-size: 14px; }
.btn { margin-top: 16px; padding: 10px 24px; border-radius: 20px; border: 1px solid var(--gold); background: rgba(212,175,85,0.1); color: var(--gold); cursor: pointer; }
.report { line-height: 2; font-size: 16px; }
.report :deep(h3) { margin-top: 28px; color: var(--gold); }
</style>
