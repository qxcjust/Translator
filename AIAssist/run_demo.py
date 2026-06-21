"""示例流水线：解析->记忆->分段翻译->质量检查->合并输出（保存为简单txt）。"""
from AIAssist import parse_document, MemoryStore, SegmentTranslator, QualityChecker
import sys
import logging

logging.basicConfig(level=logging.INFO)


def run(path, src='Chinese', tgt='English'):
    segments = parse_document(path)
    mem = MemoryStore()
    mem.add_segments(segments)

    translator = SegmentTranslator()
    qc = QualityChecker()

    output_segments = []
    prev = []
    glossary = {}  # 可填入固定术语映射

    for seg in mem.all():
        # 在检索中加入上下文（简单示例）
        retrieved = mem.retrieve(seg['text'], top_k=2)
        ctx_texts = [r['text'] for r in retrieved if r['id'] != seg['id']]
        translated = translator.translate_segment(seg, src, tgt, prev_translations=ctx_texts, glossary=glossary)
        score = qc.score(seg['text'], translated)
        output_segments.append({'id': seg['id'], 'source': seg['text'], 'translation': translated, 'score': score})
        prev.append(translated)

    out_path = path + f".translated.{tgt}.txt"
    with open(out_path, 'w', encoding='utf-8') as f:
        for o in output_segments:
            f.write(o['translation'] + '\n\n')

    logging.info(f"Saved combined translation to {out_path}")
    return out_path


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python run_demo.py <file_path> [src_lang] [tgt_lang]')
        sys.exit(1)
    path = sys.argv[1]
    src = sys.argv[2] if len(sys.argv) > 2 else 'Chinese'
    tgt = sys.argv[3] if len(sys.argv) > 3 else 'English'
    run(path, src, tgt)
