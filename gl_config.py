# 配置文件，用于管理整个工程的默认配置
import logging

# 日志配置
LOG_LEVEL = logging.INFO

# 模型配置
MODEL_NAME = "qwen2.5:14b"
ENDPOINT_URL = "http://192.168.146.137:11434/v1"
TEMPERATURE = 0.2

# Redis 配置
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0
REDIS_PASSWORD = None

# 其他配置
MAX_RETRY = 3

# 是否使用反思和改进功能
USE_REFLECTION = False

# MIME类型到缩写形式的映射
MIME_TO_EXTENSION = {
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'DOCX',
    'application/vnd.ms-powerpoint': 'PPT',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation': 'PPTX',
    'application/vnd.ms-excel': 'XLS',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'XLSX'
}