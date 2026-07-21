<template>
  <transition name="direction-slide">
    <div v-if="visible" class="direction-wrapper">
      <!-- 半透明遮罩 -->
      <div class="direction-backdrop" @click="$emit('close')"></div>

      <!-- 面板 -->
      <div class="direction-panel">
        <!-- 关闭按钮 -->
        <button class="direction-close" @click="$emit('close')">✕</button>

        <!-- ═══ 内容 ═══ -->
        <div class="direction-content">
          <!-- 1. Header -->
          <div class="direction-header">
            <span class="direction-header-icon">📡</span>
            <h2 class="direction-title">今日走向</h2>
            <p class="direction-date">{{ dateLabel }}</p>
          </div>

          <!-- 2. 今日引路星灵 (compact card) -->
          <section v-if="todayStarSpirit" class="section section--spirit">
            <div class="spirit-compact">
              <span class="spirit-compact-icon" :style="{ background: spiritBgColor }">
                <span class="spirit-compact-symbol">{{ todayStarSpirit.symbol || '★' }}</span>
              </span>
              <div class="spirit-compact-info">
                <span class="spirit-compact-name">{{ todayStarSpirit.planet_label }}</span>
                <span class="spirit-compact-sign">{{ todayStarSpirit.sign_label }}</span>
              </div>
              <span class="spirit-compact-reason">{{ todayStarSpirit.reason }}</span>
            </div>
          </section>

          <!-- ═══════ Section 1: 今日月晕 ═══════ -->
          <section v-if="transitReport" class="section section--moon">
            <div class="section-header">
              <span class="section-header-icon">🌙</span>
              <span class="section-header-title">今日月晕</span>
            </div>
            <div class="section-body">
              <!-- 月亮星座 + 月相 + 宫位 -->
              <div class="moon-location">
                <div class="moon-location-line">
                  月亮在{{ transitReport.moon_sign_label }}
                  <template v-if="moonPhaseLabel">
                    <span class="moon-location-dot">·</span>
                    {{ moonPhaseLabel }}
                    <span class="moon-phase-emoji">{{ moonPhaseEmoji }}</span>
                  </template>
                </div>
                <div class="moon-house-line">
                  行经你的{{ transitReport.moon_house_label }}
                </div>
              </div>

              <!-- 月亮相位 -->
              <template v-if="transitReport.moon_aspects?.length">
                <div v-for="(a, i) in transitReport.moon_aspects" :key="'m-a-' + i" class="moon-aspect">
                  <div class="moon-aspect-text">
                    <span class="aspect-planet">{{ a.transiting_label }}</span>
                    <span class="aspect-type" :class="aspectClass(a.aspect_label)">{{ a.aspect_label }}</span>
                    <span class="aspect-natal">本命{{ a.natal_label }}</span>
                    <span class="aspect-orb">（orb {{ a.orb }}°，{{ a.is_applying ? '入相位' : '出相位' }}）</span>
                  </div>
                  <div v-if="a.highlight" class="moon-aspect-hint">→ {{ a.highlight }}</div>
                  <button
                    class="transit-chat-btn"
                    @click.stop="emitChat(a.transiting_planet, a.transiting_label, a)"
                  >
                    💬 和{{ a.transiting_label }}灵聊聊这个
                  </button>
                </div>
              </template>
            </div>
          </section>

          <!-- ═══════ Section 2: 近期触发 ═══════ -->
          <section v-if="transitReport" class="section section--fast">
            <div
              class="section-header section-header--clickable"
              @click="toggleSection('fast')"
            >
              <span class="section-header-icon">⚡</span>
              <span class="section-header-title">近期触发</span>
              <span class="section-header-toggle">{{ expandedSections.fast ? '▾' : '▸' }}</span>
            </div>
            <div v-show="expandedSections.fast" class="section-body">
              <template v-if="transitReport.fast_transits?.length">
                <div v-for="(t, i) in transitReport.fast_transits" :key="'fast-' + i" class="transit-card">
                  <div class="transit-row">
                    <span class="transit-planet">{{ t.transiting_label }}</span>
                    <span class="transit-aspect" :class="aspectClass(t.aspect_label)">{{ t.aspect_label }}</span>
                    <span class="transit-natal">{{ t.natal_label }}</span>
                    <span class="transit-orb">{{ t.orb }}°</span>
                  </div>
                  <button
                    class="transit-chat-btn"
                    @click.stop="emitChat(t.transiting_planet, t.transiting_label, t)"
                  >
                    💬 和{{ t.transiting_label }}灵聊聊
                  </button>
                </div>
              </template>
              <div v-else class="section-empty">暂无近期触发</div>
            </div>
          </section>

          <!-- ═══════ Section 3: 逆行提醒 ═══════ -->
          <section
            v-if="transitReport?.active_retrogrades?.length"
            class="section section--retrograde"
          >
            <div class="section-header">
              <span class="section-header-icon">⚠️</span>
              <span class="section-header-title">逆行提醒</span>
            </div>
            <div class="section-body">
              <div
                v-for="(r, i) in transitReport.active_retrogrades"
                :key="'retro-' + i"
                class="retrograde-card"
              >
                <div class="retrograde-card-header">
                  <span class="retrograde-badge">⚠️ 逆行</span>
                  <span class="retrograde-planet-name">{{ r.planet_label }}正在逆行</span>
                </div>
                <div class="retrograde-house">
                  本次{{ r.planet_label }}逆发生在你的{{ r.in_house_label }}
                </div>
                <div class="retrograde-desc">{{ retrogradeDescription(r.planet) }}</div>
                <button
                  class="transit-chat-btn"
                  @click.stop="emitRetroChat(r.planet, r.planet_label)"
                >
                  💬 和{{ r.planet_label }}灵聊聊这次逆行
                </button>
              </div>
            </div>
          </section>

          <!-- ═══════ Section 4: 长期星象背景 ═══════ -->
          <section
            v-if="transitReport?.slow_background?.length"
            class="section section--slow"
          >
            <div
              class="section-header section-header--clickable"
              @click="toggleSection('slow')"
            >
              <span class="section-header-icon">🌌</span>
              <span class="section-header-title">长期星象背景</span>
              <span class="section-header-toggle">{{ expandedSections.slow ? '▾' : '▸' }}</span>
            </div>
            <!-- 折叠态：一行提示 -->
            <div v-show="!expandedSections.slow" class="slow-collapsed-hint">
              {{ slowSummary }}
            </div>
            <!-- 展开态 -->
            <div v-show="expandedSections.slow" class="section-body">
              <div v-for="(s, i) in transitReport.slow_background" :key="'slow-' + i" class="transit-card">
                <div class="transit-row">
                  <span class="transit-planet">{{ s.transiting_label }}</span>
                  <span class="transit-aspect" :class="aspectClass(s.aspect_label)">{{ s.aspect_label }}</span>
                  <span class="transit-natal">{{ s.natal_label }}</span>
                  <span class="transit-orb">{{ s.orb }}°</span>
                </div>
                <button
                  class="transit-chat-btn"
                  @click.stop="emitChat(s.transiting_planet, s.transiting_label, s)"
                >
                  💬 和{{ s.transiting_label }}灵聊聊
                </button>
              </div>
            </div>
          </section>

          <!-- ═══ 语音播报 ═══ -->
          <section class="section section--voice">
            <VoicePlayer :text="summaryText" :style="'broadcast'" showLabel block />
          </section>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { computed, reactive } from "vue";
