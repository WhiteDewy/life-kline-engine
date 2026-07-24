<template>
  <div class="onboard-page">
    <canvas ref="particleCanvas" class="particle-canvas"></canvas>
    <div class="glow glow--a"></div>
    <div class="glow glow--b"></div>

    <!-- ── 进度点 ── -->
    <div class="dots" v-if="step < 4">
      <span v-for="i in 3" :key="i" class="dot" :class="{ done: i < step, cur: i === step }"></span>
    </div>

    <!-- ═══ Step 1: 昵称 ═══ -->
    <transition name="step" mode="out-in">
      <div class="step-wrap" v-if="step === 1" key="s1">
        <div class="s-emoji">✨</div>
        <h2 class="s-title">告诉我，怎么称呼你</h2>
        <p class="s-sub">星灵们会记住这个名字</p>

        <div class="glass-inp">
          <input ref="ni" v-model="nickname" class="g-inp" maxlength="12" placeholder="输入你的昵称" @keyup.enter="goStep(2)" />
          <button class="g-icon" @click="randomNickname"><span>🎲</span></button>
        </div>

        <div class="chip-row">
          <button v-for="n in randomSuggestions" :key="n" class="chip" @click="nickname = n">{{ n }}</button>
        </div>

        <button class="main-btn" :disabled="!nickname.trim()" @click="goStep(2)">继续</button>
      </div>
    </transition>

    <!-- ═══ Step 2: 性别 ═══ -->
    <transition name="step" mode="out-in">
      <div class="step-wrap" v-if="step === 2" key="s2">
        <div class="s-emoji">💫</div>
        <h2 class="s-title">你的能量是</h2>
        <p class="s-sub">星灵会以最契合的方式感知你</p>

        <div class="gender-row">
          <button class="g-card" :class="{ on: gender === '女' }" @click="gender = '女'; after(() => goStep(3), 350)">
            <div class="g-orb g-orb--yin"><span>♀</span></div>
            <span class="g-label">女性</span>
            <span class="g-sub">阴 · 月 · 水</span>
          </button>
          <button class="g-card" :class="{ on: gender === '男' }" @click="gender = '男'; after(() => goStep(3), 350)">
            <div class="g-orb g-orb--yang"><span>♂</span></div>
            <span class="g-label">男性</span>
            <span class="g-sub">阳 · 日 · 火</span>
          </button>
        </div>
      </div>
    </transition>

    <!-- ═══ Step 3: 出生 ═══ -->
    <transition name="step" mode="out-in">
      <div class="step-wrap" v-if="step === 3" key="s3">
        <div class="s-emoji">🌙</div>
        <h2 class="s-title">你什么时候来到这个世界的</h2>
        <p class="s-sub">越精确，星盘与你的共振越深</p>

        <div class="form-stack">
          <!-- 公历/农历切换 -->
          <div class="toggle-row">
            <button :class="{ on: calendarType === 'solar' }" @click="calendarType = 'solar'">☀️ 公历</button>
            <button :class="{ on: calendarType === 'lunar' }" @click="calendarType = 'lunar'">🌙 农历</button>
          </div>

          <div class="f-label">出生日期</div>
          <el-date-picker v-model="birthDate" type="date" placeholder="选择日期" format="YYYY / MM / DD" value-format="YYYY-MM-DD" class="f-picker" popper-class="heal-popper" />

          <div class="f-label">出生时间</div>
          <el-time-picker v-model="birthTime" placeholder="选择时间" format="HH:mm" value-format="HH:mm" class="f-picker" popper-class="heal-popper" />

          <div class="f-label">出生地点</div>
          <el-cascader
            v-model="birthRegionCodes"
            :options="regionData"
            :props="{ label: 'label', value: 'value', children: 'children' }"
            clearable filterable
            placeholder="省 / 市 / 区"
            class="f-cascader"
            popper-class="heal-popper"
            @change="onBirthRegionChange"
          />
          <div class="coord-bar">
            <span class="coord-text" v-if="birthCoordLabel">{{ birthCoordLabel }}</span>
            <span class="coord-text" v-else>选择地点后自动获取坐标</span>
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

          <div class="f-label">现居地</div>
          <el-cascader
            v-model="residenceRegionCodes"
            :options="regionData"
            :props="{ label: 'label', value: 'value', children: 'children' }"
            clearable filterable
            placeholder="省 / 市 / 区"
            class="f-cascader"
            popper-class="heal-popper"
            @change="onResidenceRegionChange"
          />
          <div class="coord-bar">
            <span class="coord-text" v-if="residenceCoordLabel">{{ residenceCoordLabel }}</span>
            <span class="coord-text" v-else>选择地点后自动获取坐标</span>
          </div>

          <!-- 夏令时 -->
          <div class="toggle-row dls-row">
            <button class="dls-btn" :class="{ on: daylightSaving }" @click="daylightSaving = !daylightSaving">
              <span>☀️ 夏令时</span>
              <span class="dls-hint">{{ daylightSaving ? '已开启' : '未开启' }}</span>
            </button>
            <p class="dls-note">{{ dstHint }}</p>
          </div>

        </div>

        <button class="main-btn" :disabled="!canSubmit" @click="submitBirth">绘制我的星图</button>
      </div>
    </transition>

    <!-- ═══ Step 4: 唤醒 ═══ -->
    <div class="awaken" v-if="step === 4">
      <!-- 4a: 卡片 -->
      <transition name="card-up">
        <div class="user-card" v-if="awakenPhase === 'card' && showCard" key="uc">
          <div class="uc-ring"><span class="uc-avatar">{{ gender === '女' ? '♀' : '♂' }}</span></div>
          <div class="uc-name">{{ nickname }}</div>
          <div class="uc-meta">{{ birthDateStr }} · {{ birthPlace || '地球' }}</div>
        </div>
      </transition>

      <!-- 4b: 行星升起 -->
      <div class="planet-rise" v-if="awakenPhase === 'planets'">
        <p class="rise-hint">星辰正在苏醒...</p>
        <div class="rise-col">
          <transition-group name="p-up">
            <div v-for="p in visiblePlanets" :key="p.key" class="p-row" :style="{ '--pc': p.color }">
              <span class="p-dot" :style="{ background: p.color }"></span>
              <span class="p-sym" :style="{ color: p.color }">{{ p.symbol }}</span>
              <span class="p-name">{{ p.name }}</span>
            </div>
          </transition-group>
        </div>
      </div>

      <!-- 4c: 上升 + 完整图景 -->
      <div class="asc-stage" v-if="awakenPhase === 'ascendant'">
        <transition name="asc-in">
          <div class="asc-card" v-if="showAsc" key="asc">
            <div class="asc-ring"><span>⇧</span></div>
            <p class="asc-label">上升星座</p>
            <p class="asc-sign">{{ ascSign }}</p>
            <p class="asc-desc">{{ ascDesc || '这是你与世界相遇的那一刻，东方地平线升起的星座' }}</p>
          </div>
        </transition>

        <transition name="grid-in">
          <div class="p-grid" v-if="showFinalPlanets" key="grid">
            <div v-for="(p, i) in allPlanets" :key="p.key" class="p-cell" :style="{ '--pc': p.color, animationDelay: i * 0.07 + 's' }">
              <span class="pc-sym" :style="{ color: p.color }">{{ p.symbol }}</span>
              <span class="pc-sign">{{ p.signLabel || '?' }}</span>
              <span class="pc-name">{{ p.name }}</span>
            </div>
          </div>
        </transition>

        <transition name="cta-in">
          <button v-if="showCta" class="main-btn enter-btn" @click="enterGarden" key="cta">进入星灵花园</button>
        </transition>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onBeforeUnmount, nextTick, watch } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { regionData, codeToText } from "element-china-area-data";
