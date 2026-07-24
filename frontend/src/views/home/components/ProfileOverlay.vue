<template>
  <transition name="profile-slide">
    <div v-if="visible" class="profile-wrapper">
      <!-- 半透明遮罩 -->
      <div class="profile-backdrop" @click="$emit('close')"></div>

      <!-- 面板：从左滑出 -->
      <div class="profile-panel">
        <!-- 关闭按钮 -->
        <button class="profile-close" @click="$emit('close')">✕</button>

        <!-- ═══ 内容 ═══ -->
        <div class="profile-content">
          <!-- 头像 + 身份 -->
          <div class="profile-hero">
            <div class="ph-avatar">
              <SpiritAvatar planet="SUN" :sign="sunSign" :gender="gender" size="lg" />
            </div>
            <div class="ph-name-row">
              <span v-if="!editingName" class="ph-name">{{ displayName }}</span>
              <input
                v-else
                ref="nameEditInput"
                v-model="editName"
                class="ph-name-input"
                maxlength="12"
                @blur="saveName"
                @keyup.enter="saveName"
              />
              <button class="ph-edit" @click="startEditName">✎</button>
            </div>
            <div class="ph-sign" v-if="sunSignLabel">{{ sunSignEmoji }} {{ sunSignLabel }}</div>
          </div>

          <!-- 上升 / 月亮 -->
          <div class="profile-info" v-if="ascSignLabel || moonSignLabel">
            <div class="pi-row" v-if="ascSignLabel">
              <span class="pi-label">上升</span>
              <span class="pi-value">{{ ascSignLabel }}</span>
            </div>
            <div class="pi-row" v-if="moonSignLabel">
              <span class="pi-label">月亮</span>
              <span class="pi-value">{{ moonSignLabel }}</span>
            </div>
          </div>

          <!-- ═══ 菜单 ═══ -->
          <div class="profile-menu">
            <button class="pm-item pm-item--primary" @click="$emit('go-garden'); $emit('close')">
              <span>🌸</span><span>进入星灵花园</span><span>→</span>
            </button>
            <button class="pm-item" @click="$emit('go-history'); $emit('close')">
              <span>📋</span><span>历史报告</span><span>→</span>
            </button>
            <button class="pm-item" @click="$emit('go-profile'); $emit('close')">
              <span>📝</span><span>编辑档案</span><span>→</span>
            </button>
            <button class="pm-item" @click="$emit('go-diary'); $emit('close')">
              <span>📖</span><span>星灵日记</span><span>→</span>
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
import SpiritAvatar from "@/components/garden/SpiritAvatar.vue";

const props = defineProps<{
  visible: boolean;
  displayName: string;
  sunSign: string;
  sunSignEmoji: string;
  sunSignLabel: string;
  ascSignLabel: string;
  moonSignLabel: string;
  gender: string;
}>();

defineEmits<{
  close: [];
  "go-garden": [];
  "go-history": [];
  "go-onboarding": [];
  "go-profile": [];
  "go-diary": [];
  logout: [];
}>();

const editingName = ref(false);
const editName = ref("");
const nameEditInput = ref<HTMLInputElement | null>(null);

function startEditName() {
  editName.value = props.displayName;
  editingName.value = true;
  nextTick(() => nameEditInput.value?.focus());
}
function saveName() {
  editingName.value = false;
}
</script>

<style scoped>
/* ═══════════════ Transition ═══════════════ */
.profile-slide-enter-active {
  transition: all 0.35s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}
.profile-slide-leave-active {
  transition: all 0.25s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}
.profile-slide-enter-from .profile-panel {
  transform: translateX(-100%);
}
.profile-slide-leave-to .profile-panel {
  transform: translateX(-100%);
}
.profile-slide-enter-from .profile-backdrop,
.profile-slide-leave-to .profile-backdrop {
  opacity: 0;
}

/* ═══════════════ Wrapper ═══════════════ */
.profile-wrapper {
  position: fixed;
  inset: 0;
  z-index: 210;
  display: flex;
  justify-content: flex-start;
}

/* ═══════════════ Backdrop ═══════════════ */
.profile-backdrop {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.35);
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
  transition: opacity 0.35s ease;
}

/* ═══════════════ Panel ═══════════════ */
.profile-panel {
  position: relative;
  width: 380px;
  max-width: 100%;
  height: 100%;
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border-right: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 8px 0 32px rgba(0, 0, 0, 0.08);
  display: flex;
  flex-direction: column;
  transition: transform 0.35s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  overflow-y: auto;
}

.profile-panel::-webkit-scrollbar {
  width: 3px;
}
.profile-panel::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 2px;
}

/* ═══════════════ Close ═══════════════ */
.profile-close {
  position: absolute;
  top: 16px;
  right: 16px;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: 1px solid rgba(255, 255, 255, 0.2);
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.7);
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  font-family: inherit;
  z-index: 1;
}
.profile-close:hover {
  background: rgba(255, 255, 255, 0.25);
  color: #fff;
  transform: scale(1.08);
}

/* ═══════════════ Content ═══════════════ */
.profile-content {
  padding: 24px;
  padding-top: calc(24px + env(safe-area-inset-top, 0px));
  padding-bottom: calc(24px + env(safe-area-inset-bottom, 0px));
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* ═══════════════ Hero ═══════════════ */
.profile-hero {
  text-align: center;
  margin-bottom: 4px;
}
.ph-avatar {
  margin-bottom: 10px;
}
.ph-name-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-bottom: 4px;
}
.ph-name {
  font-size: 18px;
  font-weight: 700;
  color: #fff;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  letter-spacing: 1px;
}
.ph-name-input {
  font-size: 18px;
  font-weight: 600;
  background: rgba(255, 255, 255, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 10px;
  padding: 4px 10px;
  color: #fff;
  outline: none;
  font-family: inherit;
  width: 130px;
  text-align: center;
}
.ph-edit {
  border: none;
  background: none;
  color: rgba(255, 255, 255, 0.35);
  cursor: pointer;
  font-size: 14px;
}
.ph-edit:hover {
  color: rgba(255, 255, 255, 0.7);
}
.ph-sign {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.7);
  letter-spacing: 1px;
  text-shadow: 0 1px 4px rgba(0, 0, 0, 0.15);
}

/* ═══════════════ Info ═══════════════ */
.profile-info {
  display: flex;
  gap: 10px;
  justify-content: center;
}
.pi-row {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: 8px 18px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.06);
}
.pi-label {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.45);
  letter-spacing: 1px;
}
.pi-value {
  font-size: 13px;
  color: #fff;
  font-weight: 500;
}

/* ═══════════════ Menu ═══════════════ */
.profile-menu {
  display: flex;
  flex-direction: column;
  gap: 2px;
  margin-top: 8px;
}
.pm-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 16px;
  border-radius: 14px;
  border: none;
  background: transparent;
  color: rgba(255, 255, 255, 0.75);
  font-size: 14px;
  font-family: inherit;
  cursor: pointer;
  transition: all 0.2s;
  text-align: left;
}
.pm-item:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}
.pm-item span:last-child {
  margin-left: auto;
  opacity: 0.35;
}
.pm-item--primary {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.9);
  font-weight: 600;
}
.pm-item--primary:hover {
  background: rgba(255, 255, 255, 0.16);
  border-color: rgba(255, 255, 255, 0.2);
}
.pm-item--out {
  opacity: 0.45;
  margin-top: 12px;
}
.pm-item--out:hover {
  opacity: 1;
  color: #ff8a80;
}
</style>
