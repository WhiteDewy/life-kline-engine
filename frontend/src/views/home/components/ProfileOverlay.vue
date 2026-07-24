<template>
  <transition name="profile-slide">
    <div v-if="visible" class="profile-wrapper">
      <div class="profile-backdrop" @click="$emit('close')"></div>

      <div class="profile-panel">
        <button class="profile-close" @click="$emit('close')" aria-label="关闭">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M18 6L6 18M6 6l12 12" />
          </svg>
        </button>

        <div class="profile-content">
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
              <button class="ph-edit" @click="startEditName" aria-label="编辑昵称">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                  <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
                </svg>
              </button>
            </div>
            <div v-if="sunSignLabel" class="ph-sign">{{ sunSignEmoji }} {{ sunSignLabel }}</div>
          </div>

          <div v-if="ascSignLabel || moonSignLabel" class="profile-info">
            <div v-if="ascSignLabel" class="pi-row">
              <span class="pi-label">上升</span>
              <span class="pi-value">{{ ascSignLabel }}</span>
            </div>
            <div v-if="moonSignLabel" class="pi-row">
              <span class="pi-label">月亮</span>
              <span class="pi-value">{{ moonSignLabel }}</span>
            </div>
          </div>

          <div class="profile-menu">
            <button class="pm-item pm-item--primary" @click="$emit('go-garden'); $emit('close')">
              <span class="pm-item__icon">🌸</span>
              <span class="pm-item__label">进入星灵花园</span>
              <svg class="pm-item__arrow" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M9 18l6-6-6-6" />
              </svg>
            </button>
            <button class="pm-item" @click="$emit('go-diary'); $emit('close')">
              <span class="pm-item__icon">📖</span>
              <span class="pm-item__label">星灵日记</span>
              <svg class="pm-item__arrow" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M9 18l6-6-6-6" />
              </svg>
            </button>
            <button class="pm-item" @click="$emit('go-history'); $emit('close')">
              <span class="pm-item__icon">📋</span>
              <span class="pm-item__label">历史报告</span>
              <svg class="pm-item__arrow" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M9 18l6-6-6-6" />
              </svg>
            </button>
            <button class="pm-item" @click="$emit('go-profile'); $emit('close')">
              <span class="pm-item__icon">📝</span>
              <span class="pm-item__label">编辑档案</span>
              <svg class="pm-item__arrow" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M9 18l6-6-6-6" />
              </svg>
            </button>
            <button class="pm-item" @click="$emit('go-onboarding'); $emit('close')">
              <span class="pm-item__icon">🔄</span>
              <span class="pm-item__label">重新绘制星盘</span>
              <svg class="pm-item__arrow" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M9 18l6-6-6-6" />
              </svg>
            </button>
            <button class="pm-item pm-item--out" @click="$emit('logout')">
              <span class="pm-item__icon">🚪</span>
              <span class="pm-item__label">退出登录</span>
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

<style scoped lang="less">
.profile-slide-enter-active {
  transition: all var(--duration-normal) var(--ease-smooth);
}

.profile-slide-leave-active {
  transition: all var(--duration-fast) var(--ease-smooth);
}

.profile-slide-enter-from .profile-panel,
.profile-slide-leave-to .profile-panel {
  transform: translateX(-100%);
}

.profile-slide-enter-from .profile-backdrop,
.profile-slide-leave-to .profile-backdrop {
  opacity: 0;
}

.profile-wrapper {
  position: fixed;
  inset: 0;
  z-index: 210;
  display: flex;
  justify-content: flex-start;
}

.profile-backdrop {
  position: absolute;
  inset: 0;
  background: rgba(44, 38, 34, 0.25);
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
  transition: opacity var(--duration-normal) var(--ease-smooth);
}

.profile-panel {
  position: relative;
  width: 340px;
  max-width: 85%;
  height: 100%;
  background: var(--bg-card-glass);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border-right: 1px solid var(--border-light);
  box-shadow: 8px 0 32px rgba(44, 38, 34, 0.08);
  display: flex;
  flex-direction: column;
  transition: transform var(--duration-normal) var(--ease-smooth);
  overflow-y: auto;
}