import { useAuth } from "@/utils/auth";
import { apiClient } from "@/config/api";
import { formatCoordinateLabel, splitCoordinateParts, composeCoordinateValue } from "@/utils/coordinates";
import { textToRegionCodes } from "@/utils/regions";
import { Lunar } from "lunar-javascript";

const router = useRouter();
const { saveProfile, profiles, loadMe } = useAuth();

const step = ref(1);
const nickname = ref("");
const gender = ref("");
const calendarType = ref<"solar" | "lunar">("solar");
const birthDate = ref<Date | null>(null);
const birthTime = ref<Date | null>(null);
const birthPlace = ref("");
const birthLat = ref(0);
const birthLon = ref(0);
const birthRegionCodes = ref<string[]>([]);
const residencePlace = ref("");
const residenceLat = ref(0);
const residenceLon = ref(0);
const residenceRegionCodes = ref<string[]>([]);
const daylightSaving = ref(false);
const geoLoading = ref(false);
const showManualCoord = ref(false);
const manualBirthLat = reactive({ deg: 0, min: 0, dir: "N" as "N" | "S" });
const manualBirthLon = reactive({ deg: 0, min: 0, dir: "E" as "E" | "W" });
const ni = ref<HTMLInputElement | null>(null);
const canSubmit = computed(() => birthDate.value && birthTime.value && birthPlace.value.trim());
const birthDateStr = computed(() => { if (!birthDate.value) return ""; return typeof birthDate.value === "string" ? birthDate.value : (birthDate.value as Date).toISOString().slice(0, 10); });

const birthCoordLabel = computed(() => {
  if (!birthLat.value && !birthLon.value) return "";
  return `${formatCoordinateLabel(birthLat.value, "latitude")} / ${formatCoordinateLabel(birthLon.value, "longitude")}`;
});
const residenceCoordLabel = computed(() => {
  if (!residenceLat.value && !residenceLon.value) return "";
  return `${formatCoordinateLabel(residenceLat.value, "latitude")} / ${formatCoordinateLabel(residenceLon.value, "longitude")}`;
});
const dstHint = computed(() => {
  const year = birthDate.value ? new Date(birthDate.value).getFullYear() : 0;
  if (year >= 1986 && year <= 1991) return "你出生于中国夏令时期，建议开启";
  return "1986-1991年间出生请注意";
});

