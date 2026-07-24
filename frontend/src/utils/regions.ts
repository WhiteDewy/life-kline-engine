/**
 * 行政区域地址 ↔ code 转换工具
 *
 * `element-china-area-data` 只提供了 codeToText（code→text）的单向映射。
 * 这个模块从 regionData 构建 text→codes 的 Map，用于在加载已有 profile
 * 时恢复 <el-cascader> 的选中状态。
 *
 * regionData codes 格式：省 2 位 / 市 4 位 / 区 6 位（如 "11" / "1101" / "110101"）
 */
import { regionData } from "element-china-area-data";

function buildTextToCodesMap(): Map<string, string[]> {
  const map = new Map<string, string[]>();

  for (const p of regionData) {
    const pName = p.label;
    const pValue = p.value;

    if (p.children) {
      for (const c of p.children) {
        const cName = c.label;
        const cValue = c.value;

        if (c.children) {
          for (const d of c.children) {
            // 三级：省 市 区（如 "北京市 市辖区 东城区"）
            const fullName = `${pName} ${cName} ${d.label}`;
            map.set(fullName, [pValue, cValue, d.value]);
          }
        }

        // 两级：直辖市，省 = 市，可能没有区级 children
        const fullName2 = `${pName} ${cName}`;
        if (!map.has(fullName2)) {
          map.set(fullName2, [pValue, cValue]);
        }
      }
    }

    // 一级：只有省
    if (!map.has(pName)) {
      map.set(pName, [pValue]);
    }
  }

  return map;
}

const _textToCodes: Map<string, string[]> = buildTextToCodesMap();

/**
 * 将地点文本（如 "北京市 市辖区 东城区"）转换为 cascader codes
 * （如 ["11", "1101", "110101"]）。
 *
 * 查找策略：
 * 1. 精确匹配
 * 2. 模糊匹配：返回 text 与 key 互相包含的最长 key 对应的 codes
 *
 * @param text 地点文本，格式为 "省 市 区"（空格分隔）
 * @returns codes 数组，未找到时返回 null
 */
export function textToRegionCodes(text: string): string[] | null {
  if (!text) return null;
  const trimmed = text.trim();

  // 精确匹配
  const exact = _textToCodes.get(trimmed);
  if (exact) return exact;

  // 模糊匹配：找最长互相包含的 key
  let bestMatch: string[] | null = null;
  let bestLen = 0;

  for (const [key, codes] of _textToCodes) {
    if (trimmed.includes(key) || key.includes(trimmed)) {
      const matchLen = Math.min(key.length, trimmed.length);
      if (matchLen > bestLen) {
        bestLen = matchLen;
        bestMatch = codes;
      }
    }
  }

  return bestMatch;
}
