/**
 * 首页示例命盘 — 匿名化真人案例，供用户快速体验报告内容。
 * 所有示例走统一的引擎通道，不设特殊分支。
 */
import { formatCoordinateLabel, formatTimezoneLabel } from "@/utils/coordinates";

export const HOMEPAGE_EXAMPLE_VISIBLE =
  import.meta.env.VITE_SHOW_HOMEPAGE_EXAMPLE !== "false";

export const FEATURED_EXAMPLES = [
  {
    key: "example-creative",
    name: "小夏",
    gender: "女",
    birthTime: "1995-08-12T14:30:00",
    birthTimeLabel: "1995年8月12日 14:30",
    birthPlace: "成都",
    longitude: 104.06,
    latitude: 30.67,
    longitudeLabel: formatCoordinateLabel(104.06, "longitude"),
    latitudeLabel: formatCoordinateLabel(30.67, "latitude"),
    timezone: 8,
    timezoneLabel: formatTimezoneLabel(8),
    tagline: "创意型人格，想知道自己适合做什么",
  },
  {
    key: "example-career",
    name: "阿正",
    gender: "男",
    birthTime: "1989-03-25T09:15:00",
    birthTimeLabel: "1989年3月25日 09:15",
    birthPlace: "杭州",
    longitude: 120.15,
    latitude: 30.28,
    longitudeLabel: formatCoordinateLabel(120.15, "longitude"),
    latitudeLabel: formatCoordinateLabel(30.28, "latitude"),
    timezone: 8,
    timezoneLabel: formatTimezoneLabel(8),
    tagline: "事业转型期，不知道该不该换赛道",
  },
];
