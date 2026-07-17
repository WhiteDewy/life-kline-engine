import { ref, computed } from "vue";

const STORAGE_KEY = "lk_purchases";

interface PurchaseRecord {
  reportId: string;
  type: "domain" | "full" | "subscription";
  domain?: string;
  purchasedAt: string;
}

function loadPurchases(): PurchaseRecord[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function savePurchases(records: PurchaseRecord[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(records));
}

const purchases = ref<PurchaseRecord[]>(loadPurchases());

export function usePayment() {
  const isPurchased = (reportId: string, domain?: string) => {
    return purchases.value.some((p) => {
      if (p.reportId !== reportId) return false;
      if (p.type === "full" || p.type === "subscription") return true;
      if (domain && p.type === "domain" && p.domain === domain) return true;
      return false;
    });
  };

  const hasFullAccess = (reportId: string) => {
    return purchases.value.some(
      (p) => p.reportId === reportId && (p.type === "full" || p.type === "subscription")
    );
  };

  const isSubscriber = computed(() => {
    return purchases.value.some((p) => p.type === "subscription");
  });

  const unlockedDomains = (reportId: string) => {
    return purchases.value
      .filter((p) => p.reportId === reportId)
      .map((p) => p.domain)
      .filter(Boolean) as string[];
  };

  function recordPurchase(reportId: string, type: PurchaseRecord["type"], domain?: string) {
    purchases.value.push({
      reportId,
      type,
      domain,
      purchasedAt: new Date().toISOString(),
    });
    savePurchases(purchases.value);
  }

  function resetAll() {
    purchases.value = [];
    savePurchases([]);
  }

  return {
    purchases,
    isPurchased,
    hasFullAccess,
    isSubscriber,
    unlockedDomains,
    recordPurchase,
    resetAll,
  };
}

export const PRICING = {
  singleDomain: { price: 9.9, label: "单领域解锁" },
  fullAccess: { price: 29.9, label: "全领域解锁" },
  subscription: { price: 199, label: "年度订阅", period: "年" },
};
