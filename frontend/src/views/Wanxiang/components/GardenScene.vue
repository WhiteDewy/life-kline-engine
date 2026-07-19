<template>
  <div class="garden-scene" :style="transparent ? { background: 'transparent' } : {}">
    <!-- 星空层 -->
    <div class="stars-layer">
      <span
        v-for="star in stars"
        :key="star.id"
        class="star"
        :style="{
          left: star.x + '%',
          top: star.y + '%',
          width: star.size + 'px',
          height: star.size + 'px',
          animationDelay: star.delay + 's',
          animationDuration: star.duration + 's',
        }"
      ></span>
    </div>

    <!-- 浮云层 -->
    <div class="clouds-layer">
      <div
        v-for="cloud in clouds"
        :key="cloud.id"
        class="cloud"
        :style="{
          top: cloud.y + '%',
          animationDuration: cloud.duration + 's',
          animationDelay: cloud.delay + 's',
          opacity: cloud.opacity,
          transform: 'scale(' + cloud.scale + ')',
        }"
      >
        <svg viewBox="0 0 120 60" class="cloud-svg">
          <ellipse cx="40" cy="35" rx="35" ry="20" :fill="cloud.color" />
          <ellipse cx="65" cy="25" rx="30" ry="22" :fill="cloud.color" />
          <ellipse cx="85" cy="35" rx="28" ry="18" :fill="cloud.color" />
        </svg>
      </div>
    </div>

    <!-- 柔光粒子 -->
    <div class="particles-layer">
      <span
        v-for="p in particles"
        :key="p.id"
        class="particle"
        :style="{
          left: p.x + '%',
          top: p.y + '%',
          width: p.size + 'px',
          height: p.size + 'px',
          background: p.color,
          animationDelay: p.delay + 's',
          animationDuration: p.duration + 's',
        }"
      ></span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";

withDefaults(defineProps<{ transparent?: boolean }>(), { transparent: false });

const stars = computed(() =>
  Array.from({ length: 40 }, (_, i) => ({
    id: i,
    x: Math.random() * 100,
    y: Math.random() * 60,
    size: 1.5 + Math.random() * 2.5,
    delay: Math.random() * 4,
    duration: 2 + Math.random() * 3,
  }))
);

const clouds = computed(() =>
  Array.from({ length: 5 }, (_, i) => ({
    id: i,
    y: 5 + i * 18 + Math.random() * 8,
    duration: 30 + Math.random() * 40,
    delay: -(Math.random() * 30),
    opacity: 0.3 + Math.random() * 0.4,
    scale: 0.6 + Math.random() * 1.2,
    color: i % 2 === 0 ? "rgba(255,255,255,0.7)" : "rgba(255,240,245,0.5)",
  }))
);

const particles = computed(() =>
  Array.from({ length: 15 }, (_, i) => ({
    id: i,
    x: Math.random() * 100,
    y: Math.random() * 100,
    size: 3 + Math.random() * 8,
    delay: Math.random() * 6,
    duration: 4 + Math.random() * 6,
    color: [
      "rgba(255, 154, 139, 0.3)",
      "rgba(240, 192, 96, 0.3)",
      "rgba(155, 196, 208, 0.3)",
      "rgba(232, 160, 191, 0.25)",
    ][Math.floor(Math.random() * 4)],
  }))
);
</script>

<style scoped>
.garden-scene {
  position: fixed;
  inset: 0;
  z-index: 0;
  overflow: hidden;
  pointer-events: none;
  background: linear-gradient(
    180deg,
    var(--garden-bg-1, #fff5ee) 0%,
    var(--garden-bg-2, #ffefd5) 30%,
    var(--garden-bg-2, #fff0f5) 60%,
    var(--garden-bg-1, #f0f4ff) 100%
  );
  transition: background 0.6s ease;
}

/* ── 星星 ── */
.stars-layer {
  position: absolute;
  inset: 0;
}
.star {
  position: absolute;
  display: block;
  border-radius: 50%;
  background: rgba(240, 192, 96, 0.6);
  animation: twinkle ease-in-out infinite;
}
@keyframes twinkle {
  0%,
  100% {
    opacity: 0.2;
    transform: scale(1);
  }
  50% {
    opacity: 0.8;
    transform: scale(1.5);
  }
}

/* ── 云朵 ── */
.clouds-layer {
  position: absolute;
  inset: 0;
}
.cloud {
  position: absolute;
  left: -150px;
  animation: drift linear infinite;
}
.cloud-svg {
  width: 120px;
  height: 60px;
}
@keyframes drift {
  0% {
    transform: translateX(-150px);
  }
  100% {
    transform: translateX(calc(100vw + 150px));
  }
}

/* ── 柔光粒子 ── */
.particles-layer {
  position: absolute;
  inset: 0;
}
.particle {
  position: absolute;
  border-radius: 50%;
  filter: blur(3px);
  animation: float-particle ease-in-out infinite;
}
@keyframes float-particle {
  0%,
  100% {
    transform: translateY(0) translateX(0);
    opacity: 0;
  }
  30% {
    opacity: 0.6;
  }
  50% {
    transform: translateY(-30px) translateX(10px);
    opacity: 0.8;
  }
  70% {
    opacity: 0.4;
  }
}
</style>
