export interface PlanetMeaningEntry {
  key: string;
  label: string;
  groupKey: string;
  groupTitle: string;
  essence: string;
  focus: string;
  caution?: string;
}

export const PLANET_MEANINGS: Record<string, PlanetMeaningEntry> = {
  SUN: {
    key: "SUN",
    label: "太阳",
    groupKey: "will",
    groupTitle: "意志",
    essence: "纯粹的自我意志，带着使命感与无限可能性。",
    focus: "会把注意力放到使命、主导权与自我定义上。",
    caution: "容易因为过度强调主观意志而忽略现实节奏。",
  },
  MOON: {
    key: "MOON",
    label: "月亮",
    groupKey: "behavior",
    groupTitle: "行为",
    essence: "守护自我，持续追寻安全感、满足感与内在安稳。",
    focus: "会把注意力放到情绪、照料、归属与安全边界上。",
    caution: "容易被情绪与环境牵着走，先稳内在再谈效率。",
  },
  MERCURY: {
    key: "MERCURY",
    label: "水星",
    groupKey: "behavior",
    groupTitle: "行为",
    essence: "定位自我，通过学习、连接与表达理解世界和自己。",
    focus: "会把注意力放到信息、沟通、学习、判断与路径选择上。",
    caution: "容易因为过度分散、怀疑或用脑过度而消耗自己。",
  },
  VENUS: {
    key: "VENUS",
    label: "金星",
    groupKey: "behavior",
    groupTitle: "行为",
    essence: "展示自我，用吸引力、审美与价值观让自己被看见。",
    focus: "会把注意力放到关系、价值、审美、资源协调与被喜欢上。",
    caution: "容易为了维持和谐、讨好或享乐而忽略真实代价。",
  },
  MARS: {
    key: "MARS",
    label: "火星",
    groupKey: "behavior",
    groupTitle: "行为",
    essence: "实践自我，把意志变成行动、争取、突破与执行。",
    focus: "会把注意力放到推进、竞争、决断、攻坚与拿结果上。",
    caution: "容易因为着急、对抗或提前消耗而拉高摩擦成本。",
  },
  JUPITER: {
    key: "JUPITER",
    label: "木星",
    groupKey: "belief",
    groupTitle: "信念",
    essence: "拓展自我，以信念、远见和对可能性的相信打开机会。",
    focus: "会把注意力放到成长、贵人、资源扩张、意义与远方上。",
    caution: "容易过度乐观、承诺过量，先落地再放大。",
  },
  SATURN: {
    key: "SATURN",
    label: "土星",
    groupKey: "belief",
    groupTitle: "信念",
    essence: "磨炼自我，在压力、责任与长期建设中夯实能力。",
    focus: "会把注意力放到结构、纪律、耐力、责任与长期主义上。",
    caution: "容易因为压抑、迟缓或过度保守而错过节奏。",
  },
  URANUS: {
    key: "URANUS",
    label: "天王星",
    groupKey: "will",
    groupTitle: "意志",
    essence: "超越自我，用绝对理性、革新与突破旧框架完成更新。",
    focus: "会把注意力放到创新、反常规、独立判断与理性突围上。",
    caution: "容易走得太快、太跳脱，让关系或现实跟不上。",
  },
  NEPTUNE: {
    key: "NEPTUNE",
    label: "海王星",
    groupKey: "will",
    groupTitle: "意志",
    essence: "摈弃过强主观意识，借由感受、潜意识与奉献进入更深层连接。",
    focus: "会把注意力放到灵感、共情、理想、救赎与模糊边界上。",
    caution: "容易理想化、失去边界或在混乱中被外界裹挟。",
  },
  PLUTO: {
    key: "PLUTO",
    label: "冥王星",
    groupKey: "will",
    groupTitle: "意志",
    essence: "重塑自我，在失去、掌控、极端拉扯与再生中完成蜕变。",
    focus: "会把注意力放到掌控、深层欲望、断舍离与重建上。",
    caution: "容易走向偏执、极端或非黑即白的控制模式。",
  },
  NORTH_NODE: {
    key: "NORTH_NODE",
    label: "北交点",
    groupKey: "direction",
    groupTitle: "成长方向",
    essence: "提醒你往更陌生但更有成长性的方向去发展。",
    focus: "会把注意力放到长期成长课题与未来要学会的能力上。",
  },
  SOUTH_NODE: {
    key: "SOUTH_NODE",
    label: "南交点",
    groupKey: "direction",
    groupTitle: "惯性模式",
    essence: "代表熟悉的惯性、旧经验与容易反复回去的舒适区。",
    focus: "会把注意力放到你已经会做、但不能一直依赖的旧路径上。",
  },
  CHIRON: {
    key: "CHIRON",
    label: "凯龙星",
    groupKey: "healing",
    groupTitle: "疗愈",
    essence: "对应伤口、敏感点，以及把伤口转成理解力与疗愈力的能力。",
    focus: "会把注意力放到脆弱感、补课与修复他人或自己的方式上。",
  },
  JUNO: {
    key: "JUNO",
    label: "婚神星",
    groupKey: "relationship",
    groupTitle: "承诺关系",
    essence: "对应承诺、契约、伴侣标准与长期合作关系。",
    focus: "会把注意力放到关系中的规则、公平、承诺与绑定方式上。",
  },
  CERES: {
    key: "CERES",
    label: "谷神星",
    groupKey: "nurture",
    groupTitle: "养分",
    essence: "对应滋养、照顾、失去与重新建立供给感的能力。",
    focus: "会把注意力放到喂养、养护、资源供应与被需要感上。",
  },
  PALLAS: {
    key: "PALLAS",
    label: "智神星",
    groupKey: "strategy",
    groupTitle: "策略",
    essence: "对应洞察模式、抽象思维、策略与解决复杂问题的能力。",
    focus: "会把注意力放到布局、判断、看穿结构与策略处理上。",
  },
  VESTA: {
    key: "VESTA",
    label: "灶神星",
    groupKey: "devotion",
    groupTitle: "专注",
    essence: "对应专注、奉献、长期投入与守住核心火种的方式。",
    focus: "会把注意力放到守护、投入、节制与长期专注的主题上。",
  },
};

