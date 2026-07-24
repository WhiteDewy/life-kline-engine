<template>
  <div class="life-rhythm-page">
    <!-- 首屏：阶段 Hero -->
    <section class="section-header text-center phase-hero">
      <div class="meta-row justify-center">
        <span>当前人生阶段</span>
        <span class="font-mono ml-4">ID: 9527-ALPHA ｜ 校准精度: 99.98%</span>
      </div>

      <h1 class="main-title">结构重组期</h1>

      <p class="description max-w-2xl mx-auto">
        你正在经历的不是低谷，而是一个
        <strong class="highlight">旧模式失效、新结构尚未成型</strong>的阶段。
      </p>

      <p class="description subtle mt-4">
        在这个周期里，<strong>方向比速度更重要</strong>。
      </p>
    </section>
    <!-- 核心整合模块：全息节律堆叠图 -->
    <section class="section-block rhythm-panel">
      <div class="panel-header">
        <h2 class="block-title">阶段趋势总览</h2>
        <span class="panel-subtitle">Time Quality Overview</span>
      </div>

      <!-- 堆叠图容器 -->
      <div class="stacked-chart-container">
        <div class="chart-legend">
          <div v-for="dim in dimensions" :key="dim.name" class="legend-item">
            <span class="legend-dot" :style="{ background: dim.color }"></span>
            <span class="legend-name">{{ dim.name }}</span>
          </div>
        </div>

        <div class="chart-wrapper">
          <svg viewBox="0 0 300 150" class="stacked-chart">
            <defs>
              <linearGradient
                v-for="dim in dimensions"
                :key="'grad-' + dim.name"
                :id="'grad-' + dim.name"
                x1="0"
                y1="0"
                x2="0"
                y2="1"
              >
                <stop offset="0%" :stop-color="dim.color" stop-opacity="0.8" />
                <stop
                  offset="100%"
                  :stop-color="dim.color"
                  stop-opacity="0.2"
                />
              </linearGradient>
            </defs>

            <!-- 堆叠区域 -->
            <path
              v-for="(area, index) in stackedAreas"
              :key="index"
              :d="area.path"
              :fill="`url(#grad-${dimensions[index].name})`"
              class="stack-layer"
            />

            <!-- 当前时间线 -->
            <line
              :x1="currentIndex * 50"
              y1="0"
              :x2="currentIndex * 50"
              y2="150"
              stroke="rgba(255,255,255,0.2)"
              stroke-dasharray="4 2"
            />
          </svg>

          <!-- 时间轴 -->
          <div class="time-axis">
            <span>2023</span>
            <span
              class="current"
              :style="{ left: (currentIndex / 6) * 100 + '%' }"
              >NOW</span
            >
            <span>2025</span>
          </div>
        </div>

        <!-- 详细数据面板 -->
        <div class="dimension-grid">
          <div v-for="dim in dimensions" :key="dim.name" class="dimension-card">
            <div class="dim-header">
              <span class="dim-name" :style="{ color: dim.color }">{{
                dim.name
              }}</span>
              <span class="dim-score font-mono">{{ dim.currentScore }}</span>
            </div>
            <div class="dim-bar-bg">
              <div
                class="dim-bar-fill"
                :style="{
                  width: dim.currentScore + '%',
                  background: dim.color,
                }"
              ></div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="section-block natal-section">
      <h2 class="block-title text-center mb-8">
        为什么你会以这样的方式经历这个阶段
      </h2>

      <div class="natal-grid">
        <!-- 模块 1: 核心原型 -->
        <div class="content-card natal-card">
          <div class="card-icon-wrapper gold">
            <el-icon><Cpu /></el-icon>
          </div>
          <h3 class="natal-title">本命原型</h3>
          <p class="card-text highlight-text">
            结构与秩序<br /><span class="highlight">高度敏感者</span>
          </p>
          <p class="card-desc">
            日月升与土星结构较强，让你习惯为长期稳定负责。
          </p>
        </div>

        <!-- 模块 2: 核心优势 -->
        <div class="content-card natal-card">
          <div class="card-icon-wrapper indigo">
            <el-icon><Sunny /></el-icon>
          </div>
          <h3 class="natal-title">核心优势</h3>
          <ul class="card-list">
            <li>✔ 耐力强，擅长长跑</li>
            <li>✔ 系统思维，全局观</li>
            <li>✔ 能抗住长期的高压</li>
          </ul>
        </div>

        <!-- 模块 3: 潜在卡点 -->
        <div class="content-card natal-card">
          <div class="card-icon-wrapper red">
            <el-icon><Warning /></el-icon>
          </div>
          <h3 class="natal-title">潜在卡点</h3>
          <ul class="card-list">
            <li>⚠ 在不确定期易焦虑</li>
            <li>⚠ 容易过度自我否定</li>
            <li>⚠ 讨厌无意义的消耗</li>
          </ul>
        </div>
      </div>
    </section>

    <!-- 底部：分栏布局 (左：天象+相位，右：关键点) -->
    <div class="bottom-grid">
      <!-- 左栏：环境与相位 -->
      <div class="left-col">
        <!-- 解析卡片 2：当前天象 -->
        <section class="section-block">
          <h2 class="block-title">当前时间环境</h2>

          <div class="content-card">
            <p class="card-text">
              当前天海冥正在对你的个人结构施加压力与重塑。
            </p>

            <div class="impact-grid">
              <div class="impact-item">
                <p class="impact-title positive">正向影响</p>
                <p class="impact-desc">你会逐渐看清哪些事情值得长期投入。</p>
              </div>

              <div class="impact-item">
                <p class="impact-title negative">挑战面</p>
                <p class="impact-desc">
                  情绪与现实反馈不同步，容易怀疑“是不是我选错了”。
                </p>
              </div>
            </div>
          </div>
        </section>

        <!-- 解析卡片 3：关键相位 -->
        <section class="section-block">
          <h2 class="block-title">重要相位</h2>

          <div
            v-for="(aspect, i) in aspects"
            :key="i"
            class="content-card mb-4"
          >
            <p class="aspect-title">{{ aspect.title }}</p>
            <p class="aspect-meta">{{ aspect.meta }}</p>
            <p class="aspect-desc">{{ aspect.desc }}</p>
          </div>
        </section>
      </div>

      <!-- 右栏：下一个关键点 -->
      <div class="right-col">
        <section class="cta-section sticky-cta">
          <h2 class="cta-title">下一个关键节点</h2>
          <p class="cta-desc">
            预计在未来 <span class="highlight">2–3 个月</span> 内，
            你的节律将发生一次明显切换。
          </p>

          <div class="timeline-preview">
            <!-- 简单的垂直时间轴示意 -->
            <div class="timeline-item active">
              <div class="dot"></div>
              <div class="content">当前：结构重组</div>
            </div>
            <div class="timeline-line"></div>
            <div class="timeline-item future">
              <div class="dot"></div>
              <div class="content">2024 Q3：能量释放</div>
            </div>
          </div>

          <button class="cta-btn">解锁完整人生周期解析</button>

          <p class="cta-footer">
            查看未来 12 个月 · 学业 / 桃花 / 婚姻 / 事业 / 财富
          </p>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";
