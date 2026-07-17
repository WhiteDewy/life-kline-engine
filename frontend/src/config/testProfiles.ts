import { formatCoordinateLabel, formatTimezoneLabel } from "@/utils/coordinates";

export interface TestUserProfile {
  key: string;
  name: string;
  gender: string;
  birthDatetime: string;
  birthTime: string;
  birthTimeLabel: string;
  birthPlace: string;
  lat: number;
  lon: number;
  latitudeLabel: string;
  longitudeLabel: string;
  timezone: number;
  timezoneLabel: string;
  note: string;
  tags: string[];
  lifeTrack?: string[];
  validationAnchors?: Array<{
    title: string;
    summary: string;
    tags?: string[];
  }>;
}

const DEFAULT_LAT = 35.7;
const DEFAULT_LON = 113.35;

export const TEST_USER_PROFILES: TestUserProfile[] = [
  {
    key: "xiatian",
    name: "\u590f\u5929",
    gender: "\u5973",
    birthDatetime: "1991-03-21T09:25",
    birthTime: "1991-03-21T09:25:00",
    birthTimeLabel: "1991-03-21 09:25",
    birthPlace: "\u5c71\u897f\u7701\u9675\u5ddd\u53bf\u9644\u57ce\u9547\u9752\u6768\u5e84\u6751",
    lat: DEFAULT_LAT,
    lon: DEFAULT_LON,
    latitudeLabel: formatCoordinateLabel(DEFAULT_LAT, "latitude"),
    longitudeLabel: formatCoordinateLabel(DEFAULT_LON, "longitude"),
    timezone: 8,
    timezoneLabel: formatTimezoneLabel(8),
    note: "\u5f53\u524d\u9ed8\u8ba4\u6d4b\u8bd5\u7528\u6237\uff0c\u73b0\u5b9e\u8def\u5f84\u5df2\u7ecf\u6709\u8f83\u6e05\u695a\u7684\u8de8\u9886\u57df\u8f6c\u5411\uff0c\u9002\u5408\u7528\u6765\u5bf9\u7167\u672c\u547d\u84dd\u56fe\u4e0e\u804c\u4e1a\u8def\u7ebf\u662f\u5426\u6253\u4e2d\u3002",
    tags: [
      "\u9ed8\u8ba4\u6d4b\u8bd5",
      "\u5973\u76d8",
      "\u672c\u547d\u84dd\u56fe",
      "\u9636\u6bb5\u5bfc\u822a",
      "\u8de8\u9886\u57df\u8f6c\u578b",
      "\u73b0\u5b9e\u6821\u9a8c",
    ],
    lifeTrack: [
      "\u5927\u5b66\u5b66\u4e60\u56ed\u6797\u4e13\u4e1a",
      "\u6bd5\u4e1a\u540e\u5148\u505a\u56ed\u6797\u8bbe\u8ba1",
      "\u540e\u7eed\u8f6c\u884c\u8ba1\u7b97\u673a\u884c\u4e1a\u505a\u7a0b\u5e8f\u5458",
      "\u73b0\u5728\u5f00\u59cb\u5b66\u4e60\u7384\u5b66\u3001\u5360\u661f\u7b49\u9886\u57df",
    ],
    validationAnchors: [
      {
        title: "\u56ed\u6797\u4e0e\u8bbe\u8ba1\u8d77\u70b9",
        summary: "\u5927\u5b66\u5b66\u56ed\u6797\uff0c\u6bd5\u4e1a\u540e\u5148\u8fdb\u5165\u56ed\u6797\u8bbe\u8ba1\u65b9\u5411\uff0c\u8fd9\u6761\u7ebf\u53ef\u7528\u6765\u6821\u9a8c\u5ba1\u7f8e\u3001\u7a7a\u95f4\u3001\u7ed3\u6784\u548c\u8bbe\u8ba1\u76f8\u5173\u8c61\u5f81\u3002",
        tags: ["\u56ed\u6797", "\u8bbe\u8ba1", "\u5ba1\u7f8e", "\u7a7a\u95f4"],
      },
      {
        title: "\u8f6c\u5411\u7a0b\u5e8f\u5f00\u53d1",
        summary: "\u540e\u9762\u8f6c\u884c\u5230\u8ba1\u7b97\u673a\u884c\u4e1a\u505a\u7a0b\u5e8f\u5458\uff0c\u53ef\u7528\u6765\u6821\u9a8c\u6c34\u661f\u3001\u5929\u738b\u661f\u3001\u6c34\u74f6\u7b49\u201c\u7cfb\u7edf\u3001\u903b\u8f91\u3001\u6280\u672f\u201d\u8def\u7ebf\u3002",
        tags: ["\u7a0b\u5e8f\u5458", "\u8ba1\u7b97\u673a", "\u6280\u672f", "\u903b\u8f91"],
      },
      {
        title: "\u73b0\u5728\u5b66\u7384\u5b66\u5360\u661f",
        summary: "\u5f53\u4e0b\u5f00\u59cb\u6295\u5165\u7384\u5b66\u3001\u5360\u661f\u7b49\u5b66\u4e60\uff0c\u53ef\u7528\u6765\u6821\u9a8c9\u5bab\u300112\u5bab\u3001\u6728\u661f\u3001\u6d77\u738b\u661f\u7b49\u201c\u610f\u4e49\u3001\u4fe1\u5ff5\u3001\u7075\u6027\u3001\u8eab\u5fc3\u7075\u201d\u4e3b\u9898\u3002",
        tags: ["\u7384\u5b66", "\u5360\u661f", "\u5b66\u4e60", "\u7075\u6027"],
      },
    ],
  },
  {
    key: "beibei",
    name: "\u5317\u5317",
    gender: "\u7537",
    birthDatetime: "1989-11-25T18:00",
    birthTime: "1989-11-25T18:00:00",
    birthTimeLabel: "1989-11-25 18:00",
    birthPlace: "\u6cb3\u5317\u7701",
    lat: 38.7,
    lon: 114.5,
    latitudeLabel: formatCoordinateLabel(38.7, "latitude"),
    longitudeLabel: formatCoordinateLabel(114.5, "longitude"),
    timezone: 8,
    timezoneLabel: formatTimezoneLabel(8),
    note: "\u7528\u4e8e\u7537\u76d8\u6d4b\u8bd5\uff0c\u53ef\u76f4\u63a5\u7528\u6765\u5bf9\u7167\u672c\u547d\u84dd\u56fe\u4e0e\u9636\u6bb5\u5bfc\u822a\u7ed3\u679c\u3002",
    tags: [
      "\u6d4b\u8bd5\u7528\u6237",
      "\u7537\u76d8",
      "\u672c\u547d\u84dd\u56fe",
      "\u9636\u6bb5\u5bfc\u822a",
    ],
  },
  {
    key: "wenjing",
    name: "\u6587\u955c",
    gender: "\u5973",
    birthDatetime: "1987-01-28T15:20",
    birthTime: "1987-01-28T15:20:00",
    birthTimeLabel: "1987-01-28 15:20",
    birthPlace: "\u4e0a\u6d77\u7701",
    lat: 31.2333333333,
    lon: 121.4333333333,
    latitudeLabel: formatCoordinateLabel(31.2333333333, "latitude"),
    longitudeLabel: formatCoordinateLabel(121.4333333333, "longitude"),
    timezone: 8,
    timezoneLabel: formatTimezoneLabel(8),
    note: "\u7528\u4e8e\u5973\u76d8\u6d4b\u8bd5\uff0c\u65b9\u4fbf\u5bf9\u7167\u672c\u547d\u7ed3\u6784\u3001\u76f8\u4f4d\u4e0e\u89d2\u8272\u6a21\u5757\u7684\u5c55\u793a\u6548\u679c\u3002",
    tags: [
      "\u6d4b\u8bd5\u7528\u6237",
      "\u5973\u76d8",
      "\u672c\u547d\u84dd\u56fe",
      "\u9636\u6bb5\u5bfc\u822a",
    ],
  },
];

export const DEFAULT_TEST_USER_PROFILE_KEY = TEST_USER_PROFILES[0]?.key || "xiatian";

export function getTestUserProfileByKey(key?: string | null) {
  if (!key) return undefined;
  return TEST_USER_PROFILES.find((item) => item.key === key);
}

export function buildSubjectFromProfile(
  profile: Pick<TestUserProfile, "name" | "gender" | "birthTime" | "lat" | "lon" | "timezone">
) {
  return {
    name: profile.name,
    gender: profile.gender,
    birth_time: profile.birthTime,
    lat: profile.lat,
    lon: profile.lon,
    timezone: profile.timezone,
  };
}
