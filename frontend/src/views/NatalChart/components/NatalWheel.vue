<template>
  <div class="natal-wheel-wrap">
    <div class="wheel-toolbar">
      <label class="toggle">
        <input type="checkbox" v-model="showAspects" />
        <span>显示相位线</span>
      </label>
      <span class="legend">
        <span class="dot dot-support"></span> 柔和
        <span class="dot dot-challenge"></span> 挑战
        <span class="dot dot-neutral"></span> 中性
      </span>
    </div>

    <svg
      :viewBox="`0 0 ${size} ${size}`"
      :width="size"
      :height="size"
      class="chart-svg"
      xmlns="http://www.w3.org/2000/svg"
    >
      <defs>
        <filter id="glowGold">
          <feGaussianBlur stdDeviation="2" result="blur" />
          <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
        </filter>
        <radialGradient id="bgGradGold" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stop-color="#1a1f35" />
          <stop offset="100%" stop-color="#0a0e1a" />
        </radialGradient>
      </defs>

      <!-- 底盘 -->
      <rect :x="2" :y="2" :width="size-4" :height="size-4" rx="14" class="chart-frame" />
      <circle :cx="cx" :cy="cy" :r="outerR" fill="url(#bgGradGold)" />

      <!-- 星座色带 -->
      <g v-for="(seg, i) in signSegments" :key="'sign-' + i">
        <path :d="seg.path" :class="['sign-band', seg.element]" />
        <text
          :x="seg.symbolX" :y="seg.symbolY"
          class="sign-symbol"
          text-anchor="middle" dominant-baseline="middle"
        >{{ seg.symbol }}</text>
      </g>

      <!-- 内圈 -->
      <circle :cx="cx" :cy="cy" :r="ringR" class="inner-ring" />

      <!-- 宫位线 -->
      <line v-for="(h, i) in houseLines" :key="'hline-'+i"
        :x1="h.x1" :y1="h.y1" :x2="h.x2" :y2="h.y2" class="house-line"
      />

      <!-- 宫位数字 -->
      <text v-for="(h, i) in houseLabels" :key="'hlbl-'+i"
        :x="h.x" :y="h.y" class="house-num"
        text-anchor="middle" dominant-baseline="middle"
      >{{ h.num }}</text>

      <!-- ASC / MC / DESC / IC -->
      <text v-for="(a, i) in angleLabels" :key="'angle-'+i"
        :x="a.x" :y="a.y" class="angle-label"
        text-anchor="middle" dominant-baseline="middle"
      >{{ a.label }}</text>

      <!-- 相位线 -->
      <g v-if="showAspects">
        <line v-for="(a, i) in aspectLines" :key="'aspect-'+i"
          :x1="a.x1" :y1="a.y1" :x2="a.x2" :y2="a.y2"
          :class="['aspect-line', a.nature]"
        />
      </g>

      <!-- 行星 -->
      <g v-for="(p, i) in planetPoints" :key="'planet-' + i">
        <circle :cx="p.x" :cy="p.y" :r="p.radius" class="planet-dot" filter="url(#glowGold)" />
        <text :x="p.x" :y="p.y" class="planet-glyph"
          text-anchor="middle" dominant-baseline="middle"
        >{{ p.glyph }}</text>
        <text :x="p.tagX" :y="p.tagY" class="planet-tag"
          text-anchor="middle" dominant-baseline="middle"
        >{{ p.signTag }}</text>
      </g>

      <circle :cx="cx" :cy="cy" :r="6" class="center-dot" />
    </svg>

    <div class="chart-guide" v-if="ascendant?.sign_label">
      <p class="guide-line">
        <span class="guide-key">ASC</span>
        上升在 <strong>{{ ascendant.sign_label }}</strong>；
        <span v-if="sunSign">太阳 <strong>{{ sunSign }}</strong>；</span>
        <span v-if="moonSign">月亮 <strong>{{ moonSign }}</strong>。</span>
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";