import VoicePlayer from "./VoicePlayer.vue";

const props = defineProps<{
  visible: boolean;
  transitReport: any;
  todayStarSpirit: any;
  dateLabel: string;
}>();

const emit = defineEmits<{
  close: [];
  'chat-with-spirit': [payload: { planet: string; detail: string }];
}>();

// ── 折叠/展开状态 ──
const expandedSections = reactive<Record<string, boolean>>({
  fast: true,
  slow: false,
});

function toggleSection(key: string) {
  expandedSections[key] = !expandedSections[key];
}

// ── 月相映射 ──
const MOON_PHASE_EMOJI: Record<string, string> = {
  '新月': '🌑',
  '蛾眉月': '🌒',
  '上弦月': '🌓',
  '盈凸月': '🌔',
  '满月': '🌕',
  '亏凸月': '🌖',
  '下弦月': '🌗',
  '残月': '🌘',
};

const moonPhaseLabel = computed(() => {
  return props.transitReport?.moon_phase?.phase || '';
});

const moonPhaseEmoji = computed(() => {
  const phase = props.transitReport?.moon_phase?.phase;
  return MOON_PHASE_EMOJI[phase] || '🌙';
});

// ── 星灵颜色 ──
const spiritBgColor = computed(() => {
  const color = props.todayStarSpirit?.color || '#F2A900';
  return `${color}22`;
});

