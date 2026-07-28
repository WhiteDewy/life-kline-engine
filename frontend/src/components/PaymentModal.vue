<template>
  <teleport to="body">
    <div class="payment-overlay" v-if="visible" @click.self="$emit('close')">
      <div class="payment-modal">
        <button class="close-btn" @click="$emit('close')">✕</button>

        <div class="modal-head">
          <span class="modal-icon">🌟</span>
          <h3 class="modal-title">{{ product?.name || "购买" }}</h3>
          <p class="modal-price">
            <span class="price-num">¥{{ product?.price_cny ?? price }}</span>
            <span v-if="productType === 'vip'" class="price-period">
              / {{ durationDays }}天
            </span>
          </p>
          <p v-if="productType === 'coin'" class="modal-sub">
            {{ product?.total_coins }} 星币
            <span v-if="product?.bonus">（含赠送 {{ product.bonus }}）</span>
          </p>
        </div>

        <div class="modal-body">
          <!-- 安卓：微信/支付宝；iOS：由父组件传 channel="iap" 走苹果内购 -->
          <div v-if="channel !== 'iap'" class="pay-methods">
            <button
              class="pay-method"
              :class="{ active: payMethod === 'wechat' }"
              @click="payMethod = 'wechat'"
            >
              <span class="pay-icon">💚</span>
              <span>微信支付</span>
            </button>
            <button
              class="pay-method"
              :class="{ active: payMethod === 'alipay' }"
              @click="payMethod = 'alipay'"
            >
              <span class="pay-icon">💙</span>
              <span>支付宝</span>
            </button>
          </div>
          <div v-else class="iap-hint">通过 Apple 内购完成支付</div>

          <p v-if="error" class="pay-error">{{ error }}</p>

          <el-button
            class="pay-btn"
            type="primary"
            round
            size="large"
            :loading="processing"
            @click="onConfirm"
          >
            {{ processing ? "支付处理中…" : `确认支付 ¥${product?.price_cny ?? price}` }}
          </el-button>
        </div>

        <p class="modal-trust">🔒 安全支付 · 不满意可退款 · 数据加密传输</p>
      </div>
    </div>
  </teleport>
</template>

<script setup lang="ts">
import { ref, computed, watch } from "vue";
import { useAccess, purchase, type VerifyResult } from "@/utils/payment";

const props = defineProps<{
  visible: boolean;
  /** 后端产品 id：coin_100 / monthly_auto / ... */
  productId?: string;
  /** 支付渠道：iOS 传 'iap'，安卓传 'wechat'/'alipay' */
  channel?: "iap" | "wechat" | "alipay";
  /** 兜底显示价（pricing 未加载时） */
  price?: number;
}>();

const emit = defineEmits<{
  close: [];
  success: [result: VerifyResult];
}>();

const { pricing, fetchPricing } = useAccess();
const payMethod = ref<"wechat" | "alipay">("wechat");
const processing = ref(false);
const error = ref("");

const channel = computed(() => props.channel || "iap");

const product = computed(() => {
  const pid = props.productId;
  if (!pid || !pricing.value) return null;
  const coin = pricing.value.coin_packages.find((p) => p.id === pid);
  if (coin) return coin;
  const vip = pricing.value.vip_plans[pid];
  if (vip) return { ...vip, total_coins: 0, bonus: 0 };
  return null;
});

const productType = computed(() => {
  if (!props.productId || !pricing.value) return "coin";
  return pricing.value.coin_packages.some((p) => p.id === props.productId)
    ? "coin"
    : "vip";
});

const durationDays = computed(() => {
  if (productType.value !== "vip" || !props.productId || !pricing.value) return 0;
  return pricing.value.vip_plans[props.productId]?.duration_days || 0;
});

watch(
  () => props.visible,
  async (v) => {
    if (v) {
      error.value = "";
      await fetchPricing();
    }
  },
  { immediate: true },
);

async function onConfirm() {
  if (!props.productId) return;
  error.value = "";
  processing.value = true;
  try {
    const ch = channel.value === "iap" ? "iap" : payMethod.value;
    const result = await purchase(props.productId, ch);
    emit("success", result);
  } catch (e: any) {
    error.value = e?.message || "支付失败，请稍后重试";
  } finally {
    processing.value = false;
  }
}
</script>

<style scoped lang="less">
.payment-overlay {
  position: fixed;
  inset: 0;
  z-index: 2000;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(2, 6, 23, 0.8);
  backdrop-filter: blur(8px);
}
.payment-modal {
  position: relative;
  width: 92%;
  max-width: 420px;
  padding: 32px 28px 24px;
  border-radius: 24px;
  border: 1px solid rgba(0,0,0,0.06);
  background: #0f172a;
  box-shadow: 0 24px 64px rgba(0, 0, 0, 0.6);
}
.close-btn {
  position: absolute;
  top: 14px;
  right: 14px;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: 1px solid rgba(255,255,255,0.08);
  background: transparent;
  color: #8b7355;
  cursor: pointer;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.modal-head { text-align: center; margin-bottom: 24px; }
.modal-icon { font-size: 32px; }
.modal-title {
  margin: 8px 0 6px;
  color: #4a3728;
  font-size: 20px;
  font-weight: 700;
}
.modal-price { margin: 0; }
.price-num { color: #ff9a8b; font-size: 32px; font-weight: 700; }
.price-period { color: #64748b; font-size: 14px; }
.modal-sub { margin: 6px 0 0; color: #8b7355; font-size: 13px; }
.modal-body { margin-bottom: 16px; }
.pay-methods { display: flex; gap: 10px; margin-bottom: 20px; }
.pay-method {
  flex: 1;
  padding: 12px;
  border-radius: 12px;
  border: 1px solid rgba(255,255,255,0.06);
  background: rgba(255,255,255,0.02);
  color: #8b7355;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  font-size: 14px;
  transition: all 0.2s;
}
.pay-method.active {
  border-color: rgba(255,154,139, 0.3);
  background: rgba(255,154,139, 0.06);
  color: #4a3728;
}
.pay-icon { font-size: 18px; }
.iap-hint { text-align: center; color: #8b7355; font-size: 13px; margin-bottom: 20px; }
.pay-error {
  margin: 0 0 14px;
  color: #ff6b6b;
  font-size: 13px;
  text-align: center;
}
.pay-btn { width: 100%; font-weight: 600; }
.modal-trust { margin: 0; text-align: center; color: #64748b; font-size: 12px; }
</style>
