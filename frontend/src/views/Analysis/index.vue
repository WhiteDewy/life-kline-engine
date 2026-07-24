<template>
  <div class="analysis-page">
    <div class="glow glow-a"></div>
    <div class="glow glow-b"></div>

    <div class="page-content">
      <!-- ═══ 加载态 ═══ -->
      <div class="loading-view" v-if="loading">
        <div class="loading-crystal"></div>
        <h2 class="loading-title">正在绘制你的星盘...</h2>
        <div class="loading-stages">
          <div class="loading-stage" v-for="(stage, i) in loadingStages" :key="i"
            :class="{ active: loadingStageIndex >= i, current: loadingStageIndex === i }">
            <span class="stage-dot"></span>
            <span>{{ stage }}</span>
          </div>
        </div>
      </div>

      <!-- ═══ 表单 ═══ -->
      <div class="form-view" v-else>
        <div class="form-header">
          <span class="form-emoji">{{ formEmoji }}</span>
          <h1 class="form-title">{{ formTitle }}</h1>
          <p class="form-sub">帮我画出你出生那一刻的天空——那是你人生的出厂设置</p>
        </div>

        <div class="form-card">
          <!-- 称呼 + 性别 -->
          <div class="field-row">
            <div class="field field--name">
              <label class="field-label">你的称呼</label>
              <input v-model="form.name" class="field-input" placeholder="怎么称呼你？" />
            </div>
            <div class="field field--gender">
              <label class="field-label">性别</label>
              <div class="gender-toggle">
                <button :class="{ active: form.gender === '女' }" @click="form.gender = '女'">♀ 女</button>
                <button :class="{ active: form.gender === '男' }" @click="form.gender = '男'">♂ 男</button>
              </div>
            </div>
          </div>

          <!-- 出生日期 -->
          <div class="field">
            <label class="field-label">出生日期和时间</label>
            <el-date-picker
              v-model="form.birthDatetime"
              type="datetime"
              style="width: 100%"
              format="YYYY-MM-DD HH:mm"
              value-format="YYYY-MM-DDTHH:mm"
              placeholder="选择你的生日和时间"
              popper-class="heal-popper"
            />
          </div>

          <!-- 出生地点 -->
          <div class="field">
            <label class="field-label">出生地点</label>
            <div class="place-input" @click="placeDialogOpen = true">
              <span v-if="form.birthPlace" class="place-text">{{ form.birthPlace }}</span>
              <span v-else class="place-placeholder">点击设置出生地点</span>
              <span class="place-arrow">📍</span>
            </div>
            <div class="coord-preview" v-if="hasCoordinates">
              <span>{{ latitudePreview }}</span>
              <span>·</span>
              <span>{{ longitudePreview }}</span>
              <span>·</span>
              <span>{{ timezonePreview }}</span>
            </div>
          </div>

          <!-- CTA -->
          <button class="submit-btn" :disabled="!canSubmit" @click="onSubmit">
            {{ ctaText }}
          </button>
          <p class="submit-hint">生成报告大约需要 10 秒</p>

          <!-- 示例入口 -->
          <div class="demo-entry" v-if="showExamples">
            <span class="demo-divider">或者</span>
            <button class="demo-btn" v-for="ex in examples" :key="ex.key"
              @click="openExample(ex)">
              看看 {{ ex.name }} 的报告 →
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══ 地点弹窗（逻辑不变） ═══ -->
    <el-dialog v-model="placeDialogOpen" title="设置出生地点" width="92%" :max-width="480" destroy-on-close>
      <div class="place-dialog">
        <el-tabs v-model="locationMode">
          <el-tab-pane label="自动获取" name="auto">
            <el-form-item label="出生地区">
              <el-cascader v-model="selectedOptions" :options="regionData" clearable filterable popper-class="heal-popper"
                placeholder="省 / 市 / 区" style="width: 100%" @change="handleAddressChange" />
            </el-form-item>
            <el-button type="primary" plain :loading="geoLoading" :disabled="!form.birthPlace" @click="autoGeocode">
              自动获取坐标
            </el-button>
          </el-tab-pane>
          <el-tab-pane label="手动填写" name="custom">
            <el-form-item label="地点名称">
              <el-input v-model="form.birthPlace" placeholder="例如：北京市朝阳区" />
            </el-form-item>
            <div class="manual-grid">
              <div class="manual-field">
                <label>纬度</label>
                <div class="manual-row">
                  <el-input-number v-model="manualCoords.latDegrees" :min="0" :max="90" controls-position="right" size="small" />
                  <span>°</span>
                  <el-input-number v-model="manualCoords.latMinutes" :min="0" :max="59" controls-position="right" size="small" />
                  <span>′</span>
                  <el-select v-model="manualCoords.latDirection" size="small" style="width:70px">
                    <el-option label="N" value="N" /><el-option label="S" value="S" />
                  </el-select>
                </div>
              </div>
              <div class="manual-field">
                <label>经度</label>
                <div class="manual-row">
                  <el-input-number v-model="manualCoords.lonDegrees" :min="0" :max="180" controls-position="right" size="small" />
                  <span>°</span>
                  <el-input-number v-model="manualCoords.lonMinutes" :min="0" :max="59" controls-position="right" size="small" />
                  <span>′</span>
                  <el-select v-model="manualCoords.lonDirection" size="small" style="width:70px">
                    <el-option label="E" value="E" /><el-option label="W" value="W" />
                  </el-select>
                </div>
              </div>
            </div>
            <el-form-item label="时区">
              <el-select v-model="form.timezone" style="width:100%" placeholder="选择时区">
                <el-option v-for="tz in commonTimezones" :key="tz.value" :label="tz.label" :value="tz.value" />
              </el-select>
            </el-form-item>
          </el-tab-pane>
        </el-tabs>
      </div>
      <template #footer>
        <el-button @click="placeDialogOpen = false">取消</el-button>
        <el-button type="primary" @click="savePlaceSettings">保存地点</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { regionData, codeToText } from "element-china-area-data";
