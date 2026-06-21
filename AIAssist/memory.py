"""轻量级内存存储与检索：基于词重叠打分的简单检索器。"""
from typing import List, Dict
import re


def _tokenize(text: str):
    return re.findall(r"\w+", text.lower())


class MemoryStore:
    def __init__(self):
        self.segments: List[Dict] = []

    def add_segments(self, segments: List[Dict]):
        for seg in segments:
            seg = dict(seg)
            seg["_tokens"] = set(_tokenize(seg.get("text", "")))
            self.segments.append(seg)

    def retrieve(self, query: str, top_k: int = 3):
        qtok = set(_tokenize(query))
        scored = []
        for seg in self.segments:
            inter = len(qtok & seg.get("_tokens", set()))
            scored.append((inter, seg))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [s for score, s in scored[:top_k] if score > 0]

    def all(self):
        return list(self.segments)
