<template>
  <div class="dq-card">
    <div class="dq-header">
      <span class="dq-icon">💭</span>
      <span class="dq-label">每日一问</span>
    </div>

    <p class="dq-question">{{ todayQuestion }}</p>

    <div class="dq-spirits" v-if="!answered">
      <p class="dq-prompt">选择一个星灵来回答——</p>
      <div class="dq-spirit-row">
        <button
          v-for="s in answerSpirits"
          :key="s.planet"
          class="dq-spirit-btn"
          :style="{ '--sq-color': s.color }"
          @click="getAnswer(s)"
        >
          <SpiritAvatar :planet="s.planet" :symbol="s.symbol" :name="s.name" :color="s.color" size="sm" />
          <span class="dq-spirit-name">{{ s.name }}</span>
        </button>
      </div>
    </div>

    <div class="dq-answer" v-else>
      <div class="dq-answer-head">
        <SpiritAvatar :planet="answeredBy.planet" :symbol="answeredBy.symbol" :name="answeredBy.name" :color="answeredBy.color" size="sm" />
        <span class="dq-answer-by">{{ answeredBy.name }}的回答</span>
      </div>
      <p class="dq-answer-text">"{{ answerText }}"</p>
      <button class="dq-retry" @click="answered = false">换一个问题 🔄</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from "vue";
import SpiritAvatar from "./SpiritAvatar.vue";
import type { PlanetCharacterProfilesData, PlanetCharacterProfile } from "@/utils/types";

const props = defineProps<{
  planetProfiles: PlanetCharacterProfilesData | null;
}>();

const answered = ref(false);
const answeredBy = ref<any>(null);
const answerText = ref("");
const questionIndex = ref(0);

// 每日问题库（按天轮换）
const questionBank = [
  "今天有什么事情让你感到充实？",
  "你最近一次感到被理解是什么时候？",
  "如果今天可以改变一件事，会是什么？",
  "你现在最需要听到的一句话是什么？",
  "有什么事情你一直在拖延，其实只需要五分钟就能开始？",
  "最近有没有人对你说过让你心里一暖的话？",
  "你最近在为什么事情感到骄傲，哪怕很小？",
  "如果把你今天的心情比作一种天气，会是什么？",
  "你上一次完全放松、什么都不想，是什么时候？",
  "有没有什么习惯，你坚持了很久？它带给你什么？",
  "最近有没有哪本书、哪句话或者哪首歌特别触动你？",
  "你现在的生活里，有没有什么'刚刚好'的事情？",
  "如果有一位星灵可以陪你度过今天，你希望是谁？为什么？",
  "你有没有对某件事情的直觉，后来被证明是对的？",
];

const todayQuestion = computed(() => {
  const dayOfYear = Math.floor(
    (Date.now() - new Date(new Date().getFullYear(), 0, 0).getTime()) / 86400000
  );
  return questionBank[dayOfYear % questionBank.length];
});

const answerSpirits = computed(() => {
  const profiles = props.planetProfiles?.planet_characters || {};
  const order = ["SUN", "MOON", "MERCURY", "VENUS", "MARS", "JUPITER", "SATURN"];
  return order
    .map((key) => {
      const p = profiles[key] as PlanetCharacterProfile | undefined;
      if (!p) return null;
      return {
        planet: key,
        symbol: p.persona?.symbol || "●",
        name: p.persona?.name_zh || key,
        color: p.persona?.visual_color || "#999",
        adviceApproach: p.persona?.advice_approach || "",
        gift: p.persona?.gift_to_user || "",
      };
    })
    .filter(Boolean) as any[];
});

function getAnswer(spirit: any) {
  answeredBy.value = spirit;
  const tpls = [
    `让我用我的方式来看这个问题——${spirit.adviceApproach?.slice(0, 120) || "跟着你的心走，答案就在不远处。"}`,
    `嗯，这个问题...${spirit.gift?.slice(0, 120) || "我能给你的最好的东西，就是帮你记起你已经知道的事。"}`,
    `从我的位置看过去——你问的其实是另一个更深的问题。不急，我们慢慢来。`,
    `我听到了。你知道吗，有时候问题本身比答案更重要。今天这个问题就是个好问题。`,
  ];
  answerText.value = tpls[Math.floor(Math.random() * tpls.length)];
  answered.value = true;
}
</script>

<style scoped>
.dq-card {
  padding: 20px;
  border-radius: 22px;
  background: rgba(255,255,255,0.7);
  border: 1px solid rgba(0,0,0,0.04);
}
.dq-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}
.dq-icon { font-size: 18px; }
.dq-label { font-size: 13px; font-weight: 700; color: #8b7355; }
.dq-question {
  font-size: 16px; font-weight: 600; color: #4a3728;
  margin: 0 0 14px; line-height: 1.5;
}
.dq-prompt { font-size: 12px; color: #a89880; margin: 0 0 8px; }
.dq-spirit-row { display: flex; gap: 8px; flex-wrap: wrap; }
.dq-spirit-btn {
  display: flex; align-items: center; gap: 6px;
  padding: 8px 14px; border-radius: 16px; border: 1px solid rgba(0,0,0,0.06);
  background: rgba(255,255,255,0.6); cursor: pointer; font-family: inherit;
  transition: all 0.2s;
}
.dq-spirit-btn:hover { border-color: var(--sq-color); background: rgba(255,255,255,0.9); }
.dq-spirit-name { font-size: 12px; font-weight: 600; color: #4a3728; }

.dq-answer-head { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.dq-answer-by { font-size: 13px; font-weight: 600; color: #6b5744; }
.dq-answer-text { font-size: 14px; color: #4a3728; line-height: 1.7; margin: 0 0 10px; font-style: italic; }
.dq-retry {
  padding: 8px 16px; border-radius: 14px; border: none;
  background: rgba(0,0,0,0.04); color: #8b7355; font-size: 12px; font-weight: 600;
  cursor: pointer; font-family: inherit;
}
</style>
