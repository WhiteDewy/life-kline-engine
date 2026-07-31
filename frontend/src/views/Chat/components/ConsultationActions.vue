<template>
  <div v-if="actions.length" class="consult-actions">
    <button
      v-for="action in visibleActions"
      :key="action"
      class="consult-action"
      @click="$emit('action', action)"
    >
      {{ labelFor(action) }}
    </button>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{ actions: string[] }>();
defineEmits<{ (e: "action", action: string): void }>();

const LABELS: Record<string, string> = {
  continue: "继续",
  deepen: "深入",
  next_topic: "下一个话题",
  pause: "暂停",
  resume: "继续聊",
  question: "提问",
  confirm: "确认",
  partial: "部分像",
  reject: "不是这样",
  uncertain: "还不确定",
  close: "收尾",
};

const visibleActions = computed(() =>
  props.actions.filter((a) => LABELS[a]).slice(0, 4),
);

function labelFor(action: string) {
  return LABELS[action] ?? action;
}
</script>

<style scoped>
.consult-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
}
.consult-action {
  padding: 5px 12px;
  border-radius: 14px;
  border: 1px solid rgba(184, 125, 90, 0.3);
  background: rgba(255, 255, 255, 0.6);
  color: var(--chat-color, #b87d5a);
  font-size: 12px;
  cursor: pointer;
  transition: all 0.15s;
}
.consult-action:hover {
  background: var(--chat-color, #b87d5a);
  color: #fff;
}
</style>
