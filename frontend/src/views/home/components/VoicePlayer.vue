<template>
  <button
    v-if="supported"
    class="voice-player-btn"
    :class="[
      block ? 'voice-player-btn--block' : '',
      size === 'mini' ? 'voice-player-btn--mini' : '',
      { 'voice-player-btn--playing': playing, 'voice-player-btn--paused': paused }
    ]"
    :title="buttonLabel"
    @click="toggle"
  >
    <span class="voice-player-icon">{{ icon }}</span>
    <span class="voice-player-label" v-if="showLabel">{{ buttonLabel }}</span>
  </button>
</template>

<script setup lang="ts">
import { ref, computed, onUnmounted } from "vue";

const props = withDefaults(
  defineProps<{
    text: string;
    style?: "broadcast" | "whisper";
    showLabel?: boolean;
    block?: boolean;
    size?: "normal" | "mini";
  }>(),
  {
    style: "broadcast",
    showLabel: false,
    block: false,
    size: "normal",
  }
);

type State = "idle" | "playing" | "paused";
const state = ref<State>("idle");
let currentUtterance: SpeechSynthesisUtterance | null = null;

const supported = computed(() => {
  return typeof window !== "undefined" && "speechSynthesis" in window;
});

const icon = computed(() => {
  switch (state.value) {
    case "playing":
      return "⏹";
    case "paused":
      return "▶";
    default:
      return "🎤";
  }
});

const buttonLabel = computed(() => {
  switch (state.value) {
    case "playing":
      return "停止";
    case "paused":
      return "继续";
    default:
      return "语音播报";
  }
});

const playing = computed(() => state.value === "playing");
const paused = computed(() => state.value === "paused");

function getChineseVoice(): SpeechSynthesisVoice | null {
  const voices = window.speechSynthesis.getVoices();
  // Prefer zh-CN or zh-TW
  return (
    voices.find((v) => v.lang.startsWith("zh-CN")) ||
    voices.find((v) => v.lang.startsWith("zh-HK")) ||
    voices.find((v) => v.lang.startsWith("zh-TW")) ||
    voices.find((v) => v.lang.startsWith("zh")) ||
    null
  );
}

function speak() {
  if (!supported.value || !props.text) return;

  window.speechSynthesis.cancel();

  const utterance = new SpeechSynthesisUtterance(props.text);
  utterance.lang = "zh-CN";
  utterance.rate = props.style === "whisper" ? 0.85 : 1.0;
  utterance.pitch = props.style === "whisper" ? 0.9 : 1.0;

  const zhVoice = getChineseVoice();
  if (zhVoice) {
    utterance.voice = zhVoice;
  }

  utterance.onstart = () => {
    state.value = "playing";
  };

  utterance.onend = () => {
    state.value = "idle";
    currentUtterance = null;
  };

  utterance.onerror = () => {
    state.value = "idle";
    currentUtterance = null;
  };

  utterance.onpause = () => {
    state.value = "paused";
  };

  utterance.onresume = () => {
    state.value = "playing";
  };

  currentUtterance = utterance;
  window.speechSynthesis.speak(utterance);
}

function toggle() {
  if (!supported.value) return;

  if (state.value === "idle") {
    speak();
  } else if (state.value === "playing") {
    if (window.speechSynthesis.speaking && currentUtterance) {
      window.speechSynthesis.pause();
    } else {
      window.speechSynthesis.cancel();
      state.value = "idle";
    }
  } else if (state.value === "paused") {
    if (window.speechSynthesis.paused && currentUtterance) {
      window.speechSynthesis.resume();
    } else {
      // Fallback: restart
      speak();
    }
  }
}

// Cancel on unmount
onUnmounted(() => {
  if (currentUtterance) {
    window.speechSynthesis.cancel();
  }
});
</script>

<style scoped>
.voice-player-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px 14px;
  border-radius: 14px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
  font-size: 13px;
  font-weight: 600;
  font-family: inherit;
  cursor: pointer;
  transition: all 0.25s ease;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
  white-space: nowrap;
  line-height: 1;
}

.voice-player-btn:hover {
  background: rgba(255, 255, 255, 0.18);
  transform: translateY(-1px);
}

.voice-player-btn:active {
  transform: scale(0.97);
}

.voice-player-btn--playing {
  background: rgba(255, 80, 80, 0.2);
  border-color: rgba(255, 80, 80, 0.3);
}

.voice-player-btn--playing:hover {
  background: rgba(255, 80, 80, 0.3);
}

.voice-player-btn--paused {
  background: rgba(255, 215, 0, 0.15);
  border-color: rgba(255, 215, 0, 0.25);
}

.voice-player-btn--block {
  display: flex;
  width: 100%;
}

.voice-player-btn--mini {
  padding: 2px 6px;
  border-radius: 8px;
  font-size: 10px;
  gap: 3px;
}
.voice-player-btn--mini .voice-player-icon {
  font-size: 11px;
}

.voice-player-icon {
  font-size: 16px;
  line-height: 1;
}

.voice-player-label {
  white-space: nowrap;
}
</style>
