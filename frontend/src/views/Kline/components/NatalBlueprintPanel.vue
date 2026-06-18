<template>
  <section v-if="blueprint" class="blueprintSection">
    <article class="panel blueprintPanel">
      <div class="panelHeader">
        <div class="panelCopy">
          <div class="panelEyebrow">Natal Blueprint</div>
          <h2 class="panelTitle">本命蓝图</h2>
          <p class="panelNote">{{ panelNote }}</p>
        </div>
      </div>

      <section v-if="selfProfile" class="profileSection">
        <div class="sectionEyebrow">Self Reading</div>
        <h3 class="sectionTitle">{{ selfProfile.title || "先认识你自己" }}</h3>
        <p v-if="selfProfile.summary" class="sectionSummary">{{ selfProfile.summary }}</p>
        <p v-if="selfProfile.baseline" class="profileBaseline">{{ selfProfile.baseline }}</p>

        <div v-if="selfProfile.cards?.length" class="profileCardGrid">
          <article
            v-for="item in selfProfile.cards"
            :key="`${item.label}-${item.value}`"
            class="profileCard"
          >
            <div class="signalLabel">{{ item.label }}</div>
            <div class="signalValue">{{ item.value }}</div>
            <p v-if="item.hint" class="signalHint">{{ item.hint }}</p>
          </article>
        </div>

        <div v-if="selfProfile.evidence?.length" class="evidenceRow">
          <span v-for="item in selfProfile.evidence" :key="item" class="evidenceChip">
            {{ item }}
          </span>
        </div>

        <ul v-if="selfProfile.points?.length" class="layerList profileList">
          <li v-for="point in selfProfile.points" :key="point">{{ point }}</li>
        </ul>
      </section>

      <section v-if="insightLayers.length" class="insightSection">
        <div class="sectionEyebrow">Structure & Leverage</div>
        <h3 class="sectionTitle">结构与杠杆</h3>
        <p class="sectionSummary">
          先看这张盘长期会反复回到哪些课题，再看资源如何放大，优势又会从哪里反噬。
        </p>

        <div v-if="stepItems.length" class="stepRail">
          <article v-for="item in stepItems" :key="item.key" class="stepCard">
            <div class="stepIndex">{{ item.order }}</div>
            <h3 class="stepTitle">{{ item.title }}</h3>
            <p class="stepQuestion">{{ item.question }}</p>
          </article>
        </div>

        <div class="layerGrid">
          <article v-for="layer in insightLayers" :key="layer.key" class="layerCard">
            <div class="layerMetaRow">
              <span class="layerStep">{{ getLayerMeta(layer.key).order }}</span>
              <span class="layerQuestion">{{ getLayerMeta(layer.key).question }}</span>
            </div>

            <div class="layerHead">
              <div class="layerEyebrow">{{ layer.title }}</div>
              <h3 class="layerTitle">{{ layer.headline }}</h3>
            </div>

            <p v-if="layer.summary" class="layerSummary">{{ layer.summary }}</p>

            <div v-if="layer.evidence?.length" class="evidenceRow">
              <span v-for="item in layer.evidence" :key="item" class="evidenceChip">
                {{ item }}
              </span>
            </div>

            <div v-if="layer.focus_cards?.length" class="focusGrid">
              <article
                v-for="card in layer.focus_cards.slice(0, 2)"
                :key="`${card.label}-${card.value}`"
                class="focusCard"
              >
                <div class="focusLabel">{{ card.label }}</div>
                <div class="focusValue">{{ card.value }}</div>
                <p v-if="card.hint" class="focusHint">{{ card.hint }}</p>
              </article>
            </div>

            <ul v-if="layer.points?.length" class="layerList">
              <li v-for="point in layer.points" :key="point">{{ point }}</li>
            </ul>
          </article>
        </div>
      </section>

      <section v-if="careerBlueprint" class="careerSection">
        <div class="sectionEyebrow">Career Blueprint</div>
        <h3 class="sectionTitle">{{ careerBlueprint.title || "职业路线" }}</h3>
        <p v-if="careerBlueprint.summary" class="sectionSummary">{{ careerBlueprint.summary }}</p>

        <div v-if="careerBlueprint.method_tags?.length" class="evidenceRow">
          <span v-for="item in careerBlueprint.method_tags" :key="item" class="evidenceChip">
            {{ item }}
          </span>
        </div>

        <div v-if="careerBlueprint.paths?.length" class="careerGrid">
          <article
            v-for="path in careerBlueprint.paths"
            :key="path.key"
            class="careerCard"
          >
            <div class="careerTop">
              <div>
                <div class="careerFit">{{ path.track_label || path.fit_label }}</div>
                <h4 class="careerTitle">{{ path.title }}</h4>
              </div>
              <div class="careerScore">
                <span class="careerScoreLabel">匹配度</span>
                <strong>{{ formatFitScore(path.fit_score) }}</strong>
              </div>
            </div>

            <p class="careerSummary">{{ path.summary }}</p>
            <p v-if="path.track_reason" class="careerDecision">{{ path.track_reason }}</p>
            <p v-if="path.risk_summary" class="careerRisk">{{ path.risk_summary }}</p>

            <div v-if="path.selection_tags?.length" class="careerTagRow">
              <span v-for="item in path.selection_tags" :key="item" class="careerTag">
                {{ item }}
              </span>
            </div>

            <ul v-if="path.points?.length" class="layerList careerList">
              <li v-for="point in path.points" :key="point">{{ point }}</li>
            </ul>

            <div v-if="path.sources?.length" class="careerSourceRow">
              <div class="careerSubTitle">路径来源</div>
              <div class="evidenceRow compactEvidence">
                <span v-for="item in path.sources" :key="item" class="evidenceChip">
                  {{ item }}
                </span>
              </div>
            </div>

            <div v-if="path.theory?.length" class="careerTheory">
              <div class="careerSubTitle">理论依据</div>
              <p v-for="item in path.theory" :key="item">{{ item }}</p>
            </div>

            <div v-if="path.evidence?.length" class="evidenceRow compactEvidence">
              <span v-for="item in path.evidence" :key="item" class="evidenceChip">
                {{ item }}
              </span>
            </div>
          </article>
        </div>

        <p v-else class="sectionSummary">当前还没有足够稳定的职业路径，请先回看命主入口和重点宫位。</p>

        <p v-if="careerBlueprint.selection_prompt" class="careerPrompt">
          {{ careerBlueprint.selection_prompt }}
        </p>
      </section>

      <details v-if="theoryBasis" class="theoryFold">
        <summary class="theorySummary">
          <div>
            <div class="sectionEyebrow">Theory</div>
            <h3 class="sectionTitle theoryTitle">{{ theoryBasis.title || "理论依据区" }}</h3>
          </div>
          <span class="theoryBadge">默认折叠 / 点击展开</span>
        </summary>

        <div class="theoryBody">
          <p v-if="theoryBasis.summary" class="sectionSummary">{{ theoryBasis.summary }}</p>

          <div v-if="theoryBasis.chips?.length" class="evidenceRow">
            <span v-for="item in theoryBasis.chips" :key="item" class="evidenceChip">
              {{ item }}
            </span>
          </div>

          <ul v-if="theoryBasis.points?.length" class="layerList theoryList">
            <li v-for="point in theoryBasis.points" :key="point">{{ point }}</li>
          </ul>
        </div>
      </details>
    </article>
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";

