<template>
  <div class="insight-draft">
    <div class="insight-draft__head">
      <span class="insight-draft__badge">星灵为你起的标题</span>
      <span class="insight-draft__planet">{{ insight.planet }}</span>
    </div>
    <p class="insight-draft__summary">{{ insight.summary }}</p>

    <label class="insight-draft__label">用你自己的话说一句（可编辑）</label>
    <textarea
      v-model="editedQuote"
      class="insight-draft__textarea"
      rows="2"
      :placeholder="insight.user_quote || '比如：我经常先在心里演完一整部剧'"
    />

    <div v-if="insight.growth_action" class="insight-draft__action">
      <span class="insight-draft__action-label">可观察的小动作</span>
      <p>{{ insight.growth_action }}</p>
    </div>

    <div class="insight-draft__buttons">
      <button class="insight-btn insight-btn--confirm" @click="decide('confirmed')">
        确认，写进日记
      </button>
      <button class="insight-btn insight-btn--partial" @click="decide('partial')">
        部分像
      </button>
      <button class="insight-btn insight-btn--reject" @click="decide('rejected')">
        不是这样
      </button>
      <button class="insight-btn insight-btn--uncertain" @click="decide('uncertain')">
        还不确定
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from "vue";
import type { InsightDraft } from "@/composables/useSpiritConsultation";

const props = defineProps<{ insight: InsightDraft }>();
const emit = defineEmits<{
  (e: "decide", payload: { decision: string; editedQuote: string }): void;
}>();

const editedQuote = ref(props.insight.user_quote ?? "");
watch(
  () => props.insight.insight_id,
  () => {
    editedQuote.value = props.insight.user_quote ?? "";
  },
);

function decide(decision: string) {
  emit("decide", { decision, editedQuote: editedQuote.value.trim() });
}
</script>

<style scoped>
.insight-draft {
  margin: 12px 0;
  padding: 14px;
  border-radius: 14px;
  background: rgba(184, 125, 90, 0.08);
  border: 1px solid rgba(184, 125, 90, 0.25);
}
.insight-draft__head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.insight-draft__badge {
  font-size: 12px;
  color: var(--chat-color, #b87d5a);
  font-weight: 600;
}
.insight-draft__planet {
  font-size: 11px;
  color: rgba(0, 0, 0, 0.4);
}
.insight-draft__summary {
  margin: 0 0 10px;
  font-size: 14px;
  line-height: 1.6;
  color: rgba(0, 0, 0, 0.75);
}
.insight-draft__label {
  display: block;
  font-size: 12px;
  color: rgba(0, 0, 0, 0.5);
  margin-bottom: 4px;
}
.insight-draft__textarea {
  width: 100%;
  border: 1px solid rgba(0, 0, 0, 0.15);
  border-radius: 10px;
  padding: 8px 10px;
  font-size: 13px;
  line-height: 1.5;
  resize: vertical;
  box-sizing: border-box;
}
.insight-draft__action {
  margin-top: 10px;
  padding: 8px 10px;
  background: rgba(255, 255, 255, 0.5);
  border-radius: 8px;
}
.insight-draft__action-label {
  font-size: 11px;
  color: rgba(0, 0, 0, 0.45);
}
.insight-draft__action p {
  margin: 4px 0 0;
  font-size: 13px;
  line-height: 1.5;
}
.insight-draft__buttons {
  margin-top: 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.insight-btn {
  flex: 1 1 calc(50% - 8px);
  padding: 8px 6px;
  border-radius: 10px;
  border: 1px solid rgba(0, 0, 0, 0.1);
  background: #fff;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s;
}
.insight-btn--confirm {
  background: var(--chat-color, #b87d5a);
  color: #fff;
  border-color: transparent;
}
.insight-btn--partial {
  background: rgba(184, 125, 90, 0.12);
}
.insight-btn--reject {
  background: rgba(0, 0, 0, 0.04);
}
.insight-btn--uncertain {
  background: rgba(0, 0, 0, 0.04);
}
</style>
