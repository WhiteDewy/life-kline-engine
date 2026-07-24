<template>
  <section v-if="hasContent" class="patternsSection">
    <article class="panel patternsPanel">
      <details class="patternsFold">
        <summary class="foldSummary">
          <div class="panelHeader">
            <div>
              <div class="panelEyebrow">底层关系</div>
              <h2 class="panelTitle">底层关系与专业解读</h2>
              <p class="panelSummary">
                {{
                  advancedPatterns?.summary ||
                  "如果你想知道前面的判断为什么成立，这里会把宫主链路、飞宫、接纳和转宫关系翻成人话，再把专业证据留在后面。"
                }}
              </p>
            </div>
            <span class="foldBadge">默认折叠 · 点击展开</span>
          </div>
        </summary>

        <div class="foldBody">
          <section v-if="visiblePatternReadings.length" class="readingBlock">
            <div class="blockTitle">这张盘为什么会这样运作</div>
            <p class="blockSummary">先看底层结构结论，再决定要不要继续核对术语链路。</p>

            <div class="readingGrid">
              <article
                v-for="item in visiblePatternReadings"
                :key="item.key"
                class="readingCard"
              >
                <div class="readingHead">
                  <h3 class="readingTitle">{{ item.title }}</h3>
                </div>
                <p class="readingSummary">{{ item.summary }}</p>
                <p v-if="item.risk_summary" class="readingRisk">{{ item.risk_summary }}</p>

                <ul v-if="visiblePoints(item.points).length" class="readingList">
                  <li v-for="point in visiblePoints(item.points)" :key="point">{{ point }}</li>
                </ul>

                <details v-if="item.evidence?.length" class="inlineFold">
                  <summary class="inlineSummary">看判断依据</summary>
                  <div class="evidenceRow">
                    <span v-for="evidence in item.evidence" :key="evidence" class="evidenceChip">
                      {{ evidence }}
                    </span>
                  </div>
                </details>
              </article>
            </div>
          </section>

          <section v-if="visibleCoreThreads.length" class="threadBlock">
            <div class="blockTitle">长期反复出现的主线</div>
            <p class="blockSummary">这些不是一次性的情绪，而是你的人生里反复会被点亮的结构主题。</p>

            <div class="threadGrid">
              <article
                v-for="item in visibleCoreThreads"
                :key="`${item.house}-${item.title}`"
                class="threadCard"
              >
                <div class="threadTitle">{{ item.title }}</div>
                <p class="threadSummary">{{ item.summary }}</p>
                <ul v-if="visiblePoints(item.points).length" class="threadList">
                  <li v-for="point in visiblePoints(item.points)" :key="point">{{ point }}</li>
                </ul>
              </article>
            </div>
          </section>

          <section v-if="visibleDerivedHouses.length" class="derivedBlock">
            <div class="blockTitle">这些关系会互相牵动什么</div>
            <p class="blockSummary">转宫最适合拿来看“一个关系主题，会把哪些现实场景一起带出来”。</p>

            <div class="derivedGrid">
              <article
                v-for="item in visibleDerivedHouses"
                :key="`${item.base_house}-${item.base_label}`"
                class="derivedCard"
              >
                <div class="threadTitle">{{ item.base_label }}</div>
                <p class="threadSummary">{{ item.summary }}</p>
                <div class="derivedList">
                  <div
                    v-for="link in visibleLinks(item.links)"
                    :key="`${link.label}-${link.radical_house}`"
                    class="derivedItem"
                  >
                    <strong>{{ link.line }}</strong>
                    <p>{{ link.ruler_line }}</p>
                    <p class="derivedHint">{{ link.title }} · {{ link.adult_meaning }}</p>
                  </div>
                </div>
              </article>
            </div>
          </section>

          <!-- ═══ v2.5 新增: 格局检测 ═══ -->

          <section v-if="visibleEnclosures.length" class="readingBlock">
            <div class="blockTitle">夹辅围荣格局</div>
            <p class="blockSummary">
              古典占星中的行星包围格局——两颗星体将中间星体"夹辅"，决定其掌管的领域是得助力还是承压力。
            </p>
            <div class="readingGrid">
              <article
                v-for="item in visibleEnclosures"
                :key="`${item.left_planet}-${item.enclosed_planet}-${item.right_planet}`"
                class="readingCard"
                :class="{
                  enclosureBenefic: item.pattern_type === 'benefic_enclosure',
                  enclosureMalefic: item.pattern_type === 'malefic_siege',
                }"
              >
                <div class="readingHead">
                  <span class="enclosureBadge" :class="item.pattern_type">
                    {{ enclosureTypeLabel(item.pattern_type) }}
                  </span>
                  <h3 class="readingTitle">{{ item.description }}</h3>
                </div>
                <p class="readingSummary">{{ item.significance }}</p>
              </article>
            </div>
          </section>

          <section v-if="visibleAspectPatterns.length" class="readingBlock">
            <div class="blockTitle">相位格局</div>
            <p class="blockSummary">
              星体间的特殊几何构型——T三角、大十字、大三角、风筝等，揭示了人生中持续运作的底层能量模式。
            </p>
            <div class="readingGrid">
              <article
                v-for="item in visibleAspectPatterns"
                :key="`${item.pattern_type}-${item.planets.join('-')}`"
                class="readingCard"
                :class="{ patternHigh: item.severity === 'high' }"
              >
                <div class="readingHead">
                  <span
                    class="patternBadge"
                    :class="item.pattern_type"
                  >
                    {{ patternTypeLabel(item.pattern_type) }}
                  </span>
                  <span
                    v-if="item.severity === 'high'"
                    class="severityBadge"
                  >高张力</span>
                </div>
                <p class="readingSummary">{{ item.description }}</p>
                <p class="readingRisk" v-if="item.severity === 'high'">
                  {{ item.interpretation }}
                </p>
                <p v-else class="threadSummary">{{ item.interpretation }}</p>
                <div v-if="item.houses?.length" class="metaRow">
                  <span
                    v-for="h in item.houses"
                    :key="h"
                    class="metaChip"
                  >第{{ h }}宫</span>
                </div>
              </article>
            </div>
          </section>

          <section
            v-if="interceptionInfo && (hasInterceptedSigns || hasExpandedRulers)"
            class="ruleBlock"
          >
            <div class="blockTitle">宫位劫夺</div>
            <p class="blockSummary">
              宫位劫夺会影响宫主星的权柄——被劫夺则话语权减弱，扩权则管理范围增加。
            </p>
            <div class="ruleChips">
              <span
                v-for="(sign, house) in interceptionInfo.intercepted_signs"
                :key="`int-${house}`"
                class="ruleChip intBadge"
              >
                第{{ house }}宫劫夺 {{ sign }}
              </span>
              <span
                v-for="(houses, ruler) in interceptionInfo.expanded_rulers"
                :key="`exp-${ruler}`"
                class="ruleChip expBadge"
              >
                {{ ruler }}权柄扩张至 {{ (houses as number[]).join('、') }}宫
              </span>
            </div>
          </section>

          <details v-if="hasTechnicalEvidence" class="innerFold">
            <summary class="innerSummary">
              <div>
                <div class="panelEyebrow">专业依据</div>
                <div class="blockTitle">继续看专业链路</div>
              </div>
              <span class="foldBadge innerBadge">展开术语依据</span>
            </summary>

            <div class="innerBody">
              <div v-if="advancedPatterns?.ruler_groups?.length" class="ruleBlock">
                <div class="blockTitle">宫主链路</div>
                <div class="ruleChips">
                  <span
                    v-for="item in advancedPatterns.ruler_groups"
                    :key="item.line"
                    class="ruleChip"
                  >
                    {{ item.line }}
                  </span>
                </div>
              </div>

              <div v-if="visibleHouseRulers.length" class="rulerBlock">
                <div class="blockTitle">飞宫目录</div>
                <div class="rulerGrid">
                  <article
                    v-for="item in visibleHouseRulers"
                    :key="`${item.house}-${item.line}`"
                    class="rulerCard"
                  >
                    <div class="rulerHead">
                      <div>
                        <div class="rulerKicker">{{ item.title }} · {{ item.notation }}</div>
                        <h3 class="rulerTitle">{{ item.line }}</h3>
                      </div>
                      <div class="rulerBadges">
                        <span
                          v-if="item.flight_tone_label"
                          class="toneChip"
                        >
                          {{ item.flight_tone_label }}
                        </span>
                        <span
                          v-if="fortuneForRuler(item.house, item.ruler_house)"
                          class="fortuneChip"
                          :class="fortuneLevelClass(fortuneForRuler(item.house, item.ruler_house).fortune_level)"
                        >
                          {{ fortuneLevelLabel(fortuneForRuler(item.house, item.ruler_house).fortune_level) }}
                          <span class="fortuneScore">
                            {{ fortuneForRuler(item.house, item.ruler_house).fortune_score > 0 ? '+' : '' }}{{ fortuneForRuler(item.house, item.ruler_house).fortune_score.toFixed(0) }}
                          </span>
                        </span>
                      </div>
                    </div>

                    <p v-if="item.flight_summary" class="rulerSummary">{{ item.flight_summary }}</p>
                    <p v-else class="rulerSummary">{{ item.adult_meaning || item.ruler_house_title }}</p>

                    <div class="metaRow">
                      <span class="metaChip">
                        {{ item.ruler_label }}落{{ item.ruler_house }}宫 · {{ item.ruler_house_title }}
                      </span>
                      <span v-if="item.dignity_label" class="metaChip">
                        先天状态 {{ item.dignity_label }}
                      </span>
                      <span v-if="item.flight_target_title" class="metaChip">
                        目标宫 {{ item.flight_target_title }}
                      </span>
                    </div>

                    <p v-if="item.flight_note" class="rulerNote">{{ item.flight_note }}</p>
                    <p v-if="item.late_five_note" class="rulerHint">{{ item.late_five_note }}</p>
                    <p v-if="item.flight_target_theme" class="rulerHint">
                      {{ item.flight_target_theme }}
                    </p>

                    <div
                      v-if="item.flight_positive || item.flight_negative"
                      class="rulerColumns"
                    >
                      <div v-if="item.flight_positive" class="rulerColumn">
                        <div class="columnLabel">顺手时</div>
                        <p>{{ item.flight_positive }}</p>
                      </div>
                      <div v-if="item.flight_negative" class="rulerColumn danger">
                        <div class="columnLabel">失衡时</div>
                        <p>{{ item.flight_negative }}</p>
                      </div>
                    </div>
                  </article>
                </div>
              </div>

              <div v-if="advancedPatterns?.reception_groups?.length" class="ruleBlock">
                <div class="blockTitle">接纳链</div>
                <div class="ruleChips">
                  <span
                    v-for="item in advancedPatterns.reception_groups"
                    :key="item.line"
                    class="ruleChip"
                  >
                    {{ item.line }}
                  </span>
                </div>
              </div>

              <div v-if="advancedPatterns?.mutual_receptions?.length" class="ruleBlock">
                <div class="blockTitle">互溶对</div>
                <div class="ruleChips">
                  <span
                    v-for="item in advancedPatterns.mutual_receptions"
                    :key="item.line"
                    class="ruleChip"
                  >
                    {{ item.line }}
                  </span>
                </div>
              </div>
            </div>
          </details>
        </div>
      </details>
    </article>
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{
  advancedPatterns: Record<string, any> | null;
}>();

