from file_parsers import parse_excel, parse_powerpoint
from format_preserver import save_translated_excel, save_translated_powerpoint
from translation_core import TranslationCore

class FileTranslator:
    def __init__(self, ollama_api_key):
        self.translation_core = TranslationCore(api_key=ollama_api_key)

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

    def translate_file(self, file_path, output_path, source_lang, target_lang):
        if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
            self.translate_excel(file_path, output_path, source_lang, target_lang)
        elif file_path.endswith('.pptx'):
            self.translate_powerpoint(file_path, output_path, source_lang, target_lang)
        else:
            raise ValueError("Unsupported file type")