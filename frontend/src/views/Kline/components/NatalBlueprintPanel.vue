<template>
  <section v-if="blueprint" class="blueprintSection">
    <article class="panel blueprintPanel">
      <div class="panelHeader">
        <div>
          <div class="panelEyebrow">Natal Blueprint</div>
          <h2 class="panelTitle">本命蓝图</h2>
          <p class="panelSummary">
            不是只看性格标签，而是把这张盘拆成结构、权力、角色、代价四层去看。
          </p>
        </div>
        <div class="heroBadge">
          <span class="badgeTitle">{{ blueprint.role_title || "人生角色" }}</span>
          <div class="badgeKeywords" v-if="blueprint.keywords?.length">
            <span v-for="item in blueprint.keywords" :key="item" class="keywordChip">
              {{ item }}
            </span>
          </div>
        </div>
      </div>

      <div class="layerGrid">
        <article
          v-for="layer in blueprint.layers || []"
          :key="layer.key"
          class="layerCard"
        >
          <div class="layerHead">
            <div class="layerEyebrow">{{ layer.title }}</div>
            <h3 class="layerTitle">{{ layer.headline }}</h3>
          </div>
          <p class="layerSummary">{{ layer.summary }}</p>
          <ul class="layerList">
            <li v-for="point in layer.points || []" :key="point">{{ point }}</li>
          </ul>
        </article>
      </div>
    </article>
  </section>
</template>

<script setup lang="ts">
defineProps<{
  blueprint: Record<string, any> | null;
}>();
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

.panelSummary {
  margin: 12px 0 0;
  color: var(--text-secondary);
  line-height: 1.8;
}

.heroBadge {
  min-width: 280px;
  padding: 16px 18px;
  border-radius: 22px;
  border: 1px solid rgba(212, 175, 55, 0.18);
  background:
    radial-gradient(circle at top left, rgba(212, 175, 55, 0.12), transparent 42%),
    rgba(255, 255, 255, 0.03);
}

.badgeTitle {
  color: var(--text);
  font-size: 18px;
  font-weight: 700;
}

.badgeKeywords {
  margin-top: 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.keywordChip {
  display: inline-flex;
  align-items: center;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.06);
  color: var(--text-secondary);
  font-size: 12px;
}

.layerGrid {
  margin-top: 22px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.layerCard {
  padding: 18px;
  border-radius: 22px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background:
    radial-gradient(circle at top left, rgba(212, 175, 55, 0.07), transparent 36%),
    rgba(2, 6, 23, 0.5);
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

.layerList {
  margin: 14px 0 0;
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

@media (max-width: 980px) {
  .panelHeader {
    flex-direction: column;
  }

  .heroBadge {
    min-width: 0;
    width: 100%;
  }

  .layerGrid {
    grid-template-columns: 1fr;
  }
}
</style>
