"""
recognizer.py — AKG 主题识别器

ThemeRecognizer.recognize(user_question, report_data, top_k) -> list[ThemeNode]
匹配既有 seam（consultation.py:118 / consultation_engine.py:798）。

流程：关键词命中 → 证据收集 → 强度+置信度 → 排序 → top_k。
无关键词命中时按星盘强度 fallback，让星盘本身说话。
任何异常返回空 list（与 seam 的 try/except 降级一致）。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .theme_catalog import THEME_CATALOG, ThemeDef, all_themes
from .evidence import (
    EvidenceItem,
    collect_theme_evidence,
    score_theme,
    theme_confidence,
)


@dataclass
class ThemeNode:
    """识别出的主题节点。"""
    key: str
    label: str
    description: str
    evidence: list[dict] = field(default_factory=list)   # EvidenceItem.to_dict()
    strength: float = 0.0        # 0-1
    confidence: float = 0.0      # 0-1
    narrative: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "label": self.label,
            "description": self.description,
            "evidence": self.evidence,
            "strength": round(self.strength, 3),
            "confidence": round(self.confidence, 3),
            "narrative": self.narrative,
        }


class ThemeRecognizer:
    """从用户问题 + 星盘数据识别主题。"""

    def recognize(
        self,
        user_question: str,
        chart_data: dict,
        top_k: int = 3,
    ) -> list[ThemeNode]:
        """识别 top_k 主题。

        Args:
            user_question: 用户问题文本
            chart_data: report_data 字典（持久化报告）
            top_k: 返回主题数

        Returns:
            按 (关键词*0.4 + 强度*0.4 + 置信度*0.2) 排序的 ThemeNode 列表。
            无证据的主题被过滤。report_data 缺字段时返回空 list。
        """
        if not isinstance(chart_data, dict):
            return []

        question = user_question or ""
        nodes: list[ThemeNode] = []
        kw_scores: list[float] = []

        for theme in all_themes():
            evidence = collect_theme_evidence(theme, chart_data)
            if not evidence:
                continue
            kw_score = self._keyword_score(theme, question)
            kw_scores.append(kw_score)
            nodes.append(ThemeNode(
                key=theme.key,
                label=theme.label,
                description=theme.description,
                evidence=[e.to_dict() for e in evidence],
                strength=score_theme(evidence),
                confidence=theme_confidence(evidence),
            ))

        if not nodes:
            return []

        max_kw = max(kw_scores) if kw_scores else 0.0
        has_keyword = max_kw > 0

        def rank(n: ThemeNode) -> float:
            if has_keyword:
                kw = self._keyword_score(THEME_CATALOG[n.key], question) / max(max_kw, 1e-6)
                return kw * 0.4 + n.strength * 0.4 + n.confidence * 0.2
            # 无关键词命中：仅按星盘强度
            return n.strength

        nodes.sort(key=rank, reverse=True)
        return nodes[:top_k]

    @staticmethod
    def _keyword_score(theme: ThemeDef, question: str) -> float:
        if not question:
            return 0.0
        return float(sum(1 for kw in theme.keywords if kw in question))
