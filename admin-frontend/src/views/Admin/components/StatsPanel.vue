<template>
  <div class="stats">
    <div class="grid">
      <div class="card">
        <span class="label">总用户数</span>
        <span class="value">{{ stats?.total_users ?? "--" }}</span>
        <span class="hint">
          活跃 {{ stats?.active_users ?? "--" }} ·
          禁用 {{ stats?.disabled_users ?? "--" }}
        </span>
      </div>
      <div class="card">
        <span class="label">活跃用户 (7日)</span>
        <span class="value accent">{{ stats?.active_users_7d ?? "--" }}</span>
      </div>
      <div class="card">
        <span class="label">档案数</span>
        <span class="value">{{ stats?.total_profiles ?? "--" }}</span>
      </div>
      <div class="card">
        <span class="label">星语者报告</span>
        <span class="value">{{ stats?.total_reports ?? "--" }}</span>
      </div>
      <div class="card">
        <span class="label">星灵日记</span>
        <span class="value">{{ stats?.total_diary ?? "--" }}</span>
        <span class="hint">
          隐藏 {{ stats?.hidden_diary ?? 0 }} ·
          标记 {{ stats?.flagged_diary ?? 0 }}
        </span>
      </div>
      <div class="card">
        <span class="label">星语者咨询</span>
        <span class="value">{{ stats?.total_consultations ?? "--" }}</span>
      </div>
      <div class="card">
        <span class="label">花园签到</span>
        <span class="value">{{ stats?.total_checkins ?? "--" }}</span>
      </div>
      <div class="card">
        <span class="label">成长对话</span>
        <span class="value">{{ stats?.total_growth_convos ?? "--" }}</span>
      </div>
    </div>

    <div class="panel">
      <h3 class="panel-title">报告类型分布</h3>
      <div class="bar-list" v-if="stats?.reports_by_type">
        <div
          v-for="(count, key) in stats.reports_by_type"
          :key="key"
          class="bar-row"
        >
          <span class="bar-label">{{ key }}</span>
          <div class="bar-track">
            <div
              class="bar-fill"
              :style="{ width: barWidth(count) + '%' }"
            ></div>
          </div>
          <span class="bar-value">{{ count }}</span>
        </div>
        <div v-if="!hasReports" class="empty">暂无数据</div>
      </div>
    </div>

    <div class="row">
      <div class="panel">
        <h3 class="panel-title">用户注册趋势 (近14日)</h3>
        <SimpleBarChart :data="stats?.user_signup_trend || []" />
      </div>
      <div class="panel">
        <h3 class="panel-title">日记新增趋势 (近14日)</h3>
        <SimpleBarChart :data="stats?.diary_trend || []" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import SimpleBarChart from "./SimpleBarChart.vue";

defineProps<{ stats: any }>();

const hasReports = computed(() => {
  return true;
});

function barWidth(count: number) {
  const max = Math.max(
    ...Object.values(arguments[0] || {}) as number[],
    1,
  );
  return Math.round((count / max) * 100);
}
</script>

<style scoped>
.stats {
  display: flex;
  flex-direction: column;
  gap: 24px;
}
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 14px;
}
.card {
  background: #fff;
  border-radius: 18px;
  padding: 20px 18px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  border: 1px solid rgba(0, 0, 0, 0.04);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
}
.label {
  font-size: 12px;
  color: #6b7280;
  font-weight: 500;
}
.value {
  font-size: 28px;
  font-weight: 800;
  color: #1f2937;
  line-height: 1.2;
}
.value.accent {
  color: #f2a900;
}
.hint {
  font-size: 11px;
  color: #9ca3af;
}

.panel {
  background: #fff;
  border-radius: 18px;
  padding: 22px;
  border: 1px solid rgba(0, 0, 0, 0.04);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
}
.panel-title {
  font-size: 14px;
  font-weight: 700;
  color: #1f2937;
  margin: 0 0 16px;
}
.row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
  gap: 14px;
}
.bar-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.bar-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}
.bar-label {
  width: 100px;
  color: #4b5563;
  font-weight: 500;
}
.bar-track {
  flex: 1;
  height: 10px;
  border-radius: 4px;
  background: rgba(0, 0, 0, 0.04);
  overflow: hidden;
}
.bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #f2a900, #ff9a8b);
  border-radius: 4px;
}
.bar-value {
  width: 40px;
  text-align: right;
  font-weight: 600;
  color: #1f2937;
}
.empty {
  text-align: center;
  color: #9ca3af;
  font-size: 13px;
  padding: 16px;
}
</style>
