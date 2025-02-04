from celery import Celery
from file_translator import FileTranslator
import logging

# 配置日志记录
logging.basicConfig(level=logging.INFO)

app = Celery('task_manager', broker='redis://localhost:6379/0')

@app.task(bind=True)
def translate_file(self, file_path, output_path, source_lang, target_lang):
    logging.info(f"Starting translation for file: {file_path}")
    file_translator = FileTranslator()
    try:
        logging.info(f"Initializing translation for file: {file_path}")
        file_translator.translate_file(file_path, output_path, source_lang, target_lang, self)
        logging.info(f"Translation completed for file: {file_path}")
    except Exception as e:
        logging.error(f"Error during translation for file {file_path}: {e}")
        self.update_state(state='FAILURE', meta={'error': str(e)})