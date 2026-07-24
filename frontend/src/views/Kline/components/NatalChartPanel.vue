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

      <section class="reader-section primaryReaderSection">
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

      <details class="chartEvidenceFold" open>
        <summary class="technical-toggle chartEvidenceSummary">
          <div class="technical-toggle-copy">
            <div class="panel-kicker">{{ copy.chartEvidenceKicker }}</div>
            <h3 class="section-heading">{{ copy.chartEvidenceTitle }}</h3>
            <p class="section-note">{{ copy.chartEvidenceNote }}</p>
          </div>
          <span class="header-chip">{{ copy.chartEvidenceAction }}</span>
        </summary>

        <div class="chart-layout">
          <section class="wheel-card">
            <div class="wheel-frame">
              <svg
                class="wheel-svg"
                viewBox="0 0 640 640"
                role="img"
                :aria-label="copy.title"
              >
                <defs>
                  <clipPath :id="aspectClipId">
                    <circle :cx="CENTER" :cy="CENTER" :r="ASPECT_CLIP_RADIUS" />
                  </clipPath>
                </defs>

                <circle :cx="CENTER" :cy="CENTER" :r="OUTER_RADIUS" class="wheel-base" />

                <path
                  v-for="segment in zodiacSegments"
                  :key="segment.sign"
                  :d="segment.path"
                  class="zodiac-segment"
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
                <circle :cx="CENTER" :cy="CENTER" :r="PLANET_TRACK_RADIUS + 20" class="ring-line soft planet-outer-ring" />
                <circle :cx="CENTER" :cy="CENTER" :r="PLANET_TRACK_RADIUS" class="ring-line" />
                <circle :cx="CENTER" :cy="CENTER" :r="HOUSE_LABEL_RADIUS + 18" class="ring-line soft house-label-ring" />
                <circle :cx="CENTER" :cy="CENTER" :r="ASPECT_RADIUS" class="aspect-boundary" />
                <circle :cx="CENTER" :cy="CENTER" :r="HOUSE_INNER_RADIUS" class="inner-core-ring" />

                <g class="aspect-layer" :clip-path="`url(#${aspectClipId})`">
                  <line
                    v-for="line in wheelAspectLines"
                    :key="`${line.from}-${line.to}-${line.kind}`"
                    :x1="line.start.x"
                    :y1="line.start.y"
                    :x2="line.end.x"
                    :y2="line.end.y"
                    :class="['aspect-line', line.kind]"
                  />
                </g>

                <g v-for="tick in zodiacDegreeTicks" :key="`tick-${tick.key}`">
                  <line
                    :x1="tick.start.x"
                    :y1="tick.start.y"
                    :x2="tick.end.x"
                    :y2="tick.end.y"
                    :class="['degree-tick', { major: tick.major, sign: tick.signBoundary }]"
                  />
                  <text
                    v-if="tick.label"
                    :x="tick.labelPosition.x"
                    :y="tick.labelPosition.y"
                    class="degree-label"
                    :transform="tick.labelTransform"
                  >
                    {{ tick.label }}
                  </text>
                </g>

                <g v-for="label in zodiacSignLabels" :key="`zodiac-label-${label.sign}`">
                  <text
                    :x="label.position.x"
                    :y="label.position.y"
                    class="zodiac-glyph astro-symbol"
                    :style="{ '--zodiac-accent': label.color }"
                  >
                    {{ label.glyph }}
                  </text>
                </g>

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
                  <text
                    :x="axis.position.x"
                    :y="axis.position.y"
                    :text-anchor="axis.anchor"
                    class="axis-label"
                  >
                    {{ axis.label }}
                  </text>
                </g>

                <g v-for="cusp in cuspMarkers" :key="`cusp-${cusp.house}`" class="cusp-marker">
                  <text
                    :x="cusp.icon.x"
                    :y="cusp.icon.y - 1"
                    class="cusp-glyph astro-symbol"
                    :style="{ '--cusp-accent': cusp.color }"
                  >
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
                  <text
                    :x="planet.degreePosition.x"
                    :y="planet.degreePosition.y"
                    :text-anchor="planet.degreeAnchor"
                    class="planet-degree planet-degree-main"
                  >
                    {{ degreeParts(planet.degree).degrees }}
                  </text>
                  <text
                    :x="planet.minutePosition.x"
                    :y="planet.minutePosition.y"
                    :text-anchor="planet.degreeAnchor"
                    class="planet-degree planet-degree-minute"
                  >
                    {{ degreeParts(planet.degree).minutes }}
                  </text>
                </g>

              </svg>
            </div>
          </section>

          <aside class="detail-card classic-sidebar">
            <section class="detail-section">
              <div class="classic-table-title">{{ copy.planetStatusTable }}</div>
              <div class="classic-table-scroll">
                <table class="classic-table planet-status-table">
                  <thead>
                    <tr>
                      <th>{{ copy.planet }}</th>
                      <th>{{ copy.zodiacPosition }}</th>
                      <th>{{ copy.house }}</th>
                      <th>{{ copy.condition }}</th>
                      <th>{{ copy.motion }}</th>
                      <th>{{ copy.note }}</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="planet in orderedPlanets" :key="planet.key">
                      <td class="symbol-cell">
                        <div class="classic-symbol-wrap">
                          <span class="classic-symbol astro-symbol">{{ planet.glyph }}</span>
                          <span class="classic-symbol-label">{{ planet.label }}</span>
                        </div>
                      </td>
                      <td class="position-cell">
                        <strong>{{ planet.degreeLabel }}</strong>
                        <span>{{ planet.signLabel }}</span>
                      </td>
                      <td class="center-cell">
                        <strong>H{{ planet.house }}</strong>
                        <span class="cell-sub">{{ planet.houseTitle }}</span>
                      </td>
                      <td class="center-cell">
                        <span :class="['classic-state', planet.dignity || 'peregrine']">
                          {{ planet.dignityLabel }}
                        </span>
                      </td>
                      <td class="center-cell">{{ planet.retrograde ? copy.retrograde : copy.direct }}</td>
                      <td>
                        {{ planet.descriptionLine || planet.meaningLine || copy.unknown }}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </section>

            <section class="detail-section">
              <div class="classic-table-title">{{ copy.houseStatusTable }}</div>
              <div class="classic-table-scroll">
                <table class="classic-table house-status-table">
                  <thead>
                    <tr>
                      <th>{{ copy.house }}</th>
                      <th>{{ copy.zodiacPosition }}</th>
                      <th>{{ copy.sign }}</th>
                      <th>{{ copy.theme }}</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="house in houseCuspDetails" :key="house.house">
                      <td class="center-cell"><strong>H{{ house.house }}</strong></td>
                      <td class="center-cell">{{ house.degreeLabel }}</td>
                      <td class="symbol-cell">
                        <div class="classic-symbol-wrap">
                          <span class="classic-symbol astro-symbol">{{ house.glyph }}</span>
                          <span class="classic-symbol-label">{{ house.signLabel }}</span>
                        </div>
                      </td>
                      <td>{{ house.title }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </section>
          </aside>
        </div>
      </details>

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

          <article v-if="aspectMatrixRows.length" class="table-card classic-table-card">
            <div class="classic-table-title">{{ copy.aspectMatrix }}</div>
            <div class="classic-table-scroll">
              <table class="aspect-matrix classic-matrix">
                <thead>
                  <tr>
                    <th class="matrix-corner"></th>
                    <th v-for="planet in aspectMatrixPlanets" :key="`head-${planet.key}`">
                      <div class="matrix-planet">
                        <svg viewBox="0 0 34 34" class="matrix-icon" aria-hidden="true">
                          <text x="17" y="15" class="matrix-icon-glyph astro-symbol">{{ planet.glyph }}</text>
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
                        </svg>
                      </div>
                    </th>
                    <td
                      v-for="cell in row.cells"
                      :key="cell.key"
                      :class="['matrix-cell', cell.state, cell.nature, cell.kindClass]"
                      :title="cell.tooltip"
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

          <article v-if="relationFeatureRows.length" class="table-card classic-table-card">
            <div class="classic-table-title">{{ copy.relationTable }}</div>
            <div class="classic-table-scroll">
              <table class="classic-table relation-table">
                <thead>
                  <tr>
                    <th>{{ copy.type }}</th>
                    <th>{{ copy.combination }}</th>
                    <th>{{ copy.position }}</th>
                    <th>{{ copy.chain }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="row in relationFeatureRows" :key="`${row.type}-${row.line}`">
                    <td class="center-cell">{{ row.type }}</td>
                    <td>{{ row.combination }}</td>
                    <td>{{ row.position }}</td>
                    <td>{{ row.line }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </article>
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
  speed?: number;
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
  speed: number;
  longitude: number;
  positionLine: string;
  meaningLine: string;
  descriptionLine: string;
}

interface PlanetMarkerView extends PlanetView {
  position: { x: number; y: number };
  degreePosition: { x: number; y: number };
  minutePosition: { x: number; y: number };
  degreeAnchor: "start" | "middle" | "end";
  tickStart: { x: number; y: number };
  tickEnd: { x: number; y: number };
  retro: { x: number; y: number };
  relativeLongitude: number;
  lane: number;
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
  exactAngle: number;
  title: string;
  nature: "supportive" | "challenging" | "neutral";
  summary: string;
  delta: number;
  closeness: number;
  direction: "applying" | "separating" | "exact";
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
  cuspHint: "\u5bab\u5934\u5ea6\u6570\u5747\u4ee5\u201cxx\u00b0xx\u2032\u201d\u663e\u793a",
  planetTable: "\u661f\u4f53\u843d\u70b9",
  cuspTable: "\u5bab\u5934\u5ea6\u6570",
  planetStatusTable: "\u661f\u76d8\u8868",
  houseStatusTable: "\u5bab\u4f4d\u8868",
  professionalKicker: "\u0050rofessional\u0020\u0052eading",
  professionalTitle: "\u4e13\u4e1a\u5224\u8bfb\u533a",
  professionalNote:
    "\u76f8\u4f4d\u8868\u3001\u63a5\u7eb3\u8868\u3001\u4e92\u6eb6\u8868\u66f4\u9002\u5408\u4e13\u4e1a\u5360\u661f\u5e08\u76f4\u8bfb\uff0c\u6216\u8005\u4f60\u9700\u8981\u56de\u5934\u6821\u5bf9\u8bc1\u636e\u65f6\u518d\u5c55\u5f00\u3002",
  professionalAction: "\u5c55\u5f00\u4e13\u4e1a\u533a",
  chartEvidenceKicker: "\u0043hart\u0020\u0045vidence",
  chartEvidenceTitle: "\u672c\u547d\u76d8\u9762\u4e0e\u843d\u70b9\u8bc1\u636e",
  chartEvidenceNote:
    "\u5982\u679c\u4f60\u60f3\u56de\u5934\u770b\u661f\u76d8\u672c\u8eab\uff0c\u8fd9\u91cc\u4f1a\u5c55\u793a\u8f6e\u76d8\u3001\u884c\u661f\u843d\u70b9\u548c\u5bab\u4f4d\u8868\u3002",
  chartEvidenceAction: "\u5c55\u5f00\u76d8\u9762\u8bc1\u636e",
  aspectMatrix: "\u76f8\u4f4d\u8868",
  receptionTable: "\u63a5\u7eb3\u8868",
  mutualReceptionTable: "\u4e92\u6eb6\u8868",
  relationTable: "\u4e92\u6eb6\u63a5\u7eb3\u8868",
  planet: "\u661f\u4f53",
  zodiacPosition: "\u9ec4\u7ecf\u5ea6\u6570",
  house: "\u843d\u5bab",
  sign: "\u661f\u5ea7",
  theme: "\u4e3b\u9898",
  condition: "\u72b6\u6001",
  motion: "\u987a\u9006",
  note: "\u5907\u6ce8",
  receiver: "\u63a5\u7eb3\u661f",
  position: "\u843d\u70b9",
  guests: "\u88ab\u63a5\u7eb3\u661f",
  chain: "\u94fe\u8def",
  combination: "\u661f\u4f53\u7ec4\u5408",
  type: "\u7c7b\u578b",
  applying: "A",
  separating: "S",
  exact: "E",
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
const OUTER_RADIUS = 292;
const ZODIAC_INNER_RADIUS = 258;
const PLANET_TRACK_RADIUS = 222;
const PLANET_BASE_RADIUS = 218;
const HOUSE_LABEL_RADIUS = 136;
const HOUSE_INNER_RADIUS = 112;
const ASPECT_RADIUS = 136;
const ASPECT_POINT_RADIUS = ASPECT_RADIUS - 6;
const ASPECT_CLIP_RADIUS = ASPECT_RADIUS - 1;
const CUSP_ICON_RADIUS = 274;
const CUSP_TEXT_RADIUS = 288;
const AXIS_LABEL_RADIUS = 282;
const DEGREE_TICK_OUTER_RADIUS = 292;
const DEGREE_TICK_MINOR_RADIUS = 286;
const DEGREE_TICK_MAJOR_RADIUS = 281;
const DEGREE_LABEL_RADIUS = 282;
const ZODIAC_LABEL_RADIUS = 278;

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
  ARIES: { label: "\u767d\u7f8a", glyph: "\u2648", shortLabel: "Ar", color: "#C7352F" },
  TAURUS: { label: "\u91d1\u725b", glyph: "\u2649", shortLabel: "Ta", color: "#2F8F55" },
  GEMINI: { label: "\u53cc\u5b50", glyph: "\u264a", shortLabel: "Ge", color: "#2F55C7" },
  CANCER: { label: "\u5de8\u87f9", glyph: "\u264b", shortLabel: "Cn", color: "#356AC3" },
  LEO: { label: "\u72ee\u5b50", glyph: "\u264c", shortLabel: "Le", color: "#C7352F" },
  VIRGO: { label: "\u5904\u5973", glyph: "\u264d", shortLabel: "Vi", color: "#2F8F55" },
  LIBRA: { label: "\u5929\u79e4", glyph: "\u264e", shortLabel: "Li", color: "#2F55C7" },
  SCORPIO: { label: "\u5929\u874e", glyph: "\u264f", shortLabel: "Sc", color: "#356AC3" },
  SAGITTARIUS: { label: "\u5c04\u624b", glyph: "\u2650", shortLabel: "Sg", color: "#C7352F" },
  CAPRICORN: { label: "\u6469\u7faf", glyph: "\u2651", shortLabel: "Cp", color: "#2F8F55" },
  AQUARIUS: { label: "\u6c34\u74f6", glyph: "\u2652", shortLabel: "Aq", color: "#2F55C7" },
  PISCES: { label: "\u53cc\u9c7c", glyph: "\u2653", shortLabel: "Pi", color: "#356AC3" },
};

const PLANET_META: Record<
  string,
  { label: string; glyph: string; shortLabel: string; color: string }
> = {
  SUN: { label: "\u592a\u9633", glyph: "\u2609", shortLabel: "Su", color: "#E38B22" },
  MOON: { label: "\u6708\u4eae", glyph: "\u263d", shortLabel: "Mo", color: "#4F6E91" },
  MERCURY: { label: "\u6c34\u661f", glyph: "\u263f", shortLabel: "Me", color: "#2A6E8F" },
  VENUS: { label: "\u91d1\u661f", glyph: "\u2640", shortLabel: "Ve", color: "#B25A72" },
  MARS: { label: "\u706b\u661f", glyph: "\u2642", shortLabel: "Ma", color: "#C7352F" },
  JUPITER: { label: "\u6728\u661f", glyph: "\u2643", shortLabel: "Ju", color: "#2F8F55" },
  SATURN: { label: "\u571f\u661f", glyph: "\u2644", shortLabel: "Sa", color: "#5D6879" },
  URANUS: { label: "\u5929\u738b\u661f", glyph: "\u2645", shortLabel: "Ur", color: "#23819A" },
  NEPTUNE: { label: "\u6d77\u738b\u661f", glyph: "\u2646", shortLabel: "Ne", color: "#405EA8" },
  PLUTO: { label: "\u51a5\u738b\u661f", glyph: "\u2647", shortLabel: "Pl", color: "#8C1D46" },
  NORTH_NODE: { label: "\u5317\u4ea4\u70b9", glyph: "\u260a", shortLabel: "NN", color: "#6D3E9E" },
  SOUTH_NODE: { label: "\u5357\u4ea4\u70b9", glyph: "\u260b", shortLabel: "SN", color: "#6D3E9E" },
  CHIRON: { label: "\u51ef\u9f99\u661f", glyph: "\u26b7", shortLabel: "Ch", color: "#6A6F3D" },
  JUNO: { label: "\u5a5a\u795e\u661f", glyph: "\u26b5", shortLabel: "Jn", color: "#8B4F62" },
  CERES: { label: "\u8c37\u795e\u661f", glyph: "\u26b3", shortLabel: "Ce", color: "#4F7D45" },
  PALLAS: { label: "\u667a\u795e\u661f", glyph: "\u26b4", shortLabel: "Pa", color: "#516C8E" },
  VESTA: { label: "\u7076\u795e\u661f", glyph: "\u26b6", shortLabel: "Vs", color: "#8B5A3A" },
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
  {
    key: "quincunx",
    symbol: "\u26bb",
    title: "\u6885\u82b1",
    kind: "quincunx",
    angle: 150,
    orb: 3,
    nature: "challenging",
    summary: "\u8c03\u6574\u4e0e\u4ee3\u4ef7",
  },
];

const _legendItems = [
  { label: "\u5211/\u51b2", kind: "challenging", y: 12 },
  { label: "\u62f1/\u516d\u5408", kind: "supportive", y: 28 },
  { label: "\u6885\u82b1\u76f8", kind: "special", y: 44 },
];
void _legendItems;

const aspectClipId = `aspect-clip-${Math.random().toString(36).slice(2, 8)}`;

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
    const sign = (SIGN_SEQUENCE[signIndex] ?? "ARIES") as string;
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

      const metaSafe = meta!;
      return {
        key,
        label: metaSafe.label,
        shortLabel: metaSafe.shortLabel,
        glyph: metaSafe.glyph,
        color: signMeta?.color || metaSafe.color,
        sign: record.sign || "",
        signLabel,
        degree,
        house,
        houseTitle,
        degreeLabel: formatDegree(degree),
        dignity: record.dignity,
        dignityLabel: record.dignity_label || dignityLabel(record.dignity),
        retrograde: Boolean(record.retrograde),
        speed: toNumber(record.speed),
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
      path: ringSegmentPath(startLongitude, endLongitude, OUTER_RADIUS, ZODIAC_INNER_RADIUS),
      divider: {
        start: boundary,
        end: innerBoundary,
      },
    };
  })
);

