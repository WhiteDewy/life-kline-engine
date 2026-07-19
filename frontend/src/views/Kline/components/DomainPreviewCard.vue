<template>
  <article class="preview-card">
    <p class="preview-bridge" v-if="domain.hero_bridge">{{ domain.hero_bridge }}</p>

    <div class="preview-head">
      <h3 class="preview-theme">{{ domain.core_theme || domainLabel }}</h3>
      <span class="preview-badge">免费预览</span>
    </div>

    <div class="preview-body">
      <div class="preview-text-clip">
        <p class="preview-text" v-html="highlightEmotion(truncatedText)"></p>
        <div class="preview-fade"></div>
      </div>

      <div class="preview-locked">
        <div class="locked-icon">🔒</div>
        <p class="locked-title">解锁完整解读</p>
        <p class="locked-desc">
          查看 {{ domainLabel }}的完整分析——包含心理层面解读、建议方向，以及深度对话。
        </p>
        <div class="locked-actions">
          <el-button class="unlock-btn" type="primary" round @click="$emit('unlock-domain', domain.domain)">
            仅解锁{{ domainLabel }} · ¥9.9
          </el-button>
          <el-button class="unlock-all-btn" plain round @click="$emit('unlock-all')">
            解锁全部 12 领域 · ¥29.9
          </el-button>
        </div>
      </div>
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
  "unlock-domain": [domainKey: string];
  "unlock-all": [];
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

const truncatedText = computed(() => {
  const text = props.domain.structure || "";
  const lines = text.split("\n").filter((s) => s.trim());
  const firstPara = lines[0] || "";
  if (firstPara.length > 120) {
    return firstPara.slice(0, 120) + "…";
  }
  return firstPara;
});
</script>

<style scoped lang="less">
.preview-card {
  padding: 0;
}
.preview-bridge {
  margin: 0 0 16px;
  color: #8b7355;
  font-size: 13px;
  font-style: italic;
  line-height: 1.7;
}
.preview-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
.preview-theme {
  margin: 0;
  color: #4a3728;
  font-size: 20px;
  font-weight: 700;
}
.preview-badge {
  padding: 3px 10px;
  border-radius: 999px;
  background: rgba(255,154,139, 0.12);
  color: #ff9a8b;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.04em;
}
.preview-body {
  position: relative;
}
.preview-text-clip {
  position: relative;
  max-height: 72px;
  overflow: hidden;
}
.preview-text {
  color: #5c4a3a;
  line-height: 1.9;
  font-size: 15px;
  padding: 8px 14px;
  border-left: 2px solid rgba(255,154,139, 0.25);
  background: rgba(255, 255, 255, 0.012);
  border-radius: 6px;
  margin: 0;
}
.preview-fade {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 40px;
  background: linear-gradient(transparent, #0f172a);
  pointer-events: none;
}
.preview-locked {
  margin-top: 20px;
  padding: 24px 20px;
  border-radius: 16px;
  border: 1px solid rgba(255,154,139, 0.12);
  background: linear-gradient(135deg, rgba(255,154,139, 0.04), rgba(255,154,139, 0.01));
  text-align: center;
}
.locked-icon {
  font-size: 24px;
  margin-bottom: 8px;
}
.locked-title {
  margin: 0 0 6px;
  color: #4a3728;
  font-size: 16px;
  font-weight: 600;
}
.locked-desc {
  margin: 0 0 18px;
  color: #8b7355;
  font-size: 13px;
  line-height: 1.6;
}
.locked-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: center;
}
.unlock-btn {
  font-weight: 600;
  min-width: 220px;
}
.unlock-all-btn {
  font-weight: 500;
  min-width: 220px;
  color: #8b7355;
  border-color: rgba(255,255,255,0.08);
}
</style>