function onBirthRegionChange(codes: string[]) {
  if (!codes?.length) { birthPlace.value = ""; return; }
  birthPlace.value = codes.map(c => codeToText[c] || "").join(" ");
}
function onResidenceRegionChange(codes: string[]) {
  if (!codes?.length) { residencePlace.value = ""; return; }
  residencePlace.value = codes.map(c => codeToText[c] || "").join(" ");
}

async function autoGeocode() {
  if (!birthPlace.value) { ElMessage.warning("请先选择出生地点"); return; }
  geoLoading.value = true;
  try {
    const r = await apiClient.post("/geocode", { query: birthPlace.value });
    if (r.data?.status === "success" && r.data?.data) {
      birthLat.value = Number(r.data.data.lat);
      birthLon.value = Number(r.data.data.lon);
      ElMessage.success("坐标已获取");
    } else {
      ElMessage.warning("获取失败，请检查地点名称");
    }
  } catch {
    ElMessage.warning("获取失败，请检查地点名称");
  } finally {
    geoLoading.value = false;
  }
}

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
}

// 进入 step 3 时预填已有 profile
watch(step, async (s) => {
  if (s === 3) {
    if (!profiles.value?.length) {
      try { await loadMe(); } catch { /* 静默失败 */ }
    }
    const p = profiles.value?.[0];
    if (p) {
      if (p.birth_time) {
        const dt = new Date(p.birth_time);
        birthDate.value = dt;
        birthTime.value = dt;
      }
      birthPlace.value = p.birth_place || "";
      birthLat.value = p.lat || 0;
      birthLon.value = p.lon || 0;
      if (p.birth_place) {
        const codes = textToRegionCodes(p.birth_place);
        if (codes) birthRegionCodes.value = codes;
      }
      residencePlace.value = p.residence_place || "";
      residenceLat.value = p.residence_lat || 0;
      residenceLon.value = p.residence_lon || 0;
      if (p.residence_place) {
        const codes = textToRegionCodes(p.residence_place);
        if (codes) residenceRegionCodes.value = codes;
      }
      daylightSaving.value = !!p.daylight_saving;
      syncManualFromForm();
      if (!p.lat && !p.lon) showManualCoord.value = true;
    }
  }
});

// 农历转公历
function lunarToSolar(lunarDateStr: string): string {
  const parts = lunarDateStr.split("-");
  const y = Number(parts[0]), m = Number(parts[1]), d = Number(parts[2]);
  try {
    const lunar = Lunar.fromYmd(y, m, d);
    const solar = lunar.getSolar();
    const mm = String(solar.getMonth()).padStart(2, "0");
    const dd = String(solar.getDay()).padStart(2, "0");
    return `${solar.getYear()}-${mm}-${dd}`;
  } catch {
    return lunarDateStr;
  }
}

const NICKNAMES = ["追星星的人","月光旅人","银河漫游者","晨曦微光","晚风轻轻","星辰大海","云端之上","深海鲸鱼","北极星的眼泪","夏日萤火","冬日暖阳","风铃草","薄荷糖","小宇宙","半糖去冰","森林里的鹿","海边的小贝壳","南山南","北方的雪","向日葵"];
const randomSuggestions = ref<string[]>([]);
function shuffle() { randomSuggestions.value = [...NICKNAMES].sort(() => Math.random() - 0.5).slice(0, 4); }
function randomNickname() { const pool = NICKNAMES.filter(n => n !== nickname.value); nickname.value = pool[Math.floor(Math.random() * pool.length)] ?? ""; }
shuffle();
function goStep(n: number) { step.value = n; if (n === 1) { shuffle(); nextTick(() => ni.value?.focus()); } if (n === 3) shuffle(); }
function after(fn: () => void, ms: number) { setTimeout(fn, ms); }

