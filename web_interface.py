from flask import Flask, request, jsonify, render_template
from task_manager import translate_file
import os
from datetime import datetime
from pptx import Presentation

app = Flask(__name__)

# 设置上传文件夹
UPLOAD_FOLDER = 'Updatefile'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def home():
    return render_template('upload.html')

@app.route('/translate', methods=['POST'])
def translate():
    data = request.form  # 修改为 request.form 以接收 FormData 数据
    file_path = data.get('file_path')
    output_path = os.path.join(os.path.dirname(file_path), f"translated_{os.path.basename(file_path)}")
    source_lang = data['source_lang']
    target_lang = data['target_lang']
    
    # 保存文件信息到会话或数据库中（这里仅打印）
    print(f"File Path: {file_path}")
    print(f"Source Language: {source_lang}")
    print(f"Target Language: {target_lang}")

    translate_file.delay(file_path, output_path, source_lang, target_lang)
    return jsonify({"status": "Translation started"}), 202

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    if file:
        # 获取文件扩展名
        file_extension = os.path.splitext(file.filename)[1].lower()
        # 定义允许的文件类型
        allowed_extensions = {'.docx', '.ppt', '.pptx', '.xls', '.xlsx'}
        if file_extension not in allowed_extensions:
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
        prs = Presentation(file_path)
        file_pages = len(prs.slides)
        
        return jsonify({
            "message": "File successfully uploaded",
            "file_path": file_path,
            "file_name": file.filename,
            "file_type": file_type,
            "file_size": file_size,
            "file_pages": file_pages
        }), 200

if __name__ == "__main__":
    app.run(debug=True)