const zodiacDegreeTicks = computed(() =>
  SIGN_SEQUENCE.flatMap((sign, signIndex) =>
    Array.from({ length: 30 }, (_, degreeIndex) => {
      const longitude = signIndex * 30 + degreeIndex;
      const signBoundary = degreeIndex === 0;
      const major = signBoundary || degreeIndex % 5 === 0;
      const label = degreeIndex % 10 === 0 ? `${degreeIndex}\u00b0` : "";
      const labelPosition = pointOnCircle(longitude + 5, DEGREE_LABEL_RADIUS);
      const labelAngle = angleFromLongitude(longitude + 5);
      return {
        key: `${sign}-${degreeIndex}`,
        major,
        signBoundary,
        label,
        start: pointOnCircle(longitude, DEGREE_TICK_OUTER_RADIUS),
        end: pointOnCircle(longitude, major ? DEGREE_TICK_MAJOR_RADIUS : DEGREE_TICK_MINOR_RADIUS),
        labelPosition,
        labelTransform: readableTextTransform(labelAngle, labelPosition),
      };
    })
  )
);

const zodiacSignLabels = computed(() =>
  SIGN_SEQUENCE.map((sign, index) => {
    const longitude = index * 30 + 15;
    const meta = SIGN_META[sign]!;
    return {
      sign,
      glyph: meta.glyph,
      color: meta.color,
      position: pointOnCircle(longitude, ZODIAC_LABEL_RADIUS),
    };
  })
);