const PLANET_LABEL_TO_KEY = Object.values(PLANET_MEANINGS).reduce<Record<string, string>>(
  (result, item) => {
    result[item.label] = item.key;
    return result;
  },
  {}
);

export function getPlanetMeaning(value?: string | null): PlanetMeaningEntry | null {
  if (!value) return null;

  const raw = String(value).trim();
  const normalizedKey = raw.toUpperCase();
  if (PLANET_MEANINGS[normalizedKey]) {
    return PLANET_MEANINGS[normalizedKey];
  }

  const mappedKey = PLANET_LABEL_TO_KEY[raw];
  if (mappedKey) {
    return PLANET_MEANINGS[mappedKey] ?? null;
  }

  return null;
}

export function extractPlanetKeysFromText(text?: string | null): string[] {
  if (!text) return [];
  const content = String(text);

  return Object.values(PLANET_MEANINGS)
    .filter((item) => content.includes(item.label))
    .map((item) => item.key);
}

export function buildPlanetBlendLine(
  values: Array<string | null | undefined>,
  variant: "essence" | "focus" | "caution" = "essence"
): string {
  const lines = values
    .map((value) => getPlanetMeaning(value))
    .filter((item, index, list): item is PlanetMeaningEntry =>
      Boolean(item) && list.findIndex((entry) => entry?.key === item?.key) === index
    )
    .map((item) => {
      const detail =
        variant === "focus" ? item.focus : variant === "caution" ? item.caution || item.essence : item.essence;
      return `${item.label}：${detail}`;
    });

  return lines.join(" ");
}
