<template>
  <div class="chat-page" :style="{ '--chat-color': chatColor }">
    <!-- 顶部导航 -->
    <header class="chat-header">
      <button class="chat-back" @click="goBack" aria-label="返回">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M19 12H5M12 19l-7-7 7-7" />
        </svg>
      </button>

      <div class="chat-header__spirit">
        <div class="chat-header__avatar">
          <SpiritAvatar :planet="chatPlanet" :symbol="chatSymbol" :name="chatName" size="sm" />
        </div>
        <div class="chat-header__meta">
          <span class="chat-header__name">{{ chatName }}</span>
          <span v-if="chatArchetype" class="chat-header__archetype">{{ chatArchetype }}</span>
        </div>
      </div>

      <button v-if="chatGreeting" class="chat-header__voice" aria-label="播放问候">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
          <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07" />
        </svg>
      </button>
    </header>

    <!-- 聊天主体 -->
    <div ref="messagesEl" class="chat-messages">
      <!-- 开场白 -->
      <div class="chat-msg chat-msg--spirit">
        <div class="msg-avatar">
          <SpiritAvatar :planet="chatPlanet" :symbol="chatSymbol" :name="chatName" size="sm" />
        </div>
        <div class="msg-bubble spirit-bubble">
          <p>{{ chatGreeting || defaultGreeting }}</p>
          <p class="spirit-hint">{{ chatHint }}</p>
          <div v-if="chatGreeting" class="msg-actions">
            <VoicePlayer :text="chatGreeting" voice-style="whisper" :show-label="false" size="mini" />
          </div>
        </div>
      </div>

      <!-- 用户消息和回复 -->
      <template v-for="(msg, i) in messages" :key="i">
        <div v-if="msg.role === 'user'" class="chat-msg chat-msg--user">
          <div class="msg-bubble user-bubble">{{ msg.text }}</div>
        </div>
        <div v-else class="chat-msg chat-msg--spirit">
          <div class="msg-avatar">
            <SpiritAvatar :planet="chatPlanet" :symbol="chatSymbol" :name="chatName" size="sm" />
          </div>
          <div class="msg-bubble spirit-bubble">
            <p>{{ msg.text }}</p>
            <div v-if="msg.text" class="msg-actions">
              <VoicePlayer :text="msg.text" voice-style="whisper" :show-label="false" size="mini" />
            </div>
            <!-- 星盘依据 -->
            <div v-if="msg.engine_reading?.evidence?.length" class="evidence-area">
              <div class="evidence-toggle" @click.stop="toggleEvidence(i)">
                <span class="evidence-toggle-line">─</span>
                <span class="evidence-toggle-label">查看星盘依据</span>
                <span class="evidence-toggle-arrow">{{ expandedEvidence === i ? '▴' : '▾' }}</span>
              </div>
              <div class="evidence-collapse" :class="{ 'is-open': expandedEvidence === i }">
                <div class="evidence-inner">
                  <div v-for="(line, li) in msg.engine_reading.evidence" :key="li" class="evidence-line">
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
      <div v-if="isThinking" class="chat-msg chat-msg--spirit">
        <div class="msg-avatar">
          <SpiritAvatar :planet="chatPlanet" :symbol="chatSymbol" :name="chatName" size="sm" />
        </div>
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
        :disabled="isThinking"
        :placeholder="isThinking ? `${chatName}正在回应你的问题……` : `和${chatName}说点什么...`"
        @keyup.enter="sendMessage"
      />
      <button
        class="chat-send-btn"
        :disabled="!inputText.trim() || isThinking"
        :style="{ background: inputText.trim() ? chatColor : 'var(--border-light)' }"
        @click="sendMessage">
        <svg v-if="!isThinking" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="22" y1="2" x2="11" y2="13" />
          <polygon points="22 2 15 22 11 13 2 9 22 2" />
        </svg>
        <span v-else>...</span>
      </button>
    </div>

    <!-- 保存提示 -->
    <p class="chat-disclaimer">
      {{ chatName }}的回应来自你的星盘分析，不是 AI 随机生成 ✦
    </p>

    <!-- 加载态 -->
    <div v-if="!isLoaded" class="chat-loading">
      <div class="loading-ring" :style="{ '--chat-color': chatColor }"></div>
      <p class="loading-text">正在唤醒 {{ chatName }}…</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, watch, onMounted, computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { apiClient } from "@/config/api";
import { useHomeData } from "@/composables/useHomeData";
import SpiritAvatar from "@/components/garden/SpiritAvatar.vue";
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

const route = useRoute();
const router = useRouter();
const homeData = useHomeData();

const chatPlanet = computed(() => String(route.params.planet || "SUN"));
const reportId = computed(() => homeData.reportId.value);

