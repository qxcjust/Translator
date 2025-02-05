import logging
from file_parsers import parse_excel, parse_powerpoint, parse_word
from format_preserver import save_translated_excel, save_translated_powerpoint, save_translated_word
from translation_core import TranslationCore
from celery import shared_task

# 配置日志记录
logging.basicConfig(level=logging.INFO)

class FileTranslator:
    def __init__(self):
        self.translation_core = TranslationCore(endpoint_url="http://192.168.146.137:11434/v1")

    def translate_excel(self, file_path, output_path, source_lang, target_lang, task):
        logging.info(f"Starting translation of Excel file: {file_path}")
        df = parse_excel(file_path)
        total_rows = len(df)
        translated_df = df.applymap(lambda x: self.translation_core.translate_text(x, source_lang, target_lang) if isinstance(x, str) else x)
        save_translated_excel(translated_df, output_path)
        logging.info(f"Completed translation of Excel file: {file_path}")
        task.update_state(state='PROGRESS', meta={'current': total_rows, 'total': total_rows, 'progress': 100.0})

    def translate_powerpoint(self, file_path, output_path, source_lang, target_lang, task):
        logging.info(f"Starting translation of PowerPoint file: {file_path}")
        prs = parse_powerpoint(file_path)
        total_slides = len(prs.slides)
        for i, slide in enumerate(prs.slides):
            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    logging.info(f"Text: {shape.text} Source Lang: {source_lang} Target Lang: {target_lang}")
                    shape.text = self.translation_core.translate_text(shape.text, source_lang, target_lang)
            task.update_state(state='PROGRESS', meta={'current': i + 1, 'total': total_slides, 'progress': ((i + 1) / total_slides) * 100.0})
        save_translated_powerpoint(prs, output_path)
        logging.info(f"Completed translation of PowerPoint file: {file_path}")

    def translate_word(self, file_path, output_path, source_lang, target_lang, task):
        logging.info(f"Starting translation of Word file: {file_path}")
        doc = parse_word(file_path)
        total_paragraphs = len(doc.paragraphs)
        for i, paragraph in enumerate(doc.paragraphs):
            paragraph.text = self.translation_core.translate_text(paragraph.text, source_lang, target_lang)
            task.update_state(state='PROGRESS', meta={'current': i + 1, 'total': total_paragraphs, 'progress': ((i + 1) / total_paragraphs) * 100.0})
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    cell.text = self.translation_core.translate_text(cell.text, source_lang, target_lang)
        save_translated_word(doc, output_path)
        logging.info(f"Completed translation of Word file: {file_path}")

    def translate_file(self, file_path, output_path, source_lang, target_lang, task):
        logging.info(f"Starting translation of file: {file_path}")
        if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
            self.translate_excel(file_path, output_path, source_lang, target_lang, task)
        elif file_path.endswith('.pptx') or file_path.endswith('.ppt'):
            self.translate_powerpoint(file_path, output_path, source_lang, target_lang, task)
        elif file_path.endswith('.docx'):
            self.translate_word(file_path, output_path, source_lang, target_lang, task)
        else:
            raise ValueError("Unsupported file type")
        logging.info(f"Completed translation of file: {file_path}")