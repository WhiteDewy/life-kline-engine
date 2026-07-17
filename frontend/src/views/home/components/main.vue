<template>
  <div class="page">
    <div class="glow glow-a"></div>
    <div class="glow glow-b"></div>
    <div class="glow glow-c"></div>

    <!-- ═══ Hero：情绪驱动 ═══ -->
    <section class="hero">
      <p class="heroEyebrow">你的情绪是信号，不是问题</p>
      <h1 class="title">最近是不是总觉得<br />哪里不太对？</h1>
      <p class="subtitle">
        这不一定是你的问题。很多人只是走到了同一个人生阶段——<br />星盘可以帮你解释清楚。
      </p>
      <el-button class="cta" type="primary" size="large" round @click="startExplore">
        免费生成我的星盘解读
      </el-button>
      <p class="ctaHint">
        <span class="ctaTrust">已帮助 12,000+ 人更了解自己</span>
        <span class="ctaDot">·</span>
        <span>不需要懂占星</span>
        <span class="ctaDot">·</span>
        <span>大约 3 分钟读完</span>
      </p>
    </section>

    <!-- ═══ 快速入口问题：替代分析类型选择 ═══ -->
    <section class="questions">
      <h2 class="questionsTitle">你想先聊聊哪个？</h2>
      <p class="questionsSub">点击你关心的问题，直接进入对应解读</p>

      <div class="questionGrid">
        <button
          v-for="q in quickQuestions"
          :key="q.key"
          class="questionCard"
          @click="openQuestion(q)"
        >
          <span class="questionIcon">{{ q.icon }}</span>
          <span class="questionText">{{ q.text }}</span>
          <span class="questionArrow">→</span>
        </button>
      </div>
    </section>

    <!-- ═══ 按主题浏览（降级） ═══ -->
    <section class="groups">
      <h2 class="groupTitle">或者，按主题浏览</h2>

      <div class="groupGrid">
        <div class="groupCard" v-for="g in groups" :key="g.key">
          <div class="groupIcon">{{ g.icon }}</div>
          <h3 class="groupName">{{ g.name }}</h3>
          <ul class="groupItems">
            <li v-for="item in g.items" :key="item">{{ item }}</li>
          </ul>
        </div>
      </div>
    </section>

    <!-- ═══ 信任与社交证明 ═══ -->
    <section class="bottom">
      <div class="trustBar">
        <span class="trustItem">🔒 你的数据只属于你</span>
        <span class="trustDivider">|</span>
        <span class="trustItem">🚫 不贩售恐惧 · 不做宿命预测</span>
        <span class="trustDivider">|</span>
        <span class="trustItem">🌟 基于古典+现代占星双重验证</span>
      </div>

      <p class="belief">
        我们不贩卖恐惧，不制造依赖。<br />
        只做你人生阶段的解释器和朋友。
      </p>

      <div v-if="showExamples" class="examples">
        <p class="exampleHint">或者，先看看别人的报告长什么样——</p>
        <div class="exampleRow">
          <button
            class="examplePill"
            v-for="ex in examples"
            :key="ex.key"
            @click="openExample(ex)"
          >
            {{ ex.name }} · {{ ex.tagline }}
          </button>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from "vue-router";
import { FEATURED_EXAMPLES, HOMEPAGE_EXAMPLE_VISIBLE } from "@/config/examples";

const router = useRouter();
const showExamples = HOMEPAGE_EXAMPLE_VISIBLE;
const examples = FEATURED_EXAMPLES;

const quickQuestions = [
  {
    key: "natal_blueprint",
    icon: "🪐",
    text: "我是什么样的人？适合做什么？",
    analysis: "natal_blueprint",
  },
  {
    key: "phase_navigation",
    icon: "🧭",
    text: "我现在为什么这么累？什么时候能好？",
    analysis: "phase_navigation",
  },
  {
    key: "finance",
    icon: "💰",
    text: "我的钱到底从哪里来？正财还是偏财？",
    analysis: "phase_navigation",
  },
  {
    key: "romance",
    icon: "💛",
    text: "为什么我总是在感情里遇到同样的问题？",
    analysis: "natal_blueprint",
  },
  {
    key: "career",
    icon: "💼",
    text: "我适合做什么事业？方向在哪里？",
    analysis: "natal_blueprint",
  },
  {
    key: "monthly",
    icon: "🌙",
    text: "这个月我应该抓住什么、避开什么？",
    analysis: "monthly_lunar_return",
  },
];

const groups = [
  {
    key: "self",
    icon: "🪐",
    name: "认识自己",
    items: ["你的性格底色", "你的外形和气质"],
  },
  {
    key: "work",
    icon: "💼",
    name: "事业与财富",
    items: ["事业方向", "工作方式", "学业发展", "财运格局"],
  },
  {
    key: "rel",
    icon: "💛",
    name: "关系与情感",
    items: ["桃花感情", "婚姻画像", "原生家庭", "事业合伙", "亲子关系"],
  },
  {
    key: "now",
    icon: "🧭",
    name: "当下指引",
    items: ["当前人生阶段", "本月运势提醒"],
  },
  {
    key: "body",
    icon: "🌿",
    name: "身体",
    items: ["先天体质", "健康提醒"],
  },
];

function startExplore() {
  router.push({ name: "analysis", params: { type: "natal_blueprint" } });
}

function openQuestion(q: (typeof quickQuestions)[0]) {
  router.push({ name: "analysis", params: { type: q.analysis } });
}

function openExample(ex: (typeof examples)[0]) {
  router.push({
    name: "report",
    query: { example: ex.key, analysis: "natal_blueprint" },
  });
}
</script>

