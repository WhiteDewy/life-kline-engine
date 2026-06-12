<template>
  <section class="natalSection" v-if="natalChart">
    <article class="panel chartPanel">
      <div class="panelHeader">
        <div>
          <div class="panelEyebrow">Natal Chart</div>
          <h2 class="panelTitle">本命星盘</h2>
          <p class="panelSummary">
            参考本命盘查看方式，优先呈现宫头、行星落点与主轴信息，方便直接对照阅读。
          </p>
        </div>
        <div class="chartMeta">
          <span class="metaChip">
            上升 {{ natalChart.ascendant?.sign_label || natalChart.ascendant?.sign || "-" }}
            {{ formatDegree(natalChart.ascendant?.degree) }}
          </span>
          <span class="metaChip">
            命主星 {{ natalChart.chart_ruler_label || natalChart.chart_ruler || "-" }}
          </span>
        </div>
      </div>

      <div class="chartLayout">
        <div class="wheelCard">
          <div class="wheelGrid">
            <div
              v-for="cell in wheelCells"
              :key="cell.key"
              class="wheelCell"
              :class="[`house-${cell.house || 0}`, { centerCell: cell.type === 'center' }]"
            >
              <template v-if="cell.type === 'house'">
                <div class="houseHead">
                  <span class="houseNo">H{{ cell.house }}</span>
                  <span class="houseSign">
                    {{ cell.cusp?.sign_label || "-" }}
                    {{ formatDegree(cell.cusp?.degree) }}
                  </span>
                </div>
                <div class="houseTitle">{{ cell.cusp?.title || "" }}</div>
                <div class="planetStack">
                  <div
                    v-for="planet in planetsByHouse[cell.house || 0] || []"
                    :key="planet.planet"
                    class="planetPill"
                  >
                    <strong>{{ planet.label }}</strong>
                    <span>{{ planet.signLabel }} {{ formatDegree(planet.degree) }}</span>
                  </div>
                  <span
                    v-if="!(planetsByHouse[cell.house || 0] || []).length"
                    class="emptyPlanet"
                  >
                    暂无主行星
                  </span>
                </div>
              </template>

              <template v-else>
                <div class="centerContent">
                  <div class="centerLabel">Chart Core</div>
                  <div class="centerTitle">{{ natalChart.sect_label || "-" }}</div>
                  <p class="centerText">{{ natalChart.signature || "-" }}</p>
                </div>
              </template>
            </div>
          </div>
        </div>

        <div class="legendCard">
          <div class="legendGroup">
            <div class="legendTitle">行星落点</div>
            <div class="legendList">
              <article
                v-for="planet in orderedPlanets"
                :key="planet.planet"
                class="legendItem"
              >
                <div class="legendTop">
                  <strong>{{ planet.label }}</strong>
                  <span :class="['dignityBadge', planet.dignity]">
                    {{ planet.dignityLabel }}
                  </span>
                </div>
                <p>
                  {{ planet.signLabel }} {{ formatDegree(planet.degree) }} · 第{{ planet.house }}宫
                  {{ planet.houseTitle }}
                </p>
                <p class="legendHint">
                  {{ planet.retrograde ? "逆行" : "顺行" }} · {{ planet.gift || planet.reason || "-" }}
                </p>
              </article>
            </div>
          </div>

          <div class="legendGroup" v-if="natalChart.pressure_points?.length">
            <div class="legendTitle">需要留意</div>
            <div class="pressureList">
              <div
                v-for="item in natalChart.pressure_points"
                :key="item.planet"
                class="pressureItem"
              >
                <strong>{{ item.label }}</strong>
                <span>{{ item.score }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </article>
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";

interface NatalPlanet {
  planet: string;
  label: string;
  signLabel: string;
  degree: number;
  house: number;
  houseTitle?: string;
  dignity?: string;
  dignityLabel?: string;
  retrograde?: boolean;
  gift?: string;
  reason?: string;
}

interface NatalHouse {
  house: number;
  sign: string;
  sign_label?: string;
  degree: number;
  title?: string;
}

const props = defineProps<{
  natalChart: Record<string, any> | null;
}>();

const PLANET_ORDER = ["SUN", "MOON", "MERCURY", "VENUS", "MARS", "JUPITER", "SATURN"];

const houseIndexOrder = [10, 11, 12, 9, 0, 1, 8, 7, 6, 5, 4, 3];

const orderedPlanets = computed<NatalPlanet[]>(() => {
  const planets = props.natalChart?.planets || {};
  return PLANET_ORDER.map((planetKey) => {
    const item = planets[planetKey];
    if (!item) return null;
    return {
      planet: planetKey,
      label: planetLabel(planetKey),
      signLabel: item.sign_label || item.sign || "-",
      degree: Number(item.degree || 0),
      house: Number(item.house || 0),
      houseTitle: item.house_title,
      dignity: item.dignity,
      dignityLabel: item.dignity_label || item.dignity || "-",
      retrograde: Boolean(item.retrograde),
      gift: item.gift,
      reason: item.reason,
    };
  }).filter(Boolean) as NatalPlanet[];
});

const planetsByHouse = computed<Record<number, NatalPlanet[]>>(() => {
  const grouped: Record<number, NatalPlanet[]> = {};
  for (const planet of orderedPlanets.value) {
    if (!grouped[planet.house]) {
      grouped[planet.house] = [];
    }
    grouped[planet.house].push(planet);
  }
  return grouped;
});

const houses = computed<NatalHouse[]>(() => {
  const items = props.natalChart?.houses;
  if (Array.isArray(items) && items.length) {
    return items as NatalHouse[];
  }

  const asc = props.natalChart?.ascendant;
  if (!asc) return [];

  const signCycle = [
    "白羊座",
    "金牛座",
    "双子座",
    "巨蟹座",
    "狮子座",
    "处女座",
    "天秤座",
    "天蝎座",
    "射手座",
    "摩羯座",
    "水瓶座",
    "双鱼座",
  ];
  const ascIndex = signCycle.indexOf(asc.sign_label || "");
  if (ascIndex === -1) return [];

  return Array.from({ length: 12 }, (_, index) => ({
    house: index + 1,
    sign: "",
    sign_label: signCycle[(ascIndex + index) % 12],
    degree: index === 0 ? Number(asc.degree || 0) : 0,
    title: `第${index + 1}宫`,
  }));
});

const wheelCells = computed(() => {
  const cells: Array<{
    key: string;
    type: "house" | "center";
    house?: number;
    cusp?: NatalHouse;
  }> = [];

  houseIndexOrder.forEach((houseIndex, index) => {
    if (index === 4) {
      cells.push({ key: "center", type: "center" });
    }

    const cusp = houses.value[houseIndex];
    cells.push({
      key: `house-${houseIndex + 1}`,
      type: "house",
      house: houseIndex + 1,
      cusp,
    });
  });

  return cells;
});

function formatDegree(value?: number) {
  if (typeof value !== "number" || Number.isNaN(value)) return "-";
  return `${value.toFixed(1)}°`;
}

function planetLabel(planet: string) {
  const labels: Record<string, string> = {
    SUN: "太阳",
    MOON: "月亮",
    MERCURY: "水星",
    VENUS: "金星",
    MARS: "火星",
    JUPITER: "木星",
    SATURN: "土星",
    URANUS: "天王星",
    NEPTUNE: "海王星",
    PLUTO: "冥王星",
  };
  return labels[planet] || planet;
}
</script>

<style scoped>
.natalSection {
  margin-bottom: 22px;
}

.chartPanel {
  padding: 24px;
}

.panelHeader {
  display: flex;
  justify-content: space-between;
  gap: 18px;
  align-items: flex-start;
}

.panelEyebrow {
  font-size: 12px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--gold);
}

