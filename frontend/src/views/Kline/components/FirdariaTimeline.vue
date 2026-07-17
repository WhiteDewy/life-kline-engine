<template>
  <section class="phase-section" v-if="insight">
    <!-- ═══ 核心洞察 ═══ -->
    <div class="insight-card">
      <p class="insight-headline">{{ insight.headline }}</p>

      <div class="insight-body">
        <p class="insight-para">{{ insight.body }}</p>
        <p class="insight-para insight-advice">{{ insight.advice }}</p>
      </div>

      <!-- 时间感 -->
      <div class="insight-time" v-if="remainingText">
        <span class="time-icon">⏳</span>
        <span class="time-text">{{ remainingText }}</span>
        <span class="time-note">· {{ insight.trend_note }}</span>
      </div>

      <!-- 运势偏向 -->
      <div class="insight-bias" v-if="insight.top_domains.length">
        <p class="bias-text">{{ insight.bias_note }}</p>

        <div class="bias-rows">
          <div class="bias-row" v-if="insight.top_domains.length">
            <span class="bias-label">当下最顺</span>
            <span class="bias-value bias-value--favor">{{ insight.top_domains.join(" · ") }}</span>
          </div>
          <div class="bias-row" v-if="insight.patience_domains.length">
            <span class="bias-label">需要耐心</span>
            <span class="bias-value bias-value--patience">{{ insight.patience_domains.join(" · ") }}</span>
          </div>
        </div>

        <button class="bias-why" @click="showEvidence = !showEvidence">
          为什么这么说？{{ showEvidence ? '▲' : '▼' }}
        </button>

        <div class="bias-evidence" v-if="showEvidence">
          <p class="evidence-text">
            {{ insight.planet_label }}落在{{ insight.house_title }}，先天状态{{ insight.dignity_label }}。
            {{ insight.dignity_note }}
          </p>
          <p class="evidence-text" v-if="nextPhaseText">
            {{ nextPhaseText }}
          </p>
        </div>
      </div>
    </div>

    <!-- ═══ 一生节奏（折叠） ═══ -->
    <div class="life-rhythm">
      <button class="rhythm-toggle" @click="showFull = !showFull">
        📖 {{ showFull ? '收起' : '查看' }}一生的运势节奏
      </button>

      <div class="rhythm-strip" v-if="!showFull && majorPeriods.length">
        <div
          v-for="group in majorPeriods"
          :key="group.startAge"
          class="rhythm-dot-wrap"
          :class="{ 'rhythm-dot-wrap--current': group.isCurrent }"
        >
          <div
            class="rhythm-dot"
            :style="{ background: group.isCurrent ? group.color : 'rgba(255,255,255,0.12)' }"
          ></div>
          <span class="rhythm-age">{{ group.startAge }}</span>
        </div>
      </div>

      <div class="rhythm-full" v-if="showFull">
        <div
          v-for="group in majorPeriods"
          :key="group.startAge"
          class="rhythm-chapter"
          :class="{ 'rhythm-chapter--current': group.isCurrent }"
          :style="{ '--planet-color': group.color }"
        >
          <div class="rhythm-chapter-head">
            <span class="rhythm-chapter-symbol" :style="{ color: group.color }">{{ group.symbol }}</span>
            <span class="rhythm-chapter-name">{{ group.name }}</span>
            <span class="rhythm-chapter-age">{{ group.startAge }}–{{ group.endAge }}岁</span>
            <span v-if="group.isCurrent" class="rhythm-chapter-now">你在这里</span>
          </div>
          <p class="rhythm-chapter-summary" v-if="group.summary">{{ group.summary }}</p>
        </div>
      </div>
    </div>
  </section>

  <section v-else class="phase-section">
    <div class="insight-card insight-card--empty">
      <p class="empty-text">暂无当前阶段数据</p>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import type { KlinePeriod } from "@/utils/types";

const props = defineProps<{
  periods: KlinePeriod[];
  currentAge?: number;
}>();

const showFull = ref(false);
const showEvidence = ref(false);

const PLANET: Record<string, { name: string; symbol: string; color: string }> = {
  SUN:        { name: "太阳", symbol: "☉", color: "#D4AF37" },
  MOON:       { name: "月亮", symbol: "☽", color: "#C0C0C0" },
  MERCURY:    { name: "水星", symbol: "☿", color: "#38BDF8" },
  VENUS:      { name: "金星", symbol: "♀", color: "#F472B6" },
  MARS:       { name: "火星", symbol: "♂", color: "#EF4444" },
  JUPITER:    { name: "木星", symbol: "♃", color: "#FB923C" },
  SATURN:     { name: "土星", symbol: "♄", color: "#94A3B8" },
  NORTH_NODE: { name: "北交", symbol: "☊", color: "#A78BFA" },
  SOUTH_NODE: { name: "南交", symbol: "☋", color: "#94A3B8" },
};