const houseLines = computed(() =>
  houseCusps.value.map((cusp) => {
    const longitude = longitudeFromSign(cusp.sign, cusp.degree) ?? 0;
    const isAxis = [1, 4, 7, 10].includes(cusp.house);
    return {
      house: cusp.house,
      start: isAxis ? { x: CENTER, y: CENTER } : pointOnCircle(longitude, HOUSE_INNER_RADIUS),
      end: pointOnCircle(longitude, OUTER_RADIUS),
      isAxis,
    };
  })
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
  const axisMeta: Record<
    string,
    { offset: { x: number; y: number }; anchor: "start" | "middle" | "end" }
  > = {
    ASC: { offset: { x: -18, y: 0 }, anchor: "end" },
    DSC: { offset: { x: 18, y: 0 }, anchor: "start" },
    MC: { offset: { x: 0, y: -12 }, anchor: "middle" },
    IC: { offset: { x: 0, y: 12 }, anchor: "middle" },
  };
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
      const meta = axisMeta[item.label] || axisMeta.ASC!;
      const basePosition = pointOnCircle(longitude, AXIS_LABEL_RADIUS);
      return {
        label: item.label,
        anchor: meta.anchor,
        position: {
          x: basePosition.x + meta.offset.x,
          y: basePosition.y + meta.offset.y,
        },
      };
    })
    .filter(Boolean) as Array<{
      label: string;
      anchor: "start" | "middle" | "end";
      position: { x: number; y: number };
    }>;
});