// ── 逆行描述 ──
const RETROGRADE_DESCRIPTIONS: Record<string, string> = {
  MERCURY: '沟通、合同、出行需反复确认。适合回顾、修正、重新表达。',
  VENUS: '感情、审美、价值观需要重新审视。适合反思旧日关系。',
  MARS: '行动力受阻，容易旧事重提。适合调整节奏，避免冲动。',
  JUPITER: '信念和扩张的节奏放缓。适合回顾和深化已有认知。',
  SATURN: '结构和责任议题再次浮现。适合重新审视长期目标。',
  URANUS: '变革和突破的能量内转。适合反思真正需要改变什么。',
  NEPTUNE: '迷幻和理想主义的迷雾加重。适合保持清醒的现实感。',
  PLUTO: '深层转化的力量向内聚焦。适合深入挖掘内在真相。',
};

function retrogradeDescription(planet: string): string {
  return RETROGRADE_DESCRIPTIONS[planet] || '这段时间适合放慢节奏，回顾与反思。';
}

// ── 长期星象背景折叠态摘要 ──
const slowSummary = computed(() => {
  const items = props.transitReport?.slow_background || [];
  if (items.length === 0) return '';
  const first = items[0];
  const summary = `${first.transiting_label}${first.aspect_label}本命${first.natal_label}`;
  if (items.length === 1) return summary;
  return `${summary} + ${items.length - 1}项长期影响`;
});

// ── 聊聊按钮 ──
function emitChat(planet: string, label: string, transit: any) {
  const detail = transit
    ? `${label}${transit.aspect_label || ''}你的本命${transit.natal_label || ''}（orb ${transit.orb || ''}°）`
    : `${label}行运`;
  emit('chat-with-spirit', { planet, detail });
}

function emitRetroChat(planet: string, label: string) {
  const houseLabel = props.transitReport?.active_retrogrades?.find((r: any) => r.planet === planet)?.in_house_label || '';
  const detail = `${label}逆行（${houseLabel}）`;
  emit('chat-with-spirit', { planet, detail });
}

// ── 语音播报摘要 ──
const summaryText = computed(() => {
  const parts: string[] = [];

  // 引路星灵
  if (props.todayStarSpirit) {
    parts.push(`今日引路星灵是${props.todayStarSpirit.planet_label || ""}，位于${props.todayStarSpirit.sign_label || ""}。`);
    if (props.todayStarSpirit.reason) {
      parts.push(props.todayStarSpirit.reason);
    }
  }

  // 月晕
  if (props.transitReport) {
    const moon = props.transitReport;
    parts.push(`月亮在${moon.moon_sign_label}，行经第${moon.moon_house}宫${moon.moon_house_label}，月相为${moon.moon_phase?.phase || ''}。`);

    if (moon.moon_aspects?.length) {
      const desc = moon.moon_aspects.map((a: any) => `${a.transiting_label}${a.aspect_label}本命${a.natal_label}`).join('，');
      parts.push(`月亮相位：${desc}。`);
    }

    if (moon.fast_transits?.length) {
      const desc = moon.fast_transits.slice(0, 3).map((t: any) => `${t.transiting_label}${t.aspect_label}本命${t.natal_label}`).join('，');
      parts.push(`近期星象：${desc}。`);
    }

    if (moon.active_retrogrades?.length) {
      const desc = moon.active_retrogrades.map((r: any) => `${r.planet_label}逆行`).join('、');
      parts.push(`注意：${desc}。`);
    }
  }

  return parts.join('');
});

// ── 相位样式 ──
function aspectClass(label: string): string {
  if (label === "合" || label === "0°") return "aspect--conjunction";
  if (label === "冲" || label === "180°") return "aspect--opposition";
  if (label === "刑" || label === "90°") return "aspect--square";
  if (label === "三合" || label === "120°") return "aspect--trine";
  if (label === "六合" || label === "60°") return "aspect--sextile";
  return "";
}
</script>

