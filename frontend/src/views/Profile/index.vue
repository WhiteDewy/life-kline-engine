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

    <!-- ═══ 加载失败 ═══ -->
    <div v-else-if="loadError" class="loading-wrap">
      <p class="error-emoji">😔</p>
      <p class="error-text">档案加载失败</p>
      <button class="retry-btn" @click="loadProfile">重新加载</button>
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
        <el-date-picker
          v-model="form.birthDate"
          type="date"
          placeholder="选择日期"
          format="YYYY / MM / DD"
          value-format="YYYY-MM-DD"
          class="f-picker"
          popper-class="heal-popper"
          @change="markDirty"
        />
      </div>

      <!-- 出生时间 -->
      <div class="form-section">
        <div class="fs-label">出生时间</div>
        <el-time-picker
          v-model="form.birthTime"
          placeholder="选择时间"
          format="HH:mm"
          value-format="HH:mm"
          class="f-picker"
          popper-class="heal-popper"
          @change="markDirty"
        />
      </div>

      <!-- 出生地点 -->
      <div class="form-section">
        <div class="fs-label">出生地点</div>
        <el-cascader
          v-model="birthRegionCodes"
          :options="regionData"
          :props="{ label: 'label', value: 'value', children: 'children' }"
          clearable filterable
          placeholder="省 / 市 / 区"
          class="f-cascader"
          popper-class="heal-cascader-popper"
          @change="onBirthRegionChange"
        />
        <div class="coord-bar">
          <span class="coord-text" v-if="birthCoordLabel">{{ birthCoordLabel }}</span>
          <span class="coord-text" v-else>选择地点后获取坐标，或手动填写</span>
          <button class="geo-btn" :disabled="geoLoading" @click="autoGeocode">
            {{ geoLoading ? '获取中...' : '获取坐标' }}
          </button>
        </div>

        <!-- 手动坐标入口 -->
        <details class="manual-coord" :open="showManualCoord">
          <summary class="manual-coord-summary" @click.prevent="showManualCoord = !showManualCoord">
            📐 手动填写经纬度（自动获取失败时使用）{{ showManualCoord ? '▲' : '▼' }}
          </summary>
          <div class="manual-grid">
            <div class="manual-field">
              <label>纬度</label>
              <div class="manual-row">
                <input type="number" v-model.number="manualBirthLat.deg" min="0" max="90" class="manual-num" @input="applyManualCoords" />
                <span>°</span>
                <input type="number" v-model.number="manualBirthLat.min" min="0" max="59" class="manual-num" @input="applyManualCoords" />
                <span>′</span>
                <select v-model="manualBirthLat.dir" class="manual-sel" @change="applyManualCoords">
                  <option>N</option><option>S</option>
                </select>
              </div>
            </div>
            <div class="manual-field">
              <label>经度</label>
              <div class="manual-row">
                <input type="number" v-model.number="manualBirthLon.deg" min="0" max="180" class="manual-num" @input="applyManualCoords" />
                <span>°</span>
                <input type="number" v-model.number="manualBirthLon.min" min="0" max="59" class="manual-num" @input="applyManualCoords" />
                <span>′</span>
                <select v-model="manualBirthLon.dir" class="manual-sel" @change="applyManualCoords">
                  <option>E</option><option>W</option>
                </select>
              </div>
            </div>
          </div>
        </details>
      </div>

      <!-- 现居地 -->
      <div class="form-section">
        <div class="fs-label">现居地</div>
        <el-cascader
          v-model="residenceRegionCodes"
          :options="regionData"
          :props="{ label: 'label', value: 'value', children: 'children' }"
          clearable filterable
          placeholder="省 / 市 / 区"
          class="f-cascader"
          popper-class="heal-cascader-popper"
          @change="onResidenceRegionChange"
        />
        <div class="coord-bar">
          <span class="coord-text" v-if="residenceCoordLabel">{{ residenceCoordLabel }}</span>
          <span class="coord-text" v-else>选择地点后手动获取坐标</span>
          <button class="geo-btn" :disabled="resGeoLoading" @click="autoResidenceGeocode">
            {{ resGeoLoading ? '获取中...' : '获取坐标' }}
          </button>
        </div>
      </div>

      <!-- 时区 -->
      <div class="form-section">
        <div class="fs-label">时区</div>
        <div class="tz-select-wrap">
          <select v-model.number="form.timezone" class="tz-select" @change="markDirty">
            <option v-for="tz in timezoneOptions" :key="tz.value" :value="tz.value">{{ tz.label }}</option>
          </select>
          <span class="tz-arrow">▼</span>
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
import { ElMessage } from "element-plus";
import { regionData, codeToText } from "element-china-area-data";
import { useAuth } from "@/utils/auth";
import { apiClient } from "@/config/api";
import { formatCoordinateLabel, splitCoordinateParts, composeCoordinateValue } from "@/utils/coordinates";
import { textToRegionCodes } from "@/utils/regions";

