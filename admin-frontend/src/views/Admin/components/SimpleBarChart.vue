<template>
  <div class="chart">
    <div class="bars">
      <div
        v-for="(d, i) in data"
        :key="i"
        class="bar-wrap"
        :title="`${d.date}: ${d.count}`"
      >
        <div
          class="bar"
          :style="{ height: barHeight(d.count) + '%' }"
        ></div>
        <span class="lbl">{{ d.date.slice(5) }}</span>
      </div>
    </div>
    <div v-if="data.length === 0" class="empty">暂无数据</div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{ data: Array<{ date: string; count: number }> }>();

const max = computed(() =>
  Math.max(1, ...props.data.map((d) => d.count)),
);

function barHeight(count: number) {
  if (!max.value) return 0;
  return Math.round((count / max.value) * 100);
}
</script>

<style scoped>
.chart {
  padding: 4px 0;
}
.bars {
  display: flex;
  align-items: flex-end;
  height: 140px;
  gap: 6px;
}
.bar-wrap {
  flex: 1;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  align-items: center;
  gap: 4px;
}
.bar {
  width: 100%;
  background: linear-gradient(180deg, #f2a900, #ff9a8b);
  border-radius: 6px 6px 0 0;
  min-height: 4px;
  transition: height 0.4s;
}
.lbl {
  font-size: 10px;
  color: #9ca3af;
}
.empty {
  text-align: center;
  color: #9ca3af;
  font-size: 13px;
  padding: 32px 0;
}
</style>
