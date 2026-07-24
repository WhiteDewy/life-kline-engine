<template>
  <div class="profile-page">
    <canvas ref="particleCanvas" class="particle-canvas"></canvas>
    <div class="glow glow--a"></div>
    <div class="glow glow--b"></div>

    <!-- ═══ 顶部 ═══ -->
    <div class="pp-header">
      <button class="back-btn" @click="goBack">← 返回</button>
      <h1 class="pp-title">编辑档案</h1>
      <button class="save-btn" :disabled="!saveDirty || saving" @click="doSave">
        {{ saving ? '保存中...' : '保存' }}
      </button>
    </div>

    <!-- ═══ 加载态 ═══ -->
    <div v-if="loading" class="loading-wrap">
      <div class="state-spinner">
        <span v-for="i in 10" :key="i" class="spinner-dot" :style="{ animationDelay: i * 0.1 + 's', background: '#f0b8a0' }"></span>
      </div>
      <p class="loading-text">加载档案中...</p>
    </div>

    <!-- ═══ 表单 ═══ -->
    <div v-else class="pp-form">
      <!-- 昵称 -->
      <div class="form-section">
        <div class="fs-label">昵称</div>
        <div class="glass-inp">
          <input v-model="form.name" class="g-inp" maxlength="12" placeholder="输入昵称" @input="markDirty" />
        </div>
      </div>

      <!-- 性别 -->
      <div class="form-section">
        <div class="fs-label">性别</div>
        <div class="gender-row">
          <button class="g-card" :class="{ on: form.gender === '女' }" @click="form.gender = '女'; markDirty()">
            <div class="g-orb g-orb--yin"><span>♀</span></div>
            <span class="g-label">女性</span>
          </button>
          <button class="g-card" :class="{ on: form.gender === '男' }" @click="form.gender = '男'; markDirty()">
            <div class="g-orb g-orb--yang"><span>♂</span></div>
            <span class="g-label">男性</span>
          </button>
        </div>
      </div>

      <!-- 出生日期 -->
      <div class="form-section">
        <div class="fs-label">出生日期</div>
        <el-date-picker v-model="form.birthDate" type="date" placeholder="选择日期" format="YYYY / MM / DD" value-format="YYYY-MM-DD" class="f-picker heal-popper" @change="markDirty" />
      </div>

      <!-- 出生时间 -->
      <div class="form-section">
        <div class="fs-label">出生时间</div>
        <el-time-picker v-model="form.birthTime" placeholder="选择时间" format="HH:mm" value-format="HH:mm" class="f-picker heal-popper" @change="markDirty" />
      </div>

      <!-- 出生地点 -->
      <div class="form-section">
        <div class="fs-label">出生地点</div>
        <div class="glass-inp">
          <input v-model="form.birthPlace" class="g-inp" placeholder="城市名，如 北京" @input="markDirty" />
        </div>
      </div>

      <!-- 夏令时 -->
      <div class="form-section">
        <div class="fs-label">夏令时</div>
        <div class="toggle-row dls-row">
          <button class="dls-btn" :class="{ on: form.daylightSaving }" @click="form.daylightSaving = !form.daylightSaving; markDirty()">
            <span>☀️ {{ form.daylightSaving ? '已开启' : '未开启' }}</span>
            <span class="dls-hint">1986-1991年间出生请注意</span>
          </button>
        </div>
      </div>

      <!-- 宫位制 -->
      <div class="form-section">
        <div class="fs-label">宫位制</div>
        <div class="glass-inp house-select-row">
          <button v-for="hs in houseSystemOptions" :key="hs.value" class="hs-chip" :class="{ on: form.houseSystem === hs.value }" @click="form.houseSystem = hs.value; markDirty(); refreshChart()">{{ hs.label }}</button>
        </div>
      </div>

      <!-- ═══ 星盘预览 ═══ -->
      <div class="form-section" v-if="chartData">
        <div class="fs-label">星盘预览</div>
        <div class="chart-preview">
          <div class="cp-row">
            <span class="cp-key">上升</span>
            <span class="cp-val">{{ chartData.ascendant?.sign_label || '-' }}</span>
          </div>
          <div class="cp-grid">
            <div v-for="p in chartPlanets" :key="p.key" class="cp-cell">
              <span class="cp-sym" :style="{ color: p.color }">{{ p.symbol }}</span>
              <span class="cp-sign">{{ p.signLabel || '?' }}</span>
              <span class="cp-name">{{ p.name }}</span>
            </div>
          </div>
          <div class="cp-houses" v-if="chartData.houses">
            <div class="cp-h-label">宫位表</div>
            <div class="cp-h-grid">
              <div v-for="(h, i) in chartData.houses" :key="i" class="cp-h-cell">
                <span class="h-num">{{ Number(i) + 1 }}</span>
                <span class="h-sign">{{ h.sign_label || h.sign || '?' }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive, onMounted, onBeforeUnmount } from "vue";
