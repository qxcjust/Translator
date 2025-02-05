import logging
from file_parsers import parse_powerpoint
from format_preserver import save_translated_powerpoint
from translation_core import TranslationCore
from pptx import Presentation  # 添加导入
from pptx.util import Pt  # 添加导入

# 配置日志记录
logging.basicConfig(level=logging.INFO)

def translate_powerpoint(translation_core, file_path, output_path, source_lang, target_lang, task):
    logging.info(f"Starting translation of PowerPoint file: {file_path}")
    prs = Presentation(file_path)
    total_slides = len(prs.slides)
    for i, slide in enumerate(prs.slides):
        for shape in slide.shapes:
            if hasattr(shape, "text"):
                if shape.has_text_frame:
                    for paragraph in shape.text_frame.paragraphs:
                        for run in paragraph.runs:
                            logging.info(f"Text: {run.text} Source Lang: {source_lang} Target Lang: {target_lang}")
                            run.text = translation_core.translate_text(run.text, source_lang, target_lang)
        task.update_state(state='PROGRESS', meta={'current': i + 1, 'total': total_slides, 'progress': ((i + 1) / total_slides) * 100.0})
    save_translated_powerpoint(prs, output_path)
    logging.info(f"Completed translation of PowerPoint file: {file_path}")