<!-- 专业感太强 冷启动很危险 -->
<template>
  <div class="page">
    <div
      class="star-container"
      :style="{
        '--shadow-1': shadow1,
        '--shadow-2': shadow2,
        '--shadow-3': shadow3,
      }"
    >
      <div class="star-layer layer-1"></div>
      <div class="star-layer layer-2"></div>
      <div class="star-layer layer-3"></div>
    </div>

    <div class="wrap">
      <!-- Hero -->
      <header class="hero">
        <h1 class="title">
          看清你的生命出厂设置<br />
          掌握你的人生气候变化
        </h1>
        <p class="subtitle">
          理性美学与数据驱动的人生节律解析。<br />
          不是预测，而是基于天文算法的深度自我认知。
        </p>

        <div class="transit-ticker-container">
          <div class="transit-ticker-track">
            <div class="ticker-group" v-for="n in 2" :key="n">
              <span class="ticker-item">
                <span class="dot gold">●</span>
                <span class="label">实时天象感知：</span>
                当前水星位于
                {{ transitData?.planets?.MERCURY?.sign || "Aquarius" }} 15°,
                正在与木星形成三分相
              </span>
              <span class="separator">|</span>
              <span class="ticker-item">
                <span class="dot indigo">●</span>
                <span class="label">宇宙当前节律：</span>
                思维活跃度提升 25%，适合进行长期战略规划与复杂逻辑推演
              </span>
              <span class="separator">|</span>
              <span class="ticker-item">
                <span class="dot gold">●</span>
                <span class="label">全局能量场：</span>
                稳定度 [高] 建议行动：方案输出、契约签署
              </span>
              <span class="separator">|</span>
            </div>
          </div>
        </div>

        <div class="cta-container">
          <el-button
            class="cta-btn-large"
            type="primary"
            round
            @click="scrollToForm"
          >
            Generate Profile
          </el-button>
        </div>
      </header>

      <!-- Section 2: Bento Grid -->
      <section class="section bento-section">
        <div class="bento-grid">
          <div class="bento-card large shine">
            <el-icon class="card-icon"><Cpu /></el-icon>
            <h3>理性核心 (Rational Core)</h3>
            <p>
              告别宿命论。我们采用 NASA
              级别的天文算法计算时间质量，为您提供清醒、客观的人生节律分析。
            </p>
          </div>
          <div class="bento-card medium">
            <el-icon class="card-icon"><TrendCharts /></el-icon>
            <h3>数据驱动 (Data-Driven)</h3>
            <p>基于 Swiss Ephemeris 的高精度数据，精确到分钟的周期演算。</p>
            <p>支持追踪行星回归、月相周期等深层节律</p>
          </div>
          <div class="bento-card medium">
            <el-icon class="card-icon"><Lock /></el-icon>
            <h3>长期有效 (Long-Term Usability)</h3>
            <p>
              你的星盘不会改变， 但你所处的人生阶段一直在变。
              这个系统不是一次性解读， 而是可以反复回看的长期参考。
            </p>
          </div>
          <div class="bento-card medium">
            <el-icon class="card-icon"><Sunny /></el-icon>
            <h3>确认你的闪光点 (Shining Point)</h3>
            <p>
              你真正擅长什么？我们深度挖掘被忽略的天赋领域，识别你的高光时刻模式。通过算法识别你的“核心竞争优势”，不再在非天赋领域内耗。
            </p>
          </div>
          <div class="bento-card medium">
            <el-icon class="card-icon"><Warning /></el-icon>
            <h3>当下节律卡点</h3>
            <p>
              为什么最近感到卡顿？识别当前人生周期的压力源，区分“自身选择”与“宇宙气候”。
            </p>
          </div>
        </div>
      </section>

      <!-- Section 3: Showcase -->
      <section class="section showcase-section-v2">
        <div class="showcase-container">
          <div class="sync-animation">
            <!-- PC Mock -->
            <div class="mock-pc">
              <div class="window-controls">
                <div class="ctrl red"></div>
                <div class="ctrl yellow"></div>
                <div class="ctrl green"></div>
              </div>
              <div class="pc-content">
                <div class="skeleton-line w-30 mb-4"></div>
                <div class="chart-bars">
                  <div
                    v-for="h in [40, 70, 50, 90, 60, 80, 40]"
                    :key="h"
                    :style="{ height: h + '%' }"
                    class="bar"
                  ></div>
                </div>
                <div class="terminal-text mt-4">
                  SYSTEM_STATUS: CONTINUOUS_CALCULATION...
                </div>
              </div>
            </div>
            <!-- Phone Mock -->
            <div class="mock-phone">
              <div class="phone-screen">
                <div class="notification-card">
                  <div class="notif-header">
                    <span class="app-name">LIFE ENGINE</span>
                    <span class="time">CURRENT PHASE</span>
                  </div>
                  <div class="notif-title">当前节律解读</div>
                  <div class="notif-body">
                    检测到“高敏感”周期，建议今晚推迟非必要谈判。
                  </div>
                </div>

                <div class="widget-grid">
                  <div class="widget-card small">
                    <div class="widget-label">今日能量</div>
                    <div class="energy-ring">
                      <div class="ring-track"></div>
                      <div class="ring-value" style="--p: 75"></div>
                      <span class="value-text">75%</span>
                    </div>
                  </div>
                  <div class="widget-card small">
                    <div class="widget-label">专注力</div>
                    <div class="focus-bar">
                      <div class="bar-fill" style="width: 60%"></div>
                    </div>
                    <span class="value-text-sm">Moderate</span>
                  </div>
                </div>

                <div class="widget-card medium">
                  <div class="widget-label">下一个关键点</div>
                  <div class="next-event">
                    <span class="time">14:00</span>
                    <span class="desc">水星进入双子座</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="showcase-info">
            <h2 class="section-title-large">从宇宙大数据到你的口袋助理</h2>
            <p class="section-desc">
              这不仅是一次测算，而是一套持续更新的人生节律分析系统。 我们基于
              Swiss Ephemeris 高精度历表进行长期运算，
              将天文变化转化为可理解、可参考的个体节律信息，
              帮助你更清楚地认识自己所处的阶段。
            </p>
            <ul class="feature-list">
              <li>
                <el-icon class="icon-gold"><CircleCheck /></el-icon>
                <span>个人节律档案：支持持续更新与阶段对照</span>
              </li>
              <li>
                <el-icon class="icon-gold"><CircleCheck /></el-icon>
                <span>将枯燥的星历数据转化为直观的人生波动 K 线图，一眼看清未来半年趋势。</span>
              </li>
              <li>
                <el-icon class="icon-gold"><CircleCheck /></el-icon>
                <span>基于数千个真实案例校正的逻辑库，精准过滤模棱两可的玄学描述。</span>
              </li>
            </ul>
          </div>
        </div>
      </section>

      <!-- Section 4: Form (Card) -->
      <div id="start-engine" class="engine-section">
        <el-card class="card form-card" shadow="never">
          <div class="head">
            <div>
              <div class="headTitle">初始化个人模型 (Initialize)</div>
              <div class="headHint">输入出生数据以校准您的节律模型。</div>
            </div>

            <el-tooltip content="Data Usage Policy" placement="left">
              <el-button
                class="infoBtn"
                :icon="InfoFilled"
                circle
                @click="infoOpen = true"
              />
            </el-tooltip>
          </div>

          <el-form
            ref="formRef"
            :model="form"
            :rules="rules"
            label-position="top"
            class="form"
            @submit.prevent
          >
            <el-form-item label="姓名 / 称谓" prop="name">
              <el-input
                v-model="form.name"
                placeholder="输入姓名 (可选)"
                clearable
              />
            </el-form-item>

            <div class="row">
              <el-form-item class="col" label="生理性别" prop="gender">
                <el-select
                  v-model="form.gender"
                  placeholder="请选择"
                  style="width: 100%"
                >
                  <el-option label="女 (Female)" value="female" />
                  <el-option label="男 (Male)" value="male" />
                  <el-option label="其他 (Non-binary)" value="nonbinary" />
                  <el-option
                    label="保密 (Prefer not to say)"
                    value="prefer_not_say"
                  />
                </el-select>
              </el-form-item>

              <el-form-item class="col" label="出生时间" prop="birthDatetime">
                <el-date-picker
                  v-model="form.birthDatetime"
                  type="datetime"
                  placeholder="选择出生时间"
                  style="width: 100%"
                  format="YYYY-MM-DD HH:mm"
                  value-format="YYYY-MM-DDTHH:mm"
                />
              </el-form-item>
            </div>

            <el-form-item label="夏令时校准">
              <div class="dstRow">
                <div class="dstText">
                  <div class="dstTitle">
                    启用夏令时?
                    <el-icon class="infoIcon" @click="dstInfoOpen = true">
                      <InfoFilled />
                    </el-icon>
                  </div>
                </div>
                <el-switch v-model="form.isDst" />
              </div>
            </el-form-item>

            <el-form-item label="原生坐标 (出生地)" prop="birthPlace">
              <el-input
                v-model="form.birthPlace"
                placeholder="点击设置出生地"
                readonly
                @click="openPlaceDialog('birth')"
              >
                <template #suffix>
                  <el-icon
                    class="clickableIcon"
                    @click.stop="openPlaceDialog('birth')"
                    ><Location
                  /></el-icon>
                </template>
              </el-input>
            </el-form-item>

            <el-form-item label="当前坐标 (居住地)" prop="residence">
              <el-input
                v-model="form.residence"
                placeholder="点击设置居住地"
                readonly
                @click="openPlaceDialog('residence')"
              >
                <template #suffix>
                  <el-icon
                    class="clickableIcon"
                    @click.stop="openPlaceDialog('residence')"
                    ><Location
                  /></el-icon>
                </template>
              </el-input>
            </el-form-item>

            <div class="actions">
              <el-button class="btn" @click="onClear">重置</el-button>
              <el-button class="btn primary" type="primary" @click="onSubmit"
                >启动运算</el-button
              >
            </div>
          </el-form>
        </el-card>
      </div>
    </div>

    <!-- Info Dialog -->
    <el-dialog
      v-model="infoOpen"
      title="为什么我们需要这些信息？"
      width="92%"
      :max-width="520"
    >
      <div class="dialogBody">
        <p>我们使用“时间结构”而非事件预测。</p>
        <p class="muted">
          出生时间决定了您的上升星座和宫位结构。时间越准确，节律校准越精确。
        </p>
      </div>
      <template #footer>
        <el-button type="primary" @click="infoOpen = false">知道了</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="dstInfoOpen"
      title="夏令时说明"
      width="92%"
      :max-width="520"
    >
      <div class="dstDialog">
        <p>请确认您出生时当地是否实行夏令时。</p>
      </div>
      <template #footer>
        <el-button type="primary" @click="dstInfoOpen = false">
          知道了
        </el-button>
      </template>
    </el-dialog>

    <!-- Place Dialog -->
    <el-dialog
      v-model="placeDialogOpen"
      :title="currentPlaceType === 'birth' ? '设置出生地点' : '设置现居地'"
      width="92%"
      :max-width="520"
      destroy-on-close
      class="place-dialog-wrapper"
    >
      <div class="placeDialog">
        <el-tabs v-model="currentLocationMode" class="modeTabs" type="card">
          <el-tab-pane label="自动搜索" name="auto">
            <div class="tabContent">
              <el-alert
                title="推荐使用"
                type="success"
                :closable="false"
                class="mb-3"
                show-icon
              >
                <template #default> 选择地区以自动填充经纬度。 </template>
              </el-alert>

              <el-form-item label="地区" required class="mt-4">
                <el-cascader
                  v-model="currentSelectedOptions"
                  :options="regionData"
                  placeholder="选择地区"
                  style="width: 100%"
                  @change="handleAddressChange"
                  clearable
                />
              </el-form-item>

              <div class="geoResult" v-if="currentLat && currentLon">
                <div class="geoItem">
                  <div class="geoLabel">纬度</div>
                  <div class="geoValue">{{ currentLat }}</div>
                </div>
                <div class="geoItem">
                  <div class="geoLabel">经度</div>
                  <div class="geoValue">{{ currentLon }}</div>
                </div>
                <div class="geoItem">
                  <div class="geoLabel">时区</div>
                  <div class="geoValue">
                    UTC{{ currentTimezone >= 0 ? "+" : ""
                    }}{{ currentTimezone }}
                  </div>
                </div>
              </div>

              <el-button
                type="primary"
                plain
                class="full-width-btn mt-4"
                :loading="geoLoading"
                @click="autoGeocode"
                :disabled="
                  currentPlaceType === 'birth'
                    ? !form.birthPlace
                    : !form.residence
                "
              >
                <el-icon class="mr-1"><Position /></el-icon>
                获取经纬度
              </el-button>
            </div>
          </el-tab-pane>

          <el-tab-pane label="自定义" name="custom">
            <div class="tabContent">
              <el-form-item label="地点名称" required class="mt-4">
                <el-input
                  v-if="currentPlaceType === 'birth'"
                  v-model="form.birthPlace"
                  placeholder="例如：北京"
                />
                <el-input
                  v-else
                  v-model="form.residence"
                  placeholder="例如：上海"
                />
              </el-form-item>

              <div class="row small-gap">
                <el-form-item label="纬度" required class="col">
                  <el-input
                    v-model="form.lat"
                    type="number"
                    placeholder="39.90"
                  />
                </el-form-item>
                <el-form-item label="经度" required class="col">
                  <el-input
                    v-model="form.lon"
                    type="number"
                    placeholder="116.40"
                  />
                </el-form-item>
              </div>

              <el-form-item label="时区" required>
                <el-select
                  v-model="form.timezone"
                  placeholder="选择时区"
                  style="width: 100%"
                >
                  <el-option
                    v-for="tz in commonTimezones"
                    :key="tz.value"
                    :label="tz.label"
                    :value="tz.value"
                  />
                </el-select>
              </el-form-item>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="placeDialogOpen = false">取消</el-button>
          <el-button type="primary" @click="savePlaceSettings">
            确认
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import {
  InfoFilled,
  Location,
  Position,
  Cpu,
  TrendCharts,
  Lock,
  CircleCheck,
  Sunny,
  Warning,
} from "@element-plus/icons-vue";
import { regionData, codeToText } from "element-china-area-data";
import { ElMessage } from "element-plus";
import { apiClient } from "@/config/api";

