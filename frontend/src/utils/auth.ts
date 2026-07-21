/**
 * 认证 & 用户状态管理
 */
import { ref, computed } from "vue";
import { apiClient } from "@/config/api";

const TOKEN_KEY = "lk_token";
const USER_KEY = "lk_user";

/** 开发环境调试手机号（环境变量 VITE_DEV_BYPASS_PHONE），非空且匹配时跳过验证码 */
const DEV_BYPASS_PHONE = import.meta.env.VITE_DEV_BYPASS_PHONE?.trim() || "";
export function isDevBypassPhone(phone: string): boolean {
  return !!DEV_BYPASS_PHONE && phone === DEV_BYPASS_PHONE;
}

const token = ref(localStorage.getItem(TOKEN_KEY) || "");
const user = ref<any>(_loadJson(USER_KEY));
const profiles = ref<any[]>([]);

function _loadJson(key: string) {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function _saveJson(key: string, data: any) {
  localStorage.setItem(key, JSON.stringify(data));
}

export function useAuth() {
  const isLoggedIn = computed(() => !!token.value);

  async function sendCode(phone: string) {
    const res = await apiClient.post("/auth/send-code", { phone });
    return res.data;
  }

  async function verifyCode(phone: string, code: string) {
    const res = await apiClient.post("/auth/verify-code", { phone, code });
    if (res.data?.token) {
      token.value = res.data.token;
      localStorage.setItem(TOKEN_KEY, res.data.token);
      await loadMe();
    }
    return res.data;
  }

  async function loadMe() {
    if (!token.value) return;
    try {
      const res = await apiClient.get("/me", {
        headers: { Authorization: `Bearer ${token.value}` },
      });
      if (res.data?.user) {
        user.value = res.data.user;
        _saveJson(USER_KEY, res.data.user);
      }
      if (res.data?.profiles) {
        profiles.value = res.data.profiles;
      }
    } catch {
      logout();
      // 非登录页面时提示
      if (!window.location.pathname.startsWith("/login")) {
        import("@/utils/toast").then(({ toast }) => {
          toast.error("登录已过期，请重新登录");
        });
      }
    }
  }

  async function saveProfile(data: {
    name?: string;
    gender?: string;
    birth_time: string;
    lat: number;
    lon: number;
    timezone?: number;
  }) {
    const res = await apiClient.post("/profiles", data, {
      headers: { Authorization: `Bearer ${token.value}` },
    });
    if (res.data?.profile_id) {
      await loadMe();
    }
    return res.data;
  }

  async function getHistory() {
    const res = await apiClient.get("/reports/history", {
      headers: { Authorization: `Bearer ${token.value}` },
    });
    return res.data?.reports || [];
  }

  function logout() {
    token.value = "";
    user.value = null;
    profiles.value = [];
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  }

  function authHeaders() {
    return token.value ? { Authorization: `Bearer ${token.value}` } : {};
  }

  return {
    token,
    user,
    profiles,
    isLoggedIn,
    sendCode,
    verifyCode,
    loadMe,
    saveProfile,
    getHistory,
    logout,
    authHeaders,
  };
}
