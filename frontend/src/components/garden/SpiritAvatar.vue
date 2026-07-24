<template>
  <div
    class="spirit-avatar"
    :class="[sizeClass, { 'spirit-avatar--has-img': !!imgSrc }]"
    :style="imgSrc ? {} : { color: color || undefined }"
  >
    <img v-if="imgSrc" :src="imgSrc" :alt="name" class="avatar-img" />
    <span v-else class="avatar-symbol">{{ displaySymbol }}</span>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { getSpiritImage, getSunSignImage, getPlanetAvatarImage, SPIRIT_SYMBOLS } from "@/config/spiritAssets";

const props = withDefaults(
  defineProps<{
    planet?: string;
    symbol?: string;
    color?: string;
    name?: string;
    size?: "sm" | "md" | "lg" | "xl";
    sign?: string;        // 行星落座（用于匹配该星座的图片作为头像皮肤）
    gender?: string | null; // 用户性别
  }>(),
  { size: "md" }
);

const imgSrc = computed(() => {
  if (!props.planet) return "";
  // 太阳星灵 → 优先按 sign+gender 匹配 24 张图片
  if (props.planet === "SUN" && props.sign) {
    const sunImg = getSunSignImage(props.sign, props.gender);
    if (sunImg) return sunImg;
  }
  // 任意行星 + 落座 → 按 planet+sign 获取星座皮肤头像
  if (props.sign) {
    const avatarImg = getPlanetAvatarImage(props.planet, props.sign);
    if (avatarImg) return avatarImg;
  }
  // 通用 fallback
  return getSpiritImage(props.planet);
});

const displaySymbol = computed(() => {
  if (props.symbol) return props.symbol;
  if (props.planet) return SPIRIT_SYMBOLS[props.planet] || "●";
  return "●";
});

const sizeClass = computed(() => `spirit-avatar--${props.size}`);
</script>

<style scoped lang="less">
.spirit-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  flex-shrink: 0;
  overflow: hidden;
}
.spirit-avatar--sm {
  width: 28px;
  height: 28px;
  font-size: 15px;
}
.spirit-avatar--md {
  width: 48px;
  height: 48px;
  font-size: 24px;
}
.spirit-avatar--lg {
  width: 64px;
  height: 64px;
  font-size: 30px;
}
.spirit-avatar--xl {
  width: 80px;
  height: 80px;
  font-size: 38px;
}

.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-symbol {
  line-height: 1;
  text-align: center;
}
</style>
