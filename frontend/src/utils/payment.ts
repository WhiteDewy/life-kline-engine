/**
 * 权限与定价 —— 服务端单一真相源
 *
 * 变现模型：报告查看免费；AI/议会对话有每日免费额度，超出走星币或 VIP。
 * 额度校验全在后端 AccessChecker；前端只负责展示与引导付费。
 *
 * 历史遗留的 localStorage 付费墙（lk_purchases / 解锁报告领域 9.9/29.9/199）
 * 已废弃：清 localStorage 即可绕过，不可用于生产。
 */
import { ref, computed } from "vue";
import { apiClient } from "@/config/api";

export interface AccessResult {
  allowed: boolean;
  reason: string;
  remaining_free: number;
  cost_coins: number;
  user_coins: number;
  is_vip: boolean;
  is_test_user: boolean;
  action_required: string; // "purchase_coins" | "upgrade_vip" | ""
  used: number | null;
  limit: number | null;
}

export interface AccessInfo {
  is_test_user: boolean;
  is_vip: boolean;
  coins: number;
  engine: AccessResult;
  ai: AccessResult;
  council: AccessResult;
}

export interface PricingInfo {
  currency: string;
  rate: string;
  free_quota: {
    engine_daily_rounds: number;
    engine_per_spirit: number;
    ai_daily_rounds: number;
    council_weekly: number;
  };
  vip_plans: Record<
    string,
    {
      name: string;
      price_cny: number;
      duration_days: number;
      auto_renew: boolean;
      ai_monthly_rounds: number;
      description: string;
    }
  >;
  coin_packages: Array<{
    id: string;
    name: string;
    coins: number;
    price_cny: number;
    bonus: number;
    total_coins: number;
    popular: boolean;
  }>;
  consumption: {
    engine_per_round: number;
    ai_per_round: number;
    ai_deep_dive: number;
  };
}

// ── 单例状态（跨组件共享）──
const access = ref<AccessInfo | null>(null);
const pricing = ref<PricingInfo | null>(null);
const loading = ref(false);

function userId(): string {
  try {
    const raw = localStorage.getItem("lk_user");
    return raw ? JSON.parse(raw)?.id || "" : "";
  } catch {
    return "";
  }
}

async function fetchAccess(): Promise<AccessInfo | null> {
  const uid = userId();
  if (!uid) return null;
  try {
    const res = await apiClient.get(`/access/${uid}`);
    if (res.data?.status === "success") {
      access.value = res.data.data;
      return res.data.data;
    }
  } catch {
    /* 静默：调用方按 null 处理 */
  }
  return null;
}

async function fetchPricing(): Promise<PricingInfo | null> {
  if (pricing.value) return pricing.value;
  try {
    const res = await apiClient.get("/pricing");
    if (res.data?.status === "success") {
      pricing.value = res.data.data;
      return res.data.data;
    }
  } catch {
    /* 静默 */
  }
  return null;
}

export function useAccess() {
  const isVip = computed(() => !!access.value?.is_vip);
  const coins = computed(() => access.value?.coins ?? 0);

  /** AI 对话是否可用（综合 ai.allowed；后端 AI 层超额会静默降级 source=engine） */
  const aiAllowed = computed(() => !!access.value?.ai?.allowed);

  async function refresh() {
    loading.value = true;
    await fetchAccess();
    loading.value = false;
  }

  return {
    access,
    pricing,
    loading,
    isVip,
    coins,
    aiAllowed,
    fetchAccess,
    fetchPricing,
    refresh,
  };
}

// ── 下单 / 支付凭证校验（对接 backend/routers/billing.py）──

export interface OrderResult {
  order_id: string;
  product_id: string;
  product_type: "coin" | "vip";
  channel: string;
  amount_cny: number;
  status: string;
}

export interface VerifyResult {
  order_id: string;
  granted?: string;
  coins?: number;
  is_vip?: boolean;
  vip_expire_at?: string;
  already_paid?: boolean;
}

async function createOrder(
  productId: string,
  channel: "iap" | "wechat" | "alipay" = "iap",
): Promise<OrderResult> {
  const res = await apiClient.post("/billing/orders", {
    product_id: productId,
    channel,
  });
  if (res.data?.status === "success") return res.data.data;
  throw new Error(res.data?.message || "下单失败");
}

/**
 * 拉起原生支付并校验。原生壳通过 window.__nativePay__ 桥接（Capacitor 等）；
 * 无原生桥时，仅 dev/test 用户可走 dev 旁路直发（后端 LIFE_KLINE_DEV_BYPASS 控制），
 * 生产构建禁用。
 */
async function payAndVerify(order: OrderResult): Promise<VerifyResult> {
  const bridge = (window as any).__nativePay__;
  let receipt: string | undefined;
  let providerData: any;

  if (typeof bridge === "function") {
    const payResult = await bridge(order);
    receipt = payResult?.receipt;
    providerData = payResult?.provider_data;
  } else if (!import.meta.env.DEV) {
    // 生产环境无原生桥 → 不能支付
    throw new Error("支付通道不可用");
  }
  // dev/无桥 + dev 旁路：receipt 为空，后端 dev 旁路直发

  const res = await apiClient.post("/billing/verify", {
    order_id: order.order_id,
    channel: order.channel,
    receipt,
    provider_data: providerData,
  });
  if (res.data?.status === "success") {
    // 发放成功后刷新本地额度
    await fetchAccess();
    return res.data.data;
  }
  throw new Error(res.data?.message || "支付校验失败");
}

/** 一站式：选定产品 → 下单 → 支付 → 校验 → 刷新额度 */
export async function purchase(
  productId: string,
  channel: "iap" | "wechat" | "alipay" = "iap",
): Promise<VerifyResult> {
  const order = await createOrder(productId, channel);
  return payAndVerify(order);
}
