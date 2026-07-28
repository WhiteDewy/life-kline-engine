"""
akg — Astrology Knowledge Graph（占星知识图谱 · 主题层）

Theme 是「用户语言」与「占星知识」之间的桥梁。
ThemeRecognizer 把用户问题映射到主题，并从星盘事实中抽取带置信度的证据。

本模块点亮既有 seam：
- consultation.py:116  `from .akg import ThemeRecognizer`
- consultation_engine.py:786  `from .akg import ThemeRecognizer, build_theme_narrative`
"""
from .theme_catalog import ThemeDef, THEME_CATALOG, get_theme, all_themes
from .evidence import EvidenceItem, collect_theme_evidence, score_theme, theme_confidence
from .recognizer import ThemeNode, ThemeRecognizer
from .narrative import build_theme_narrative

__all__ = [
    "ThemeDef",
    "THEME_CATALOG",
    "get_theme",
    "all_themes",
    "EvidenceItem",
    "collect_theme_evidence",
    "score_theme",
    "theme_confidence",
    "ThemeNode",
    "ThemeRecognizer",
    "build_theme_narrative",
]
