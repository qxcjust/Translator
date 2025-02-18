from flask import Flask, request, jsonify, render_template, send_from_directory
from task_manager import translate_file, translate_texts, app as celery
import os
from datetime import datetime
from celery import Celery
import logging
import time
from file_parsers import get_file_pages, get_file_size
from celery.result import AsyncResult
from gl_config import REDIS_DB, REDIS_HOST, REDIS_PORT, MIME_TO_EXTENSION,LOG_LEVEL

# 配置日志记录
logging.basicConfig(level=LOG_LEVEL)

app = Flask(__name__)

# 设置上传文件夹
UPLOAD_FOLDER = 'Updatefile'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Celery配置
app.config['CELERY_BROKER_URL'] = f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}'
app.config['CELERY_RESULT_BACKEND'] = f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}'

# 修改 Celery 初始化配置
celery = Celery(app.name, 
                broker=app.config['CELERY_BROKER_URL'],
                backend=app.config['CELERY_RESULT_BACKEND'])

@app.route('/')
def home():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    logging.info("Handling file upload request")
    if 'file' not in request.files:
        logging.error("No file part in the request")
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        logging.error("No file selected")
        return jsonify({"error": "No selected file"}), 400
    if file:
        # 获取文件扩展名
        file_extension = os.path.splitext(file.filename)[1].lower()
        # 定义允许的文件类型
        allowed_extensions = {'.docx', '.ppt', '.pptx', '.xls', '.xlsx'}
        if file_extension not in allowed_extensions:
            logging.error(f"Invalid file type: {file_extension}")
            return jsonify({"error": "Invalid file type. Allowed types: DOCX, PPT, PPTX, XLS, XLSX"}), 400
        
        # 获取当前日期并创建子文件夹
        upload_date = datetime.now().strftime('%Y-%m-%d')
        date_folder = os.path.join(app.config['UPLOAD_FOLDER'], upload_date)
        os.makedirs(date_folder, exist_ok=True)
        
        file_path = os.path.join(date_folder, file.filename)
        file.save(file_path)
        
        # 获取文件大小
        file_size = get_file_size(file_path)
        page_size = get_file_pages(file_path)
        
        # 获取文件MIME类型
        file_mime_type = file.content_type
        
        # 转换MIME类型到缩写形式
        file_type = MIME_TO_EXTENSION.get(file_mime_type, file_extension)
        
        logging.info(f"File uploaded successfully: {file_path}")
        return jsonify({
            "message": "File successfully uploaded",
            "file_path": file_path,
            "file_name": file.filename,
            "file_type": file_type,
            "file_size": file_size,
            "file_pages": page_size
        }), 200

# 假设有一个全局字典来存储任务状态
translate_task_status = {}

