/**
 * useHomeData — Main 页面数据加载 & 计算逻辑
 *
 * 从 main.vue 抽取所有 API 调用、computed 转换、星灵议会数据。
 * 新增 activePlanet 机制：跟踪当前选中的星灵，驱动视频背景动态切换。
 */
import { ref, computed } from "vue";
import { useAuth } from "@/utils/auth";
import { apiClient } from "@/config/api";
import { getVideoBySign } from "@/config/videoAssets";
import { ZODIAC_SIGNS, SIGN_EMOJI_BY_NAME, PLANET_ORDER } from "@/config/zodiac";

export function useHomeData() {
  const { user, profiles, isLoggedIn, loadMe, logout, authHeaders } = useAuth();

  // ── 核心状态 ──
  const loading = ref(true);
  const error = ref("");
  const reportData = ref<any>(null);
  const dailyData = ref<any>(null);
  const reportId = ref("");

  // ── 当前活跃星灵 / 星座（驱动视频背景）──
  const activePlanet = ref("SUN");
  const activeSign = ref(""); // 用户选中星座时设置（如 "PISCES"）

  // ═══════════════════════════════════════
  // 用户
  // ═══════════════════════════════════════

  const hasProfile = computed(() => !!(reportData.value || isLoggedIn.value));
  const userName = computed(() => {
    if (user.value?.nickname) return user.value.nickname;
    if (reportData.value?.user_info?.name) return reportData.value.user_info.name;
    return "星灵旅人";
  });
  const userGender = computed(() => reportData.value?.user_info?.gender || "");

  // ═══════════════════════════════════════
  // 太阳
  // ═══════════════════════════════════════

  const sunSignLabel = computed(() => reportData.value?.natal_chart?.planets?.SUN?.sign_label || "");
  const ascSignLabel = computed(() => reportData.value?.natal_chart?.ascendant?.sign_label || "");
  const moonSignLabel = computed(() => reportData.value?.natal_chart?.planets?.MOON?.sign_label || "");
  const sunSignEmoji = computed(() => SIGN_EMOJI_BY_NAME[sunSignLabel.value] || "☉");
  const sunSign = computed(() => reportData.value?.natal_chart?.planets?.SUN?.sign || "");
  const sunHouse = computed(() => reportData.value?.natal_chart?.planets?.SUN?.house || 1);

  const planetProfiles = computed<any>(() => reportData.value?.planet_characters || null);
  const sunProfile = computed(() => planetProfiles.value?.planet_characters?.["SUN"] || null);
  const sunName = computed(() => sunProfile.value?.persona?.name_zh || "太阳");
  const sunArchetype = computed(() => sunProfile.value?.persona?.archetype_zh || "主角 / 自我定义者");
  const sunColor = computed(() => sunProfile.value?.persona?.visual_color || "#F2A900");
  const sunEssence = computed(() => sunProfile.value?.persona?.essence || "我是你想成为的那个人——你的核心意志和生命方向。");

  const sunTransits = computed(() => {
    const fast = reportData.value?._transits_fast || [];
    return fast.filter((t: any) => t.natal_planet === "SUN");
  });
  const sunTransitStatus = computed(() => {
    const t = sunTransits.value[0];
    if (!t) return "";
    return `${t.transiting_label}${t.aspect_label}太阳`;
  });

  // ═══════════════════════════════════════
  // 活跃星灵档案（决定视频 & 聊天）
  // ═══════════════════════════════════════

  /** 当前选中星灵的完整档案 */
  const activePlanetProfile = computed(() => {
    const profiles = planetProfiles.value?.planet_characters || {};
    return profiles[activePlanet.value] || sunProfile.value;
  });

  /** 当前选中星灵的落座星座 key（如 "PISCES"） */
  const activePlanetSign = computed(() => {
    if (activePlanet.value === "SUN") return sunSign.value;
    return activePlanetProfile.value?.sign || sunSign.value;
  });

  /** 当前应播放的视频（优先 activeSign，其次 activePlanet 落座） */
  const currentSignVideo = computed(() => {
    const sign = activeSign.value || activePlanetSign.value;
    return getVideoBySign(sign);
  });

  // ═══════════════════════════════════════
  // 每日
  // ═══════════════════════════════════════

  const dailyTheme = computed(() => dailyData.value?.daily_theme || "");
  const dateLabel = computed(() => {
    const d = new Date();
    const w = ["日", "一", "二", "三", "四", "五", "六"];
    return `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日 · 星期${w[d.getDay()]}`;
  });

  const chatCtaText = computed(() => {
    const h = new Date().getHours();
    if (h < 10) return "早安，星灵在等你";
    if (h < 18) return "触碰你的内在星辰";
    return "今夜，星光为你低语";
  });

  // ── 今日星灵 ──
  const todayStarSpirit = ref<any>(null);
  const dailyQuestion = ref<any>(null);
  const diaryEntries = ref<any[]>([]);

  // ── 今日星象（每日走向面板用）──
  // TODO: /api/daily-transits/{report_id} 后端同步开发中，暂用 try/catch 兜底
  const dailyTransitReport = ref<any>(null);

  const todaysPlanetProfile = computed(() => {
    const planetKey = todayStarSpirit.value?.planet;
    if (!planetKey) return null;
    const profiles = planetProfiles.value?.planet_characters || {};
    return profiles[planetKey] || null;
  });

  const directionTheme = computed(() => {
    const sunTransitText = sunTransitStatus.value;
    if (sunTransitText) return sunTransitText;
    return dailyData.value?.daily_theme || "";
  });

  // ═══════════════════════════════════════
  // 星灵议会
  // ═══════════════════════════════════════

    /** 行星 → 疗愈主题映射 */
  const HEALING_LABELS: Record<string, string> = {
    SUN: "自我认同",
    MOON: "情感安全",
    MERCURY: "思维清晰",
    VENUS: "关系和谐",
    MARS: "行动勇气",
    JUPITER: "信念希望",
    SATURN: "结构边界",
    URANUS: "突破创新",
    NEPTUNE: "内在平静",
    PLUTO: "深度转化",
  };

  const councilPlanetList = computed(() => {
    const profiles = planetProfiles.value?.planet_characters || {};
    const activationScores = dailyData.value?.activation_scores || {};
    const featuredSet = new Set((dailyData.value?.featured_planets || []).map((f: any) => f.planet));
    return PLANET_ORDER.map((key) => {
      const p = profiles[key];
      if (!p) return null;
      const archetype = p.persona?.archetype_zh || "";
      return {
        planet: key,
        sign: p.sign || "",
        shortName: p.persona?.name_zh || key,
        archetypeShort: archetype.includes("/") ? archetype.split("/")[0].trim() : archetype.slice(0, 6),
        color: p.persona?.visual_color || "#999",
        symbol: p.persona?.symbol || "●",
        signLabel: p.sign_label || "",
        dignityLabel: p.dignity_label || "",
        isFeatured: featuredSet.has(key),
        activationScore: activationScores[key] ?? null,
        greeting: p.personalized_greeting || "",
        healingLabel: HEALING_LABELS[key] || "",
      };
    }).filter(Boolean) as any[];
  });

  const councilSignList = computed(() => {
    const planets = reportData.value?.natal_chart?.planets || {};
    const signPlanets: Record<string, string[]> = {};
    for (const [pKey, pData] of Object.entries(planets)) {
      const sKey = (pData as any)?.sign;
      if (sKey) {
        if (!signPlanets[sKey]) signPlanets[sKey] = [];
        const label = (pData as any)?.sign_label || pKey;
        signPlanets[sKey].push(label.slice(0, 2));
      }
    }
    return ZODIAC_SIGNS.map((s) => ({
      ...s,
      hasPlanets: !!signPlanets[s.key]?.length,
      planetsHere: signPlanets[s.key]?.join("·") || "",
    }));
  });

  // ═══════════════════════════════════════
  // 数据加载
  // ═══════════════════════════════════════

  /** Demo 默认用户 — 调试用，确保始终有视频背景 */
  const DEMO_SUBJECT = {
    name: "夏天",
    gender: "女",
    birth_time: "1991-03-21T09:25:00",
    lat: 35.7,
    lon: 113.35,
    timezone: 8,
  };

  async function refreshData() {
    loading.value = true;
    error.value = "";
    try {
      // 尝试加载用户数据
      await loadMe();
      let loaded = false;

      if (profiles.value.length > 0 || user.value) {
        const hist = await apiClient.get("/reports/history", {
          headers: authHeaders(),
        });
        const reports = hist.data?.reports || [];
        if (reports.length > 0) {
          const lastId = reports[0].report_id || reports[0].id;
          if (lastId) {
            reportId.value = lastId;
            const res = await apiClient.get(`/analyses/${lastId}`);
            if (res.data?.status === "success") {
              reportData.value = res.data.data;
              loaded = true;
            }
            try {
              const dRes = await apiClient.get(`/characters/${lastId}/daily`);
              if (dRes.data?.status === "success") dailyData.value = dRes.data.data;
            } catch { /* optional */ }
            // 非阻塞加载今日星灵、每日一问、日记、每日星象
            try {
              const ssRes = await apiClient.get(`/today-star-spirit/${lastId}`);
              if (ssRes.data?.status === "success") todayStarSpirit.value = ssRes.data.data;
            } catch { /* optional */ }
            try {
              const dqRes = await apiClient.get(`/daily-question/${lastId}`);
              if (dqRes.data?.status === "success") dailyQuestion.value = dqRes.data.data;
            } catch { /* optional */ }
            try {
              const deRes = await apiClient.get(`/spirit-diary/${lastId}?limit=30&offset=0`);
              if (deRes.data?.status === "success") diaryEntries.value = deRes.data.data?.entries || deRes.data.data || [];
            } catch { /* optional */ }
            // TODO: /api/daily-transits/{report_id} 后端同步开发中，可能尚未就绪
            try {
              const dtRes = await apiClient.get(`/daily-transits/${lastId}`);
              if (dtRes.data?.status === "success") dailyTransitReport.value = dtRes.data.data;
            } catch { /* API not available yet - gracefully degrade */ }
          }
        }
      }

      // Fallback: 未登录或无报告时，加载 demo 用户确保视频可显示
      if (!loaded) {
        const fb = await apiClient.post("/analyses", {
          analysis_type: "natal_blueprint",
          subjects: [DEMO_SUBJECT],
        });
        if (fb.data?.status === "success") {
          reportData.value = fb.data.data;
          reportId.value = fb.data.report_id || "";
          try {
            const dRes = await apiClient.get(`/characters/${reportId.value}/daily`);
            if (dRes.data?.status === "success") dailyData.value = dRes.data.data;
          } catch { /* optional */ }
          // 非阻塞加载今日星灵、每日一问、日记、每日星象
          try {
            const ssRes = await apiClient.get(`/today-star-spirit/${reportId.value}`);
            if (ssRes.data?.status === "success") todayStarSpirit.value = ssRes.data.data;
          } catch { /* optional */ }
          try {
            const dqRes = await apiClient.get(`/daily-question/${reportId.value}`);
            if (dqRes.data?.status === "success") dailyQuestion.value = dqRes.data.data;
          } catch { /* optional */ }
          try {
            const deRes = await apiClient.get(`/spirit-diary/${reportId.value}?limit=30&offset=0`);
            if (deRes.data?.status === "success") diaryEntries.value = deRes.data.data?.entries || deRes.data.data || [];
          } catch { /* optional */ }
          // TODO: /api/daily-transits/{report_id} 后端同步开发中，可能尚未就绪
          try {
            const dtRes = await apiClient.get(`/daily-transits/${reportId.value}`);
            if (dtRes.data?.status === "success") dailyTransitReport.value = dtRes.data.data;
          } catch { /* API not available yet - gracefully degrade */ }
        }
      }
    } catch (err: any) {
      console.error(err);
      error.value = "无法加载星盘数据，请检查后端服务。";
    } finally {
      loading.value = false;
    }
  }

  /** 切换活跃星灵 → 视频切换为该星灵落座星座 */
  function setActivePlanet(planetKey: string) {
    activePlanet.value = planetKey;
    activeSign.value = ""; // 清除星座选中
  }

  /** 切换活跃星座 → 视频切换为该星座 */
  function setActiveSign(signKey: string) {
    activeSign.value = signKey;
    // 同时将 activePlanet 设为该星座中第一颗行星（如果有的话）
    const planetInSign = councilPlanetList.value.find((p: any) => p.sign === signKey);
    if (planetInSign) activePlanet.value = planetInSign.planet;
  }

  /** 清除数据（退出登录时调用） */
  function clearData() {
    reportData.value = null;
    dailyData.value = null;
    dailyTransitReport.value = null;
    reportId.value = "";
    activePlanet.value = "SUN";
    activeSign.value = "";
  }

  return {
    // 状态
    loading,
    error,
    reportData,
    dailyData,
    reportId,
    // 用户
    hasProfile,
    userName,
    userGender,
    // 太阳
    sunSign,
    sunSignLabel,
    ascSignLabel,
    moonSignLabel,
    sunSignEmoji,
    sunHouse,
    sunName,
    sunArchetype,
    sunColor,
    sunEssence,
    sunTransits,
    sunTransitStatus,
    sunProfile,
    planetProfiles,
    // 活跃星灵
    activePlanet,
    activeSign,
    activePlanetSign,
    activePlanetProfile,
    currentSignVideo,
    // 每日
    dailyTheme,
    dateLabel,
    chatCtaText,
    // 今日星灵
    todayStarSpirit,
    dailyQuestion,
    diaryEntries,
    todaysPlanetProfile,
    directionTheme,
    // 每日星象
    dailyTransitReport,
    // 议会
    councilPlanetList,
    councilSignList,
    // 操作
    refreshData,
    setActivePlanet,
    setActiveSign,
    clearData,
    // 暴露底层 ref 给 doLogout 等场景
    logout,
  };
}
