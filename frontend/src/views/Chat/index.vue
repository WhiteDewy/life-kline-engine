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

      <button v-if="chatName" class="chat-header__voice" aria-label="播放问候">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
          <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07" />
        </svg>
      </button>
    </header>

    <!-- 聊天主体 -->
    <div ref="messagesEl" class="chat-messages">
      <!-- ═══════ 结构地图 ═══════ -->
      <div v-if="consultation.dossier.value" class="chat-msg chat-msg--spirit">
        <div class="msg-avatar">
          <SpiritAvatar :planet="chatPlanet" :symbol="chatSymbol" :name="chatName" size="sm" />
        </div>
        <div class="msg-bubble spirit-bubble structure-map">
          <p class="structure-title">{{ consultation.dossier.value.identity_statement }}</p>
          <div class="structure-topics">
            <span
              v-for="key in consultation.dossier.value.topic_order"
              :key="key"
              class="topic-chip"
            >{{ consultation.dossier.value.topics.find((t: any) => t.key === key)?.title || key }}</span>
          </div>
        </div>
      </div>

      <!-- ═══════ 对话消息 ═══════ -->
      <template v-for="(msg, i) in (consultation.messages.value ?? [])" :key="i">
        <div v-if="msg.role === 'user'" class="chat-msg chat-msg--user">
          <div class="msg-bubble user-bubble">{{ msg.text }}</div>
        </div>
        <div v-else class="chat-msg chat-msg--spirit">
          <div class="msg-avatar">
            <SpiritAvatar :planet="chatPlanet" :symbol="chatSymbol" :name="chatName" size="sm" />
          </div>
          <div class="msg-bubble spirit-bubble">
            <p>{{ msg.text }}</p>
            <div v-if="msg.evidence?.length" class="evidence-area">
              <div class="evidence-line" v-for="(e, ei) in msg.evidence" :key="ei">
                <span class="evidence-bullet">•</span>
                <span>{{ e.fact }}</span>
              </div>
            </div>
          </div>
        </div>
      </template>

      <!-- ═══════ 洞察草稿卡 ═══════ -->
      <div v-if="consultation.currentInsight.value" class="chat-msg chat-msg--spirit">
        <InsightDraftCard
          :insight="consultation.currentInsight.value!"
          @decide="({ decision, editedQuote }) => consultation.decideInsight(consultation.currentInsight.value!.insight_id, decision, editedQuote)"
        />
      </div>

      <!-- ═══════ 操作按钮 ═══════ -->
      <div v-if="consultation.currentActions.value.length && !consultation.isThinking.value" class="chat-msg chat-msg--spirit">
        <ConsultationActions
          :actions="consultation.currentActions.value"
          @action="(a: string) => consultation.sendTurn('', a)"
        />
      </div>

      <!-- 思考中 -->
      <div v-if="consultation.isThinking.value" class="chat-msg chat-msg--spirit">
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
      <div v-if="needUpgrade" class="quota-banner">
        <span class="quota-text">{{ quotaReason || "对话额度已用完" }}</span>
        <button class="quota-btn" @click="showPayment = true">升级解锁</button>
      </div>
      <input
        v-model="inputText"
        class="chat-input"
        :disabled="consultation.isThinking.value"
        :placeholder="consultation.isThinking.value ? `${chatName}正在回应你的问题……` : `和${chatName}说点什么...`"
        @keyup.enter="sendMessage"
      />
      <button
        class="chat-send-btn"
        :disabled="!inputText.trim() || consultation.isThinking.value"
        :style="{ background: inputText.trim() ? chatColor : 'var(--border-light)' }"
        @click="sendMessage">
        <svg v-if="!consultation.isThinking.value" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
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

    <PaymentModal
      :visible="showPayment"
      :product-id="upgradeProduct"
      channel="iap"
      @close="showPayment = false"
      @success="onPaymentSuccess"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, watch, onMounted, computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useHomeData } from "@/composables/useHomeData";
import SpiritAvatar from "@/components/garden/SpiritAvatar.vue";
import PaymentModal from "@/components/PaymentModal.vue";
import { useSpiritConsultation } from "@/composables/useSpiritConsultation";
import InsightDraftCard from "./components/InsightDraftCard.vue";
import ConsultationActions from "./components/ConsultationActions.vue";

const route = useRoute();
const router = useRouter();
const homeData = useHomeData();

const chatPlanet = computed(() => String(route.params.planet || "SUN"));
const reportId = computed(() => homeData.reportId.value);

const consultation = useSpiritConsultation(reportId);

const spiritProfile = computed(() => homeData.planetProfiles.value?.planet_characters?.[chatPlanet.value]);
const chatSymbol = computed(() => spiritProfile.value?.persona?.symbol || "★");
const chatName = computed(() => spiritProfile.value?.persona?.name_zh || chatPlanet.value);
const chatArchetype = computed(() => spiritProfile.value?.persona?.archetype_zh || "");
const chatColor = computed(() => spiritProfile.value?.persona?.visual_color || "#B87D5A");