import { useRouter } from "vue-router";
import { useAuth } from "@/utils/auth";
import { apiClient } from "@/config/api";

const router = useRouter();
const { profiles, loadMe } = useAuth();

const loading = ref(true);
const saving = ref(false);
const saveDirty = ref(false);

const form = reactive({
  name: "",
  gender: "",
  birthDate: null as string | null,
  birthTime: null as string | null,
  birthPlace: "",
  daylightSaving: false,
  houseSystem: "B",
});

const houseSystemOptions = [
  { value: "B", label: "阿卡比特" },
  { value: "P", label: "普拉西度" },
  { value: "W", label: "整宫制" },
  { value: "K", label: "柯赫" },
];

const chartData = ref<any>(null);

function markDirty() { saveDirty.value = true; }

function goBack() { router.back(); }

const PLANETS = [
  { key: "SUN", symbol: "☉", name: "太阳", color: "#E8A840" },
  { key: "MOON", symbol: "☽", name: "月亮", color: "#B0C4D0" },
  { key: "MERCURY", symbol: "☿", name: "水星", color: "#90A878" },
  { key: "VENUS", symbol: "♀", name: "金星", color: "#D898A8" },
  { key: "MARS", symbol: "♂", name: "火星", color: "#D07050" },
  { key: "JUPITER", symbol: "♃", name: "木星", color: "#7888B0" },
  { key: "SATURN", symbol: "♄", name: "土星", color: "#889098" },
  { key: "URANUS", symbol: "♅", name: "天王星", color: "#68B0B0" },
  { key: "NEPTUNE", symbol: "♆", name: "海王星", color: "#6878B0" },
  { key: "PLUTO", symbol: "♇", name: "冥王星", color: "#987898" },
];

const chartPlanets = computed(() => {
  const planets = chartData.value?.natal_chart?.planets || {};
  return PLANETS.map((p) => ({
    ...p,
    signLabel: planets[p.key]?.sign_label || "",
  }));
});

// ── 加载现有档案 ──
async function loadProfile() {
  loading.value = true;
  await loadMe();
  const p = profiles.value?.[0];
  if (p) {
    form.name = p.name || "";
    form.gender = p.gender || "";
    if (p.birth_time) {
      const dt = p.birth_time.split("T");
      form.birthDate = dt[0] || null;
      form.birthTime = dt[1]?.slice(0, 5) || null;
    }
    form.birthPlace = p.birth_place || "";
    form.daylightSaving = !!p.daylight_saving;
    form.houseSystem = p.house_system || "B";
    saveDirty.value = false;
  }
  loading.value = false;
  await refreshChart();
}

// ── 刷新星盘预览 ──
async function refreshChart() {
  try {
    const res = await apiClient.get("/users/chart", {
      params: { house_system: form.houseSystem },
    });
    if (res.data?.status === "success") {
      chartData.value = res.data.data;
    } else if (res.data?.data) {
      chartData.value = res.data.data;
    }
  } catch {
    // 静默
  }
}

// ── 保存 ──
const profileId = computed(() => profiles.value?.[0]?.id || profiles.value?.[0]?.profile_id || "");