const router = useRouter();
const infoOpen = ref(false);
const dstInfoOpen = ref(false);
const formRef = ref();
const transitData = ref<any>(null);

const scrollToForm = () => {
  const el = document.getElementById("start-engine");
  if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
};

// --- Star Field Logic (CSS Box-Shadow Version) ---
const generateBoxShadows = (n: number) => {
  let value = "";
  const width =
    typeof window !== "undefined" ? Math.max(window.innerWidth, 2500) : 2500;
  for (let i = 0; i < n; i++) {
    const x = Math.floor(Math.random() * width);
    const y = Math.floor(Math.random() * 2000);
    value += `${x}px ${y}px #FFF`;
    if (i < n - 1) value += ", ";
  }
  return value;
};

const shadow1 = generateBoxShadows(100); // Small stars
const shadow2 = generateBoxShadows(50); // Medium stars
const shadow3 = generateBoxShadows(20); // Large stars

onMounted(async () => {
  // Fetch real-time transit
  try {
    const res = await apiClient.get("/transit/now");
    if (res.data.status === "success") {
      transitData.value = res.data.data;
    }
  } catch (e) {
    console.error("Failed to fetch transit data", e);
  }
});

// Dialog state
const placeDialogOpen = ref(false);
const currentPlaceType = ref<"birth" | "residence">("birth");
const geoLoading = ref(false);