import { Cpu, Sunny, Warning } from "@element-plus/icons-vue";

const currentIndex = 3; // NOW

// 维度数据 (包含趋势)
// 归一化处理：为了堆叠图好看，假设总高度固定，按比例分配
const dimensions = [
  {
    name: "事业",
    color: "#6366F1",
    currentScore: 82,
    trend: [70, 72, 75, 82, 85, 88, 90],
  }, // Indigo
  {
    name: "学业",
    color: "#D4AF37",
    currentScore: 75,
    trend: [60, 65, 70, 75, 78, 80, 82],
  }, // Gold
  {
    name: "财富",
    color: "#10B981",
    currentScore: 55,
    trend: [50, 52, 50, 55, 60, 58, 65],
  }, // Green
  {
    name: "婚姻",
    color: "#F43F5E",
    currentScore: 60,
    trend: [55, 58, 60, 60, 60, 62, 65],
  }, // Red
  {
    name: "桃花",
    color: "#EC4899",
    currentScore: 45,
    trend: [50, 48, 45, 45, 42, 40, 50],
  }, // Pink
  {
    name: "亲子",
    color: "#06B6D4",
    currentScore: 40,
    trend: [40, 40, 42, 40, 45, 48, 50],
  }, // Cyan
];

// 计算堆叠区域路径
const stackedAreas = computed(() => {
  const width = 300;
  const height = 150;
  const timePoints = 7;
  const xStep = width / (timePoints - 1);

  // 初始化基线 (y=height, 因为SVG坐标向下)
  let baseLine = new Array(timePoints).fill(height);

  return dimensions.map((dim) => {
    // 简单的缩放：假设总分大概在 400 左右，映射到 150 高度
    // Scale factor: 150 / 450 ≈ 0.33
    const scale = 0.33;

    // 计算当前层的顶线
    const topLine = baseLine.map((y, i) => y - dim.trend[i] * scale);

    // 生成路径: M(start) -> Top Line -> L(end) -> Bottom Line (reverse) -> Z
    let path = `M0,${baseLine[0]}`;

    // 绘制顶线
    topLine.forEach((y, i) => {
      path += ` L${i * xStep},${y}`;
    });

    // 绘制底线 (逆序)
    for (let i = timePoints - 1; i >= 0; i--) {
      path += ` L${i * xStep},${baseLine[i]}`;
    }

    path += " Z";

    // 更新基线为当前顶线，供下一层使用
    const currentBaseLine = [...baseLine];
    baseLine = topLine;

    return { path, baseLine: currentBaseLine }; // Store baseLine if needed
  });
});

