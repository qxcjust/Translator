from celery import Celery
from file_translator import FileTranslator
import logging
import os
from redis import Redis, ConnectionPool
from redis.exceptions import ConnectionError
import time

# 配置日志记录
logging.basicConfig(level=logging.INFO)

# Redis连接配置
REDIS_HOST = '127.0.0.1'  # 明确使用IP而不是hostname
REDIS_PORT = 6379
REDIS_DB = 0
REDIS_URL = f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}'

# 创建Redis连接池
REDIS_POOL = ConnectionPool(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    decode_responses=True,
    socket_timeout=30,
    socket_connect_timeout=30,
    socket_keepalive=True,
    retry_on_timeout=True
)

def wait_for_redis(max_retries=5, retry_delay=2):
    """等待Redis服务可用"""
    for attempt in range(max_retries):
        try:
            client = Redis(connection_pool=REDIS_POOL)
            client.ping()
            logging.info("Redis连接成功")
            return True
        except Exception as e:
            if attempt < max_retries - 1:
                logging.warning(f"Redis连接失败，{retry_delay}秒后重试... ({attempt + 1}/{max_retries})")
                time.sleep(retry_delay)
            else:
                logging.error(f"Redis连接失败: {str(e)}")
                return False

# Windows平台特定设置
os.environ.setdefault('FORKED_BY_MULTIPROCESSING', '1')

# 等待Redis可用
if not wait_for_redis():
    raise RuntimeError("无法连接到Redis服务")

# Celery配置
app = Celery('task_manager',
             broker=REDIS_URL,
             backend=REDIS_URL)

# 更新Celery配置
app.conf.update(
    broker_connection_retry=True,
    broker_connection_retry_on_startup=True,
    broker_connection_max_retries=5,
    broker_connection_timeout=30,
    worker_pool='solo',
    worker_prefetch_multiplier=1,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    result_expires=3600,
    task_ignore_result=False,
    broker_transport_options={
        'visibility_timeout': 3600,
        'socket_timeout': 30,
        'socket_connect_timeout': 30,
        'retry_on_timeout': True
    }
)

class TranslationError(Exception):
    """自定义翻译异常类"""
    pass

@app.task(bind=True)
def translate_file(self, file_path, output_path, source_lang, target_lang):
    """
    文件翻译任务
    """
    logging.info(f"Starting translation for file: {file_path}")
    file_translator = FileTranslator()
    try:
        logging.info(f"Initializing translation for file: {file_path}")
        file_translator.translate_file(file_path, output_path, source_lang, target_lang, self)
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