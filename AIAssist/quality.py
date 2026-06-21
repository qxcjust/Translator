"""后置质量检查：使用轻量 LLM 打分或简单启发式判断。"""
import re
import logging
from typing import Dict
from translation_core import TranslationCore

logger = logging.getLogger(__name__)


class QualityChecker:
    def __init__(self):
        self.core = TranslationCore()

    def score(self, source: str, translation: str) -> float:
        """使用 LLM 简短评估当前句子的质量，返回 0.0-1.0 的置信度。
        实现：向模型请求 0-1 分数，解析返回的数字；出错时退回启发式分数。
        """
        prompt = (
            "As an automotive localization expert, please provide a confidence score between 0 and 1"
            " for the quality of the following translation. Respond with a single number only.\n\n"
            f"Source:\n{source}\n\nTranslation:\n{translation}"
        )
        try:
            resp = self.core.initial_translation_with_lang(prompt, "auto", "English")
            # Try extract float
            m = re.search(r"([01](?:\.\d+)?)", resp)
            if m:
                val = float(m.group(1))
                val = max(0.0, min(1.0, val))
                return val
        except Exception as e:
            logger.debug(f"QE model error: {e}")

        # fallback heuristic: longer translations get slightly higher score
        score = min(1.0, len(translation) / max(1, len(source)))
        return float(score)