interface BlueprintSignal {
  label: string;
  value: string;
  hint?: string;
}

interface BlueprintFocusCard {
  label: string;
  value: string;
  hint?: string;
}

interface BlueprintLayer {
  key: string;
  title: string;
  headline: string;
  summary?: string;
  evidence?: string[];
  focus_cards?: BlueprintFocusCard[];
  points?: string[];
}

interface BlueprintSelfProfile {
  title?: string;
  summary?: string;
  baseline?: string;
  cards?: BlueprintSignal[];
  evidence?: string[];
  points?: string[];
}

interface CareerPath {
  key: string;
  title: string;
  fit_score: number;
  fit_label: string;
  track_label?: string;
  track_reason?: string;
  summary: string;
  risk_summary?: string;
  sources?: string[];
  selection_tags?: string[];
  evidence?: string[];
  theory?: string[];
  points?: string[];
}

interface CareerBlueprint {
  title?: string;
  summary?: string;
  selection_prompt?: string;
  method_tags?: string[];
  paths?: CareerPath[];
}

interface TheoryBasis {
  title?: string;
  summary?: string;
  chips?: string[];
  points?: string[];
}

const PANEL_NOTE =
  "\u7528\u6237\u770b\u672c\u547d\u84dd\u56fe\uff0c\u5176\u5b9e\u662f\u60f3\u5148\u77e5\u9053\u81ea\u5df1\u662f\u4ec0\u4e48\u6837\u7684\u4eba\u3002\u6240\u4ee5\u5148\u770b\u57fa\u8c03\u548c\u89d2\u8272\uff0c\u518d\u770b\u7ed3\u6784\u3001\u6760\u6746\u3001\u804c\u4e1a\u8def\u7ebf\u548c\u4ee3\u4ef7\u3002";

const props = defineProps<{
  blueprint: Record<string, any> | null;
}>();

