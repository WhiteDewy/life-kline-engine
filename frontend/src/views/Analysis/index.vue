<template>
  <div class="page">
    <div class="backdrop"></div>

    <div class="wrap">
      <section v-if="analysis" class="hero">
        <div class="heroMain">
          <div class="eyebrow">Reading Setup</div>
          <div class="heroTop">
            <div>
              <h1 class="title">{{ analysis.title }}</h1>
              <p class="tagline">{{ analysis.tagline }}</p>
            </div>
            <span class="statusBadge" :class="analysis.status">
              {{ statusLabel(analysis.status) }}
            </span>
          </div>

          <p class="summary">{{ analysis.description }}</p>

          <div class="metaGrid">
            <div class="metaCard">
              <span>适合解决</span>
              <strong>{{ categoryLabel }}</strong>
            </div>
            <div class="metaCard">
              <span>适用人数</span>
              <strong>{{ subjectLabel(analysis.subjects_count) }}</strong>
            </div>
            <div class="metaCard">
              <span>报告内容</span>
              <strong>{{ analysis.modules.length }} 个结果模块</strong>
            </div>
          </div>
        </div>

        <aside class="heroAside">
          <div class="panelEyebrow">What You'll Get</div>
          <h2 class="panelTitle">这次解读会告诉你什么</h2>
          <div class="moduleList">
            <span v-for="module in analysis.modules" :key="module" class="moduleChip">
              {{ module }}
            </span>
          </div>
          <p class="panelText">
            它不会只给你一个简单标签，而会结合本命结构、阶段主题与关键提醒，帮助你知道“我现在在哪里，接下来怎么走”。
          </p>
        </aside>
      </section>

      <section v-else class="stateCard errorCard">
        <div class="stateTitle">没有找到这个解读入口</div>
        <p class="stateText">请返回首页，从已开放的解读入口重新进入。</p>
      </section>

      <section v-if="analysis" class="contentGrid">
        <article class="panel introPanel">
          <div class="panelEyebrow">Before We Start</div>
          <h2 class="panelTitle">先补全你的出生资料</h2>
          <p class="panelText">
            出生时间与地点会影响上升、宫位和阶段推演。资料越准确，报告越能贴近你的真实节奏。
          </p>
          <ul class="list">
            <li>当前支持单人解读，适合查看个人阶段、人生主轴与关键趋势。</li>
            <li>后续关系合盘会扩展为双人资料输入，不需要重新学习新的填写方式。</li>
            <li>如果自动定位失败，也可以手动填写坐标，不影响报告生成。</li>
          </ul>
        </article>

        <el-card class="formCard" shadow="never">
          <div class="formHeader">
            <div>
              <div class="panelEyebrow">Birth Data</div>
              <h2 class="formTitle">录入这次解读所需的信息</h2>
            </div>
            <el-alert
              v-if="analysis.status !== 'active'"
              title="这个解读入口还在准备中"
              type="warning"
              :closable="false"
              show-icon
            >
              <template #default>
                当前可以先体验“阶段导航”，先看看你正处于怎样的人生阶段。
              </template>
            </el-alert>
          </div>

          <el-form ref="formRef" :model="form" :rules="rules" label-position="top" class="form">
            <div class="twoCol">
              <el-form-item label="你的称呼（可选）" prop="name">
                <el-input v-model="form.name" placeholder="例如：Luna" clearable />
              </el-form-item>

              <el-form-item label="出生日期与时间" prop="birthDatetime">
                <el-date-picker
                  v-model="form.birthDatetime"
                  type="datetime"
                  style="width: 100%"
                  format="YYYY-MM-DD HH:mm"
                  value-format="YYYY-MM-DDTHH:mm"
                  placeholder="选择出生日期与时间"
                />
              </el-form-item>
            </div>

            <el-form-item label="出生地点" prop="birthPlace">
              <el-input
                v-model="form.birthPlace"
                readonly
                placeholder="点击设置出生地点"
                @click="placeDialogOpen = true"
              >
                <template #suffix>
                  <el-icon class="suffixIcon" @click.stop="placeDialogOpen = true">
                    <Location />
                  </el-icon>
                </template>
              </el-input>
            </el-form-item>

            <div class="coordPreview" v-if="form.lat && form.lon">
              <div class="coordItem">
                <span>纬度</span>
                <strong>{{ form.lat }}</strong>
              </div>
              <div class="coordItem">
                <span>经度</span>
                <strong>{{ form.lon }}</strong>
              </div>
              <div class="coordItem">
                <span>时区</span>
                <strong>UTC{{ form.timezone >= 0 ? "+" : "" }}{{ form.timezone }}</strong>
              </div>
            </div>

            <div class="actions">
              <el-button class="ghostBtn" @click="resetForm">重新填写</el-button>
              <el-button
                class="primaryBtn"
                type="primary"
                :loading="loading"
                :disabled="analysis.status !== 'active'"
                @click="onSubmit"
              >
                {{ analysis.primary_cta }}
              </el-button>
            </div>
          </el-form>
        </el-card>
      </section>
    </div>

    <el-dialog
      v-model="placeDialogOpen"
      title="设置出生地点"
      width="92%"
      :max-width="560"
      destroy-on-close
    >
      <div class="dialogBody">
        <el-tabs v-model="locationMode" type="card">
          <el-tab-pane label="自动获取" name="auto">
            <div class="tabBody">
              <el-alert title="推荐方式" type="success" :closable="false" show-icon>
                <template #default>
                  先选择地区，再自动获取坐标。中国大陆地区建议优先配置 AMap Key，以提升定位成功率。
                </template>
              </el-alert>

              <el-form-item label="出生地区" required class="spaced">
                <el-cascader
                  v-model="selectedOptions"
                  :options="regionData"
                  clearable
                  filterable
                  placeholder="选择省 / 市 / 区"
                  style="width: 100%"
                  @change="handleAddressChange"
                />
              </el-form-item>

              <el-button
                class="geoBtn"
                type="primary"
                plain
                :loading="geoLoading"
                :disabled="!form.birthPlace"
                @click="autoGeocode"
              >
                <el-icon><Position /></el-icon>
                自动获取坐标
              </el-button>
            </div>
          </el-tab-pane>

          <el-tab-pane label="手动填写" name="custom">
            <div class="tabBody">
              <el-form-item label="地点名称" required>
                <el-input v-model="form.birthPlace" placeholder="例如：北京市朝阳区" />
              </el-form-item>

              <div class="twoCol compact">
                <el-form-item label="纬度" required>
                  <el-input v-model="form.lat" type="number" placeholder="39.9042" />
                </el-form-item>
                <el-form-item label="经度" required>
                  <el-input v-model="form.lon" type="number" placeholder="116.4074" />
                </el-form-item>
              </div>

              <el-form-item label="时区" required>
                <el-select v-model="form.timezone" style="width: 100%" placeholder="选择时区">
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
        <div class="dialogFooter">
          <el-button @click="placeDialogOpen = false">取消</el-button>
          <el-button type="primary" @click="savePlaceSettings">保存地点</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage, type FormInstance, type FormRules } from "element-plus";