const props = withDefaults(
  defineProps<{
    planets?: Record<string, any>;
    houses?: Array<{ house: number; sign: string; sign_label?: string; degree: number; title?: string }>;
    ascendant?: { sign: string; sign_label?: string; degree: number };
    aspects?: Array<{ title: string; strength: number; nature: string; summary?: string; from?: string; to?: string }>;
    size?: number;
  }>(),
  { size: 460 }
);

const showAspects = ref(true);

const sunSign = computed(() => props.planets?.SUN?.sign_label || "");
const moonSign = computed(() => props.planets?.MOON?.sign_label || "");

const cx = computed(() => props.size / 2);
const cy = computed(() => props.size / 2);
const outerR = computed(() => props.size / 2 - 16);
const ringR = computed(() => outerR.value * 0.76);
const planetR = computed(() => outerR.value * 0.63);

const SIGN_DATA = [
  { name: "白羊", symbol: "♈", element: "fire" },
  { name: "金牛", symbol: "♉", element: "earth" },
  { name: "双子", symbol: "♊", element: "air" },
  { name: "巨蟹", symbol: "♋", element: "water" },
  { name: "狮子", symbol: "♌", element: "fire" },
  { name: "处女", symbol: "♍", element: "earth" },
  { name: "天秤", symbol: "♎", element: "air" },
  { name: "天蝎", symbol: "♏", element: "water" },
  { name: "射手", symbol: "♐", element: "fire" },
  { name: "摩羯", symbol: "♑", element: "earth" },
  { name: "水瓶", symbol: "♒", element: "air" },
  { name: "双鱼", symbol: "♓", element: "water" },
];

const PLANET_GLYPHS: Record<string, string> = {
  SUN: "☉", MOON: "☽", MERCURY: "☿", VENUS: "♀", MARS: "♂",
  JUPITER: "♃", SATURN: "♄", URANUS: "♅", NEPTUNE: "♆", PLUTO: "♇",
  NORTH_NODE: "☊", SOUTH_NODE: "☋",
};

const PLANET_NAMES: Record<string, string> = {
  SUN: "日", MOON: "月", MERCURY: "水", VENUS: "金", MARS: "火",
  JUPITER: "木", SATURN: "土", URANUS: "天", NEPTUNE: "海", PLUTO: "冥",
};

function lonToAngle(lon: number): number {
  return ((lon % 360) * Math.PI) / 180 - Math.PI / 2;
}

function polarToXY(r: number, angle: number) {
  return { x: cx.value + r * Math.cos(angle), y: cy.value + r * Math.sin(angle) };
}

function signLongitude(signLabel: string, degree: number): number {
  const idx = SIGN_DATA.findIndex((s) => s.name === signLabel || s.symbol === signLabel);
  if (idx < 0) return degree;
  return idx * 30 + degree;
}

const signSegments = computed(() => {
  const segs: Array<any> = [];
  for (let i = 0; i < 12; i++) {
    const startAngle = (i * 30 * Math.PI) / 180 - Math.PI / 2;
    const endAngle = ((i + 1) * 30 * Math.PI) / 180 - Math.PI / 2;
    const midAngle = (startAngle + endAngle) / 2;
    const x1 = cx.value + ringR.value * Math.cos(startAngle);
    const y1 = cy.value + ringR.value * Math.sin(startAngle);
    const x2 = cx.value + ringR.value * Math.cos(endAngle);
    const y2 = cy.value + ringR.value * Math.sin(endAngle);
    const ox1 = cx.value + outerR.value * Math.cos(startAngle);
    const oy1 = cy.value + outerR.value * Math.sin(startAngle);
    const ox2 = cx.value + outerR.value * Math.cos(endAngle);
    const oy2 = cy.value + outerR.value * Math.sin(endAngle);
    const path = [
      `M ${x1.toFixed(1)} ${y1.toFixed(1)}`,
      `L ${ox1.toFixed(1)} ${oy1.toFixed(1)}`,
      `A ${outerR.value} ${outerR.value} 0 0 1 ${ox2.toFixed(1)} ${oy2.toFixed(1)}`,
      `L ${x2.toFixed(1)} ${y2.toFixed(1)}`,
      `A ${ringR.value} ${ringR.value} 0 0 0 ${x1.toFixed(1)} ${y1.toFixed(1)}`,
    ].join(" ");
    const midR = (ringR.value + outerR.value) / 2;
    const symPos = polarToXY(midR, midAngle);
    const segData = SIGN_DATA[i]!;
    segs.push({
      path,
      symbol: segData.symbol,
      element: segData.element,
      symbolX: symPos.x,
      symbolY: symPos.y,
    });
  }
  return segs;
});