@app.route('/translate', methods=['POST'])
def translate():
    data = request.form  # 修改为 request.form 以接收 FormData 数据
    file_path = data.get('file_path')
    source_lang = data['source_lang']
    target_lang = data['target_lang']
    
    # 翻译后目标文件路径translateFiles下，以日期为子文件夹，子文件夹中放置翻译后文件，文件名后缀为filename_target_lang.
    base_output_folder = 'translateFiles'
    os.makedirs(base_output_folder, exist_ok=True)
    upload_date = datetime.now().strftime('%Y-%m-%d')
    date_folder = os.path.join(base_output_folder, upload_date)
    os.makedirs(date_folder, exist_ok=True)
    
    file_name, file_extension = os.path.splitext(os.path.basename(file_path))
    output_file_name = f"{file_name}_{target_lang}{file_extension}"
    output_path = os.path.join(date_folder, output_file_name)
    
    # 保存文件信息到会话或数据库中（这里仅打印）
    logging.info(f"File Path: {file_path}")
    logging.info(f"Output Path: {output_path}")
    logging.info(f"Source Language: {source_lang}")
    logging.info(f"Target Language: {target_lang}")

    try:
        # 启动异步任务
        task = translate_file.apply_async(
            args=(file_path, output_path, source_lang, target_lang),
            kwargs={}
        )
        
        # 返回翻译任务信息
        translation_info = {
            'file_name': os.path.basename(file_path),
            'file_pages': get_file_pages(file_path),
            'file_size': get_file_size(file_path),
            'source_lang': source_lang,
            'target_lang': target_lang,
            'status': '0%',
            'start_time': time.strftime('%Y-%m-%d %H:%M:%S'),
            'translated_file_path': None  # 翻译完成后更新此路径
        }     
        # 保存任务ID以便后续查询状态
        task_id = task.id
        logging.info(f"task id:{task_id}")
        translate_task_status[task_id] = translation_info
        return jsonify({'task_id': task_id, 'translation_info': translation_info, 'status': 'Translation started'})
    except Exception as e:
        logging.error(f"Error starting translation: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/task_status/<task_id>', methods=['GET'])
def task_status(task_id):
    try:
        task = AsyncResult(task_id, app=celery)
        # 基础响应结构
        response = {
            'state': task.state,
            'progress': 0.0,
            'current': 0,
            'total': 1,
            'translated_file_path': None,
            'error': None
        }

        if task.state == 'PROGRESS':
            meta = task.info
            response.update({
                'progress': float(f"{meta.get('progress', 0.0):.1f}"),  # 格式化为小数点后1位
                'current': meta.get('current', 0),
                'total': meta.get('total', 1)
            })
        elif task.state == 'SUCCESS':
            # 处理成功完成的任务
            meta = task.info
            response.update({
                'progress': 100.0,
                'current': meta.get('current', 1),
                'total': meta.get('total', 1),
                'translated_file_path': meta.get('translated_file_path')
            })
        elif task.state == 'FAILURE':
            # 处理失败任务
            response.update({
                'error': str(task.result),
                'progress': 100.0  # 标记为完全结束
            })
        print(response)
        return jsonify(response)
    
    except Exception as e:
        logging.error(f"查询任务状态失败: {str(e)}")
        return jsonify({'error': '内部服务器错误'}), 500

@app.route('/download', methods=['GET'])
def download():
    file_path = request.args.get('file_path')
    if not file_path or file_path == 'null':
        logging.error("No file path provided or file path is null")
        return jsonify({"error": "No file path provided or file path is invalid"}), 400
    
    # 检查文件是否存在
    if not os.path.exists(file_path):
        logging.error(f"File not found: {file_path}")
        return jsonify({"error": "File not found"}), 404
    
    # 提取文件名
    file_name = os.path.basename(file_path)
    
    # 发送文件
    return send_from_directory(os.path.dirname(file_path), file_name, as_attachment=True)

    
# text文字翻译接口
@app.route('/translate_text', methods=['POST'])
def translate_text():
    data = request.get_json()
    source_text = data.get('text')
    source_lang = data.get('source_lang')
    target_lang = data.get('target_lang')
    if not source_text or not source_lang or not target_lang:
        return jsonify({"error": "Missing required parameters"}), 400
    try:
        task = translate_texts.apply_async(
                args=(source_text, source_lang, target_lang),
                kwargs={}
            )
        return jsonify({"task_id": task.id}), 202  # Return the task ID
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# 获取翻译结果的接口
@app.route('/translation_text/<task_id>', methods=['GET'])
def translation_text(task_id):
    task = AsyncResult(task_id, app=celery)
    # 基础响应结构
    response = {
        'state': task.state,
        'status': None,
        'result': None
    }
    if task.state == 'PENDING':
        response = {
            'state': task.state,
            'status': 'pending...'
        }
    elif task.state == 'SUCCESS':
        meta = task.info
        response = {
            'state': task.state,
            'result': meta.get('translate_result')
        }
    elif task.state == 'FAILURE':
        response = {
            'state': task.state,
            'result': 'Translation failed'
        }
    else:
        response = {
            'state': task.state,
            'status': 'processing...'
        }
    return jsonify(response)    

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True) #自动使用电脑IP
    #app.run(debug=True) #使用172.0.0.01