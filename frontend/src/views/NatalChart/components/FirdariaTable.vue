<template>
  <div class="firdaria-table-wrap">
    <div class="firdaria-meta">
      <span class="meta-item">
        <span class="meta-label">盘主类型</span>
        <span class="meta-value">{{ isDayChart ? "昼盘（日生）" : "夜盘（夜生）" }}</span>
      </span>
      <span class="meta-item">
        <span class="meta-label">当前年龄</span>
        <span class="meta-value">{{ currentAge.toFixed(1) }} 岁</span>
      </span>
      <span class="meta-item">
        <span class="meta-label">当前主运</span>
        <span class="meta-value accent">{{ currentLord }}</span>
      </span>
    </div>

    <div class="scroll">
      <table class="firdaria-table">
        <thead>
          <tr>
            <th>年龄段</th>
            <th>主运</th>
            <th>子运顺序</th>
            <th>状态</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(row, idx) in rows"
            :key="idx"
            :class="{ active: row.is_current, past: row.is_past, future: row.is_future }"
          >
            <td class="age-cell">
              <strong>{{ row.start_age }} – {{ row.end_age }} 岁</strong>
            </td>
            <td>
              <span class="lord-chip">{{ row.lord_zh }}</span>
            </td>
            <td class="sub-cell">
              <span v-for="(s, i) in row.sub_sequence" :key="i" class="sub-tag">
                {{ s }}
              </span>
            </td>
            <td>
              <span v-if="row.is_current" class="status current">● 当前</span>
              <span v-else-if="row.is_past" class="status past">已过</span>
              <span v-else class="status future">未来</span>
            </td>
          </tr>
          <tr v-if="!rows.length">
            <td colspan="4" class="empty">暂无法达周期数据</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{
  periods?: Array<any>;
  currentAge?: number;
  isDayChart?: boolean;
}>();

const PLANET_ZH: Record<string, string> = {
  SUN: "太阳", MOON: "月亮", MERCURY: "水星", VENUS: "金星",
  MARS: "火星", JUPITER: "木星", SATURN: "土星",
  URANUS: "天王星", NEPTUNE: "海王星", PLUTO: "冥王星",
  NORTH_NODE: "北交点", SOUTH_NODE: "南交点",
};

const CHALDEAN_ZH = ["土", "木", "火", "日", "金", "水", "月"];

const currentAge = computed(() => Number(props.currentAge || 0));
const isDayChart = computed(() => Boolean(props.isDayChart));

const rows = computed(() => {
  const list: Array<any> = [];
  let majorAccumulator: string[] = [];
  let lastMajor = "";

  for (const p of props.periods || []) {
    const lord = p.lord || "";
    const lordZh = PLANET_ZH[lord] || p.lord_zh || lord || "-";
    const subLord = p.sub_lord || "";
    const subZh = PLANET_ZH[subLord] || p.sub_lord_zh || subLord || "";

    if (lord !== lastMajor) {
      majorAccumulator = CHALDEAN_ZH.slice();
      lastMajor = lord;
    }

    if (p.is_node) {
      // 南北交点无子运
      list.push({
        start_age: p.start_age,
        end_age: p.end_age,
        lord_zh: lordZh,
        sub_sequence: ["—"],
        is_current: currentAge.value >= p.start_age && currentAge.value < p.end_age,
        is_past: currentAge.value >= p.end_age,
        is_future: currentAge.value < p.start_age,
      });
      continue;
    }

    // 记录本次子运：把第一个 subZh 标记为高亮
    const seq = majorAccumulator.map((s) => ({
      zh: s,
      highlight: s === subZh,
    }));

    list.push({
      start_age: p.start_age,
      end_age: p.end_age,
      lord_zh: lordZh,
      sub_sequence: seq,
      is_current: currentAge.value >= p.start_age && currentAge.value < p.end_age,
      is_past: currentAge.value >= p.end_age,
      is_future: currentAge.value < p.start_age,
    });
  }
  return list;
});

const currentLord = computed(() => {
  const cur = rows.value.find((r) => r.is_current);
  return cur?.lord_zh || "-";
});
</script>

<style scoped lang="less">
.firdaria-table-wrap {
  width: 100%;
}

.firdaria-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  padding: 14px 16px;
  background: linear-gradient(135deg, #1a1f35, #2a2f45);
  color: #d4af37;
  border-radius: 10px;
  margin-bottom: 16px;
}

.meta-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.meta-label {
  font-size: 11px;
  color: #94a3b8;
  letter-spacing: 0.06em;
}

.meta-value {
  font-size: 14px;
  font-weight: 600;
  color: #fef3c7;
}

.meta-value.accent {
  color: #f0c040;
  font-size: 16px;
}

.scroll {
  width: 100%;
  overflow-x: auto;
  background: #ffffff;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
}

.firdaria-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
  min-width: 720px;
}

.firdaria-table thead {
  background: #1a1f35;
  color: #d4af37;
}

.firdaria-table th {
  padding: 12px 10px;
  text-align: left;
  font-weight: 600;
  letter-spacing: 0.04em;
}

.firdaria-table td {
  padding: 12px 10px;
  border-bottom: 1px solid #f1f5f9;
  color: #334155;
  vertical-align: middle;
}

.firdaria-table tbody tr.past {
  background: #f8fafc;
  color: #94a3b8;
}

.firdaria-table tbody tr.active {
  background: linear-gradient(90deg, rgba(212, 175, 55, 0.18), rgba(212, 175, 55, 0.06));
  border-left: 3px solid #d4af37;
}

.firdaria-table tbody tr.active td {
  color: #1e293b;
  font-weight: 600;
}

.firdaria-table tbody tr.future td {
  color: #475569;
}

.age-cell strong {
  font-variant-numeric: tabular-nums;
}

.lord-chip {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 6px;
  background: #1a1f35;
  color: #d4af37;
  font-weight: 600;
  font-size: 12px;
}

.sub-cell {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.sub-tag {
  display: inline-block;
  width: 22px;
  height: 22px;
  line-height: 22px;
  text-align: center;
  border-radius: 4px;
  background: #f1f5f9;
  color: #475569;
  font-size: 12px;
  font-weight: 600;
}

.sub-tag.highlight {
  background: #d4af37;
  color: #1a1f35;
}

.status {
  font-size: 12px;
  font-weight: 600;
}

.status.current {
  color: #d4af37;
}

.status.past {
  color: #94a3b8;
}

.status.future {
  color: #475569;
}

.empty {
  text-align: center;
  color: #94a3b8;
  padding: 30px;
}
</style>