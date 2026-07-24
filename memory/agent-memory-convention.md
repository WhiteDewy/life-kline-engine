---
name: agent-memory-convention
description: subagent 必须遵循的 memory 读写规范
metadata:
  type: reference
---

# Agent Memory 管理规范

## 核心原则

每次 spawn subagent 时，agent 必须：
1. **先读** `memory/MEMORY.md` 获取索引
2. **再读** 相关 memory 文件注入上下文
3. **任务结束后** 将重要发现写入 memory

## 自动读写流程

```
Spawn Agent
    ↓
读取 memory/MEMORY.md
    ↓
读取相关 memory 文件
    ↓
执行任务
    ↓
重要发现 → 写入 memory/
    ↓
更新 memory/MEMORY.md 索引
```

## 哪些内容需要写入 memory

- ✅ 产品方向决策（如"星灵日记定位为情绪疗愈工具"）
- ✅ 技术架构变更（如"前端后端分离为独立项目"）
- ✅ 用户偏好/反馈（如"用户不喜欢模板化的日记"）
- ✅ 重要约束（如"不能硬编码特定人的数据"）
- ❌ 临时调试信息
- ❌ 显而易见的代码逻辑

## Memory 文件命名

- 使用 kebab-case：`project-architecture-2026-07.md`
- 包含日期便于追溯：`YYYY-MM` 或 `YYYY-MM-DD`

## 类型标签

| type | 用途 |
|------|------|
| `user` | 用户信息、偏好 |
| `feedback` | 用户反馈 |
| `project` | 项目状态、目标 |
| `reference` | 参考资料 |

**Why:** 确保 subagent 跨会话累积上下文，不再每次重复说明背景
**How to apply:** spawn agent 时，在 prompt 开头加入读取 memory 的指令
