<template>
  <section class="pricing-section">
    <h3 class="pricing-title">解锁你的完整解读</h3>
    <p class="pricing-sub">上面的免费预览只是一个开始。解锁后你可以查看全部 12 个领域的深度解读。</p>

    <div class="pricing-grid">
      <div
        class="pricing-card"
        v-for="plan in plans"
        :key="plan.key"
        :class="{ featured: plan.featured }"
      >
        <div class="plan-badge" v-if="plan.badge">{{ plan.badge }}</div>
        <div class="plan-icon">{{ plan.icon }}</div>
        <h4 class="plan-name">{{ plan.name }}</h4>
        <div class="plan-price">
          <span class="price-symbol">¥</span>
          <span class="price-value">{{ plan.price }}</span>
          <span class="price-unit" v-if="plan.period">/{{ plan.period }}</span>
        </div>
        <ul class="plan-features">
          <li v-for="f in plan.features" :key="f">
            <span class="check">✓</span> {{ f }}
          </li>
        </ul>
        <el-button
          class="plan-btn"
          :type="plan.featured ? 'primary' : 'default'"
          round
          @click="$emit('select', plan.key)"
        >
          {{ plan.cta }}
        </el-button>
      </div>
    </div>

    <p class="pricing-trust">🔒 一次购买，永久可看 · 不满意可退款</p>
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";

defineEmits<{
  select: [key: string];
}>();

const plans = computed(() => [
  {
    key: "full",
    icon: "🌟",
    name: "全领域解锁",
    badge: "最受欢迎",
    price: "29.9",
    period: "",
    featured: true,
    cta: "解锁全部 12 领域",
    features: [
      "12 个领域完整解读",
      "心理层面深度分析",
      "个性化建议方向",
      "AI 对话 3 次免费",
      "永久可看",
    ],
  },
  {
    key: "subscription",
    icon: "👑",
    name: "年度订阅",
    badge: "最超值",
    price: "199",
    period: "年",
    featured: false,
    cta: "订阅年度会员",
    features: [
      "全领域解锁 + AI 无限对话",
      "每月月度报告自动生成",
      "行运提醒与分析",
      "新功能优先体验",
      "7 天免费试用",
    ],
  },
]);
</script>

<style scoped lang="less">
.pricing-section {
  text-align: center;
  padding: 8px 0;
}
.pricing-title {
  margin: 0 0 8px;
  color: #4a3728;
  font-size: 22px;
  font-weight: 700;
}
.pricing-sub {
  margin: 0 auto 28px;
  max-width: 480px;
  color: #8b7355;
  font-size: 14px;
  line-height: 1.7;
}
.pricing-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 14px;
  max-width: 560px;
  margin: 0 auto;
}
.pricing-card {
  position: relative;
  padding: 28px 20px 22px;
  border-radius: 20px;
  border: 1px solid rgba(0,0,0,0.06);
  background: rgba(255,255,255, 0.55);
  backdrop-filter: blur(10px);
  text-align: center;
  transition: all 0.25s;
}
.pricing-card.featured {
  border-color: rgba(255,154,139, 0.25);
  background: rgba(255,154,139, 0.04);
}
.plan-badge {
  position: absolute;
  top: -10px;
  left: 50%;
  transform: translateX(-50%);
  padding: 3px 12px;
  border-radius: 999px;
  background: #ff9a8b;
  color: #020617;
  font-size: 11px;
  font-weight: 700;
  white-space: nowrap;
}
.plan-icon { font-size: 28px; margin-bottom: 8px; }
.plan-name {
  margin: 0 0 12px;
  color: #f1f5f9;
  font-size: 18px;
  font-weight: 600;
}
.plan-price {
  margin-bottom: 16px;
}
.price-symbol { color: #8b7355; font-size: 18px; }
.price-value { color: #4a3728; font-size: 36px; font-weight: 700; }
.price-unit { color: #a89880; font-size: 14px; }
.plan-features {
  list-style: none;
  padding: 0;
  margin: 0 0 20px;
  text-align: left;
  display: grid;
  gap: 8px;
}
.plan-features li {
  color: #8b7355;
  font-size: 13px;
  line-height: 1.5;
}
.check {
  color: #10b981;
  margin-right: 4px;
}
.plan-btn {
  width: 100%;
  font-weight: 600;
}
.pricing-trust {
  margin-top: 18px;
  color: #a89880;
  font-size: 12px;
}

@media (max-width: 560px) {
  .pricing-grid {
    grid-template-columns: 1fr;
  }
}
</style>