.profile-panel::-webkit-scrollbar {
  width: 3px;
}

.profile-panel::-webkit-scrollbar-thumb {
  background: var(--border-light);
  border-radius: 2px;
}

.profile-close {
  position: absolute;
  top: var(--space-4);
  right: var(--space-4);
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: 1px solid var(--border-light);
  background: var(--bg-card);
  color: var(--text-tertiary);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--duration-fast) var(--ease-smooth);
  z-index: 1;
}

.profile-close:hover {
  background: var(--bg-elevated);
  color: var(--text-primary);
}

.profile-content {
  padding: var(--space-6);
  padding-top: calc(var(--space-6) + env(safe-area-inset-top, 0px));
  padding-bottom: calc(var(--space-6) + env(safe-area-inset-bottom, 0px));
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

.profile-hero {
  text-align: center;
  margin-bottom: var(--space-1);
}

.ph-avatar {
  margin-bottom: var(--space-3);
}

.ph-name-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  margin-bottom: var(--space-1);
}

.ph-name {
  font-size: var(--text-lg);
  font-weight: var(--font-bold);
  color: var(--text-primary);
  letter-spacing: 0.5px;
}

.ph-name-input {
  font-size: var(--text-lg);
  font-weight: var(--font-bold);
  background: var(--bg-elevated);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  padding: 4px 10px;
  color: var(--text-primary);
  outline: none;
  font-family: inherit;
  width: 130px;
  text-align: center;
}

.ph-name-input:focus {
  border-color: var(--color-primary);
  box-shadow: var(--shadow-glow);
}

.ph-edit {
  color: var(--text-muted);
  padding: 4px;
  border-radius: var(--radius-sm);
  transition: all var(--duration-fast) var(--ease-smooth);
}

.ph-edit:hover {
  color: var(--color-primary);
  background: var(--color-primary-soft);
}

.ph-sign {
  font-size: var(--text-sm);
  color: var(--text-secondary);
  letter-spacing: 0.5px;
}

.profile-info {
  display: flex;
  gap: var(--space-3);
  justify-content: center;
}

.pi-row {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-lg);
  background: rgba(255, 255, 255, 0.5);
  border: 1px solid var(--border-light);
  flex: 1;
}

.pi-label {
  font-size: 10px;
  color: var(--text-tertiary);
  letter-spacing: 1px;
  font-weight: var(--font-medium);
}

.pi-value {
  font-size: var(--text-base);
  color: var(--text-primary);
  font-weight: var(--font-semibold);
}

.profile-menu {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  margin-top: var(--space-2);
}

.pm-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-4);
  border-radius: var(--radius-lg);
  border: none;
  background: transparent;
  color: var(--text-secondary);
  font-size: var(--text-base);
  font-family: inherit;
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-smooth);
  text-align: left;
}

.pm-item:hover {
  background: var(--bg-elevated);
  color: var(--text-primary);
}

.pm-item__icon {
  font-size: var(--text-lg);
  width: 24px;
  text-align: center;
}

.pm-item__label {
  flex: 1;
  font-weight: var(--font-medium);
}

.pm-item__arrow {
  color: var(--text-muted);
  transition: transform var(--duration-fast) var(--ease-smooth);
}

.pm-item:hover .pm-item__arrow {
  transform: translateX(3px);
  color: var(--text-tertiary);
}

.pm-item--primary {
  background: var(--color-primary-soft);
  color: var(--color-primary-dark);
  border: 1px solid rgba(184, 125, 90, 0.12);
}

.pm-item--primary:hover {
  background: var(--color-primary-soft);
  border-color: rgba(184, 125, 90, 0.2);
  box-shadow: var(--shadow-card);
}

.pm-item--primary .pm-item__label {
  font-weight: var(--font-semibold);
}

.pm-item--out {
  opacity: 0.7;
  margin-top: var(--space-2);
}

.pm-item--out:hover {
  opacity: 1;
  color: var(--color-danger);
  background: rgba(184, 92, 92, 0.06);
}

@media (max-width: 380px) {
  .profile-content {
    padding: var(--space-5);
  }
  .profile-panel {
    width: 300px;
  }
}
</style>
