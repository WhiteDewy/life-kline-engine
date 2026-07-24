<template>
  <teleport to="body">
    <div class="payment-overlay" v-if="visible" @click.self="$emit('close')">
      <div class="payment-modal">
        <button class="close-btn" @click="$emit('close')">✕</button>

        <div class="modal-head">
          <span class="modal-icon">🌟</span>
          <h3 class="modal-title">{{ title }}</h3>
          <p class="modal-price">
            <span class="price-num">¥{{ price }}</span>
            <span v-if="period" class="price-period">/{{ period }}</span>
          </p>
        </div>

        <div class="modal-body">
          <div class="pay-methods">
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

          <div class="qr-placeholder">
            <div class="qr-box">
              <span class="qr-text">扫码支付<br/>{{ payMethod === 'wechat' ? '微信' : '支付宝' }}</span>
            </div>
            <p class="qr-hint">（支付功能接入中，当前为模拟体验）</p>
          </div>

          <el-button
            class="simulate-btn"
            type="primary"
            round
            size="large"
            :loading="processing"
            @click="simulatePayment"
          >
            {{ processing ? '处理中…' : '模拟支付完成' }}
          </el-button>
        </div>

        <p class="modal-trust">🔒 安全支付 · 不满意可退款 · 数据加密传输</p>
      </div>
    </div>
  </teleport>
</template>

<script setup lang="ts">
import { ref, computed } from "vue";
import { PRICING } from "@/utils/payment";

const props = defineProps<{
  visible: boolean;
  planKey?: string;
}>();

const emit = defineEmits<{
  close: [];
  confirm: [planKey: string];
}>();

const payMethod = ref<"wechat" | "alipay">("wechat");
const processing = ref(false);

const plan = computed(() => {
  if (props.planKey === "full") return { ...PRICING.fullAccess, period: "" };
  if (props.planKey === "subscription") return PRICING.subscription;
  return { ...PRICING.singleDomain, period: "" };
});

const title = computed(() => plan.value.label);
const price = computed(() => plan.value.price);
const period = computed(() => (plan.value as any).period || "");

function simulatePayment() {
  processing.value = true;
  setTimeout(() => {
    processing.value = false;
    emit("confirm", props.planKey || "full");
  }, 1200);
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
.close-btn:hover { color: #4a3728; border-color: rgba(255,255,255,0.15); }
.modal-head {
  text-align: center;
  margin-bottom: 24px;
}
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
.modal-body { margin-bottom: 16px; }
.pay-methods {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}
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
.qr-placeholder {
  text-align: center;
  margin-bottom: 20px;
}
.qr-box {
  width: 160px;
  height: 160px;
  margin: 0 auto;
  border-radius: 16px;
  border: 1px solid rgba(255,255,255,0.08);
  background: rgba(255,255,255,0.03);
  display: flex;
  align-items: center;
  justify-content: center;
}
.qr-text {
  color: #64748b;
  font-size: 13px;
  line-height: 1.6;
}
.qr-hint {
  margin: 10px 0 0;
  color: #475569;
  font-size: 12px;
}
.simulate-btn {
  width: 100%;
  font-weight: 600;
}
.modal-trust {
  margin: 0;
  text-align: center;
  color: #64748b;
  font-size: 12px;
}
</style>
