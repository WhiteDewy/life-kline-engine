<template>
  <section v-if="blueprint" class="blueprintSection">
    <article class="panel blueprintPanel">
      <div class="panelHeader">
        <div class="panelCopy">
          <div class="panelEyebrow">本命蓝图</div>
          <h2 class="panelTitle">本命蓝图</h2>
          <p class="panelNote">{{ panelNote }}</p>
        </div>
      </div>

      <section v-if="questionSections.length" class="questionSection">
        <div class="sectionEyebrow">用户六问</div>
        <h3 class="sectionTitle">先回答你最关心的六个问题</h3>
        <p class="sectionSummary">
          本命蓝图先直接回答“我是谁、适合做什么、学业、事业、财富、桃花与伴侣”这六个问题，技术推理放到后面折叠查看。
        </p>

        <div class="questionGrid">
          <article
            v-for="(item, index) in questionSections"
            :key="item.key"
            class="questionCard"
          >
            <div class="questionMeta">
              <span class="questionIndex">{{ String(index + 1).padStart(2, "0") }}</span>
              <span class="questionLabel">{{ item.question }}</span>
            </div>

            <p class="questionAnswer">{{ item.answer }}</p>

            <div class="questionBlockGrid">
              <section v-if="item.takeaways?.length" class="questionBlock">
                <div class="questionBlockTitle">关键判断</div>
                <ul class="layerList compactList">
                  <li v-for="point in item.takeaways" :key="point">{{ point }}</li>
                </ul>
              </section>

              <section v-if="item.risks?.length" class="questionBlock">
                <div class="questionBlockTitle">风险点</div>
                <ul class="layerList compactList">
                  <li v-for="point in item.risks" :key="point">{{ point }}</li>
                </ul>
              </section>

              <section v-if="item.actions?.length" class="questionBlock">
                <div class="questionBlockTitle">行动建议</div>
                <ul class="layerList compactList">
                  <li v-for="point in item.actions" :key="point">{{ point }}</li>
                </ul>
              </section>
            </div>

            <details v-if="item.evidence?.length" class="questionEvidenceFold">
              <summary class="questionEvidenceSummary">看判断依据</summary>
              <div class="evidenceRow">
                <span v-for="evidence in item.evidence" :key="evidence" class="evidenceChip">
                  {{ evidence }}
                </span>
              </div>
            </details>
          </article>
        </div>
      </section>

      <details
        v-if="hasSupportingContent"
        class="supportFold"
        :open="!questionSections.length"
      >
        <summary class="theorySummary">
          <div>
            <div class="sectionEyebrow">补充解读</div>
            <h3 class="sectionTitle theoryTitle">底层推理与扩展解读</h3>
          </div>
          <span class="theoryBadge">
            {{ questionSections.length ? "默认折叠 / 点击展开" : "旧版数据 / 默认展开" }}
          </span>
        </summary>

        <div class="theoryBody">
          <section v-if="questionSections.length && keySignals.length" class="signalSection">
            <div class="sectionEyebrow">快速入口</div>
            <h3 class="sectionTitle">这张盘的核心信号</h3>
            <p class="sectionSummary">
              如果你想快速回看占星依据，先看这几个最关键的入口，不需要一上来就读完整长文。
            </p>

            <div class="profileCardGrid">
              <article
                v-for="item in keySignals.slice(0, 4)"
                :key="`${item.label}-${item.value}`"
                class="profileCard"
              >
                <div class="signalLabel">{{ item.label }}</div>
                <div class="signalValue">{{ item.value }}</div>
                <p v-if="item.hint" class="signalHint">{{ item.hint }}</p>
              </article>
            </div>
          </section>

          <section v-else-if="selfProfile" class="profileSection">
            <div class="sectionEyebrow">认识你自己</div>
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
            <div class="sectionEyebrow">长期结构</div>
            <h3 class="sectionTitle">主轴、发力点与代价</h3>
            <p class="sectionSummary">
              这里保留更底层的结构判断，方便你回看这张盘长期反复出现的主轴、资源放大点和代价来源。
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
                  <li v-for="point in visibleLayerPoints(layer)" :key="point">{{ point }}</li>
                </ul>
              </article>
            </div>
          </section>

          <section v-if="careerBlueprint" class="careerSection">
            <div class="sectionEyebrow">职业方向</div>
            <h3 class="sectionTitle">{{ careerBlueprint.title || "职业路线" }}</h3>
            <p v-if="careerBlueprint.summary" class="sectionSummary">{{ careerBlueprint.summary }}</p>

            <div v-if="careerBlueprint.method_tags?.length" class="evidenceRow">
              <span v-for="item in careerBlueprint.method_tags" :key="item" class="evidenceChip">
                {{ item }}
              </span>
            </div>

            <div v-if="supportCareerPaths.length" class="careerGrid">
              <article
                v-for="path in supportCareerPaths"
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
                  <span v-for="item in visibleCareerTags(path)" :key="item" class="careerTag">
                    {{ item }}
                  </span>
                </div>

                <ul v-if="path.points?.length" class="layerList careerList">
                  <li v-for="point in visibleCareerPoints(path)" :key="point">{{ point }}</li>
                </ul>

                <div v-if="path.sources?.length" class="careerSourceRow">
                  <div class="careerSubTitle">路径来源</div>
                  <div class="evidenceRow compactEvidence">
                    <span v-for="item in path.sources" :key="item" class="evidenceChip">
                      {{ item }}
                    </span>
                  </div>
                </div>

                <details v-if="path.theory?.length && questionSections.length" class="careerTheoryFold">
                  <summary class="questionEvidenceSummary">展开完整推理</summary>
                  <div class="careerTheory">
                    <div class="careerSubTitle">判断依据</div>
                    <p v-for="item in path.theory" :key="item">{{ item }}</p>
                  </div>
                </details>

                <div v-else-if="path.theory?.length" class="careerTheory">
                  <div class="careerSubTitle">判断依据</div>
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

            <p v-if="careerBlueprint.selection_prompt && !questionSections.length" class="careerPrompt">
              {{ careerBlueprint.selection_prompt }}
            </p>
          </section>

          <details v-if="theoryBasis" class="theoryFold">
            <summary class="theorySummary innerTheorySummary">
              <div>
                <div class="sectionEyebrow">完整依据</div>
                <h3 class="sectionTitle theoryTitle">{{ theoryBasis.title || "完整判断依据" }}</h3>
              </div>
              <span class="theoryBadge">继续展开</span>
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