const cuspMarkers = computed(() =>
  houseCusps.value.map((cusp) => {
    const longitude = longitudeFromSign(cusp.sign, cusp.degree) ?? 0;
    const signMeta = SIGN_META[cusp.sign] || SIGN_META.ARIES!;
    return {
      house: cusp.house,
      glyph: signMeta.glyph,
      color: signMeta.color,
      degreeLabel: formatDegree(cusp.degree),
      icon: pointOnCircle(longitude, CUSP_ICON_RADIUS),
      degree: pointOnCircle(longitude, CUSP_TEXT_RADIUS),
    };
  })
);

const houseCuspDetails = computed(() =>
  houseCusps.value.map((cusp) => {
    const signMeta = SIGN_META[cusp.sign] || SIGN_META.ARIES!;
    return {
      house: cusp.house,
      signLabel: cusp.sign_label || signMeta.label,
      degreeLabel: formatDegree(cusp.degree),
      title: cusp.title || houseLabel(cusp.house),
      glyph: signMeta.glyph,
    };
  })
);

const planetMarkers = computed<PlanetMarkerView[]>(() => {
  const minimumGap = 6;
  const laneStep = 13;
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
    const angleRadians = (angle * Math.PI) / 180;
    const onRightSide = Math.cos(angleRadians) >= 0;
    const position = pointFromAngle(angle, radius);
    const degreeOffsetX = onRightSide ? 12 : -12;
    const degreeOffsetY = Math.sin(angleRadians) > 0.64 ? -2 : 2;
    const degreeAnchor: "start" | "end" = onRightSide ? "start" : "end";

    return {
      ...planet,
      position,
      degreePosition: {
        x: position.x + degreeOffsetX,
        y: position.y + degreeOffsetY - 3,
      },
      minutePosition: {
        x: position.x + degreeOffsetX,
        y: position.y + degreeOffsetY + 6,
      },
      degreeAnchor,
      tickStart: pointFromAngle(angle, PLANET_TRACK_RADIUS + 3),
      tickEnd: pointFromAngle(angle, radius + 8),
      retro: pointFromAngle(angle + 9, radius - 13),
    };
  });

  if (placed.length > 1) {
    const first = placed[0]!;
    const last = placed[placed.length - 1]!;
    if (first.relativeLongitude + 360 - last.relativeLongitude < minimumGap) {
      const lane = last.lane + 1;
      const radius = PLANET_BASE_RADIUS - lane * laneStep;
      const angle = angleFromLongitude(first.longitude);
      const angleRadians = (angle * Math.PI) / 180;
      const onRightSide = Math.cos(angleRadians) >= 0;
      const position = pointFromAngle(angle, radius);
      const degreeOffsetX = onRightSide ? 12 : -12;
      const degreeOffsetY = Math.sin(angleRadians) > 0.64 ? -2 : 2;
      const degreeAnchor: "start" | "end" = onRightSide ? "start" : "end";
      first.position = position;
      first.degreePosition = {
        x: position.x + degreeOffsetX,
        y: position.y + degreeOffsetY - 3,
      };
      first.minutePosition = {
        x: position.x + degreeOffsetX,
        y: position.y + degreeOffsetY + 6,
      };
      first.degreeAnchor = degreeAnchor;
      first.tickEnd = pointFromAngle(angle, radius + 8);
      first.retro = pointFromAngle(angle + 9, radius - 13);
    }
  }

  return placed;
});

