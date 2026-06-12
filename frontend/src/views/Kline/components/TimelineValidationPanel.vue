<template>
  <section v-if="timeline?.events?.length" class="timelineSection">
    <article class="panel timelinePanel">
      <div class="panelHeader">
        <div>
          <div class="panelEyebrow">Historical Validation</div>
          <h2 class="panelTitle">{{ timeline.title || "人生节点校验" }}</h2>
          <p class="panelSummary">
            {{ timeline.summary || "用已知人生事件反推阶段与本命结构是否成立。" }}
          </p>
        </div>
      </div>

      <div class="eventList">
        <article
          v-for="event in timeline.events || []"
          :key="`${event.date_label}-${event.title}`"
          class="eventCard"
        >
          <div class="eventTop">
            <div>
              <div class="eventDate">{{ event.date_label }}</div>
              <h3 class="eventTitle">{{ event.title }}</h3>
            </div>
            <span class="eventCategory">{{ event.category }}</span>
          </div>

          <div class="eventMeta">
            <span>{{ event.age_label }}</span>
            <span>{{ event.phase_range }}</span>
            <span>{{ event.phase_lords }}</span>
          </div>

          <div class="eventBlock">
            <strong>对应阶段</strong>
            <p>{{ event.phase_title }}</p>
            <p class="muted">{{ event.phase_summary }}</p>
          </div>

          <div class="eventBlock">
            <strong>为什么对得上</strong>
            <p>{{ event.reading }}</p>
            <p class="muted">{{ event.validation }}</p>
          </div>
        </article>
      </div>
    </article>
  </section>
</template>

<script setup lang="ts">
defineProps<{
  timeline: Record<string, any> | null;
}>();
</script>

<style scoped>
.timelineSection {
  margin-bottom: 22px;
}

.timelinePanel {
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
}

.panelSummary {
  margin: 12px 0 0;
  color: var(--text-secondary);
  line-height: 1.8;
}

.eventList {
  margin-top: 22px;
  display: grid;
  gap: 16px;
}

.eventCard {
  padding: 18px;
  border-radius: 22px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background:
    radial-gradient(circle at top left, rgba(212, 175, 55, 0.08), transparent 36%),
    rgba(2, 6, 23, 0.48);
}

.eventTop {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
}

.eventDate {
  color: var(--gold);
  font-size: 12px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.eventTitle {
  margin: 8px 0 0;
  color: var(--text);
  font-size: 22px;
  line-height: 1.25;
}

.eventCategory {
  display: inline-flex;
  align-items: center;
  padding: 7px 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.06);
  color: var(--text-secondary);
  font-size: 12px;
  white-space: nowrap;
}

.eventMeta {
  margin-top: 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.eventMeta span {
  display: inline-flex;
  align-items: center;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  color: var(--text-secondary);
  font-size: 12px;
}

.eventBlock {
  margin-top: 14px;
}

.eventBlock strong {
  color: var(--text);
  font-size: 14px;
}

.eventBlock p {
  margin: 8px 0 0;
  color: var(--text-secondary);
  line-height: 1.8;
}

.muted {
  opacity: 0.92;
}

@media (max-width: 760px) {
  .eventTop {
    flex-direction: column;
  }
}
</style>