const spiritProfile = computed(() => homeData.planetProfiles.value?.planet_characters?.[chatPlanet.value]);
const chatSymbol = computed(() => spiritProfile.value?.persona?.symbol || "★");
const chatName = computed(() => spiritProfile.value?.persona?.name_zh || chatPlanet.value);
const chatArchetype = computed(() => spiritProfile.value?.persona?.archetype_zh || "");
const chatColor = computed(() => spiritProfile.value?.persona?.visual_color || "#B87D5A");
const chatGreeting = computed(() => spiritProfile.value?.personalized_greeting || "");

const defaultGreeting = "你好，我在这里陪着你。";
const chatHint = "想聊什么都可以，我听着。";

const inputText = ref("");
const isThinking = ref(false);
const isLoaded = ref(false);
const messages = ref<ChatMessage[]>([]);
const messagesEl = ref<HTMLElement | null>(null);
const expandedEvidence = ref<number | null>(null);

const entryContext = computed(() => {
  const source = String(route.query.source || "direct");
  const dailyQuestion = String(route.query.question || "");
  return {
    source,
    daily_question: dailyQuestion,
    from_daily_question: source === "today" && !!dailyQuestion,
  };
});

async function sendMessage() {
  const text = inputText.value.trim();
  if (!text || isThinking.value) return;

  messages.value.push({ role: "user", text });
  inputText.value = "";
  isThinking.value = true;

  await nextTick();
  scrollToBottom();

  let apiResponse = "";
  let engineReading: EngineReading | undefined;

  if (reportId.value && chatPlanet.value) {
    try {
      const chatHistory = messages.value.map((m) => ({
        role: m.role === "spirit" ? "assistant" : "user",
        text: m.text,
      }));
      const res = await apiClient.post(`/spirit-chat/${reportId.value}`, {
        planet: chatPlanet.value,
        message: text,
        history: chatHistory,
        entry_context: entryContext.value,
      });
      if (res.data?.status === "success") {
        apiResponse = res.data.data?.response || "";
        engineReading = res.data.data?.engine_reading;
      }
    } catch {
      // fallback
    }
  }

  if (!apiResponse) {
    apiResponse = `抱歉，我现在暂时无法连接。请稍后再试——${chatName.value}一直都在。`;
  }

  messages.value.push({
    role: "spirit",
    text: apiResponse,
    engine_reading: engineReading?.evidence?.length ? engineReading : undefined,
  });
  isThinking.value = false;

  saveDiaryEntry(text, apiResponse);

  await nextTick();
  scrollToBottom();
}

async function saveDiaryEntry(userText: string, spiritReply: string) {
  if (!reportId.value || !chatPlanet.value) return;
  try {
    const chatContext = `用户：${userText.slice(0, 300)}\n${chatName.value}：${spiritReply.slice(0, 300)}`;
    await apiClient.post(`/spirit-diary/${reportId.value}/entry`, {
      chat_context: chatContext,
      spirit_planet: chatPlanet.value,
      mood_emoji: "",
    });
  } catch (e) {
    console.error("[Diary] 保存日记失败:", e);
  }
}

function scrollToBottom() {
  if (messagesEl.value) {
    messagesEl.value.scrollTop = messagesEl.value.scrollHeight;
  }
}

function toggleEvidence(index: number) {
  expandedEvidence.value = expandedEvidence.value === index ? null : index;
}

function goBack() {
  router.back();
}

onMounted(async () => {
  await homeData.refreshData();
  isLoaded.value = true;
  if (entryContext.value.from_daily_question && entryContext.value.daily_question) {
    isThinking.value = true;
    try {
      const res = await apiClient.post(`/spirit-chat/${reportId.value}`, {
        planet: chatPlanet.value,
        message: entryContext.value.daily_question,
        history: [],
        entry_context: entryContext.value,
      });
      if (res.data?.status === "success") {
        const data = res.data.data || {};
        messages.value.push({
          role: "spirit",
          text: data.response || "",
          engine_reading: data.engine_reading?.evidence?.length ? data.engine_reading : undefined,
        });
        saveDiaryEntry(entryContext.value.daily_question, data.response || "");
      }
    } catch (e) {
      console.error("[AutoInit] 失败:", e);
    }
    isThinking.value = false;
    await nextTick();
    scrollToBottom();
  }
});

watch(messages, () => {
  nextTick(scrollToBottom);
}, { deep: true });
</script>

<style scoped lang="less">
.chat-page {
  min-height: 100vh;
  min-height: 100dvh;
  display: flex;
  flex-direction: column;
  background: var(--bg-main);
  position: relative;
}

.chat-header {
  position: sticky;
  top: 0;
  z-index: 10;
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  padding-top: calc(var(--space-3) + env(safe-area-inset-top, 0px));
  background: var(--bg-card-glass);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-bottom: 1px solid var(--border-light);
}

.chat-back,
.chat-header__voice {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  transition: all var(--duration-fast) var(--ease-smooth);
  flex-shrink: 0;
}

.chat-back:hover,
.chat-header__voice:hover {
  background: var(--fill-color);
  color: var(--text-primary);
}

.chat-header__spirit {
  flex: 1;
  display: flex;
  align-items: center;
  gap: var(--space-3);
  justify-content: center;
}

