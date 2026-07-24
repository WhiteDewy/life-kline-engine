<template>
  <div class="consultation-flow">
    <!-- 返回按钮 -->
    <button class="back-btn" @click="$emit('back')">← 返回分类</button>

    <!-- 进度指示器 -->
    <div class="cf-progress">
      <div
        v-for="s in 4"
        :key="s"
        class="cf-step"
        :class="{
          'cf-step--done': completedStep > s || state.is_complete,
          'cf-step--active': completedStep === s && !state.is_complete,
        }"
      >
        <span class="cf-step-dot">
          {{ completedStep > s || state.is_complete ? '✓' : completedStep === s ? '●' : '○' }}
        </span>
        <span class="cf-step-label">第{{ s }}/4 · {{ STEP_LABELS[s - 1] }}</span>
      </div>
    </div>

    <!-- 消息历史（滚动） -->
    <div class="cf-messages" ref="messagesEl">
      <div
        v-for="(msg, i) in messages"
        :key="i"
        :class="msg.role === 'user' ? 'cf-msg--user' : 'cf-msg--star'"
      >
        <!-- 星语者消息 -->
        <template v-if="msg.role === 'star'">
          <div class="ss-avatar">🔮</div>
          <div class="ss-bubble">
            <div class="ss-name">星语者</div>
            <div class="ss-text">{{ msg.content }}</div>
            <div v-if="msg.evidence?.length" class="ss-evidence">
              <div class="ss-evid-title">📋 星盘锚点</div>
              <div v-for="e in msg.evidence" :key="e" class="ss-evid-item">{{ e }}</div>
            </div>
          </div>
        </template>
        <!-- 用户消息 -->
        <template v-else>
          <div class="user-bubble">{{ msg.content }}</div>
        </template>
      </div>

      <!-- Sending indicator -->
      <div v-if="isSending" class="cf-msg--star">
        <div class="ss-avatar">🔮</div>
        <div class="ss-bubble ss-bubble--thinking">
          <span class="thinking-dot">·</span>
          <span class="thinking-dot">·</span>
          <span class="thinking-dot">·</span>
        </div>
      </div>
    </div>

    <!-- 完成面板 -->
    <div v-if="state.is_complete" class="cf-complete">
      <div class="cf-done-icon">✨</div>
      <h3 class="cf-done-title">分析完成</h3>
      <p class="cf-done-text">星语者已经对你的问题做了完整的星盘分析。</p>
      <button class="cf-gen-btn" @click="$emit('generate-report')">查看完整报告</button>
    </div>

    <!-- 用户输入 -->
    <div class="cf-input-area" v-if="!state.is_complete">
      <textarea
        v-model="userInput"
        class="cf-textarea"
        :disabled="isSending"
        :placeholder="isSending ? '星语者正在思考...' : '输入你的回答...'"
        rows="3"
        @keydown.enter.exact.prevent="sendResponse"
      ></textarea>
      <button
        class="cf-send-btn"
        @click="sendResponse"
        :disabled="!userInput.trim() || isSending"
      >
        {{ isSending ? '发送中...' : '发送' }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from "vue";
import type { ConsultationState } from "@/utils/types";

const STEP_LABELS = ["锚定", "情境", "验证", "守护"];

interface ChatMessage {
  role: "star" | "user";
  content: string;
  evidence?: string[];
}

const props = defineProps<{
  state: ConsultationState;
}>();

const emit = defineEmits<{
  "send-response": [text: string];
  "generate-report": [];
  back: [];
}>();

const userInput = ref("");
const isSending = ref(false);
const messages = ref<ChatMessage[]>([]);
const messagesEl = ref<HTMLElement | null>(null);

// Track what we've already added to avoid duplicates
let lastAnchorHash = "";
let lastQuestionHash = "";
let lastUserMsgCount = 0;

const completedStep = ref(1);

function scrollToBottom() {
  nextTick(() => {
    if (messagesEl.value) {
      messagesEl.value.scrollTop = messagesEl.value.scrollHeight;
    }
  });
}

// Watch state changes and append messages
watch(
  () => props.state,
  (s) => {
    if (!s) return;

    // Anchor message
    if (s.anchor_text && s.anchor_text !== lastAnchorHash) {
      lastAnchorHash = s.anchor_text;
      const hadAnchor = messages.value.some((m) => m.role === "star" && m.content === s.anchor_text);
      if (!hadAnchor) {
        messages.value.push({
          role: "star",
          content: s.anchor_text,
          evidence: s.anchor_evidence,
        });
      }
    }

    // Pending question (new star speaker message)
    if (s.pending_question && s.pending_question !== lastQuestionHash) {
      lastQuestionHash = s.pending_question;
      const hadQ = messages.value.some((m) => m.role === "star" && m.content === s.pending_question);
      if (!hadQ) {
        messages.value.push({
          role: "star",
          content: s.pending_question,
        });
      }
    }

    // User responses
    const userResponses = s.user_responses ?? [];
    if (userResponses.length > lastUserMsgCount) {
      for (let i = lastUserMsgCount; i < userResponses.length; i++) {
        messages.value.push({
          role: "user",
          content: userResponses[i] ?? "",
        });
      }
      lastUserMsgCount = userResponses.length;
    }

    // Track step progression
    if (s.step > completedStep.value) {
      completedStep.value = s.step;
    }

    scrollToBottom();
  },
  { deep: true, immediate: true },
);

async function sendResponse() {
  const text = userInput.value.trim();
  if (!text || isSending.value) return;

  // Add user message locally
  messages.value.push({ role: "user", content: text });
  userInput.value = "";
  isSending.value = true;
  scrollToBottom();

  emit("send-response", text);
}
</script>

<style scoped>
.consultation-flow {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 200px);
  min-height: 400px;
  padding: 0 4px;
}
.back-btn {
  padding: 6px 14px; border-radius: 14px;
  border: 1px solid rgba(0,0,0,0.08); background: rgba(255,255,255,0.6);
  font-size: 13px; font-weight: 600; color: #8b7355;
  cursor: pointer; font-family: inherit;
  align-self: flex-start; margin-bottom: 12px; flex-shrink: 0;
}
.cf-progress {
  display: flex; justify-content: center; gap: 16px;
  margin-bottom: 16px; padding: 10px 16px; border-radius: 16px;
  background: rgba(255,255,255,0.5); flex-shrink: 0;
}
.cf-step {
  display: flex; flex-direction: column; align-items: center; gap: 2px;
  opacity: 0.35; transition: opacity 0.3s;
}
.cf-step--done, .cf-step--active { opacity: 1; }
.cf-step-dot { font-size: 12px; color: #ff9a8b; }
.cf-step-label { font-size: 11px; font-weight: 600; color: #4a3728; white-space: nowrap; }

/* Messages */
.cf-messages {
  flex: 1; overflow-y: auto; padding: 0 4px 12px;
  display: flex; flex-direction: column; gap: 16px;
}
.cf-messages::-webkit-scrollbar { width: 3px; }
.cf-messages::-webkit-scrollbar-thumb { background: rgba(0,0,0,0.1); border-radius: 3px; }

.cf-msg--star { display: flex; gap: 10px; }
.cf-msg--user { display: flex; justify-content: flex-end; }

.ss-avatar {
  width: 36px; height: 36px; border-radius: 50%;
  background: rgba(255,154,139,0.12); display: flex;
  align-items: center; justify-content: center; font-size: 18px; flex-shrink: 0;
}
.ss-bubble {
  max-width: 80%; padding: 12px 16px; border-radius: 16px;
  background: rgba(255,255,255,0.75); border: 1px solid rgba(0,0,0,0.05);
}
.ss-bubble--thinking {
  padding: 8px 20px; display: flex; gap: 4px;
}
.thinking-dot {
  font-size: 24px; color: #8b7355;
  animation: dot-pulse 1.2s infinite;
}
.thinking-dot:nth-child(2) { animation-delay: 0.2s; }
.thinking-dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes dot-pulse {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 1; }
}
.ss-name { font-size: 12px; font-weight: 700; color: #ff9a8b; margin-bottom: 6px; }
.ss-text { font-size: 14px; color: #4a3728; line-height: 1.7; white-space: pre-line; }
.ss-evidence { margin-top: 10px; padding-top: 10px; border-top: 1px solid rgba(0,0,0,0.06); }
.ss-evid-title { font-size: 11px; font-weight: 600; color: #8b7355; margin-bottom: 4px; }
.ss-evid-item { font-size: 12px; color: #8b7355; line-height: 1.5; }

.user-bubble {
  max-width: 75%; padding: 10px 16px; border-radius: 16px;
  background: linear-gradient(135deg, #f0b8a0, #e8a890);
  color: #fff; font-size: 14px; line-height: 1.6;
}

/* Input */
.cf-input-area {
  display: flex; flex-direction: column; gap: 10px;
  padding-top: 12px; border-top: 1px solid rgba(0,0,0,0.05); flex-shrink: 0;
}
.cf-textarea {
  width: 100%; padding: 12px 14px; border-radius: 14px;
  border: 1px solid rgba(0,0,0,0.08); background: rgba(255,255,255,0.8);
  font-family: inherit; font-size: 14px; color: #4a3728; resize: none; outline: none;
}
.cf-textarea:focus { border-color: rgba(255,154,139,0.3); }
.cf-textarea:disabled { opacity: 0.6; }
.cf-send-btn {
  align-self: flex-end; padding: 10px 28px; border-radius: 16px;
  border: none; background: linear-gradient(135deg, #f0b8a0, #e8a890);
  color: #fff; font-weight: 600; font-family: inherit; cursor: pointer;
  transition: all 0.2s;
}
.cf-send-btn:hover:not(:disabled) { transform: translateY(-1px); }
.cf-send-btn:disabled { opacity: 0.5; cursor: default; }

/* Complete */
.cf-complete {
  text-align: center; padding: 20px; flex-shrink: 0;
}
.cf-done-icon { font-size: 40px; margin-bottom: 8px; }
.cf-done-title { font-size: 20px; font-weight: 700; color: #4a3728; margin: 0 0 4px; }
.cf-done-text { font-size: 14px; color: #8b7355; margin: 0 0 16px; }
.cf-gen-btn {
  padding: 12px 32px; border-radius: 18px;
  border: none; background: linear-gradient(135deg, #f0b8a0, #e8a890);
  color: #fff; font-weight: 700; font-size: 15px;
  font-family: inherit; cursor: pointer;
  box-shadow: 0 4px 20px rgba(220,150,120,0.2);
  transition: all 0.3s;
}
.cf-gen-btn:hover { transform: translateY(-2px); box-shadow: 0 8px 28px rgba(220,150,120,0.3); }
</style>