const aspects = [
  {
    title: "土星 ☐ 本命太阳",
    meta: "Saturn Square Sun ｜ 影响期约 4–6 个月",
    desc: "这是一次典型的自我定位修正相位，会逼你重新定义“我到底要什么”。",
  },
  {
    title: "冥王星 △ 本命月亮",
    meta: "Pluto Trine Moon ｜ 深层心理支持",
    desc: "在压力下，你的内在恢复力比你想象中更强。",
  },
];
</script>

<style scoped lang="less">
@bg: var(--bg-main);
@card-bg: var(--bg-card);
@text: var(--text-primary);
@muted: var(--text-muted);
@border: var(--border-light);
@primary: var(--color-gold);
@primary-rgb: var(--color-gold-rgb);
@radius: var(--radius);

.life-rhythm-page {
  min-height: 100vh;
  background: @bg;
  color: @text;
  font-family: var(--font-sans);
  padding: 64px 24px;
  max-width: var(--report-shell-max);
  margin: 0 auto;
}

/* Utility Classes */
.text-center {
  text-align: center;
}
.justify-center {
  justify-content: center;
}
.max-w-2xl {
  max-width: 672px;
}
.mx-auto {
  margin-left: auto;
  margin-right: auto;
}
.ml-4 {
  margin-left: 16px;
}

/* Natal Grid (Top) */
.natal-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
  margin-bottom: 0; /* Let section-block handle spacing */

  @media (max-width: 768px) {
    grid-template-columns: 1fr;
  }
}

.natal-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  min-height: 240px; /* Consistent height */

  .card-icon-wrapper {
    width: 48px;
    height: 48px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 16px;
    font-size: 24px;
    transition: all 0.3s;

    &.gold {
      background: rgba(@primary-rgb, 0.1);
      color: @primary;
    }
    &.indigo {
      background: rgba(99, 102, 241, 0.1);
      color: #6366f1;
    }
    &.red {
      background: rgba(244, 63, 94, 0.1);
      color: #f43f5e;
    }
  }

  &:hover .card-icon-wrapper {
    transform: scale(1.1);
  }

  .natal-title {
    font-size: 14px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 12px;
    color: @muted;
  }
}

.section-header {
  margin: 64px 0 48px;

  .meta-row {
    display: flex;
    /* justify-content handled by utility */
    font-size: 12px;
    color: @muted;
    margin-bottom: 16px;
  }

  .main-title {
    font-size: 48px; /* Larger title */
    font-weight: 700;
    color: @text;
    margin-bottom: 24px;
    background: linear-gradient(180deg, #fff 0%, #94a3b8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }

  .description {
    font-size: 16px;
    line-height: 1.8;
    color: @muted;

    .highlight {
      color: @text;
      font-weight: 600;
    }
  }
}

.section-block {
  margin-bottom: 32px;

  .block-title {
    font-size: 18px;
    font-weight: 600;
    margin-bottom: 16px;
    color: @text;
  }
}

/* Bottom Grid Layout */
.bottom-grid {
  display: grid;
  grid-template-columns: 1.6fr 1fr;
  gap: 32px;
  align-items: start;
  margin-top: 48px;

  @media (max-width: 768px) {
    grid-template-columns: 1fr;
  }
}

.sticky-cta {
  position: sticky;
  top: 24px;
  margin-top: 0; /* Reset default margin */
}

/* Timeline Preview */
.timeline-preview {
  margin: 32px 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;

  .timeline-line {
    width: 2px;
    height: 32px;
    background: linear-gradient(
      to bottom,
      @primary 0%,
      rgba(@primary-rgb, 0.1) 100%
    );
    margin: 4px 0;
  }

  .timeline-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
    font-size: 13px;

    .dot {
      width: 10px;
      height: 10px;
      border-radius: 50%;
      background: @border;
      border: 2px solid @card-bg;
    }

    .content {
      color: @muted;
    }

    &.active {
      .dot {
        background: @primary;
        box-shadow: 0 0 12px rgba(@primary-rgb, 0.5);
      }
      .content {
        color: @text;
        font-weight: 600;
      }
    }

    &.future {
      opacity: 0.6;
    }
  }
}

/* ... Existing Chart & Card Styles ... */
.rhythm-panel {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid @border;
  border-radius: @radius;
  padding: 24px;
  backdrop-filter: blur(10px);

  .panel-header {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-bottom: 24px;

    .block-title {
      margin-bottom: 0;
    }
    .panel-subtitle {
      font-size: 12px;
      color: @muted;
      font-family: var(--font-mono);
      text-transform: uppercase;
      opacity: 0.7;
    }
  }

  .stacked-chart-container {
    .chart-legend {
      display: flex;
      flex-wrap: wrap;
      gap: 16px;
      margin-bottom: 16px;

      .legend-item {
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 12px;
        color: @muted;

        .legend-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
        }
      }
    }

    .chart-wrapper {
      position: relative;
      margin-bottom: 24px;

      .stacked-chart {
        width: 100%;
        height: 150px;
        overflow: visible;

        .stack-layer {
          transition: all 0.3s;
          &:hover {
            opacity: 0.9;
          }
        }
      }

      .time-axis {
        display: flex;
        justify-content: space-between;
        margin-top: 8px;
        font-size: 12px;
        color: @muted;
        font-family: var(--font-mono);
        position: relative;

        .current {
          position: absolute;
          transform: translateX(-50%);
          color: #fff;
          font-weight: bold;
        }
      }
    }

    .dimension-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 16px;

      .dimension-card {
        background: rgba(255, 255, 255, 0.03);
        border-radius: 8px;
        padding: 12px;

        .dim-header {
          display: flex;
          justify-content: space-between;
          margin-bottom: 8px;
          font-size: 13px;
          font-weight: 500;
        }

        .dim-bar-bg {
          height: 4px;
          background: rgba(255, 255, 255, 0.1);
          border-radius: 2px;
          overflow: hidden;

          .dim-bar-fill {
            height: 100%;
            border-radius: 2px;
          }
        }
      }
    }
  }
}