const router = useRouter();
const { profiles, loadMe } = useAuth();

const loading = ref(true);
const loadError = ref(false);
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
  timezone: 8,
});

const houseSystemOptions = [
  { value: "B", label: "阿卡比特" },
  { value: "P", label: "普拉西度" },
  { value: "W", label: "整宫制" },
  { value: "K", label: "柯赫" },
];

const timezoneOptions = [
  { value: -12, label: "GMT-12 · 贝克岛" },
  { value: -11, label: "GMT-11 · 美属萨摩亚、中途岛" },
  { value: -10, label: "GMT-10 · 夏威夷、檀香山" },
  { value: -9, label: "GMT-9 · 阿拉斯加" },
  { value: -8, label: "GMT-8 · 洛杉矶、温哥华（太平洋时间）" },
  { value: -7, label: "GMT-7 · 丹佛、卡尔加里（山地时间）" },
  { value: -6, label: "GMT-6 · 芝加哥、墨西哥城（中部时间）" },
  { value: -5, label: "GMT-5 · 纽约、多伦多（东部时间）" },
  { value: -4, label: "GMT-4 · 加拉加斯、哈利法克斯" },
  { value: -3, label: "GMT-3 · 布宜诺斯艾利斯、圣保罗" },
  { value: -2, label: "GMT-2 · 南乔治亚岛" },
  { value: -1, label: "GMT-1 · 亚速尔群岛" },
  { value: 0, label: "GMT+0 · 伦敦、都柏林（格林威治标准时间）" },
  { value: 1, label: "GMT+1 · 巴黎、柏林、罗马" },
  { value: 2, label: "GMT+2 · 雅典、开罗、耶路撒冷" },
  { value: 3, label: "GMT+3 · 莫斯科、内罗毕" },
  { value: 3.5, label: "GMT+3:30 · 德黑兰" },
  { value: 4, label: "GMT+4 · 迪拜、巴库" },
  { value: 4.5, label: "GMT+4:30 · 喀布尔" },
  { value: 5, label: "GMT+5 · 卡拉奇、塔什干" },
  { value: 5.5, label: "GMT+5:30 · 新德里、孟买" },
  { value: 5.75, label: "GMT+5:45 · 加德满都" },
  { value: 6, label: "GMT+6 · 达卡、阿拉木图" },
  { value: 6.5, label: "GMT+6:30 · 仰光" },
  { value: 7, label: "GMT+7 · 曼谷、雅加达" },
  { value: 8, label: "GMT+8 · 北京、上海、香港、新加坡、珀斯" },
  { value: 8.75, label: "GMT+8:45 · 尤克拉（澳大利亚）" },
  { value: 9, label: "GMT+9 · 东京、首尔" },
  { value: 9.5, label: "GMT+9:30 · 阿德莱德、达尔文" },
  { value: 10, label: "GMT+10 · 悉尼、墨尔本" },
  { value: 10.5, label: "GMT+10:30 · 豪勋爵岛" },
  { value: 11, label: "GMT+11 · 所罗门群岛" },
  { value: 12, label: "GMT+12 · 奥克兰、斐济" },
  { value: 12.75, label: "GMT+12:45 · 查塔姆群岛" },
  { value: 13, label: "GMT+13 · 汤加" },
  { value: 14, label: "GMT+14 · 莱恩群岛" },
];

const chartData = ref<any>(null);