async function submitBirth() {
  if (!canSubmit.value) return;

  // 农历转换
  let dateStr = birthDateStr.value;
  if (calendarType.value === "lunar") {
    dateStr = lunarToSolar(dateStr);
  }

  const ts = typeof birthTime.value === "string" ? birthTime.value : (birthTime.value as Date).toTimeString().slice(0, 5);
  const iso = `${dateStr}T${ts}:00`;
  step.value = 4; awakenPhase.value = "card"; showCard.value = false;

  // 如果没有手动获取坐标，尝试自动 geocode
  let lat = birthLat.value || 39.9;
  let lon = birthLon.value || 116.4;
  if (!birthLat.value && !birthLon.value && birthPlace.value.trim()) {
    try {
      const geoRes = await apiClient.post("/geocode", { query: birthPlace.value.trim() });
      if (geoRes.data?.data?.lat != null && geoRes.data?.data?.lon != null) {
        lat = Number(geoRes.data.data.lat);
        lon = Number(geoRes.data.data.lon);
      }
    } catch { /* fall through */ }
  }

  // 现居地 geocode
  let rLat = residenceLat.value;
  let rLon = residenceLon.value;
  if (!rLat && !rLon && residencePlace.value.trim()) {
    try {
      const geoRes = await apiClient.post("/geocode", { query: residencePlace.value.trim() });
      if (geoRes.data?.data?.lat != null && geoRes.data?.data?.lon != null) {
        rLat = Number(geoRes.data.data.lat);
        rLon = Number(geoRes.data.data.lon);
      }
    } catch { /* fall through */ }
  }

  try {
    await saveProfile({
      name: nickname.value, gender: gender.value, birth_time: iso,
      lat, lon, timezone: 8,
      birth_place: birthPlace.value,
      daylight_saving: daylightSaving.value, house_system: "B",
      residence_place: residencePlace.value, residence_lat: rLat, residence_lon: rLon,
    });
    const res = await apiClient.post("/analyses", {
      analysis_type: "natal_blueprint",
      subjects: [{ name: nickname.value, gender: gender.value, birth_time: iso, lat, lon, timezone: 8, daylight_saving: daylightSaving.value, house_system: "B" }],
      });
    if (res.data?.status === "success") {
      const reportId = res.data.report_id || "";
      try {
        const d = await apiClient.get(`/analyses/${reportId}`);
        if (d.data?.status === "success") {
          const nc = d.data.data.natal_chart;
          if (nc) {
            ascSign.value = nc.ascendant?.sign_label || "未知";
            ascDesc.value = nc.ascendant?.sign_meaning?.slice(0, 80) || "";
            const pm: Record<string, { signLabel: string }> = {};
            if (nc.planets) for (const [k, v] of Object.entries(nc.planets)) pm[k] = { signLabel: (v as any).sign_label || "" };
            planetData.value = pm;
          }
        }
      } catch {}
    }
  } catch (e) { console.error(e); }

  await nextTick(); showCard.value = true;
  setTimeout(() => startPlanets(), 2000);
}

const awakenPhase = ref<"card"|"planets"|"ascendant">("card");
const showCard = ref(false);
const PLANETS = [
  { key:"SUN",symbol:"☉",name:"太阳",color:"#E8A840"},{ key:"MOON",symbol:"☽",name:"月亮",color:"#B0C4D0"},{ key:"MERCURY",symbol:"☿",name:"水星",color:"#90A878"},{ key:"VENUS",symbol:"♀",name:"金星",color:"#D898A8"},{ key:"MARS",symbol:"♂",name:"火星",color:"#D07050"},{ key:"JUPITER",symbol:"♃",name:"木星",color:"#7888B0"},{ key:"SATURN",symbol:"♄",name:"土星",color:"#889098"},{ key:"URANUS",symbol:"♅",name:"天王星",color:"#68B0B0"},{ key:"NEPTUNE",symbol:"♆",name:"海王星",color:"#6878B0"},{ key:"PLUTO",symbol:"♇",name:"冥王星",color:"#987898"},
];
const visiblePlanets = ref<typeof PLANETS>([]);
const planetData = ref<Record<string,{signLabel:string}>>({});
function startPlanets() { awakenPhase.value = "planets"; visiblePlanets.value = []; PLANETS.forEach((p,i) => { setTimeout(() => { visiblePlanets.value = [...visiblePlanets.value, p]; if (i === PLANETS.length - 1) setTimeout(() => startAsc(), 350); }, i * 260); }); }
const ascSign = ref(""); const ascDesc = ref(""); const showAsc = ref(false); const showFinalPlanets = ref(false); const showCta = ref(false);
const allPlanets = computed(() => PLANETS.map((p,i) => ({...p, signLabel: planetData.value[p.key]?.signLabel||"", delay:i*0.07})));
function startAsc() { awakenPhase.value = "ascendant"; showAsc.value = false; showFinalPlanets.value = false; showCta.value = false; setTimeout(()=>{showAsc.value=true},350); setTimeout(()=>{showFinalPlanets.value=true},1300); setTimeout(()=>{showCta.value=true},2200); }
function enterGarden() {
  localStorage.setItem("spirit_profile_completed", "1");
  router.replace({ name: "entry" });
}

