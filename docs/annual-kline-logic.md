# Annual Life K-Line Engine PRD

## 1. 背景与问题 (Context & Problem)

### 1.1 核心矛盾
- **法达星限 (Firdaria)**：基于出生时间计算的连续时间段，起止时间精确到分钟，周期长度不固定（如 1.43 年、2 年、3 年等）。
- **年度 K 线 (Annual K-Line)**：用户期望以**年龄 (Age)** 为维度的运势坐标，即“每一岁一个坐标点”（如 0岁、1岁、2岁...）。
- **问题**：法达周期与整岁不重合。例如，某个法达运势在“32.5岁”时结束，那么“32岁”这一整岁（32.0 - 33.0）的运势应该如何计算？

### 1.2 当前现状 (Current Implementation)
目前前端（`LifeStructureChart.vue`）采用了简单的**整岁切分（Integer Snapping）**逻辑：
- 遍历 0-99 岁。
- 对于每一岁（Age N），寻找覆盖该年龄的第一个法达周期。
- 判定逻辑：`if (Age >= floor(StartAge) && Age < ceil(EndAge))`。
- **缺点**：精度丢失。若运势在年中（如 32.5岁）切换，当前逻辑会强制将整年归属给其中一个周期，导致运势转折点显示滞后或提前。

---

## 2. 解决方案：时间加权重采样 (Time-Weighted Resampling)

为了获得精确的整岁评分，我们采用**时间加权平均法**。

### 2.1 算法逻辑
假设我们要计算 **32岁**（即 32.0岁 到 33.0岁）的综合评分：

1. **定义时间窗口**：
   - 目标窗口：`[Age_start, Age_end]` (例如 32.0 到 33.0)。
   - 总时长：`Duration = 1.0` 年。

2. **寻找重叠周期**：
   - 找出所有与该窗口有交集的法达周期 `P1, P2...`。

3. **计算权重**：
   - 对于每个周期 `Pi`，计算其在窗口内的覆盖时长 `d_i`。
   - 权重 `w_i = d_i / Duration`。

4. **合成评分**：
   - `Score_Age = Σ (Score_Pi * w_i)`
   - `Trend_Age = Σ (Trend_Pi * w_i)`

### 2.2 示例
- **目标年龄**：32岁（32.0 - 33.0）。
- **周期 A**（好运，得分 80）：覆盖 30.0 至 32.4 岁。在目标窗口内覆盖 `[32.0, 32.4]`，时长 0.4 年。
- **周期 B**（差运，得分 40）：覆盖 32.4 至 34.0 岁。在目标窗口内覆盖 `[32.4, 33.0]`，时长 0.6 年。
- **计算**：
  - `Score = 80 * 0.4 + 40 * 0.6`
  - `Score = 32 + 24 = 56`
- **结论**：32岁这一年整体评分 56分，且经历了由好转差的过程。

---

## 3. 数据结构设计 (Data Structure)

后端 API 应返回标准化的法达周期数据，由前端或中间层进行“年化”处理。

### 3.1 核心数据模型 (Core Models)

```typescript
// 基础法达周期 (原始数据)
interface FirdariaPeriod {
  index: number;
  timing: {
    start_date: string; // ISO 8601
    end_date: string;
    start_age: number;  // float, e.g., 32.45
    end_age: number;
  };
  // 后端需返回计算好的基础分
  trend: {
    bonus_coefficient: number; // e.g., 0.2
    type: string; // 'bull' | 'bear'
  };
  domains: {
    career: number;
    wealth: number;
    // ...
  };
}

// 年龄 K 线数据 (前端处理后)
interface AgeKPoint {
  x: string;          // "32岁"
  open: number;       // 32.0岁时的得分
  close: number;      // 33.0岁时的得分
  high: number;       // 这一岁内的最高得分
  low: number;        // 这一岁内的最低得分
  score: number;      // 加权平均分
  astrology: {
    major: string;    // 这一岁占比最大的大运星
    sub: string;      // 这一岁占比最大的子运星
  };
}
```

---

## 4. K线生成逻辑 (OHLC Generation)

### 4.1 Open/Close (开/收) - 解决边界精度问题
- **Open**: 取 `Age_start` (例如 32.0) 时刻所属周期的得分。
- **Close**: 取 `Age_end - ε` (例如 32.999...) 时刻所属周期的得分。
- **效果**：
  - 允许 **跳空缺口 (Gap)**：如果 33.0 岁发生运势突变（80分 -> 40分），32岁 K 线 Close 为 80，33岁 K 线 Open 为 40。视觉上形成断崖，符合占星学“换运即变天”的体感。

### 4.2 High/Low (高/低) - 引入波动性 (Volatility)
为避免单一周期年份出现“一字板”（Open=Close=High=Low），引入基础波动值。
- **基础波动 (Base Volatility)**: 设为 ±5 分（可配置）。
- **High**: `Max(Open, Close, 区间内所有周期的最高分) + 波动值`
- **Low**: `Min(Open, Close, 区间内所有周期的最低分) - 波动值`
- **限制**: 结果需 Clamp 在 [0, 100] 范围内。

### 4.3 运势成分 (Composition)
- **成分列表**: 记录该岁数内所有参与的运势及其权重。
  - 例如：`[{ planet: "Saturn", weight: 0.3, score: 20 }, { planet: "Jupiter", weight: 0.7, score: 90 }]`
- **主导趋势 (Dominant Trend)**:
  - 若 `Close - Open > 阈值`: "Turnaround" (转折向上)
  - 若 `Open - Close > 阈值`: "Decline" (转折向下)
  - 否则: "Stable" (平稳)

---

## 5. 实施路线 (Roadmap)

1. **后端 (Backend)**：
   - 保持 `/api/analyze` 输出精确的 `start_age` / `end_age`。
   - 确保返回 `bonus_coefficient` 或 `score`。

2. **前端 (Frontend)**：
   - 实现 `resampleByAge(periods)` 函数。
   - 遍历 `age` 从 0 到 99。
   - 对每一岁计算加权平均分、Open/Close/High/Low。
   - 解决跨周期时的“平滑过渡”问题。

3. **可视化 (Visualization)**：
   - X轴：显示年龄（0岁, 1岁...）。
   - Tooltip：显示该岁数内的运势构成。
