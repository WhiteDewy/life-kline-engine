<template>
  <transition name="chat-slide">
    <div class="chat-bubble" v-if="visible" :style="{ '--chat-color': color }">
      <!-- 聊天头部 -->
      <div class="chat-header">
        <div class="chat-header-left">
          <div class="spirit-ring" :style="{ '--ring-color': color }">
            <SpiritAvatar :planet="planet" :symbol="symbol" :name="name" size="sm" />
          </div>
          <div>
            <span class="chat-name-sm">{{ name }}</span>
            <span class="chat-subtitle-sm">{{ archetype }}</span>
          </div>
        </div>
        <button class="chat-close-btn" @click="handleClose">&#10005;</button>
      </div>

      <!-- 消息列表 -->
      <div class="chat-messages" ref="messagesEl">
        <!-- 开场白 -->
        <div class="chat-msg chat-msg--spirit">
          <div class="msg-avatar"><SpiritAvatar :planet="planet" :symbol="symbol" :name="name" size="sm" /></div>
          <div class="msg-bubble spirit-bubble">
            <p>{{ greeting }}</p>
            <p class="spirit-hint">你想聊什么？我在这儿听着呢~</p>
            <div class="msg-actions" v-if="greeting">
              <VoicePlayer :text="greeting" :style="'whisper'" :show-label="false" size="mini" />
            </div>
          </div>
        </div>

        <!-- 用户消息和回复 -->
        <template v-for="(msg, i) in messages" :key="i">
          <div class="chat-msg chat-msg--user" v-if="msg.role === 'user'">
            <div class="msg-bubble user-bubble">{{ msg.text }}</div>
          </div>
          <div class="chat-msg chat-msg--spirit" v-else>
            <div class="msg-avatar"><SpiritAvatar :planet="planet" :symbol="symbol" :name="name" size="sm" /></div>
            <div class="msg-bubble spirit-bubble">
              <p>{{ msg.text }}</p>
              <div class="msg-actions" v-if="msg.text">
                <VoicePlayer :text="msg.text" :style="'whisper'" :show-label="false" size="mini" />
              </div>
              <!-- 星盘依据：可折叠 -->
              <div class="evidence-area" v-if="msg.engine_reading?.evidence?.length">
                <div class="evidence-toggle" @click.stop="toggleEvidence(i)">
                  <span class="evidence-toggle-line">─</span>
                  <span class="evidence-toggle-label">查看星盘依据</span>
                  <span class="evidence-toggle-arrow">{{ expandedEvidence === i ? '▴' : '▾' }}</span>
                </div>
                <div class="evidence-collapse" :class="{ 'is-open': expandedEvidence === i }">
                  <div class="evidence-inner">
                    <div
                      v-for="(line, li) in msg.engine_reading.evidence"
                      :key="li"
                      class="evidence-line"
                    >
                      <span class="evidence-bullet">•</span>
                      <span>{{ line }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </template>

        <!-- 思考中 -->
        <div class="chat-msg chat-msg--spirit" v-if="isThinking">
          <div class="msg-avatar"><SpiritAvatar :planet="planet" :symbol="symbol" :name="name" size="sm" /></div>
          <div class="msg-bubble spirit-bubble thinking-bubble">
            <span class="dot"></span>
            <span class="dot"></span>
            <span class="dot"></span>
          </div>
        </div>
      </div>

      <!-- 输入区 -->
      <div class="chat-input-area">
        <input
          v-model="inputText"
          class="chat-input"
          :placeholder="'和' + name + '说点什么...'"
          @keyup.enter="sendMessage"
        />
        <button
          class="chat-send-btn"
          :disabled="!inputText.trim() || isThinking"
          @click="sendMessage"
          :style="{ background: inputText.trim() ? color : 'rgba(255,255,255,0.1)' }"
        >
          <span v-if="!isThinking">发送</span>
          <span v-else>...</span>
        </button>
      </div>

      <!-- 提示 -->
      <p class="chat-disclaimer">
        {{ name }}的回应来自你的星盘分析，不是 AI 随机生成 ✦
      </p>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { ref, nextTick, watch } from "vue";
import { apiClient } from "@/config/api";
import SpiritAvatar from "./SpiritAvatar.vue";
import VoicePlayer from "@/views/home/components/VoicePlayer.vue";

interface EngineReading {
  evidence: string[];
  acknowledgment?: string;
  mirroring?: string;
  guidance?: string;
}

interface ChatMessage {
  role: "user" | "spirit";
  text: string;
  engine_reading?: EngineReading;
}

const props = defineProps<{
  visible: boolean;
  symbol: string;
  name: string;
  archetype: string;
  color: string;
  greeting: string;
  planet?: string;
  reportId?: string;
  entryContext?: {
    source: string;
    transit_planet?: string;
    transit_detail?: string;
    daily_question?: string;
    previous_spirit?: string;
    previous_chats_today?: number;
  };
}>();

const emit = defineEmits<{
  (e: "close", messages: ChatMessage[]): void;
}>();

const inputText = ref("");
const isThinking = ref(false);
const messages = ref<ChatMessage[]>([]);
const messagesEl = ref<HTMLElement | null>(null);
const expandedEvidence = ref<number | null>(null);

function handleClose() {
  emit("close", messages.value);
}

async function sendMessage() {
  const text = inputText.value.trim();
  if (!text || isThinking.value) return;

  messages.value.push({ role: "user", text });
  inputText.value = "";
  isThinking.value = true;

  await nextTick();
  scrollToBottom();

  // 尝试调用 AI 对话 API
  let apiResponse = "";
  let engineReading: EngineReading | undefined;
  if (props.reportId && props.planet) {
    try {
      const chatHistory = messages.value.map((m) => ({
        role: m.role === "spirit" ? "assistant" : "user",
        text: m.text,
      }));
      const res = await apiClient.post(`/spirit-chat/${props.reportId}`, {
        planet: props.planet,
        message: text,
        history: chatHistory,
        entry_context: props.entryContext,
      });
      if (res.data?.status === "success") {
        apiResponse = res.data.data?.response || "";
        engineReading = res.data.data?.engine_reading;
      }
    } catch {
      // fallback
    }
  }

  // 引擎占星师在后端永远在线，只有网络完全不可达时才兜底
  if (!apiResponse) {
    apiResponse = `抱歉，我现在暂时无法连接。请稍后再试——${props.name}一直都在。`;
  }

  messages.value.push({
    role: "spirit",
    text: apiResponse,
    engine_reading: engineReading?.evidence?.length ? engineReading : undefined,
  });
  isThinking.value = false;

  await nextTick();
  scrollToBottom();
}

function scrollToBottom() {
  if (messagesEl.value) {
    messagesEl.value.scrollTop = messagesEl.value.scrollHeight;
  }
}

function toggleEvidence(index: number) {
  expandedEvidence.value = expandedEvidence.value === index ? null : index;
}

watch(
  () => props.visible,
  (v) => {
    if (v) {
      messages.value = [];
      inputText.value = "";
    }
  }
);

defineExpose({ messages });
</script>

<style scoped>
.chat-bubble {
  display: flex;
  flex-direction: column;
  height: 60vh;
  max-height: 600px;
  border-radius: 24px;
  background: rgba(20, 20, 30, 0.75);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid rgba(255, 255, 255, 0.15);
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.3);
  color: #f0e6d8;
  overflow: hidden;
}