.chat-header__avatar {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 0 0 2px var(--color-primary-soft);
}

.chat-header__meta {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 2px;
}

.chat-header__name {
  font-size: var(--text-base);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
}

.chat-header__archetype {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-5);
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.chat-messages::-webkit-scrollbar {
  width: 4px;
}

.chat-messages::-webkit-scrollbar-thumb {
  background: var(--border-light);
  border-radius: 2px;
}

.chat-msg {
  display: flex;
  gap: var(--space-3);
  max-width: 85%;
  animation: message-in var(--duration-normal) var(--ease-emotional);
}

@keyframes message-in {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.chat-msg--spirit {
  align-self: flex-start;
}

.chat-msg--user {
  align-self: flex-end;
}

.msg-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 15px;
  flex-shrink: 0;
  background: var(--bg-elevated);
}

.msg-bubble {
  padding: 12px 16px;
  border-radius: var(--radius-lg);
  font-size: var(--text-base);
  line-height: var(--leading-relaxed);
}

.spirit-bubble {
  background: var(--bg-card);
  color: var(--text-primary);
  border: 1px solid var(--border-light);
  border-top-left-radius: var(--radius-sm);
  box-shadow: var(--shadow-sm);
}

.spirit-bubble p {
  margin: 0;
}

.spirit-hint {
  margin-top: var(--space-2) !important;
  font-size: var(--text-sm);
  color: var(--text-tertiary);
}

.user-bubble {
  background: var(--chat-color);
  color: #fff;
  border-top-right-radius: var(--radius-sm);
}

.msg-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: var(--space-2);
  opacity: 0.6;
  transition: opacity var(--duration-fast) var(--ease-smooth);
}

.spirit-bubble:hover .msg-actions {
  opacity: 1;
}

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
  background: var(--text-tertiary);
  animation: bounce 1.4s ease-in-out infinite;
}

.thinking-bubble .dot:nth-child(2) {
  animation-delay: 0.16s;
}

.thinking-bubble .dot:nth-child(3) {
  animation-delay: 0.32s;
}

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.6; }
  40% { transform: scale(1); opacity: 1; }
}

.evidence-area {
  margin-top: var(--space-3);
  border-top: 1px solid var(--border-light);
  padding-top: var(--space-2);
}

.evidence-toggle {
  display: flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  user-select: none;
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  transition: color var(--duration-fast) var(--ease-smooth);
}

.evidence-toggle:hover {
  color: var(--color-primary);
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
  transition: max-height var(--duration-normal) var(--ease-smooth);
}

.evidence-collapse.is-open {
  max-height: 300px;
}

.evidence-inner {
  padding: var(--space-3);
  margin-top: var(--space-2);
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
}

.evidence-line {
  font-size: var(--text-sm);
  line-height: var(--leading-relaxed);
  color: var(--text-secondary);
  display: flex;
  gap: var(--space-2);
}

.evidence-bullet {
  flex-shrink: 0;
  color: var(--text-muted);
}

.chat-input-area {
  position: sticky;
  bottom: 0;
  display: flex;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  padding-bottom: calc(var(--space-3) + env(safe-area-inset-bottom, 0px));
  background: var(--bg-card);
  border-top: 1px solid var(--border-light);
}

.chat-input {
  flex: 1;
  padding: 12px 16px;
  border-radius: var(--radius-full);
  border: 1px solid var(--border-light);
  background: var(--bg-elevated);
  font-size: var(--text-base);
  color: var(--text-primary);
  outline: none;
  font-family: inherit;
  transition: all var(--duration-fast) var(--ease-smooth);
}

.chat-input:focus {
  border-color: var(--color-primary);
  box-shadow: var(--shadow-glow);
}

.chat-input::placeholder {
  color: var(--text-muted);
}

.chat-send-btn {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
  transition: all var(--duration-fast) var(--ease-smooth);
}

.chat-send-btn:hover:not(:disabled) {
  filter: brightness(1.1);
  transform: scale(1.05);
}

.chat-send-btn:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.chat-disclaimer {
  text-align: center;
  font-size: var(--text-xs);
  color: var(--text-muted);
  padding: var(--space-2) var(--space-5) var(--space-3);
  margin: 0;
  background: var(--bg-card);
}

@media (max-width: 380px) {
  .chat-msg {
    max-width: 90%;
  }
  .msg-bubble {
    padding: 10px 14px;
  }
}

.chat-loading {
  position: absolute;
  inset: 0;
  z-index: 20;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-4);
  background: var(--bg-main);
}

.loading-ring {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  border: 2px solid var(--border-light);
  border-top-color: var(--chat-color, var(--color-primary));
  animation: chat-ring 0.9s linear infinite;
}

@keyframes chat-ring {
  to { transform: rotate(360deg); }
}

.loading-text {
  font-size: var(--text-sm);
  color: var(--text-secondary);
  margin: 0;
}
</style>
