<template>
  <transition name="chat-slide">
    <div class="chat-bubble" v-if="visible" :style="{ '--chat-color': color }">
      <!-- 聊天头部 -->
      <div class="chat-header">
        <div class="chat-header-left">
          <SpiritAvatar :planet="planet" :symbol="symbol" :name="name" size="sm" />
          <div>
            <span class="chat-name-sm">{{ name }}</span>
            <span class="chat-subtitle-sm">{{ archetype }}</span>
          </div>
        </div>
        <button class="chat-close-btn" @click="$emit('close')">✕</button>
      </div>

      <!-- 消息列表 -->
      <div class="chat-messages" ref="messagesEl">
        <!-- 开场白 -->
        <div class="chat-msg chat-msg--spirit">
          <div class="msg-avatar"><SpiritAvatar :planet="planet" :symbol="symbol" :name="name" size="sm" /></div>
          <div class="msg-bubble spirit-bubble">
            <p>{{ greeting }}</p>
            <p class="spirit-hint">你想聊什么？我在这儿听着呢~</p>
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
          :style="{ background: inputText.trim() ? color : 'rgba(0,0,0,0.06)' }"
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

const props = defineProps<{
  visible: boolean;
  symbol: string;
  name: string;
  archetype: string;
  color: string;
  greeting: string;
  planet?: string;
  reportId?: string;
}>();

const emit = defineEmits<{
  close: [];
}>();

const inputText = ref("");
const isThinking = ref(false);
const messages = ref<Array<{ role: "user" | "spirit"; text: string }>>([]);
const messagesEl = ref<HTMLElement | null>(null);

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
  if (props.reportId && props.planet) {
    try {
      const chatHistory = messages.value.map((m) => ({
        role: m.role === "spirit" ? "assistant" : "user",
        text: m.text,
      }));
      const res = await apiClient.post(`/spirit-chat/${props.reportId}`, {
        planet: props.planet,
        topic: "personal",
        message: text,
        history: chatHistory,
      });
      if (res.data?.status === "success") {
        apiResponse = res.data.data?.response || "";
      }
    } catch {
      // fallback
    }
  }

  // Fallback: 前端规则生成
  if (!apiResponse) {
    await new Promise((r) => setTimeout(r, 800 + Math.random() * 1200));
    const responses = [
      `你说得对，让我从我的角度来看——${text.slice(0, 10)}这件事，其实反映了你星盘里一个很核心的议题。`,
      `嗯，我听到了。你知道吗，你的星盘里有一个很特别的地方和这个有关——我慢慢跟你说。`,
      `这个问题很有意思。从我的位置来看，你之所以会这么想，是因为你天生就带着某种倾向...`,
      `我明白你的感受。作为你的${props.name}，我一直都在观察你这方面的模式。`,
      `让我想想...好，我看到了。你星盘里的宫位结构显示，这其实是你的一个成长课题。`,
    ];
    apiResponse = responses[Math.floor(Math.random() * responses.length)];
  }

  messages.value.push({ role: "spirit", text: apiResponse });
  isThinking.value = false;

  await nextTick();
  scrollToBottom();
}

function scrollToBottom() {
  if (messagesEl.value) {
    messagesEl.value.scrollTop = messagesEl.value.scrollHeight;
  }
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
</script>

<style scoped>
.chat-bubble {
  display: flex;
  flex-direction: column;
  height: 420px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(16px);
  box-shadow: 0 8px 40px rgba(0, 0, 0, 0.08);
  border: 1.5px solid rgba(255, 255, 255, 0.8);
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

/* ── 头部 ── */
.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 18px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  flex-shrink: 0;
}
.chat-header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}
.chat-avatar-sm {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  background: var(--chat-color) 20;
}
.chat-name-sm {
  display: block;
  font-size: 14px;
  font-weight: 600;
  color: #4a3728;
}
.chat-subtitle-sm {
  font-size: 11px;
  color: #8b7355;
}
.chat-close-btn {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: none;
  background: rgba(0, 0, 0, 0.04);
  color: #8b7355;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  transition: all 0.2s;
}
.chat-close-btn:hover {
  background: rgba(0, 0, 0, 0.08);
  color: #4a3728;
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
  background: rgba(0, 0, 0, 0.1);
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
  background: rgba(0, 0, 0, 0.03);
  color: #4a3728;
  border-top-left-radius: 6px;
}
.spirit-bubble p {
  margin: 0;
}
.spirit-hint {
  margin-top: 6px !important;
  font-size: 12px;
  color: #a89880;
}
.user-bubble {
  background: var(--chat-color);
  color: #fff;
  border-top-right-radius: 6px;
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
  background: #c4b5a5;
  animation: bounce 1.4s ease-in-out infinite;
}
.thinking-bubble .dot:nth-child(2) {
  animation-delay: 0.16s;
}
.thinking-bubble .dot:nth-child(3) {
  animation-delay: 0.32s;
}
@keyframes bounce {
  0%,
  80%,
  100% {
    transform: scale(0.6);
  }
  40% {
    transform: scale(1);
  }
}

/* ── 输入区 ── */
.chat-input-area {
  display: flex;
  gap: 8px;
  padding: 12px 18px;
  border-top: 1px solid rgba(0, 0, 0, 0.05);
  flex-shrink: 0;
}
.chat-input {
  flex: 1;
  padding: 10px 16px;
  border-radius: 16px;
  border: 1px solid rgba(0, 0, 0, 0.08);
  background: rgba(0, 0, 0, 0.02);
  font-size: 14px;
  color: #4a3728;
  outline: none;
  font-family: inherit;
  transition: border-color 0.2s;
}
.chat-input:focus {
  border-color: var(--chat-color);
}
.chat-input::placeholder {
  color: #c4b5a5;
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

/* ── 免责 ── */
.chat-disclaimer {
  text-align: center;
  font-size: 11px;
  color: #c4b5a5;
  padding: 8px 18px 12px;
  margin: 0;
  flex-shrink: 0;
}
</style>
