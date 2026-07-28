import axios from "axios";

const DEFAULT_API_BASE_URL = "/api";
const rawApiBaseUrl =
  import.meta.env.VITE_API_BASE_URL?.trim() || DEFAULT_API_BASE_URL;

export const API_BASE_URL = rawApiBaseUrl.endsWith("/")
  ? rawApiBaseUrl.slice(0, -1)
  : rawApiBaseUrl;

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
});

// ── 额度超限错误 ──
// 后端 spirit-chat/council 在额度耗尽时返回 HTTP 200 + body
// {status:"error", error_code:"QUOTA_EXCEEDED", data:{message, access}}。
// 不能只看 HTTP 状态码，必须按 body error_code 识别。
export class QuotaError extends Error {
  access: any;
  action_required: string;
  constructor(message: string, access: any) {
    super(message || "额度不足");
    this.name = "QuotaError";
    this.access = access || {};
    this.action_required = access?.action_required || "";
  }
}

// ── Request interceptor: 自动附加 token ──
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("lk_token");
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ── Response interceptor ──
apiClient.interceptors.response.use(
  (response) => {
    // HTTP 200 但 body 标记 QUOTA_EXCEEDED → 抛 QuotaError 供调用方引导升级
    const body = response?.data;
    if (body && body.error_code === "QUOTA_EXCEEDED") {
      const data = body.data || {};
      throw new QuotaError(data.message || "额度不足", data.access);
    }
    return response;
  },
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("lk_token");
      localStorage.removeItem("lk_user");
      // 避免登录页自身触发循环
      if (!window.location.pathname.startsWith("/login")) {
        window.location.href = `/login?redirect=${encodeURIComponent(window.location.pathname)}`;
      }
    }
    return Promise.reject(error);
  },
);
