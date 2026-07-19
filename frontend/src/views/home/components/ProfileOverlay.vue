<template>
  <transition name="overlay-fade">
    <div v-if="visible" class="overlay-backdrop" @click.self="$emit('close')">
      <div class="overlay-content">
        <div class="profile-card">
          <button class="detail-close" @click="$emit('close')">✕</button>
          <div class="profile-hero">
            <div class="ph-avatar">
              <SpiritAvatar planet="SUN" :sign="sunSign" :gender="gender" size="lg" />
            </div>
            <div class="ph-name-row">
              <span v-if="!editingName" class="ph-name">{{ displayName }}</span>
              <input v-else ref="nameEditInput" v-model="editName" class="ph-name-input"
                maxlength="12" @blur="saveName" @keyup.enter="saveName" />
              <button class="ph-edit" @click="startEditName">✎</button>
            </div>
            <div class="ph-sign" v-if="sunSignLabel">{{ sunSignEmoji }} {{ sunSignLabel }}</div>
          </div>
          <div class="profile-info" v-if="ascSignLabel || moonSignLabel">
            <div class="pi-row" v-if="ascSignLabel">
              <span class="pi-label">上升</span><span class="pi-value">{{ ascSignLabel }}</span>
            </div>
            <div class="pi-row" v-if="moonSignLabel">
              <span class="pi-label">月亮</span><span class="pi-value">{{ moonSignLabel }}</span>
            </div>
          </div>
          <div class="profile-menu">
            <button class="pm-item" @click="$emit('go-garden'); $emit('close')">
              <span>🌸</span><span>进入星灵花园</span><span>→</span>
            </button>
            <button class="pm-item" @click="$emit('go-history'); $emit('close')">
              <span>📋</span><span>历史报告</span><span>→</span>
            </button>
            <button class="pm-item" @click="$emit('go-onboarding'); $emit('close')">
              <span>🔄</span><span>重新绘制星盘</span><span>→</span>
            </button>
            <button class="pm-item pm-item--out" @click="$emit('logout')">
              <span>🚪</span><span>退出登录</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { ref, nextTick } from "vue";
import SpiritAvatar from "@/views/Wanxiang/components/SpiritAvatar.vue";

const props = defineProps<{
  visible: boolean
  displayName: string
  sunSign: string
  sunSignEmoji: string
  sunSignLabel: string
  ascSignLabel: string
  moonSignLabel: string
  gender: string
}>()

defineEmits<{
  close: []
  'go-garden': []
  'go-history': []
  'go-onboarding': []
  logout: []
}>()

const editingName = ref(false);
const editName = ref("");
const nameEditInput = ref<HTMLInputElement | null>(null);

function startEditName() {
  editName.value = props.displayName;
  editingName.value = true;
  nextTick(() => nameEditInput.value?.focus());
}
function saveName() { editingName.value = false; }
</script>

<style scoped>
.overlay-backdrop {
  position: fixed; inset: 0; z-index: 200;
  background: rgba(0,0,0,0.15); backdrop-filter: blur(4px);
  display: flex; align-items: center; justify-content: center; padding: 20px;
}
.overlay-content {
  width: 100%; max-width: 500px; max-height: 90vh; overflow-y: auto;
  border-radius: 28px;
}
.overlay-content::-webkit-scrollbar { width: 4px; }
.overlay-fade-enter-active { transition: all 0.3s ease; }
.overlay-fade-leave-active { transition: all 0.2s ease; }
.overlay-fade-enter-from { opacity: 0; }
.overlay-fade-enter-from .overlay-content { transform: scale(0.95) translateY(20px); }
.overlay-fade-leave-to { opacity: 0; }

.profile-card {
  position: relative; padding: 36px 24px 24px;
  background: rgba(255,255,255,0.9); backdrop-filter: blur(20px);
  box-shadow: 0 12px 48px rgba(0,0,0,0.12); border: 1px solid rgba(255,255,255,0.5);
  border-radius: 28px; text-align: center;
}
.detail-close {
  position: absolute; top: 16px; right: 16px;
  width: 30px; height: 30px; border-radius: 50%; border: none;
  background: rgba(0,0,0,0.04); color: #8b7355; font-size: 13px;
  cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all 0.2s;
}
.detail-close:hover { background: rgba(0,0,0,0.08); color: #4a3728; }
.profile-hero { margin-bottom: 20px; }
.ph-avatar { margin-bottom: 12px; }
.ph-name-row { display: flex; align-items: center; justify-content: center; gap: 8px; margin-bottom: 4px; }
.ph-name { font-size: 18px; font-weight: 700; color: #4a3728; letter-spacing: 1px; }
.ph-name-input { font-size: 18px; font-weight: 600; background: rgba(0,0,0,0.03); border: 1px solid rgba(0,0,0,0.1); border-radius: 10px; padding: 4px 10px; color: #4a3728; outline: none; font-family: inherit; width: 130px; text-align: center; }
.ph-edit { border: none; background: none; color: rgba(0,0,0,0.25); cursor: pointer; font-size: 14px; }
.ph-edit:hover { color: rgba(0,0,0,0.5); }
.ph-sign { font-size: 14px; color: #ff9a8b; letter-spacing: 1px; }
.profile-info { display: flex; gap: 10px; justify-content: center; margin-bottom: 24px; }
.pi-row { display: flex; flex-direction: column; align-items: center; gap: 2px; padding: 8px 18px; border-radius: 12px; background: rgba(0,0,0,0.02); }
.pi-label { font-size: 10px; color: #8b7355; opacity: 0.5; letter-spacing: 1px; }
.pi-value { font-size: 13px; color: #4a3728; font-weight: 500; }
.profile-menu { display: flex; flex-direction: column; gap: 2px; }
.pm-item {
  display: flex; align-items: center; gap: 10px; padding: 14px 16px; border-radius: 14px;
  border: none; background: transparent; color: #4a3728; font-size: 14px;
  font-family: inherit; cursor: pointer; transition: all 0.2s; text-align: left; opacity: 0.75;
}
.pm-item:hover { background: rgba(0,0,0,0.04); opacity: 1; }
.pm-item span:last-child { margin-left: auto; opacity: 0.3; }
.pm-item--out { opacity: 0.4; margin-top: 12px; }
.pm-item--out:hover { opacity: 1; color: #e8533f; }
</style>
