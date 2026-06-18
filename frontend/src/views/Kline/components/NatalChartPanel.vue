<template>
  <section v-if="natalChart" class="natal-section">
    <article class="natal-panel">
      <header class="panel-header">
        <div class="panel-copy">
          <div class="panel-kicker">{{ copy.kicker }}</div>
          <h2 class="panel-title">{{ copy.title }}</h2>
          <p class="panel-summary">{{ copy.summary }}</p>
        </div>

        <div class="header-chips">
          <span class="header-chip">{{ copy.zodiacMode }}</span>
          <span class="header-chip">{{ copy.houseSystem }}</span>
          <span class="header-chip">{{ copy.ascendant }} {{ ascendantLine }}</span>
          <span class="header-chip">{{ copy.chartRuler }} {{ chartRulerLabel }}</span>
          <span class="header-chip">{{ sectLabel }}</span>
        </div>
      </header>

      <div class="chart-layout">
        <section class="wheel-card">
          <div class="wheel-frame">
            <svg
              class="wheel-svg"
              viewBox="0 0 640 640"
              role="img"
              :aria-label="copy.title"
            >
              <circle :cx="CENTER" :cy="CENTER" :r="OUTER_RADIUS + 8" class="wheel-shadow" />
              <circle :cx="CENTER" :cy="CENTER" :r="OUTER_RADIUS" class="wheel-base" />

              <path
                v-for="segment in zodiacSegments"
                :key="segment.sign"
                :d="segment.path"
                class="zodiac-segment"
                :style="{ '--segment-fill': segment.color }"
              />

              <line
                v-for="segment in zodiacSegments"
                :key="`${segment.sign}-divider`"
                :x1="segment.divider.start.x"
                :y1="segment.divider.start.y"
                :x2="segment.divider.end.x"
                :y2="segment.divider.end.y"
                class="zodiac-divider"
              />

              <circle :cx="CENTER" :cy="CENTER" :r="ZODIAC_INNER_RADIUS" class="ring-line" />
              <circle :cx="CENTER" :cy="CENTER" :r="PLANET_TRACK_RADIUS + 20" class="ring-line soft" />
              <circle :cx="CENTER" :cy="CENTER" :r="PLANET_TRACK_RADIUS" class="ring-line" />
              <circle :cx="CENTER" :cy="CENTER" :r="HOUSE_LABEL_RADIUS + 18" class="ring-line soft" />
              <circle :cx="CENTER" :cy="CENTER" :r="ASPECT_RADIUS" class="aspect-boundary" />

              <line
                v-for="line in wheelAspectLines"
                :key="`${line.from}-${line.to}-${line.kind}`"
                :x1="line.start.x"
                :y1="line.start.y"
                :x2="line.end.x"
                :y2="line.end.y"
                :class="['aspect-line', line.kind]"
              />

              <line
                v-for="house in houseLines"
                :key="`house-${house.house}`"
                :x1="house.start.x"
                :y1="house.start.y"
                :x2="house.end.x"
                :y2="house.end.y"
                :class="['house-line', { axis: house.isAxis }]"
              />

              <text
                v-for="house in houseLabels"
                :key="`house-label-${house.house}`"
                :x="house.position.x"
                :y="house.position.y"
                class="house-number"
              >
                {{ house.house }}
              </text>

              <g v-for="axis in axisLabels" :key="axis.label">
                <text :x="axis.position.x" :y="axis.position.y" class="axis-label">
                  {{ axis.label }}
                </text>
              </g>

              <g v-for="cusp in cuspMarkers" :key="`cusp-${cusp.house}`" class="cusp-marker">
                <text :x="cusp.icon.x" :y="cusp.icon.y - 1" class="cusp-glyph astro-symbol">
                  {{ cusp.glyph }}
                </text>
                <text :x="cusp.degree.x" :y="cusp.degree.y" class="cusp-degree">
                  {{ cusp.degreeLabel }}
                </text>
              </g>

              <g v-for="planet in planetMarkers" :key="planet.key" class="planet-marker">
                <line
                  :x1="planet.tickStart.x"
                  :y1="planet.tickStart.y"
                  :x2="planet.tickEnd.x"
                  :y2="planet.tickEnd.y"
                  class="planet-tick"
                />
                <text
                  :x="planet.position.x"
                  :y="planet.position.y - 1"
                  class="planet-glyph astro-symbol"
                  :style="{ '--planet-accent': planet.color }"
                >
                  {{ planet.glyph }}
                </text>
                <text
                  v-if="planet.retrograde"
                  :x="planet.retro.x"
                  :y="planet.retro.y"
                  class="retro-flag"
                >
                  R
                </text>
              </g>

              <circle :cx="CENTER" :cy="CENTER" :r="INNER_DISC_RADIUS" class="center-disc" />
              <text :x="CENTER" :y="CENTER - 18" class="center-kicker">{{ copy.centerAsc }}</text>
              <text :x="CENTER" :y="CENTER + 6" class="center-main">{{ ascendantSignLabel }}</text>
              <text :x="CENTER" :y="CENTER + 28" class="center-sub">{{ chartRulerLabel }}</text>
            </svg>
          </div>

          <div class="wheel-footer">
            <span class="footer-chip">{{ copy.houseSystem }}</span>
            <span class="footer-text">{{ copy.cuspHint }}</span>
          </div>
        </section>

        <aside class="detail-card">
          <section class="detail-section">
            <div class="section-title">{{ copy.planetTable }}</div>
            <div class="planet-list">
              <article
                v-for="planet in orderedPlanets"
                :key="planet.key"
                class="planet-row"
                :style="{ '--planet-accent': planet.color }"
              >
                <svg viewBox="0 0 42 42" class="list-icon" aria-hidden="true">
                  <text x="21" y="17" class="list-icon-glyph astro-symbol">{{ planet.glyph }}</text>
                  <text x="21" y="30" class="list-icon-code">{{ planet.shortLabel }}</text>
                </svg>

                <div class="planet-copy">
                  <div class="planet-topline">
                    <strong>{{ planet.label }}</strong>
                    <span :class="['state-chip', planet.dignity || 'peregrine']">
                      {{ planet.dignityLabel }}
                    </span>
                  </div>
                  <p class="planet-meta">{{ planet.positionLine }}</p>
                  <p v-if="planet.meaningLine" class="planet-meaning">{{ planet.meaningLine }}</p>
                  <p v-if="planet.descriptionLine" class="planet-note">{{ planet.descriptionLine }}</p>
                </div>
              </article>
            </div>
          </section>

          <section class="detail-section">
            <div class="section-title">{{ copy.cuspTable }}</div>
            <div class="cusp-grid">
              <article v-for="house in houseCuspDetails" :key="house.house" class="cusp-card">
                <div class="cusp-head">
                  <span class="cusp-index">H{{ house.house }}</span>
                  <span class="cusp-line">{{ house.degreeLabel }}</span>
                </div>
                <div class="cusp-sign">
                  <svg viewBox="0 0 38 38" class="cusp-icon" aria-hidden="true">
                    <text x="19" y="19" class="cusp-icon-glyph astro-symbol">{{ house.glyph }}</text>
                  </svg>
                  <div>
                    <strong>{{ house.signLabel }}</strong>
                    <p>{{ house.title }}</p>
                  </div>
                </div>
              </article>
            </div>
          </section>
        </aside>
      </div>

      <section class="reader-section">
        <div class="section-header">
          <div>
            <div class="panel-kicker">{{ copy.readerKicker }}</div>
            <h3 class="section-heading">{{ copy.readerTitle }}</h3>
            <p class="section-note">{{ copy.readerNote }}</p>
          </div>
        </div>

        <div class="reader-grid">
          <article class="reader-card">
            <div class="section-title">{{ copy.signatureCard }}</div>
            <p class="reader-summary">{{ natalChart.signature || fallbackSignature }}</p>
            <div v-if="dominantPlanetRows.length" class="reader-stack">
              <div v-for="item in dominantPlanetRows" :key="item.label" class="reader-item">
                <div class="reader-row">
                  <strong>{{ item.label }}</strong>
                  <span>{{ item.score }}</span>
                </div>
                <p v-if="item.meaningLine" class="reader-emphasis">{{ item.meaningLine }}</p>
                <p v-if="item.detailLine" class="reader-subnote">{{ item.detailLine }}</p>
              </div>
            </div>
          </article>

          <article class="reader-card">
            <div class="section-title">{{ copy.aspectHighlights }}</div>
            <div class="reader-stack">
              <div v-for="item in aspectHighlights" :key="item.title" class="reader-item">
                <div class="reader-row">
                  <strong>{{ item.title }}</strong>
                  <span>{{ item.strengthLabel }}</span>
                </div>
                <p v-if="item.meaningLine" class="reader-emphasis">{{ item.meaningLine }}</p>
                <p>{{ item.summary }}</p>
              </div>
            </div>
          </article>

          <article class="reader-card">
            <div class="section-title">{{ copy.houseHighlights }}</div>
            <div class="reader-stack">
              <div v-for="item in houseHighlights" :key="item.key" class="reader-item">
                <div class="reader-row">
                  <strong>{{ item.title }}</strong>
                  <span>{{ item.value }}</span>
                </div>
                <p>{{ item.summary }}</p>
              </div>
            </div>
          </article>

          <article v-if="pressureRows.length" class="reader-card">
            <div class="section-title">{{ copy.pressurePoints }}</div>
            <div class="reader-stack">
              <div v-for="item in pressureRows" :key="item.label" class="reader-item">
                <div class="reader-row">
                  <strong>{{ item.label }}</strong>
                  <span>{{ item.score }}</span>
                </div>
                <p v-if="item.meaningLine" class="reader-emphasis">{{ item.meaningLine }}</p>
                <p>{{ item.reason }}</p>
              </div>
            </div>
          </article>
        </div>
      </section>

      <details v-if="hasTechnicalArea" class="technical-fold">
        <summary class="technical-toggle">
          <div class="technical-toggle-copy">
            <div class="panel-kicker">{{ copy.professionalKicker }}</div>
            <h3 class="section-heading">{{ copy.professionalTitle }}</h3>
            <p class="section-note">{{ copy.professionalNote }}</p>
          </div>
          <span class="header-chip">{{ copy.professionalAction }}</span>
        </summary>

        <section class="technical-section">
          <div class="section-header">
            <div>
              <div class="panel-kicker">{{ copy.professionalKicker }}</div>
              <h3 class="section-heading">{{ copy.professionalTitle }}</h3>
            </div>
            <span class="header-chip">{{ copy.houseSystem }}</span>
          </div>

          <article v-if="aspectMatrixRows.length" class="table-card">
            <div class="table-title-row">
              <div class="section-title">{{ copy.aspectMatrix }}</div>
            </div>
            <div class="table-scroll">
              <table class="aspect-matrix">
                <thead>
                  <tr>
                    <th class="matrix-corner"></th>
                    <th v-for="planet in aspectMatrixPlanets" :key="`head-${planet.key}`">
                      <div class="matrix-planet">
                        <svg viewBox="0 0 34 34" class="matrix-icon" aria-hidden="true">
                          <text x="17" y="15" class="matrix-icon-glyph astro-symbol">{{ planet.glyph }}</text>
                          <text x="17" y="25" class="matrix-icon-code">{{ planet.shortLabel }}</text>
                        </svg>
                      </div>
                    </th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="row in aspectMatrixRows" :key="`row-${row.planet.key}`">
                    <th>
                      <div class="matrix-planet">
                        <svg viewBox="0 0 34 34" class="matrix-icon" aria-hidden="true">
                          <text x="17" y="15" class="matrix-icon-glyph astro-symbol">{{ row.planet.glyph }}</text>
                          <text x="17" y="25" class="matrix-icon-code">{{ row.planet.shortLabel }}</text>
                        </svg>
                      </div>
                    </th>
                    <td
                      v-for="cell in row.cells"
                      :key="cell.key"
                      :class="['matrix-cell', cell.state, cell.nature]"
                    >
                      <template v-if="cell.symbol">
                        <div class="matrix-symbol astro-symbol">{{ cell.symbol }}</div>
                        <div class="matrix-orb">{{ cell.orbLabel }}</div>
                      </template>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </article>

          <div class="relation-grid">
            <article v-if="receptionRows.length" class="table-card">
              <div class="table-title-row">
                <div class="section-title">{{ copy.receptionTable }}</div>
              </div>
              <div class="table-scroll">
                <table class="data-table">
                  <thead>
                    <tr>
                      <th>{{ copy.receiver }}</th>
                      <th>{{ copy.position }}</th>
                      <th>{{ copy.guests }}</th>
                      <th>{{ copy.chain }}</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="row in receptionRows" :key="row.line">
                      <td>{{ row.receiver }}</td>
                      <td>{{ row.position }}</td>
                      <td>{{ row.guests }}</td>
                      <td>{{ row.line }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </article>

            <article v-if="mutualReceptionRows.length" class="table-card">
              <div class="table-title-row">
                <div class="section-title">{{ copy.mutualReceptionTable }}</div>
              </div>
              <div class="table-scroll">
                <table class="data-table">
                  <thead>
                    <tr>
                      <th>{{ copy.combination }}</th>
                      <th>{{ copy.chain }}</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="row in mutualReceptionRows" :key="row.line">
                      <td>{{ row.pair }}</td>
                      <td>{{ row.line }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </article>
          </div>
        </section>
      </details>
    </article>
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { buildPlanetBlendLine, extractPlanetKeysFromText, getPlanetMeaning } from "@/utils/planetMeaning";

interface NatalPlanetRecord {
  sign?: string;
  sign_label?: string;
  house?: number;
  house_title?: string;
  degree?: number;
  retrograde?: boolean;
  dignity?: string;
  dignity_label?: string;
  gift?: string;
  reason?: string;
  longitude?: number;
  [key: string]: any;
}

interface NatalHouse {
  house: number;
  sign: string;
  sign_label?: string;
  degree: number;
  title?: string;
}

interface PlanetView {
  key: string;
  label: string;
  shortLabel: string;
  glyph: string;
  color: string;
  sign: string;
  signLabel: string;
  degree: number;
  house: number;
  houseTitle: string;
  degreeLabel: string;
  dignity?: string;
  dignityLabel: string;
  retrograde: boolean;
  longitude: number;
  positionLine: string;
  meaningLine: string;
  descriptionLine: string;
}

interface ReaderPlanetRow {
  label: string;
  score: string;
  meaningLine: string;
  detailLine: string;
}

interface PressureRow {
  label: string;
  score: string;
  meaningLine: string;
  reason: string;
}

interface AspectHighlightRow {
  title: string;
  strengthLabel: string;
  summary: string;
  meaningLine: string;
}

interface AspectLine {
  key: string;
  symbol: string;
  title: string;
  kind: string;
  angle: number;
  orb: number;
  nature: "supportive" | "challenging" | "neutral";
  summary: string;
}

interface AspectRecord {
  from: string;
  to: string;
  kind: string;
  symbol: string;
  title: string;
  nature: "supportive" | "challenging" | "neutral";
  summary: string;
  delta: number;
  closeness: number;
  start: { x: number; y: number };
  end: { x: number; y: number };
}

const props = defineProps<{
  natalChart: Record<string, any> | null;
  advancedPatterns?: Record<string, any> | null;
}>();

const copy = {
  kicker: "\u004eatal\u0020\u0057heel",
  title: "\u672c\u547d\u661f\u76d8",
  summary:
    "\u8f6e\u76d8\u3001\u76f8\u4f4d\u77e9\u9635\u3001\u4e92\u6eb6\u4e0e\u63a5\u7eb3\u8868\u62c6\u5206\u5448\u73b0\uff0c\u4e0a\u534a\u533a\u4f9b\u4e13\u4e1a\u5360\u661f\u5e08\u76f4\u8bfb\uff0c\u4e0b\u534a\u533a\u4fdd\u7559\u7ed9\u7528\u6237\u9605\u8bfb\u3002",
  houseSystem: "\u963f\u5361\u6bd4\u7279\u5bab\u4f4d\u5236",
  zodiacMode: "\u56de\u5f52\u9ec4\u9053",
  ascendant: "\u4e0a\u5347",
  chartRuler: "\u547d\u4e3b\u661f",
  centerAsc: "ASC",
  cuspHint: "\u5bab\u5934\u5ea6\u6570\u5747\u4ee5\u201cxx\u00b0xx\u2032\u201d\u663e\u793a",
  planetTable: "\u661f\u4f53\u843d\u70b9",
  cuspTable: "\u5bab\u5934\u5ea6\u6570",
  professionalKicker: "\u0050rofessional\u0020\u0052eading",
  professionalTitle: "\u4e13\u4e1a\u5224\u8bfb\u533a",
  professionalNote:
    "\u76f8\u4f4d\u8868\u3001\u63a5\u7eb3\u8868\u3001\u4e92\u6eb6\u8868\u66f4\u9002\u5408\u4e13\u4e1a\u5360\u661f\u5e08\u76f4\u8bfb\uff0c\u6216\u8005\u4f60\u9700\u8981\u56de\u5934\u6821\u5bf9\u8bc1\u636e\u65f6\u518d\u5c55\u5f00\u3002",
  professionalAction: "\u5c55\u5f00\u4e13\u4e1a\u533a",
  aspectMatrix: "\u76f8\u4f4d\u8868",
  receptionTable: "\u63a5\u7eb3\u8868",
  mutualReceptionTable: "\u4e92\u6eb6\u8868",
  receiver: "\u63a5\u7eb3\u661f",
  position: "\u843d\u70b9",
  guests: "\u88ab\u63a5\u7eb3\u661f",
  chain: "\u94fe\u8def",
  combination: "\u661f\u4f53\u7ec4\u5408",
  readerKicker: "\u0052eader\u0020\u0056iew",
  readerTitle: "\u7528\u6237\u9605\u8bfb\u533a",
  readerNote:
    "\u666e\u901a\u7528\u6237\u5efa\u8bae\u5148\u770b\u547d\u76d8\u6458\u8981\u3001\u5173\u952e\u76f8\u4f4d\u3001\u91cd\u70b9\u9886\u57df\u548c\u9700\u8981\u7559\u610f\u3002",
  signatureCard: "\u547d\u76d8\u6458\u8981",
  aspectHighlights: "\u5173\u952e\u76f8\u4f4d",
  houseHighlights: "\u91cd\u70b9\u9886\u57df",
  pressurePoints: "\u9700\u8981\u7559\u610f",
  retrograde: "\u9006\u884c",
  direct: "\u987a\u884c",
  unknown: "-",
} as const;

const CENTER = 320;
const OUTER_RADIUS = 286;
const ZODIAC_INNER_RADIUS = 236;
const PLANET_TRACK_RADIUS = 202;
const PLANET_BASE_RADIUS = 184;
const HOUSE_LABEL_RADIUS = 142;
const HOUSE_INNER_RADIUS = 84;
const ASPECT_RADIUS = 120;
const INNER_DISC_RADIUS = 64;
const CUSP_ICON_RADIUS = 298;
const CUSP_TEXT_RADIUS = 274;
const AXIS_LABEL_RADIUS = 96;

const SIGN_SEQUENCE = [
  "ARIES",
  "TAURUS",
  "GEMINI",
  "CANCER",
  "LEO",
  "VIRGO",
  "LIBRA",
  "SCORPIO",
  "SAGITTARIUS",
  "CAPRICORN",
  "AQUARIUS",
  "PISCES",
] as const;

const SIGN_META: Record<
  string,
  { label: string; glyph: string; shortLabel: string; color: string }
> = {
  ARIES: { label: "\u767d\u7f8a", glyph: "\u2648", shortLabel: "Ar", color: "#d7b48a" },
  TAURUS: { label: "\u91d1\u725b", glyph: "\u2649", shortLabel: "Ta", color: "#c4b07d" },
  GEMINI: { label: "\u53cc\u5b50", glyph: "\u264a", shortLabel: "Ge", color: "#9ea9b8" },
  CANCER: { label: "\u5de8\u87f9", glyph: "\u264b", shortLabel: "Cn", color: "#8ea7b7" },
  LEO: { label: "\u72ee\u5b50", glyph: "\u264c", shortLabel: "Le", color: "#c5915a" },
  VIRGO: { label: "\u5904\u5973", glyph: "\u264d", shortLabel: "Vi", color: "#94a17b" },
  LIBRA: { label: "\u5929\u79e4", glyph: "\u264e", shortLabel: "Li", color: "#8fa8b9" },
  SCORPIO: { label: "\u5929\u874e", glyph: "\u264f", shortLabel: "Sc", color: "#a88485" },
  SAGITTARIUS: { label: "\u5c04\u624b", glyph: "\u2650", shortLabel: "Sg", color: "#c38b66" },
  CAPRICORN: { label: "\u6469\u7faf", glyph: "\u2651", shortLabel: "Cp", color: "#8e8f93" },
  AQUARIUS: { label: "\u6c34\u74f6", glyph: "\u2652", shortLabel: "Aq", color: "#7f9cab" },
  PISCES: { label: "\u53cc\u9c7c", glyph: "\u2653", shortLabel: "Pi", color: "#95a0bf" },
};

const PLANET_META: Record<
  string,
  { label: string; glyph: string; shortLabel: string; color: string }
> = {
  SUN: { label: "\u592a\u9633", glyph: "\u2609", shortLabel: "Su", color: "#b7772a" },
  MOON: { label: "\u6708\u4eae", glyph: "\u263d", shortLabel: "Mo", color: "#607087" },
  MERCURY: { label: "\u6c34\u661f", glyph: "\u263f", shortLabel: "Me", color: "#3e6b86" },
  VENUS: { label: "\u91d1\u661f", glyph: "\u2640", shortLabel: "Ve", color: "#b15f66" },
  MARS: { label: "\u706b\u661f", glyph: "\u2642", shortLabel: "Ma", color: "#9f4a36" },
  JUPITER: { label: "\u6728\u661f", glyph: "\u2643", shortLabel: "Ju", color: "#8b5f2d" },
  SATURN: { label: "\u571f\u661f", glyph: "\u2644", shortLabel: "Sa", color: "#5d6776" },
  URANUS: { label: "\u5929\u738b\u661f", glyph: "\u2645", shortLabel: "Ur", color: "#537a88" },
  NEPTUNE: { label: "\u6d77\u738b\u661f", glyph: "\u2646", shortLabel: "Ne", color: "#4e6586" },
  PLUTO: { label: "\u51a5\u738b\u661f", glyph: "\u2647", shortLabel: "Pl", color: "#89594b" },
  NORTH_NODE: { label: "\u5317\u4ea4\u70b9", glyph: "\u260a", shortLabel: "NN", color: "#6d7682" },
  SOUTH_NODE: { label: "\u5357\u4ea4\u70b9", glyph: "\u260b", shortLabel: "SN", color: "#6d7682" },
  CHIRON: { label: "\u51ef\u9f99\u661f", glyph: "\u26b7", shortLabel: "Ch", color: "#6b7b7c" },
  JUNO: { label: "\u5a5a\u795e\u661f", glyph: "\u26b5", shortLabel: "Jn", color: "#9b6953" },
  CERES: { label: "\u8c37\u795e\u661f", glyph: "\u26b3", shortLabel: "Ce", color: "#647b56" },
  PALLAS: { label: "\u667a\u795e\u661f", glyph: "\u26b4", shortLabel: "Pa", color: "#5f7083" },
  VESTA: { label: "\u7076\u795e\u661f", glyph: "\u26b6", shortLabel: "Vs", color: "#8e5f55" },
};

const PLANET_ORDER = [
  "SUN",
  "MOON",
  "MERCURY",
  "VENUS",
  "MARS",
  "JUPITER",
  "SATURN",
  "URANUS",
  "NEPTUNE",
  "PLUTO",
  "CHIRON",
  "JUNO",
  "CERES",
  "PALLAS",
  "VESTA",
  "NORTH_NODE",
  "SOUTH_NODE",
];

const MATRIX_PLANETS = [
  "SUN",
  "MOON",
  "MERCURY",
  "VENUS",
  "MARS",
  "JUPITER",
  "SATURN",
  "URANUS",
  "NEPTUNE",
  "PLUTO",
];

const ASPECTS: AspectLine[] = [
  {
    key: "conjunction",
    symbol: "\u260c",
    title: "\u5408",
    kind: "conjunction",
    angle: 0,
    orb: 8,
    nature: "neutral",
    summary: "\u4e3b\u9898\u53e0\u52a0",
  },
  {
    key: "sextile",
    symbol: "\u26b9",
    title: "\u516d\u5408",
    kind: "sextile",
    angle: 60,
    orb: 4,
    nature: "supportive",
    summary: "\u534f\u540c\u4e0e\u5f15\u52a8",
  },
  {
    key: "square",
    symbol: "\u25a1",
    title: "\u5211",
    kind: "square",
    angle: 90,
    orb: 6,
    nature: "challenging",
    summary: "\u62c9\u626f\u4e0e\u51b2\u7a81",
  },
  {
    key: "trine",
    symbol: "\u25b3",
    title: "\u62f1",
    kind: "trine",
    angle: 120,
    orb: 6,
    nature: "supportive",
    summary: "\u987a\u6d41\u4e0e\u653e\u5927",
  },
  {
    key: "opposition",
    symbol: "\u260d",
    title: "\u51b2",
    kind: "opposition",
    angle: 180,
    orb: 8,
    nature: "challenging",
    summary: "\u5916\u90e8\u5f20\u529b\u4e0e\u955c\u50cf\u8bfe\u9898",
  },
];

const houseCusps = computed<NatalHouse[]>(() => {
  const source = Array.isArray(props.natalChart?.houses) ? props.natalChart?.houses : [];
  if (source.length) {
    return [...source]
      .map((item: Record<string, any>) => ({
        house: toNumber(item.house),
        sign: String(item.sign || ""),
        sign_label: item.sign_label,
        degree: toNumber(item.degree),
        title: item.title,
      }))
      .sort((left, right) => left.house - right.house);
  }

  const ascSign = props.natalChart?.ascendant?.sign;
  const ascDegree = toNumber(props.natalChart?.ascendant?.degree);
  const ascLongitude = longitudeFromSign(ascSign, ascDegree);
  if (ascLongitude == null) return [];

  return Array.from({ length: 12 }, (_, index) => {
    const longitude = normalizeLongitude(ascLongitude + index * 30);
    const signIndex = Math.floor(longitude / 30) % 12;
    const sign = SIGN_SEQUENCE[signIndex];
    return {
      house: index + 1,
      sign,
      sign_label: SIGN_META[sign]?.label,
      degree: longitude % 30,
      title: houseLabel(index + 1),
    };
  });
});

const ascendantLongitude = computed(() => {
  const direct = longitudeFromSign(
    props.natalChart?.ascendant?.sign,
    toNumber(props.natalChart?.ascendant?.degree)
  );
  if (direct != null) return direct;
  return houseCusps.value[0] ? longitudeFromSign(houseCusps.value[0].sign, houseCusps.value[0].degree) ?? 0 : 0;
});

const ascendantSignLabel = computed(
  () =>
    props.natalChart?.ascendant?.sign_label ||
    SIGN_META[props.natalChart?.ascendant?.sign || ""]?.label ||
    copy.unknown
);

const ascendantLine = computed(() => {
  const sign = ascendantSignLabel.value;
  const degree = formatDegree(toNumber(props.natalChart?.ascendant?.degree));
  return `${sign} ${degree}`;
});

const chartRulerLabel = computed(
  () => props.natalChart?.chart_ruler_label || PLANET_META[props.natalChart?.chart_ruler || ""]?.label || copy.unknown
);

const sectLabel = computed(() => props.natalChart?.sect_label || props.natalChart?.sect || copy.unknown);

const fallbackSignature = computed(() => {
  const asc = ascendantSignLabel.value;
  const ruler = chartRulerLabel.value;
  const rulerMeaning = getPlanetMeaning(props.natalChart?.chart_ruler);
  if (rulerMeaning) {
    return `${copy.ascendant}${asc} / ${copy.chartRuler}${ruler}。${rulerMeaning.label}代表${rulerMeaning.essence}`;
  }
  return `${copy.ascendant}${asc} / ${copy.chartRuler}${ruler}`;
});

const orderedPlanets = computed<PlanetView[]>(() => {
  const planets = props.natalChart?.planets || {};

  return Object.entries(planets)
    .filter(([key]) => Boolean(PLANET_META[key]))
    .map(([key, raw]) => {
      const record = raw as NatalPlanetRecord;
      const meta = PLANET_META[key];
      const longitude =
        Number.isFinite(Number(record.longitude))
          ? normalizeLongitude(toNumber(record.longitude))
          : longitudeFromSign(record.sign, toNumber(record.degree)) ?? 0;
      const signMeta = SIGN_META[record.sign || ""];
      const signLabel = record.sign_label || signMeta?.label || record.sign || copy.unknown;
      const house = toNumber(record.house);
      const houseTitle = record.house_title || houseLabel(house);
      const degree = toNumber(record.degree);
      const motion = record.retrograde ? copy.retrograde : copy.direct;
      const meaning = getPlanetMeaning(key);
      const detail = Array.from(new Set([record.gift, record.reason].filter(Boolean))).join(" ");

      return {
        key,
        label: meta.label,
        shortLabel: meta.shortLabel,
        glyph: meta.glyph,
        color: meta.color,
        sign: record.sign || "",
        signLabel,
        degree,
        house,
        houseTitle,
        degreeLabel: formatDegree(degree),
        dignity: record.dignity,
        dignityLabel: record.dignity_label || dignityLabel(record.dignity),
        retrograde: Boolean(record.retrograde),
        longitude,
        positionLine: `${signLabel} ${formatDegree(degree)} · ${houseLine(house, houseTitle)} · ${motion}`,
        meaningLine: meaning ? `${meaning.groupTitle}主题：${meaning.essence}` : "",
        descriptionLine: detail,
      };
    })
    .sort((left, right) => planetOrder(left.key) - planetOrder(right.key));
});

const dominantPlanetRows = computed<ReaderPlanetRow[]>(() =>
  (props.natalChart?.dominant_planets || []).slice(0, 4).map((item: Record<string, any>) => {
    const planetKey = String(item.planet || "");
    const meaning = getPlanetMeaning(planetKey);
    return {
      label: item.label || PLANET_META[planetKey]?.label || planetKey || copy.unknown,
      score: formatMaybeNumber(item.score),
      meaningLine: meaning ? `${meaning.groupTitle}核心：${meaning.focus}` : "",
      detailLine: item.reason || "",
    };
  })
);

const pressureRows = computed<PressureRow[]>(() =>
  (props.natalChart?.pressure_points || []).slice(0, 4).map((item: Record<string, any>) => {
    const planetKey = String(item.planet || "");
    const meaning = getPlanetMeaning(planetKey);
    return {
      label: item.label || PLANET_META[planetKey]?.label || planetKey || copy.unknown,
      score: formatMaybeNumber(item.score),
      meaningLine: meaning ? `这颗星管的是：${meaning.focus}` : "",
      reason: item.reason || meaning?.caution || "",
    };
  })
);

const zodiacSegments = computed(() =>
  SIGN_SEQUENCE.map((sign, index) => {
    const startLongitude = index * 30;
    const endLongitude = startLongitude + 30;
    const boundary = pointOnCircle(startLongitude, OUTER_RADIUS);
    const innerBoundary = pointOnCircle(startLongitude, ZODIAC_INNER_RADIUS);
    return {
      sign,
      glyph: SIGN_META[sign].glyph,
      shortLabel: SIGN_META[sign].shortLabel,
      color: SIGN_META[sign].color,
      path: ringSegmentPath(startLongitude, endLongitude, OUTER_RADIUS, ZODIAC_INNER_RADIUS),
      divider: {
        start: boundary,
        end: innerBoundary,
      },
    };
  })
);

const houseLines = computed(() =>
  houseCusps.value.map((cusp) => ({
    house: cusp.house,
    start: pointOnCircle(longitudeFromSign(cusp.sign, cusp.degree) ?? 0, ZODIAC_INNER_RADIUS),
    end: pointOnCircle(longitudeFromSign(cusp.sign, cusp.degree) ?? 0, HOUSE_INNER_RADIUS),
    isAxis: [1, 4, 7, 10].includes(cusp.house),
  }))
);

const houseLabels = computed(() =>
  houseCusps.value.map((cusp, index) => {
    const current = longitudeFromSign(cusp.sign, cusp.degree) ?? 0;
    const nextCusp = houseCusps.value[(index + 1) % houseCusps.value.length];
    const next = nextCusp ? longitudeFromSign(nextCusp.sign, nextCusp.degree) ?? current : current + 30;
    const midpoint = midpointLongitude(current, next);
    return {
      house: cusp.house,
      position: pointOnCircle(midpoint, HOUSE_LABEL_RADIUS),
    };
  })
);

const axisLabels = computed(() => {
  const map: Array<{ house: number; label: string }> = [
    { house: 1, label: "ASC" },
    { house: 4, label: "IC" },
    { house: 7, label: "DSC" },
    { house: 10, label: "MC" },
  ];
  return map
    .map((item) => {
      const cusp = houseCusps.value.find((entry) => entry.house === item.house);
      if (!cusp) return null;
      const longitude = longitudeFromSign(cusp.sign, cusp.degree) ?? 0;
      return {
        label: item.label,
        position: pointOnCircle(longitude, AXIS_LABEL_RADIUS),
      };
    })
    .filter(Boolean) as Array<{ label: string; position: { x: number; y: number } }>;
});

const cuspMarkers = computed(() =>
  houseCusps.value.map((cusp) => {
    const longitude = longitudeFromSign(cusp.sign, cusp.degree) ?? 0;
    const signMeta = SIGN_META[cusp.sign] || SIGN_META.ARIES;
    return {
      house: cusp.house,
      glyph: signMeta.glyph,
      degreeLabel: formatDegree(cusp.degree),
      icon: pointOnCircle(longitude, CUSP_ICON_RADIUS),
      degree: pointOnCircle(longitude, CUSP_TEXT_RADIUS),
    };
  })
);

const houseCuspDetails = computed(() =>
  houseCusps.value.map((cusp) => {
    const signMeta = SIGN_META[cusp.sign] || SIGN_META.ARIES;
    return {
      house: cusp.house,
      signLabel: cusp.sign_label || signMeta.label,
      degreeLabel: formatDegree(cusp.degree),
      title: cusp.title || houseLabel(cusp.house),
      glyph: signMeta.glyph,
    };
  })
);

const planetMarkers = computed(() => {
  const minimumGap = 7;
  const laneStep = 16;
  const sorted = orderedPlanets.value
    .map((planet) => ({
      ...planet,
      relativeLongitude: normalizeLongitude(planet.longitude - ascendantLongitude.value),
      lane: 0,
    }))
    .sort((left, right) => left.relativeLongitude - right.relativeLongitude);

  const placed = sorted.map((planet, index) => {
    let lane = 0;
    const previous = sorted[index - 1];
    if (previous) {
      const distance = planet.relativeLongitude - previous.relativeLongitude;
      if (distance < minimumGap) {
        lane = previous.lane + 1;
      }
    }

    planet.lane = lane;
    const radius = PLANET_BASE_RADIUS - lane * laneStep;
    const angle = angleFromLongitude(planet.longitude);

    return {
      ...planet,
      position: pointFromAngle(angle, radius),
      tickStart: pointFromAngle(angle, PLANET_TRACK_RADIUS + 6),
      tickEnd: pointFromAngle(angle, radius + 18),
      retro: pointFromAngle(angle + 11, radius - 18),
    };
  });

  if (placed.length > 1) {
    const first = placed[0];
    const last = placed[placed.length - 1];
    if (first.relativeLongitude + 360 - last.relativeLongitude < minimumGap) {
      const lane = last.lane + 1;
      const radius = PLANET_BASE_RADIUS - lane * laneStep;
      const angle = angleFromLongitude(first.longitude);
      first.position = pointFromAngle(angle, radius);
      first.tickEnd = pointFromAngle(angle, radius + 18);
      first.retro = pointFromAngle(angle + 11, radius - 18);
    }
  }

  return placed;
});

const aspectMatrixPlanets = computed(() =>
  orderedPlanets.value.filter((planet) => MATRIX_PLANETS.includes(planet.key))
);

const aspectRecords = computed<AspectRecord[]>(() => {
  const result: AspectRecord[] = [];
  const planets = aspectMatrixPlanets.value;

  for (let index = 0; index < planets.length; index += 1) {
    for (let cursor = index + 1; cursor < planets.length; cursor += 1) {
      const left = planets[index];
      const right = planets[cursor];
      const distance = angularDistance(left.longitude, right.longitude);
      const matched = ASPECTS
        .map((aspect) => ({
          ...aspect,
          delta: Math.abs(distance - aspect.angle),
        }))
        .filter((aspect) => aspect.delta <= aspect.orb)
        .sort((leftAspect, rightAspect) => leftAspect.delta - rightAspect.delta)[0];

      if (!matched) continue;

      result.push({
        from: left.key,
        to: right.key,
        kind: matched.kind,
        symbol: matched.symbol,
        title: `${left.label} ${matched.title} ${right.label}`,
        nature: matched.nature,
        summary: matched.summary,
        delta: matched.delta,
        closeness: matched.orb - matched.delta,
        start: pointOnCircle(left.longitude, ASPECT_RADIUS),
        end: pointOnCircle(right.longitude, ASPECT_RADIUS),
      });
    }
  }

  return result.sort((left, right) => right.closeness - left.closeness);
});

const wheelAspectLines = computed(() => aspectRecords.value.slice(0, 16));

const aspectLookup = computed(() => {
  const map = new Map<string, AspectRecord>();
  for (const aspect of aspectRecords.value) {
    map.set(pairKey(aspect.from, aspect.to), aspect);
  }
  return map;
});

const mutualReceptionPairSet = computed(() => {
  const pairs = new Set<string>();
  for (const item of props.advancedPatterns?.mutual_receptions || []) {
    const pair = Array.isArray(item?.pair) ? item.pair : [];
    if (pair.length !== 2) continue;
    pairs.add(pairKey(String(pair[0]), String(pair[1])));
  }
  return pairs;
});

const aspectMatrixRows = computed(() =>
  aspectMatrixPlanets.value.map((planet, rowIndex) => ({
    planet,
    cells: aspectMatrixPlanets.value.map((target, colIndex) => {
      if (planet.key === target.key) {
        return {
          key: `${planet.key}-${target.key}`,
          state: "diagonal",
          nature: "",
          symbol: "",
          orbLabel: "",
        };
      }

      if (colIndex > rowIndex) {
        return {
          key: `${planet.key}-${target.key}`,
          state: "upper",
          nature: "",
          symbol: "",
          orbLabel: "",
        };
      }

      const aspect = aspectLookup.value.get(pairKey(planet.key, target.key));
      if (!aspect) {
        return {
          key: `${planet.key}-${target.key}`,
          state: "empty",
          nature: "",
          symbol: "",
          orbLabel: "",
        };
      }

      return {
        key: `${planet.key}-${target.key}`,
        state: "filled",
        nature: aspect.nature,
        symbol: aspect.symbol,
        orbLabel: formatDegree(aspect.delta),
      };
    }),
  }))
);

const receptionRows = computed(() =>
  (props.advancedPatterns?.reception_groups || [])
    .map((item: Record<string, any>) => {
      const receiverKey = String(item.receiver || "");
      const receiverLabel = item.receiver_label || item.receiver || copy.unknown;
      const guests = (item.guests || []).filter((guest: Record<string, any>) => {
        const guestKey = String(guest.planet || "");
        if (!receiverKey || !guestKey) return false;
        return (
          aspectLookup.value.has(pairKey(receiverKey, guestKey)) ||
          mutualReceptionPairSet.value.has(pairKey(receiverKey, guestKey))
        );
      });

      if (!guests.length) return null;

      return {
        receiver: receiverLabel,
        position: `${houseLine(item.receiver_house, item.receiver_house_title)} / ${
          item.receiver_sign_label || item.receiver_sign || copy.unknown
        }`,
        guests: guests
          .map(
            (guest: Record<string, any>) =>
              `${guest.label || guest.planet || copy.unknown} · H${toNumber(guest.house)}`
          )
          .join(" / "),
        line: `${receiverLabel}接纳${guests
          .map((guest: Record<string, any>) => guest.label || guest.planet || copy.unknown)
          .join("/")}`,
      };
    })
    .filter(
      (item): item is { receiver: string; position: string; guests: string; line: string } =>
        Boolean(item)
    )
);

const mutualReceptionRows = computed(() =>
  (props.advancedPatterns?.mutual_receptions || []).map((item: Record<string, any>) => ({
    pair: (item.labels || item.pair || []).join(" / "),
    line: item.line || copy.unknown,
  }))
);

const hasTechnicalArea = computed(
  () =>
    aspectMatrixRows.value.length > 0 ||
    receptionRows.value.length > 0 ||
    mutualReceptionRows.value.length > 0
);

const aspectHighlights = computed<AspectHighlightRow[]>(() => {
  const source = props.natalChart?.major_aspects;
  if (Array.isArray(source) && source.length) {
    return source.slice(0, 6).map((item: Record<string, any>) => {
      const keys = extractPlanetKeysFromText(`${item.title || ""} ${item.summary || ""}`);
      const pairKeys = Array.isArray(item.pair) ? item.pair : [];
      return {
        title: item.title || copy.unknown,
        strengthLabel: formatMaybeNumber(item.strength),
        summary: item.summary || "",
        meaningLine: buildPlanetBlendLine(
          keys.length ? keys : [...pairKeys, item.from, item.to],
          "focus"
        ),
      };
    });
  }

  return aspectRecords.value.slice(0, 6).map((item) => ({
    title: item.title,
    strengthLabel: formatDegree(item.delta),
    summary: item.summary,
    meaningLine: buildPlanetBlendLine([item.from, item.to], "focus"),
  }));
});

const houseHighlights = computed(() => {
  const emphasis = props.natalChart?.house_emphasis;
  if (Array.isArray(emphasis) && emphasis.length) {
    return emphasis.slice(0, 6).map((item: Record<string, any>) => ({
      key: `${item.house}-${item.title || ""}`,
      title: `${houseLine(item.house, item.title)}`,
      value: formatMaybeNumber(item.weight),
      summary: (item.keywords || []).join(" / "),
    }));
  }

  return houseCuspDetails.value.slice(0, 6).map((item) => ({
    key: `house-${item.house}`,
    title: houseLine(item.house, item.title),
    value: item.degreeLabel,
    summary: item.signLabel,
  }));
});

function toNumber(value: unknown) {
  const number = Number(value);
  return Number.isFinite(number) ? number : 0;
}

function normalizeLongitude(value: number) {
  return ((value % 360) + 360) % 360;
}

function longitudeFromSign(sign?: string, degree?: number) {
  if (!sign) return null;
  const index = SIGN_SEQUENCE.indexOf(sign as (typeof SIGN_SEQUENCE)[number]);
  if (index < 0) return null;
  return normalizeLongitude(index * 30 + toNumber(degree));
}

function angleFromLongitude(longitude: number) {
  const relative = normalizeLongitude(longitude - ascendantLongitude.value);
  return normalizeLongitude(180 - relative);
}

function pointFromAngle(angle: number, radius: number) {
  const radians = (angle * Math.PI) / 180;
  return {
    x: CENTER + radius * Math.cos(radians),
    y: CENTER + radius * Math.sin(radians),
  };
}

function pointOnCircle(longitude: number, radius: number) {
  return pointFromAngle(angleFromLongitude(longitude), radius);
}

function ringSegmentPath(
  startLongitude: number,
  endLongitude: number,
  outerRadius: number,
  innerRadius: number,
  steps = 16
) {
  let end = endLongitude;
  while (end <= startLongitude) {
    end += 360;
  }

  const outerPoints: string[] = [];
  const innerPoints: string[] = [];

  for (let index = 0; index <= steps; index += 1) {
    const longitude = startLongitude + ((end - startLongitude) * index) / steps;
    const point = pointOnCircle(longitude, outerRadius);
    outerPoints.push(`${point.x.toFixed(2)} ${point.y.toFixed(2)}`);
  }

  for (let index = steps; index >= 0; index -= 1) {
    const longitude = startLongitude + ((end - startLongitude) * index) / steps;
    const point = pointOnCircle(longitude, innerRadius);
    innerPoints.push(`${point.x.toFixed(2)} ${point.y.toFixed(2)}`);
  }

  return `M ${outerPoints[0]} L ${outerPoints.slice(1).join(" L ")} L ${innerPoints.join(" L ")} Z`;
}

function midpointLongitude(start: number, end: number) {
  let endPoint = normalizeLongitude(end);
  const startPoint = normalizeLongitude(start);
  if (endPoint <= startPoint) {
    endPoint += 360;
  }
  return normalizeLongitude((startPoint + endPoint) / 2);
}

function angularDistance(left: number, right: number) {
  const delta = Math.abs(normalizeLongitude(left) - normalizeLongitude(right));
  return Math.min(delta, 360 - delta);
}

function pairKey(left: string, right: string) {
  return [left, right].sort().join(":");
}

function planetOrder(key: string) {
  const index = PLANET_ORDER.indexOf(key);
  return index >= 0 ? index : PLANET_ORDER.length + 1;
}

function dignityLabel(value?: string) {
  if (value === "domicile") return "\u5165\u5e99";
  if (value === "exaltation") return "\u64e2\u5347";
  if (value === "detriment") return "\u843d\u9677";
  if (value === "fall") return "\u5931\u52bf";
  return "\u5e73\u5e38";
}

function formatMaybeNumber(value: unknown) {
  const number = Number(value);
  return Number.isFinite(number) ? number.toFixed(2) : copy.unknown;
}

function formatDegree(value?: number) {
  if (typeof value !== "number" || Number.isNaN(value)) return copy.unknown;
  const totalMinutes = Math.min(Math.round(Math.abs(value) * 60), 29 * 60 + 59);
  const degrees = Math.floor(totalMinutes / 60);
  const minutes = totalMinutes % 60;
  return `${degrees}\u00b0${String(minutes).padStart(2, "0")}\u2032`;
}

function houseLabel(house: number) {
  return `\u7b2c${house}\u5bab`;
}

function houseLine(house: unknown, title?: string) {
  const value = toNumber(house);
  const label = title || houseLabel(value);
  return `H${value} ${label}`;
}
</script>

<style scoped>
.natal-section {
  margin-bottom: 24px;
}

.natal-panel {
  --paper: #f7f2e8;
  --paper-2: #fffdf8;
  --ink: #1f2937;
  --muted: #556171;
  --line: rgba(31, 41, 55, 0.14);
  --line-strong: rgba(31, 41, 55, 0.26);
  --accent: #7b5c24;
  --accent-soft: rgba(123, 92, 36, 0.12);
  --astro-font: "Segoe UI Symbol", "Noto Sans Symbols 2", "Symbola", "Apple Symbols", serif;
  padding: 22px;
  border-radius: 14px;
  border: 1px solid rgba(31, 41, 55, 0.16);
  background: var(--paper);
  box-shadow: 0 8px 22px rgba(15, 23, 42, 0.08);
}

.panel-header,
.section-header,
.table-title-row,
.planet-topline,
.reader-row,
.cusp-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
}

.panel-header {
  margin-bottom: 16px;
  padding-bottom: 14px;
  border-bottom: 1px solid var(--line);
}

.panel-copy {
  max-width: 760px;
}

.panel-kicker {
  color: #667085;
  font-size: 11px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.panel-title,
.section-heading {
  margin: 10px 0 0;
  color: var(--ink);
  font-family: "Iowan Old Style", "Palatino Linotype", "Book Antiqua", Palatino, serif;
  font-weight: 700;
  line-height: 1.14;
}

.panel-title {
  font-size: 28px;
}

.section-heading {
  font-size: 20px;
}

.panel-summary {
  margin: 12px 0 0;
  color: var(--muted);
  line-height: 1.72;
  font-size: 13px;
}

.header-chips,
.wheel-footer {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.header-chips {
  justify-content: flex-end;
}

.header-chip,
.footer-chip {
  display: inline-flex;
  align-items: center;
  min-height: 30px;
  padding: 0 10px;
  border-radius: 999px;
  border: 1px solid rgba(31, 41, 55, 0.12);
  background: rgba(255, 255, 255, 0.68);
  color: #475467;
  font-size: 12px;
  white-space: nowrap;
}

.chart-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(360px, 0.9fr);
  gap: 14px;
}

.wheel-card,
.detail-card,
.table-card,
.reader-card {
  border-radius: 12px;
  background: var(--paper-2);
  border: 1px solid rgba(31, 41, 55, 0.12);
  box-shadow: none;
}

.wheel-card {
  padding: 14px;
}

.wheel-frame {
  border-radius: 10px;
  border: 1px solid var(--line);
  background: #fffdf8;
  padding: 10px;
}

.wheel-svg {
  width: 100%;
  height: auto;
  display: block;
  overflow: visible;
}

.wheel-shadow {
  fill: rgba(31, 41, 55, 0.03);
}

.wheel-base {
  fill: #fffefb;
  stroke: var(--line-strong);
  stroke-width: 1.1;
}

.zodiac-segment {
  fill: var(--segment-fill);
  opacity: 0.16;
  stroke: rgba(29, 36, 48, 0.06);
  stroke-width: 0.7;
}

.zodiac-divider,
.ring-line,
.aspect-boundary {
  fill: none;
  stroke: rgba(29, 36, 48, 0.18);
}

.ring-line {
  stroke-width: 1;
}

.ring-line.soft,
.aspect-boundary {
  stroke-dasharray: 4 6;
  stroke: rgba(29, 36, 48, 0.12);
}

.zodiac-divider {
  stroke-width: 1;
}

.house-line {
  stroke: rgba(31, 41, 55, 0.28);
  stroke-width: 1;
}

.house-line.axis {
  stroke: rgba(123, 92, 36, 0.82);
  stroke-width: 1.5;
}

.aspect-line {
  fill: none;
  stroke-width: 1;
  opacity: 0.42;
}

.aspect-line.conjunction {
  stroke: rgba(92, 104, 120, 0.44);
}

.aspect-line.sextile {
  stroke: rgba(46, 125, 50, 0.62);
}

.aspect-line.square {
  stroke: rgba(198, 40, 40, 0.62);
}

.aspect-line.trine {
  stroke: rgba(46, 125, 50, 0.62);
}

.aspect-line.opposition {
  stroke: rgba(123, 31, 162, 0.62);
}

.center-disc {
  fill: #ffffff;
  stroke: rgba(29, 36, 48, 0.2);
  stroke-width: 1;
}

.astro-symbol {
  font-family: var(--astro-font);
  text-anchor: middle;
  dominant-baseline: middle;
}

.cusp-glyph {
  fill: #243041;
  font-size: 19px;
  font-weight: 700;
}

.planet-glyph {
  fill: var(--planet-accent, #1f2937);
  font-size: 21px;
  font-weight: 700;
}

.house-number,
.axis-label,
.center-kicker,
.center-main,
.center-sub,
.retro-flag,
.cusp-degree {
  text-anchor: middle;
  dominant-baseline: middle;
}

.house-number {
  fill: rgba(31, 41, 55, 0.84);
  font-size: 13px;
  font-weight: 700;
}

.axis-label {
  fill: rgba(75, 85, 99, 0.92);
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.12em;
}

.cusp-degree {
  fill: rgba(31, 41, 55, 0.7);
  font-size: 9px;
  font-weight: 700;
}

.planet-tick {
  stroke: rgba(31, 41, 55, 0.28);
  stroke-width: 1;
}

.retro-flag {
  fill: rgba(123, 92, 36, 0.9);
  font-size: 8px;
  font-weight: 700;
}

.center-kicker {
  fill: rgba(71, 84, 103, 0.92);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.1em;
}

.center-main {
  fill: var(--ink);
  font-size: 21px;
  font-weight: 700;
}

.center-sub {
  fill: rgba(31, 41, 55, 0.58);
  font-size: 12px;
}

.wheel-footer {
  margin-top: 12px;
  align-items: center;
}

.footer-text {
  color: var(--muted);
  font-size: 12px;
  line-height: 1.6;
}

.detail-card {
  padding: 14px;
  display: grid;
  gap: 14px;
}

.detail-section,
.reader-stack {
  display: grid;
  gap: 12px;
}

.section-title {
  color: #667085;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.planet-list {
  display: grid;
  gap: 8px;
}

.planet-row,
.cusp-card,
.reader-item,
.reader-row {
  border-radius: 18px;
}

.planet-row {
  display: grid;
  grid-template-columns: 48px minmax(0, 1fr);
  gap: 10px;
  padding: 12px;
  background: #ffffff;
  border: 1px solid var(--line);
  border-left: 2px solid var(--planet-accent);
}

.list-icon,
.matrix-icon,
.cusp-icon {
  width: 42px;
  height: 42px;
}

.matrix-icon {
  width: 34px;
  height: 34px;
}

.list-icon-glyph,
.matrix-icon-glyph,
.cusp-icon-glyph {
  fill: #243141;
}

.list-icon-glyph {
  font-size: 19px;
}

.matrix-icon-glyph {
  font-size: 16px;
}

.cusp-icon-glyph {
  font-size: 18px;
}

.list-icon-code,
.matrix-icon-code {
  fill: rgba(29, 36, 48, 0.72);
  font-size: 8px;
  font-weight: 700;
  text-anchor: middle;
  letter-spacing: 0.04em;
}

.planet-copy {
  min-width: 0;
}

.planet-topline strong,
.reader-row strong,
.cusp-sign strong {
  color: var(--ink);
}

.planet-meta,
.planet-note,
.cusp-sign p,
.reader-summary,
.reader-item p {
  margin: 0;
  color: var(--muted);
  line-height: 1.6;
  font-size: 12px;
}

.planet-meta,
.reader-summary {
  margin-top: 8px;
}

.planet-note {
  margin-top: 6px;
}

.planet-meaning,
.reader-emphasis,
.reader-subnote {
  margin: 0;
  line-height: 1.7;
}

.planet-meaning {
  margin-top: 6px;
  color: #2c4058;
  font-size: 12px;
}

.reader-emphasis {
  color: #2c4058;
  font-size: 12px;
}

.reader-subnote {
  color: var(--muted);
  font-size: 12px;
}

.state-chip {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  padding: 0 8px;
  border-radius: 999px;
  background: rgba(31, 41, 55, 0.04);
  color: var(--ink);
  border: 1px solid rgba(29, 36, 48, 0.08);
  font-size: 11px;
}

.state-chip.domicile,
.state-chip.exaltation {
  background: rgba(81, 122, 89, 0.12);
  color: #385342;
}

.state-chip.detriment,
.state-chip.fall {
  background: rgba(161, 84, 66, 0.12);
  color: #7a4539;
}

.cusp-grid,
.reader-grid,
.relation-grid {
  display: grid;
  gap: 12px;
}

.cusp-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.cusp-card {
  padding: 12px;
  background: #ffffff;
  border: 1px solid var(--line);
}

.cusp-index {
  color: var(--accent);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.cusp-line {
  color: var(--ink);
  font-size: 12px;
}

.cusp-sign {
  margin-top: 8px;
  display: grid;
  grid-template-columns: 42px minmax(0, 1fr);
  gap: 8px;
  align-items: center;
}

.technical-section,
.reader-section {
  margin-top: 18px;
}

.section-note {
  margin: 8px 0 0;
  color: var(--muted);
  line-height: 1.7;
  font-size: 13px;
}

.technical-fold {
  margin-top: 18px;
  border: 1px solid var(--line);
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.58);
}

.technical-fold[open] {
  background: rgba(255, 255, 255, 0.78);
}

.technical-toggle {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: center;
  padding: 18px;
  cursor: pointer;
  list-style: none;
}

.technical-toggle::-webkit-details-marker {
  display: none;
}

.technical-toggle-copy {
  min-width: 0;
}

.table-card {
  overflow: hidden;
}

.table-title-row {
  padding: 14px 14px 0;
}

.table-scroll {
  overflow-x: auto;
  padding: 10px 14px 14px;
}

.aspect-matrix,
.data-table {
  width: 100%;
  border-collapse: collapse;
}

.aspect-matrix {
  min-width: 760px;
  table-layout: fixed;
}

.data-table {
  min-width: 520px;
}

.aspect-matrix th,
.aspect-matrix td,
.data-table th,
.data-table td {
  border: 1px solid var(--line);
  vertical-align: middle;
}

.aspect-matrix th,
.data-table th {
  background: rgba(31, 41, 55, 0.035);
}

.aspect-matrix th {
  padding: 8px 6px;
}

.matrix-corner {
  width: 66px;
}

.matrix-planet {
  display: flex;
  justify-content: center;
  align-items: center;
}

.matrix-cell {
  width: 66px;
  height: 58px;
  padding: 0;
  text-align: center;
  background: #ffffff;
}

.matrix-cell.diagonal,
.matrix-cell.upper {
  background: rgba(29, 36, 48, 0.03);
}

.matrix-cell.empty {
  background: rgba(31, 41, 55, 0.015);
}

.matrix-cell.supportive {
  background: rgba(87, 131, 95, 0.14);
}

.matrix-cell.challenging {
  background: rgba(167, 95, 73, 0.14);
}

.matrix-cell.neutral {
  background: rgba(108, 118, 131, 0.14);
}

.matrix-symbol {
  color: var(--ink);
  font-size: 16px;
  line-height: 1;
}

.matrix-orb {
  margin-top: 4px;
  color: var(--muted);
  font-size: 9px;
  font-weight: 700;
}

.data-table th,
.data-table td {
  padding: 9px 10px;
  text-align: left;
}

.data-table th {
  color: #667085;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.data-table td {
  color: #344054;
  font-size: 12px;
  line-height: 1.6;
}

.data-table tbody tr:hover td {
  background: rgba(29, 36, 48, 0.02);
}

.reader-grid {
  margin-top: 12px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.reader-card {
  padding: 14px;
}

.reader-summary {
  color: var(--ink);
  line-height: 1.7;
  font-size: 13px;
}

.reader-stack {
  margin-top: 10px;
}

.reader-row {
  align-items: center;
  padding: 10px 12px;
  background: #ffffff;
  border: 1px solid var(--line);
}

.reader-row span {
  color: var(--accent);
  font-size: 12px;
  font-weight: 700;
}

.reader-item {
  padding: 12px;
  background: #ffffff;
  border: 1px solid var(--line);
}

.reader-item p {
  margin-top: 8px;
}

@media (max-width: 1200px) {
  .chart-layout,
  .reader-grid,
  .relation-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 920px) {
  .panel-header,
  .section-header {
    flex-direction: column;
  }

  .header-chips {
    justify-content: flex-start;
  }
}

@media (max-width: 720px) {
  .natal-panel {
    padding: 18px;
    border-radius: 22px;
  }

  .panel-title {
    font-size: 26px;
  }

  .wheel-card,
  .detail-card,
  .table-card,
  .reader-card {
    border-radius: 20px;
  }

  .cusp-grid {
    grid-template-columns: 1fr;
  }

  .aspect-matrix {
    min-width: 680px;
  }
}
</style>