// ── 出生地 cascader + 坐标 ──
const birthRegionCodes = ref<string[]>([]);
const birthLat = ref(0);
const birthLon = ref(0);
const geoLoading = ref(false);
const showManualCoord = ref(false);
const manualBirthLat = reactive({ deg: 0, min: 0, dir: "N" as "N" | "S" });
const manualBirthLon = reactive({ deg: 0, min: 0, dir: "E" as "E" | "W" });

// ── 现居地 cascader + 坐标 ──
const residenceRegionCodes = ref<string[]>([]);
const residencePlace = ref("");
const residenceLat = ref(0);
const residenceLon = ref(0);
const resGeoLoading = ref(false);

const birthCoordLabel = computed(() => {
  if (!birthLat.value && !birthLon.value) return "";
  return `${formatCoordinateLabel(birthLat.value, "latitude")} / ${formatCoordinateLabel(birthLon.value, "longitude")}`;
});
const residenceCoordLabel = computed(() => {
  if (!residenceLat.value && !residenceLon.value) return "";
  return `${formatCoordinateLabel(residenceLat.value, "latitude")} / ${formatCoordinateLabel(residenceLon.value, "longitude")}`;
});

function markDirty() { saveDirty.value = true; }

function goBack() { router.back(); }

// ── 地点 → cascader codes ──
function onBirthRegionChange(codes: string[]) {
  if (!codes?.length) { form.birthPlace = ""; markDirty(); return; }
  form.birthPlace = codes.map((c) => codeToText[c] || "").join(" ");
  markDirty();
}
function onResidenceRegionChange(codes: string[]) {
  if (!codes?.length) { residencePlace.value = ""; markDirty(); return; }
  residencePlace.value = codes.map((c) => codeToText[c] || "").join(" ");
  markDirty();
}

// ── geocode ──
async function autoGeocode() {
  if (!form.birthPlace) { ElMessage.warning("请先选择出生地点"); return; }
  geoLoading.value = true;
  try {
    const r = await apiClient.post("/geocode", { query: form.birthPlace });
    if (r.data?.status === "success" && r.data?.data) {
      birthLat.value = Number(r.data.data.lat);
      birthLon.value = Number(r.data.data.lon);
      syncManualFromForm();
      markDirty();
      ElMessage.success("坐标已获取");
    } else {
      ElMessage.warning("获取失败，请检查地点名称或手动填写");
    }
  } catch {
    ElMessage.warning("获取失败，请检查地点名称或手动填写");
  } finally {
    geoLoading.value = false;
  }
}

async function autoResidenceGeocode() {
  if (!residencePlace.value) { ElMessage.warning("请先选择现居地"); return; }
  resGeoLoading.value = true;
  try {
    const r = await apiClient.post("/geocode", { query: residencePlace.value });
    if (r.data?.status === "success" && r.data?.data) {
      residenceLat.value = Number(r.data.data.lat);
      residenceLon.value = Number(r.data.data.lon);
      markDirty();
      ElMessage.success("坐标已获取");
    } else {
      ElMessage.warning("获取失败，请检查地点名称");
    }
  } catch {
    ElMessage.warning("获取失败，请检查地点名称");
  } finally {
    resGeoLoading.value = false;
  }
}

// ── 手动坐标 ──
function syncManualFromForm() {
  const lat = splitCoordinateParts(birthLat.value, "latitude");
  const lon = splitCoordinateParts(birthLon.value, "longitude");
  manualBirthLat.deg = lat.degrees;
  manualBirthLat.min = lat.minutes;
  manualBirthLat.dir = lat.direction as "N" | "S";
  manualBirthLon.deg = lon.degrees;
  manualBirthLon.min = lon.minutes;
  manualBirthLon.dir = lon.direction as "E" | "W";
}

