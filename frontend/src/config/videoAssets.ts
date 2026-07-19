/**
 * 星座视频背景配置
 *
 * 视频放于 src/assets/video/ 目录下。
 * 命名规则: {sign_lowercase}.mp4  例: aries.mp4, cancer.mp4
 */

// ── 动态导入所有视频 ──
const videoModules = import.meta.glob<string>("../assets/video/*.mp4", {
  query: "?url",
  import: "default",
  eager: true,
});

// ── 星座 ↔ 视频文件映射 ──
const SIGN_TO_FILE: Record<string, string> = {
  ARIES: "aries",
  TAURUS: "taurus",
  GEMINI: "gemini",
  CANCER: "cancer",
  LEO: "leo",
  VIRGO: "virgo",
  LIBRA: "libra",
  SCORPIO: "scorpio",
  SAGITTARIUS: "sagittarius",
  CAPRICORN: "capricorn",
  AQUARIUS: "aquarius",
  PISCES: "pisces",
};

/** 获取已存在的视频 URL map: { ARIES: "/src/assets/video/aries.mp4", ... } */
function buildVideoMap(): Record<string, string> {
  const map: Record<string, string> = {};
  for (const [path, url] of Object.entries(videoModules)) {
    for (const [sign, filename] of Object.entries(SIGN_TO_FILE)) {
      if (path.toLowerCase().includes(filename)) {
        map[sign] = url;
      }
    }
  }
  return map;
}

const VIDEO_URLS = buildVideoMap();

/** 所有可用视频的 URL 列表 */
export const AVAILABLE_VIDEOS: string[] = Object.values(VIDEO_URLS);

/** 所有可用视频对应的星座 key */
export const AVAILABLE_SIGNS: string[] = Object.keys(VIDEO_URLS);

// ── 当前太阳星座（按日期粗略计算）──
const ZODIAC_SEASONS: { sign: string; start: [number, number] }[] = [
  { sign: "CAPRICORN", start: [1, 1] },
  { sign: "AQUARIUS", start: [1, 20] },
  { sign: "PISCES", start: [2, 19] },
  { sign: "ARIES", start: [3, 21] },
  { sign: "TAURUS", start: [4, 20] },
  { sign: "GEMINI", start: [5, 21] },
  { sign: "CANCER", start: [6, 21] },
  { sign: "LEO", start: [7, 23] },
  { sign: "VIRGO", start: [8, 23] },
  { sign: "LIBRA", start: [9, 23] },
  { sign: "SCORPIO", start: [10, 23] },
  { sign: "SAGITTARIUS", start: [11, 22] },
  { sign: "CAPRICORN", start: [12, 22] },
];

function getCurrentZodiacSeason(): string {
  const now = new Date();
  const m = now.getMonth() + 1;
  const d = now.getDate();
  let current = "CANCER"; // fallback
  for (const s of ZODIAC_SEASONS) {
    const [sm, sd] = s.start;
    if (m > sm || (m === sm && d >= sd)) {
      current = s.sign;
    }
  }
  return current;
}

/**
 * 获取当前应播放的视频 URL。
 * 优先当前星座季节 → 无对应视频则随机选一个可用视频 → 无视频返回空字符串。
 */
export function getCurrentVideo(): string {
  const season = getCurrentZodiacSeason();
  if (VIDEO_URLS[season]) return VIDEO_URLS[season];
  if (AVAILABLE_VIDEOS.length > 0) {
    return AVAILABLE_VIDEOS[Math.floor(Math.random() * AVAILABLE_VIDEOS.length)];
  }
  return "";
}

/**
 * 根据星座 key（如 "LEO", "ARIES"）获取对应视频 URL。
 * 无对应视频时 fallback 到 getCurrentVideo()。
 */
export function getVideoBySign(sign: string): string {
  const upper = sign?.toUpperCase() || "";
  if (VIDEO_URLS[upper]) return VIDEO_URLS[upper];
  return getCurrentVideo();
}

/**
 * 获取下一个视频 URL（用于轮播），按可用星座列表顺序循环。
 */
export function getNextVideo(currentUrl: string): string {
  if (AVAILABLE_VIDEOS.length <= 1) return currentUrl;
  const idx = AVAILABLE_VIDEOS.indexOf(currentUrl);
  return AVAILABLE_VIDEOS[(idx + 1) % AVAILABLE_VIDEOS.length];
}