<style scoped>
/* ═══════════════ Transition ═══════════════ */
.direction-slide-enter-active {
  transition: all 0.35s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}
.direction-slide-leave-active {
  transition: all 0.25s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}
.direction-slide-enter-from .direction-panel {
  transform: translateX(100%) !important;
}
.direction-slide-leave-to .direction-panel {
  transform: translateX(100%) !important;
}
.direction-slide-enter-from .direction-backdrop,
.direction-slide-leave-to .direction-backdrop {
  opacity: 0;
}

/* ═══════════════ Wrapper ═══════════════ */
.direction-wrapper {
  position: fixed;
  inset: 0;
  z-index: 210;
  display: flex;
  justify-content: flex-end;
}

/* ═══════════════ Backdrop ═══════════════ */
.direction-backdrop {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.35);
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
  transition: opacity 0.35s ease;
}

/* ═══════════════ Panel ═══════════════ */
.direction-panel {
  position: relative;
  width: 380px;
  max-width: 100%;
  height: 100%;
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border-left: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: -8px 0 32px rgba(0, 0, 0, 0.08);
  display: flex;
  flex-direction: column;
  transition: transform 0.35s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  overflow-y: auto;
}

.direction-panel::-webkit-scrollbar {
  width: 3px;
}
.direction-panel::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 2px;
}

/* ═══════════════ Close ═══════════════ */
.direction-close {
  position: absolute;
  top: 16px;
  right: 16px;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: 1px solid rgba(255, 255, 255, 0.2);
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.7);
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  font-family: inherit;
  z-index: 1;
}
.direction-close:hover {
  background: rgba(255, 255, 255, 0.25);
  color: #fff;
  transform: scale(1.08);
}

/* ═══════════════ Content ═══════════════ */
.direction-content {
  padding: 24px;
  padding-top: calc(24px + env(safe-area-inset-top, 0px));
  padding-bottom: calc(24px + env(safe-area-inset-bottom, 0px));
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* ═══════════════ Header ═══════════════ */
.direction-header {
  text-align: center;
  margin-bottom: 4px;
}
.direction-header-icon {
  font-size: 32px;
  display: block;
  margin-bottom: 8px;
}
.direction-title {
  font-size: 22px;
  font-weight: 700;
  color: #fff;
  margin: 0 0 4px;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  letter-spacing: 0.05em;
}
.direction-date {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.6);
  margin: 0;
  letter-spacing: 0.03em;
}

/* ═══════════════ Section Base ═══════════════ */
.section {
  background: rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  padding: 14px 16px;
  border: 1px solid rgba(255, 255, 255, 0.08);
}
.section-body {
  padding-top: 8px;
}
.section-empty {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.35);
  text-align: center;
  padding: 12px 0;
}

/* ═══════════════ Section Header ═══════════════ */
.section-header {
  display: flex;
  align-items: center;
  gap: 6px;
  user-select: none;
}
.section-header--clickable {
  cursor: pointer;
  transition: opacity 0.2s;
}
.section-header--clickable:hover {
  opacity: 0.8;
}
.section-header-icon {
  font-size: 15px;
  line-height: 1;
}
.section-header-title {
  font-size: 13px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.7);
  letter-spacing: 0.04em;
  flex: 1;
}
.section-header-toggle {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.35);
  transition: transform 0.2s;
}

/* ═══════════════ Spirit Compact ═══════════════ */
.section--spirit {
  padding: 10px 14px;
}
.spirit-compact {
  display: flex;
  align-items: center;
  gap: 10px;
}
.spirit-compact-icon {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1.5px solid rgba(255, 255, 255, 0.15);
  flex-shrink: 0;
}
.spirit-compact-symbol {
  font-size: 18px;
  line-height: 1;
  color: #fff;
  filter: drop-shadow(0 1px 3px rgba(0, 0, 0, 0.2));
}
.spirit-compact-info {
  display: flex;
  flex-direction: column;
  gap: 1px;
  min-width: 0;
}
.spirit-compact-name {
  font-size: 14px;
  font-weight: 700;
  color: #fff;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.12);
}
.spirit-compact-sign {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.55);
}
.spirit-compact-reason {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.4);
  line-height: 1.4;
  margin-left: auto;
  text-align: right;
  max-width: 140px;
}