const inputText = ref("");
const isLoaded = ref(false);
const messagesEl = ref<HTMLElement | null>(null);
const needUpgrade = ref(false);
const quotaReason = ref("");
const showPayment = ref(false);
const upgradeProduct = ref("monthly_auto");

const entryContext = computed(() => ({
  source: String(route.query.source || "direct"),
  daily_question: String(route.query.question || ""),
  transit_detail: String(route.query.detail || ""),
}));

function scrollToBottom() {
  if (messagesEl.value) {
    messagesEl.value.scrollTop = messagesEl.value.scrollHeight;
  }
}

function onPaymentSuccess() {
  showPayment.value = false;
  needUpgrade.value = false;
}

async function sendMessage() {
  const t = inputText.value.trim();
  if (!t || consultation.isThinking.value) return;
  inputText.value = "";
  await consultation.sendTurn(t);
  await nextTick();
  scrollToBottom();
}

function goBack() { router.back(); }

onMounted(async () => {
  await homeData.refreshData();
  isLoaded.value = true;
  if (reportId.value) {
    const planet = String(route.params.planet || "SUN");
    await consultation.start(planet, entryContext.value);
  }
});

watch(() => consultation.messages.value.length, () => {
  nextTick(scrollToBottom);
});
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
.quota-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 8px 14px;
  margin-bottom: 8px;
  border-radius: 12px;
  background: rgba(255, 154, 139, 0.1);
  border: 1px solid rgba(255, 154, 139, 0.25);
}
.quota-text {
  font-size: var(--text-sm);
  color: var(--text-secondary);
}
.quota-btn {
  flex-shrink: 0;
  padding: 6px 14px;
  border-radius: 999px;
  border: none;
  background: #ff9a8b;
  color: #fff;
  font-size: var(--text-sm);
  font-weight: 600;
  cursor: pointer;
}

/* ── v2 深度咨询── */
.structure-map {
  padding: var(--space-2) var(--space-3);
}
.structure-title {
  font-size: 13px;
  line-height: 1.6;
  color: var(--text-secondary);
  margin: 0 0 10px;
}
.structure-topics {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.topic-chip {
  padding: 4px 10px;
  border-radius: 12px;
  background: rgba(184, 125, 90, 0.08);
  border: 1px solid rgba(184, 125, 90, 0.18);
  font-size: 12px;
  color: var(--chat-color, #B87D5A);
  transition: all 0.15s;
}
.topic-chip.active {
  background: var(--chat-color, #B87D5A);
  color: #fff;
}

/* v2 操作按钮 */
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
  color: var(--chat-color, #B87D5A);
  font-size: 12px;
  cursor: pointer;
  background: transparent;
  transition: all 0.15s;
}
.consult-action:hover, .consult-action:active {
  background: var(--chat-color, #B87D5A);
  color: #fff;
}

/* v2 洞察草稿卡 */
.insight-draft {
  margin: 0;
  padding: 12px;
  border-radius: 12px;
  background: rgba(184, 125, 90, 0.06);
  border: 1px solid rgba(184, 125, 90, 0.2);
}
.insight-draft__head {
  display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;
}
.insight-draft__badge {
  font-size: 11px; color: var(--chat-color, #B87D5A); font-weight: 600;
}
.insight-draft__planet { font-size: 10px; color: var(--text-tertiary); }
.insight-draft__summary { margin: 0 0 8px; font-size: 13px; line-height: 1.6; color: var(--text-primary); }
.insight-draft__label { display: block; font-size: 11px; color: var(--text-tertiary); margin-bottom: 3px; }
.insight-draft__textarea {
  width: 100%; border: 1px solid var(--border-light); border-radius: 8px;
  padding: 6px 8px; font-size: 13px; line-height: 1.5; resize: vertical; box-sizing: border-box;
}
.insight-draft__action { margin-top: 8px; padding: 6px 8px; background: rgba(255,255,255,0.5); border-radius: 6px; }
.insight-draft__action-label { font-size: 10px; color: var(--text-tertiary); }
.insight-draft__buttons { margin-top: 10px; display: flex; flex-wrap: wrap; gap: 6px; }
.insight-btn {
  flex: 1 1 calc(50% - 6px); padding: 6px 4px; border-radius: 8px;
  border: 1px solid var(--border-light); background: #fff; font-size: 12px; cursor: pointer;
}
.insight-btn--confirm { background: var(--chat-color, #B87D5A); color: #fff; border-color: transparent; }
.insight-btn--partial, .insight-btn--reject, .insight-btn--uncertain { background: rgba(0,0,0,0.03); }
</style>

