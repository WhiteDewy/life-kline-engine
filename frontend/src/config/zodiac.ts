/**
 * 星座 & 行星共享常量
 *
 * 统一 Zodiac signs、planet colors、symbols 等被多文件引用的常量。
 * 之前散落在 main.vue、Wanxiang/index.vue、CharacterWheel.vue、AIChatPanel.vue 中。
 */

// ── 12 星座完整数据 ──
export const ZODIAC_SIGNS = [
  { key: "ARIES",       name: "白羊座",  emoji: "♈", color: "#E8533F", element: "火" },
  { key: "TAURUS",      name: "金牛座",  emoji: "♉", color: "#7B8D6F", element: "土" },
  { key: "GEMINI",      name: "双子座",  emoji: "♊", color: "#F2A900", element: "风" },
  { key: "CANCER",      name: "巨蟹座",  emoji: "♋", color: "#9BC4D0", element: "水" },
  { key: "LEO",         name: "狮子座",  emoji: "♌", color: "#F2A900", element: "火" },
  { key: "VIRGO",       name: "处女座",  emoji: "♍", color: "#7B8D6F", element: "土" },
  { key: "LIBRA",       name: "天秤座",  emoji: "♎", color: "#E8A0BF", element: "风" },
  { key: "SCORPIO",     name: "天蝎座",  emoji: "♏", color: "#6D28D9", element: "水" },
  { key: "SAGITTARIUS", name: "射手座",  emoji: "♐", color: "#4B6BAA", element: "火" },
  { key: "CAPRICORN",   name: "摩羯座",  emoji: "♑", color: "#5B6770", element: "土" },
  { key: "AQUARIUS",    name: "水瓶座",  emoji: "♒", color: "#8B5CF6", element: "风" },
  { key: "PISCES",      name: "双鱼座",  emoji: "♓", color: "#06B6D4", element: "水" },
];

// ── 英文 key → emoji（给 CharacterWheel / AIChatPanel / Wanxiang 用）──
export const SIGN_EMOJI_MAP: Record<string, string> = {
  ARIES: "♈", TAURUS: "♉", GEMINI: "♊", CANCER: "♋",
  LEO: "♌", VIRGO: "♍", LIBRA: "♎", SCORPIO: "♏",
  SAGITTARIUS: "♐", CAPRICORN: "♑", AQUARIUS: "♒", PISCES: "♓",
};

// ── 中文名 → emoji（给 main.vue 的 sunSignEmoji 用）──
export const SIGN_EMOJI_BY_NAME: Record<string, string> = {
  白羊座: "♈", 金牛座: "♉", 双子座: "♊", 巨蟹座: "♋",
  狮子座: "♌", 处女座: "♍", 天秤座: "♎", 天蝎座: "♏",
  射手座: "♐", 摩羯座: "♑", 水瓶座: "♒", 双鱼座: "♓",
};

// ── 行星颜色（10 行星）──
export const PLANET_COLORS = [
  "#F2A900", "#9BC4D0", "#7B8D6F", "#E8A0BF", "#E8533F",
  "#4B6BAA", "#5B6770", "#8B5CF6", "#06B6D4", "#6D28D9",
];

// ── 古典行星颜色（7 行星）──
export const PLANET_COLORS_CLASSICAL = [
  "#F2A900", "#9BC4D0", "#7B8D6F", "#E8A0BF",
  "#E8533F", "#4B6BAA", "#5B6770",
];

// ── 行星展示顺序 ──
export const PLANET_ORDER = [
  "SUN", "MOON", "MERCURY", "VENUS", "MARS",
  "JUPITER", "SATURN", "URANUS", "NEPTUNE", "PLUTO",
];

// ── 行星符号 ──
export const PLANET_SYMBOLS: Record<string, string> = {
  SUN: "☉", MOON: "☽", MERCURY: "☿", VENUS: "♀", MARS: "♂",
  JUPITER: "♃", SATURN: "♄", URANUS: "♅", NEPTUNE: "♆", PLUTO: "♇",
};