.panelTitle {
  margin: 10px 0 0;
  color: var(--text);
  font-size: 26px;
  line-height: 1.2;
}

.panelSummary {
  margin: 12px 0 0;
  color: var(--text-secondary);
  line-height: 1.8;
}

.chartMeta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: flex-end;
}

.metaChip {
  display: inline-flex;
  align-items: center;
  padding: 8px 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: var(--text-secondary);
  font-size: 12px;
}

.chartLayout {
  margin-top: 22px;
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(320px, 0.9fr);
  gap: 18px;
}

.wheelCard,
.legendCard {
  border-radius: 24px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.03);
}

.wheelCard {
  padding: 18px;
}

.wheelGrid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.wheelCell {
  min-height: 140px;
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  background:
    radial-gradient(circle at top left, rgba(212, 175, 55, 0.08), transparent 38%),
    rgba(2, 6, 23, 0.55);
  padding: 14px;
}

.centerCell {
  grid-column: span 2;
  grid-row: span 2;
  display: flex;
  align-items: center;
  justify-content: center;
  background:
    radial-gradient(circle at 50% 50%, rgba(212, 175, 55, 0.18), transparent 50%),
    rgba(2, 6, 23, 0.7);
}

.centerContent {
  text-align: center;
}

.centerLabel {
  font-size: 12px;
  color: var(--text-secondary);
  letter-spacing: 0.18em;
  text-transform: uppercase;
}