async function doSave() {
  if (!profileId.value || saving.value) return;
  saving.value = true;
  try {
    const birthTime = form.birthDate && form.birthTime ? `${form.birthDate}T${form.birthTime}:00` : undefined;
    await apiClient.put(`/profiles/${profileId.value}`, {
      name: form.name,
      gender: form.gender,
      birth_time: birthTime,
      birth_place: form.birthPlace,
      daylight_saving: form.daylightSaving,
      house_system: form.houseSystem,
    });
    saveDirty.value = false;
    const { toast } = await import("@/utils/toast");
    toast.success("档案已保存");
  } catch {
    const { toast } = await import("@/utils/toast");
    toast.error("保存失败，请重试");
  } finally {
    saving.value = false;
  }
}

// ── 背景粒子 ──
const particleCanvas = ref<HTMLCanvasElement | null>(null);
let animId = 0;
onMounted(() => { loadProfile(); initCanvas(); });
function initCanvas() {
  const c = particleCanvas.value; if (!c) return; const ctx = c.getContext("2d"); if (!ctx) return;
  const dpr = window.devicePixelRatio || 1;
  function resize() { c!.width = window.innerWidth * dpr; c!.height = window.innerHeight * dpr; c!.style.width = window.innerWidth + "px"; c!.style.height = window.innerHeight + "px"; }
  resize(); window.addEventListener("resize", resize);
  const motes: { x: number; y: number; r: number; vx: number; vy: number; a: number; ph: number }[] = [];
  for (let i = 0; i < 35; i++) motes.push({ x: Math.random() * window.innerWidth * dpr, y: Math.random() * window.innerHeight * dpr, r: 1 + Math.random() * 3, vx: (Math.random() - 0.5) * 0.25, vy: -0.15 - Math.random() * 0.35, a: 0.15 + Math.random() * 0.45, ph: Math.random() * Math.PI * 2 });
  function draw() { ctx!.clearRect(0, 0, c!.width, c!.height); const t = Date.now(); for (const m of motes) { m.x += m.vx; m.y += m.vy; if (m.y < -20) { m.y = c!.height + 20; m.x = Math.random() * c!.width; } if (m.x < -20) m.x = c!.width + 20; if (m.x > c!.width + 20) m.x = -20; const alpha = m.a * (0.5 + 0.5 * Math.sin(t * 0.0008 + m.ph)); ctx!.beginPath(); ctx!.arc(m.x, m.y, m.r, 0, Math.PI * 2); ctx!.fillStyle = `rgba(255,215,190,${alpha.toFixed(2)})`; ctx!.fill(); if (m.r > 2) { ctx!.beginPath(); ctx!.arc(m.x, m.y, m.r * 4, 0, Math.PI * 2); ctx!.fillStyle = `rgba(255,195,165,${(alpha * 0.1).toFixed(3)})`; ctx!.fill(); } } animId = requestAnimationFrame(draw); }
  draw(); onBeforeUnmount(() => { cancelAnimationFrame(animId); window.removeEventListener("resize", resize); });
}
</script>