// ── 柔光粒子 ──
const particleCanvas = ref<HTMLCanvasElement|null>(null); let animId = 0;
onMounted(() => { nextTick(() => ni.value?.focus()); initCanvas(); });
function initCanvas() {
  const c = particleCanvas.value; if (!c) return; const ctx = c.getContext("2d"); if (!ctx) return;
  const dpr = window.devicePixelRatio || 1;
  function resize() { c!.width = window.innerWidth * dpr; c!.height = window.innerHeight * dpr; c!.style.width = window.innerWidth + "px"; c!.style.height = window.innerHeight + "px"; }
  resize(); window.addEventListener("resize", resize);
  const motes: {x:number;y:number;r:number;vx:number;vy:number;a:number;ph:number}[] = [];
  for (let i=0;i<45;i++) motes.push({x:Math.random()*window.innerWidth*dpr,y:Math.random()*window.innerHeight*dpr,r:1+Math.random()*3,vx:(Math.random()-0.5)*0.25,vy:-0.15-Math.random()*0.35,a:0.15+Math.random()*0.45,ph:Math.random()*Math.PI*2});
  function draw() { ctx!.clearRect(0,0,c!.width,c!.height); const t=Date.now(); for(const m of motes){m.x+=m.vx;m.y+=m.vy;if(m.y<-20){m.y=c!.height+20;m.x=Math.random()*c!.width;}if(m.x<-20)m.x=c!.width+20;if(m.x>c!.width+20)m.x=-20;const alpha=m.a*(0.5+0.5*Math.sin(t*0.0008+m.ph));ctx!.beginPath();ctx!.arc(m.x,m.y,m.r,0,Math.PI*2);ctx!.fillStyle=`rgba(255,215,190,${alpha.toFixed(2)})`;ctx!.fill();if(m.r>2){ctx!.beginPath();ctx!.arc(m.x,m.y,m.r*4,0,Math.PI*2);ctx!.fillStyle=`rgba(255,195,165,${(alpha*0.1).toFixed(3)})`;ctx!.fill();}}animId=requestAnimationFrame(draw);}
  draw(); onBeforeUnmount(()=>{cancelAnimationFrame(animId);window.removeEventListener("resize",resize);});
}
</script>

