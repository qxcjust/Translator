from flask import Flask, request, jsonify, render_template
from task_manager import translate_file
import os
from datetime import datetime
from pptx import Presentation
from celery import Celery
import logging

# 配置日志记录
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# 设置上传文件夹
UPLOAD_FOLDER = 'Updatefile'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Celery配置
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'

# 初始化Celery
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

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
        file_size = os.path.getsize(file_path)
        # 格式化文件大小，文件大小过大的话，则用MB表示
        if file_size > 1024 * 1024:
            file_size = f"{file_size / (1024 * 1024):.2f} MB"
        else:
            file_size = f"{file_size / 1024:.2f} KB"
        
        # 获取文件MIME类型
        file_mime_type = file.content_type
        
        # 定义MIME类型到缩写形式的映射
        mime_to_extension = {
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'DOCX',
            'application/vnd.ms-powerpoint': 'PPT',
            'application/vnd.openxmlformats-officedocument.presentationml.presentation': 'PPTX',
            'application/vnd.ms-excel': 'XLS',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'XLSX'
        }
        
        # 转换MIME类型到缩写形式
        file_type = mime_to_extension.get(file_mime_type, file_extension)
        
        # 计算文件页数
        file_pages = 0
        try:
            prs = Presentation(file_path)
            file_pages = len(prs.slides)
        except Exception as e:
            logging.error(f"Error reading file: {e}")
            file_pages = 0
        
        logging.info(f"File uploaded successfully: {file_path}")
        return jsonify({
            "message": "File successfully uploaded",
            "file_path": file_path,
            "file_name": file.filename,
            "file_type": file_type,
            "file_size": file_size,
            "file_pages": file_pages
        }), 200

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
        translate_file.delay(file_path, output_path, source_lang, target_lang)
        logging.info(f"Translation started for file: {file_path}")
        return jsonify({"status": "Translation started"}), 202
    except Exception as e:
        logging.error(f"Error starting translation: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)