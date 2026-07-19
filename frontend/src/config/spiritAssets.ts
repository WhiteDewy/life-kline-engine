/**
 * 星灵图片资源配置
 *
 * 图片放于 frontend/public/spirits/ 目录下。
 * 修改此文件中的路径即可全局生效，留空 → 自动 fallback 到 Unicode 符号。
 *
 * 目录结构（预留给用户放入图片）：
 *   public/spirits/
 *     sun/                      # 太阳星灵（12 星座 × 2 性别 = 24 张）
 *       aries_male.png          # 白羊男
 *       aries_female.png        # 白羊女
 *       taurus_male.png         # 金牛男
 *       taurus_female.png       # 金牛女
 *       ...
 *       pisces_female.png       # 双鱼女
 *     moon.png                  # 月亮星灵（后续扩展）
 *     mercury.png               # 水星星灵（后续扩展）
 *     ...
 */

// ── 通用：7 行星固定图片（非太阳或太阳无匹配 sign 时使用）──
export const SPIRIT_IMAGES: Record<string, string> = {
  SUN: "", // 留空 → 走 sign+gender 匹配；也可设兜底图片
  MOON: "",
  MERCURY: "",
  VENUS: "",
  MARS: "",
  JUPITER: "",
  SATURN: "",
};

// ── 通用：10 行星 × 12 星座头像映射 ──
// 路径约定: /spirits/planets/{planet_lower}/{sign_lower}.png
// 全部初始为空，用户后续填入图片
const PLANET_SIGN_IMAGES: Record<string, Record<string, string>> = {
  SUN:     { ARIES: "", TAURUS: "", GEMINI: "", CANCER: "", LEO: "", VIRGO: "", LIBRA: "", SCORPIO: "", SAGITTARIUS: "", CAPRICORN: "", AQUARIUS: "", PISCES: "" },
  MOON:    { ARIES: "", TAURUS: "", GEMINI: "", CANCER: "", LEO: "", VIRGO: "", LIBRA: "", SCORPIO: "", SAGITTARIUS: "", CAPRICORN: "", AQUARIUS: "", PISCES: "" },
  MERCURY: { ARIES: "", TAURUS: "", GEMINI: "", CANCER: "", LEO: "", VIRGO: "", LIBRA: "", SCORPIO: "", SAGITTARIUS: "", CAPRICORN: "", AQUARIUS: "", PISCES: "" },
  VENUS:   { ARIES: "", TAURUS: "", GEMINI: "", CANCER: "", LEO: "", VIRGO: "", LIBRA: "", SCORPIO: "", SAGITTARIUS: "", CAPRICORN: "", AQUARIUS: "", PISCES: "" },
  MARS:    { ARIES: "", TAURUS: "", GEMINI: "", CANCER: "", LEO: "", VIRGO: "", LIBRA: "", SCORPIO: "", SAGITTARIUS: "", CAPRICORN: "", AQUARIUS: "", PISCES: "" },
  JUPITER: { ARIES: "", TAURUS: "", GEMINI: "", CANCER: "", LEO: "", VIRGO: "", LIBRA: "", SCORPIO: "", SAGITTARIUS: "", CAPRICORN: "", AQUARIUS: "", PISCES: "" },
  SATURN:  { ARIES: "", TAURUS: "", GEMINI: "", CANCER: "", LEO: "", VIRGO: "", LIBRA: "", SCORPIO: "", SAGITTARIUS: "", CAPRICORN: "", AQUARIUS: "", PISCES: "" },
  URANUS:  { ARIES: "", TAURUS: "", GEMINI: "", CANCER: "", LEO: "", VIRGO: "", LIBRA: "", SCORPIO: "", SAGITTARIUS: "", CAPRICORN: "", AQUARIUS: "", PISCES: "" },
  NEPTUNE: { ARIES: "", TAURUS: "", GEMINI: "", CANCER: "", LEO: "", VIRGO: "", LIBRA: "", SCORPIO: "", SAGITTARIUS: "", CAPRICORN: "", AQUARIUS: "", PISCES: "" },
  PLUTO:   { ARIES: "", TAURUS: "", GEMINI: "", CANCER: "", LEO: "", VIRGO: "", LIBRA: "", SCORPIO: "", SAGITTARIUS: "", CAPRICORN: "", AQUARIUS: "", PISCES: "" },
};

/** 按行星 + 落座获取头像图片 URL */
export function getPlanetAvatarImage(planet: string, sign: string): string {
  const planetUpper = planet?.toUpperCase() || "";
  const signUpper = sign?.toUpperCase() || "";
  const planetImages = PLANET_SIGN_IMAGES[planetUpper];
  if (!planetImages) return "";
  return planetImages[signUpper] || "";
}
const SUN_SIGN_IMAGES: Record<string, Record<string, string>> = {
  ARIES:       { male: "", female: "" },
  TAURUS:      { male: "", female: "" },
  GEMINI:      { male: "", female: "" },
  CANCER:      { male: "", female: "" },
  LEO:         { male: "", female: "" },
  VIRGO:       { male: "", female: "" },
  LIBRA:       { male: "", female: "" },
  SCORPIO:     { male: "", female: "" },
  SAGITTARIUS: { male: "", female: "" },
  CAPRICORN:   { male: "", female: "" },
  AQUARIUS:    { male: "", female: "" },
  PISCES:      { male: "", female: "" },
};

/** 按行星 key 获取通用图片 URL */
export function getSpiritImage(planet: string): string {
  return SPIRIT_IMAGES[planet] || "";
}

/** 获取太阳星灵图片 —— 按星座 + 性别匹配 */
export function getSunSignImage(sign: string, gender?: string | null): string {
  const signUpper = sign?.toUpperCase() || "";
  const signImages = SUN_SIGN_IMAGES[signUpper];
  if (!signImages) return "";

  // 优先精确匹配性别
  const g = (gender || "").toLowerCase();
  if (g === "男" || g === "male") return signImages.male || "";
  if (g === "女" || g === "female") return signImages.female || "";

  // 无性别 → 尝试任一非空
  return signImages.male || signImages.female || "";
}

/** 行星符号 fallback */
export const SPIRIT_SYMBOLS: Record<string, string> = {
  SUN: "☉", MOON: "☽", MERCURY: "☿", VENUS: "♀",
  MARS: "♂", JUPITER: "♃", SATURN: "♄",
};

/** 一键填入所有太阳图片路径（用户放入图片后运行） */
export function fillSunImages(basePath = "/spirits/sun") {
  const signs = Object.keys(SUN_SIGN_IMAGES);
  for (const sign of signs) {
    const lower = sign.toLowerCase();
    SUN_SIGN_IMAGES[sign] = {
      male: `${basePath}/${lower}_male.png`,
      female: `${basePath}/${lower}_female.png`,
    };
  }
}
