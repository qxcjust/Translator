import logging
from file_parsers import parse_powerpoint
from format_preserver import save_translated_powerpoint
from translation_core import TranslationCore
from pptx import Presentation
from pptx.util import Pt
import traceback

# 配置日志记录
logging.basicConfig(level=logging.INFO)

def translate_powerpoint(translation_core, file_path, output_path, source_lang, target_lang, task):
    logging.info(f"Starting translation of PowerPoint file: {file_path}")
    try:
        prs = Presentation(file_path)
        total_slides = len(prs.slides)
        for i, slide in enumerate(prs.slides):
            for shape in slide.shapes:
                # 处理文本框
                if shape.has_text_frame:
                    for paragraph in shape.text_frame.paragraphs:
                        if len(paragraph.runs) > 0:
                            for run in paragraph.runs:
                                if run.text.strip():
                                    logging.info(f"Run text: {run.text} Source Lang: {source_lang} Target Lang: {target_lang}")
                                    run.text = translation_core.translate_text(run.text, source_lang, target_lang)
                        else:
                            if paragraph.text.strip():
                                logging.info(f"Paragraph text: {paragraph.text} Source Lang: {source_lang} Target Lang: {target_lang}")
                                paragraph.text = translation_core.translate_text(paragraph.text, source_lang, target_lang)
                
                # 处理图形中的文本
                elif hasattr(shape, "text"):
                    if shape.text.strip():
                        logging.info(f"Shape text: {shape.text} Source Lang: {source_lang} Target Lang: {target_lang}")
                        shape.text = translation_core.translate_text(shape.text, source_lang, target_lang)
                
                # 处理表格
                elif shape.has_table:
                    for row in shape.table.rows:
                        for cell in row.cells:
                            if cell.text.strip():
                                logging.info(f"Table cell text: {cell.text} Source Lang: {source_lang} Target Lang: {target_lang}")
                                cell.text = translation_core.translate_text(cell.text, source_lang, target_lang)
            if task is not None:
                task.update_state(state='PROGRESS', meta={'current': i + 1, 'total': total_slides, 'progress': ((i + 1) / total_slides) * 100.0})
        
        save_translated_powerpoint(prs, output_path)
        logging.info(f"Completed translation of PowerPoint file: {file_path}")
    
    except Exception as e:
        logging.error(f"Error during translation for file {file_path}: {e}")
        logging.error(traceback.format_exc())
        if task is not None:
            task.update_state(state='FAILURE', meta={'exc_type': type(e).__name__, 'exc_message': str(e), 'traceback': traceback.format_exc()})
        raise