// ── 当前阶段 ──
const currentPeriod = computed(() => {
  const age = props.currentAge ?? -1;
  return props.periods.find((p) => age >= p.timing.start_age && age < p.timing.end_age) || null;
});

// ── 引擎生成的洞察：零前端硬编码 ──
const insight = computed(() => currentPeriod.value?.insight || null);

// ── 时间感 ──
const remainingData = computed(() => {
  const p = currentPeriod.value;
  if (!p) return null;
  const age = props.currentAge ?? 0;
  return { remaining: p.timing.end_age - age };
});

const remainingText = computed(() => {
  const d = remainingData.value;
  if (!d || d.remaining <= 0) return "";
  if (d.remaining < 0.5) return "这个阶段即将结束——是时候收尾和准备了。";
  if (d.remaining < 1) {
    const months = (d.remaining * 12).toFixed(0);
    return `这个阶段还剩 ${months} 个月。`;
  }
  return `这个阶段还剩 ${d.remaining.toFixed(1)} 年。`;
});

// ── 下一阶段预告 ──
const nextPhaseText = computed(() => {
  const currentMajor = currentPeriod.value?.lords.major;
  const age = props.currentAge ?? 0;
  for (const p of props.periods) {
    if (p.timing.start_age > age && p.lords.major !== currentMajor) {
      const info = PLANET[p.lords.major];
      const nextName = info?.name || p.lords.major;
      return `${Math.round(p.timing.start_age)}岁前后进入${nextName}阶段——到时候的重心和现在会很不一样。如果现在有想做的事，这段时间是最好的窗口。`;
    }
  }
  return "";
});

// ── 大运列表 ──
const majorPeriods = computed(() => {
  const age = props.currentAge ?? -1;
  const seen = new Set<string>();
  const groups: Array<{
    startAge: number;
    endAge: number;
    name: string;
    symbol: string;
    color: string;
    isCurrent: boolean;
    summary: string;
  }> = [];

  let current: typeof groups[0] | null = null;

  for (const p of props.periods) {
    const majorLord = p.lords.major;
    if (!seen.has(majorLord)) {
      seen.add(majorLord);
      if (current) {
        current.endAge = Math.round(p.timing.start_age);
        groups.push(current);
      }
      const info = PLANET[majorLord] || { name: majorLord, symbol: "?", color: "#94A3B8" };
      current = {
        startAge: Math.round(p.timing.start_age),
        endAge: 0,
        name: info.name,
        symbol: info.symbol,
        color: info.color,
        isCurrent: age >= p.timing.start_age && age < p.timing.end_age,
        summary: p.summary || "",
      };
    }
    if (current && age >= p.timing.start_age && age < p.timing.end_age) {
      current.isCurrent = true;
    }
  }
  if (current) {
    current.endAge = Math.round(props.periods[props.periods.length - 1]?.timing.end_age || 75);
    groups.push(current);
  }

  return groups;
});
</script>

<style scoped>
.phase-section {
  margin: 38px 0;
}

/* ── 洞察卡片 ── */
.insight-card {
  position: relative;
  padding: 36px 32px 32px;
  border-radius: 24px;
  background:
    radial-gradient(ellipse at 50% 0%, rgba(212, 175, 55, 0.05), transparent 55%),
    linear-gradient(180deg, rgba(15, 23, 42, 0.9), rgba(15, 23, 42, 0.6));
  border: 1px solid rgba(255, 255, 255, 0.07);
  box-shadow: 0 24px 64px rgba(0, 0, 0, 0.3);
}

.insight-card::before {
  content: "";
  position: absolute;
  top: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 140px;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(212, 175, 55, 0.3), transparent);
}

.insight-card--empty {
  padding: 32px;
  text-align: center;
}

.empty-text {
  color: #64748b;
  font-size: 14px;
  margin: 0;
}

/* ── 标题 ── */
.insight-headline {
  margin: 0 0 18px;
  color: #f8fafc;
  font-size: 20px;
  font-weight: 600;
  line-height: 1.6;
  letter-spacing: -0.01em;
}

/* ── 正文 ── */
.insight-body {
  margin-bottom: 16px;
}

.insight-para {
  margin: 0 0 8px;
  color: #cbd5e1;
  font-size: 15px;
  line-height: 1.85;
}

.insight-advice {
  color: #e2e8f0;
}

