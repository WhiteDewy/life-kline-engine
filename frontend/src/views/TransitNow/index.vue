<template>
  <div class="transit-page">
    <header class="transit-header">
      <button class="back-btn" @click="goBack">← 返回</button>
      <h1 class="transit-title">🌌 此刻星象</h1>
      <span class="transit-refresh" @click="load" title="刷新">🔄</span>
    </header>

    <div class="loading" v-if="loading">
      <div class="loading-spinner">
        <span v-for="i in 6" :key="i" class="dot" :style="{ animationDelay: i * 0.12 + 's' }"></span>
      </div>
      <p>正在连接宇宙...</p>
    </div>

    <div class="error" v-else-if="error">{{ error }}</div>

    <div class="error" v-else-if="!payload">
      <p>暂无可用星象数据，请稍后刷新。</p>
      <button class="retry-btn" @click="load">重新加载</button>
    </div>

    <template v-else>
      <!-- 时间戳 -->
      <p class="update-time">数据更新于 {{ formatTime(payload.timestamp) }}</p>

      <!-- 行星网格 -->
      <div class="planets-grid">
        <div
          v-for="item in planetList"
          :key="item.planet"
          class="planet-card"
          :class="{ 'planet-card--retrograde': item.retrograde }"
          :style="{ '--pc': item.color }"
        >
          <div class="pc-symbol">{{ item.symbol }}</div>
          <div class="pc-name">{{ item.zh }}</div>
          <div class="pc-sign">
            {{ item.signLabel }}
            <span v-if="item.retrograde" class="retrograde-tag">逆行</span>
          </div>
          <div class="pc-degree">{{ item.formattedDegree }}</div>
        </div>
      </div>

      <!-- 当下宇宙提示 -->
      <div class="cosmos-note" v-if="cosmosNote">
        <p class="cosmos-note__text">{{ cosmosNote }}</p>
      </div>

      <!-- 行运解读（如果有） -->
      <div class="interpretation" v-if="payload.interpretation">
        <h2 class="section-title">🌟 今日宇宙能量提示</h2>
        <p class="interpretation-text">{{ payload.interpretation }}</p>
      </div>

      <!-- 行星相位关系 -->
      <div class="aspects-section" v-if="activeAspects.length">
        <h2 class="section-title">⚡ 活跃相位</h2>
        <div class="aspect-list">
          <div v-for="a in activeAspects" :key="a.key" class="aspect-item">
            <span class="aspect-planets">{{ a.label }}</span>
            <span class="aspect-type" :class="`aspect-type--${a.nature}`">{{ a.typeLabel }}</span>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import { apiClient } from "@/config/api";

const router = useRouter();
const loading = ref(true);
const error = ref("");
const payload = ref<any>(null);

const PLANET_META: Record<string, { zh: string; symbol: string; color: string }> = {
  SUN:     { zh: "太阳", symbol: "☉",  color: "#F2A900" },
  MOON:    { zh: "月亮", symbol: "☽",  color: "#C4B87A" },
  MERCURY: { zh: "水星", symbol: "☿",  color: "#A8A8A8" },
  VENUS:   { zh: "金星", symbol: "♀",  color: "#E8A0BF" },
  MARS:    { zh: "火星", symbol: "♂",  color: "#E85D5D" },
  JUPITER: { zh: "木星", symbol: "♃",  color: "#6EB3E8" },
  SATURN:  { zh: "土星", symbol: "♄",  color: "#C4A882" },
  URANUS:  { zh: "天王星", symbol: "♅", color: "#5DC8A8" },
  NEPTUNE: { zh: "海王星", symbol: "♆", color: "#7B9EDB" },
  PLUTO:   { zh: "冥王星", symbol: "♇", color: "#8B7BA8" },
};

const ZODIAC_EMOJI: Record<string, string> = {
  ARIES: "♈", TAURUS: "♉", GEMINI: "♊", CANCER: "♋",
  LEO: "♌", VIRGO: "♍", LIBRA: "♎", SCORPIO: "♏",
  SAGITTARIUS: "♐", CAPRICORN: "♑", AQUARIUS: "♒", PISCES: "♓",
};

async function load() {
  loading.value = true;
  error.value = "";
  try {
    const res = await apiClient.get("/transit/now");
    if (res.data?.status === "success") {
      payload.value = res.data.data;
    } else {
      error.value = "数据格式异常";
    }
  } catch (e: any) {
    if (e?.response?.status === 503) {
      error.value = "星象服务暂时不可用，请稍后刷新";
    } else {
      error.value = e?.message || "加载失败";
    }
  } finally {
    loading.value = false;
  }
}

const planetList = computed(() => {
  if (!payload.value?.planets) return [];
  return Object.entries(payload.value.planets).map(([planet, data]: [string, any]) => {
    const meta = PLANET_META[planet] || { zh: planet, symbol: "✦", color: "#999" };
    const sign = data.sign || "";
    return {
      planet,
      zh: meta.zh,
      symbol: meta.symbol,
      color: meta.color,
      signLabel: sign ? `${ZODIAC_EMOJI[sign] || ""} ${sign.replace("_", " ")}` : "",
      retrograde: !!data.retrograde,
      formattedDegree: data.degree != null ? `${Math.floor(data.degree)}°` : "",
    };
  });
});