import { Location, Position } from "@element-plus/icons-vue";
import { regionData, codeToText } from "element-china-area-data";
import { apiClient } from "@/config/api";
import { ANALYSIS_CATEGORY_LABELS, FALLBACK_ANALYSIS_TYPES } from "@/utils/analysis";
import type { AnalysisDefinition, AnalysisResponse, AnalysisStatus, LifeReport } from "@/utils/types";

const route = useRoute();
const router = useRouter();
const formRef = ref<FormInstance>();

const catalog = ref<AnalysisDefinition[]>([...FALLBACK_ANALYSIS_TYPES]);
const placeDialogOpen = ref(false);
const locationMode = ref<"auto" | "custom">("auto");
const selectedOptions = ref<string[]>([]);
const geoLoading = ref(false);
const loading = ref(false);

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
  birthDatetime: "",
  birthPlace: "",
  lat: 0,
  lon: 0,
  timezone: 8,
});

const rules: FormRules = {
  birthDatetime: [{ required: true, message: "请选择出生日期与时间", trigger: "change" }],
  birthPlace: [{ required: true, message: "请设置出生地点", trigger: "blur" }],
};

const analysis = computed(() => {
  const type = String(route.params.type || "");
  return catalog.value.find((item) => item.key === type) ?? null;
});

const categoryLabel = computed(() => {
  return ANALYSIS_CATEGORY_LABELS[analysis.value?.category || ""] || "未分类";
});

const birthTimePayload = computed(() => {
  if (!form.birthDatetime) return "";
  return form.birthDatetime.length === 16 ? `${form.birthDatetime}:00` : form.birthDatetime;
});

