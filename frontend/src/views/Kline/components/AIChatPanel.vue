<template>
  <div class="chat-panel">
    <div class="chat-messages" ref="msgContainer">
      <div
        class="chat-msg"
        v-for="(msg, i) in messages"
        :key="i"
        :class="{ 'chat-msg--user': msg.role === 'user', 'chat-msg--astro': msg.role === 'astro' }"
      >
        <div class="msg-avatar" v-if="msg.role === 'astro'">{{ avatarEmoji }}</div>
        <div class="msg-bubble">
          <p class="msg-text">{{ msg.text }}</p>
          <span class="msg-time">{{ msg.time }}</span>
        </div>
        <div class="msg-avatar" v-if="msg.role === 'user'">🙋</div>
      </div>
      <div v-if="typing" class="chat-msg chat-msg--astro">
        <div class="msg-avatar">{{ avatarEmoji }}</div>
        <div class="msg-bubble typing-bubble">
          <span class="typing-dot"></span>
          <span class="typing-dot"></span>
          <span class="typing-dot"></span>
        </div>
      </div>
    </div>

    <div class="chat-input-row">
      <div class="free-hint">
        想更深入地聊？<button class="upgrade-link" @click="$emit('upgrade')">和星灵深度对话 →</button>
      </div>
      <div class="input-wrap">
        <input
          class="chat-input"
          v-model="inputText"
          placeholder="输入你的问题…"
          @keydown.enter="sendMessage"
          :disabled="typing"
        />
        <button class="send-btn" @click="sendMessage" :disabled="!inputText.trim() || typing">
          发送
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, watch, computed } from "vue";
import { apiClient } from "@/config/api";
import { SIGN_EMOJI_MAP } from "@/config/zodiac";

const props = defineProps<{
  greeting?: string;
  characterSign?: string;
  characterName?: string;
  characterColor?: string;
  reportId?: string;
}>();

const emit = defineEmits<{
  upgrade: [];
  'select-character': [];
}>();

const inputText = ref("");
const typing = ref(false);
const msgContainer = ref<HTMLElement | null>(null);

const SIGN_EMOJIS = SIGN_EMOJI_MAP;

const avatarEmoji = computed(() => {
  if (props.characterSign) {
    return SIGN_EMOJIS[props.characterSign] || '🔮';
  }
  return '🔮';
});

interface ChatMsg {
  role: "user" | "astro";
  text: string;
  time: string;
}

const messages = ref<ChatMsg[]>([]);

function timeStr() {
  return new Date().toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" });
}

watch(
  () => props.greeting,
  (greeting) => {
    if (greeting) {
      messages.value.push({ role: "astro", text: greeting, time: timeStr() });
    }
  },
  { immediate: true }
);

async function sendMessage() {
  const text = inputText.value.trim();
  if (!text) return;

  messages.value.push({ role: "user", text, time: timeStr() });
  inputText.value = "";

  typing.value = true;
  await nextTick();
  scrollToBottom();

  // 调用免费规则对话 API（/characters/{id}/chat，无 LLM、不计额度）。
  // 失败或空回复时诚实告知，绝不返回编造的星盘解读。
  let reply = "";
  try {
    if (props.reportId) {
      const res = await apiClient.post(`/characters/${props.reportId}/chat`, {
        sign: props.characterSign || 'ARIES',
        topic: detectTopic(text),
        message: text,
      });
      reply = res.data?.data?.response || "";
    }
  } catch {
    reply = "";
  }

  typing.value = false;
  messages.value.push({
    role: "astro",
    text: reply || "暂时无法回应，稍后再试，或点下方与星灵深度对话。",
    time: timeStr(),
  });

  await nextTick();
  scrollToBottom();
}

function detectTopic(text: string): string {
  if (text.includes('感情') || text.includes('爱情') || text.includes('喜欢') || text.includes('恋爱')) return 'romance';
  if (text.includes('工作') || text.includes('事业') || text.includes('职业') || text.includes('换工作')) return 'career';
  if (text.includes('钱') || text.includes('财运') || text.includes('财务') || text.includes('收入')) return 'finance';
  if (text.includes('婚姻') || text.includes('结婚') || text.includes('伴侣')) return 'marriage';
  if (text.includes('家庭') || text.includes('父母') || text.includes('原生')) return 'family';
  if (text.includes('学习') || text.includes('读书') || text.includes('考试')) return 'education';
  if (text.includes('健康') || text.includes('身体') || text.includes('累')) return 'health';
  if (text.includes('孩子') || text.includes('小孩')) return 'children';
  return 'personal';
}

function scrollToBottom() {
  if (msgContainer.value) {
    msgContainer.value.scrollTop = msgContainer.value.scrollHeight;
  }
}
</script>

<style scoped lang="less">
.chat-panel {
  display: flex;
  flex-direction: column;
  height: 420px;
  border-radius: 20px;
  border: 1px solid rgba(155,196,208, 0.12);
  background: rgba(255,255,255, 0.6);
  backdrop-filter: blur(12px);
  overflow: hidden;
}
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: grid;
  gap: 16px;
  align-content: start;
}
.chat-msg {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  max-width: 90%;
}
.chat-msg--user {
  margin-left: auto;
  flex-direction: row-reverse;
}
.chat-msg--astro {
  margin-right: auto;
}
.msg-avatar {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: rgba(155,196,208, 0.15);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
}
.msg-bubble {
  padding: 12px 16px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(0,0,0,0.06);
}
.chat-msg--user .msg-bubble {
  background: rgba(155,196,208, 0.12);
  border-color: rgba(155,196,208, 0.18);
}
.msg-text {
  margin: 0;
  color: #4a3728;
  font-size: 14px;
  line-height: 1.7;
}
.msg-time {
  display: block;
  margin-top: 4px;
  color: #475569;
  font-size: 10px;
  text-align: right;
}
.typing-bubble {
  display: flex;
  gap: 4px;
  align-items: center;
  padding: 14px 18px;
}
.typing-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #64748b;
  animation: typing-bounce 1.2s ease infinite;
}
.typing-dot:nth-child(2) { animation-delay: 0.15s; }
.typing-dot:nth-child(3) { animation-delay: 0.3s; }
@keyframes typing-bounce {
  0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
  30% { transform: translateY(-4px); opacity: 1; }
}
.chat-input-row {
  border-top: 1px solid rgba(0,0,0,0.06);
  padding: 14px 18px;
}
.free-hint {
  text-align: center;
  color: #a89880;
  font-size: 12px;
  margin-bottom: 10px;
}
.upgrade-link {
  background: none;
  border: none;
  color: #ff9a8b;
  cursor: pointer;
  font-size: 12px;
  padding: 0;
  text-decoration: underline;
}
.input-wrap {
  display: flex;
  gap: 8px;
}
.chat-input {
  flex: 1;
  padding: 10px 16px;
  border-radius: 999px;
  border: 1px solid rgba(0,0,0,0.06);
  background: rgba(255, 255, 255, 0.03);
  color: #4a3728;
  font-size: 14px;
  outline: none;
}
.chat-input:focus {
  border-color: rgba(155,196,208, 0.3);
}
.chat-input::placeholder { color: #475569; }
.send-btn {
  padding: 10px 20px;
  border-radius: 999px;
  border: none;
  background: rgba(155,196,208, 0.2);
  color: #a5b4fc;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}
.send-btn:hover:not(:disabled) {
  background: rgba(155,196,208, 0.35);
}
.send-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}
</style>
