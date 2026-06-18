import { formatCoordinateLabel, formatTimezoneLabel } from "@/utils/coordinates";

export const HOMEPAGE_EXAMPLE_VISIBLE =
  import.meta.env.VITE_SHOW_HOMEPAGE_EXAMPLE !== "false";

export const FEATURED_NATAL_EXAMPLE = {
  key: "huang-jinrong",
  name: "黄金荣",
  gender: "男",
  birthTime: "1868-12-14T00:01:00",
  birthTimeLabel: "1868-12-14 00:01",
  birthPlace: "浙江余姚",
  longitude: 121.1667,
  latitude: 30.05,
  longitudeLabel: formatCoordinateLabel(121.1667, "longitude"),
  latitudeLabel: formatCoordinateLabel(30.05, "latitude"),
  timezone: 8,
  timezoneLabel: formatTimezoneLabel(8),
};

export const DEFAULT_TEST_SUBJECT = {
  name: "夏天",
  gender: "女",
  birthDatetime: "1991-03-21T09:25",
  birthTime: "1991-03-21T09:25:00",
  birthPlace: "山西省陵川县附城镇青杨庄村",
  lat: 35.7,
  lon: 113.35,
  latitudeLabel: formatCoordinateLabel(35.7, "latitude"),
  longitudeLabel: formatCoordinateLabel(113.35, "longitude"),
  timezone: 8,
  timezoneLabel: formatTimezoneLabel(8),
};
