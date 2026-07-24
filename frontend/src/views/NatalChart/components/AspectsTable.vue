<template>
  <div class="aspects-table-wrap">
    <table class="aspects-table">
      <thead>
        <tr>
          <th>星体组合</th>
          <th>相位</th>
          <th>度数</th>
          <th>容许度</th>
          <th>性质</th>
          <th>解读</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(row, idx) in rows" :key="idx">
          <td>
            <span class="planet-pair">
              <span>{{ row.planet1_zh }}</span>
              <span class="dot">·</span>
              <span>{{ row.planet2_zh }}</span>
            </span>
          </td>
          <td>{{ row.type_zh }}</td>
          <td class="num">{{ row.degree }}</td>
          <td class="num">{{ row.orb }}</td>
          <td>
            <span :class="['nature-chip', row.nature]">
              <span class="dot-color"></span>{{ row.nature_label }}
            </span>
          </td>
          <td class="desc-cell">{{ row.description }}</td>
        </tr>
        <tr v-if="!rows.length">
          <td colspan="6" class="empty">暂无相位数据</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{
  aspects?: Array<any>;
}>();

const PLANET_ZH: Record<string, string> = {
  SUN: "太阳", MOON: "月亮", MERCURY: "水星", VENUS: "金星",
  MARS: "火星", JUPITER: "木星", SATURN: "土星",
  URANUS: "天王星", NEPTUNE: "海王星", PLUTO: "冥王星",
  NORTH_NODE: "北交点", SOUTH_NODE: "南交点",
};

const NATURE_LABEL: Record<string, string> = {
  supportive: "柔和",
  challenging: "挑战",
  neutral: "中性",
};

const NATURE_DESC: Record<string, string> = {
  supportive: "能量流动顺畅，容易相互成就",
  challenging: "产生张力，需要主动调和",
  neutral: "中性互动，主题叠加",
};

function planetKey(text: string): string | null {
  for (const [k, v] of Object.entries(PLANET_ZH)) {
    if (text.includes(v)) return k;
  }
  return null;
}

const rows = computed(() => {
  const list: Array<any> = [];
  const aspects = props.aspects || [];

  for (const asp of aspects) {
    const title = asp.title || "";
    const nature = asp.nature || "neutral";
    const parts = title.split(" ");
    let p1Key = asp.from || asp.planet1 || null;
    let p2Key = asp.to || asp.planet2 || null;

    if (!p1Key || !p2Key) {
      if (parts.length >= 3) {
        p1Key = planetKey(parts[0] ?? "");
        p2Key = planetKey(parts[2] ?? "");
      }
    }

    const p1Zh = p1Key && PLANET_ZH[p1Key] ? PLANET_ZH[p1Key] : parts[0] || "-";
    const p2Zh = p2Key && PLANET_ZH[p2Key] ? PLANET_ZH[p2Key] : parts[2] || "-";

    const typeZh = asp.type_zh || parts[1] || "-";
    const degree = asp.degree || (typeof asp.strength === "number" ? `${asp.strength.toFixed(2)}°` : "-");
    const orb = asp.orb || (typeof asp.orb === "number" ? `${asp.orb.toFixed(2)}°` : "-");
    const description = asp.description || asp.summary || NATURE_DESC[nature] || "";

    list.push({
      planet1: p1Key || "",
      planet1_zh: p1Zh,
      planet2: p2Key || "",
      planet2_zh: p2Zh,
      type: asp.type || "",
      type_zh: typeZh,
      degree,
      orb,
      nature,
      nature_label: NATURE_LABEL[nature] || nature,
      description,
    });
  }
  return list;
});
</script>

<style scoped lang="less">
.aspects-table-wrap {
  width: 100%;
  overflow-x: auto;
}

.aspects-table {
  width: 100%;
  border-collapse: collapse;
  background: #ffffff;
  border-radius: 10px;
  overflow: hidden;
  font-size: 13px;
  min-width: 640px;
}

.aspects-table thead {
  background: #1a1f35;
  color: #d4af37;
}

.aspects-table th {
  padding: 12px 10px;
  text-align: left;
  font-weight: 600;
  letter-spacing: 0.04em;
}

.aspects-table td {
  padding: 12px 10px;
  border-bottom: 1px solid #f1f5f9;
  color: #334155;
  vertical-align: middle;
}

.aspects-table tbody tr:hover {
  background: #faf8f2;
}

.planet-pair {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  color: #1e293b;
}

.dot {
  color: #94a3b8;
}

.num {
  font-variant-numeric: tabular-nums;
  color: #475569;
}

.nature-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
  background: #f1f5f9;
  color: #334155;
}

.nature-chip.supportive {
  background: rgba(74, 222, 128, 0.18);
  color: #166534;
}

.nature-chip.challenging {
  background: rgba(248, 113, 113, 0.18);
  color: #991b1b;
}

.nature-chip.neutral {
  background: rgba(148, 163, 184, 0.22);
  color: #475569;
}

.dot-color {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.nature-chip.supportive .dot-color { background: #22c55e; }
.nature-chip.challenging .dot-color { background: #ef4444; }
.nature-chip.neutral .dot-color { background: #94a3b8; }

.desc-cell {
  color: #475569;
  line-height: 1.6;
  max-width: 320px;
}

.empty {
  text-align: center;
  color: #94a3b8;
  padding: 30px;
}
</style>