function statusLabel(status: AnalysisStatus) {
  return status === "active" ? "已开放" : "即将上线";
}

function subjectLabel(count: number) {
  return count > 1 ? `${count} 人解读` : "1 人解读";
}

function handleAddressChange(codes: string[]) {
  if (!codes?.length) {
    form.birthPlace = "";
    return;
  }
  form.birthPlace = codes.map((code) => codeToText[code]).join(" ");
}

async function autoGeocode() {
  if (!form.birthPlace) {
    ElMessage.warning("请先选择出生地点");
    return;
  }

  geoLoading.value = true;
  try {
    const response = await apiClient.post("/geocode", { query: form.birthPlace });
    if (response.data.status === "success") {
      const { lat, lon, timezone } = response.data.data;
      form.lat = Number(lat);
      form.lon = Number(lon);
      form.timezone = Number(timezone);
      ElMessage.success("已获取坐标");
      return;
    }
    ElMessage.error("没有找到对应地点");
  } catch (error) {
    console.error(error);
    const response = (error as { response?: { status?: number; data?: { detail?: string } } })
      ?.response;
    const detail = response?.data?.detail;
    if (response?.status === 404) {
      ElMessage.error(detail || "没有找到对应地点，请输入更具体的地址");
    } else if (response?.status === 502 || response?.status === 504) {
      ElMessage.error(detail || "自动定位暂时不可用，请改用手动填写坐标");
    } else {
      ElMessage.error(detail || "获取坐标失败");
    }
  } finally {
    geoLoading.value = false;
  }
}

function savePlaceSettings() {
  if (!form.birthPlace) {
    ElMessage.warning("请先设置出生地点");
    return;
  }
  if (!form.lat || !form.lon) {
    ElMessage.warning("请先获取或填写坐标");
    return;
  }
  placeDialogOpen.value = false;
}

function resetForm() {
  form.name = "";
  form.birthDatetime = "";
  form.birthPlace = "";
  form.lat = 0;
  form.lon = 0;
  form.timezone = 8;
  selectedOptions.value = [];
  locationMode.value = "auto";
}

async function onSubmit() {
  if (!analysis.value || !formRef.value) return;
  const valid = await formRef.value.validate().catch(() => false);
  if (!valid) return;

  if (!form.lat || !form.lon) {
    ElMessage.warning("请先设置出生地点对应的坐标");
    return;
  }

  loading.value = true;
  try {
    const response = await apiClient.post<AnalysisResponse<LifeReport>>("/analyses", {
      analysis_type: analysis.value.key,
      subjects: [
        {
          name: form.name || undefined,
          birth_time: birthTimePayload.value,
          lat: Number(form.lat),
          lon: Number(form.lon),
          timezone: Number(form.timezone),
        },
      ],
    });

    if (response.data.status === "success" && response.data.report_id) {
      router.push({
        name: "report",
        params: { id: response.data.report_id },
      });
      return;
    }

    ElMessage.error("报告生成失败");
  } catch (error) {
    console.error(error);
    const detail = (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
    ElMessage.error(detail || "请求失败，请检查后端服务是否已启动");
  } finally {
    loading.value = false;
  }
}

async function loadCatalog() {
  try {
    const response = await apiClient.get<{ status: string; data: AnalysisDefinition[] }>(
      "/analysis-types"
    );
    if (response.data?.status === "success" && response.data.data?.length) {
      catalog.value = response.data.data;
    }
  } catch (error) {
    console.error("Failed to load analysis catalog", error);
  }
}

onMounted(() => {
  loadCatalog();
});
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
  mask-image: linear-gradient(180deg, rgba(0, 0, 0, 0.25), transparent 90%);
  pointer-events: none;
}

.wrap {
  position: relative;
  z-index: 1;
  max-width: 1240px;
  margin: 0 auto;
}

.hero,
.contentGrid {
  display: grid;
  gap: 22px;
}

.hero {
  grid-template-columns: minmax(0, 1.3fr) minmax(320px, 0.7fr);
}

.contentGrid {
  margin-top: 22px;
  grid-template-columns: minmax(0, 0.82fr) minmax(0, 1.18fr);
  align-items: start;
}

.heroMain,
.heroAside,
.panel,
.formCard,
.stateCard {
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(15, 23, 42, 0.74);
  backdrop-filter: blur(18px);
  border-radius: 28px;
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.24);
}

.heroMain,
.heroAside,
.panel,
.stateCard {
  padding: 28px;
}