const LAYER_META: Record<string, { order: string; question: string }> = {
  role: {
    order: "01",
    question: "\u4f60\u5728\u793e\u4f1a\u91cc\u662f\u4ec0\u4e48\u89d2\u8272",
  },
  structure: {
    order: "01",
    question: "\u8fd9\u5f20\u76d8\u9760\u4ec0\u4e48\u957f\u671f\u8fd0\u8f6c",
  },
  power: {
    order: "02",
    question: "\u4f60\u9760\u4ec0\u4e48\u62ff\u8d44\u6e90\u548c\u653e\u5927\u7ed3\u679c",
  },
  cost: {
    order: "03",
    question: "\u4f60\u7684\u4f18\u52bf\u6700\u5bb9\u6613\u4ece\u54ea\u91cc\u53cd\u566c",
  },
};

const DEFAULT_LAYER_META = {
  order: "--",
  question: "\u8fd9\u4e00\u5c42\u5728\u56de\u7b54\u4ec0\u4e48",
};

function getLayerMeta(key?: string) {
  if (!key) return DEFAULT_LAYER_META;
  return LAYER_META[key] || DEFAULT_LAYER_META;
}

const panelNote = computed(() => PANEL_NOTE);

const orderedLayers = computed<BlueprintLayer[]>(() => {
  const source = Array.isArray(props.blueprint?.layers)
    ? (props.blueprint?.layers as BlueprintLayer[])
    : [];
  const order = ["role", "structure", "power", "cost"];

  return [...source].sort((left, right) => {
    const leftIndex = order.indexOf(left.key);
    const rightIndex = order.indexOf(right.key);
    return (leftIndex === -1 ? 99 : leftIndex) - (rightIndex === -1 ? 99 : rightIndex);
  });
});

const insightLayers = computed<BlueprintLayer[]>(() =>
  orderedLayers.value.filter((layer) => layer.key !== "role")
);

const stepItems = computed(() =>
  insightLayers.value.map((layer) => {
    const meta = getLayerMeta(layer.key);
    return {
      key: layer.key,
      order: meta.order,
      title: layer.title || layer.headline,
      question: meta.question,
    };
  })
);

const selfProfile = computed<BlueprintSelfProfile | null>(() => {
  if (!props.blueprint?.self_profile) return null;
  return props.blueprint.self_profile as BlueprintSelfProfile;
});

const careerBlueprint = computed<CareerBlueprint | null>(() => {
  if (!props.blueprint?.career_blueprint) return null;
  return props.blueprint.career_blueprint as CareerBlueprint;
});

const theoryBasis = computed<TheoryBasis | null>(() => {
  if (!props.blueprint?.theory_basis) return null;
  return props.blueprint.theory_basis as TheoryBasis;
});

function formatFitScore(value: number) {
  return Number.isFinite(value) ? value.toFixed(1) : "--";
}
</script>

<style scoped>
.blueprintSection {
  margin-bottom: 22px;
}

.blueprintPanel {
  padding: 24px;
}

.panelHeader {
  display: flex;
  justify-content: space-between;
  gap: 18px;
  align-items: flex-start;
}

.panelCopy {
  max-width: 760px;
}

.panelEyebrow,
.layerEyebrow {
  font-size: 12px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--gold);
}

.panelTitle {
  margin: 10px 0 0;
  color: var(--text);
  font-size: 26px;
}

.panelNote {
  margin: 12px 0 0;
  color: var(--text-secondary);
  line-height: 1.8;
}

.profileSection,
.insightSection,
.careerSection,
.theoryFold {
  margin-top: 22px;
}

.sectionEyebrow {
  font-size: 12px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--gold);
}

.sectionTitle {
  margin: 10px 0 0;
  color: var(--text);
  font-size: 24px;
  line-height: 1.25;
}

.sectionSummary,
.profileBaseline,
.careerSummary,
.careerDecision,
.careerRisk,
.careerTheory p,
.careerPrompt {
  color: var(--text-secondary);
  line-height: 1.8;
}

.sectionSummary {
  margin: 12px 0 0;
}

.profileBaseline {
  margin: 14px 0 0;
  padding: 18px;
  border-radius: 22px;
  border: 1px solid rgba(212, 175, 55, 0.12);
  background:
    radial-gradient(circle at top left, rgba(212, 175, 55, 0.08), transparent 38%),
    rgba(255, 255, 255, 0.03);
  color: var(--text);
  font-size: 16px;
}

.profileCardGrid,
.careerGrid {
  margin-top: 18px;
  display: grid;
  gap: 14px;
}