import { apiClient } from "@/config/api";
import { FEATURED_EXAMPLES, HOMEPAGE_EXAMPLE_VISIBLE } from "@/config/examples";
import { getTestUserProfileByKey } from "@/config/testProfiles";
import { composeCoordinateValue, formatCoordinateLabel, formatTimezoneLabel, splitCoordinateParts } from "@/utils/coordinates";
import { textToRegionCodes } from "@/utils/regions";

const route = useRoute();
const router = useRouter();
const showExamples = HOMEPAGE_EXAMPLE_VISIBLE;
const examples = FEATURED_EXAMPLES;

const loading = ref(false);
const loadingStageIndex = ref(-1);
let loadingStageTimer: ReturnType<typeof setInterval> | null = null;
const loadingStages = ["计算星盘…", "分析性格结构…", "匹配人生阶段…", "整理专属解读…"];

const placeDialogOpen = ref(false);
const locationMode = ref<"auto" | "custom">("auto");
const selectedOptions = ref<string[]>([]);
const geoLoading = ref(false);
const manualCoords = reactive({ latDegrees: 0, latMinutes: 0, latDirection: "N" as "N" | "S", lonDegrees: 0, lonMinutes: 0, lonDirection: "E" as "E" | "W" });

const DEFAULT = { name: "夏天", gender: "女", birthDatetime: "1991-03-21T09:25", birthPlace: "山西省陵川县附城镇青杨庄村", lat: 35.7, lon: 113.35, timezone: 8 };
const form = reactive({ ...DEFAULT });

const formEmoji = computed(() => {
  const t = String(route.params.type || "");
  if (t === "monthly_lunar_return") return "🌙";
  return "🪐";
});
const formTitle = computed(() => {
  const t = String(route.params.type || "");
  if (t === "monthly_lunar_return") return "本月运势";
  return "认识你自己";
});
const ctaText = computed(() => {
  const t = String(route.params.type || "");
  if (t === "monthly_lunar_return") return "看看这个月 🌙";
  return "开始探索 🪐";
});