/* ── 时间感 ── */
.insight-time {
  display: flex;
  align-items: baseline;
  gap: 6px;
  padding: 12px 16px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.05);
  margin-bottom: 18px;
  flex-wrap: wrap;
}

.time-icon {
  font-size: 14px;
  flex-shrink: 0;
}

.time-text {
  color: #e2e8f0;
  font-size: 14px;
  font-weight: 500;
}

.time-note {
  color: #64748b;
  font-size: 13px;
}

/* ── 运势偏向 ── */
.insight-bias {
  padding-top: 14px;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
}

.bias-text {
  margin: 0 0 10px;
  color: #94a3b8;
  font-size: 14px;
  line-height: 1.7;
}

.bias-rows {
  display: grid;
  gap: 5px;
  margin-bottom: 8px;
}

.bias-row {
  display: flex;
  align-items: baseline;
  gap: 10px;
}

.bias-label {
  font-size: 12px;
  color: #64748b;
  flex-shrink: 0;
  width: 56px;
}

.bias-value {
  font-size: 14px;
  font-weight: 500;
}

.bias-value--favor {
  color: #f8fafc;
}

.bias-value--patience {
  color: #94a3b8;
}

.bias-why {
  margin-top: 6px;
  padding: 0;
  background: none;
  border: none;
  color: #64748b;
  font-size: 12px;
  cursor: pointer;
  transition: color 0.2s;
}

.bias-why:hover {
  color: #94a3b8;
}

.bias-evidence {
  margin-top: 12px;
  padding: 14px 16px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.02);
  border-left: 2px solid rgba(212, 175, 55, 0.2);
}

.evidence-text {
  margin: 0 0 8px;
  color: #94a3b8;
  font-size: 13px;
  line-height: 1.75;
}

.evidence-text:last-child {
  margin-bottom: 0;
}

/* ── 一生节奏 ── */
.life-rhythm {
  margin-top: 16px;
  padding: 16px 20px;
  border-radius: 18px;
  background: rgba(15, 23, 42, 0.4);
  border: 1px solid rgba(255, 255, 255, 0.04);
}

.rhythm-toggle {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: none;
  border: none;
  color: #94a3b8;
  font-size: 13px;
  cursor: pointer;
  padding: 0;
  margin-bottom: 10px;
  transition: color 0.2s;
}

.rhythm-toggle:hover {
  color: #e2e8f0;
}

.rhythm-strip {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 2px;
  height: 48px;
}

.rhythm-dot-wrap {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 5px;
}

.rhythm-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  transition: all 0.3s;
}

.rhythm-dot-wrap--current .rhythm-dot {
  width: 14px;
  height: 14px;
  box-shadow: 0 0 14px rgba(212, 175, 55, 0.5);
}

.rhythm-age {
  font-size: 9px;
  color: #475569;
}

.rhythm-dot-wrap--current .rhythm-age {
  color: #94a3b8;
  font-weight: 700;
}

.rhythm-full {
  display: grid;
  gap: 6px;
  max-height: 400px;
  overflow-y: auto;
}

.rhythm-chapter {
  padding: 14px 16px;
  border-radius: 14px;
  background: rgba(15, 23, 42, 0.5);
  border: 1px solid rgba(255, 255, 255, 0.04);
  transition: all 0.2s;
}

.rhythm-chapter:not(.rhythm-chapter--current) {
  opacity: 0.45;
}

.rhythm-chapter--current {
  border-color: color-mix(in srgb, var(--planet-color, #d4af37) 25%, transparent);
  background: color-mix(in srgb, var(--planet-color, #d4af37) 6%, rgba(15, 23, 42, 0.9));
}

.rhythm-chapter-head {
  display: flex;
  align-items: center;
  gap: 8px;
}

.rhythm-chapter-symbol {
  font-size: 16px;
  line-height: 1;
}

.rhythm-chapter-name {
  font-size: 14px;
  font-weight: 700;
  color: #e2e8f0;
}

.rhythm-chapter-age {
  font-size: 12px;
  color: #64748b;
  margin-left: auto;
}

.rhythm-chapter-now {
  padding: 2px 8px;
  border-radius: 999px;
  background: #d4af37;
  color: #020617;
  font-size: 10px;
  font-weight: 800;
}

.rhythm-chapter-summary {
  margin: 8px 0 0;
  color: #94a3b8;
  font-size: 12px;
  line-height: 1.7;
}

@media (max-width: 600px) {
  .insight-card {
    padding: 24px 18px 22px;
  }

  .insight-headline {
    font-size: 18px;
  }

  .insight-para {
    font-size: 14px;
  }
}
</style>