const commonTimezones = [
  { label: "UTC-12:00", value: -12 },
  { label: "UTC-11:00", value: -11 },
  { label: "UTC-10:00", value: -10 },
  { label: "UTC-09:00", value: -9 },
  { label: "UTC-08:00 (Pacific)", value: -8 },
  { label: "UTC-07:00 (Mountain)", value: -7 },
  { label: "UTC-06:00 (Central)", value: -6 },
  { label: "UTC-05:00 (Eastern)", value: -5 },
  { label: "UTC-04:00", value: -4 },
  { label: "UTC-03:00", value: -3 },
  { label: "UTC-02:00", value: -2 },
  { label: "UTC-01:00", value: -1 },
  { label: "UTC+00:00 (GMT)", value: 0 },
  { label: "UTC+01:00 (CET)", value: 1 },
  { label: "UTC+02:00 (EET)", value: 2 },
  { label: "UTC+03:00", value: 3 },
  { label: "UTC+04:00", value: 4 },
  { label: "UTC+05:00", value: 5 },
  { label: "UTC+06:00", value: 6 },
  { label: "UTC+07:00", value: 7 },
  { label: "UTC+08:00 (CST)", value: 8 },
  { label: "UTC+09:00 (JST)", value: 9 },
  { label: "UTC+10:00", value: 10 },
  { label: "UTC+11:00", value: 11 },
  { label: "UTC+12:00", value: 12 },
];

