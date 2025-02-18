from celery import Celery
from translator import Translator
import logging
import os
from redis import Redis
from redis.exceptions import ConnectionError
from gl_config import REDIS_DB, REDIS_HOST, REDIS_PORT
from gl_config import LOG_LEVEL

# 配置日志记录
logging.basicConfig(level=LOG_LEVEL)

app = Celery('task_manager', 
             broker=f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}',
             backend=f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}')

class TranslationError(Exception):
    """自定义翻译异常类"""
    pass

@app.task(bind=True)
def translate_file(self, file_path, output_path, source_lang, target_lang):
    """
    文件翻译任务
    """
    logging.info(f"Starting translation for file: {file_path}")
    translator = Translator()
    try:
        logging.info(f"Initializing translation for file: {file_path}")
        translator.translate_file(file_path, output_path, source_lang, target_lang, self)
        logging.info(f"Translation completed for file: {file_path}")
        
        return {
            'current': 1,
            'total': 1,
            'progress': 100.0,
            'translated_file_path': output_path
        }
        
    except Exception as e:
        logging.error(f"Error during translation for file {file_path}: {str(e)}")
        error = TranslationError(f"Translation failed: {str(e)}")
        self.update_state(
            state='FAILURE',
            meta={
                'exc_type': type(error).__name__,
                'exc_message': str(error),
                'error': str(error)
            }
        )
        raise error


@app.task(bind=True)
def translate_texts(self, text, source_lang, target_lang):
    try:
        translator = Translator()
        translator.translate_text(text, source_lang, target_lang, self)
    except Exception as e:
        logging.error(f"Error during translation for {text}: {str(e)}")
        error = TranslationError(f"Translation failed: {str(e)}")
        raise error
