<template>
  <div class="sun-card">
    <div class="sun-card-header">
      <span class="sun-badge">【日{{ signLabel }}】{{ house }}宫</span>
      <span class="sun-transit" v-if="transitStatus">{{ transitStatus }}</span>
    </div>

    <div class="sun-avatar-wrap">
      <div class="sun-avatar-ring" :style="{ borderColor: color }">
        <SpiritAvatar planet="SUN" :sign="sunSign" :gender="gender" size="xl" />
      </div>
      <span class="sun-resident-badge">常驻</span>
    </div>

    <h2 class="sun-name">{{ name }}</h2>
    <span class="sun-archetype" :style="{ background: color + '18', color: color }">
      {{ archetype }}
    </span>

    <p class="sun-essence">"{{ essence }}"</p>

    <div class="sun-transit-tags" v-if="transits.length">
      <span
        v-for="t in transits.slice(0, 3)" :key="t.transiting_label + t.aspect_label"
        class="transit-chip" :class="{ 'transit-chip--applying': t.is_applying }"
      >
        {{ t.transiting_label }}{{ t.aspect_label }}{{ t.is_applying ? ' · 入相' : '' }}
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import SpiritAvatar from "@/views/Wanxiang/components/SpiritAvatar.vue";

defineProps<{
  signLabel: string
  house: number
  transitStatus: string
  sunSign: string
  gender: string
  color: string
  name: string
  archetype: string
  essence: string
  transits: any[]
}>()
</script>

<style scoped>
.sun-card {
  position: relative; border-radius: 28px; overflow: hidden;
  background: linear-gradient(135deg,
    rgba(255,255,255,0.85) 0%,
    rgba(255,245,238,0.8) 50%,
    rgba(255,240,245,0.7) 100%);
  box-shadow: 0 4px 24px rgba(0,0,0,0.04), 0 1px 4px rgba(0,0,0,0.03);
  border: 1px solid rgba(255,255,255,0.8);
  padding: 28px 24px 24px; text-align: center;
}

.sun-card-header {
  display: flex; flex-direction: column; align-items: center; gap: 4px;
  margin-bottom: 20px;
}
.sun-badge {
  font-size: 18px; font-weight: 700; color: #4a3728; letter-spacing: 2px;
}
.sun-transit {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 5px 16px; border-radius: 14px;
  background: rgba(240,192,96,0.1); font-size: 13px; color: #6b5744;
}

.sun-avatar-wrap { position: relative; display: inline-block; margin-bottom: 14px; }
.sun-avatar-ring {
  width: 96px; height: 96px; border-radius: 50%;
  border: 3px solid; display: flex; align-items: center; justify-content: center;
  background: rgba(255,255,255,0.6);
}
.sun-resident-badge {
  position: absolute; bottom: -6px; left: 50%; transform: translateX(-50%);
  font-size: 11px; font-weight: 700; padding: 3px 12px; border-radius: 12px;
  background: linear-gradient(135deg,#fff9c4,#fff176); color: #f57f17;
  box-shadow: 0 1px 4px rgba(255,193,7,0.2); white-space: nowrap;
}

.sun-name { font-size: 24px; font-weight: 700; color: #4a3728; margin: 0 0 6px; }
.sun-archetype {
  display: inline-block; font-size: 12px; font-weight: 600;
  padding: 4px 14px; border-radius: 12px; margin-bottom: 12px;
}

.sun-essence {
  font-size: 14px; color: #8b7355; font-style: italic;
  line-height: 1.65; margin: 0 auto 16px; max-width: 340px;
}

.sun-transit-tags { display: flex; justify-content: center; gap: 8px; flex-wrap: wrap; }
.transit-chip {
  font-size: 12px; font-weight: 600; padding: 5px 14px; border-radius: 14px;
  background: rgba(255,255,255,0.6); color: #8b7355;
  border: 1px solid rgba(0,0,0,0.05);
}
.transit-chip--applying { border-color: #ff9a8b; color: #e8533f; background: rgba(255,154,139,0.06); }
</style>
