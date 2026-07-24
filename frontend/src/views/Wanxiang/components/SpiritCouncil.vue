<template>
  <div class="council-view">
    <!-- 标题 -->
    <div class="council-header">
      <h2 class="council-title">🔮 星灵议会</h2>
      <p class="council-desc">选一个你想聊的话题，听听不同星灵的视角</p>
    </div>

    <!-- 话题选择 -->
    <div class="topic-section" v-if="!selectedTopic">
      <p class="topic-prompt">今天想聊什么？</p>
      <div class="topic-grid">
        <button
          v-for="t in topics"
          :key="t.key"
          class="topic-chip"
          @click="selectTopic(t)"
        >
          <span class="topic-chip-icon">{{ t.icon }}</span>
          <span class="topic-chip-label">{{ t.label }}</span>
        </button>
      </div>
    </div>

    <!-- 选中话题后：星灵视角 -->
    <div class="perspectives-section" v-else>
      <!-- 话题头 -->
      <div class="selected-topic-bar">
        <button class="back-btn" @click="selectedTopic = null">← 换话题</button>
        <span class="selected-topic-label">
          {{ selectedTopic.icon }} {{ selectedTopic.label }}
        </span>
      </div>

      <!-- 加载动画 -->
      <div class="council-loading" v-if="isLoading">
        <p class="loading-text">星灵们正在思考中...</p>
        <div class="loading-spirits">
          <span
            v-for="(s, i) in councilSpirits"
            :key="s.planet"
            class="loading-spirit-dot"
            :style="{
              background: s.color,
              animationDelay: i * 0.2 + 's',
            }"
          ></span>
        </div>
      </div>

      <!-- 视角卡片 -->
      <div class="perspective-cards" v-else>
        <div
          v-for="(card, i) in perspectiveCards"
          :key="card.planet"
          class="perspective-card"
          :style="{
            '--p-color': card.color,
            animationDelay: i * 0.15 + 's',
          }"
        >
          <div class="p-card-header">
            <span class="p-symbol" :style="{ color: card.color }">{{ card.symbol }}</span>
            <div class="p-meta">
              <span class="p-name">{{ card.name }}</span>
              <span class="p-archetype">{{ card.archetype }}</span>
            </div>
            <span class="p-lens-tag" :style="{ background: card.color + '18', color: card.color }">
              {{ card.lensLabel }}
            </span>
            <span v-if="card.usedAI" class="p-ai-badge">✨ AI</span>
          </div>
          <p class="p-body">{{ card.perspective }}</p>
          <p class="p-gift">{{ card.gift }}</p>
        </div>
      </div>

      <!-- 综合 synthesis -->
      <div class="synthesis-card" v-if="!isLoading && synthesisText">
        <div class="synth-icon">💫</div>
        <h4 class="synth-title">星灵们的共识</h4>
        <p class="synth-body">{{ synthesisText }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from "vue";
import { apiClient } from "@/config/api";
import type {
  PlanetCharacterProfile,
  PlanetCharacterProfilesData,
  DomainReport,
} from "@/utils/types";

const props = defineProps<{
  planetProfiles: PlanetCharacterProfilesData | null;
  domains: Record<string, DomainReport> | null;
  reportId?: string;
}>();

// ── 话题定义 ──
const topics = [
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

const selectedTopic = ref<(typeof topics)[0] | null>(null);
const isLoading = ref(false);

// ── 选中话题后选择 3 个最相关星灵 ──
const councilSpirits = computed(() => {
  if (!props.planetProfiles?.planet_characters) return [];
  const profiles = props.planetProfiles.planet_characters;
  const topicKey = selectedTopic.value?.key || "";

  // 按 expertise_domains 匹配度 + core_strength 排序
  const scored = Object.values(profiles)
    .map((p: PlanetCharacterProfile) => {
      const domains = p.persona?.expertise_domains || [];
      const matchScore = domains.includes(topicKey) ? 50 : 0;
      return {
        ...p,
        matchScore: matchScore + (p.core_strength || 0),
        color: p.persona?.visual_color || "#999",
      };
    })
    .sort((a, b) => b.matchScore - a.matchScore);

  return scored.slice(0, 3);
});

// ── 视角卡片生成 ──
interface PerspectiveCard {
  planet: string;
  symbol: string;
  name: string;
  archetype: string;
  color: string;
  lensLabel: string;
  perspective: string;
  gift: string;
  usedAI?: boolean;
}

const perspectiveCards = ref<PerspectiveCard[]>([]);
const synthesisText = ref("");

// 视角标签映射
const lensLabels: Record<string, string> = {
  SUN: "自我视角",
  MOON: "情感视角",
  MERCURY: "理性视角",
  VENUS: "价值视角",
  MARS: "行动视角",
  JUPITER: "成长视角",
  SATURN: "现实视角",
};

async function selectTopic(topic: (typeof topics)[0]) {
  selectedTopic.value = topic;
  isLoading.value = true;
  perspectiveCards.value = [];
  synthesisText.value = "";

  // 模拟星灵思考延迟
  await new Promise((r) => setTimeout(r, 1200));

  const domainData = props.domains?.[topic.key];
  const coreTheme = domainData?.core_theme || "";
  const structure = domainData?.structure || "";
  const psychology = domainData?.psychology || "";
  const suggestion = domainData?.suggestion || "";

  // 尝试 AI 生成每个星灵的视角
  const aiCards = await Promise.all(
    councilSpirits.value.map(async (spirit) => {
      const persona = spirit.persona;
      let perspective = "";
      let usedAI = false;

      if (props.reportId) {
        try {
          const res = await apiClient.post(`/spirit-chat/${props.reportId}`, {
            planet: spirit.planet,
            topic: topic.key,
            message: `请从你的视角，用你的风格，简短地（150字以内）谈谈你对「${topic.label}」这个人生领域的看法。结合这个用户的星盘配置来谈。`,
            history: [],
          });
          if (res.data?.status === "success" && res.data.data?.response) {
            perspective = res.data.data.response;
            usedAI = true;
          }
        } catch { /* fallback */ }
      }

      if (!perspective) {
        perspective = buildPerspective(
          persona?.name_zh || "",
          persona?.advice_approach || "",
          persona?.voice_tone?.slice(0, 60) || "",
          coreTheme,
          structure,
          psychology
        );
      }

      return {
        planet: spirit.planet,
        symbol: persona?.symbol || "●",
        name: persona?.name_zh || "",
        archetype: persona?.archetype_zh || "",
        color: persona?.visual_color || "#999",
        lensLabel: lensLabels[spirit.planet] || "综合视角",
        perspective,
        gift: persona?.gift_to_user || "",
        usedAI,
      };
    })
  );

  perspectiveCards.value = aiCards;

  // AI 综合 synthesis
  if (props.reportId && aiCards.some((c) => c.usedAI)) {
    try {
      const res = await apiClient.post(`/spirit-chat/${props.reportId}`, {
        planet: "SUN",
        topic: topic.key,
        message: `以下三位星灵分别从不同角度谈了「${topic.label}」：\n${aiCards.map((c) => `${c.name}：${c.perspective.slice(0, 100)}`).join("\n")}\n\n请用2-3句话综合三位星灵的观点，给出一个温暖的总结。`,
        history: [],
      });
      if (res.data?.status === "success" && res.data.data?.response) {
        synthesisText.value = res.data.data.response;
      }
    } catch { /* fallback */ }
  }

  if (!synthesisText.value) {
    synthesisText.value = buildSynthesis(structure, suggestion, aiCards);
  }
  isLoading.value = false;
}

function buildPerspective(
  name: string,
  _approach: string,
  _voiceTone: string,
  coreTheme: string,
  structure: string,
  psychology: string
): string {
  // 引擎在后端永远在线，此函数仅在网络完全不可达时兜底
  const themeText = coreTheme ? `核心议题：${coreTheme}。` : "";
  const structText = structure ? structure.slice(0, 200) : "";
  const psychText = psychology ? `从心理层面看：${psychology.slice(0, 120)}` : "";
  return `${name}看这个话题——${themeText}${structText} ${psychText}`.slice(0, 400);
}

function buildSynthesis(
  structure: string,
  suggestion: string,
  cards: PerspectiveCard[]
): string {
  const names = cards.map((c) => c.name).join("、");
  const structText = structure ? structure.slice(0, 200) : "你的星盘在这方面有独特的配置。";
  const suggestText = suggestion ? `建议方向——${suggestion.slice(0, 150)}` : "";
  return `${names}——三位星灵从不同角度看了这个话题。${structText} ${suggestText}`;
}
</script>

<style scoped>
.council-view {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding-bottom: 100px;
}

/* ── 头部 ── */
.council-header {
  text-align: center;
}
.council-title {
  font-size: 24px;
  font-weight: 700;
  color: #4a3728;
  margin: 0 0 6px;
}
.council-desc {
  font-size: 13px;
  color: #8b7355;
  margin: 0;
}

/* ── 话题选择 ── */
.topic-section {
  text-align: center;
}
.topic-prompt {
  font-size: 15px;
  color: #6b5744;
  margin: 0 0 14px;
  font-weight: 600;
}
.topic-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}
.topic-chip {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 18px 12px;
  border-radius: 20px;
  border: 1.5px solid rgba(0, 0, 0, 0.05);
  background: rgba(255, 255, 255, 0.7);
  cursor: pointer;
  transition: all 0.25s;
  font-family: inherit;
}
.topic-chip:hover {
  border-color: rgba(255, 154, 139, 0.3);
  background: rgba(255, 255, 255, 0.9);
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.05);
}
.topic-chip-icon {
  font-size: 26px;
}
.topic-chip-label {
  font-size: 13px;
  font-weight: 600;
  color: #4a3728;
}