function applyManualCoords() {
  birthLat.value = composeCoordinateValue(manualBirthLat.deg, manualBirthLat.min, manualBirthLat.dir, "latitude");
  birthLon.value = composeCoordinateValue(manualBirthLon.deg, manualBirthLon.min, manualBirthLon.dir, "longitude");
  markDirty();
}

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
  loadError.value = false;
  try {
    await loadMe();
  } catch {
    loadError.value = true;
    loading.value = false;
    return;
  }

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
    form.timezone = p.timezone ?? 8;

    // 出生地坐标 + cascader 回显
    birthLat.value = p.lat || 0;
    birthLon.value = p.lon || 0;
    if (p.birth_place) {
      const codes = textToRegionCodes(p.birth_place);
      if (codes) birthRegionCodes.value = codes;
    }
    syncManualFromForm();
    if (!p.lat && !p.lon) showManualCoord.value = true;

    // 现居地 + cascader 回显
    residencePlace.value = p.residence_place || "";
    residenceLat.value = p.residence_lat || 0;
    residenceLon.value = p.residence_lon || 0;
    if (p.residence_place) {
      const codes = textToRegionCodes(p.residence_place);
      if (codes) residenceRegionCodes.value = codes;
    }

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
      lat: birthLat.value || undefined,
      lon: birthLon.value || undefined,
      timezone: form.timezone,
      residence_place: residencePlace.value || undefined,
      residence_lat: residenceLat.value || undefined,
      residence_lon: residenceLon.value || undefined,
    });
    saveDirty.value = false;

    // 触发重新分析，保持报告与档案数据一致
    try {
      await apiClient.post("/analyses", {
        analysis_type: "natal_blueprint",
        subjects: [{
          name: form.name,
          gender: form.gender,
          birth_time: birthTime,
          lat: birthLat.value || 39.9,
          lon: birthLon.value || 116.4,
          timezone: form.timezone,
          daylight_saving: form.daylightSaving,
          house_system: form.houseSystem,
        }],
      });
    } catch {
      // 分析生成失败不阻塞保存
    }

    await refreshChart();
    const { toast } = await import("@/utils/toast");
    toast.success("档案已保存，星盘已更新");
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

<style scoped lang="less">
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

