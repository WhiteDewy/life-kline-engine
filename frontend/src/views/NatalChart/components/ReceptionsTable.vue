<template>
  <div class="receptions-table-wrap">
    <table class="receptions-table">
      <thead>
        <tr>
          <th>接纳方向</th>
          <th>类型</th>
          <th>说明</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(row, idx) in rows" :key="idx">
          <td>
            <span class="direction">
              <span class="from">{{ row.from_zh }}</span>
              <span class="arrow">→</span>
              <span class="to">{{ row.to_zh }}</span>
            </span>
          </td>
          <td>
            <span :class="['type-chip', row.type]">
              <span class="icon">{{ row.icon }}</span>{{ row.type_zh }}
            </span>
          </td>
          <td class="desc-cell">{{ row.description }}</td>
        </tr>
        <tr v-if="!rows.length">
          <td colspan="3" class="empty">暂无接纳/互溶数据</td>
        </tr>
      </tbody>
    </table>

    <div class="legend-strip">
      <span class="legend-item"><span class="icon">🔄</span>互溶（双向接管能量）</span>
      <span class="legend-item"><span class="icon">↪</span>庙宫接纳（单方借力）</span>
      <span class="legend-item"><span class="icon">✨</span>擢升（最被推崇的状态）</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{ receptions?: Array<any> }>();

const TYPE_META: Record<string, { icon: string; zh: string; cls: string }> = {
  reception: { icon: "↪", zh: "庙宫接纳", cls: "reception" },
  mutual_reception: { icon: "🔄", zh: "互溶", cls: "mutual" },
  exaltation: { icon: "✨", zh: "擢升", cls: "exaltation" },
};

const rows = computed(() => {
  const list: Array<any> = [];
  for (const r of props.receptions || []) {
    const type = (r.type || "reception") as string;
    const meta = TYPE_META[type] || TYPE_META.reception!;
    list.push({
      from: r.from || "",
      from_zh: r.from_zh || r.from || "-",
      to: r.to || "",
      to_zh: r.to_zh || r.to || "-",
      type: meta.cls,
      type_zh: r.type_zh || meta.zh,
      icon: meta.icon,
      description: r.description || "",
    });
  }
  return list;
});
</script>

<style scoped lang="less">
.receptions-table-wrap {
  width: 100%;
}

.receptions-table {
  width: 100%;
  border-collapse: collapse;
  background: #ffffff;
  border-radius: 10px;
  overflow: hidden;
  font-size: 13px;
}

.receptions-table thead {
  background: #1a1f35;
  color: #d4af37;
}

.receptions-table th {
  padding: 12px 10px;
  text-align: left;
  font-weight: 600;
  letter-spacing: 0.04em;
}

.receptions-table td {
  padding: 12px 10px;
  border-bottom: 1px solid #f1f5f9;
  color: #334155;
  vertical-align: middle;
}

.receptions-table tbody tr:hover {
  background: #faf8f2;
}

.direction {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #1e293b;
}

.from { color: #475569; }
.to { color: #1e293b; }
.arrow { color: #d4af37; font-size: 16px; }

.type-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
  background: #f1f5f9;
  color: #334155;
}

.type-chip.mutual {
  background: rgba(212, 175, 55, 0.2);
  color: #7a5a14;
}

.type-chip.reception {
  background: rgba(96, 165, 250, 0.18);
  color: #1d4ed8;
}

.type-chip.exaltation {
  background: rgba(74, 222, 128, 0.18);
  color: #166534;
}

.icon {
  font-size: 14px;
}

.desc-cell {
  color: #475569;
  line-height: 1.6;
}

.empty {
  text-align: center;
  color: #94a3b8;
  padding: 30px;
}

.legend-strip {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  margin-top: 16px;
  padding: 10px 14px;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  font-size: 12px;
  color: #64748b;
}
</style>