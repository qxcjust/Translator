import logging
from redis import Redis
import sys

# 配置日志记录（支持中文）
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

def clear_redis_tasks():
    try:
        redis_client = Redis(
            host='localhost',
            port=6379,
            db=0,
            socket_connect_timeout=1,
            retry_on_timeout=True
        )
        redis_client.flushdb()
        logging.info("已清除Redis中的所有任务数据")
    except Exception as e:
        logging.error(f"清除Redis数据失败: {str(e)}")

if __name__ == "__main__":
    clear_redis_tasks() 