/* ═══════════════ Moon Section ═══════════════ */
.section--moon {
  border-color: rgba(100, 180, 255, 0.15);
  background: rgba(100, 180, 255, 0.06);
}
.moon-location {
  padding: 4px 0 6px;
}
.moon-location-line {
  font-size: 14px;
  font-weight: 600;
  color: #fff;
  margin-bottom: 4px;
}
.moon-location-dot {
  color: rgba(255, 255, 255, 0.3);
  margin: 0 4px;
}
.moon-phase-emoji {
  font-size: 18px;
  margin-left: 4px;
  vertical-align: middle;
}
.moon-house-line {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.55);
}
.moon-aspect {
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}
.moon-aspect-text {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.8);
  margin-bottom: 4px;
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  align-items: center;
}
.moon-aspect-text .aspect-planet {
  font-weight: 600;
  color: #fff;
}
.moon-aspect-text .aspect-type {
  font-weight: 700;
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}
.moon-aspect-text .aspect-natal {
  color: rgba(255, 255, 255, 0.7);
}
.moon-aspect-text .aspect-orb {
  color: rgba(255, 255, 255, 0.35);
  font-size: 11px;
}
.moon-aspect-hint {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.6);
  line-height: 1.5;
  padding: 4px 0 4px 10px;
  position: relative;
}

/* ═══════════════ Transit Card ═══════════════ */
.transit-card {
  display: flex;
  flex-direction: column;
  gap: 6px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  padding: 8px 0;
}
.transit-card:last-child {
  border-bottom: none;
}
.transit-row {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  flex-wrap: wrap;
}
.transit-planet {
  font-weight: 600;
  color: #fff;
}
.transit-aspect {
  font-weight: 700;
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}
.transit-aspect.aspect--conjunction { background: rgba(255, 215, 0, 0.25); color: #ffe066; }
.transit-aspect.aspect--opposition { background: rgba(255, 80, 80, 0.25); color: #ff6b6b; }
.transit-aspect.aspect--square { background: rgba(255, 100, 50, 0.25); color: #ff8a6b; }
.transit-aspect.aspect--trine { background: rgba(80, 200, 120, 0.25); color: #6be08a; }
.transit-aspect.aspect--sextile { background: rgba(80, 160, 255, 0.25); color: #8ab8ff; }
.transit-natal {
  color: rgba(255, 255, 255, 0.75);
}
.transit-orb {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.3);
  font-weight: 500;
  margin-left: auto;
}
.transit-chat-btn {
  align-self: flex-end;
  padding: 3px 10px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  background: rgba(255, 255, 255, 0.06);
  color: rgba(255, 255, 255, 0.65);
  font-size: 10px;
  font-weight: 500;
  font-family: inherit;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
  line-height: 1.4;
}
.transit-chat-btn:hover {
  background: rgba(255, 255, 255, 0.16);
  color: #fff;
  border-color: rgba(255, 255, 255, 0.3);
  box-shadow: 0 0 12px rgba(255, 255, 255, 0.08);
}

/* ═══════════════ Retrograde Section ═══════════════ */
.section--retrograde {
  background: rgba(240, 160, 96, 0.08);
  border-color: rgba(240, 160, 96, 0.15);
}
.retrograde-card {
  border-left: 3px solid #f0a060;
  background: rgba(240, 160, 96, 0.06);
  border-radius: 12px;
  padding: 12px;
  margin-top: 8px;
}
.retrograde-card:first-child {
  margin-top: 0;
}
.retrograde-card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
.retrograde-badge {
  font-size: 11px;
  font-weight: 700;
  color: #f0a060;
  background: rgba(240, 160, 96, 0.15);
  padding: 2px 8px;
  border-radius: 6px;
}
.retrograde-planet-name {
  font-size: 13px;
  font-weight: 600;
  color: #fff;
}
.retrograde-house {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.55);
  margin-bottom: 6px;
}
.retrograde-desc {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.6);
  line-height: 1.6;
  margin-bottom: 8px;
}

/* ═══════════════ Slow Background Section ═══════════════ */
.section--slow {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(255, 255, 255, 0.06);
}
.slow-collapsed-hint {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.45);
  padding: 6px 0 2px;
  line-height: 1.4;
}

/* ═══════════════ Voice Section ═══════════════ */
.section--voice {
  border-color: rgba(255, 255, 255, 0.06);
}
</style>