const houseLines = computed(() => {
  if (!props.houses?.length) return [];
  return props.houses.map((h) => {
    const lon = signLongitude(h.sign_label || h.sign, h.degree || 0);
    const angle = lonToAngle(lon % 360);
    const outer = polarToXY(outerR.value, angle);
    const inner = polarToXY(ringR.value - 14, angle);
    return { x1: inner.x, y1: inner.y, x2: outer.x, y2: outer.y };
  });
});

const houseLabels = computed(() => {
  if (!props.houses?.length) return [];
  return props.houses.map((h, i) => {
    const lon = signLongitude(h.sign_label || h.sign, h.degree || 0);
    const nextH = props.houses![(i + 1) % 12]!;
    const nextLon = signLongitude(nextH.sign_label || nextH.sign, nextH.degree || 0);
    let midLon = (lon + (nextLon < lon ? nextLon + 360 : nextLon)) / 2;
    if (midLon >= 360) midLon -= 360;
    const midAngle = lonToAngle(midLon);
    const pos = polarToXY((ringR.value + planetR.value) / 2, midAngle);
    return { x: pos.x, y: pos.y, num: h.house };
  });
});

const angleLabels = computed(() => {
  const labels: Array<{ x: number; y: number; label: string }> = [];
  if (!props.houses?.length) return labels;
  const angleDefs = [
    { idx: 0, label: "ASC" },
    { idx: 3, label: "IC" },
    { idx: 6, label: "DESC" },
    { idx: 9, label: "MC" },
  ];
  for (const def of angleDefs) {
    const h = props.houses[def.idx];
    if (!h) continue;
    const lon = signLongitude(h.sign_label || h.sign, h.degree || 0);
    const angle = lonToAngle(lon % 360);
    const pos = polarToXY(ringR.value + 14, angle);
    labels.push({ x: pos.x, y: pos.y, label: def.label });
  }
  return labels;
});

const DISPLAY_ORDER = ["SUN", "MOON", "MERCURY", "VENUS", "MARS", "JUPITER", "SATURN", "URANUS", "NEPTUNE", "PLUTO"];

const planetPoints = computed(() => {
  const planets = props.planets || {};
  const points: Array<any> = [];
  const placed: Array<{ x: number; y: number }> = [];

  for (const key of DISPLAY_ORDER) {
    const p = planets[key];
    if (!p || p.longitude === undefined) continue;
    const lon = p.longitude || 0;
    let r = planetR.value;
    const cand = polarToXY(r, lonToAngle(lon));
    const tooClose = placed.some((pp) => Math.hypot(pp.x - cand.x, pp.y - cand.y) < 22);
    if (tooClose) r = planetR.value + 14;
    const pos = polarToXY(r, lonToAngle(lon));
    const tagPos = polarToXY(r + 16, lonToAngle(lon));
    const signName = p.sign_label || p.sign || "";
    const signIdx = SIGN_DATA.findIndex((s) => s.name === signName || s.symbol === signName);
    placed.push(pos);
    points.push({
      x: pos.x, y: pos.y,
      tagX: tagPos.x, tagY: tagPos.y,
      glyph: PLANET_GLYPHS[key] || "●",
      signTag: signIdx >= 0 ? SIGN_DATA[signIdx]!.symbol : "",
      radius: key === "SUN" ? 12 : key === "MOON" ? 11 : 8,
      key,
    });
  }
  return points;
});