const aspectWheelPlanets = computed(() =>
  orderedPlanets.value.filter((planet) => Number.isFinite(planet.longitude))
);

const aspectMatrixPlanets = computed(() =>
  orderedPlanets.value.filter((planet) => MATRIX_PLANETS.includes(planet.key))
);

const aspectRecords = computed<AspectRecord[]>(() => {
  const result: AspectRecord[] = [];
  const planets = aspectWheelPlanets.value;

  for (let index = 0; index < planets.length; index += 1) {
    for (let cursor = index + 1; cursor < planets.length; cursor += 1) {
      const left = planets[index]!;
      const right = planets[cursor]!;
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
        exactAngle: matched.angle,
        title: `${left.label} ${matched.title} ${right.label}`,
        nature: matched.nature,
        summary: matched.summary,
        delta: matched.delta,
        closeness: matched.orb - matched.delta,
        direction: aspectDirection(left, right!, matched.angle, matched.delta),
        start: pointOnCircle(left.longitude, ASPECT_POINT_RADIUS),
        end: pointOnCircle(right.longitude, ASPECT_POINT_RADIUS),
      });
    }
  }

  return result.sort((left, right) => right.closeness - left.closeness);
});

const wheelAspectLines = computed(() =>
  aspectRecords.value
    .filter((aspect) => aspect.kind !== "conjunction")
    .sort((left, right) => {
      const weight: Record<string, number> = {
        square: 0,
        opposition: 0,
        trine: 1,
        sextile: 1,
        quincunx: 2,
      };
      return (weight[left.kind] ?? 3) - (weight[right.kind] ?? 3);
    })
);

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
          tooltip: "",
          kindClass: "",
        };
      }

      if (colIndex > rowIndex) {
        return {
          key: `${planet.key}-${target.key}`,
          state: "upper",
          nature: "",
          symbol: "",
          orbLabel: "",
          tooltip: "",
          kindClass: "",
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
          tooltip: "",
          kindClass: "",
        };
      }

      return {
        key: `${planet.key}-${target.key}`,
        state: "filled",
        nature: aspect.nature,
        symbol: aspect.symbol,
        orbLabel: formatAspectOrb(aspect.delta, aspect.direction),
        tooltip: `${aspect.title} | ${Math.round(aspect.exactAngle)}° | ${formatAspectOrb(
          aspect.delta,
          aspect.direction
        )}`,
        kindClass: `aspect-${aspect.kind}`,
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
      (item: { receiver: string; position: string; guests: string; line: string } | null): item is { receiver: string; position: string; guests: string; line: string } =>
        Boolean(item)
    )
);

