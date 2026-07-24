<template>
  <div class="report-history">
    <div class="rh-header">
      <button class="back-btn" @click="$emit('close')">← 返回花园</button>
      <h3 class="rh-title">📜 历史报告</h3>
    </div>

    <ReportFilters
      :categories="categories"
      :active-filter="activeFilter"
      @filter="activeFilter = $event"
    />

    <div v-if="loading" class="rh-empty">加载中...</div>

    <div v-else-if="!reports.length" class="rh-empty">
      <div class="rh-empty-icon">🌱</div>
      <p>还没有报告，去花园里探索吧</p>
    </div>

    <div v-else class="rh-list">
      <div
        v-for="r in filteredReports"
        :key="r.id"
        class="rh-item"
        @click="$emit('view-report', r.id)"
      >
        <div class="rh-item-top">
          <span class="rh-item-cat">{{ r.category_label }}</span>
          <span class="rh-item-date">{{ formatDate(r.created_at) }}</span>
        </div>
        <div class="rh-item-question">{{ r.question_label }}</div>
        <div class="rh-item-summary">{{ r.summary }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { GardenCategory, ConsultationReportItem } from "@/utils/types";
import ReportFilters from "./ReportFilters.vue";

const props = defineProps<{
  reports: ConsultationReportItem[];
  categories: GardenCategory[];
  loading: boolean;
  activeFilter: string;
}>();

const emit = defineEmits<{
  "view-report": [id: string];
  "update:activeFilter": [f: string];
  close: [];
}>();

const filteredReports = computed(() => {
  if (!props.activeFilter) return props.reports;
  return props.reports.filter((r) => r.category === props.activeFilter);
});

function formatDate(iso: string): string {
  if (!iso) return "";
  return iso.slice(0, 10);
}
</script>

<style scoped lang="less">
.report-history { padding: 0 4px; }
.rh-header { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.back-btn { padding: 6px 14px; border-radius: 14px; border: 1px solid rgba(0,0,0,0.08); background: rgba(255,255,255,0.6); font-size: 13px; font-weight: 600; color: #8b7355; cursor: pointer; font-family: inherit; }
.rh-title { font-size: 20px; font-weight: 700; color: #4a3728; margin: 0; }
.rh-empty { text-align: center; padding: 60px 20px; color: #8b7355; font-size: 14px; }
.rh-empty-icon { font-size: 40px; margin-bottom: 12px; }
.rh-list { display: flex; flex-direction: column; gap: 10px; }
.rh-item { padding: 14px 16px; border-radius: 14px; background: rgba(255,255,255,0.65); border: 1px solid rgba(0,0,0,0.05); cursor: pointer; transition: all 0.2s; }
.rh-item:hover { background: rgba(255,255,255,0.85); transform: translateX(3px); }
.rh-item-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }
.rh-item-cat { font-size: 11px; font-weight: 600; color: #ff9a8b; background: rgba(255,154,139,0.1); padding: 2px 10px; border-radius: 8px; }
.rh-item-date { font-size: 11px; color: #a89880; }
.rh-item-question { font-size: 14px; font-weight: 600; color: #4a3728; margin-bottom: 4px; }
.rh-item-summary { font-size: 12px; color: #8b7355; line-height: 1.4; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
</style>
