/**
 * 文字情绪高亮 —— 在纯文本中标记痛点、共鸣点、洞察点。
 * 每个段落最多应用 2 个高亮，避免视觉过载。
 */

const EMOTION_PATTERNS: Array<{ regex: RegExp; class: string }> = [
  // 痛点：怕、难、被伤
  { regex: /(你最怕的[^。，]+)/g, class: "hl-pain" },
  { regex: /(被[^你]{1,12}是你最[^。，]+)/g, class: "hl-pain" },
  { regex: /(最[^，]{1,20}的是[^。，]{1,30})/g, class: "hl-pain" },
  // 需求：你需要、你真正
  { regex: /(你需要[^。，]+)/g, class: "hl-need" },
  { regex: /(你真正[^是]{1,20}是[^。，]{1,30})/g, class: "hl-need" },
  // 天赋：这是你的、做自己
  { regex: /(这是你的[^。，]+)/g, class: "hl-gift" },
  { regex: /(做自己[^。，]+)/g, class: "hl-gift" },
  // 实话
  { regex: /(说实话[^。，]+)/g, class: "hl-honest" },
  // 纠正
  { regex: /(你不是[^。，]+)/g, class: "hl-correct" },
  { regex: /(不是[^。，]+——[^。，]+)/g, class: "hl-contrast" },
  // 洞察：你的X是Y
  { regex: /(你的[^是]{1,20}是[^。，]{1,35})/g, class: "hl-insight" },
  { regex: /(答案[^。，]{1,30})/g, class: "hl-insight" },
  { regex: /(这意味着[^。，]{1,30})/g, class: "hl-insight" },
  // 轻松
  { regex: /(不用[^。，]{1,20})/g, class: "hl-ease" },
  { regex: /(顺势[^。，]{1,25})/g, class: "hl-ease" },
  // 提醒
  { regex: /(留意[^。，]{1,30})/g, class: "hl-warn" },
  { regex: /(注意[^。，]{1,30})/g, class: "hl-warn" },
  // 行动
  { regex: /(是时候[^。，]+)/g, class: "hl-action" },
  { regex: /(别让[^。，]+)/g, class: "hl-action" },
  { regex: /(好好用[^。，]+)/g, class: "hl-action" },
];

export function highlightEmotion(text: string): string {
  let result = text;
  const applied = new Set<number>();
  let count = 0;
  const MAX_PER_PARA = 2;

  for (const pattern of EMOTION_PATTERNS) {
    if (count >= MAX_PER_PARA) break;
    let match;
    pattern.regex.lastIndex = 0;
    while ((match = pattern.regex.exec(result)) !== null) {
      if (applied.has(match.index)) continue;
      if (count >= MAX_PER_PARA) break;
      applied.add(match.index);
      count++;
      const matched = match[1] ?? "";
      const before = result.slice(0, match.index);
      const after = result.slice(match.index + matched.length);
      result = `${before}<mark class="${pattern.class}">${matched}</mark>${after}`;
      pattern.regex.lastIndex = match.index + 30;
      break;
    }
  }
  return result;
}
