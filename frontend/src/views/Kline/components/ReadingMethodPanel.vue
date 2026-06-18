<template>
  <section class="methodSection">
    <article class="methodPanel">
      <div class="introGrid">
        <div>
          <div class="panelEyebrow">Reading Method</div>
          <h2 class="panelTitle">{{ guide.title }}</h2>
          <p class="panelSummary">{{ guide.summary }}</p>
        </div>

        <div class="beliefCard">
          <div class="beliefEyebrow">Core Belief</div>
          <p>{{ coreBelief }}</p>
        </div>
      </div>

      <div class="pathGrid">
        <article v-for="item in guide.steps" :key="item.step" class="pathCard">
          <div class="pathStep">{{ item.step }}</div>
          <h3>{{ item.title }}</h3>
          <p>{{ item.summary }}</p>
        </article>
      </div>

      <details class="methodFold">
        <summary class="foldSummary">
          <div>
            <div class="foldEyebrow">Methodology</div>
            <div class="foldTitle">阅读原则与三组星体框架</div>
          </div>
          <span class="foldBadge">默认折叠 / 点击展开</span>
        </summary>

        <div class="foldBody">
          <div class="principleGrid">
            <article v-for="item in readingPrinciples" :key="item.key" class="principleCard">
              <div class="principleTitle">{{ item.title }}</div>
              <p>{{ item.summary }}</p>
            </article>
          </div>

          <div class="groupGrid">
            <article v-for="group in groupCards" :key="group.key" class="groupCard">
              <div class="groupEyebrow">{{ group.title }}</div>
              <h3>{{ group.summary }}</h3>
              <p class="groupFocus">{{ group.focus }}</p>
              <div class="planetRow">
                <span v-for="planet in group.planets" :key="planet.name" class="planetChip">
                  {{ planet.name }}
                </span>
              </div>
            </article>
          </div>

          <div class="caseBlock">
            <div class="foldEyebrow">Career & Wealth Rules</div>
            <div class="caseIntro">
              先把职业和财富的基础判断框架立住，再回头看真实案例，就不会被个别标签带偏。
            </div>

            <div class="caseGrid">
              <article v-for="item in wealthCareerRules" :key="item.key" class="caseCard">
                <h3>{{ item.title }}</h3>
                <p class="caseFocus">{{ item.summary }}</p>
                <ul class="caseList">
                  <li v-for="point in item.notes" :key="point">{{ point }}</li>
                </ul>
              </article>
            </div>
          </div>

          <div class="caseBlock">
            <div class="foldEyebrow">Case Reference</div>
            <div class="caseIntro">
              用真实案例校正“事业格局”和“财富格局”的判断，不只看某一颗星，而是一起看四财宫、事业轴线、社交合作与相位支持。
            </div>

            <div class="caseGrid">
              <article v-for="item in caseCards" :key="item.key" class="caseCard">
                <div class="caseMeta">{{ item.subject }}</div>
                <h3>{{ item.title }}</h3>
                <p class="caseFocus">{{ item.focus }}</p>
                <p class="caseSummary">{{ item.summary }}</p>

                <div class="planetRow caseTagRow">
                  <span v-for="tag in item.tags" :key="tag" class="planetChip">
                    {{ tag }}
                  </span>
                </div>

                <ul class="caseList">
                  <li v-for="point in item.userPoints" :key="point">{{ point }}</li>
                </ul>

                <details class="caseDetail">
                  <summary>专业备注</summary>
                  <ul class="caseList">
                    <li v-for="point in item.astrologerNotes" :key="point">{{ point }}</li>
                  </ul>
                </details>
              </article>
            </div>
          </div>
        </div>
      </details>
    </article>
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";
import {
  CAREER_WEALTH_CASES,
  CAREER_WEALTH_RULES,
  CORE_BELIEF,
  PLANET_GROUPS,
  READING_PRINCIPLES,
} from "@/config/methodology";

type AnalysisKey = "natal_blueprint" | "phase_navigation";

interface ReadingStep {
  step: string;
  title: string;
  summary: string;
}

const props = defineProps<{
  analysisKey?: string;
}>();

const coreBelief = CORE_BELIEF;
const readingPrinciples = READING_PRINCIPLES;
const caseCards = CAREER_WEALTH_CASES;
const wealthCareerRules = CAREER_WEALTH_RULES;

const GUIDE_BY_ANALYSIS: Record<
  AnalysisKey,
  {
    title: string;
    summary: string;
    steps: ReadingStep[];
  }
> = {
  natal_blueprint: {
    title: "这份本命蓝图先看什么",
    summary:
      "先用本命蓝图定角色，再看结构和杠杆，最后回到星盘、相位和接纳表核对证据，不要一开始就陷进细节。",
    steps: [
      {
        step: "01",
        title: "先定角色",
        summary: "先回答你在社会里更像什么样的人，再决定后面的解读重点。",
      },
      {
        step: "02",
        title: "再看结构与杠杆",
        summary: "把长期主轴、资源入口和放大结果的方式连起来看，才知道盘的核心运作。",
      },
      {
        step: "03",
        title: "最后看代价与证据",
        summary: "再回头看星盘、相位表、互溶和接纳表，校对优势会从哪里反噬。",
      },
    ],
  },
  phase_navigation: {
    title: "这份阶段报告先看什么",
    summary:
      "先认清本命底盘，再看你现在正走到哪一段，最后把阶段窗口翻译成现实里的推进和取舍。",
    steps: [
      {
        step: "01",
        title: "先看本命底盘",
        summary: "先知道自己的长期结构，避免被短期波动带偏判断。",
      },
      {
        step: "02",
        title: "再看当前阶段",
        summary: "把主运、副运和阶段主题放在一起，看现在适合扩张、沉淀还是重组。",
      },
      {
        step: "03",
        title: "最后看窗口与行动",
        summary: "把时间窗口、机会和注意点转成现实动作，而不是只看热闹。",
      },
    ],
  },
};

