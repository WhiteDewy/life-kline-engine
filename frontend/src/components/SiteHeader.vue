<template>
  <header class="siteHeader">
    <div class="content">
      <button class="brandBlock" type="button" @click="goHome">
        <div class="topLine">
          <img class="logo" src="/icon.svg" alt="占星人生" />
          <span class="name">占星人生</span>
        </div>
        <span class="sub">Astrology Life Map</span>
      </button>

      <nav class="nav">
        <button class="navLink" type="button" @click="$emit('history')" v-if="loggedIn">
          我的报告
        </button>
        <button class="navLink navPremium" type="button" v-if="loggedIn">
          ✦ 升级会员
        </button>
        <button class="navLink" type="button" @click="$emit('login')" v-if="!loggedIn">
          登录
        </button>
        <span class="navLink userTag" v-if="loggedIn && userPhone">
          {{ displayName }}
        </span>
        <el-button type="primary" round class="navAction" @click="goExplore">
          开始探索
        </el-button>
      </nav>
    </div>
  </header>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRouter } from "vue-router";

const props = defineProps<{
  loggedIn?: boolean;
  userPhone?: string;
}>();

const displayName = computed(() => {
  if (!props.userPhone) return "";
  return props.userPhone.replace(/(\d{3})\d{4}(\d{4})/, "$1****$2");
});

const router = useRouter();

function goHome() {
  router.push({ name: "entry" });
}

function goExplore() {
  router.push({ name: "analysis", params: { type: "natal_blueprint" } });
}
</script>

<style scoped lang="less">
.siteHeader {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1000;
  height: var(--h-header);
  background: rgba(2, 6, 23, 0.7);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(0,0,0,0.06);
}

.content {
  height: 100%;
  max-width: var(--page-shell-max);
  margin: 0 auto;
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
}

.brandBlock {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 4px;
  min-width: 0;
  padding: 0;
  border: 0;
  background: transparent;
  cursor: pointer;
}

.topLine {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.logo {
  width: 28px;
  height: 28px;
  display: block;
  flex: 0 0 auto;
  opacity: 0.9;
}

.name {
  color: var(--text);
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 0.12em;
}

.sub {
  color: var(--text-secondary);
  font-size: 11px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

.nav {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.navLink {
  padding: 8px 12px;
  border: 0;
  background: transparent;
  color: var(--text-secondary);
  font-size: 14px;
  cursor: pointer;
  transition: color 0.2s ease;
}

.navLink:hover {
  color: var(--gold);
}
.navPremium {
  color: #ff9a8b;
  font-weight: 600;
}

.navAction {
  font-weight: 600;
}

@media (max-width: 720px) {
  .content {
    padding: 0 14px;
  }

  .name {
    letter-spacing: 0.06em;
  }

  .sub {
    display: none;
  }
}
</style>
