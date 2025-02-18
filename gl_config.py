# Configuration file for managing default configurations of the entire project
import logging

#version information based on tag information
#DONOT CHANGE by manual modification
#mktag.sh will update this file
VERSION = 'v1.0.3'

# Logging configuration for the entire project
LOG_LEVEL = logging.INFO

# Model configuration
MODEL_NAME = "qwen2.5:14b"
ENDPOINT_URL = "http://192.168.146.137:11434/v1"
TEMPERATURE = 0.3
API_KEY = "my-api-key"

# Redis configuration
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0
REDIS_PASSWORD = None

# Other configurations
MAX_RETRY = 3

# Whether to use reflection and improvement functionality
USE_REFLECTION = False

# Mapping of MIME types to abbreviation forms
MIME_TO_EXTENSION = {
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'DOCX',
    'application/vnd.ms-powerpoint': 'PPT',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation': 'PPTX',
    'application/vnd.ms-excel': 'XLS',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'XLSX'
}