const hasContent = computed(() => {
  const patterns = props.advancedPatterns;
  return Boolean(
    patterns?.house_rulers?.length ||
      patterns?.ruler_groups?.length ||
      patterns?.reception_groups?.length ||
      patterns?.mutual_receptions?.length ||
      patterns?.core_threads?.length ||
      patterns?.pattern_readings?.length ||
      patterns?.derived_houses?.length ||
      patterns?.enclosure_patterns?.length ||
      patterns?.aspect_patterns?.length ||
      patterns?.interception_info
  );
});

const visiblePatternReadings = computed(() =>
  Array.isArray(props.advancedPatterns?.pattern_readings)
    ? props.advancedPatterns.pattern_readings.slice(0, 4)
    : []
);

const visibleCoreThreads = computed(() =>
  Array.isArray(props.advancedPatterns?.core_threads)
    ? props.advancedPatterns.core_threads.slice(0, 4)
    : []
);

const visibleDerivedHouses = computed(() =>
  Array.isArray(props.advancedPatterns?.derived_houses)
    ? props.advancedPatterns.derived_houses.slice(0, 3)
    : []
);

const visibleHouseRulers = computed(() =>
  Array.isArray(props.advancedPatterns?.house_rulers)
    ? props.advancedPatterns.house_rulers.slice(0, 6)
    : []
);

