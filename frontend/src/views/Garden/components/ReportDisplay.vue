<template>
  <div class="report-display" v-if="report">
    <div class="rd-header">
      <h3 class="rd-title">🔮 星语者解读报告</h3>
      <p class="rd-subtitle">{{ report.question_label }}</p>
    </div>

    <!-- 锚定 -->
    <section class="rd-section" v-if="report.anchor_summary">
      <h4 class="rd-section-title">📌 问题锚定</h4>
      <div class="rd-text">{{ report.anchor_summary }}</div>
    </section>

    <!-- 情境 -->
    <section class="rd-section" v-if="report.scenario_summary">
      <h4 class="rd-section-title">💬 你的情境</h4>
      <div class="rd-text">{{ report.scenario_summary }}</div>
    </section>

    <!-- 星盘解读 -->
    <section class="rd-section" v-if="report.chart_reading">
      <h4 class="rd-section-title">🌟 星盘解读</h4>
      <div class="rd-text" v-html="formatText(report.chart_reading)"></div>
    </section>

    <!-- 证据 -->
    <section class="rd-section" v-if="report.evidence?.length">
      <h4 class="rd-section-title">📋 星盘证据</h4>
      <div class="rd-evidence-list">
        <div v-for="e in report.evidence" :key="e" class="rd-evid-item">{{ e }}</div>
      </div>
    </section>

    <!-- 边界提示 -->
    <section class="rd-section rd-section--notes" v-if="report.boundary_notes?.length">
      <h4 class="rd-section-title">⚠️ 温馨提示</h4>
      <div v-for="(n, i) in report.boundary_notes" :key="i" class="rd-note">
        {{ n }}
      </div>
    </section>

    <div class="rd-actions">
      <button class="rd-action-btn" @click="$emit('close')">返回花园</button>
      <button class="rd-action-btn rd-action-btn--primary" @click="$emit('save')">
        保存报告
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { ConsultationReport } from "@/utils/types";

defineProps<{
  report: ConsultationReport | null;
}>();

defineEmits<{
  close: [];
  save: [];
}>();

function formatText(text: string): string {
  return text
    .replace(/\n\n/g, "</p><p>")
    .replace(/\n/g, "<br>")
    .replace(/^/, "<p>")
    .replace(/$/, "</p>");
}
</script>

<style scoped lang="less">
.report-display {
  padding: 0 4px;
}
.rd-header {
  text-align: center; margin-bottom: 24px;
}
.rd-title { font-size: 22px; font-weight: 700; color: #4a3728; margin: 0 0 4px; }
.rd-subtitle { font-size: 14px; color: #8b7355; margin: 0; }

.rd-section {
  margin-bottom: 20px;
  padding: 16px 18px;
  border-radius: 16px;
  background: rgba(255,255,255,0.7);
  border: 1px solid rgba(0,0,0,0.04);
}
.rd-section--notes {
  background: rgba(255,220,200,0.15);
  border-color: rgba(255,154,139,0.15);
}
.rd-section-title {
  font-size: 14px; font-weight: 700; color: #4a3728; margin: 0 0 10px;
}
.rd-text {
  font-size: 14px; color: #4a3728; line-height: 1.8;
}
.rd-text :deep(p) { margin: 0 0 8px; }
.rd-text :deep(br) { display: block; content: ''; margin-top: 4px; }
.rd-evidence-list {
  display: flex; flex-direction: column; gap: 6px;
}
.rd-evid-item {
  font-size: 13px; color: #8b7355; padding: 6px 12px;
  border-radius: 10px; background: rgba(255,154,139,0.06);
}
.rd-note {
  font-size: 12px; color: #8b7355; line-height: 1.6; margin-bottom: 6px;
}

.rd-actions {
  display: flex; gap: 12px; justify-content: center; margin-top: 24px;
}
.rd-action-btn {
  padding: 12px 28px; border-radius: 18px;
  border: 1px solid rgba(0,0,0,0.1);
  background: rgba(255,255,255,0.7);
  font-size: 14px; font-weight: 600; color: #4a3728;
  cursor: pointer; font-family: inherit; transition: all 0.2s;
}
.rd-action-btn--primary {
  background: linear-gradient(135deg, #f0b8a0, #e8a890);
  color: #fff; border: none;
}
.rd-action-btn:hover { transform: translateY(-1px); }
</style>
