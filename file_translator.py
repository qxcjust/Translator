import logging
from file_parsers import parse_excel, parse_powerpoint, parse_word
from format_preserver import save_translated_excel, save_translated_powerpoint, save_translated_word
from translation_core import TranslationCore

# 配置日志记录
logging.basicConfig(level=logging.INFO)

class FileTranslator:
    def __init__(self):
        self.translation_core = TranslationCore(endpoint_url="http://192.168.146.137:11434/v1")

    def translate_excel(self, file_path, output_path, source_lang, target_lang):
        logging.info(f"Starting translation of Excel file: {file_path}")
        df = parse_excel(file_path)
        translated_df = df.applymap(lambda x: self.translation_core.translate_text(x, source_lang, target_lang) if isinstance(x, str) else x)
        save_translated_excel(translated_df, output_path)
        logging.info(f"Completed translation of Excel file: {file_path}")

    def translate_powerpoint(self, file_path, output_path, source_lang, target_lang):
        logging.info(f"Starting translation of PowerPoint file: {file_path}")
        prs = parse_powerpoint(file_path)
        for slide in prs.slides:
            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    logging.info(f"Text: {shape.text} Source Lang: {source_lang} Target Lang: {target_lang}")
                    shape.text = self.translation_core.translate_text(shape.text, source_lang, target_lang)
        save_translated_powerpoint(prs, output_path)
        logging.info(f"Completed translation of PowerPoint file: {file_path}")

    def translate_word(self, file_path, output_path, source_lang, target_lang):
        logging.info(f"Starting translation of Word file: {file_path}")
        doc = parse_word(file_path)
        for paragraph in doc.paragraphs:
            paragraph.text = self.translation_core.translate_text(paragraph.text, source_lang, target_lang)
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    cell.text = self.translation_core.translate_text(cell.text, source_lang, target_lang)
        save_translated_word(doc, output_path)
        logging.info(f"Completed translation of Word file: {file_path}")

    def translate_file(self, file_path, output_path, source_lang, target_lang):
        logging.info(f"Starting translation of file: {file_path}")
        if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
            self.translate_excel(file_path, output_path, source_lang, target_lang)
        elif file_path.endswith('.pptx') or file_path.endswith('.ppt'):
            self.translate_powerpoint(file_path, output_path, source_lang, target_lang)
        elif file_path.endswith('.docx'):
            self.translate_word(file_path, output_path, source_lang, target_lang)
        else:
            raise ValueError("Unsupported file type")
        logging.info(f"Completed translation of file: {file_path}")