---
name: place-input-fix-plan
description: 出生地/现居地 cascader 回显修复 + 手动坐标输入方案
metadata:
  type: project
---

# 出生地/现居地回显 + 手动输入方案

## 问题

用户在三个页面编辑/填写地址时，`el-cascader` 不能回显已保存的地区：
1. 后端存储了 `birth_place` 文本（如 "北京市 市辖区 东城区"），但前端 codes 数组始终为空
2. `element-china-area-data` 库只导出 `codeToText`（code → 文本），没有反向函数 `textToCode`
3. Onboarding 页面完全没有手动坐标入口，geocoding 失败时用户无法继续

## 技术分析

### `element-china-area-data` 数据结构

底层数据来自 `china-division` 包的 `pca-code.json`：

```json
[{"code":"11","name":"北京市","children":[
  {"code":"1101","name":"市辖区","children":[
    {"code":"110101","name":"东城区"},
    ...
  ]}
]}]
```

经过 `formatData` 包装后导出为 `regionData`：
```typescript
{value: "11", label: "北京市", children: [
  {value: "1101", label: "市辖区", children: [
    {value: "110101", label: "东城区"}
  ]}
]}
```

注意：code 是 2/4/6 位数字字符串（非任务初步估计的 `'110000'` 带尾零格式）。`codeToText` 是扁平映射表：`{"11": "北京市", "1101": "市辖区", "110101": "东城区", ...}`。

**库现有导出**：`regionData`、`codeToText`、`provinceAndCityData`、`pcTextArr`、`pcaTextArr` — 无 `textToCode`。

### 三个页面现状

| 页面 | 地点输入 | 手动坐标 | 回显 | codes 来源 |
|:---|:---|:---|:---|:---|
| `Profile/index.vue` | `el-cascader` v-model `bRC`/`rRC` | `details` 折叠（`sMC`/`sRMC` 初始 false，不显眼） | 仅文本回显 (`saved-place` div)，codes 数组为空 | `lp()` L32 只设 `f.birthPlace`，不设 `bRC.value` |
| `Onboarding/index.vue` | `el-cascader` v-model `birthRegionCodes`/`residenceRegionCodes` | 完全没有 | 不加载已有档案（新用户流程）；若中途返回，codes 不恢复 | 初始化空数组 L200-204 |
| `Analysis/index.vue` | 弹窗内 `el-cascader` v-model `selectedOptions` | 弹窗"手动填写" tab（功能完整） | `resetForm()` L238 重置 `selectedOptions = []` | 同样不恢复 |

### 核心算法：文本 → region codes 反向解析

#### 方案选择

**方案 A：全量预建索引（推荐）**

遍历 `regionData` 树，构建 `Map<string, string[]>`：
- key：完整路径文本（如 `"北京市 市辖区 东城区"`）
- value：codes 数组（如 `["11", "1101", "110101"]`）
- 同时注册前缀（`"北京市"` → `["11"]`，`"北京市 市辖区"` → `["11", "1101"]`）

优点：
- O(1) 查询
- 精确匹配 + 前缀降级
- 构建一次（约 3400 个节点），内存微不足道（~100KB）

缺点：初始化需遍历整棵树（毫秒级，对用户体验无影响）。

**方案 B：递归树遍历**

每次查询都从根遍历树，逐 token 匹配。

优点：零额外内存开销。
缺点：每次 O(depth × breadth)，模糊匹配逻辑复杂。

**结论：选择方案 A（全量预建索引）**。

#### 算法伪码

```typescript
function buildTextToCodesMap(regionData): Map<string, string[]> {
  const map = new Map()
  function walk(nodes, pathLabels, pathCodes) {
    for (const node of nodes) {
      const newLabels = [...pathLabels, node.label]
      const newCodes = [...pathCodes, node.value]
      map.set(newLabels.join(' '), newCodes)
      if (node.children?.length) walk(node.children, newLabels, newCodes)
    }
  }
  walk(regionData, [], [])
  return map
}

function textToRegionCodes(text: string): string[] {
  // 1. 标准化空白字符
  // 2. 精确全文匹配
  // 3. 前缀降级匹配（从最长到最短，如 "省 市 区 额外文本" → "省 市 区" → "省 市" → "省"）
  // 4. 都不匹配返回 []
}
```

#### 降级处理

当用户手填地名（如 "山西省陵川县附城镇青杨庄村"）无法在 `regionData` 中匹配时：
- `textToRegionCodes()` 返回 `[]`
- cascader 保持空白
- 用户通过手动坐标入口填写经纬度
- 这是预期行为：无法解析的文本不应该伪造 codes