const hasCoordinates = computed(() => Number.isFinite(Number(form.lat)) && Number.isFinite(Number(form.lon)));
const latitudePreview = computed(() => formatCoordinateLabel(Number(form.lat), "latitude"));
const longitudePreview = computed(() => formatCoordinateLabel(Number(form.lon), "longitude"));
const timezonePreview = computed(() => formatTimezoneLabel(Number(form.timezone)));
const canSubmit = computed(() => form.birthDatetime && form.birthPlace && hasCoordinates.value);

const timezonePresets = [-12,-11,-10,-9,-8,-7,-6,-5,-4,-3,-2,-1,0,1,2,3,4,5,6,7,8,9,10,11,12];
const commonTimezones = timezonePresets.map(v => ({ label: formatTimezoneLabel(v), value: v }));

function handleAddressChange(codes: string[]) {
  if (!codes?.length) { form.birthPlace = ""; return; }
  form.birthPlace = codes.map(c => codeToText[c]).join(" ");
}
function syncManualCoordsFromForm() {
  const lat = splitCoordinateParts(Number(form.lat), "latitude");
  const lon = splitCoordinateParts(Number(form.lon), "longitude");
  manualCoords.latDegrees = lat.degrees; manualCoords.latMinutes = lat.minutes; manualCoords.latDirection = lat.direction as "N" | "S";
  manualCoords.lonDegrees = lon.degrees; manualCoords.lonMinutes = lon.minutes; manualCoords.lonDirection = lon.direction as "E" | "W";
}
function syncFormCoordsFromManual() {
  form.lat = composeCoordinateValue(manualCoords.latDegrees, manualCoords.latMinutes, manualCoords.latDirection, "latitude");
  form.lon = composeCoordinateValue(manualCoords.lonDegrees, manualCoords.lonMinutes, manualCoords.lonDirection, "longitude");
}
async function autoGeocode() {
  if (!form.birthPlace) { ElMessage.warning("请先选择出生地点"); return; }
  geoLoading.value = true;
  try {
    const r = await apiClient.post("/geocode", { query: form.birthPlace });
    if (r.data.status === "success") {
      form.lat = Number(r.data.data.lat); form.lon = Number(r.data.data.lon); form.timezone = Number(r.data.data.timezone);
      syncManualCoordsFromForm(); ElMessage.success("已获取坐标");
    } else { ElMessage.error("没有找到对应地点"); }
  } catch { ElMessage.error("定位失败，请手动填写"); }
  finally { geoLoading.value = false; }
}
function savePlaceSettings() {
  if (!form.birthPlace) { ElMessage.warning("请先设置出生地点"); return; }
  if (locationMode.value === "custom") syncFormCoordsFromManual();
  if (!hasCoordinates.value) { ElMessage.warning("请先获取或填写坐标"); return; }
  placeDialogOpen.value = false;
}
function resetForm() {
  const key = typeof route.query.profile === "string" ? route.query.profile : undefined;
  const p = (key ? getTestUserProfileByKey(key) : null) || DEFAULT;
  Object.assign(form, p);
  syncManualCoordsFromForm();
  // 恢复 cascader 选中状态
  if (p && p !== DEFAULT && form.birthPlace) {
    const codes = textToRegionCodes(form.birthPlace);
    selectedOptions.value = codes || [];
  } else {
    selectedOptions.value = [];
  }
}
async function onSubmit() {
  if (!canSubmit.value) return;
  loading.value = true; loadingStageIndex.value = 0;
  loadingStageTimer = setInterval(() => { if (loadingStageIndex.value < loadingStages.length - 1) loadingStageIndex.value++; }, 1500);
  try {
    const birthTime = form.birthDatetime.length === 16 ? `${form.birthDatetime}:00` : form.birthDatetime;
    const r = await apiClient.post("/analyses", {
      analysis_type: String(route.params.type || "natal_blueprint"),
      subjects: [{ name: form.name || undefined, gender: form.gender, birth_time: birthTime, lat: Number(form.lat), lon: Number(form.lon), timezone: Number(form.timezone) }],
    });
    if (r.data.status === "success" && r.data.report_id) {
      loadingStageIndex.value = loadingStages.length;
      const target = String(route.params.type) === "monthly_lunar_return" ? "monthly-return" : "report";
      setTimeout(() => router.push({ name: target, params: { id: r.data.report_id } }), 400);
    } else { ElMessage.error("报告生成失败"); }
  } catch { ElMessage.error("请求失败"); }
  finally { loading.value = false; if (loadingStageTimer) { clearInterval(loadingStageTimer); loadingStageTimer = null; } loadingStageIndex.value = -1; }
}
function openExample(ex: typeof examples[0]) {
  router.push({ name: "report", query: { example: ex.key, analysis: "natal_blueprint" } });
}
watch(placeDialogOpen, (open) => { if (open) syncManualCoordsFromForm(); });
watch(() => route.query.profile, resetForm);
onMounted(resetForm);
</script>

