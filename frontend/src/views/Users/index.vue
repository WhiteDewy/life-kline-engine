<template>
  <div class="page">
    <div class="backdrop"></div>

    <div class="wrap">
      <section class="hero">
        <div class="heroMain">
          <div class="eyebrow">Test Users</div>
          <h1 class="title">用户列表</h1>
          <p class="summary">
            这里放测试用出生资料。现在先放夏天，后面你给新的用户信息，我继续往这个列表里加。
          </p>
        </div>

        <aside class="heroAside">
          <div class="panelEyebrow">Usage</div>
          <h2 class="panelTitle">直接从用户卡片进入测试</h2>
          <ul class="list">
            <li>查看本命蓝图：直接生成“我是谁、适合做什么、事业财富感情怎么样”的报告。</li>
            <li>查看阶段导航：直接生成该用户的阶段导航报告。</li>
            <li>填入资料：把资料带到录入页，继续手动调整。</li>
          </ul>
        </aside>
      </section>

      <section class="userGrid">
        <article v-for="profile in profiles" :key="profile.key" class="userCard">
          <div class="cardTop">
            <div>
              <div class="panelEyebrow">Test Profile</div>
              <h2 class="cardTitle">
                {{ profile.name }}
                <span>{{ profile.gender }}</span>
              </h2>
              <p class="cardSummary">{{ profile.note }}</p>
            </div>
            <span class="statusBadge">测试用户</span>
          </div>

          <div class="metaGrid">
            <div class="metaCard">
              <span>出生时间</span>
              <strong>{{ profile.birthTimeLabel }}</strong>
            </div>
            <div class="metaCard">
              <span>出生地点</span>
              <strong>{{ profile.birthPlace }}</strong>
            </div>
            <div class="metaCard">
              <span>经纬度</span>
              <strong>{{ profile.longitudeLabel }} / {{ profile.latitudeLabel }}</strong>
            </div>
            <div class="metaCard">
              <span>时区</span>
              <strong>{{ profile.timezoneLabel }}</strong>
            </div>
          </div>

          <div class="tagRow">
            <span v-for="tag in profile.tags" :key="tag" class="tag">{{ tag }}</span>
          </div>

          <div v-if="profile.lifeTrack?.length" class="trackBlock">
            <div class="panelEyebrow">Life Track</div>
            <ul class="trackList">
              <li v-for="item in profile.lifeTrack" :key="item">{{ item }}</li>
            </ul>
          </div>

          <div class="actionRow">
            <el-button type="primary" round @click="openReport(profile.key, 'natal_blueprint')">
              本命蓝图
            </el-button>
            <el-button round @click="openReport(profile.key, 'phase_navigation')">
              阶段导航
            </el-button>
            <el-button text @click="openAnalysis(profile.key)">填入资料</el-button>
          </div>
        </article>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from "vue-router";
import { TEST_USER_PROFILES } from "@/config/testProfiles";

const router = useRouter();
const profiles = TEST_USER_PROFILES;

function openReport(profile: string, analysis: "natal_blueprint" | "phase_navigation") {
  router.push({
    name: "report",
    query: {
      profile,
      analysis,
    },
  });
}

function openAnalysis(profile: string) {
  router.push({
    name: "analysis",
    params: { type: "natal_blueprint" },
    query: { profile },
  });
}
</script>

<style scoped lang="less">
.page {
  position: relative;
  min-height: calc(100vh - var(--h-footer));
  padding: 40px 20px 80px;
  background:
    radial-gradient(circle at 12% 12%, rgba(212, 175, 55, 0.08), transparent 24%),
    radial-gradient(circle at 88% 18%, rgba(42, 167, 184, 0.1), transparent 22%),
    linear-gradient(180deg, #020617 0%, #07111f 100%);
}

.backdrop {
  position: absolute;
  inset: 0;
  background:
    linear-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px);
  background-size: 42px 42px;
  mask-image: linear-gradient(180deg, rgba(0, 0, 0, 0.28), transparent 90%);
  pointer-events: none;
}

.wrap {
  position: relative;
  z-index: 1;
}

.hero,
.userGrid {
  display: grid;
  gap: 22px;
}

.hero {
  grid-template-columns: minmax(0, 1.2fr) minmax(320px, 0.8fr);
  margin-bottom: 22px;
}

.heroMain,
.heroAside,
.userCard,
.metaCard {
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(15, 23, 42, 0.74);
  backdrop-filter: blur(18px);
  border-radius: 28px;
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.24);
}

.heroMain,
.heroAside,
.userCard {
  padding: 28px;
}

.eyebrow,
.panelEyebrow {
  font-size: 12px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--gold);
}

.title {
  margin: 12px 0 0;
  color: var(--text);
  font-size: 44px;
  line-height: 1.04;
  letter-spacing: -0.04em;
}

.summary,
.cardSummary,
.list,
.list li {
  color: var(--text-secondary);
  line-height: 1.8;
}

.summary {
  margin: 16px 0 0;
}

.panelTitle {
  margin: 10px 0 0;
  color: var(--text);
  font-size: 24px;
  line-height: 1.25;
}

.list {
  margin: 16px 0 0;
  padding-left: 18px;
}

.userGrid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.cardTop {
  display: flex;
  justify-content: space-between;
  gap: 18px;
  align-items: flex-start;
}

.cardTitle {
  margin: 10px 0 0;
  color: var(--text);
  font-size: 28px;
  line-height: 1.2;
}

.cardTitle span {
  margin-left: 10px;
  color: var(--text-secondary);
  font-size: 15px;
  font-weight: 500;
}

.cardSummary {
  margin: 12px 0 0;
}

.statusBadge,
.tag {
  display: inline-flex;
  align-items: center;
  padding: 7px 12px;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.04);
  color: var(--text-secondary);
  font-size: 12px;
}

.statusBadge {
  white-space: nowrap;
}

.metaGrid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
  margin-top: 18px;
}

.metaCard {
  padding: 16px;
}

.metaCard span {
  display: block;
  color: var(--text-secondary);
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.metaCard strong {
  display: block;
  margin-top: 10px;
  color: var(--text);
  font-size: 16px;
  line-height: 1.6;
}

.tagRow {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 18px;
}

.trackBlock {
  margin-top: 20px;
  padding-top: 18px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.trackList {
  margin: 14px 0 0;
  padding: 0;
  list-style: none;
  display: grid;
  gap: 10px;
}

.trackList li {
  position: relative;
  padding-left: 18px;
  color: var(--text-secondary);
  line-height: 1.75;
}

.trackList li::before {
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

.actionRow {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  margin-top: 22px;
}

@media (max-width: 1100px) {
  .hero,
  .userGrid,
  .metaGrid {
    grid-template-columns: 1fr;
  }

  .cardTop {
    flex-direction: column;
  }
}

@media (max-width: 720px) {
  .page {
    padding-inline: 14px;
  }

  .heroMain,
  .heroAside,
  .userCard {
    padding: 22px;
  }

  .title {
    font-size: 34px;
  }
}
</style>