/* ── 过渡 ── */
.chat-slide-enter-active {
  transition: all 0.35s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}
.chat-slide-leave-active {
  transition: all 0.2s ease-in;
}
.chat-slide-enter-from {
  opacity: 0;
  transform: translateY(16px);
}
.chat-slide-leave-to {
  opacity: 0;
  transform: translateY(8px);
}

/* ── 呼吸光晕环 ── */
.spirit-ring {
  position: relative;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: ring-pulse 2.5s ease-in-out infinite;
  box-shadow: 0 0 0 0 var(--ring-color);
  flex-shrink: 0;
}

@keyframes ring-pulse {
  0% { box-shadow: 0 0 0 0 color-mix(in srgb, var(--ring-color) 40%, transparent); }
  50% { box-shadow: 0 0 0 8px color-mix(in srgb, var(--ring-color) 10%, transparent); }
  100% { box-shadow: 0 0 0 0 color-mix(in srgb, var(--ring-color) 40%, transparent); }
}

/* ── 头部 ── */
.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 18px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  flex-shrink: 0;
}
.chat-header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}
.chat-name-sm {
  display: block;
  font-size: 14px;
  font-weight: 600;
  color: #f0e6d8;
}
.chat-subtitle-sm {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.5);
}
.chat-close-btn {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(255, 255, 255, 0.06);
  color: rgba(255, 255, 255, 0.6);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  transition: all 0.2s;
  font-family: inherit;
}
.chat-close-btn:hover {
  background: rgba(255, 255, 255, 0.15);
  color: #f0e6d8;
}