.eyebrow,
.panelEyebrow {
  font-size: 12px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--gold);
}

.heroTop {
  display: flex;
  justify-content: space-between;
  gap: 18px;
  margin-top: 14px;
}

.title {
  margin: 0;
  color: var(--text);
  font-size: 48px;
  line-height: 1.04;
  letter-spacing: -0.04em;
  font-family: "Georgia", "Times New Roman", serif;
}

.tagline,
.summary,
.panelText,
.stateText {
  color: var(--text-secondary);
  line-height: 1.8;
}

.tagline {
  margin: 12px 0 0;
  font-size: 18px;
}

.summary {
  margin: 18px 0 0;
}

.statusBadge {
  display: inline-flex;
  align-items: center;
  height: fit-content;
  padding: 8px 12px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.statusBadge.active {
  color: #10b981;
  background: rgba(16, 185, 129, 0.12);
  border: 1px solid rgba(16, 185, 129, 0.2);
}

.statusBadge.planned {
  color: #f59e0b;
  background: rgba(245, 158, 11, 0.12);
  border: 1px solid rgba(245, 158, 11, 0.2);
}

.metaGrid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-top: 22px;
}

.metaCard {
  padding: 14px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.metaCard span {
  display: block;
  color: var(--text-secondary);
  font-size: 12px;
}

.metaCard strong {
  display: block;
  margin-top: 8px;
  color: var(--text);
  line-height: 1.5;
}

.panelTitle,
.formTitle,
.stateTitle {
  margin: 10px 0 0;
  color: var(--text);
}

.panelTitle,
.formTitle {
  font-size: 28px;
  line-height: 1.2;
}

.moduleList {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 16px;
}

.moduleChip {
  display: inline-flex;
  align-items: center;
  padding: 7px 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.06);
  color: var(--text-secondary);
  font-size: 12px;
}

.panelText {
  margin: 14px 0 0;
}

.list {
  margin: 16px 0 0;
  padding: 0;
  list-style: none;
  display: grid;
  gap: 10px;
}

.list li {
  position: relative;
  padding-left: 18px;
  color: var(--text-secondary);
  line-height: 1.7;
}

.list li::before {
  content: "";
  position: absolute;
  left: 0;
  top: 11px;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--gold);
}

.formCard {
  padding: 10px;
}

.formCard :deep(.el-card__body) {
  padding: 18px;
}

.formHeader {
  display: grid;
  gap: 14px;
  margin-bottom: 12px;
}

.form :deep(.el-form-item__label) {
  color: var(--text-secondary);
  letter-spacing: 0.02em;
}

.form :deep(.el-input__wrapper),
.form :deep(.el-select__wrapper),
.form :deep(.el-textarea__inner) {
  background: rgba(255, 255, 255, 0.04) !important;
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
  box-shadow: none !important;
  border-radius: 14px !important;
}

.form :deep(.el-input__inner),
.form :deep(.el-select__selected-item) {
  color: var(--text) !important;
}

.twoCol {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.twoCol.compact {
  gap: 12px;
}

.coordPreview {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin: 4px 0 10px;
}

.coordItem {
  padding: 12px 14px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.coordItem span {
  display: block;
  color: var(--text-secondary);
  font-size: 12px;
}

.coordItem strong {
  display: block;
  margin-top: 8px;
  color: var(--text);
}

.suffixIcon {
  cursor: pointer;
  color: var(--text-secondary);
}

.actions {
  margin-top: 18px;
  display: flex;
  gap: 12px;
}

.primaryBtn {
  min-width: 180px;
}

.ghostBtn {
  min-width: 120px;
}

.dialogBody {
  padding-top: 8px;
}

.tabBody {
  padding-top: 8px;
}

.spaced {
  margin-top: 16px;
}

.geoBtn {
  margin-top: 4px;
}

.dialogFooter {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.errorCard {
  border-color: rgba(244, 63, 94, 0.24);
}

@media (max-width: 1100px) {
  .hero,
  .contentGrid,
  .metaGrid,
  .coordPreview {
    grid-template-columns: 1fr;
  }

  .title {
    font-size: 40px;
  }
}

@media (max-width: 720px) {
  .page {
    padding-inline: 14px;
  }

  .heroTop,
  .twoCol,
  .actions {
    grid-template-columns: 1fr;
    display: grid;
  }

  .heroTop {
    gap: 12px;
  }
}
</style>
