<template>
  <div class="constellation-stories">
    <div class="stories-card">
      <button class="back-btn" @click="router.back()">← 返回</button>
      <div class="header">
        <span class="emoji">{{ signEmoji }}</span>
        <h1>{{ signName }} · 神话故事</h1>
      </div>
      <p class="placeholder-note">
        12 星座神话故事内容正在筹备中……<br />
        <small>这是一个新模块的占位页面，先打通路由跳转流程。</small>
      </p>
      <div v-if="signKey" class="meta">
        <span>当前星座：{{ signKey }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";

const route = useRoute();
const router = useRouter();

const signKey = computed(() => (route.query.sign as string) || "");

// 临时映射（占位用）
const SIGN_INFO: Record<string, { name: string; emoji: string }> = {
  aries: { name: "白羊座", emoji: "♈" },
  taurus: { name: "金牛座", emoji: "♉" },
  gemini: { name: "双子座", emoji: "♊" },
  cancer: { name: "巨蟹座", emoji: "♋" },
  leo: { name: "狮子座", emoji: "♌" },
  virgo: { name: "处女座", emoji: "♍" },
  libra: { name: "天秤座", emoji: "♎" },
  scorpio: { name: "天蝎座", emoji: "♏" },
  sagittarius: { name: "射手座", emoji: "♐" },
  capricorn: { name: "摩羯座", emoji: "♑" },
  aquarius: { name: "水瓶座", emoji: "♒" },
  pisces: { name: "双鱼座", emoji: "♓" },
};

const signName = computed(() => SIGN_INFO[signKey.value]?.name || "星座");
const signEmoji = computed(() => SIGN_INFO[signKey.value]?.emoji || "✨");
</script>

<style scoped>
.constellation-stories {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: linear-gradient(160deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
}
.stories-card {
  max-width: 480px;
  width: 100%;
  padding: 32px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(20px);
  color: #fff;
  position: relative;
}
.back-btn {
  position: absolute;
  top: 16px;
  left: 16px;
  background: none;
  border: none;
  color: #fff;
  font-size: 14px;
  cursor: pointer;
  opacity: 0.7;
}
.back-btn:hover {
  opacity: 1;
}
.header {
  text-align: center;
  margin-bottom: 24px;
}
.emoji {
  font-size: 64px;
  display: block;
  margin-bottom: 8px;
}
h1 {
  margin: 0;
  font-size: 24px;
  font-weight: 500;
}
.placeholder-note {
  text-align: center;
  line-height: 1.8;
  opacity: 0.8;
  font-size: 15px;
}
.placeholder-note small {
  opacity: 0.6;
}
.meta {
  text-align: center;
  margin-top: 24px;
  opacity: 0.5;
  font-size: 12px;
}
</style>
