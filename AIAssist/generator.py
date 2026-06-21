"""分段翻译生成器：用已有 `TranslationCore` 执行带上下文和术语约束的翻译。"""
from typing import List, Dict, Optional
import logging

from translation_core import TranslationCore

logger = logging.getLogger(__name__)


class SegmentTranslator:
    def __init__(self, model_name=None, endpoint_url=None, temperature=0.3):
        # Only pass values that are explicitly provided so TranslationCore can use its defaults
        kwargs = {"temperature": temperature}
        if model_name is not None:
            kwargs["model_name"] = model_name
        if endpoint_url is not None:
            kwargs["endpoint_url"] = endpoint_url

        self.core = TranslationCore(**kwargs)

    def _build_prompt(self, text: str, prev_translations: List[str], glossary: Optional[Dict[str, str]] = None):
        parts = []
        if glossary:
            terms = "\n".join([f"{k} => {v}" for k, v in glossary.items()])
            parts.append(f"Glossary (force use):\n{terms}\n")
        if prev_translations:
            ctx = "\n".join(prev_translations[-3:])
            parts.append(f"Context (previous translations):\n{ctx}\n")
        parts.append(f"Translate this text preserving glossary and formatting:\n{text}")
        return "\n\n".join(parts)

    def translate_segment(self, segment: Dict, source_lang: str, target_lang: str, prev_translations: Optional[List[str]] = None, glossary: Optional[Dict[str, str]] = None):
        prev_translations = prev_translations or []
        prompt = self._build_prompt(segment.get("text", ""), prev_translations, glossary)
        # Use core.initial_translation_with_lang to keep consistent behavior
        result = self.core.initial_translation_with_lang(prompt, source_lang, target_lang)
        logger.debug(f"Translated segment {segment.get('id')} -> {result}")
        return result
