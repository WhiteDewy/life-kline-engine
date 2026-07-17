<template>
  <article class="domain-panel">
    <!-- hero_bridge: 承接上面的叙事 -->
    <p class="domain-bridge" v-if="domain.hero_bridge">{{ domain.hero_bridge }}</p>

    <div class="domain-head">
      <h3 class="domain-theme">{{ domain.core_theme || domainLabel }}</h3>
    </div>

    <div class="domain-body">
      <p
        class="domain-text"
        v-for="(para, i) in structureParagraphs"
        :key="'s'+i"
        :class="{ 'domain-text--first': i === 0, 'domain-text--alt': i % 2 === 1 }"
        v-html="highlightEmotion(para)"
      ></p>

      <div class="psychology-block" v-if="domain.psychology">
        <span class="psych-badge">🧠 心理层面</span>
        <p class="psych-text" v-html="highlightEmotion(domain.psychology)"></p>
      </div>

      <div class="suggestion-block" v-if="domain.suggestion">
        <span class="suggestion-badge">💡 建议方向</span>
        <p class="suggestion-text" v-html="highlightEmotion(domain.suggestion)"></p>
      </div>
    </div>

    <div class="domain-hook">
      <div class="hook-divider"></div>
      <p class="hook-text">是不是说到你心里了？关于{{ domainLabel }}，你肯定有更多想问的——</p>
      <el-button class="hook-btn" type="primary" plain round @click="$emit('chat', domain.domain)">
        聊聊{{ domainLabel }}
      </el-button>
    </div>
  </article>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { DomainReport } from "@/utils/types";
import { highlightEmotion } from "@/utils/textHighlight";

const props = defineProps<{
  domain: DomainReport;
}>();

defineEmits<{
  chat: [domainKey: string];
}>();

const DOMAIN_LABELS: Record<string, string> = {
  personal: "你的性格",
  appearance: "你的气质",
  career: "你的事业",
  work_skill: "你的工作方式",
  education: "你的学业",
  finance: "你的财运",
  romance: "你的感情",
  marriage: "你的婚姻",
  family: "你的家庭",
  partnership: "你的合伙",
  children: "你的亲子关系",
  health: "你的健康",
};

const domainLabel = computed(() => DOMAIN_LABELS[props.domain.domain] || props.domain.domain);

const structureParagraphs = computed(() => {
  const text = props.domain.structure || "";
  return text
    .split("\n")
    .map((s) => s.trim())
    .filter((s) => s.length > 0);
});
</script>

<style scoped lang="less">
.domain-panel {
  padding: 0;
}
.domain-bridge {
  margin: 0 0 18px;
  color: #94a3b8;
  font-size: 14px;
  font-style: italic;
  line-height: 1.7;
}
.domain-head {
  margin-bottom: 18px;
}
.domain-theme {
  margin: 0;
  color: #f8fafc;
  font-size: 22px;
  font-weight: 700;
  line-height: 1.4;
}
.domain-body {
  display: grid;
  gap: 10px;
}

/* ── 结构段落 ── */
.domain-text {
  margin: 0;
  color: #cbd5e1;
  line-height: 1.9;
  font-size: 15px;
  padding: 8px 12px;
  border-radius: 8px;
  transition: background 0.2s;
}
.domain-text--first {
  color: #e2e8f0;
  font-size: 15.5px;
  border-left: 2px solid rgba(212, 175, 55, 0.3);
  padding-left: 14px;
  background: rgba(255, 255, 255, 0.012);
}
.domain-text--alt {
  background: rgba(255, 255, 255, 0.01);
}

/* ── 心理层面 ── */
.psychology-block {
  margin-top: 10px;
  padding: 18px 18px 16px;
  border-radius: 16px;
  border-left: 3px solid rgba(99, 102, 241, 0.35);
  background: rgba(99, 102, 241, 0.05);
}
.psych-badge {
  display: inline-block;
  margin-bottom: 8px;
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(99, 102, 241, 0.15);
  color: #a5b4fc;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.04em;
}
.psych-text {
  margin: 0;
  color: #c7d2fe;
  line-height: 1.8;
  font-size: 14px;
}

/* ── 建议方向 ── */
.suggestion-block {
  margin-top: 10px;
  padding: 18px 18px 16px;
  border-radius: 16px;
  background: rgba(212, 175, 55, 0.05);
  border: 1px solid rgba(212, 175, 55, 0.1);
}
.suggestion-badge {
  display: inline-block;
  margin-bottom: 8px;
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(212, 175, 55, 0.12);
  color: #d4af37;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.04em;
}
.suggestion-text {
  margin: 0;
  color: #e2d5a4;
  line-height: 1.8;
  font-size: 14px;
}

/* ── Hook ── */
.domain-hook {
  margin-top: 24px;
  padding-top: 0;
  border-top: none;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}
.hook-divider {
  width: 100%;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.08), transparent);
  margin-bottom: 4px;
}
.hook-text {
  margin: 0;
  color: #94a3b8;
  font-size: 14px;
  line-height: 1.6;
}
.hook-btn {
  font-weight: 600;
}

/* ── 高亮标记（scoped 穿透） ── */
:deep(mark.hl-pain)     { background: linear-gradient(180deg, transparent 55%, rgba(248,113,113,0.18) 55%); color: #fca5a5; }
:deep(mark.hl-need)     { background: linear-gradient(180deg, transparent 55%, rgba(167,139,250,0.18) 55%); color: #c4b5fd; }
:deep(mark.hl-gift)     { background: linear-gradient(180deg, transparent 55%, rgba(212,175,55,0.22) 55%); color: #f8fafc; }
:deep(mark.hl-honest)   { background: linear-gradient(180deg, transparent 55%, rgba(148,163,184,0.12) 55%); color: #cbd5e1; font-style: italic; }
:deep(mark.hl-correct)  { color: #a5b4fc; font-weight: 500; }
:deep(mark.hl-insight)  { color: #d4af37; font-weight: 500; }
:deep(mark.hl-contrast) { background: linear-gradient(180deg, transparent 55%, rgba(212,175,55,0.1) 55%); }
:deep(mark.hl-ease)     { color: #6ee7b7; }
:deep(mark.hl-warn)     { color: #fbbf24; border-bottom: 1px dashed rgba(251,191,36,0.25); }
:deep(mark.hl-action)   { color: #f8fafc; font-weight: 600; }
:deep(mark)             { background: transparent; border-radius: 2px; padding: 0 2px; }
</style>
