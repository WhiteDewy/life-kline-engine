<template>
  <div class="codex-view">
    <div class="codex-header">
      <h2 class="codex-title">📜 星灵宝典</h2>
      <p class="codex-desc">用星灵的视角，深度解读你的人生课题</p>
    </div>

    <!-- ═══ 领域选择 ═══ -->
    <div class="domain-picker" v-if="!selectedDomain">
      <p class="picker-prompt">选择你想深入了解的领域——</p>
      <div class="domain-grid">
        <button
          v-for="d in domains"
          :key="d.key"
          class="domain-card"
          @click="selectDomain(d)"
        >
          <span class="domain-card-icon">{{ d.icon }}</span>
          <span class="domain-card-label">{{ d.label }}</span>
          <span class="domain-card-spirit" v-if="d.matchedSpirit">
            {{ d.matchedSpirit.symbol }}
          </span>
        </button>
      </div>
    </div>

    <!-- ═══ 宝典卷轴 ═══ -->
    <div class="scroll-view" v-else>
      <button class="back-link" @click="selectedDomain = null">← 换一个领域</button>

      <!-- 卷轴 -->
      <div class="scroll" :style="{ '--s-color': selectedDomain.matchedSpirit?.color || '#d4af37' }">
        <!-- 顶部装饰 -->
        <div class="scroll-top-ornament">
          <svg viewBox="0 0 200 20" class="ornament-svg">
            <path d="M10,10 Q50,0 100,10 Q150,20 190,10" fill="none" stroke="var(--s-color)" stroke-width="1" opacity="0.3" />
            <circle cx="100" cy="10" r="4" fill="var(--s-color)" opacity="0.4" />
          </svg>
        </div>

        <!-- 标题横幅 -->
        <div class="scroll-banner">
          <div class="banner-left"></div>
          <div class="banner-center">
            <h3 class="banner-title">《{{ selectedDomain.label }}》</h3>
            <span class="banner-sub" v-if="selectedDomain.matchedSpirit">
              解读星灵：{{ selectedDomain.matchedSpirit.symbol }} {{ selectedDomain.matchedSpirit.name }}
            </span>
          </div>
          <div class="banner-right"></div>
        </div>

        <!-- 内容区 -->
        <div class="scroll-body">
          <!-- 古占结构 -->
          <div class="scroll-section scroll-section--structure">
            <h4 class="section-heading">
              <span class="section-dot"></span>
              古占结构 · 事件潜力
            </h4>
            <p class="section-text">{{ structureText }}</p>
          </div>

          <!-- 心理感受 -->
          <div class="scroll-section scroll-section--psychology">
            <h4 class="section-heading">
              <span class="section-dot section-dot--psych"></span>
              心理感受 · 内在体验
            </h4>
            <p class="section-text">{{ psychologyText }}</p>
          </div>

          <!-- 星灵建议 -->
          <div class="scroll-section scroll-section--advice">
            <h4 class="section-heading">
              <span class="section-dot section-dot--advice"></span>
              星灵建言 · 行动方向
            </h4>
            <p class="section-text">{{ adviceText }}</p>
            <div class="spirit-note" v-if="selectedDomain.matchedSpirit">
              <span class="spirit-note-symbol">{{ selectedDomain.matchedSpirit.symbol }}</span>
              <span class="spirit-note-text">
                "{{ selectedDomain.matchedSpirit.gift }}"
              </span>
            </div>
          </div>
        </div>

        <!-- 底部装饰 -->
        <div class="scroll-bottom-ornament">
          <svg viewBox="0 0 200 20" class="ornament-svg">
            <path d="M10,10 Q50,20 100,10 Q150,0 190,10" fill="none" stroke="var(--s-color)" stroke-width="1" opacity="0.3" />
            <circle cx="100" cy="10" r="4" fill="var(--s-color)" opacity="0.4" />
          </svg>
        </div>
      </div>

      <!-- CTA -->
      <div class="scroll-cta-row" v-if="selectedDomain.matchedSpirit">
        <button
          class="scroll-cta"
          @click="$emit('chatWith', selectedDomain.matchedSpirit.planet)"
          :style="{ background: selectedDomain.matchedSpirit.color }"
        >
          💬 和{{ selectedDomain.matchedSpirit.name }}深入聊聊
        </button>
        <button class="scroll-share" @click="$emit('share', {
          symbol: selectedDomain.matchedSpirit.symbol,
          name: selectedDomain.matchedSpirit.name,
          archetype: '',
          color: selectedDomain.matchedSpirit.color,
          message: adviceText,
        })">
          📤
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from "vue";
import type {
  PlanetCharacterProfile,
  PlanetCharacterProfilesData,
  DomainReport,
} from "@/utils/types";

