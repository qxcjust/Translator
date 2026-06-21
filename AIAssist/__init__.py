"""轻量级 AI Assist 原型包：文档解析、全局记忆、分段生成、后置校验。"""

from .parser import parse_document
from .memory import MemoryStore
from .generator import SegmentTranslator
from .quality import QualityChecker

__all__ = ["parse_document", "MemoryStore", "SegmentTranslator", "QualityChecker"]