const activeAspects = computed(() => {
  if (!payload.value?.aspects) return [];
  return payload.value.aspects.map((a: any) => ({
    key: `${a.planet1}-${a.planet2}-${a.type}`,
    label: `${PLANET_META[a.planet1]?.zh || a.planet1} ${PLANET_META[a.planet2]?.zh || a.planet2}`,
    type: a.type,
    typeLabel: a.type_zh || a.type || "",
    nature: a.nature || "neutral",
  }));
});

const cosmosNote = computed(() => {
  const planets = planetList.value;
  if (!planets.length) return "";

  // 找出逆行行星
  const retrogrades = planets.filter(p => p.retrograde);
  if (retrogrades.length) {
    const names = retrogrades.map(r => r.zh).join("、");
    return `⚠️ ${names}当前处于逆行状态，适宜内省与回顾，而非外在行动。`;
  }

  // 快速行星（新月、满月等）提示可扩展
  return "✨ 宇宙此刻平静，适合安宁地观察自己的内在状态。";
});

function formatTime(ts: string | number): string {
  if (!ts) return "";
  const d = new Date(ts);
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,"0")}-${String(d.getDate()).padStart(2,"0")} ${String(d.getHours()).padStart(2,"0")}:${String(d.getMinutes()).padStart(2,"0")}`;
}

function goBack() { router.back(); }

onMounted(load);
</script>

<style scoped lang="less">
.transit-page {
  min-height: 100vh;
  background: #0a0a1a;
  padding: 0 16px 80px;
  font-family: -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif;
  color: #e0d8cc;
}

.transit-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 0 16px;
  position: sticky;
  top: 0;
  background: #0a0a1a;
  z-index: 10;
}

.back-btn {
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.1);
  color: #a89880;
  padding: 6px 14px;
  border-radius: 999px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}
.back-btn:hover { background: rgba(255,255,255,0.1); color: #e0d8cc; }

.transit-title {
  font-size: 18px;
  font-weight: 700;
  color: #e0d8cc;
  margin: 0;
  letter-spacing: 0.03em;
}

.transit-refresh {
  font-size: 18px;
  cursor: pointer;
  opacity: 0.6;
  transition: opacity 0.2s;
}
.transit-refresh:hover { opacity: 1; }

.loading {
  text-align: center;
  padding: 80px 0;
}
.loading-spinner {
  display: flex;
  justify-content: center;
  gap: 6px;
  margin-bottom: 16px;
}
.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #7B9EDB;
  animation: pulse 1.2s ease-in-out infinite;
}
@keyframes pulse {
  0%, 100% { transform: scale(0.8); opacity: 0.4; }
  50% { transform: scale(1.2); opacity: 1; }
}
.loading p { color: #8b7355; font-size: 14px; }

.error {
  text-align: center;
  padding: 60px 0;
  color: #e8a0a0;
  font-size: 14px;
}
.retry-btn {
  margin-top: 12px;
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.1);
  color: #a89880;
  padding: 8px 20px;
  border-radius: 999px;
  cursor: pointer;
  font-size: 13px;
}

.update-time {
  text-align: center;
  font-size: 12px;
  color: #5a5060;
  margin: 0 0 20px;
  letter-spacing: 0.05em;
}

.planets-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin-bottom: 24px;
}

.planet-card {
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 16px;
  padding: 16px 14px;
  text-align: center;
  position: relative;
  transition: all 0.2s;
}
.planet-card:hover { border-color: var(--pc); background: rgba(255,255,255,0.07); }
.planet-card--retrograde { opacity: 0.85; }

.pc-symbol {
  font-size: 28px;
  line-height: 1;
  margin-bottom: 6px;
  color: var(--pc);
}
.pc-name {
  font-size: 14px;
  font-weight: 700;
  color: #e0d8cc;
  margin-bottom: 4px;
}
.pc-sign {
  font-size: 12px;
  color: #8b7b6b;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  margin-bottom: 4px;
}
.retrograde-tag {
  font-size: 10px;
  background: rgba(232,90,90,0.2);
  color: #e85d5d;
  padding: 1px 6px;
  border-radius: 999px;
  border: 1px solid rgba(232,90,90,0.3);
}
.pc-degree {
  font-size: 11px;
  color: #6b6070;
  letter-spacing: 0.05em;
}

.cosmos-note {
  background: rgba(123,158,219,0.08);
  border: 1px solid rgba(123,158,219,0.15);
  border-radius: 14px;
  padding: 14px 18px;
  margin-bottom: 24px;
}
.cosmos-note__text {
  margin: 0;
  font-size: 13px;
  color: #a8b8d8;
  line-height: 1.6;
}

.section-title {
  font-size: 16px;
  font-weight: 700;
  color: #e0d8cc;
  margin: 0 0 14px;
  letter-spacing: 0.02em;
}

.interpretation {
  margin-bottom: 24px;
}
.interpretation-text {
  font-size: 14px;
  color: #b8a898;
  line-height: 1.8;
  margin: 0;
}

.aspects-section { margin-bottom: 24px; }
.aspect-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.aspect-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  background: rgba(255,255,255,0.03);
  border-radius: 10px;
  border: 1px solid rgba(255,255,255,0.05);
}
.aspect-planets { font-size: 13px; color: #c8b898; font-weight: 600; }
.aspect-type {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 10px;
  border-radius: 999px;
}
.aspect-type--supportive { background: rgba(110,179,231,0.15); color: #6eb3e8; }
.aspect-type--challenging { background: rgba(232,90,90,0.15); color: #e85d5d; }
.aspect-type--neutral { background: rgba(184,169,201,0.15); color: #b8a9c8; }
</style>