const hasTechnicalEvidence = computed(() => {
  const patterns = props.advancedPatterns;
  return Boolean(
    patterns?.house_rulers?.length ||
      patterns?.ruler_groups?.length ||
      patterns?.reception_groups?.length ||
      patterns?.mutual_receptions?.length
  );
});

const visibleEnclosures = computed(() =>
  Array.isArray(props.advancedPatterns?.enclosure_patterns)
    ? props.advancedPatterns.enclosure_patterns
    : []
);

const visibleAspectPatterns = computed(() =>
  Array.isArray(props.advancedPatterns?.aspect_patterns)
    ? props.advancedPatterns.aspect_patterns
    : []
);

const flystarFortunes = computed(() =>
  props.advancedPatterns?.flystar_fortunes || {}
);

const interceptionInfo = computed(() =>
  props.advancedPatterns?.interception_info || null
);

function fortuneLevelLabel(level: string) {
  if (level === "fortunate") return "得吉";
  if (level === "afflicted") return "受克";
  return "中性";
}

function fortuneLevelClass(level: string) {
  if (level === "fortunate") return "fortuneGood";
  if (level === "afflicted") return "fortuneBad";
  return "fortuneNeutral";
}

function patternTypeLabel(type: string) {
  const labels: Record<string, string> = {
    t_square: "T三角",
    grand_cross: "大十字",
    grand_trine: "大三角",
    kite: "风筝",
  };
  return labels[type] || type;
}

