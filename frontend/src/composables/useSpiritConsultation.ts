import { ref, computed, type Ref } from "vue";
import { apiClient, API_BASE_URL } from "@/config/api";

/**
 * 星灵深度咨询编排（v2）。
 *
 * 引擎决定事实与咨询步骤，LLM 负责星灵口吻表达。这里只管理：
 * - 启动/恢复咨询会话
 * - 流式接收 SSE 事件（opening / text_delta / evidence / state / insight_draft / prompt / crisis / done）
 * - 用户对洞察草稿的确认/否定/编辑
 * - 一段一停、话题切换、暂停
 */
export interface ChartEvidence {
  evidence_id: string;
  source: string;
  title: string;
  fact: string;
  importance?: number;
  current?: boolean;
}
export interface StructureTopic {
  key: string;
  title: string;
  summary: string;
  evidence_ids: string[];
  interpretation_options: string[];
  inquiry_question: string;
  domain_tags?: string[];
}
export interface SpiritDossier {
  planet: string;
  spirit_name: string;
  archetype: string;
  identity_statement: string;
  evidence: ChartEvidence[];
  topics: StructureTopic[];
  topic_order: string[];
  entry_mode?: string;
}
export interface InsightDraft {
  insight_id: string;
  hypothesis_id?: string;
  planet: string;
  topic_key: string;
  evidence_ids: string[];
  user_quote: string;
  summary: string;
  domain_tags: string[];
  growth_action: string;
  validation_status?: string;
}
export interface ConsultationMessage {
  role: "user" | "spirit";
  text: string;
  evidence?: ChartEvidence[];
  insight?: InsightDraft;
  actions?: string[];
  stage?: string;
  crisis?: boolean;
}

export function useSpiritConsultation(reportId: Ref<string>) {
  const sessionId = ref<string>("");
  const dossier = ref<SpiritDossier | null>(null);
  const stage = ref<string>("introduction");
  const messages = ref<ConsultationMessage[]>([]);
  const isThinking = ref(false);
  const currentInsight = ref<InsightDraft | null>(null);
  const currentActions = ref<string[]>([]);
  const degraded = ref(false);
  const error = ref<string>("");
  const quotaExceeded = ref(false);

  const topicOrder = computed(() => dossier.value?.topic_order ?? []);
  const evidenceByTopic = computed(() => {
    const map: Record<string, ChartEvidence[]> = {};
    const byId: Record<string, ChartEvidence> = {};
    for (const e of dossier.value?.evidence ?? []) byId[e.evidence_id] = e;
    for (const t of dossier.value?.topics ?? []) {
      map[t.key] = t.evidence_ids
        .map((id) => byId[id])
        .filter((e): e is ChartEvidence => Boolean(e));
    }
    return map;
  });

  async function start(planet: string, entryContext?: Record<string, any>) {
    error.value = "";
    const res = await apiClient.post(
      `/v2/spirit-consultations/${reportId.value}`,
      { planet, entry_context: entryContext ?? null },
    );
    const data = res.data?.data ?? {};
    sessionId.value = data.session_id;
    dossier.value = data.dossier;
    stage.value = data.state?.stage ?? "introduction";
    degraded.value = !!data.degraded;
    if (data.opening_text) {
      messages.value = [
        {
          role: "spirit",
          text: data.opening_text,
          actions: data.opening_plan?.actions ?? [],
          stage: data.opening_plan?.stage,
        },
      ];
      currentActions.value = data.opening_plan?.actions ?? [];
    }
  }

  async function sendTurn(message: string, intentHint = "") {
    if (!sessionId.value) return;
    isThinking.value = true;
    error.value = "";
    const userMsg: ConsultationMessage = { role: "user", text: message };
    messages.value.push(userMsg);
    const spiritMsg: ConsultationMessage = { role: "spirit", text: "" };
    messages.value.push(spiritMsg);
    const idx = messages.value.length - 1;

    try {
      const token = localStorage.getItem("lk_token") ?? "";
      const resp = await fetch(
        `${API_BASE_URL}/v2/spirit-consultations/${reportId.value}/${sessionId.value}/turn`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            message,
            intent_hint: intentHint,
            history: messages.value
              .filter((m) => m.text)
              .slice(-6)
              .map((m) => ({ role: m.role, content: m.text })),
          }),
        },
      );
      if (resp.status === 429) {
        quotaExceeded.value = true;
        isThinking.value = false;
        return;
      }
      if (!resp.ok || !resp.body) {
        error.value = "咨询暂时无法连接";
        isThinking.value = false;
        return;
      }
      const reader = resp.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";
      let pendingEvidence: ChartEvidence[] = [];
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split("\n\n");
        buffer = parts.pop() ?? "";
        for (const part of parts) {
          const line = part.split("\n").find((l) => l.startsWith("data: "));
          if (!line) continue;
          const payload = JSON.parse(line.slice(6));
          applyEvent(payload, idx, pendingEvidence);
          pendingEvidence = messages.value[idx]?.evidence ?? pendingEvidence;
        }
      }
    } catch (e: any) {
      error.value = e?.message ?? "咨询连接中断";
    } finally {
      isThinking.value = false;
    }
  }

  function applyEvent(payload: any, idx: number, _evidence: ChartEvidence[]) {
    const kind = payload.type;
    const msg = messages.value[idx];
    if (!msg) return;
    if (kind === "opening") {
      if (!msg.text) msg.text = payload.text ?? "";
    } else if (kind === "text_delta") {
      msg.text += payload.text ?? "";
    } else if (kind === "evidence") {
      msg.evidence = payload.evidence ?? [];
    } else if (kind === "state") {
      stage.value = payload.state?.stage ?? stage.value;
    } else if (kind === "insight_draft") {
      currentInsight.value = payload.insight ?? null;
      msg.insight = payload.insight;
    } else if (kind === "prompt") {
      msg.actions = payload.actions ?? [];
      currentActions.value = payload.actions ?? [];
    } else if (kind === "crisis") {
      msg.crisis = true;
      msg.text = "我在这里陪着你。如果你正在经历难以承受的时刻，请记得你不是一个人，也可以拨打心理援助热线。";
    } else if (kind === "done") {
      msg.stage = payload.stage;
    }
  }

  async function decideInsight(
    insightId: string,
    decision: string,
    editedQuote = "",
    requestId = "",
  ) {
    if (!sessionId.value) return;
    const res = await apiClient.post(
      `/v2/spirit-consultations/${reportId.value}/${sessionId.value}/insights/${insightId}/decision`,
      { decision, edited_user_quote: editedQuote, request_id: requestId },
    );
    currentInsight.value = null;
    return res.data?.data ?? null;
  }

  function reset() {
    sessionId.value = "";
    dossier.value = null;
    stage.value = "introduction";
    messages.value = [];
    currentInsight.value = null;
    currentActions.value = [];
    isThinking.value = false;
    error.value = "";
  }

  return {
    sessionId,
    dossier,
    stage,
    messages,
    isThinking,
    currentInsight,
    currentActions,
    degraded,
    error,
    quotaExceeded,
    topicOrder,
    evidenceByTopic,
    start,
    sendTurn,
    decideInsight,
    reset,
  };
}
