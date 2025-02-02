from flask import Flask, request, jsonify
from task_manager import translate_file

app = Flask(__name__)

@app.route('/translate', methods=['POST'])
def translate():
    data = request.json
    file_path = data['file_path']
    output_path = data['output_path']
    source_lang = data['source_lang']
    target_lang = data['target_lang']
    translate_file.delay(file_path, output_path, source_lang, target_lang)
    return jsonify({"status": "Translation started"}), 202

if __name__ == "__main__":
    app.run(debug=True)