function enclosureTypeLabel(type: string) {
  const labels: Record<string, string> = {
    benefic_enclosure: "吉星围荣",
    malefic_siege: "凶星夹困",
    mixed_enclosure: "吉凶夹辅",
  };
  return labels[type] || type;
}

function visiblePoints(points: unknown, limit = 3) {
  return Array.isArray(points) ? points.slice(0, limit) : [];
}

function visibleLinks(links: unknown, limit = 3) {
  return Array.isArray(links) ? links.slice(0, limit) : [];
}

function fortuneForRuler(sourceHouse: number, targetHouse: number) {
  const key = `${sourceHouse}R->${targetHouse}`;
  return flystarFortunes.value[key] || null;
}

const hasInterceptedSigns = computed(() => {
  const info = interceptionInfo.value;
  return info && Object.keys(info.intercepted_signs || {}).length > 0;
});

const hasExpandedRulers = computed(() => {
  const info = interceptionInfo.value;
  return info && Object.keys(info.expanded_rulers || {}).length > 0;
});
</script>

<style scoped lang="less">
.patternsSection {
  margin-bottom: 22px;
}

.patternsPanel {
  padding: 24px;
}

.patternsFold,
.innerFold {
  display: block;
}

.foldSummary,
.innerSummary {
  list-style: none;
  cursor: pointer;
}

.foldSummary::-webkit-details-marker,
.innerSummary::-webkit-details-marker,
.inlineSummary::-webkit-details-marker {
  display: none;
}

.foldBody {
  margin-top: 18px;
}

