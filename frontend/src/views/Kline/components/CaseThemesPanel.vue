<template>
  <section v-if="advancedPatterns?.case_themes?.length" class="caseSection">
    <article class="panel casePanel">
      <div class="panelHeader">
        <div>
          <div class="panelEyebrow">Case Deep Dive</div>
          <h2 class="panelTitle">黄金荣样例深拆</h2>
          <p class="panelSummary">
            {{ advancedPatterns.summary || "先看规则链路，再看这张盘如何在现实里落成具体命运。" }}
          </p>
        </div>
      </div>

      <div class="themeGrid">
        <article
          v-for="theme in advancedPatterns.case_themes"
          :key="theme.key"
          class="themeCard"
        >
          <div class="themeHead">
            <h3 class="themeTitle">{{ theme.title }}</h3>
          </div>
          <p class="themeSummary">{{ theme.summary }}</p>

          <div v-if="theme.evidence?.length" class="evidenceRow">
            <span v-for="item in theme.evidence" :key="item" class="evidenceChip">
              {{ item }}
            </span>
          </div>

          <ul class="themeList">
            <li v-for="point in theme.points || []" :key="point">{{ point }}</li>
          </ul>
        </article>
      </div>
    </article>
  </section>
</template>

<script setup lang="ts">
defineProps<{
  advancedPatterns: Record<string, any> | null;
}>();
</script>

<style scoped>
.caseSection {
  margin-bottom: 22px;
}

.casePanel {
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

.themeGrid {
  margin-top: 18px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.themeCard {
  padding: 18px;
  border-radius: 22px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background:
    radial-gradient(circle at top left, rgba(212, 175, 55, 0.08), transparent 36%),
    rgba(2, 6, 23, 0.5);
}

.themeTitle {
  margin: 0;
  color: var(--text);
  font-size: 22px;
  line-height: 1.25;
}

.themeSummary {
  margin: 12px 0 0;
  color: #f8fafc;
  line-height: 1.75;
  font-weight: 600;
}

.evidenceRow {
  margin-top: 14px;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

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

.themeList {
  margin: 14px 0 0;
  padding: 0;
  list-style: none;
  display: grid;
  gap: 10px;
}

.themeList li {
  color: var(--text-secondary);
  line-height: 1.75;
  padding-left: 18px;
  position: relative;
}

.themeList li::before {
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
  .themeGrid {
    grid-template-columns: 1fr;
  }
}
</style>
