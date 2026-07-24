<template>
  <div class="zodiac-table-wrap">
    <table class="zodiac-table">
      <thead>
        <tr>
          <th>星体</th>
          <th>落座</th>
          <th>度数</th>
          <th>状态</th>
          <th>解读</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="row in rows" :key="row.planet">
          <td>
            <span class="planet-glyph">{{ row.glyph }}</span>
            <span class="planet-label">{{ row.planet_zh }}</span>
          </td>
          <td class="sign-cell">{{ row.sign_zh }}</td>
          <td class="degree-cell">{{ row.degree }}</td>
          <td>
            <span :class="['state-chip', row.state]">
              {{ row.icon }} {{ row.state_zh }}
            </span>
          </td>
          <td class="meaning-cell">{{ row.meaning }}</td>
        </tr>
        <tr v-if="!rows.length">
          <td colspan="5" class="empty">暂无数据</td>
        </tr>
      </tbody>
    </table>

    <div class="legend-strip">
      <span class="legend-item"><span class="icon">🏠</span>庙旺（入庙）</span>
      <span class="legend-item"><span class="icon">✨</span>擢升（旺势）</span>
      <span class="legend-item"><span class="icon">😰</span>失势</span>
      <span class="legend-item"><span class="icon">💀</span>落陷</span>
      <span class="legend-item"><span class="icon">🔒</span>弱势 / 游走</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{ planets?: Record<string, any> }>();

const PLANET_META: Record<string, { zh: string; glyph: string }> = {
  SUN: { zh: "太阳", glyph: "☉" },
  MOON: { zh: "月亮", glyph: "☽" },
  MERCURY: { zh: "水星", glyph: "☿" },
  VENUS: { zh: "金星", glyph: "♀" },
  MARS: { zh: "火星", glyph: "♂" },
  JUPITER: { zh: "木星", glyph: "♃" },
  SATURN: { zh: "土星", glyph: "♄" },
  URANUS: { zh: "天王星", glyph: "♅" },
  NEPTUNE: { zh: "海王星", glyph: "♆" },
  PLUTO: { zh: "冥王星", glyph: "♇" },
};

const ORDER = ["SUN", "MOON", "MERCURY", "VENUS", "MARS", "JUPITER", "SATURN", "URANUS", "NEPTUNE", "PLUTO"];

const STATE_META: Record<string, { icon: string; zh: string; cls: string }> = {
  domicile: { icon: "🏠", zh: "庙旺", cls: "domicile" },
  exaltation: { icon: "✨", zh: "擢升", cls: "exaltation" },
  detriment: { icon: "💀", zh: "落陷", cls: "detriment" },
  fall: { icon: "😰", zh: "失势", cls: "fall" },
  peregrine: { icon: "🔒", zh: "弱势", cls: "peregrine" },
  auxiliary: { icon: "🔒", zh: "附加点", cls: "peregrine" },
};

const MEANING_HINTS: Record<string, string> = {
  domicile: "得位有力，本位能量饱满",
  exaltation: "最被推崇的状态，能力易被高估",
  detriment: "与环境摩擦，需额外努力补足",
  fall: "能量受压，需要靠经验累积化解",
  peregrine: "中性状态，需借助与其他星的相位运作",
  auxiliary: "辅助参考点",
};

function formatDegree(deg: number): string {
  if (typeof deg !== "number" || Number.isNaN(deg)) return "-";
  const total = Math.min(Math.round(Math.abs(deg) * 60), 29 * 60 + 59);
  const d = Math.floor(total / 60);
  const m = total % 60;
  return `${d}°${String(m).padStart(2, "0")}′`;
}

const rows = computed(() => {
  const planets = props.planets || {};
  const list: Array<any> = [];
  for (const key of ORDER) {
    const p = planets[key];
    if (!p) continue;
    const meta = PLANET_META[key];
    if (!meta) continue;
    const state = (p.dignity || "peregrine") as string;
    const stateMeta = STATE_META[state] || STATE_META.peregrine!;
    const signZh = p.sign_label || p.sign || "-";
    const meaning =
      (p.gift && String(p.gift)) ||
      MEANING_HINTS[state] ||
      `${meta.zh}落于${signZh}，体现其核心能量如何运作。`;
    list.push({
      planet: key,
      planet_zh: meta.zh,
      glyph: meta.glyph,
      sign_zh: signZh,
      degree: formatDegree(p.degree),
      state: stateMeta.cls,
      state_zh: p.dignity_label || stateMeta.zh,
      icon: stateMeta.icon,
      meaning,
    });
  }
  return list;
});
</script>

<style scoped lang="less">
.zodiac-table-wrap {
  width: 100%;
}

.zodiac-table {
  width: 100%;
  border-collapse: collapse;
  background: #ffffff;
  border-radius: 10px;
  overflow: hidden;
  font-size: 13px;
}

.zodiac-table thead {
  background: #1a1f35;
  color: #d4af37;
}

.zodiac-table th {
  padding: 12px 10px;
  text-align: left;
  font-weight: 600;
  letter-spacing: 0.04em;
}

.zodiac-table td {
  padding: 12px 10px;
  border-bottom: 1px solid #f1f5f9;
  color: #334155;
  vertical-align: middle;
}

.zodiac-table tbody tr:hover {
  background: #faf8f2;
}

.planet-glyph {
  display: inline-block;
  width: 28px;
  height: 28px;
  line-height: 28px;
  text-align: center;
  border-radius: 50%;
  background: #1a1f35;
  color: #d4af37;
  font-size: 16px;
  margin-right: 8px;
  vertical-align: middle;
}

.planet-label {
  font-weight: 600;
  color: #1e293b;
}

.sign-cell {
  font-weight: 600;
  color: #1e293b;
}

.degree-cell {
  font-variant-numeric: tabular-nums;
  color: #475569;
}

.state-chip {
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

.state-chip.domicile {
  background: rgba(81, 122, 89, 0.15);
  color: #2f5e3f;
}

.state-chip.exaltation {
  background: rgba(212, 175, 55, 0.18);
  color: #8a6a18;
}

.state-chip.detriment {
  background: rgba(161, 84, 66, 0.18);
  color: #7a4539;
}

.state-chip.fall {
  background: rgba(190, 100, 80, 0.18);
  color: #8a3e30;
}

.state-chip.peregrine {
  background: rgba(100, 116, 139, 0.18);
  color: #475569;
}

.meaning-cell {
  color: #475569;
  line-height: 1.6;
  max-width: 320px;
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

.legend-item .icon {
  margin-right: 4px;
}
</style>