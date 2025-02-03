from file_parsers import parse_excel, parse_powerpoint, parse_word
from format_preserver import save_translated_excel, save_translated_powerpoint, save_translated_word
from translation_core import TranslationCore

class FileTranslator:
    def __init__(self, model_address):
        self.translation_core = TranslationCore(model_address=model_address)

    def translate_excel(self, file_path, output_path, source_lang, target_lang):
        df = parse_excel(file_path)
        translated_df = df.applymap(lambda x: self.translation_core.translate_text(x, source_lang, target_lang) if isinstance(x, str) else x)
        save_translated_excel(translated_df, output_path)

    def translate_powerpoint(self, file_path, output_path, source_lang, target_lang):
        prs = parse_powerpoint(file_path)
        for slide in prs.slides:
            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    shape.text = self.translation_core.translate_text(shape.text, source_lang, target_lang)
        save_translated_powerpoint(prs, output_path)

    def translate_word(self, file_path, output_path, source_lang, target_lang):
        doc = parse_word(file_path)
        for paragraph in doc.paragraphs:
            paragraph.text = self.translation_core.translate_text(paragraph.text, source_lang, target_lang)
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    cell.text = self.translation_core.translate_text(cell.text, source_lang, target_lang)
        save_translated_word(doc, output_path)

    def translate_file(self, file_path, output_path, source_lang, target_lang):
        if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
            self.translate_excel(file_path, output_path, source_lang, target_lang)
        elif file_path.endswith('.pptx') or file_path.endswith('.ppt'):
            self.translate_powerpoint(file_path, output_path, source_lang, target_lang)
        elif file_path.endswith('.docx'):
            self.translate_word(file_path, output_path, source_lang, target_lang)
        else:
            raise ValueError("Unsupported file type")