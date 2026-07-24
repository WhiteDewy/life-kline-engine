/**
 * useGarden.ts — 花园页面数据管理 composable
 *
 * 管理：分类列表、签到状态、咨询流程、报告历史
 */
import { ref, computed } from "vue";
import { apiClient } from "@/config/api";
import type {
  GardenCategory,
  FortuneItem,
  CheckinStatus,
  ConsultationState,
  ConsultationReport,
  ConsultationReportItem,
  GardenCatalogData,
} from "@/utils/types";

export function useGarden() {
  // ── 状态 ──
  const loading = ref(true);
  const error = ref("");
  const categories = ref<GardenCategory[]>([]);
  const fortuneItems = ref<FortuneItem[]>([]);
  const checkinStatus = ref<CheckinStatus>({
    checked_in: false,
    streak_count: 0,
    checkin_date: "",
  });
  const selectedCategory = ref<GardenCategory | null>(null);
  const selectedQuestion = ref<string | null>(null);
  const consultationState = ref<ConsultationState | null>(null);
  const consultationReport = ref<ConsultationReport | null>(null);
  const reports = ref<ConsultationReportItem[]>([]);
  const reportsLoading = ref(false);
  const reportId = ref("");

  // ── 计算属性 ──
  const gardenReady = computed(() => !loading.value && !error.value);

  // ── 方法 ──

  async function loadCategories(): Promise<void> {
    try {
      const res = await apiClient.get<{ status: string; data: GardenCatalogData }>(
        "/garden/categories",
      );
      if (res.data?.status === "success") {
        categories.value = res.data.data.categories;
        fortuneItems.value = res.data.data.fortune;
      }
    } catch (err) {
      console.error("Failed to load garden categories:", err);
      // 不阻塞，使用空列表
    }
  }

  async function loadCheckinStatus(): Promise<void> {
    try {
      const res = await apiClient.get<{ status: string; data: CheckinStatus }>(
        "/garden/checkin",
      );
      if (res.data?.status === "success") {
        checkinStatus.value = res.data.data;
      }
    } catch {
      // 未登录或网络问题
    }
  }

  async function doCheckin(): Promise<void> {
    try {
      const res = await apiClient.post<{ status: string; data: CheckinStatus }>(
        "/garden/checkin",
      );
      if (res.data?.status === "success") {
        checkinStatus.value = res.data.data;
      }
    } catch {
      // silent fail
    }
  }

  function selectCategory(cat: GardenCategory): void {
    selectedCategory.value = cat;
    selectedQuestion.value = null;
    consultationState.value = null;
    consultationReport.value = null;
  }

  function clearCategory(): void {
    selectedCategory.value = null;
    selectedQuestion.value = null;
    consultationState.value = null;
    consultationReport.value = null;
  }

  function selectQuestion(questionKey: string): void {
    selectedQuestion.value = questionKey;
  }

  async function startConsultation(
    rid: string,
    category: string,
    questionKey: string,
  ): Promise<void> {
    reportId.value = rid;
    try {
      const res = await apiClient.post<{ status: string; data: ConsultationState }>(
        `/garden/consultation/${rid}/start`,
        { category, question_key: questionKey },
      );
      if (res.data?.status === "success") {
        consultationState.value = res.data.data;
      }
    } catch (err: any) {
      error.value = err?.response?.data?.detail || "启动咨询失败";
    }
  }

  async function continueConsultation(
    rid: string,
    sessionId: string,
    userResponse: string,
  ): Promise<void> {
    try {
      const res = await apiClient.post<{ status: string; data: ConsultationState }>(
        `/garden/consultation/${rid}/continue`,
        { session_id: sessionId, user_response: userResponse },
      );
      if (res.data?.status === "success") {
        consultationState.value = res.data.data;
      }
    } catch (err: any) {
      error.value = err?.response?.data?.detail || "继续咨询失败";
    }
  }

  async function generateReport(rid: string, sessionId: string): Promise<void> {
    try {
      const res = await apiClient.post<{ status: string; data: ConsultationReport }>(
        `/garden/consultation/${rid}/report`,
        { session_id: sessionId, user_response: "" },
      );
      if (res.data?.status === "success") {
        consultationReport.value = res.data.data;
      }
    } catch (err: any) {
      error.value = err?.response?.data?.detail || "生成报告失败";
    }
  }

  async function loadReports(categoryFilter?: string): Promise<void> {
    reportsLoading.value = true;
    try {
      const params: Record<string, any> = { limit: 50 };
      if (categoryFilter) params.category = categoryFilter;
      const res = await apiClient.get<{
        status: string;
        data: { reports: ConsultationReportItem[]; total: number };
      }>("/garden/reports", { params });
      if (res.data?.status === "success") {
        reports.value = res.data.data.reports;
      }
    } catch {
      // silent
    } finally {
      reportsLoading.value = false;
    }
  }

  async function loadReportDetail(reportIdDetail: string): Promise<void> {
    try {
      const res = await apiClient.get<{ status: string; data: ConsultationReport }>(
        `/garden/reports/${reportIdDetail}`,
      );
      if (res.data?.status === "success") {
        consultationReport.value = res.data.data;
      }
    } catch {
      // silent
    }
  }

  async function init(rid?: string): Promise<void> {
    loading.value = true;
    error.value = "";
    try {
      await Promise.all([loadCategories(), loadCheckinStatus()]);
      if (rid) {
        reportId.value = rid;
      }
    } catch (err: any) {
      error.value = err?.message || "加载花园数据失败";
    } finally {
      loading.value = false;
    }
  }

  return {
    // state
    loading,
    error,
    categories,
    fortuneItems,
    checkinStatus,
    selectedCategory,
    selectedQuestion,
    consultationState,
    consultationReport,
    reports,
    reportsLoading,
    reportId,
    gardenReady,
    // methods
    init,
    loadCategories,
    loadCheckinStatus,
    doCheckin,
    selectCategory,
    clearCategory,
    selectQuestion,
    startConsultation,
    continueConsultation,
    generateReport,
    loadReports,
    loadReportDetail,
  };
}