<style scoped lang="less">
.page {
  min-height: calc(100vh - var(--h-footer));
  position: relative;
  overflow: hidden;
  padding: 60px 20px 80px;
  background: linear-gradient(180deg, #020617 0%, #0a1122 50%, #0f172a 100%);
}

/* ── 氛围光 ── */
.glow {
  position: absolute;
  border-radius: 50%;
  filter: blur(120px);
  opacity: 0.35;
  pointer-events: none;
}
.glow-a {
  width: 340px;
  height: 340px;
  top: -80px;
  left: -120px;
  background: rgba(212, 175, 55, 0.10);
}
.glow-b {
  width: 420px;
  height: 420px;
  right: -180px;
  top: 200px;
  background: rgba(99, 102, 241, 0.08);
}
.glow-c {
  width: 260px;
  height: 260px;
  left: 30%;
  bottom: -80px;
  background: rgba(16, 185, 129, 0.06);
}

/* ── Hero ── */
.hero {
  position: relative;
  z-index: 1;
  text-align: center;
  padding: 30px 0 20px;
}
.heroEyebrow {
  color: #d4af37;
  font-size: 13px;
  letter-spacing: 0.14em;
  margin: 0 0 18px;
  opacity: 0.8;
}
.title {
  color: #f8fafc;
  font-size: 48px;
  line-height: 1.18;
  letter-spacing: -0.03em;
  font-family: "Georgia", "Times New Roman", serif;
  margin: 0;
}
.subtitle {
  margin: 18px 0 0;
  color: #94a3b8;
  font-size: 16px;
  line-height: 1.8;
  max-width: 560px;
  margin-left: auto;
  margin-right: auto;
}
.cta {
  margin-top: 32px;
  font-weight: 700;
  min-width: 240px;
  font-size: 16px;
  height: 48px;
}
.ctaHint {
  margin-top: 14px;
  color: #64748b;
  font-size: 13px;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}
.ctaTrust {
  color: #d4af37;
  font-weight: 600;
}
.ctaDot {
  color: #334155;
}

/* ── 快速入口问题 ── */
.questions {
  position: relative;
  z-index: 1;
  max-width: 720px;
  margin: 56px auto 0;
  text-align: center;
}
.questionsTitle {
  color: #f1f5f9;
  font-size: 22px;
  margin: 0 0 8px;
}
.questionsSub {
  color: #64748b;
  font-size: 14px;
  margin: 0 0 24px;
}
.questionGrid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
}
.questionCard {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 18px 20px;
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  background: rgba(15, 23, 42, 0.55);
  backdrop-filter: blur(10px);
  text-align: left;
  cursor: pointer;
  transition: all 0.25s;
}
.questionCard:hover {
  border-color: rgba(212, 175, 55, 0.25);
  background: rgba(212, 175, 55, 0.04);
  transform: translateY(-1px);
}
.questionIcon {
  font-size: 22px;
  flex-shrink: 0;
}
.questionText {
  color: #cbd5e1;
  font-size: 15px;
  line-height: 1.5;
  flex: 1;
}
.questionArrow {
  color: #475569;
  font-size: 14px;
  flex-shrink: 0;
  transition: all 0.2s;
}
.questionCard:hover .questionArrow {
  color: #d4af37;
  transform: translateX(3px);
}

/* ── 按主题浏览 ── */
.groups {
  position: relative;
  z-index: 1;
  max-width: 960px;
  margin: 56px auto 0;
}
.groupTitle {
  text-align: center;
  color: #64748b;
  font-size: 16px;
  margin: 0 0 18px;
  font-weight: 400;
}
.groupGrid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 14px;
}
.groupCard {
  padding: 20px 16px;
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.05);
  background: rgba(15, 23, 42, 0.40);
  backdrop-filter: blur(10px);
  transition: border-color 0.2s;
}
.groupCard:hover {
  border-color: rgba(255, 255, 255, 0.10);
}
.groupIcon {
  font-size: 22px;
}
.groupName {
  margin: 8px 0 0;
  color: #e2e8f0;
  font-size: 15px;
}
.groupItems {
  margin: 10px 0 0;
  padding: 0;
  list-style: none;
  display: grid;
  gap: 5px;
}
.groupItems li {
  color: #94a3b8;
  font-size: 13px;
  line-height: 1.5;
}

/* ── 底部 ── */
.bottom {
  position: relative;
  z-index: 1;
  text-align: center;
  margin-top: 56px;
}
.trustBar {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
  margin-bottom: 28px;
}
.trustItem {
  color: #64748b;
  font-size: 13px;
}
.trustDivider {
  color: #1e293b;
}
.belief {
  color: #64748b;
  font-size: 14px;
  line-height: 1.8;
}
.examples {
  margin-top: 24px;
}
.exampleHint {
  color: #64748b;
  font-size: 13px;
  margin: 0 0 10px;
}
.exampleRow {
  display: flex;
  justify-content: center;
  gap: 10px;
  flex-wrap: wrap;
}
.examplePill {
  display: inline-flex;
  align-items: center;
  padding: 9px 18px;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.02);
  color: #94a3b8;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}
.examplePill:hover {
  border-color: rgba(212, 175, 55, 0.25);
  color: #cbd5e1;
  background: rgba(212, 175, 55, 0.04);
}

/* ── 响应式 ── */
@media (max-width: 900px) {
  .groupGrid { grid-template-columns: repeat(3, 1fr); }
  .questionGrid { grid-template-columns: 1fr; }
  .title { font-size: 36px; }
}
@media (max-width: 560px) {
  .groupGrid { grid-template-columns: 1fr 1fr; }
  .title { font-size: 28px; }
  .subtitle { font-size: 14px; }
  .questionCard { padding: 14px 16px; }
  .questionText { font-size: 14px; }
}
</style>
