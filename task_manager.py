from celery import Celery

app = Celery('task_manager', broker='pyamqp://guest@localhost//')

@app.task
def translate_file(file_path, output_path, source_lang, target_lang):
    translator = FileTranslator(ollama_api_key="your_ollama_api_key")
    translator.translate_file(file_path, output_path, source_lang, target_lang)