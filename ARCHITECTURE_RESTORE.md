# 项目架构与已恢复运行步骤

此文件记录在本仓库中已成功恢复并能运行的最小架构、依赖与启动流程，便于复现环境或问题排查。

## 架构概览

- 翻译入口：`translator.py`（调度文件类型并调用 `TranslationCore`）
- 翻译核心：`translation_core.py`（封装与 LLM 的交互，当前使用 `langchain_openai.ChatOpenAI`）
- 配置中心：`gl_config.py`（模型名称、ENDPOINT_URL、TEMPERATURE、API_KEY 等）
- 文件处理：`file_parsers.py`, `excel_translator.py`, `ppt_translator.py`, `word_translator.py`
- 任务队列（可选）：`task_manager.py`（Celery + Redis 用于异步任务）
- Web 界面（可选）：`web_interface.py`

## 已恢复的最小运行依赖

为避免在 Windows 上从源码编译大型科学包（如 `numpy`）导致构建失败，创建了最小依赖清单：`requirements-min.txt`，包含：

- Flask
- redis
- celery
- langchain
- langchain-openai
- requests
- python-docx
- python-pptx
- openpyxl
- tqdm
- python-dotenv

该清单已添加到仓库：`requirements-min.txt`。

## 本地模型配置（已生效）

在 `gl_config.py` 中默认配置为本地 Ollama 服务：

- MODEL_NAME: `translatgemma:4b`
- ENDPOINT_URL: `http://127.0.0.1:11434/v1`
- API_KEY: `None`（本地 Ollama 默认为无密钥）

请确保 Ollama 服务已启动并加载模型 `translatgemma:4b`。

## 在 Windows 上快速启动（使用最小依赖）

1. 在项目目录创建并激活虚拟环境（假设已在 `venv` 中）：

```powershell
# 如果尚未创建 venv
python -m venv venv
.\venv\Scripts\Activate.ps1
```

2. 安装最小依赖：

```powershell
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn -r requirements-min.txt
```

3. 启动 Redis（若使用 Celery）：

```powershell
# 启动本地 redis（根据你的 redis 安装路径）
redis-server
```

4. 启动 Celery worker（可选）：

```powershell
celery -A task_manager worker --loglevel=info --pool=solo
```

5. 启动 Web 服务或命令行翻译：

```powershell
python web_interface.py
# 或直接使用命令行接口
python cl_text_interface.py
python cl_file_interface.py --file_path input.docx --output_path out.docx --source_lang English --target_lang Chinese
```

## 遇到的已知问题与建议

- 问题：在当前环境（Python 3.14）下，`numpy==1.26.4` 无可用 wheel，pip 尝试源码构建导致缺少编译器（MSVC）而失败。
- 建议：
  - 推荐方案：使用官方支持的 Python 3.12 或 3.11 创建虚拟环境，这样可以安装 NumPy 的预编译 wheel。示例：

```powershell
C:\Python312\python.exe -m venv .\venv312
.\venv312\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn -r requirements.txt
```

  - 替代方案：如不需要 `pandas`/`numpy`，可使用 `requirements-min.txt` 快速启动核心功能（Web 服务、Ollama 集成、文档翻译等）。

  - 如果必须在当前 Python 上编译，请安装 Visual Studio Build Tools（含 MSVC 与 Windows SDK），但该方案耗时且易出问题。

## 复现与验证

- 验证点：
  - 确保 `gl_config.py` 中的 `ENDPOINT_URL` 与本地 Ollama 地址一致；
  - 启动 Web 服务后，访问项目提供的翻译页面并上传文档；
  - 在 Celery worker 日志中观察任务接受与完成；
  - 若 Excel/Word/PPT 需要复杂处理，确保相应包（`python-pptx`, `python-docx`, `openpyxl`）已安装。

## 结语

本文件旨在记录已成功恢复的最小架构与操作步骤，便于快速复现与部署。如需我将 `requirements.txt` 中的问题包修复回可用版本或切回完整依赖安装流程（在 Python 3.12 下），或将该文档添加到 README，请告知。