.centerTitle {
  margin-top: 10px;
  font-size: 30px;
  color: var(--text);
  font-weight: 700;
}

.centerText {
  margin: 14px auto 0;
  max-width: 360px;
  color: var(--text-secondary);
  line-height: 1.8;
}

.houseHead {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  color: var(--text);
  font-size: 12px;
}

.houseNo {
  color: var(--gold);
  font-weight: 700;
  letter-spacing: 0.08em;
}

.houseSign {
  color: var(--text-secondary);
}

.houseTitle {
  margin-top: 8px;
  color: var(--text);
  font-size: 14px;
  font-weight: 600;
}

.planetStack {
  margin-top: 14px;
  display: grid;
  gap: 8px;
}

.planetPill {
  padding: 10px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.planetPill strong,
.legendTop strong {
  color: var(--text);
}

.planetPill span,
.legendTop span,
.legendItem p,
.emptyPlanet,
.legendHint {
  color: var(--text-secondary);
  font-size: 12px;
  line-height: 1.6;
}

.legendCard {
  padding: 18px;
  display: grid;
  gap: 18px;
}

.legendGroup {
  display: grid;
  gap: 12px;
}

.legendTitle {
  color: var(--text);
  font-size: 14px;
  font-weight: 700;
}

.legendList {
  display: grid;
  gap: 10px;
}

.legendItem {
  padding: 14px;
  border-radius: 18px;
  background: rgba(2, 6, 23, 0.45);
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.legendTop {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  align-items: center;
}

.legendItem p {
  margin: 8px 0 0;
}

.legendHint {
  opacity: 0.88;
}

.dignityBadge {
  display: inline-flex;
  align-items: center;
  padding: 4px 8px;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.dignityBadge.domicile,
.dignityBadge.exaltation {
  color: #34d399;
  background: rgba(52, 211, 153, 0.12);
}

.dignityBadge.detriment,
.dignityBadge.fall {
  color: #f97316;
  background: rgba(249, 115, 22, 0.12);
}

.dignityBadge.peregrine {
  color: #f8fafc;
  background: rgba(255, 255, 255, 0.04);
}

.pressureList {
  display: grid;
  gap: 10px;
}

.pressureItem {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  padding: 12px 14px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.pressureItem strong {
  color: var(--text);
}

.pressureItem span {
  color: #fb7185;
}

@media (max-width: 1180px) {
  .chartLayout {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 860px) {
  .panelHeader {
    flex-direction: column;
  }

  .chartMeta {
    justify-content: flex-start;
  }

  .wheelGrid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .centerCell {
    grid-column: span 2;
  }
}

@media (max-width: 560px) {
  .wheelGrid {
    grid-template-columns: 1fr;
  }

  .centerCell {
    grid-column: span 1;
    grid-row: span 1;
  }

  .wheelCell {
    min-height: 120px;
  }
}
</style>