const form = reactive({
  name: "",
  gender: "",
  birthDatetime: "",
  isDst: false,
  birthPlace: "",
  residence: "",
  birthLocationMode: "auto" as "auto" | "custom",
  residenceLocationMode: "auto" as "auto" | "custom",
  birthSelectedOptions: [] as string[],
  residenceSelectedOptions: [] as string[],
  lat: 0,
  lon: 0,
  timezone: 8.0,
  residenceLat: 0,
  residenceLon: 0,
  residenceTimezone: 8.0,
});

const currentLocationMode = computed({
  get: () =>
    currentPlaceType.value === "birth"
      ? form.birthLocationMode
      : form.residenceLocationMode,
  set: (val: "auto" | "custom") => {
    if (currentPlaceType.value === "birth") form.birthLocationMode = val;
    else form.residenceLocationMode = val;
  },
});

const currentSelectedOptions = computed({
  get: () =>
    currentPlaceType.value === "birth"
      ? form.birthSelectedOptions
      : form.residenceSelectedOptions,
  set: (val: string[]) => {
    if (currentPlaceType.value === "birth") form.birthSelectedOptions = val;
    else form.residenceSelectedOptions = val;
  },
});

const currentLat = computed(() =>
  currentPlaceType.value === "birth" ? form.lat : form.residenceLat,
);
const currentLon = computed(() =>
  currentPlaceType.value === "birth" ? form.lon : form.residenceLon,
);
const currentTimezone = computed(() =>
  currentPlaceType.value === "birth" ? form.timezone : form.residenceTimezone,
);

const openPlaceDialog = (type: "birth" | "residence") => {
  currentPlaceType.value = type;
  placeDialogOpen.value = true;
};

const handleAddressChange = (arr: string[]) => {
  if (arr && arr.length > 0) {
    const loc = arr.map((code) => codeToText[code]).join(" ");
    if (currentPlaceType.value === "birth") {
      form.birthPlace = loc;
    } else {
      form.residence = loc;
    }
  } else {
    if (currentPlaceType.value === "birth") {
      form.birthPlace = "";
    } else {
      form.residence = "";
    }
  }
};

const autoGeocode = async () => {
  const query =
    currentPlaceType.value === "birth" ? form.birthPlace : form.residence;
  if (!query) {
    ElMessage.warning("Please select or enter a place first");
    return;
  }

  geoLoading.value = true;
  try {
    const res = await apiClient.post("/geocode", {
      query,
    });
    if (res.data.status === "success") {
      const { lat, lon, timezone } = res.data.data;
      if (currentPlaceType.value === "birth") {
        form.lat = Number(lat);
        form.lon = Number(lon);
        form.timezone = Number(timezone);
        ElMessage.success("Found coordinates");
      } else {
        form.residenceLat = Number(lat);
        form.residenceLon = Number(lon);
        form.residenceTimezone = Number(timezone);
        ElMessage.success("Found coordinates");
      }
    } else {
      ElMessage.error("Location not found");
    }
  } catch (e) {
    console.error(e);
    const response = (e as {
      response?: { status?: number; data?: { detail?: string } };
    })?.response;
    const detail = response?.data?.detail;
    if (response?.status === 404) {
      ElMessage.error(detail || "Location not found. Try a more specific place.");
    } else if (response?.status === 502 || response?.status === 504) {
      ElMessage.error(
        detail || "Geocoding service is temporarily unavailable. Enter coordinates manually."
      );
    } else {
      ElMessage.error(detail || "Geocoding failed");
    }
  } finally {
    geoLoading.value = false;
  }
};

const savePlaceSettings = () => {
  if (currentLocationMode.value === "auto") {
    if (currentPlaceType.value === "birth" && (!form.lat || !form.lon)) {
      ElMessage.warning("Please get coordinates first");
      return;
    }
  }
  placeDialogOpen.value = false;
};