const GROUP_FOCUS_MAP: Record<string, string> = {
  will: "看你如何发展自我意志，如何经历理性突破、迷雾和重塑。",
  behavior: "看你如何寻找安全感、表达价值、建立连接并主动行动。",
  belief: "看你靠什么扩张自己，又会在哪些地方被现实长期磨炼。",
};

const guide = computed(() => {
  const key = props.analysisKey === "natal_blueprint" ? "natal_blueprint" : "phase_navigation";
  return GUIDE_BY_ANALYSIS[key];
});

const groupCards = computed(() =>
  PLANET_GROUPS.map((group) => ({
    ...group,
    focus: GROUP_FOCUS_MAP[group.key] || "",
  }))
);
</script>

<style scoped>
.methodSection {
  margin-bottom: 22px;
}

.methodPanel {
  padding: 24px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(15, 23, 42, 0.72);
  backdrop-filter: blur(18px);
  border-radius: 24px;
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.24);
}

.introGrid,
.foldSummary,
.pathGrid,
.principleGrid,
.groupGrid,
.planetRow,
.caseGrid {
  display: grid;
  gap: 16px;
}

.introGrid {
  grid-template-columns: minmax(0, 1.35fr) minmax(280px, 0.65fr);
  align-items: stretch;
}

.panelEyebrow,
.beliefEyebrow,
.foldEyebrow,
.groupEyebrow,
.pathStep {
  font-size: 12px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--gold);
}

.panelTitle,
.foldTitle,
.pathCard h3,
.groupCard h3 {
  margin: 10px 0 0;
  color: var(--text);
  line-height: 1.2;
}

.panelTitle {
  font-size: 26px;
}

.panelSummary,
.beliefCard p,
.pathCard p,
.principleCard p,
.groupFocus,
.caseIntro,
.caseSummary,
.caseFocus {
  margin: 12px 0 0;
  color: var(--text-secondary);
  line-height: 1.8;
}

.beliefCard,
.pathCard,
.principleCard,
.groupCard,
.caseCard {
  border-radius: 22px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background:
    radial-gradient(circle at top left, rgba(212, 175, 55, 0.08), transparent 36%),
    rgba(2, 6, 23, 0.48);
}

.beliefCard {
  padding: 20px;
}

.beliefCard p {
  color: var(--text);
  font-size: 22px;
  font-weight: 600;
  line-height: 1.45;
}

.pathGrid {
  margin-top: 18px;
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.pathCard,
.principleCard,
.groupCard,
.caseCard {
  padding: 18px;
}

.pathCard h3,
.groupCard h3 {
  font-size: 20px;
}

.methodFold {
  margin-top: 18px;
  display: block;
  border-radius: 22px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.03);
}

.foldSummary {
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  padding: 18px;
  list-style: none;
  cursor: pointer;
}

.foldSummary::-webkit-details-marker {
  display: none;
}

.foldTitle {
  font-size: 20px;
}

.foldBadge,
.planetChip {
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

.methodFold[open] .foldBadge {
  color: var(--text);
  border-color: rgba(212, 175, 55, 0.24);
  background: rgba(212, 175, 55, 0.08);
}

.foldBody {
  padding: 0 18px 18px;
}

.principleGrid {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.principleTitle {
  color: var(--text);
  font-size: 18px;
  font-weight: 700;
  line-height: 1.3;
}

.groupGrid {
  margin-top: 16px;
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.caseBlock {
  margin-top: 16px;
}

.caseGrid {
  margin-top: 16px;
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.caseMeta {
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: rgba(248, 250, 252, 0.58);
}

.caseCard h3 {
  margin: 10px 0 0;
  color: var(--text);
  font-size: 20px;
  line-height: 1.25;
}

.caseFocus {
  color: #f8fafc;
  font-weight: 600;
}

.caseTagRow {
  margin-top: 14px;
}

.caseList {
  margin: 14px 0 0;
  padding: 0;
  list-style: none;
  display: grid;
  gap: 10px;
}

.caseList li {
  color: var(--text-secondary);
  line-height: 1.75;
  padding-left: 18px;
  position: relative;
}

.caseList li::before {
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

.caseDetail {
  margin-top: 14px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  padding-top: 14px;
}

.caseDetail summary {
  cursor: pointer;
  color: var(--gold);
  font-size: 12px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  list-style: none;
}

.caseDetail summary::-webkit-details-marker {
  display: none;
}

.groupFocus {
  min-height: 58px;
}

.planetRow {
  margin-top: 14px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

@media (max-width: 1200px) {
  .introGrid,
  .pathGrid,
  .principleGrid,
  .groupGrid,
  .caseGrid {
    grid-template-columns: 1fr;
  }

  .groupFocus {
    min-height: 0;
  }
}

@media (max-width: 720px) {
  .foldSummary {
    grid-template-columns: 1fr;
  }

  .planetRow {
    grid-template-columns: 1fr 1fr;
  }
}
</style>