<style scoped>
.analysis-page {
  min-height: calc(100vh - var(--h-header));
  position: relative; overflow: hidden;
  background: linear-gradient(180deg, #FFF5EE 0%, #FFEFD5 40%, #FFF0F5 80%, #F8F4FF 100%);
}
.glow { position: absolute; border-radius: 50%; filter: blur(100px); pointer-events: none; }
.glow-a { width: 260px; height: 260px; top: -40px; right: -60px; background: rgba(255,154,139,0.10); }
.glow-b { width: 200px; height: 200px; bottom: 60px; left: -80px; background: rgba(240,192,96,0.08); }

.page-content { position: relative; z-index: 1; max-width: 440px; margin: 0 auto; padding: 36px 20px 60px; }

/* ── 加载态 ── */
.loading-view { text-align: center; padding: 80px 20px; }
.loading-crystal {
  width: 80px; height: 80px; border-radius: 50%; margin: 0 auto 20px;
  background: radial-gradient(circle at 35% 35%, rgba(255,255,255,0.8), rgba(200,180,220,0.35), rgba(150,120,200,0.15));
  box-shadow: 0 0 40px rgba(180,150,220,0.2);
  animation: orb-pulse 2s ease-in-out infinite;
}
@keyframes orb-pulse { 0%,100%{transform:scale(1)} 50%{transform:scale(1.06)} }
.loading-title { font-size: 18px; font-weight: 700; color: #4a3728; margin: 0 0 24px; }
.loading-stages { display: flex; flex-direction: column; gap: 10px; align-items: center; }
.loading-stage { display: flex; align-items: center; gap: 10px; font-size: 13px; color: #c4b5a5; opacity: 0.3; transition: all 0.4s; }
.loading-stage.active { opacity: 1; }
.loading-stage.current { color: #4a3728; font-weight: 600; }
.stage-dot { width: 6px; height: 6px; border-radius: 50%; background: #c4b5a5; flex-shrink: 0; }
.loading-stage.current .stage-dot { background: #ff9a8b; box-shadow: 0 0 8px rgba(255,154,139,0.5); animation: dot-pulse 1s ease-in-out infinite; }
@keyframes dot-pulse { 0%,100%{transform:scale(1)} 50%{transform:scale(1.8)} }

/* ── 表单头 ── */
.form-view { display: flex; flex-direction: column; gap: 20px; }
.form-header { text-align: center; }
.form-emoji { font-size: 36px; display: block; margin-bottom: 8px; }
.form-title { font-size: 24px; font-weight: 800; color: #4a3728; margin: 0 0 6px; letter-spacing: 0.03em; }
.form-sub { font-size: 13px; color: #8b7355; margin: 0; }

/* ── 表单卡片 ── */
.form-card {
  padding: 28px 24px; border-radius: 24px;
  background: rgba(255,255,255,0.82); backdrop-filter: blur(12px);
  border: 1px solid rgba(0,0,0,0.05); box-shadow: 0 4px 24px rgba(0,0,0,0.04);
  display: flex; flex-direction: column; gap: 18px;
}

/* ── 字段 ── */
.field { display: flex; flex-direction: column; gap: 6px; }
.field-label { font-size: 13px; font-weight: 700; color: #6b5744; }
.field-input {
  padding: 12px 16px; border-radius: 14px; border: 1px solid rgba(0,0,0,0.08);
  background: rgba(0,0,0,0.02); font-size: 15px; color: #4a3728; outline: none; font-family: inherit;
  transition: border-color 0.2s; width: 100%; box-sizing: border-box;
}
.field-input:focus { border-color: #ff9a8b; }
.field-input::placeholder { color: #c4b5a5; }

.field-row { display: grid; grid-template-columns: 1fr 120px; gap: 14px; }

/* 性别切换 */
.gender-toggle { display: flex; border-radius: 14px; overflow: hidden; border: 1px solid rgba(0,0,0,0.08); }
.gender-toggle button {
  flex: 1; padding: 10px 12px; border: none; background: transparent;
  font-size: 14px; font-weight: 600; color: #a89880; cursor: pointer; font-family: inherit; transition: all 0.2s;
}
.gender-toggle button.active { background: rgba(255,154,139,0.12); color: #4a3728; }

/* 地点 */
.place-input {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px 16px; border-radius: 14px; border: 1px solid rgba(0,0,0,0.08);
  background: rgba(0,0,0,0.02); cursor: pointer; transition: border-color 0.2s;
}
.place-input:hover { border-color: #ff9a8b; }
.place-text { font-size: 15px; color: #4a3728; }
.place-placeholder { font-size: 15px; color: #c4b5a5; }
.place-arrow { font-size: 16px; }
.coord-preview { display: flex; gap: 8px; font-size: 12px; color: #a89880; }

/* 提交按钮 */
.submit-btn {
  width: 100%; padding: 16px; border-radius: 18px; border: none;
  background: linear-gradient(135deg, #ff9a8b, #ffb8a8);
  color: #fff; font-size: 17px; font-weight: 700; cursor: pointer; font-family: inherit;
  box-shadow: 0 4px 16px rgba(255,154,139,0.25); transition: all 0.25s;
}
.submit-btn:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 6px 20px rgba(255,154,139,0.3); }
.submit-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.submit-hint { text-align: center; font-size: 12px; color: #c4b5a5; margin: -8px 0 0; }

/* 示例 */
.demo-entry { display: flex; flex-direction: column; align-items: center; gap: 10px; }
.demo-divider { font-size: 12px; color: #c4b5a5; }
.demo-btn {
  padding: 8px 18px; border-radius: 14px; border: 1px solid rgba(0,0,0,0.06);
  background: rgba(0,0,0,0.02); color: #8b7355; font-size: 13px; cursor: pointer; font-family: inherit; transition: all 0.2s;
}
.demo-btn:hover { border-color: rgba(255,154,139,0.2); background: rgba(255,154,139,0.04); }

/* ── 弹窗内样式 ── */
.place-dialog :deep(.el-tabs__item) { color: #6b5744; }
.manual-grid { display: grid; gap: 12px; margin-bottom: 12px; }
.manual-field label { display: block; font-size: 12px; color: #6b5744; margin-bottom: 4px; }
.manual-row { display: flex; align-items: center; gap: 6px; }
.manual-row span { color: #8b7355; font-size: 14px; }

/* ── 覆盖 Element Plus date picker 暗色 → 暖色 ── */
.analysis-page :deep(.el-input__wrapper) {
  background: rgba(0,0,0,0.02) !important; border: 1px solid rgba(0,0,0,0.08) !important;
  box-shadow: none !important; border-radius: 14px !important;
}
.analysis-page :deep(.el-input__inner) { color: #4a3728 !important; }
.analysis-page :deep(.el-input__inner::placeholder) { color: #c4b5a5 !important; }
.analysis-page :deep(.el-button--primary) {
  background: linear-gradient(135deg, #ff9a8b, #ffb8a8) !important; border: none !important;
}

/* 响应式 */
@media (max-width: 400px) {
  .field-row { grid-template-columns: 1fr; }
  .form-card { padding: 22px 16px; }
}
</style>