<style scoped>
/* ═══ 基底 ═══ */
.onboard-page { min-height:100vh;position:relative;display:flex;flex-direction:column;align-items:center;justify-content:center;background:linear-gradient(175deg,#FFF5EE 0%,#FFEFE6 25%,#FFF0F5 55%,#F5F0FF 80%,#FDF5F0 100%);overflow:hidden; }
.particle-canvas { position:absolute;inset:0;z-index:0;pointer-events:none; }
.glow { position:absolute;border-radius:50%;pointer-events:none;z-index:0; }
.glow--a { width:380px;height:380px;top:5%;right:-140px;background:radial-gradient(circle,rgba(255,200,170,0.14) 0%,transparent 65%);animation:gd 8s ease-in-out infinite; }
.glow--b { width:340px;height:340px;bottom:-80px;left:-100px;background:radial-gradient(circle,rgba(220,190,230,0.1) 0%,transparent 65%);animation:gd 10s ease-in-out infinite reverse; }
@keyframes gd { 0%,100%{transform:translate(0,0) scale(1)} 50%{transform:translate(12px,-12px) scale(1.08)} }

/* ── 进度点 ── */
.dots { position:fixed;top:20px;left:50%;transform:translateX(-50%);z-index:10;display:flex;gap:10px; }
.dot { width:6px;height:6px;border-radius:3px;background:rgba(0,0,0,0.06);transition:all 0.5s cubic-bezier(0.25,0.46,0.45,0.94); }
.dot.done { background:rgba(220,160,130,0.3); }
.dot.cur { background:rgba(220,150,120,0.6);width:20px;box-shadow:0 0 6px rgba(220,150,120,0.2); }

/* ── 步骤容器 ── */
.step-wrap { position:relative;z-index:1;width:100%;max-width:360px;padding:0 24px;display:flex;flex-direction:column;align-items:center;gap:18px; }
.s-emoji { font-size:42px; }
.s-title { font-size:21px;font-weight:600;color:#5c3d3a;margin:0;letter-spacing:2px;text-align:center; }
.s-sub { font-size:13px;color:#b8a090;margin:0;text-align:center;letter-spacing:1px; }
.step-enter-active { transition:all 0.45s cubic-bezier(0.25,0.46,0.45,0.94); }
.step-leave-active { transition:all 0.2s ease; }
.step-enter-from { opacity:0;transform:translateY(14px); }
.step-leave-to { opacity:0;transform:translateY(-10px); }

/* ── 玻璃输入 ── */
.glass-inp { width:100%;display:flex;align-items:center;padding:2px;border-radius:18px;background:rgba(255,255,255,0.55);border:1px solid rgba(0,0,0,0.04);backdrop-filter:blur(16px);transition:all 0.35s; }
.glass-inp:focus-within { border-color:rgba(255,160,130,0.3);box-shadow:0 0 0 5px rgba(255,180,150,0.07);background:rgba(255,255,255,0.7); }
.g-inp { flex:1;border:none;background:transparent;padding:14px 16px;font-size:16px;color:#4a3028;outline:none;font-family:inherit;letter-spacing:1.5px;text-align:center; }
.g-inp::placeholder { color:#c4b0a5;letter-spacing:1px; }
.g-icon { width:44px;height:44px;border:none;border-radius:14px;flex-shrink:0;background:rgba(255,200,170,0.1);cursor:pointer;transition:all 0.3s; }
.g-icon:hover { background:rgba(255,200,170,0.2);transform:scale(1.06); }
.g-icon span { font-size:18px; }

.chip-row { display:flex;flex-wrap:wrap;justify-content:center;gap:8px; }
.chip { padding:8px 16px;border-radius:14px;border:1px solid rgba(0,0,0,0.04);background:rgba(255,255,255,0.5);color:#8b6f5f;font-size:12px;cursor:pointer;font-family:inherit;letter-spacing:1px;backdrop-filter:blur(8px);transition:all 0.3s; }
.chip:hover { border-color:rgba(255,160,130,0.25);color:#4a3028;background:rgba(255,255,255,0.7);transform:translateY(-1px); }

/* ── 主按钮 ── */
.main-btn { width:100%;padding:15px;border:none;border-radius:18px;background:linear-gradient(135deg,#f0b8a0,#e8a890,#f0c0b0);color:#fff;font-size:15px;font-weight:600;cursor:pointer;font-family:inherit;letter-spacing:2px;transition:all 0.35s cubic-bezier(0.25,0.46,0.45,0.94);box-shadow:0 4px 20px rgba(220,150,120,0.18); }
.main-btn:hover:not(:disabled) { transform:translateY(-2px);box-shadow:0 10px 32px rgba(220,150,120,0.28); }
.main-btn:active:not(:disabled) { transform:scale(0.98); }
.main-btn:disabled { opacity:0.4;cursor:not-allowed;box-shadow:none; }

/* ── 性别卡片 ── */
.gender-row { display:flex;gap:14px;width:100%; }
.g-card { flex:1;display:flex;flex-direction:column;align-items:center;gap:12px;padding:34px 18px;border-radius:22px;border:1.5px solid rgba(0,0,0,0.04);background:rgba(255,255,255,0.45);cursor:pointer;font-family:inherit;backdrop-filter:blur(12px);transition:all 0.45s cubic-bezier(0.25,0.46,0.45,0.94); }
.g-card:hover { border-color:rgba(255,160,130,0.2);transform:translateY(-3px);background:rgba(255,255,255,0.6); }
.g-card.on { border-color:rgba(240,170,140,0.4);background:rgba(255,240,230,0.5);box-shadow:0 0 0 5px rgba(240,170,140,0.07),0 8px 30px rgba(0,0,0,0.04); }
.g-orb { width:68px;height:68px;border-radius:50%;display:flex;align-items:center;justify-content:center;transition:all 0.5s; }
.g-orb span { font-size:28px;color:rgba(120,80,60,0.5); }
.g-orb--yin { background:radial-gradient(circle at 35% 30%,rgba(220,190,210,0.4),rgba(180,150,180,0.15));box-shadow:0 0 25px rgba(200,160,180,0.12); }
.g-orb--yang { background:radial-gradient(circle at 35% 30%,rgba(240,200,160,0.4),rgba(200,160,120,0.15));box-shadow:0 0 25px rgba(220,180,140,0.12); }
.g-label { font-size:16px;font-weight:600;color:#4a3028;letter-spacing:2px; }
.g-sub { font-size:11px;color:#b8a090;letter-spacing:1px; }

/* ── 表单 ── */
.form-stack { width:100%;display:flex;flex-direction:column;gap:10px; }
.toggle-row { display:flex;border-radius:14px;overflow:hidden;border:1px solid rgba(0,0,0,0.04);background:rgba(255,255,255,0.4); }
.toggle-row button { flex:1;padding:10px;border:none;background:transparent;font-size:13px;font-weight:500;color:#b8a090;cursor:pointer;font-family:inherit;letter-spacing:1px;transition:all 0.3s; }
.toggle-row button.on { background:rgba(240,170,140,0.12);color:#5c3d3a; }
.f-label { font-size:11px;font-weight:500;color:#b8a090;letter-spacing:2px;text-transform:uppercase;margin-top:2px; }
.f-picker { width:100%; }

/* ── 夏令时 ── */
.dls-row { flex-direction:column;padding:6px 10px;gap:2px;border-radius:14px;border:1px solid rgba(0,0,0,0.04);background:rgba(255,255,255,0.4); }
.dls-btn { width:100%;display:flex;align-items:center;justify-content:space-between;border:none;background:transparent;font-size:13px;font-weight:500;color:#b8a090;cursor:pointer;font-family:inherit;letter-spacing:1px;padding:8px 6px;transition:all 0.3s;border-radius:12px; }
.dls-btn.on { background:rgba(240,170,140,0.12);color:#5c3d3a; }
.dls-hint { font-size:11px;opacity:0.6; }
.dls-note { margin:0;font-size:10px;color:#c4b0a5;text-align:center;letter-spacing:1px; }

/* 级联选择器 */
.f-cascader { width:100%; }
.f-cascader :deep(.el-input__wrapper) { background:rgba(255,255,255,0.55) !important;border:1px solid rgba(0,0,0,0.04) !important;border-radius:18px !important;box-shadow:none !important;padding:12px 16px !important;backdrop-filter:blur(16px) !important; }
.f-cascader :deep(.el-input__inner) { color:#4a3028 !important;font-family:inherit !important; }

/* 坐标栏 */
.coord-bar { display:flex;align-items:center;gap:10px; }
.coord-text { flex:1;font-size:12px;color:#a89880; }
.geo-btn { padding:4px 12px;border-radius:10px;border:1px solid rgba(0,0,0,0.08);background:rgba(255,255,255,0.5);color:#8b7355;font-size:11px;cursor:pointer;font-family:inherit;white-space:nowrap;transition:all 0.2s; }
.geo-btn:hover:not(:disabled) { background:rgba(255,255,255,0.7);border-color:rgba(255,154,139,0.2); }
.geo-btn:disabled { opacity:0.5; }

/* 手动坐标 */
.manual-coord { margin-top: 2px; }
.manual-coord-summary { font-size: 12px; color: #b8a090; cursor: pointer; user-select: none; }
.manual-grid { display: grid; gap: 10px; margin-top: 8px; }
.manual-field label { display: block; font-size: 11px; color: #b8a090; margin-bottom: 4px; }
.manual-row { display: flex; align-items: center; gap: 4px; }
.manual-row span { color: #8b7355; font-size: 13px; }
.manual-num { width: 55px; padding: 4px 6px; border-radius: 8px; border: 1px solid rgba(0,0,0,0.1); background: rgba(255,255,255,0.5); font-size: 13px; color: #4a3028; text-align: center; outline: none; }
.manual-num:focus { border-color: rgba(255,160,130,0.3); }
.manual-sel { padding: 4px; border-radius: 8px; border: 1px solid rgba(0,0,0,0.1); background: rgba(255,255,255,0.5); font-size: 13px; color: #4a3028; outline: none; }
/* ── 宫位制 ── */
.house-select-row { display:flex;gap:6px;padding:6px 8px;flex-wrap:wrap;justify-content:center; }
.hs-chip { padding:8px 14px;border-radius:14px;border:1px solid rgba(0,0,0,0.04);background:rgba(255,255,255,0.5);color:#8b6f5f;font-size:12px;cursor:pointer;font-family:inherit;letter-spacing:1px;transition:all 0.3s;flex:1;min-width:70px; }
.hs-chip:hover { border-color:rgba(255,160,130,0.25);color:#4a3028;background:rgba(255,255,255,0.7); }
.hs-chip.on { background:rgba(240,170,140,0.12);border-color:rgba(240,170,140,0.25);color:#5c3d3a;font-weight:600; }

/* ═══ 唤醒动画 ═══ */
.awaken { position:relative;z-index:1;width:100%;max-width:400px;padding:0 24px;display:flex;flex-direction:column;align-items:center;min-height:60vh;justify-content:center; }

/* 用户卡片 */
.user-card { text-align:center;padding:36px 32px;border-radius:26px;background:rgba(255,255,255,0.6);border:1px solid rgba(0,0,0,0.04);backdrop-filter:blur(16px);box-shadow:0 12px 40px rgba(0,0,0,0.04); }
.uc-ring { width:76px;height:76px;border-radius:50%;margin:0 auto 16px;border:1.5px solid rgba(220,170,140,0.25);display:flex;align-items:center;justify-content:center;background:radial-gradient(circle at 35% 30%,rgba(240,200,170,0.2),transparent);animation:ring-pulse 3s ease-in-out infinite; }
@keyframes ring-pulse { 0%,100%{box-shadow:0 0 16px rgba(220,160,130,0.1)} 50%{box-shadow:0 0 32px rgba(220,160,130,0.2)} }
.uc-avatar { font-size:30px;color:rgba(160,100,70,0.5); }
.uc-name { font-size:22px;font-weight:600;color:#4a3028;letter-spacing:3px;margin-bottom:4px; }
.uc-meta { font-size:12px;color:#b8a090;letter-spacing:1px; }
.card-up-enter-active { transition:all 0.7s cubic-bezier(0.25,0.46,0.45,0.94); }
.card-up-enter-from { opacity:0;transform:translateY(36px) scale(0.95); }

/* 行星升起 */
.planet-rise { width:100%; }
.rise-hint { text-align:center;font-size:14px;color:#b8a090;letter-spacing:2px;margin-bottom:20px;font-weight:400; }
.rise-col { display:flex;flex-direction:column;align-items:center;gap:1px; }
.p-row { display:flex;align-items:center;gap:12px;padding:7px 0;width:200px; }
.p-dot { width:5px;height:5px;border-radius:50%;flex-shrink:0;box-shadow:0 0 8px var(--pc);animation:dot-glow 2s ease-in-out infinite; }
@keyframes dot-glow { 0%,100%{box-shadow:0 0 5px var(--pc)} 50%{box-shadow:0 0 12px var(--pc),0 0 20px var(--pc)} }
.p-sym { font-size:17px;width:26px;text-align:center; }
.p-name { font-size:14px;color:#8b6f5f;font-weight:400;letter-spacing:1.5px;width:60px; }
.p-up-enter-active { transition:all 0.45s cubic-bezier(0.25,0.46,0.45,0.94); }
.p-up-enter-from { opacity:0;transform:translateY(20px); }

/* 上升星座 */
.asc-stage { display:flex;flex-direction:column;align-items:center;gap:22px;width:100%; }
.asc-card { text-align:center; }
.asc-ring { width:60px;height:60px;border-radius:50%;margin:0 auto 12px;border:1.5px solid rgba(200,170,150,0.25);display:flex;align-items:center;justify-content:center;background:radial-gradient(circle at 35% 30%,rgba(220,180,150,0.15),transparent); }
.asc-ring span { font-size:24px;color:rgba(160,120,90,0.5); }
.asc-label { font-size:11px;color:#b8a090;letter-spacing:2px;margin:0 0 4px; }
.asc-sign { font-size:26px;font-weight:600;color:#4a3028;letter-spacing:3px;margin:0 0 6px; }
.asc-desc { font-size:13px;color:#b8a090;margin:0;line-height:1.6;max-width:280px; }
.asc-in-enter-active { transition:all 0.55s cubic-bezier(0.25,0.46,0.45,0.94); }
.asc-in-enter-from { opacity:0;transform:scale(0.9); }

/* 完整行星网格 */
.p-grid { display:flex;flex-wrap:wrap;justify-content:center;gap:8px;max-width:300px; }
.p-cell { display:flex;flex-direction:column;align-items:center;gap:2px;width:50px;padding:8px 4px;border-radius:14px;background:rgba(255,255,255,0.45);border:1px solid rgba(0,0,0,0.03);animation:cell-pop 0.45s cubic-bezier(0.25,0.46,0.45,0.94) both; }
@keyframes cell-pop { from{opacity:0;transform:scale(0.6)} to{opacity:1;transform:scale(1)} }
.pc-sym { font-size:17px; }
.pc-sign { font-size:9px;color:#b8a090; }
.pc-name { font-size:9px;color:#c4b0a5; }
.grid-in-enter-active { transition:all 0.4s ease; }
.grid-in-enter-from { opacity:0; }

.enter-btn { width:240px!important;margin-top:6px;animation:enter-glow 2.5s ease-in-out infinite; }
@keyframes enter-glow { 0%,100%{box-shadow:0 4px 20px rgba(220,150,120,0.15)} 50%{box-shadow:0 8px 36px rgba(220,150,120,0.28)} }
.cta-in-enter-active { transition:all 0.45s cubic-bezier(0.25,0.46,0.45,0.94); }
.cta-in-enter-from { opacity:0;transform:translateY(10px); }
</style>

<style>
/* Element Plus 治愈系覆盖 */
.f-picker .el-input__wrapper { background:rgba(255,255,255,0.55)!important;border:1px solid rgba(0,0,0,0.04)!important;border-radius:18px!important;box-shadow:none!important;padding:14px 16px!important;backdrop-filter:blur(16px)!important; }
.f-picker .el-input__inner { color:#4a3028!important;font-family:inherit!important;letter-spacing:1.5px!important; }
.f-picker .el-input__inner::placeholder { color:#c4b0a5!important; }
.f-picker .el-input__prefix,.f-picker .el-input__suffix { color:#b8a090!important; }
.heal-popper { background:rgba(255,255,255,0.95)!important;backdrop-filter:blur(24px)!important;border:1px solid rgba(0,0,0,0.04)!important;box-shadow:0 16px 48px rgba(0,0,0,0.06)!important;color:#4a3028!important;border-radius:18px!important; }
.heal-popper .el-picker-panel__icon-btn { color:#b8a090!important; }
.heal-popper .el-picker-panel__icon-btn:hover { color:#4a3028!important; }
.heal-popper .el-date-table td { color:#8b6f5f!important; }
.heal-popper .el-date-table td.available:hover { color:#4a3028!important; }
.heal-popper .el-date-table td.current span { background:rgba(240,170,140,0.4)!important;color:#fff!important; }
.heal-popper .el-date-table td.today span { color:#d09070!important;font-weight:600!important; }
.heal-popper .el-time-spinner__item { color:#8b6f5f!important; }
.heal-popper .el-time-spinner__item.active { color:#4a3028!important; }
.heal-popper .el-time-spinner__item:hover { background:rgba(0,0,0,0.02)!important; }
</style>
