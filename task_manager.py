from celery import Celery
from file_translator import FileTranslator
import logging

# 配置日志记录
logging.basicConfig(level=logging.INFO)

app = Celery('task_manager', broker='redis://localhost:6379/0')

@app.task
def translate_file(file_path, output_path, source_lang, target_lang):
    logging.info(f"Starting translation for file: {file_path}")
    # 假设 TranslationCore 的初始化方法接受 model_url 作为参数
    file_translator = FileTranslator()
    try:
        logging.info(f"Initializing translation for file: {file_path}")
        file_translator.translate_file(file_path, output_path, source_lang, target_lang)
        logging.info(f"Translation completed for file: {file_path}")
    except Exception as e:
        logging.error(f"Error during translation for file {file_path}: {e}")