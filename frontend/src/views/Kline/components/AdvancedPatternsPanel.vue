<template>
  <section v-if="hasContent" class="patternsSection">
    <article class="panel patternsPanel">
      <div class="panelHeader">
        <div>
          <div class="panelEyebrow">Advanced Patterns</div>
          <h2 class="panelTitle">高级规则层</h2>
          <p class="panelSummary">
            {{ advancedPatterns?.summary || "把宫主落宫、接纳、互溶和转宫拆开看，才能知道一张盘是怎么运作的。" }}
          </p>
        </div>
      </div>

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

      <div v-if="advancedPatterns?.core_threads?.length" class="threadGrid">
        <article
          v-for="item in advancedPatterns.core_threads"
          :key="`${item.house}-${item.title}`"
          class="threadCard"
        >
          <div class="threadTitle">{{ item.title }}</div>
          <p class="threadSummary">{{ item.summary }}</p>
          <ul v-if="item.points?.length" class="threadList">
            <li v-for="point in item.points" :key="point">{{ point }}</li>
          </ul>
        </article>
      </div>

      <div v-if="advancedPatterns?.pattern_readings?.length" class="readingGrid">
        <article
          v-for="item in advancedPatterns.pattern_readings"
          :key="item.key"
          class="readingCard"
        >
          <div class="readingHead">
            <h3 class="readingTitle">{{ item.title }}</h3>
          </div>
          <p class="readingSummary">{{ item.summary }}</p>

          <div v-if="item.evidence?.length" class="evidenceRow">
            <span v-for="evidence in item.evidence" :key="evidence" class="evidenceChip">
              {{ evidence }}
            </span>
          </div>

          <ul class="readingList">
            <li v-for="point in item.points || []" :key="point">{{ point }}</li>
          </ul>
        </article>
      </div>

      <div v-if="advancedPatterns?.derived_houses?.length" class="derivedBlock">
        <div class="blockTitle">转宫关系</div>
        <div class="derivedGrid">
          <article
            v-for="item in advancedPatterns.derived_houses"
            :key="`${item.base_house}-${item.base_label}`"
            class="derivedCard"
          >
            <div class="threadTitle">{{ item.base_label }}</div>
            <p class="threadSummary">{{ item.summary }}</p>
            <div class="derivedList">
              <div
                v-for="link in item.links"
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
      </div>
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
    patterns?.ruler_groups?.length ||
      patterns?.reception_groups?.length ||
      patterns?.mutual_receptions?.length ||
      patterns?.core_threads?.length ||
      patterns?.pattern_readings?.length ||
      patterns?.derived_houses?.length
  );
});
</script>

<style scoped>
.patternsSection {
  margin-bottom: 22px;
}

.patternsPanel {
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

.ruleBlock,
.derivedBlock {
  margin-top: 20px;
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
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.04);
  color: var(--text-secondary);
  font-size: 12px;
}

.threadGrid {
  margin-top: 18px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.threadCard,
.readingCard,
.derivedCard {
  border-radius: 22px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background:
    radial-gradient(circle at top left, rgba(212, 175, 55, 0.08), transparent 36%),
    rgba(2, 6, 23, 0.5);
}

.threadCard,
.readingCard,
.derivedCard {
  padding: 16px;
}

.threadSummary,
.readingSummary {
  margin: 10px 0 0;
  color: var(--text-secondary);
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
  box-shadow: 0 0 16px rgba(212, 175, 55, 0.28);
}

.readingGrid,
.derivedGrid {
  margin-top: 18px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.readingTitle {
  margin: 0;
  color: var(--text);
  font-size: 22px;
  line-height: 1.25;
}

.evidenceRow {
  margin-top: 14px;
}

.readingSummary {
  color: #f8fafc;
  font-weight: 600;
}

.derivedList {
  margin-top: 12px;
  display: grid;
  gap: 12px;
}

.derivedItem {
  padding: 12px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.derivedItem strong {
  color: var(--text);
  font-size: 13px;
}

.derivedItem p {
  margin: 8px 0 0;
  color: var(--text-secondary);
  line-height: 1.7;
}

.derivedHint {
  opacity: 0.9;
}

@media (max-width: 1100px) {
  .threadGrid,
  .readingGrid,
  .derivedGrid {
    grid-template-columns: 1fr;
  }
}
</style>