const props = defineProps<{
  planetProfiles: PlanetCharacterProfilesData | null;
  domains: Record<string, DomainReport> | null;
}>();

defineEmits<{
  chatWith: [planet: string];
  share: [data: { symbol: string; name: string; archetype: string; color: string; message: string }];
}>();

interface DomainEntry {
  key: string;
  icon: string;
  label: string;
  matchedSpirit: {
    planet: string;
    symbol: string;
    name: string;
    color: string;
    gift: string;
  } | null;
}

const selectedDomain = ref<DomainEntry | null>(null);

const domainList = [
  { key: "personal", icon: "🪐", label: "性格底色" },
  { key: "career", icon: "💼", label: "事业方向" },
  { key: "finance", icon: "💰", label: "财务格局" },
  { key: "romance", icon: "💛", label: "桃花感情" },
  { key: "marriage", icon: "💍", label: "婚姻画像" },
  { key: "family", icon: "🏠", label: "原生家庭" },
  { key: "work_skill", icon: "🔧", label: "工作技能" },
  { key: "education", icon: "📚", label: "学业方向" },
  { key: "health", icon: "🌿", label: "健康体质" },
];

const domains = computed<DomainEntry[]>(() => {
  const profiles = props.planetProfiles?.planet_characters || {};
  return domainList.map((d) => {
    // 匹配最相关星灵
    let bestSpirit: PlanetCharacterProfile | null = null;
    let bestScore = -1;
    for (const [, p] of Object.entries(profiles)) {
      const profile = p as PlanetCharacterProfile;
      const domains = profile.persona?.expertise_domains || [];
      const score = domains.includes(d.key) ? profile.core_strength || 0 : 0;
      if (score > bestScore) {
        bestScore = score;
        bestSpirit = profile;
      }
    }

    return {
      key: d.key,
      icon: d.icon,
      label: d.label,
      matchedSpirit: bestSpirit
        ? {
            planet: bestSpirit.planet,
            symbol: bestSpirit.persona?.symbol || "●",
            name: bestSpirit.persona?.name_zh || "",
            color: bestSpirit.persona?.visual_color || "#999",
            gift: bestSpirit.persona?.gift_to_user || "",
          }
        : null,
    };
  });
});

const structureText = computed(() => {
  if (!selectedDomain.value) return "";
  const d = props.domains?.[selectedDomain.value.key];
  return d?.structure || "从星盘结构来看，这个领域由多个行星和宫位共同影响。详细的解读正在生成中——请稍后再试。";
});

const psychologyText = computed(() => {
  if (!selectedDomain.value) return "";
  const d = props.domains?.[selectedDomain.value.key];
  return d?.psychology || "从心理层面来看，你对这个领域的感受和处理方式与你的成长经历和内在需求密切相关。";
});

const adviceText = computed(() => {
  if (!selectedDomain.value) return "";
  const d = props.domains?.[selectedDomain.value.key];
  return d?.suggestion || "综合星盘配置，建议你在这个领域多关注自己的直觉——有时候身体比头脑更早知道答案。";
});

function selectDomain(d: DomainEntry) {
  selectedDomain.value = d;
  // 滚动到卷轴顶部
  setTimeout(() => {
    document.querySelector(".scroll-view")?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, 100);
}
</script>

<style scoped>
.codex-view {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding-bottom: 100px;
}

.codex-header {
  text-align: center;
}
.codex-title {
  font-size: 24px;
  font-weight: 700;
  color: #4a3728;
  margin: 0 0 6px;
}
.codex-desc {
  font-size: 13px;
  color: #8b7355;
  margin: 0;
}

/* ── 领域选择 ── */
.domain-picker {
  text-align: center;
}
.picker-prompt {
  font-size: 14px;
  color: #6b5744;
  margin: 0 0 14px;
}
.domain-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}
.domain-card {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 20px 14px;
  border-radius: 20px;
  border: 1.5px solid rgba(0, 0, 0, 0.05);
  background: rgba(255, 255, 255, 0.7);
  cursor: pointer;
  transition: all 0.25s;
  font-family: inherit;
}
.domain-card:hover {
  border-color: rgba(212, 175, 55, 0.3);
  background: rgba(255, 255, 255, 0.9);
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.05);
}
.domain-card-icon {
  font-size: 26px;
}
.domain-card-label {
  font-size: 13px;
  font-weight: 600;
  color: #4a3728;
}
.domain-card-spirit {
  position: absolute;
  top: 8px;
  right: 10px;
  font-size: 14px;
  opacity: 0.5;
}

