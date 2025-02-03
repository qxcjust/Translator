from flask import Flask, request, jsonify, render_template
from task_manager import translate_file
import os
from datetime import datetime

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
    data = request.json
    file_path = data['file_path']
    output_path = data['output_path']
    source_lang = data['source_lang']
    target_lang = data['target_lang']
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
        # 获取当前日期并创建子文件夹
        upload_date = datetime.now().strftime('%Y-%m-%d')
        date_folder = os.path.join(app.config['UPLOAD_FOLDER'], upload_date)
        os.makedirs(date_folder, exist_ok=True)
        
        file_path = os.path.join(date_folder, file.filename)
        file.save(file_path)
        return jsonify({"message": "File successfully uploaded", "file_path": file_path}), 200

if __name__ == "__main__":
    app.run(debug=True)