/* ═══ 错误态 ═══ */
.error-emoji { font-size: 40px; margin: 0; }
.error-text { font-size: 14px; color: #b8a090; letter-spacing: 1px; margin: 0; }
.retry-btn { padding: 10px 28px; border-radius: 16px; border: 1px solid rgba(0,0,0,0.06); background: rgba(255,255,255,0.6); color: #8b7355; font-size: 13px; cursor: pointer; font-family: inherit; letter-spacing: 1px; transition: all 0.3s; }
.retry-btn:hover { background: rgba(255,255,255,0.8); color: #4a3728; border-color: rgba(255,160,130,0.25); }

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

/* ═══ 时区选择 ═══ */
.tz-select-wrap { position: relative; display: flex; align-items: center; border-radius: 18px; background: rgba(255,255,255,0.55); border: 1px solid rgba(0,0,0,0.04); backdrop-filter: blur(16px); transition: all 0.35s; }
.tz-select-wrap:focus-within { border-color: rgba(255,160,130,0.3); box-shadow: 0 0 0 5px rgba(255,180,150,0.07); background: rgba(255,255,255,0.7); }
.tz-select { flex: 1; border: none; background: transparent; padding: 14px 36px 14px 16px; font-size: 15px; color: #4a3028; outline: none; font-family: inherit; letter-spacing: 1px; appearance: none; cursor: pointer; border-radius: 18px; }
.tz-arrow { position: absolute; right: 14px; font-size: 10px; color: #b8a090; pointer-events: none; }

/* ═══ 级联选择器 ═══ */
.f-cascader { width: 100%; }
.f-cascader :deep(.el-input__wrapper) { background: rgba(255,255,255,0.55) !important; border: 1px solid rgba(0,0,0,0.04) !important; border-radius: 18px !important; box-shadow: none !important; padding: 12px 16px !important; backdrop-filter: blur(16px) !important; }
.f-cascader :deep(.el-input__inner) { color: #4a3028 !important; font-family: inherit !important; }
.f-cascader :deep(.el-input__inner::placeholder) { color: #c4b0a5 !important; }

/* ═══ 坐标栏 ═══ */
.coord-bar { display: flex; align-items: center; gap: 10px; }
.coord-text { flex: 1; font-size: 12px; color: #a89880; }
.geo-btn { padding: 4px 12px; border-radius: 10px; border: 1px solid rgba(0,0,0,0.08); background: rgba(255,255,255,0.5); color: #8b7355; font-size: 11px; cursor: pointer; font-family: inherit; white-space: nowrap; flex-shrink: 0; transition: all 0.2s; }
.geo-btn:hover:not(:disabled) { background: rgba(255,255,255,0.7); border-color: rgba(255,154,139,0.2); }
.geo-btn:disabled { opacity: 0.5; }

/* ═══ 手动坐标 ═══ */
.manual-coord { margin-top: 2px; }
.manual-coord-summary { font-size: 12px; color: #b8a090; cursor: pointer; user-select: none; }
.manual-grid { display: grid; gap: 10px; margin-top: 8px; }
.manual-field label { display: block; font-size: 11px; color: #b8a090; margin-bottom: 4px; }
.manual-row { display: flex; align-items: center; gap: 4px; }
.manual-row span { color: #8b7355; font-size: 13px; }
.manual-num { width: 55px; padding: 4px 6px; border-radius: 8px; border: 1px solid rgba(0,0,0,0.1); background: rgba(255,255,255,0.5); font-size: 13px; color: #4a3028; text-align: center; outline: none; font-family: inherit; }
.manual-num:focus { border-color: rgba(255,160,130,0.3); }
.manual-sel { padding: 4px; border-radius: 8px; border: 1px solid rgba(0,0,0,0.1); background: rgba(255,255,255,0.5); font-size: 13px; color: #4a3028; outline: none; font-family: inherit; }

/* ═══ 选单样式继承 ═══ */
:deep(.f-picker .el-input__wrapper) { background: rgba(255,255,255,0.55) !important; border: 1px solid rgba(0,0,0,0.04) !important; border-radius: 18px !important; box-shadow: none !important; padding: 14px 16px !important; backdrop-filter: blur(16px) !important; }
:deep(.f-picker .el-input__inner) { color: #4a3028 !important; font-family: inherit !important; letter-spacing: 1.5px !important; }
:deep(.f-picker .el-input__inner::placeholder) { color: #c4b0a5 !important; }

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

<!-- 非 scoped: Element Plus 治愈系覆盖 -->
<style>
.f-picker .el-input__wrapper { background: rgba(255,255,255,0.55) !important; border: 1px solid rgba(0,0,0,0.04) !important; border-radius: 18px !important; box-shadow: none !important; padding: 14px 16px !important; backdrop-filter: blur(16px) !important; }
.f-picker .el-input__inner { color: #4a3028 !important; font-family: inherit !important; letter-spacing: 1.5px !important; }
.f-picker .el-input__inner::placeholder { color: #c4b0a5 !important; }
.f-picker .el-input__prefix, .f-picker .el-input__suffix { color: #b8a090 !important; }

/* popper 毛玻璃 */
.heal-popper { background: rgba(255,255,255,0.95) !important; backdrop-filter: blur(24px) !important; border: 1px solid rgba(0,0,0,0.04) !important; box-shadow: 0 16px 48px rgba(0,0,0,0.06) !important; color: #4a3028 !important; border-radius: 18px !important; }
.heal-popper .el-picker-panel__icon-btn { color: #b8a090 !important; }
.heal-popper .el-picker-panel__icon-btn:hover { color: #4a3028 !important; }
.heal-popper .el-date-table td { color: #8b6f5f !important; }
.heal-popper .el-date-table td.available:hover { color: #4a3028 !important; }
.heal-popper .el-date-table td.current span { background: rgba(240,170,140,0.4) !important; color: #fff !important; }
.heal-popper .el-date-table td.today span { color: #d09070 !important; font-weight: 600 !important; }
.heal-popper .el-time-spinner__item { color: #8b6f5f !important; }
.heal-popper .el-time-spinner__item.active { color: #4a3028 !important; }
.heal-popper .el-time-spinner__item:hover { background: rgba(0,0,0,0.02) !important; }

/* cascader popper 毛玻璃 */
.heal-cascader-popper { background: rgba(255,255,255,0.95) !important; backdrop-filter: blur(24px) !important; border: 1px solid rgba(0,0,0,0.04) !important; box-shadow: 0 16px 48px rgba(0,0,0,0.06) !important; border-radius: 18px !important; }
.heal-cascader-popper .el-cascader-node__label { color: #4a3728 !important; }
.heal-cascader-popper .el-cascader-node:not(.is-disabled):hover { background: rgba(240,170,140,0.08) !important; }
.heal-cascader-popper .el-cascader-node.is-active { background: rgba(240,170,140,0.12) !important; }
</style>