.content-card {
  background: @card-bg;
  border: 1px solid @border;
  border-radius: @radius;
  padding: 24px;
  transition: all 0.3s;
  backdrop-filter: blur(10px);

  &:hover {
    border-color: rgba(@primary-rgb, 0.3);
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
  }
}

.card-text {
  font-weight: 500;
  color: @text;
  margin-bottom: 16px;

  .highlight {
    color: @primary;
  }
}

.card-desc {
  font-size: 14px;
  color: @muted;
  line-height: 1.6;
  margin-bottom: 16px;
}

.card-list {
  font-size: 14px;
  color: @muted;
  list-style: none;
  padding: 0;
  margin: 0;

  li {
    margin-bottom: 8px;
    &:last-child {
      margin-bottom: 0;
    }
  }
}

.impact-grid {
  display: grid;
  gap: 16px;

  .impact-item {
    .impact-title {
      font-size: 14px;
      font-weight: 600;
      margin-bottom: 4px;

      &.positive {
        color: var(--color-data-pos);
      }
      &.negative {
        color: var(--color-red);
      }
    }

    .impact-desc {
      font-size: 14px;
      color: @muted;
    }
  }
}

.aspect-title {
  font-weight: 600;
  color: @text;
  margin-bottom: 4px;
}

.aspect-meta {
  font-size: 12px;
  color: @muted;
  margin-bottom: 8px;
  font-family: var(--font-mono);
}

.aspect-desc {
  font-size: 14px;
  color: @muted;
}

.cta-section {
  background: linear-gradient(
    135deg,
    rgba(@primary-rgb, 0.05) 0%,
    rgba(@primary-rgb, 0.02) 100%
  );
  border: 1px solid rgba(@primary-rgb, 0.2);
  border-radius: 24px;
  padding: 32px;
  text-align: center;
  /* margin-top: 48px;  Removed to allow sticky positioning control */

  .cta-title {
    font-size: 24px;
    font-weight: 700;
    color: @text;
    margin-bottom: 16px;
  }

  .cta-desc {
    font-size: 14px;
    color: @muted;
    margin-bottom: 24px;

    .highlight {
      color: @primary;
      font-weight: 600;
    }
  }

  .cta-btn {
    background: @primary;
    color: #000;
    font-family: var(--font-sans);
    font-weight: 600;
    font-size: 16px;
    padding: 12px 32px;
    border: none;
    border-radius: 999px;
    cursor: pointer;
    transition: all 0.3s;
    box-shadow: 0 4px 16px rgba(@primary-rgb, 0.3);

    &:hover {
      transform: translateY(-2px);
      box-shadow: 0 8px 24px rgba(@primary-rgb, 0.4);
    }
  }

  .cta-footer {
    font-size: 12px;
    color: @muted;
    margin-top: 16px;
    opacity: 0.7;
  }
}

.mb-4 {
  margin-bottom: 16px;
}
.font-mono {
  font-family: var(--font-mono);
}
</style>