const validateLat = (_rule: any, value: any, callback: any) => {
  const n = Number(value);
  if (isNaN(n)) {
    callback(new Error("Invalid number"));
  } else if (n < -90 || n > 90) {
    callback(new Error("Must be -90 to 90"));
  } else {
    callback();
  }
};

const validateLon = (_rule: any, value: any, callback: any) => {
  const n = Number(value);
  if (isNaN(n)) {
    callback(new Error("Invalid number"));
  } else if (n < -180 || n > 180) {
    callback(new Error("Must be -180 to 180"));
  } else {
    callback();
  }
};

const rules = {
  name: [{ required: true, message: "Required", trigger: "blur" }],
  gender: [{ required: true, message: "Required", trigger: "change" }],
  birthDatetime: [{ required: true, message: "Required", trigger: "change" }],
  birthPlace: [{ required: true, message: "Required", trigger: "blur" }],
  residence: [{ required: true, message: "Required", trigger: "blur" }],
  lat: [
    { required: true, message: "Required", trigger: "blur" },
    { validator: validateLat, trigger: "blur" },
  ],
  lon: [
    { required: true, message: "Required", trigger: "blur" },
    { validator: validateLon, trigger: "blur" },
  ],
};

const loading = ref(false);

const onClear = () => {
  form.name = "";
  form.gender = "";
  form.birthDatetime = "";
  form.isDst = false;
  form.birthPlace = "";
  form.birthSelectedOptions = [];
  form.birthLocationMode = "auto";
  form.residence = "";
  form.residenceSelectedOptions = [];
  form.residenceLocationMode = "auto";
  form.lat = 0;
  form.lon = 0;
  form.timezone = 8.0;
  form.residenceLat = 0;
  form.residenceLon = 0;
  form.residenceTimezone = 8.0;
};

const onSubmit = async () => {
  if (!formRef.value) return;

  await formRef.value.validate(async (valid: boolean) => {
    if (valid) {
      loading.value = true;
      try {
        if (!form.birthPlace) {
          alert("Please set birth place");
          loading.value = false;
          return;
        }
        if (form.birthLocationMode === "auto") {
          if (!form.lat || !form.lon) {
            alert("Please get coordinates first");
            loading.value = false;
            return;
          }
        }
        if (
          form.birthLocationMode === "custom" &&
          (form.timezone === undefined || form.timezone === null)
        ) {
          alert("Please set timezone");
          loading.value = false;
          return;
        }

        const birthTimeLocal = form.birthDatetime.length === 16
          ? `${form.birthDatetime}:00`
          : form.birthDatetime;

        const payload = {
          birth_time: birthTimeLocal,
          lat: Number(form.lat),
          lon: Number(form.lon),
          timezone: Number(form.timezone),
        };

        const response = await apiClient.post("/analyze", payload);

        if (response.data.status === "success") {
          const reportId = response.data.report_id;
          if (reportId) {
            router.push({ name: "report", query: { id: reportId } });
          } else {
            router.push({ name: "report" });
          }
        } else {
          console.error("API Error:", response.data);
          alert("Analysis failed");
        }
      } catch (error) {
        console.error("Request Error:", error);
        alert("Request failed");
      } finally {
        loading.value = false;
      }
    }
  });
};
</script>

<style lang="less" scoped>
@bg: var(--bg-main);
@card-bg: var(--bg-card);
@text: var(--text-primary);
@muted: var(--text-muted);
@border: var(--border-light);
@primary: var(--color-gold);
@primary-rgb: var(--color-gold-rgb);
@accent: var(--color-indigo);
@accent-rgb: var(--color-indigo-rgb);

.page {
  min-height: 100vh;
  background: var(--bg-main);
  color: @text;
  font-family: var(--font-sans);
  position: relative;
  overflow-x: hidden;
}

.star-container {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
  overflow: hidden;
  pointer-events: none;
  opacity: 0.6; /* Subtler stars */
}
/* ... keep star animation ... */
.star-layer {
  position: absolute;
  top: 0;
  left: 0;
  background: transparent;

  &.layer-1 {
    width: 1px;
    height: 1px;
    box-shadow: var(--shadow-1);
    animation: animStar 100s linear infinite; /* Slower */
    opacity: 0.8;
    &::after {
      content: " ";
      position: absolute;
      top: 2000px;
      width: 1px;
      height: 1px;
      box-shadow: var(--shadow-1);
    }
  }

  &.layer-2 {
    width: 2px;
    height: 2px;
    box-shadow: var(--shadow-2);
    animation: animStar 150s linear infinite;
    opacity: 0.5;
    &::after {
      content: " ";
      position: absolute;
      top: 2000px;
      width: 2px;
      height: 2px;
      box-shadow: var(--shadow-2);
    }
  }

  &.layer-3 {
    width: 3px;
    height: 3px;
    box-shadow: var(--shadow-3);
    animation: animStar 200s linear infinite;
    opacity: 0.3;
    &::after {
      content: " ";
      position: absolute;
      top: 2000px;
      width: 3px;
      height: 3px;
      box-shadow: var(--shadow-3);
    }
  }
}

@keyframes animStar {
  from {
    transform: translateY(0);
  }
  to {
    transform: translateY(-2000px);
  }
}

.wrap {
  position: relative;
  z-index: 1;
  max-width: 1200px; /* Wider for "Orderly" feel */
  margin: 0 auto;
  padding: 64px 20px 80px;
}

