# 文件翻译工具

## 简介
这是一个基于Python的文件翻译工具，支持Excel、PowerPoint和Word文件的翻译。工具采用模块化架构，便于扩展和维护。

## 模块结构
- `file_parsers.py`: 文件解析层，负责解析不同类型的文件。
- `translation_core.py`: 翻译核心层，封装了Ollama API接口。
- `format_preserver.py`: 格式保持层，负责保存翻译后的文件并保持原有格式。
- `task_manager.py`: 任务管理层，使用Celery和Redis进行分布式任务队列管理。
- `web_interface.py`: 用户界面层，提供Web界面和命令行CLI。
- `cli_interface.py`: 命令行接口，方便用户通过命令行进行文件翻译。

## 依赖
- pandas
- python-pptx
- openpyxl
- docx
- ollama_client
- celery
- redis
- flask
- click
- pyamqp

## 安装
1. 克隆仓库到本地：
   ```bash
   git clone https://github.com/qxcjust/Translator.git
   cd Translator
   ```
2. 创建虚拟环境并激活：
   ```bash
   python -m venv venv
   source venv/bin/activate  # 在Windows上使用 `venv\Scripts\activate`
   ```
   ```bash
   # 在MAC OS上使用以下命令
   python3 -m venv venv
   source venv/bin/activate
   ```
3. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

## 使用方法

### 通过命令行翻译文件