.panelHeader,
.innerSummary {
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

.panelSummary,
.blockSummary {
  margin: 12px 0 0;
  color: var(--text-secondary);
  line-height: 1.8;
}

.foldBadge {
  display: inline-flex;
  align-items: center;
  align-self: center;
  padding: 7px 12px;
  border-radius: 999px;
  border: 1px solid rgba(0,0,0,0.02);
  background: rgba(0,0,0,0.02);
  color: var(--text-secondary);
  font-size: 12px;
  white-space: nowrap;
}

.patternsFold[open] .foldBadge,
.innerFold[open] .foldBadge {
  color: var(--text);
  border-color: rgba(255,154,139, 0.24);
  background: rgba(255,154,139, 0.08);
}

.readingBlock,
.threadBlock,
.rulerBlock,
.ruleBlock,
.derivedBlock,
.innerFold {
  margin-top: 20px;
}

.innerFold {
  border-radius: 20px;
  border: 1px solid rgba(0,0,0,0.02);
  background: rgba(0,0,0,0.02);
}

.innerSummary {
  padding: 16px;
}

.innerBody {
  padding: 0 16px 16px;
}

.blockTitle,
.threadTitle {
  color: var(--text);
  font-size: 14px;
  font-weight: 700;
}

.ruleChips,
.evidenceRow {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.ruleChips {
  margin-top: 12px;
}

.ruleChip,
.evidenceChip {
  display: inline-flex;
  align-items: center;
  padding: 7px 12px;
  border-radius: 999px;
  border: 1px solid rgba(0,0,0,0.02);
  background: rgba(0,0,0,0.02);
  color: var(--text-secondary);
  font-size: 12px;
}

.rulerGrid,
.threadGrid,
.readingGrid,
.derivedGrid {
  margin-top: 18px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.rulerCard,
.threadCard,
.readingCard,
.derivedCard {
  padding: 16px;
  border-radius: 22px;
  border: 1px solid rgba(0,0,0,0.02);
  background:
    radial-gradient(circle at top left, rgba(255,154,139, 0.08), transparent 36%),
    rgba(2, 6, 23, 0.5);
}

.rulerHead {
  display: flex;
  justify-content: space-between;
  gap: 14px;
  align-items: flex-start;
}

.rulerKicker,
.columnLabel {
  color: var(--gold);
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.rulerTitle {
  margin: 8px 0 0;
  color: var(--text);
  font-size: 20px;
  line-height: 1.3;
}

.toneChip,
.metaChip {
  display: inline-flex;
  align-items: center;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(0,0,0,0.02);
  border: 1px solid rgba(0,0,0,0.02);
  color: var(--text-secondary);
  font-size: 12px;
}

.toneChip {
  color: var(--text);
  border-color: rgba(255,154,139, 0.24);
  background: rgba(255,154,139, 0.08);
  white-space: nowrap;
}

.rulerSummary,
.threadSummary,
.readingSummary {
  margin: 10px 0 0;
  color: var(--text-secondary);
  line-height: 1.75;
}

.rulerSummary,
.readingSummary {
  color: #4a3728;
  font-weight: 600;
}

.metaRow {
  margin-top: 14px;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.rulerNote {
  margin: 14px 0 0;
  color: var(--text);
  line-height: 1.8;
}

.rulerHint,
.derivedItem p {
  margin: 12px 0 0;
  color: var(--text-secondary);
  line-height: 1.75;
}

.rulerColumns {
  margin-top: 16px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.rulerColumn,
.derivedItem {
  padding: 14px;
  border-radius: 16px;
  background: rgba(0,0,0,0.02);
  border: 1px solid rgba(0,0,0,0.02);
}

.rulerColumn.danger {
  border-color: rgba(248, 113, 113, 0.16);
  background: rgba(127, 29, 29, 0.12);
}

.rulerColumn p {
  margin: 10px 0 0;
  color: var(--text-secondary);
  line-height: 1.75;
}

.readingTitle {
  margin: 0;
  color: var(--text);
  font-size: 22px;
  line-height: 1.25;
}

.readingRisk {
  margin: 12px 0 0;
  padding: 12px 14px;
  border-radius: 14px;
  border: 1px solid rgba(248, 113, 113, 0.18);
  background: rgba(127, 29, 29, 0.18);
  color: #fecaca;
  line-height: 1.75;
}

.threadList,
.readingList {
  margin: 14px 0 0;
  padding: 0;
  list-style: none;
  display: grid;
  gap: 10px;
}

.threadList li,
.readingList li {
  color: var(--text-secondary);
  line-height: 1.75;
  padding-left: 18px;
  position: relative;
}

.threadList li::before,
.readingList li::before {
  content: "";
  position: absolute;
  left: 0;
  top: 10px;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--gold);
  box-shadow: 0 0 16px rgba(255,154,139, 0.28);
}

.inlineFold {
  margin-top: 14px;
  padding-top: 14px;
  border-top: 1px solid rgba(0,0,0,0.02);
}

.inlineSummary {
  list-style: none;
  cursor: pointer;
  color: var(--text-secondary);
  font-size: 13px;
}

.derivedList {
  margin-top: 12px;
  display: grid;
  gap: 12px;
}

.derivedItem strong {
  color: var(--text);
  font-size: 13px;
}

.derivedHint {
  opacity: 0.9;
}

/* ── v2.5 格局与fortune样式 ── */

.rulerBadges {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.fortuneChip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 6px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
}

.fortuneChip.fortuneGood {
  color: #065f46;
  background: rgba(52, 211, 153, 0.14);
  border: 1px solid rgba(52, 211, 153, 0.28);
}

.fortuneChip.fortuneBad {
  color: #991b1b;
  background: rgba(248, 113, 113, 0.14);
  border: 1px solid rgba(248, 113, 113, 0.28);
}

.fortuneChip.fortuneNeutral {
  color: #92400e;
  background: rgba(251, 191, 36, 0.12);
  border: 1px solid rgba(251, 191, 36, 0.24);
}

.fortuneScore {
  opacity: 0.7;
  font-weight: 400;
}

.enclosureBadge,
.patternBadge {
  display: inline-flex;
  align-items: center;
  padding: 5px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
}

.enclosureBadge.benefic_enclosure {
  color: #065f46;
  background: rgba(52, 211, 153, 0.16);
}

.enclosureBadge.malefic_siege {
  color: #991b1b;
  background: rgba(248, 113, 113, 0.16);
}

.enclosureBadge.mixed_enclosure {
  color: #92400e;
  background: rgba(251, 191, 36, 0.14);
}

.enclosureBenefic {
  border-color: rgba(52, 211, 153, 0.18);
}

.enclosureMalefic {
  border-color: rgba(248, 113, 113, 0.18);
}

.patternBadge.t_square {
  color: #991b1b;
  background: rgba(248, 113, 113, 0.16);
}

.patternBadge.grand_cross {
  color: #7f1d1d;
  background: rgba(220, 38, 38, 0.2);
}

.patternBadge.grand_trine {
  color: #065f46;
  background: rgba(52, 211, 153, 0.16);
}

.patternBadge.kite {
  color: #1e40af;
  background: rgba(96, 165, 250, 0.16);
}

.severityBadge {
  display: inline-flex;
  align-items: center;
  padding: 4px 8px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  color: #991b1b;
  background: rgba(248, 113, 113, 0.12);
}

.patternHigh {
  border-color: rgba(248, 113, 113, 0.18);
}

.intBadge {
  color: #92400e;
  background: rgba(251, 191, 36, 0.12);
}

.expBadge {
  color: #065f46;
  background: rgba(52, 211, 153, 0.12);
}

@media (max-width: 1100px) {
  .rulerGrid,
  .threadGrid,
  .readingGrid,
  .derivedGrid,
  .rulerColumns {
    grid-template-columns: 1fr;
  }

  .panelHeader,
  .rulerHead,
  .innerSummary {
    flex-direction: column;
  }
}
</style>