/* Hero */
.hero {
  text-align: center;
  padding: 100px 0 80px;

  .title {
    margin: 0 0 24px;
    font-size: 64px; /* Larger */
    line-height: 1.3;
    font-family: var(--font-sans);
    font-weight: 700;
    letter-spacing: -0.03em;
    color: #fff;
    background: linear-gradient(180deg, #fff 0%, #94a3b8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }

  .subtitle {
    margin: 0 auto 40px;
    max-width: 560px;
    font-size: 18px;
    color: @muted;
    line-height: 1.6;
    font-weight: 400;
  }
}

.cta-btn-large {
  padding: 10px 48px;
  font-size: 18px;
  font-family: var(--font-sans);
  font-weight: 600;
  background: @primary;
  color: #000; /* Contrast on Gold */
  border: none;
  border-radius: 999px; /* Capsule */
  box-shadow: 0 0 24px rgba(@primary-rgb, 0.3);
  transition: all 0.3s;

  &:hover {
    box-shadow: 0 0 40px rgba(@primary-rgb, 0.5);
    transform: translateY(-2px);
    filter: brightness(1.1);
  }
}

/* Transit Ticker */
.transit-ticker-container {
  width: 100%;
  overflow: hidden;
  margin: 48px 0;
  border-top: 1px solid @border;
  border-bottom: 1px solid @border;
  padding: 16px 0;
  background: rgba(255, 255, 255, 0.02);
  backdrop-filter: blur(5px);
}

.transit-ticker-track {
  display: flex;
  gap: 48px;
  animation: scroll 30s linear infinite; /* Slower */
  white-space: nowrap;
}

.ticker-item {
  color: @muted;
  font-size: 14px;
  font-family: var(--font-mono); /* Monospace for data */
  display: flex;
  align-items: center;
  gap: 12px;

  .dot {
    color: @accent; /* Indigo dot */
    font-size: 8px;
  }
}

@keyframes scroll {
  0% {
    transform: translateX(0);
  }
  100% {
    transform: translateX(-50%);
  }
}

/* Section Common */
.section {
  padding: 80px 0;

  .section-title {
    font-size: 32px;
    text-align: center;
    margin-bottom: 56px;
    font-family: var(--font-sans);
    font-weight: 600;
    letter-spacing: -0.02em;
  }
}

/* Bento Grid */
.bento-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;

  .bento-card {
    background: @card-bg;
    border: 1px solid @border;
    border-radius: var(--radius);
    padding: 32px;
    transition: all 0.3s;
    position: relative;
    overflow: hidden;

    &:hover {
      transform: translateY(-2px);
      border-color: rgba(@primary-rgb, 0.3);
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
    }

    .card-icon {
      font-size: 24px;
      margin-bottom: 20px;
      color: @accent;
    }

    h3 {
      margin: 0 0 12px;
      font-size: 20px;
      font-family: var(--font-sans);
      font-weight: 600;
    }

    p {
      margin: 0;
      color: @muted;
      line-height: 1.6;
      font-size: 15px;
    }

    &.large {
      grid-row: span 2;
      background: linear-gradient(
        145deg,
        rgba(255, 255, 255, 0.03) 0%,
        rgba(255, 255, 255, 0.01) 100%
      );

      .card-icon {
        color: @primary;
      }
    }
  }
}

/* Showcase */
.showcase-box {
  background: rgba(255, 255, 255, 0.02);
  border-radius: var(--radius);
  padding: 48px;
  text-align: center;
  border: 1px solid @border;

  .chart-preview-mock {
    height: 180px;
    position: relative;
    border-bottom: 1px solid @border;
    margin-bottom: 24px;

    .mock-line {
      position: absolute;
      top: 50%;
      left: 0;
      width: 100%;
      height: 2px;
      background: rgba(@accent-rgb, 0.3); /* Indigo line */
    }

    .mock-candles {
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      display: flex;
      justify-content: space-around;
      align-items: center;

      .candle {
        width: 6px;
        background: @accent; /* Indigo candles */
        border-radius: 2px;
        opacity: 0.8;

        &.down {
          background: rgba(@accent-rgb, 0.4);
        }
      }
    }
  }

  .showcase-text {
    font-family: var(--font-mono);
    color: @muted;
    font-size: 14px;
    letter-spacing: 0.05em;
  }
}

/* Form Section */
.engine-section {
  padding: 60px 0;
  margin-top: 40px;
}

.form-card {
  background: rgba(15, 23, 42, 0.6); /* Darker, slightly blue */
  backdrop-filter: blur(20px);
  border: 1px solid @border;
  border-radius: var(--radius);
  color: #fff;

  :deep(.el-card__body) {
    padding: 40px;
  }
}

.head {
  display: flex;
  justify-content: space-between;
  margin-bottom: 32px;
  border-bottom: 1px solid @border;
  padding-bottom: 20px;

  .headTitle {
    font-size: 24px;
    font-family: var(--font-sans);
    font-weight: 600;
  }
  .headHint {
    color: @muted;
    font-size: 14px;
    margin-top: 8px;
  }
}

.infoBtn {
  width: 36px;
  height: 36px;
  padding: 0 !important;
  border-radius: 50% !important;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid @border;
  color: @muted;
  transition: all 0.2s;
  &:hover {
    background: @primary;
    color: #000;
    border-color: @primary;
  }
}

.form {
  :deep(.el-form-item__label) {
    color: @muted;
    font-size: 13px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    padding-bottom: 8px;
  }

  :deep(.el-input__wrapper),
  :deep(.el-select__wrapper),
  :deep(.el-textarea__inner) {
    background-color: rgba(255, 255, 255, 0.03) !important;
    box-shadow: none !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 8px;
    transition: all 0.2s;
    padding: 4px 12px;

    &:hover,
    &.is-focus {
      border-color: @primary !important;
      background-color: rgba(255, 255, 255, 0.08) !important;
    }
  }

  :deep(.el-input__inner) {
    color: #fff !important;
    font-family: var(--font-mono);
    &[readonly] {
      cursor: pointer;
    }
  }

  :deep(.el-select__selected-item) {
    color: #fff !important;
  }

  :deep(.el-input__icon),
  :deep(.el-select__caret) {
    color: @muted;
  }

  .clickableIcon {
    cursor: pointer;
    color: @muted;
    font-size: 16px;
    transition: color 0.2s;
    &:hover {
      color: @primary;
    }
  }
}

.row {
  display: flex;
  gap: 24px;
  .col {
    flex: 1;
  }
}

.dstRow {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: rgba(255, 255, 255, 0.02);
  border-radius: 12px;
  border: 1px solid @border;
  color: @text;

  .dstTitle {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 500;

    .infoIcon {
      cursor: pointer;
      color: @muted;
      transition: color 0.2s;
      &:hover {
        color: @primary;
      }
    }
  }
}

.actions {
  display: flex;
  gap: 24px;
  margin-top: 40px;

  .btn {
    flex: 1;
    padding: 20px;
    font-size: 16px;
    border-radius: 12px;
    font-weight: 600;
  }

  .primary {
    background: @primary;
    color: #000;
    border: none;
    transition: all 0.2s;
    &:hover {
      filter: brightness(1.1);
      transform: translateY(-1px);
    }
  }
}

@media (max-width: 600px) {
  .bento-grid {
    grid-template-columns: 1fr;
    grid-template-rows: auto;
  }
  .row {
    flex-direction: column;
    gap: 0;
  }
  .title {
    font-size: 40px !important;
  }
}
@media (max-width: 900px) {
  .bento-grid {
    grid-template-columns: 1fr;
    .bento-card.large {
      grid-row: span 1;
    }
  }
}

.transit-ticker-container {
  margin: 40px auto;
  max-width: 1080px;
  background: var(--bg-card);
  border: 1px solid var(--border-light);
  border-radius: 999px;
  overflow: hidden;
  height: 20px;
  display: flex;
  align-items: center;
  position: relative;

  .transit-ticker-track {
    display: flex;
    white-space: nowrap;
    animation: marquee 30s linear infinite;

    &:hover {
      animation-play-state: paused;
    }
  }

  .ticker-group {
    display: flex;
    align-items: center;
  }

  .ticker-item {
    display: inline-flex;
    align-items: center;
    padding: 0 24px;
    font-size: 14px;
    color: var(--text-secondary);

    .dot {
      margin-right: 8px;
      font-size: 12px;

      &.gold {
        color: var(--gold);
      }
      &.indigo {
        color: var(--indigo);
      }
    }

    .label {
      color: var(--text);
      font-weight: 500;
      margin-right: 4px;
    }
  }

  .separator {
    color: rgba(255, 255, 255, 0.1);
  }
}

@keyframes marquee {
  0% {
    transform: translateX(0);
  }
  100% {
    transform: translateX(-50%);
  }
}

.showcase-section-v2 {
  margin-top: 100px;
  padding: 80px 0;
  background: rgba(15, 23, 42, 0.3);
  border-top: 1px solid var(--border);
  border-bottom: 1px solid var(--border);

  .showcase-container {
    max-width: 1200px;
    margin: 0 auto;
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 64px;
    align-items: center;

    @media (max-width: 900px) {
      grid-template-columns: 1fr;
    }
  }

  .sync-animation {
    position: relative;
    height: 450px;
  }

  .sync-animation {
    perspective: 1200px; /* Creates the 3D space */
    display: flex;
    // align-items: center;
    justify-content: center;
    transform-style: preserve-3d;
  }

  .mock-pc {
    --tw-bg-opacity: 1;
    background-color: rgb(30 41 59 / var(--tw-bg-opacity, 1));

    border: 1px solid var(--border-light);
    border-radius: 12px;
    padding: 12px;
    width: 95%; /* Wider PC for dominance */
    height: 280px; /* Taller PC */
    overflow: hidden;
    position: relative;
    box-shadow: 0 40px 80px -12px rgba(0, 0, 0, 0.7);
    transform: rotateY(4deg) rotateX(2deg) translateZ(-40px);
    transition: transform 0.6s cubic-bezier(0.2, 0.8, 0.2, 1);

    &:hover {
      transform: rotateY(2deg) rotateX(1deg) translateZ(-30px);
    }

    .window-controls {
      display: flex;
      gap: 6px;
      margin-bottom: 20px;
      padding-left: 4px;
      .ctrl {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        &.red {
          background: #ef4444;
        }
        &.yellow {
          background: #eab308;
        }
        &.green {
          background: #22c55e;
        }
      }
    }

    .pc-content {
      padding: 16px;
      height: calc(100% - 40px);
      display: flex;
      flex-direction: column;
    }

    .skeleton-line {
      height: 4px;
      background: rgba(255, 255, 255, 0.1);
      border-radius: 2px;
    }

    .chart-bars {
      display: flex;
      gap: 16px; /* Wider gap for larger scale */
      align-items: flex-end;
      height: 180px; /* Taller charts */
      margin-top: auto;
      margin-bottom: 24px;
      padding: 0 10px;

      .bar {
        flex: 1;
        max-width: 8px; /* Slightly thicker bars */
        background: linear-gradient(
          to top,
          rgba(@primary-rgb, 0.2),
          rgba(@primary-rgb, 0.8)
        );
        border-radius: 4px;
        position: relative;
        transition: height 0.5s ease;

        &::after {
          content: "";
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          box-shadow: 0 0 12px rgba(@primary-rgb, 0.4);
          border-radius: 4px;
        }
      }
    }

    .terminal-text {
      font-family: var(--font-mono);
      font-size: 11px; /* Slightly larger text */
      color: rgba(148, 163, 184, 0.7);
      letter-spacing: 0.5px;
    }
  }

  .mock-phone {
    position: absolute;
    bottom: 10px;
    right: 20px; /* Tighter overlap */
    width: 170px; /* Slimmer phone */
    height: 340px; /* Modern aspect ratio */
    background: var(--bg-main);
    border: 5px solid #334155;
    border-radius: 28px;
    overflow: hidden;
    box-shadow: -25px 35px 70px rgba(0, 0, 0, 0.9);
    z-index: 10;
    transform: rotateY(-6deg) translateZ(50px);
    transition: transform 0.6s cubic-bezier(0.2, 0.8, 0.2, 1);

    &:hover {
      transform: rotateY(-3deg) translateZ(60px) scale(1.02);
    }

    .phone-screen {
      padding: 20px 14px; /* Tighter padding */
      height: 100%;
      background: var(--bg-main);
      display: flex;
      flex-direction: column;
      gap: 10px;
    }

    .notification-card {
      background: rgba(255, 255, 255, 0.08);
      backdrop-filter: blur(12px);
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 16px;
      padding: 14px;
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
      animation: slideInDown 0.8s cubic-bezier(0.2, 0.8, 0.2, 1) forwards;

      .notif-header {
        display: flex;
        justify-content: space-between;
        margin-bottom: 8px;
        font-size: 9px;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.5px;
      }

      .notif-title {
        font-size: 11px;
        font-weight: 600;
        color: var(--gold);
        margin-bottom: 4px;
      }
      .notif-body {
        font-size: 12px;
        color: #f1f5f9;
        line-height: 1.4;
      }
    }

    .widget-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 6px; /* Tighter gap */
    }

    .widget-card {
      background: var(--bg-card);
      border: 1px solid var(--border-light);
      border-radius: 12px;
      padding: 10px 8px; /* Reduced padding */

      &.small {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 80px; /* Compact height */
      }

      &.medium {
        margin-top: 4px;
        padding: 10px;
      }

      .widget-label {
        font-size: 9px;
        color: #64748b;
        margin-bottom: 6px;
        align-self: flex-start;
      }

      .value-text {
        font-size: 14px;
        font-weight: bold;
        color: #fff;
        margin-top: 2px;
      }

      .value-text-sm {
        font-size: 10px;
        color: #cbd5e1;
        margin-top: 4px;
      }

      /* Energy Ring */
      .energy-ring {
        position: relative;
        width: 36px; /* Smaller ring */
        height: 36px;
        border-radius: 50%;
        background: conic-gradient(
          var(--gold) calc(var(--p) * 1%),
          rgba(255, 255, 255, 0.1) 0
        );
        display: flex;
        align-items: center;
        justify-content: center;

        &::before {
          content: "";
          position: absolute;
          inset: 3px;
          background: #1e293b;
          border-radius: 50%;
        }

        .value-text {
          position: relative;
          z-index: 1;
          font-size: 9px;
          margin: 0;
        }
      }

      /* Focus Bar */
      .focus-bar {
        width: 100%;
        height: 4px;
        background: rgba(255, 255, 255, 0.1);
        border-radius: 2px;
        overflow: hidden;
        margin-top: 4px;

        .bar-fill {
          height: 100%;
          background: var(--indigo);
        }
      }

      /* Next Event */
      .next-event {
        display: flex;
        align-items: center;
        gap: 12px;

        .time {
          font-family: var(--font-mono);
          font-size: 14px;
          color: var(--gold);
        }
        .desc {
          font-size: 12px;
          color: #cbd5e1;
        }
      }
    }
  }

  @keyframes slideInDown {
    from {
      opacity: 0;
      transform: translateY(-20px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  .showcase-info {
    .section-title-large {
      font-size: 36px;
      font-weight: 700;
      margin-bottom: 24px;
      background: var(--grad-highlight);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      font-family: var(--font-sans);
    }

    .section-desc {
      color: #94a3b8;
      margin-bottom: 32px;
      line-height: 1.7;
      font-size: 16px;
    }

    .feature-list {
      list-style: none;
      padding: 0;
      li {
        display: flex;
        align-items: center;
        margin-bottom: 16px;
        color: #cbd5e1;
        font-size: 16px;

        .icon-gold {
          color: var(--gold);
          margin-right: 12px;
          font-size: 20px;
        }
      }
    }
  }
}
</style>
