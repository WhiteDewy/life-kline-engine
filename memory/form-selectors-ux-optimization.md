---
name: form-selectors-ux-optimization
description: 地点选择器 + 日期时间选择器 UI/UX 优化方案（16项建议，含 P0-P3 优先级）
metadata:
  type: project
---

# 表单选择器 UX 优化方案

**涉及页面：** Profile、Onboarding、Analysis
**审查日期：** 2026-07-23

---

## P0 - 必须修复（6 项）

1. **统一 popper 毛玻璃效果** — Profile 和 Analysis 的 date/time picker 无 popper-class，回退到深色默认背景。需统一设为 `heal-popper`
2. **下拉面板圆角统一 18px** — `.el-cascader-panel` 和 `.el-picker-panel` 内层圆角 4px，与外层 18px 不匹配
3. **触摸目标 ≥ 44px** — `.el-cascader-node` 高度 34px，`.el-date-table td` 高度 38px，均低于移动端标准
4. **节点文字色改为温暖色** — cascader 节点文字 `rgb(148,163,184)` slate-400 冷色调 → `#4a3728`
5. **补充选中态 hover/active 样式** — `.el-cascader-node.is-active` 无背景色反馈
6. **三页面统一 popper-class** — cascader 用 `heal-cascader-popper`，picker 用 `heal-popper`

## P1 - 重要改进（4 项）

7. 统一 placeholder 文案为"选择省 / 市 / 区"
8. 统一手动坐标入口为 inline `<details>` 折叠模式
9. 自定义 cascader 下拉滚动条
10. 优化"获取坐标"按钮布局（`flex-shrink: 0`）

## P2 - 体验提升（3 项）

11. cascader 设置 `expandTrigger: 'click'` 减少多列同时展开
12. 评估分步选择器替代 cascader
13. Profile date/time picker 增加 `popper-class="heal-popper"`

## P3 - 锦上添花（3 项）

14. 选择完省/市/区后自动触发坐标获取
15. 农历日期视觉位置优化
16. 选中日期配色微调 → `rgba(240, 170, 140, 0.6)`

---

## 关键 CSS 变量

```css
--glass-mask: rgba(255,255,255,0.85);
--border-light: rgba(0,0,0,0.06);
--text-primary: #4a3728;
--text-secondary: #8b7355;
--text-tertiary: #b8a090;
--accent-warm: rgba(240, 170, 140, 0.15);
--shadow-card: 0 8px 32px rgba(0,0,0,0.06);
```

**Why:** 当前 Element Plus 默认样式（冷色调、小触点、深浅不一致）与项目治愈系设计语言严重冲突，用户反馈"太丑了"。
**How to apply:** 集中在 `theme.css` 添加覆盖规则，三页面统一 popper-class。按 P0→P1→P2 顺序实施。