### 公共模块设计

**位置**：`frontend/src/utils/regions.ts`

导出：
```typescript
// 反向解析：文本 → codes
export function textToRegionCodes(text: string): string[]

// 正向（封装 codeToText，方便统一 import）
export function regionCodesToText(codes: string[]): string
```

不放在 composable 中：纯函数不需要 Vue 响应式，放 `utils/` 即可。三个页面各自 import。

### 三页面修复方案

#### 1. Profile（P0 最高优先）

**文件**：`frontend/src/views/Profile/index.vue`

**改动**：
a) L18 新增 `import { textToRegionCodes } from "@/utils/regions"`
b) L32 `lp()` 中，`f.birthPlace` 赋值后追加：
   ```typescript
   bRC.value = textToRegionCodes(f.birthPlace || "")
   rRC.value = textToRegionCodes(f.residencePlace || "")
   ```
c) 移除 `saved-place` 文本备用显示（cascader 回显后不再需要）
d) 手动坐标 UI 改进：
   - 将 `<details>` 替换为更显眼的设计：
     - "获取坐标" 按钮旁增加 "手动输入" 文字链接
     - 点击后展开经纬度输入（度+分+方向，保留现有精细格式）
   - 或至少将 summary 文案改为更明显的 "手动输入经纬度 ▼/▲"

#### 2. Analysis（P0）

**文件**：`frontend/src/views/Analysis/index.vue`

**改动**：
a) L156 新增 `import { textToRegionCodes } from "@/utils/regions"`
b) L238 `resetForm()` 中，`Object.assign(form, p)` 后追加：
   ```typescript
   if (form.birthPlace) {
     selectedOptions.value = textToRegionCodes(form.birthPlace)
   }
   ```
   放在 `syncManualCoordsFromForm()` 之前即可

#### 3. Onboarding（P1）

**文件**：`frontend/src/views/Onboarding/index.vue`

**改动**：
a) 新增 `import { textToRegionCodes } from "@/utils/regions"`
b) 新增手动坐标输入区域：
   - 在坐标栏 `coord-bar` 下方增加 "手动输入坐标" 文字链接
   - 点击展开简单经纬度输入（度+分+方向），复用 `splitCoordinateParts`/`composeCoordinateValue`
   - 与 Profile 的交互模式保持一致
c) 可选：如果未来 Onboarding 也加载已有档案，同样做回显修复（目前仅新用户流程）

### 关于直辖市等跨级行政区的处理

直辖市（北京、天津、上海、重庆）的 `regionData` 结构是三层：
```
"北京市" → "市辖区" → "东城区"
```
"市辖区" 在 cascader 中是必选项。若用户保存的文本是 "北京市 东城区"（跳过了 "市辖区"），反向查找会因前缀匹配失败而返回空（"北京市" 可以匹配到 `["11"]`，但 "北京市 东城区" 不是完整路径）。这种情况应降级处理，走手动填写。

### 测试要点

1. 普通城市：`"广东省 广州市 天河区"` → `["44", "4401", "440106"]`
2. 直辖市：`"北京市 市辖区 东城区"` → `["11", "1101", "110101"]`
3. 仅省份：`"北京市"` → `["11"]`
4. 两层级：`"广东省 广州市"` → `["44", "4401"]`
5. 非标准文本：`"山西省陵川县附城镇青杨庄村"` → `[]`（降级，无伪造 codes）
6. 空文本：`""` → `[]`
7. 前后空格：`" 北京市 市辖区 东城区 "` → `["11", "1101", "110101"]`
8. 连续多个空格：`"北京市  市辖区  东城区"` → `["11", "1101", "110101"]`

### 变更影响范围

- 纯增量：新增 `utils/regions.ts`（约 40 行）
- 三个页面各加 1 行 import + 1-2 个赋值语句
- 不修改数据库 schema，不修改 API 契约
- 不修改 `element-china-area-data` 库本身

### 实施顺序

1. 创建 `frontend/src/utils/regions.ts` 并手动验证
2. 修复 Profile 页面（回显 + 手动坐标 UI 改进）
3. 修复 Analysis 页面（回显）
4. 修复 Onboarding 页面（新增手动坐标入口 + 回显准备）

**Why:** 用户编辑档案时 cascader 不回显已保存的地区名，体验断裂。同时 Onboarding 缺少手动坐标输入作为 geocoding 失败的兜底方案。

**How to apply:**
- 按上述顺序实施，优先 Profile 页面
- 所有 reverse lookup 走 `utils/regions.ts` 的统一函数
- 非标准文本返回空数组是预期行为，配合手动坐标输入使用
