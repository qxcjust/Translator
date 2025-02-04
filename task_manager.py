from celery import Celery
from translation_core import TranslationCore

app = Celery('task_manager', broker='redis://localhost:6379/0')

@app.task
def translate_file(file_path, output_path, source_lang, target_lang):
    translator = TranslationCore(model_address="http://192.168.146.137:11434/v1")
    translator.translate_file(file_path, output_path, source_lang, target_lang)