/* ── 消息区 ── */
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px 18px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.chat-messages::-webkit-scrollbar {
  width: 4px;
}
.chat-messages::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 2px;
}

.chat-msg {
  display: flex;
  gap: 8px;
  max-width: 90%;
}
.chat-msg--spirit {
  align-self: flex-start;
}
.chat-msg--user {
  align-self: flex-end;
}
.msg-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 15px;
  flex-shrink: 0;
}

.msg-bubble {
  padding: 12px 16px;
  border-radius: 18px;
  font-size: 13px;
  line-height: 1.6;
}
.spirit-bubble {
  background: rgba(255, 255, 255, 0.12);
  color: #f0e6d8;
  border-top-left-radius: 6px;
}
.spirit-bubble p {
  margin: 0;
}
.spirit-hint {
  margin-top: 6px !important;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
}
.user-bubble {
  background: var(--chat-color);
  color: #fff;
  border-top-right-radius: 6px;
}

/* 消息操作按钮 */
.msg-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 6px;
  opacity: 0.6;
  transition: opacity 0.2s;
}
.spirit-bubble:hover .msg-actions {
  opacity: 1;
}

/* 思考动画 */
.thinking-bubble {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 14px 20px;
}
.thinking-bubble .dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.4);
  animation: bounce 1.4s ease-in-out infinite;
}
.thinking-bubble .dot:nth-child(2) {
  animation-delay: 0.16s;
}
.thinking-bubble .dot:nth-child(3) {
  animation-delay: 0.32s;
}
@keyframes bounce {
  0%, 80%, 100% { transform: scale(0.6); }
  40% { transform: scale(1); }
}

/* ── 输入区 ── */
.chat-input-area {
  display: flex;
  gap: 8px;
  padding: 12px 18px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  flex-shrink: 0;
}
.chat-input {
  flex: 1;
  padding: 10px 16px;
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.06);
  font-size: 14px;
  color: #f0e6d8;
  outline: none;
  font-family: inherit;
  transition: border-color 0.2s;
}
.chat-input:focus {
  border-color: var(--chat-color);
}
.chat-input::placeholder {
  color: rgba(255, 255, 255, 0.3);
}
.chat-send-btn {
  padding: 10px 20px;
  border-radius: 16px;
  border: none;
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  font-family: inherit;
}
.chat-send-btn:hover:not(:disabled) {
  filter: brightness(1.1);
}
.chat-send-btn:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

/* ── 星盘依据 ── */
.evidence-area {
  margin-top: 8px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  padding-top: 6px;
}
.evidence-toggle {
  display: flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  user-select: none;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.45);
  padding: 2px 0;
  transition: color 0.2s;
}
.evidence-toggle:hover {
  color: rgba(255, 255, 255, 0.7);
}
.evidence-toggle-line {
  opacity: 0.5;
}
.evidence-toggle-label {
  letter-spacing: 0.3px;
}
.evidence-toggle-arrow {
  font-size: 10px;
}
.evidence-collapse {
  max-height: 0;
  overflow: hidden;
  transition: max-height 0.35s ease;
}
.evidence-collapse.is-open {
  max-height: 300px;
}
.evidence-inner {
  padding: 6px 8px 4px;
  margin-top: 4px;
  background: rgba(0, 0, 0, 0.12);
  border-radius: 10px;
}
.evidence-line {
  font-size: 12px;
  line-height: 1.8;
  color: rgba(255, 255, 255, 0.6);
  display: flex;
  gap: 6px;
  padding-left: 2px;
}
.evidence-bullet {
  flex-shrink: 0;
  color: rgba(255, 255, 255, 0.3);
}

/* ── 免责 ── */
.chat-disclaimer {
  text-align: center;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.3);
  padding: 8px 18px 12px;
  margin: 0;
  flex-shrink: 0;
}
</style>