.profileCardGrid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.stepRail {
  margin-top: 20px;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.stepCard,
.signalCard,
.profileCard,
.layerCard,
.focusCard,
.careerCard {
  border-radius: 22px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background:
    radial-gradient(circle at top left, rgba(212, 175, 55, 0.07), transparent 36%),
    rgba(2, 6, 23, 0.5);
}

.stepCard {
  padding: 16px;
}

.stepIndex {
  color: var(--gold);
  font-size: 12px;
  letter-spacing: 0.16em;
  font-weight: 700;
}

.stepTitle {
  margin: 10px 0 0;
  color: var(--text);
  font-size: 18px;
  line-height: 1.3;
}

.stepQuestion,
.layerQuestion {
  margin-top: 8px;
  color: rgba(248, 250, 252, 0.72);
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.signalGrid {
  margin-top: 18px;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.signalCard {
  padding: 16px;
}

.profileCard,
.careerCard {
  padding: 18px;
}

.signalLabel,
.focusLabel,
.careerFit,
.careerSubTitle {
  color: var(--gold);
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.signalValue,
.focusValue {
  margin-top: 8px;
  color: var(--text);
  font-size: 18px;
  font-weight: 700;
  line-height: 1.35;
}

.signalHint,
.focusHint {
  margin: 10px 0 0;
  color: var(--text-secondary);
  line-height: 1.7;
  font-size: 13px;
}

.profileList {
  margin-top: 16px;
}

.layerGrid {
  margin-top: 22px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.layerCard {
  padding: 18px;
}

.layerMetaRow {
  display: flex;
  align-items: center;
  gap: 10px;
}

.layerStep {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 34px;
  height: 34px;
  border-radius: 999px;
  background: rgba(212, 175, 55, 0.12);
  color: var(--gold);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.layerHead {
  margin-top: 14px;
}

.layerTitle {
  margin: 10px 0 0;
  color: var(--text);
  font-size: 20px;
  line-height: 1.25;
}

.layerSummary {
  margin: 12px 0 0;
  color: var(--text-secondary);
  line-height: 1.8;
}

.evidenceRow {
  margin-top: 14px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.evidenceChip {
  display: inline-flex;
  align-items: center;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.06);
  color: var(--text-secondary);
  font-size: 12px;
}

.focusGrid {
  margin-top: 16px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.focusCard {
  padding: 14px;
}

.careerGrid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.careerTop {
  display: flex;
  justify-content: space-between;
  gap: 14px;
  align-items: flex-start;
}

.careerTitle,
.theoryTitle {
  margin: 8px 0 0;
  color: var(--text);
}

.careerTitle {
  font-size: 20px;
  line-height: 1.3;
}

.careerScore {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 6px;
  color: var(--text);
  line-height: 1;
}

.careerScoreLabel {
  color: rgba(248, 250, 252, 0.62);
  font-size: 11px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.careerScore strong {
  font-size: 22px;
  font-weight: 700;
}

.careerSummary {
  margin: 12px 0 0;
}

.careerDecision {
  margin: 10px 0 0;
  color: rgba(248, 250, 252, 0.88);
  font-size: 13px;
}

.careerRisk {
  margin: 12px 0 0;
  padding: 12px 14px;
  border-radius: 14px;
  border: 1px solid rgba(248, 113, 113, 0.18);
  background: rgba(127, 29, 29, 0.18);
  color: #fecaca;
  font-size: 13px;
}

.careerTagRow {
  margin-top: 14px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.careerTag,
.theoryBadge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 30px;
  padding: 0 12px;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.04);
  color: var(--text-secondary);
  font-size: 12px;
  white-space: nowrap;
}

.careerList {
  margin-top: 14px;
}

.careerSourceRow,
.careerTheory {
  margin-top: 14px;
}

.careerTheory {
  padding-top: 14px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.careerTheory p {
  margin: 8px 0 0;
}

.compactEvidence {
  margin-top: 14px;
}

.careerPrompt {
  margin: 16px 0 0;
}

.theoryFold {
  display: block;
  border-radius: 22px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.03);
}

.theorySummary {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 16px;
  align-items: center;
  padding: 18px;
  list-style: none;
  cursor: pointer;
}

.theorySummary::-webkit-details-marker {
  display: none;
}

.theoryBody {
  padding: 0 18px 18px;
}

.theoryList {
  margin-top: 16px;
}

.layerList {
  margin: 16px 0 0;
  padding: 0;
  list-style: none;
  display: grid;
  gap: 10px;
}

.layerList li {
  color: var(--text-secondary);
  line-height: 1.75;
  padding-left: 18px;
  position: relative;
}

.layerList li::before {
  content: "";
  position: absolute;
  left: 0;
  top: 10px;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--gold);
  box-shadow: 0 0 16px rgba(212, 175, 55, 0.28);
}

@media (max-width: 1100px) {
  .profileCardGrid,
  .stepRail,
  .signalGrid,
  .layerGrid,
  .focusGrid,
  .careerGrid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .theorySummary {
    grid-template-columns: 1fr;
  }
}
</style>