const mutualReceptionRows = computed(() =>
  (props.advancedPatterns?.mutual_receptions || []).map((item: Record<string, any>) => ({
    pair: (item.labels || item.pair || []).join(" / "),
    line: item.line || copy.unknown,
  }))
);

const relationFeatureRows = computed(() => {
  const receptionFeatures = receptionRows.value.map((row: { receiver: string; guests: string; position: string; line: string }) => ({
    type: copy.receptionTable,
    combination: `${row.receiver} / ${row.guests}`,
    position: row.position,
    line: row.line,
  }));

  const mutualFeatures = mutualReceptionRows.value.map((row: { pair: string; line: string }) => ({
    type: copy.mutualReceptionTable,
    combination: row.pair,
    position: copy.unknown,
    line: row.line,
  }));

  return [...receptionFeatures, ...mutualFeatures];
});

const hasTechnicalArea = computed(
  () =>
    aspectMatrixRows.value.length > 0 ||
    relationFeatureRows.value.length > 0
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

function readableTextTransform(angle: number, position: { x: number; y: number }) {
  const rotation = angle > 90 && angle < 270 ? angle + 180 : angle;
  return `rotate(${rotation.toFixed(2)} ${position.x.toFixed(2)} ${position.y.toFixed(2)})`;
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

function degreeParts(value?: number) {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return { degrees: copy.unknown, minutes: "" };
  }
  const totalMinutes = Math.min(Math.round(Math.abs(value) * 60), 29 * 60 + 59);
  const degrees = Math.floor(totalMinutes / 60);
  const minutes = totalMinutes % 60;
  return {
    degrees: `${degrees}\u00b0`,
    minutes: `${String(minutes).padStart(2, "0")}\u2032`,
  };
}

function formatAspectOrb(value?: number, direction?: "applying" | "separating" | "exact") {
  if (typeof value !== "number" || Number.isNaN(value)) return copy.unknown;
  const totalMinutes = Math.round(Math.abs(value) * 60);
  const degrees = Math.floor(totalMinutes / 60);
  const minutes = totalMinutes % 60;
  const phase =
    direction === "applying"
      ? copy.applying
      : direction === "separating"
        ? copy.separating
        : copy.exact;
  return `${degrees}\u00b0${String(minutes).padStart(2, "0")}' ${phase}`;
}

function aspectDirection(
  left: PlanetView,
  right: PlanetView,
  exactAngle: number,
  delta: number
): "applying" | "separating" | "exact" {
  if (delta < 0.2) return "exact";

  const nextLeft = normalizeLongitude(left.longitude + left.speed);
  const nextRight = normalizeLongitude(right.longitude + right.speed);
  const nextDiff = angularDistance(nextLeft, nextRight);
  const nextDelta = Math.abs(nextDiff - exactAngle);

  return nextDelta < delta ? "applying" : "separating";
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

<style scoped lang="less">
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
  margin-top: 0;
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 0;
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
  width: min(100%, 560px);
  margin: 0 auto;
  padding: 0;
  background: #ffffff;
  border: 0;
  border-radius: 0;
}

.wheel-frame {
  border-radius: 2px;
  border: 0;
  background: #ffffff;
  padding: 0;
}

.wheel-svg {
  width: 100%;
  height: auto;
  display: block;
  overflow: visible;
  shape-rendering: geometricPrecision;
  text-rendering: geometricPrecision;
  background: #ffffff;
}

.wheel-svg text:not(.astro-symbol) {
  font-family: "Segoe UI", "PingFang SC", "Microsoft YaHei", "Noto Sans", sans-serif;
  font-variant-numeric: tabular-nums lining-nums;
}

.wheel-base {
  fill: #ffffff;
  stroke: #9a9a9a;
  stroke-width: 1.5;
}

.zodiac-segment {
  fill: #ffffff;
  opacity: 1;
  stroke: none;
  stroke-width: 0;
}

.zodiac-divider,
.ring-line,
.aspect-boundary {
  fill: none;
  stroke: #9f9f9f;
}

.ring-line {
  stroke-width: 1.25;
}

.ring-line.soft,
.aspect-boundary {
  stroke-dasharray: none;
  stroke: #a6a6a6;
}

.planet-outer-ring,
.house-label-ring {
  display: none;
}

.zodiac-divider {
  stroke: #a0a0a0;
  stroke-width: 1.1;
}

.degree-tick {
  stroke: #5f5f5f;
  stroke-width: 0.5;
}

.degree-tick.major {
  stroke: #555555;
  stroke-width: 0.55;
}

.degree-tick.sign {
  stroke: #555555;
  stroke-width: 0.8;
}

.degree-label {
  display: none;
}

.zodiac-glyph {
  fill: var(--zodiac-accent, #111111);
  font-size: 16px;
  font-weight: 800;
}

.house-line {
  stroke: #adadad;
  stroke-width: 1;
}

.house-line.axis {
  stroke: #000000;
  stroke-width: 1.45;
}

.aspect-line {
  fill: none;
  stroke-linecap: square;
  stroke-width: 1.15;
  opacity: 0.72;
}

.aspect-line.conjunction {
  stroke: #263238;
}

.aspect-line.sextile {
  stroke: #3848ff;
  stroke-dasharray: none;
}

.aspect-line.square {
  stroke: #ef6a73;
}

.aspect-line.trine {
  stroke: #3848ff;
}

.aspect-line.opposition {
  stroke: #ef6a73;
}

.aspect-line.quincunx {
  stroke: #2a9b3f;
  stroke-dasharray: none;
}

.aspect-layer {
  pointer-events: none;
}

.inner-core-ring {
  fill: none;
  stroke: #9f9f9f;
  stroke-width: 1.25;
}

.astro-symbol {
  font-family: var(--astro-font);
  text-anchor: middle;
  dominant-baseline: middle;
}

.cusp-glyph {
  fill: var(--cusp-accent, #111111);
  font-size: 11px;
  font-weight: 700;
}

.planet-glyph {
  fill: var(--planet-accent, #1f2937);
  font-size: 15.5px;
  font-weight: 700;
}

.house-number,
.retro-flag,
.cusp-degree,
.planet-degree {
  text-anchor: middle;
  dominant-baseline: middle;
}

.house-number {
  fill: #000000;
  font-size: 8px;
  font-weight: 700;
}

.axis-label {
  display: none;
}

.cusp-degree {
  fill: #000000;
  font-size: 7.5px;
  font-weight: 700;
}

.planet-tick {
  display: none;
}

.planet-degree {
  fill: #111111;
  font-size: 7.5px;
  font-weight: 700;
}

.planet-degree-main {
  font-size: 7.5px;
}

.planet-degree-minute {
  font-size: 7.5px;
}

.legend-box {
  fill: #ffffff;
  stroke: rgba(17, 17, 17, 0.72);
  stroke-width: 0.8;
}

.legend-line {
  stroke-width: 1.6;
}

.legend-line.challenging {
  stroke: rgba(198, 40, 40, 0.92);
}

.legend-line.supportive {
  stroke: rgba(30, 96, 178, 0.86);
}

.legend-line.special {
  stroke: rgba(37, 132, 88, 0.82);
  stroke-dasharray: 3 3;
}

.legend-text {
  fill: rgba(17, 17, 17, 0.78);
  font-size: 8px;
  dominant-baseline: middle;
}

.retro-flag {
  fill: rgba(123, 92, 36, 0.9);
  font-size: 8px;
  font-weight: 700;
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
  max-width: 980px;
  width: 100%;
  margin: 0 auto;
}

.classic-sidebar {
  gap: 10px;
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
  width: 28px;
  height: 28px;
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
  font-size: 18px;
  font-weight: 700;
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

.chartEvidenceFold {
  display: block;
  margin-top: 18px;
  border: 0;
  border-radius: 0;
  background: #ffffff;
}

.chartEvidenceFold[open] {
  background: #ffffff;
}

.chartEvidenceSummary,
.chartEvidenceFold > .technical-toggle,
.chartEvidenceFold .detail-card {
  display: none;
}

.primaryReaderSection {
  margin-top: 0;
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

.classic-table-card {
  border-radius: 6px;
  border: 1px solid rgba(145, 179, 191, 0.6);
  background: #ffffff;
}

.classic-table-title {
  padding: 10px 12px;
  border-bottom: 1px solid rgba(145, 179, 191, 0.45);
  background: #d6f7ff;
  color: #36505c;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.classic-table-scroll {
  overflow-x: auto;
}

.classic-table,
.aspect-matrix {
  width: 100%;
  border-collapse: collapse;
}

.aspect-matrix {
  min-width: 650px;
  table-layout: fixed;
  border: 1px solid rgba(145, 179, 191, 0.45);
}

.classic-table {
  min-width: 520px;
  background: #ffffff;
}

.classic-table th,
.classic-table td,
.aspect-matrix th,
.aspect-matrix td {
  border: 1px solid #b8d7e2;
  vertical-align: middle;
}

.classic-table th,
.aspect-matrix th {
  background: #dff2f8;
  color: #46606b;
  font-size: 11px;
  font-weight: 700;
}

.classic-table th {
  padding: 9px 10px;
  text-align: center;
}

.classic-table td {
  padding: 8px 10px;
  color: #344054;
  font-size: 12px;
  line-height: 1.55;
  background: #ffffff;
}

.classic-table tbody tr:nth-child(even) td {
  background: #fbfeff;
}

.classic-table tbody tr:hover td,
.aspect-matrix tbody tr:hover td,
.aspect-matrix tbody tr:hover th {
  background: #f5fbfd;
}

.aspect-matrix th {
  padding: 5px 2px;
  background: #dff2f8;
}

.matrix-corner {
  width: 52px;
}

.matrix-planet {
  display: flex;
  justify-content: center;
  align-items: center;
}

.matrix-cell {
  width: 56px;
  height: 48px;
  padding: 1px 2px 0;
  text-align: center;
  background: #ffffff;
}

.matrix-cell.diagonal,
.matrix-cell.upper {
  background: #edf8fc;
}

.matrix-cell.empty {
  background: #ffffff;
}

.matrix-cell.filled,
.matrix-cell.supportive {
  background: #ffffff;
}

.matrix-cell.challenging {
  background: #ffffff;
}

.matrix-cell.neutral {
  background: #ffffff;
}

.matrix-symbol {
  color: #243141;
  font-size: 17px;
  line-height: 1;
  font-weight: 700;
}

.matrix-orb {
  margin-top: 3px;
  color: #4f6470;
  font-size: 10px;
  font-weight: 700;
  line-height: 1.05;
}

.matrix-cell.aspect-conjunction .matrix-symbol,
.matrix-cell.aspect-conjunction .matrix-orb {
  color: #7a5b3a;
}

.matrix-cell.aspect-sextile .matrix-symbol,
.matrix-cell.aspect-sextile .matrix-orb {
  color: #1f63c1;
}

.matrix-cell.aspect-square .matrix-symbol,
.matrix-cell.aspect-square .matrix-orb {
  color: #bf2f1b;
}

.matrix-cell.aspect-trine .matrix-symbol,
.matrix-cell.aspect-trine .matrix-orb {
  color: #16733c;
}

.matrix-cell.aspect-opposition .matrix-symbol,
.matrix-cell.aspect-opposition .matrix-orb {
  color: #8f2d24;
}

.symbol-cell,
.center-cell,
.position-cell {
  text-align: center;
}

.position-cell strong,
.center-cell strong {
  display: block;
  color: #1f2937;
}

.position-cell span,
.cell-sub {
  display: block;
  margin-top: 3px;
  color: #667085;
  font-size: 11px;
}

.classic-symbol-wrap {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.classic-symbol {
  color: #243141;
  font-size: 20px;
  line-height: 1;
}

.classic-symbol-label {
  color: #667085;
  font-size: 11px;
  line-height: 1.2;
}

.classic-state {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 52px;
  min-height: 24px;
  padding: 0 8px;
  border-radius: 999px;
  border: 1px solid rgba(145, 179, 191, 0.45);
  background: #f9fdfe;
  color: #375564;
  font-size: 11px;
}

.classic-state.domicile,
.classic-state.exaltation {
  background: rgba(88, 147, 103, 0.12);
  color: #345844;
}

.classic-state.detriment,
.classic-state.fall {
  background: rgba(194, 104, 80, 0.12);
  color: #7a4539;
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

  .classic-table {
    min-width: 640px;
  }
}
</style>
