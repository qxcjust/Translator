import logging
from translation_core import TranslationCore
from ppt_translator import translate_powerpoint
from excel_translator import translate_excel
from word_translator import translate_word

logging.basicConfig(level=logging.INFO)

class FileTranslator:
    def __init__(self):
        self.translation_core = TranslationCore(endpoint_url="http://192.168.146.137:11434/v1")
    def translate_file(self, file_path, output_path, source_lang, target_lang, task):
        logging.info(f"Starting translation of file: {file_path}")
        if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
            translate_excel(self.translation_core, file_path, output_path, source_lang, target_lang, task)
            if task is not None:
                task.update_state(state='SUCCESS', meta={'translated_file_path': output_path})
        elif file_path.endswith('.pptx') or file_path.endswith('.ppt'):
            translate_powerpoint(self.translation_core, file_path, output_path, source_lang, target_lang, task)
            if task is not None:
                task.update_state(state='SUCCESS', meta={'translated_file_path': output_path})
        elif file_path.endswith('.docx'):
            translate_word(self.translation_core, file_path, output_path, source_lang, target_lang, task)
            if task is not None:
                task.update_state(state='SUCCESS', meta={'translated_file_path': output_path})
        else:
            if task is not None:
                task.update_state(state='FAILURE', meta={'error': "Unsupported file type"})
            raise ValueError(f"Unsupported file type: {file_path}")
        logging.info(f"Completed translation of file: {file_path}")