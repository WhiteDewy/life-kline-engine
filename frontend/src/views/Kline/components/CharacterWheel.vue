<template>
  <div class="character-wheel-section">
    <div class="section-header">
      <h3>你的十二星座角色</h3>
      <span class="section-hint">点击角色开始对话</span>
    </div>

    <div class="wheel-container">
      <svg viewBox="0 0 400 400" class="character-wheel-svg">
        <!-- 背景环 -->
        <circle cx="200" cy="200" r="180" fill="none" stroke="rgba(255,255,255,0.05)" stroke-width="60" />
        <circle cx="200" cy="200" r="120" fill="none" stroke="rgba(255,255,255,0.03)" stroke-width="40" />

        <!-- 12 段 -->
        <g v-for="(item, index) in segments" :key="item.sign">
          <!-- 扇形背景 -->
          <path
            :d="arcPath(200, 200, 155, 180, index)"
            :fill="item.fillColor"
            :stroke="item.strokeColor"
            stroke-width="1"
            :opacity="item.opacity"
            class="segment-path"
            @click="$emit('select', item.sign)"
            style="cursor: pointer; transition: opacity 0.3s;"
          />
          <!-- 标签 -->
          <text
            :x="labelX(200, 170, index)"
            :y="labelY(200, 170, index)"
            :fill="item.textColor"
            :font-size="item.isFeatured ? 13 : 11"
            :font-weight="item.isFeatured ? 'bold' : 'normal'"
            text-anchor="middle"
            dominant-baseline="central"
            class="sign-label"
            @click="$emit('select', item.sign)"
            style="cursor: pointer;"
          >
            {{ item.symbol }}
          </text>
          <!-- 存在感内圈 -->
          <circle
            :cx="innerDotX(200, 135, index)"
            :cy="innerDotY(200, 135, index)"
            :r="Math.max(2, item.presenceScore / 25)"
            :fill="item.fillColor"
            :opacity="0.8"
          />
        </g>

        <!-- 中心文字 -->
        <text x="200" y="195" fill="rgba(255,255,255,0.6)" font-size="12" text-anchor="middle">
          存在感
        </text>
        <text x="200" y="210" fill="rgba(255,255,255,0.3)" font-size="10" text-anchor="middle">
          点击角色对话
        </text>
      </svg>
    </div>

    <!-- 今日登场角色 -->
    <div v-if="featured && featured.length > 0" class="featured-section">
      <div class="featured-header">{{ dailyTheme }}</div>
      <div class="featured-cards">
        <div
          v-for="(fc, i) in featured"
          :key="fc.sign"
          class="featured-card"
          :style="{ borderLeftColor: fc.visual_color }"
          @click="$emit('select', fc.sign)"
        >
          <div class="fc-rank">#{{ i + 1 }}</div>
          <div class="fc-info">
            <div class="fc-name">
              {{ fc.name }}
              <span class="fc-archetype">{{ fc.archetype }}</span>
            </div>
            <div class="fc-message">{{ fc.daily_message }}</div>
            <div class="fc-reason">{{ fc.reason }}</div>
          </div>
          <div class="fc-score" :style="{ color: fc.visual_color }">
            {{ fc.activation_score }}%
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { SIGN_EMOJI_MAP } from '@/config/zodiac'

export interface CharacterWheelSegment {
  sign: string
  symbol: string
  fillColor: string
  strokeColor: string
  opacity: number
  textColor: string
  isFeatured: boolean
  presenceScore: number
}

const props = defineProps<{
  characters?: Record<string, any>
  sortedByPresence?: Array<{ sign: string; name: string; presence_score: number; role_tag: string }>
  featured?: Array<{
    sign: string
    name: string
    archetype: string
    activation_score: number
    daily_message: string
    reason: string
    visual_color: string
  }>
  activationScores?: Record<string, number>
  dailyTheme?: string
}>()

defineEmits<{
  select: [sign: string]
}>()

const SIGN_SYMBOLS = SIGN_EMOJI_MAP

const SIGN_ORDER = [
  'ARIES', 'TAURUS', 'GEMINI', 'CANCER',
  'LEO', 'VIRGO', 'LIBRA', 'SCORPIO',
  'SAGITTARIUS', 'CAPRICORN', 'AQUARIUS', 'PISCES',
]

