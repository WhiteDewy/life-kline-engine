# Developer Reference

本文件收录从 `CLAUDE.md` 拆出的开发细节,按需查阅,不强制每次加载。

## 领域权重(Classical vs Modern)

| Domain | Classical | Modern | Rationale |
|:---|:---|:---|:---|
| Personal | 40% | 60% | 自我理解偏心理 |
| Finance | 70% | 30% | 金钱客观 |
| Family | 50% | 50% | 处境与感受各半 |
| Romance | 30% | 70% | 爱是体验 |
| Marriage | 60% | 40% | 婚姻有契约重量 |
| Work Skill | 40% | 60% | 技能是个人发展 |
| Career | 60% | 40% | 事业需客观判断 |
| Education | 50% | 50% | 学习风格 + 学业潜力 |

## OHLC 评分

人生阶段按金融 K 线评分:
- **Open**: 0.6 × dignity + 0.4 × house_power
- **High**: support_resources + benefic aspects + positive dignity
- **Low**: load_pressure + malefic aspects + negative dignity
- **Close**: theme_coherence + reception + net support

## 分析类型系统

注册于 `analysis_catalog.py`。Active: `natal_blueprint`, `phase_navigation`, `monthly_lunar_return`。Paused(时间系统重设计中): `annual_profection`, `secondary_progression`, `synastry`。

## 地理编码

Provider 链: AMap(若设 key)→ Nominatim global → Nominatim CN → maps.co。AMap 的 GCJ-02 坐标会转回 WGS84。

## Agent Memory 文件格式

```markdown
---
name: <short-kebab-case-slug>
description: <one-line summary>
metadata:
  type: user | feedback | project | reference
---

<content>

**Why:** <why this matters>
**How to apply:** <how to use this fact>
```

`MEMORY.md` 索引格式:`- [Title](file.md) — hook`

Memory 类型:
- `user` — 用户角色、专业度、偏好
- `feedback` — 用户对工作的反馈
- `project` — 进行中的工作、目标、约束
- `reference` — 外部资源、文档链接