const aspectLines = computed(() => {
  const planets = props.planets || {};
  const aspects = props.aspects || [];
  const lines: Array<{ x1: number; y1: number; x2: number; y2: number; nature: string }> = [];
  for (const asp of aspects) {
    const title = asp.title || "";
    const parts = title.split(" ");
    if (parts.length < 3) continue;
    const findKey = (label: string) => {
      for (const [k, v] of Object.entries(PLANET_NAMES)) if (v === label) return k;
      return null;
    };
    const key1 = findKey(parts[0] ?? "");
    const key2 = findKey(parts[2] ?? "");
    if (!key1 || !key2) continue;
    const p1 = planets[key1];
    const p2 = planets[key2];
    if (!p1?.longitude || !p2?.longitude) continue;
    const pos1 = polarToXY(planetR.value, lonToAngle(p1.longitude));
    const pos2 = polarToXY(planetR.value, lonToAngle(p2.longitude));
    lines.push({ x1: pos1.x, y1: pos1.y, x2: pos2.x, y2: pos2.y, nature: asp.nature || "neutral" });
  }
  return lines;
});
</script>

<style scoped lang="less">
.natal-wheel-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 8px 0 16px;
  background: #0a0e1a;
  border-radius: 16px;
}

.wheel-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  max-width: 460px;
  padding: 8px 16px;
  margin-bottom: 8px;
  color: #d4af37;
  font-size: 13px;
}

.toggle {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  user-select: none;
}

.toggle input {
  accent-color: #d4af37;
}

.legend {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  color: #cbd5e1;
  font-size: 12px;
}

.dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  margin-right: 2px;
}

.dot-support { background: #4ade80; }
.dot-challenge { background: #f87171; }
.dot-neutral { background: #94a3b8; }

.chart-svg {
  max-width: 100%;
  height: auto;
}

.chart-frame {
  fill: none;
  stroke: rgba(212, 175, 55, 0.3);
  stroke-width: 1.2;
}

.inner-ring {
  fill: none;
  stroke: rgba(212, 175, 55, 0.2);
  stroke-width: 0.8;
}

.sign-band {
  stroke: rgba(212, 175, 55, 0.15);
  stroke-width: 0.5;

  &.fire  { fill: rgba(200, 70, 50, 0.16); }
  &.earth { fill: rgba(100, 150, 80, 0.16); }
  &.air   { fill: rgba(180, 170, 90, 0.16); }
  &.water { fill: rgba(70, 110, 190, 0.16); }
}

.sign-symbol {
  fill: #d4af37;
  font-size: 14px;
  pointer-events: none;
  user-select: none;
}

.house-line {
  stroke: rgba(212, 175, 55, 0.25);
  stroke-width: 0.7;
}

.house-num {
  fill: rgba(212, 175, 55, 0.7);
  font-size: 12px;
  font-weight: 700;
  pointer-events: none;
  user-select: none;
}

.angle-label {
  fill: #f0c040;
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.08em;
  pointer-events: none;
  user-select: none;
}

.aspect-line {
  stroke-width: 1;
  opacity: 0.5;

  &.supportive   { stroke: #4ade80; }
  &.challenging  { stroke: #f87171; }
  &.neutral      { stroke: #94a3b8; }
}

.planet-dot {
  fill: #0f172a;
  stroke: #d4af37;
  stroke-width: 1.4;
}

.planet-glyph {
  fill: #fef3c7;
  font-size: 12px;
  pointer-events: none;
  user-select: none;
}

.planet-tag {
  fill: rgba(254, 243, 199, 0.7);
  font-size: 9px;
  pointer-events: none;
  user-select: none;
}

.center-dot {
  fill: rgba(212, 175, 55, 0.3);
}

.chart-guide {
  margin-top: 12px;
  padding: 10px 14px;
  border-radius: 10px;
  background: rgba(212, 175, 55, 0.06);
  border: 1px solid rgba(212, 175, 55, 0.15);
  color: #cbd5e1;
  max-width: 460px;
}

.guide-line {
  margin: 0;
  font-size: 13px;
  line-height: 1.7;
}

.guide-key {
  display: inline-block;
  padding: 1px 6px;
  border-radius: 4px;
  background: rgba(212, 175, 55, 0.18);
  color: #f0c040;
  font-size: 11px;
  font-weight: 700;
  margin-right: 4px;
}

.guide-line strong {
  color: #fef3c7;
  font-weight: 600;
}
</style>