const segments = computed<CharacterWheelSegment[]>(() => {
  const featuredSet = new Set((props.featured || []).map(f => f.sign))

  return SIGN_ORDER.map(sign => {
    const char = props.characters?.[sign]
    const persona = char?.persona || {}
    const presenceScore = char?.presence_score || 0
    const isFeatured = featuredSet.has(sign)
    const color = persona.visual_color || '#666'

    return {
      sign,
      symbol: SIGN_SYMBOLS[sign] || sign,
      fillColor: color,
      strokeColor: isFeatured ? '#fff' : 'transparent',
      opacity: isFeatured ? 0.35 : Math.max(0.08, presenceScore / 200),
      textColor: isFeatured ? '#fff' : 'rgba(255,255,255,0.5)',
      isFeatured,
      presenceScore,
    }
  })
})

function arcPath(cx: number, cy: number, innerR: number, outerR: number, index: number): string {
  const startAngle = (index * 30 - 105) * Math.PI / 180
  const endAngle = ((index + 1) * 30 - 105) * Math.PI / 180

  const x1 = cx + outerR * Math.cos(startAngle)
  const y1 = cy + outerR * Math.sin(startAngle)
  const x2 = cx + outerR * Math.cos(endAngle)
  const y2 = cy + outerR * Math.sin(endAngle)
  const x3 = cx + innerR * Math.cos(endAngle)
  const y3 = cy + innerR * Math.sin(endAngle)
  const x4 = cx + innerR * Math.cos(startAngle)
  const y4 = cy + innerR * Math.sin(startAngle)

  const large = 0
  return `M ${x1} ${y1} A ${outerR} ${outerR} 0 ${large} 1 ${x2} ${y2} L ${x3} ${y3} A ${innerR} ${innerR} 0 ${large} 0 ${x4} ${y4} Z`
}

function labelX(cx: number, r: number, index: number): number {
  const angle = (index * 30 - 90) * Math.PI / 180
  return cx + r * Math.cos(angle)
}

function labelY(cy: number, r: number, index: number): number {
  const angle = (index * 30 - 90) * Math.PI / 180
  return cy + r * Math.sin(angle)
}

function innerDotX(cx: number, r: number, index: number): number {
  const angle = (index * 30 - 90) * Math.PI / 180
  return cx + r * Math.cos(angle)
}

function innerDotY(cy: number, r: number, index: number): number {
  const angle = (index * 30 - 90) * Math.PI / 180
  return cy + r * Math.sin(angle)
}
</script>

<style scoped>
.character-wheel-section {
  margin: 32px 0;
  padding: 24px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 20px;
}

.section-header h3 {
  margin: 0;
  font-size: 18px;
  color: rgba(255, 255, 255, 0.9);
}

.section-hint {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.4);
}

.wheel-container {
  display: flex;
  justify-content: center;
  margin-bottom: 24px;
}

.character-wheel-svg {
  width: 100%;
  max-width: 380px;
  height: auto;
}

.segment-path:hover {
  opacity: 0.7 !important;
  filter: brightness(1.5);
}

.sign-label:hover {
  fill: #fff !important;
}

.featured-section {
  margin-top: 8px;
}

.featured-header {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 12px;
}

.featured-cards {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.featured-card {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 14px 16px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.03);
  border-left: 3px solid;
  cursor: pointer;
  transition: background 0.2s;
}

.featured-card:hover {
  background: rgba(255, 255, 255, 0.06);
}

.fc-rank {
  font-size: 18px;
  font-weight: bold;
  color: rgba(255, 255, 255, 0.3);
  min-width: 28px;
}

.fc-info {
  flex: 1;
  min-width: 0;
}

.fc-name {
  font-size: 14px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  margin-bottom: 4px;
}

.fc-archetype {
  font-size: 12px;
  font-weight: normal;
  color: rgba(255, 255, 255, 0.4);
  margin-left: 6px;
}

.fc-message {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.7);
  line-height: 1.5;
  margin-bottom: 4px;
}

.fc-reason {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.35);
}

.fc-score {
  font-size: 16px;
  font-weight: bold;
  white-space: nowrap;
}
</style>