/* ── 卷轴 ── */
.scroll-view {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.back-link {
  align-self: flex-start;
  padding: 6px 14px;
  border-radius: 12px;
  border: none;
  background: rgba(0, 0, 0, 0.03);
  color: #8b7355;
  font-size: 13px;
  cursor: pointer;
  font-family: inherit;
}
.back-link:hover {
  background: rgba(0, 0, 0, 0.06);
}

.scroll {
  border-radius: 16px;
  background: linear-gradient(
    180deg,
    rgba(255, 252, 245, 0.95) 0%,
    rgba(255, 250, 240, 0.9) 50%,
    rgba(255, 248, 235, 0.95) 100%
  );
  border: 1px solid rgba(212, 175, 55, 0.15);
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.05);
  overflow: hidden;
}

.scroll-top-ornament,
.scroll-bottom-ornament {
  padding: 8px 0;
  display: flex;
  justify-content: center;
}
.ornament-svg {
  width: 160px;
  height: 14px;
}

/* 标题横幅 */
.scroll-banner {
  display: flex;
  align-items: stretch;
  margin: 0 20px;
  border-top: 1px solid rgba(212, 175, 55, 0.2);
  border-bottom: 1px solid rgba(212, 175, 55, 0.2);
  padding: 14px 0;
}
.banner-left,
.banner-right {
  width: 4px;
  background: linear-gradient(180deg, transparent, rgba(212, 175, 55, 0.3), transparent);
}
.banner-center {
  flex: 1;
  text-align: center;
  padding: 0 16px;
}
.banner-title {
  font-size: 19px;
  font-weight: 700;
  color: #3a2718;
  margin: 0 0 4px;
  letter-spacing: 0.05em;
}
.banner-sub {
  font-size: 12px;
  color: #8b7355;
}

/* 内容区 */
.scroll-body {
  padding: 20px 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.scroll-section {
  padding: 16px 18px;
  border-radius: 14px;
}
.scroll-section--structure {
  background: rgba(139, 115, 85, 0.06);
}
.scroll-section--psychology {
  background: rgba(155, 196, 208, 0.08);
}
.scroll-section--advice {
  background: rgba(240, 192, 96, 0.08);
}

.section-heading {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 700;
  color: #4a3728;
  margin: 0 0 10px;
}
.section-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #8b7355;
}
.section-dot--psych {
  background: #9bc4d0;
}
.section-dot--advice {
  background: #f0c060;
}

.section-text {
  font-size: 13.5px;
  color: #5c4a3a;
  line-height: 1.8;
  margin: 0;
}

.spirit-note {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-top: 12px;
  padding: 10px 14px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.6);
  border-left: 3px solid var(--s-color);
}
.spirit-note-symbol {
  font-size: 20px;
  flex-shrink: 0;
}
.spirit-note-text {
  font-size: 13px;
  color: #6b5744;
  font-style: italic;
  line-height: 1.5;
}

/* CTA */
.scroll-cta-row {
  display: flex;
  gap: 8px;
}
.scroll-cta {
  flex: 1;
  width: 100%;
  padding: 16px;
  border-radius: 18px;
  border: none;
  color: #fff;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  font-family: inherit;
  transition: all 0.2s;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.08);
}
.scroll-cta:hover {
  filter: brightness(1.1);
  transform: translateY(-1px);
}
.scroll-share {
  padding: 16px;
  border-radius: 18px;
  border: 1.5px solid rgba(0,0,0,0.08);
  background: rgba(255,255,255,0.8);
  font-size: 18px;
  cursor: pointer;
  transition: all 0.2s;
}
.scroll-share:hover {
  background: rgba(255,255,255,1);
  border-color: rgba(0,0,0,0.15);
}

/* ── 响应式 ── */
@media (max-width: 400px) {
  .domain-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