/* ── 选中话题 bar ── */
.selected-topic-bar {
  display: flex;
  align-items: center;
  gap: 12px;
}
.back-btn {
  padding: 8px 16px;
  border-radius: 14px;
  border: none;
  background: rgba(0, 0, 0, 0.04);
  color: #8b7355;
  font-size: 13px;
  cursor: pointer;
  font-family: inherit;
  transition: all 0.2s;
}
.back-btn:hover {
  background: rgba(0, 0, 0, 0.07);
  color: #4a3728;
}
.selected-topic-label {
  font-size: 16px;
  font-weight: 700;
  color: #4a3728;
}

/* ── 加载动画 ── */
.council-loading {
  text-align: center;
  padding: 40px 0;
}
.loading-text {
  font-size: 15px;
  color: #8b7355;
  margin: 0 0 20px;
  animation: pulse-text 1.5s ease-in-out infinite;
}
@keyframes pulse-text {
  0%,
  100% {
    opacity: 0.5;
  }
  50% {
    opacity: 1;
  }
}
.loading-spirits {
  display: flex;
  justify-content: center;
  gap: 16px;
}
.loading-spirit-dot {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  animation: dot-jump 1s ease-in-out infinite;
}
@keyframes dot-jump {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-18px);
  }
}

/* ── 视角卡片 ── */
.perspective-cards {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.perspective-card {
  padding: 20px;
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.8);
  border: 1.5px solid rgba(0, 0, 0, 0.04);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.03);
  animation: card-enter 0.5s cubic-bezier(0.25, 0.46, 0.45, 0.94) both;
  transition: all 0.2s;
}
.perspective-card:hover {
  border-color: var(--p-color);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
}
@keyframes card-enter {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.p-card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}
.p-symbol {
  font-size: 28px;
  width: 40px;
  text-align: center;
  flex-shrink: 0;
}
.p-meta {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 1px;
}
.p-name {
  font-size: 16px;
  font-weight: 700;
  color: #4a3728;
}
.p-archetype {
  font-size: 11px;
  color: #8b7355;
}
.p-lens-tag {
  font-size: 11px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 10px;
  flex-shrink: 0;
}
.p-ai-badge {
  font-size: 10px; padding: 2px 8px; border-radius: 8px;
  background: rgba(240,192,96,0.15); color: #c79100; flex-shrink: 0;
}
.p-body {
  font-size: 13.5px;
  color: #5c4a3a;
  line-height: 1.7;
  margin: 0 0 8px;
}
.p-gift {
  font-size: 12px;
  color: #a89880;
  margin: 0;
  font-style: italic;
}

/* ── 综合 synthesis ── */
.synthesis-card {
  padding: 22px 24px;
  border-radius: 22px;
  background: linear-gradient(
    135deg,
    rgba(255, 245, 238, 0.9),
    rgba(255, 240, 245, 0.8)
  );
  border: 1px solid rgba(255, 154, 139, 0.15);
  text-align: center;
  animation: card-enter 0.6s 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94) both;
}
.synth-icon {
  font-size: 28px;
  margin-bottom: 8px;
}
.synth-title {
  font-size: 17px;
  font-weight: 700;
  color: #4a3728;
  margin: 0 0 10px;
}
.synth-body {
  font-size: 14px;
  color: #5c4a3a;
  line-height: 1.7;
  margin: 0;
  text-align: left;
}

/* ── 响应式 ── */
@media (max-width: 400px) {
  .topic-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .perspective-card {
    padding: 16px;
  }
}
</style>