<style scoped>
/* ═══ 基底 ═══ */
.profile-page { min-height: 100vh; position: relative; background: linear-gradient(175deg, #FFF5EE 0%, #FFEFE6 25%, #FFF0F5 55%, #F5F0FF 80%, #FDF5F0 100%); overflow-y: auto; padding: 0 0 40px; }
.particle-canvas { position: fixed; inset: 0; z-index: 0; pointer-events: none; }
.glow { position: fixed; border-radius: 50%; pointer-events: none; z-index: 0; }
.glow--a { width: 380px; height: 380px; top: 5%; right: -140px; background: radial-gradient(circle, rgba(255,200,170,0.14) 0%, transparent 65%); animation: gd 8s ease-in-out infinite; }
.glow--b { width: 340px; height: 340px; bottom: -80px; left: -100px; background: radial-gradient(circle, rgba(220,190,230,0.1) 0%, transparent 65%); animation: gd 10s ease-in-out infinite reverse; }
@keyframes gd { 0%,100%{transform:translate(0,0) scale(1)} 50%{transform:translate(12px,-12px) scale(1.08)} }

/* ═══ 顶部栏 ═══ */
.pp-header { position: sticky; top: 0; z-index: 10; display: flex; align-items: center; justify-content: space-between; padding: 16px 20px; padding-top: calc(16px + env(safe-area-inset-top, 0px)); background: rgba(255,255,255,0.7); backdrop-filter: blur(16px); }
.pp-title { font-size: 17px; font-weight: 600; color: #4a3728; margin: 0; letter-spacing: 1px; }
.back-btn { padding: 6px 14px; border-radius: 14px; border: 1px solid rgba(0,0,0,0.06); background: rgba(255,255,255,0.6); color: #8b7355; font-size: 13px; cursor: pointer; font-family: inherit; transition: all 0.2s; }
.back-btn:hover { background: rgba(255,255,255,0.8); color: #4a3728; }
.save-btn { padding: 8px 20px; border-radius: 16px; border: none; background: linear-gradient(135deg, #f0b8a0, #e8a890); color: #fff; font-size: 13px; font-weight: 600; cursor: pointer; font-family: inherit; letter-spacing: 1px; transition: all 0.3s; }
.save-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.save-btn:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 4px 16px rgba(220,150,120,0.2); }

/* ═══ 加载 ═══ */
.loading-wrap { position: relative; z-index: 1; display: flex; flex-direction: column; align-items: center; padding: 80px 20px; gap: 16px; }
.loading-text { font-size: 13px; color: #b8a090; letter-spacing: 1px; }
.state-spinner { display: flex; gap: 8px; }
.spinner-dot { width: 8px; height: 8px; border-radius: 50%; animation: db 1.2s ease-in-out infinite; }
@keyframes db { 0%,100%{transform:translateY(0);opacity:0.4} 50%{transform:translateY(-12px);opacity:1} }

/* ═══ 表单 ═══ */
.pp-form { position: relative; z-index: 1; max-width: 420px; margin: 0 auto; padding: 20px 24px; display: flex; flex-direction: column; gap: 18px; }
.form-section { display: flex; flex-direction: column; gap: 6px; }
.fs-label { font-size: 11px; font-weight: 500; color: #b8a090; letter-spacing: 2px; text-transform: uppercase; }
.glass-inp { display: flex; align-items: center; padding: 2px; border-radius: 18px; background: rgba(255,255,255,0.55); border: 1px solid rgba(0,0,0,0.04); backdrop-filter: blur(16px); transition: all 0.35s; }
.glass-inp:focus-within { border-color: rgba(255,160,130,0.3); box-shadow: 0 0 0 5px rgba(255,180,150,0.07); background: rgba(255,255,255,0.7); }
.g-inp { flex: 1; border: none; background: transparent; padding: 14px 16px; font-size: 15px; color: #4a3028; outline: none; font-family: inherit; letter-spacing: 1.5px; }
.g-inp::placeholder { color: #c4b0a5; letter-spacing: 1px; }

/* ═══ 性别 ═══ */
.gender-row { display: flex; gap: 12px; }
.g-card { flex: 1; display: flex; align-items: center; gap: 10px; padding: 14px 16px; border-radius: 18px; border: 1.5px solid rgba(0,0,0,0.04); background: rgba(255,255,255,0.45); cursor: pointer; font-family: inherit; backdrop-filter: blur(12px); transition: all 0.35s; }
.g-card:hover { border-color: rgba(255,160,130,0.2); background: rgba(255,255,255,0.6); }
.g-card.on { border-color: rgba(240,170,140,0.4); background: rgba(255,240,230,0.5); }
.g-orb { width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.g-orb span { font-size: 16px; }
.g-orb--yin { background: radial-gradient(circle at 35% 30%, rgba(220,190,210,0.4), rgba(180,150,180,0.15)); }
.g-orb--yang { background: radial-gradient(circle at 35% 30%, rgba(240,200,160,0.4), rgba(200,160,120,0.15)); }
.g-label { font-size: 14px; font-weight: 600; color: #4a3028; letter-spacing: 1px; }

/* ═══ 选单样式继承 ═══ */
:deep(.f-picker .el-input__wrapper) { background: rgba(255,255,255,0.55) !important; border: 1px solid rgba(0,0,0,0.04) !important; border-radius: 18px !important; box-shadow: none !important; padding: 14px 16px !important; backdrop-filter: blur(16px) !important; }
:deep(.f-picker .el-input__inner) { color: #4a3028 !important; font-family: inherit !important; letter-spacing: 1.5px !important; }
:deep(.f-picker .el-input__inner::placeholder) { color: #c4b0a5 !important; }
:deep(.heal-popper) { background: rgba(255,255,255,0.95) !important; backdrop-filter: blur(24px) !important; border: 1px solid rgba(0,0,0,0.04) !important; box-shadow: 0 16px 48px rgba(0,0,0,0.06) !important; color: #4a3028 !important; border-radius: 18px !important; }

/* ═══ 夏令时 ═══ */
.toggle-row { width: 100%; }
.dls-row { flex-direction: column; padding: 8px 12px; gap: 2px; border-radius: 14px; border: 1px solid rgba(0,0,0,0.04); background: rgba(255,255,255,0.4); }
.dls-btn { width: 100%; display: flex; align-items: center; justify-content: space-between; border: none; background: transparent; font-size: 13px; font-weight: 500; color: #b8a090; cursor: pointer; font-family: inherit; letter-spacing: 1px; padding: 6px 4px; border-radius: 12px; transition: all 0.3s; }
.dls-btn.on { background: rgba(240,170,140,0.12); color: #5c3d3a; }
.dls-hint { font-size: 11px; opacity: 0.6; }

/* ═══ 宫位制 ═══ */
.house-select-row { display: flex; gap: 6px; padding: 6px 8px; flex-wrap: wrap; justify-content: center; }
.hs-chip { padding: 8px 14px; border-radius: 14px; border: 1px solid rgba(0,0,0,0.04); background: rgba(255,255,255,0.5); color: #8b6f5f; font-size: 12px; cursor: pointer; font-family: inherit; letter-spacing: 1px; transition: all 0.3s; flex: 1; min-width: 68px; }
.hs-chip:hover { border-color: rgba(255,160,130,0.25); color: #4a3028; background: rgba(255,255,255,0.7); }
.hs-chip.on { background: rgba(240,170,140,0.12); border-color: rgba(240,170,140,0.25); color: #5c3d3a; font-weight: 600; }

/* ═══ 星盘预览 ═══ */
.chart-preview { background: rgba(255,255,255,0.5); border: 1px solid rgba(0,0,0,0.04); border-radius: 20px; padding: 18px 16px; backdrop-filter: blur(12px); display: flex; flex-direction: column; gap: 14px; }
.cp-row { display: flex; justify-content: center; align-items: center; gap: 8px; padding: 8px 0; }
.cp-key { font-size: 11px; color: #b8a090; letter-spacing: 2px; }
.cp-val { font-size: 16px; font-weight: 600; color: #4a3028; letter-spacing: 2px; }
.cp-grid { display: flex; flex-wrap: wrap; justify-content: center; gap: 8px; }
.cp-cell { display: flex; flex-direction: column; align-items: center; gap: 2px; width: 48px; padding: 8px 4px; border-radius: 12px; background: rgba(255,255,255,0.5); }
.cp-sym { font-size: 16px; }
.cp-sign { font-size: 9px; color: #b8a090; }
.cp-name { font-size: 9px; color: #c4b0a5; }
.cp-houses { border-top: 1px solid rgba(0,0,0,0.04); padding-top: 12px; }
.cp-h-label { font-size: 11px; color: #b8a090; letter-spacing: 2px; margin-bottom: 8px; text-align: center; }
.cp-h-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 4px; }
.cp-h-cell { display: flex; flex-direction: column; align-items: center; padding: 6px 4px; border-radius: 10px; background: rgba(255,255,255,0.4); }
.h-num { font-size: 10px; color: #b8a090; font-weight: 500; }
.h-sign { font-size: 11px; color: #4a3728; font-weight: 500; }
</style>
