<template>
  <div class="page">
    <section class="wrap">
      <h2>我的报告</h2>

      <div v-if="!loggedIn" class="empty">
        <p>请先登录查看报告历史</p>
        <el-button type="primary" round @click="$emit('login')">登录</el-button>
      </div>

      <div v-else-if="loading" class="empty">
        <p>加载中...</p>
      </div>

      <div v-else-if="reports.length === 0" class="empty">
        <p>还没有生成过报告</p>
        <el-button type="primary" round @click="goExplore">去生成第一份星盘</el-button>
      </div>

      <div v-else class="list">
        <div
          v-for="r in reports"
          :key="r.id"
          class="item"
          @click="openReport(r)"
        >
          <span class="type">{{ r.analysis_type === "natal_blueprint" ? "本命蓝图" : r.analysis_type === "phase_navigation" ? "阶段导航" : r.analysis_type }}</span>
          <span class="date">{{ r.created_at?.slice(0, 10) }}</span>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { useAuth } from "@/utils/auth";

const router = useRouter();
const { isLoggedIn, getHistory } = useAuth();
const reports = ref<any[]>([]);
const loading = ref(false);
const loggedIn = isLoggedIn;

async function loadHistory() {
  if (!isLoggedIn.value) return;
  loading.value = true;
  try {
    reports.value = await getHistory();
  } catch (e) {
    console.error(e);
  }
  loading.value = false;
}

function openReport(r: any) {
  router.push({ name: "report", params: { id: r.id } });
}

function goExplore() {
  router.push({ name: "analysis", params: { type: "natal_blueprint" } });
}

onMounted(loadHistory);
</script>

<style scoped lang="less">
.page {
  min-height: calc(100vh - var(--h-footer));
  padding: 40px 20px;
  background: linear-gradient(180deg, #020617 0%, #0a1122 100%);
}
.wrap {
  max-width: 640px;
  margin: 0 auto;
}
h2 {
  color: var(--text-primary);
  font-size: 28px;
  margin: 0 0 24px;
}
.empty {
  text-align: center;
  padding: 60px 0;
  color: var(--text-tertiary);
}
.empty p {
  margin: 0 0 16px;
}
.list {
  display: grid;
  gap: 10px;
}
.item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  background: rgba(15, 23, 42, 0.55);
  cursor: pointer;
  transition: border-color 0.2s;
}
.item:hover {
  border-color: rgba(212, 175, 55, 0.25);
}
.type {
  color: var(--text-secondary);
  font-weight: 600;
}
.date {
  color: var(--text-tertiary);
  font-size: 13px;
}
</style>