interface BlueprintQuestionSection {
  key: string;
  question: string;
  answer: string;
  takeaways?: string[];
  risks?: string[];
  actions?: string[];
  evidence?: string[];
}

const PANEL_NOTE =
  "\u7528\u6237\u770b\u672c\u547d\u84dd\u56fe\uff0c\u5176\u5b9e\u6700\u5173\u5fc3\u7684\u662f\u300c\u6211\u662f\u4ec0\u4e48\u4eba\u300d\u3001\u300c\u6211\u9002\u5408\u505a\u4ec0\u4e48\u300d\u3001\u300c\u5b66\u4e1a\u3001\u4e8b\u4e1a\u3001\u8d22\u5bcc\u3001\u611f\u60c5\u600e\u4e48\u6837\u300d\u3002\u6240\u4ee5\u4e3b\u754c\u9762\u5148\u76f4\u63a5\u56de\u7b54\u8fd9\u4e9b\u95ee\u9898\uff0c\u628a\u6280\u672f\u63a8\u7406\u6536\u5230\u540e\u9762\u3002";

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

const questionSections = computed<BlueprintQuestionSection[]>(() => {
  const source = Array.isArray(props.blueprint?.question_sections)
    ? (props.blueprint?.question_sections as BlueprintQuestionSection[])
    : [];
  return source;
});

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

const keySignals = computed<BlueprintSignal[]>(() => {
  const source = Array.isArray(props.blueprint?.key_signals)
    ? (props.blueprint?.key_signals as BlueprintSignal[])
    : [];
  return source.filter((item) => item?.label && item?.value);
});

const careerBlueprint = computed<CareerBlueprint | null>(() => {
  if (!props.blueprint?.career_blueprint) return null;
  return props.blueprint.career_blueprint as CareerBlueprint;
});

const supportCareerPaths = computed<CareerPath[]>(() => {
  const paths = Array.isArray(careerBlueprint.value?.paths) ? careerBlueprint.value?.paths ?? [] : [];
  if (!questionSections.value.length) return paths;
  return paths.slice(0, 3);
});

const theoryBasis = computed<TheoryBasis | null>(() => {
  if (!props.blueprint?.theory_basis) return null;
  return props.blueprint.theory_basis as TheoryBasis;
});

const hasSupportingContent = computed(
  () =>
    keySignals.value.length > 0 ||
    Boolean(selfProfile.value) ||
    insightLayers.value.length > 0 ||
    Boolean(careerBlueprint.value) ||
    Boolean(theoryBasis.value)
);

function visibleLayerPoints(layer: BlueprintLayer) {
  const points = Array.isArray(layer.points) ? layer.points : [];
  if (!questionSections.value.length) return points;
  return points.slice(0, 3);
}

function visibleCareerPoints(path: CareerPath) {
  const points = Array.isArray(path.points) ? path.points : [];
  if (!questionSections.value.length) return points;
  return points.slice(0, 3);
}

function visibleCareerTags(path: CareerPath) {
  const tags = Array.isArray(path.selection_tags) ? path.selection_tags : [];
  if (!questionSections.value.length) return tags;
  return tags.slice(0, 4);
}

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
.questionSection,
.signalSection,
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
.questionGrid,
.careerGrid {
  margin-top: 18px;
  display: grid;
  gap: 14px;
}

.questionGrid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
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
.questionCard,
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

.questionCard {
  padding: 18px;
}

.stepIndex {
  color: var(--gold);
  font-size: 12px;
  letter-spacing: 0.16em;
  font-weight: 700;
}

.questionMeta {
  display: flex;
  align-items: center;
  gap: 12px;
}

.questionIndex {
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

.questionLabel,
.questionBlockTitle {
  color: var(--text);
  font-size: 16px;
  font-weight: 700;
  line-height: 1.35;
}

.questionAnswer {
  margin: 14px 0 0;
  color: var(--text);
  line-height: 1.85;
  font-size: 16px;
}

.questionBlockGrid {
  margin-top: 18px;
  display: grid;
  gap: 12px;
}

.questionBlock {
  padding: 14px;
  border-radius: 18px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.03);
}

.compactList {
  margin-top: 12px;
}

.compactList li {
  line-height: 1.68;
}

.questionEvidenceFold,
.supportFold {
  margin-top: 16px;
  border-radius: 18px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.03);
}

.questionEvidenceFold {
  padding: 14px;
}

.questionEvidenceSummary {
  cursor: pointer;
  color: var(--text-secondary);
  font-size: 13px;
  list-style: none;
}

.questionEvidenceSummary::-webkit-details-marker {
  display: none;
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

.careerTheoryFold {
  margin-top: 14px;
  padding-top: 14px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.careerTheory {
  padding-top: 14px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.careerTheoryFold .careerTheory {
  margin-top: 10px;
  padding-top: 0;
  border-top: 0;
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

.supportFold {
  display: block;
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

.innerTheorySummary {
  padding-left: 0;
  padding-right: 0;
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
  .questionGrid,
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
