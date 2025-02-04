import pandas as pd
from pptx import Presentation
from openpyxl import load_workbook
from docx import Document  # 现在会指向正确的 python-docx 包
import os
def parse_excel(file_path):
    return pd.read_excel(file_path)

def parse_powerpoint(file_path):
    return Presentation(file_path)

def parse_word(file_path):
    return Document(file_path)

# 新增函数：获取文件页数
def get_file_pages(file_path):
    #自动识别file_type
    file_type = file_path.split('.')[-1].lower()
    if file_type.lower() in ['xls', 'xlsx']:
        # 读取Excel文件
        df = pd.read_excel(file_path)
        # 计算总字符数
        total_chars = df.astype(str).apply(lambda x: x.str.len()).sum().sum()
        # 每2000字符为一页
        return (total_chars + 1999) // 2000
    elif file_type.lower() in ['ppt', 'pptx']:
        # 读取PowerPoint文件
        prs = Presentation(file_path)
        return len(prs.slides)
    elif file_type.lower() in ['docx']:
        # 读取Word文件
        doc = Document(file_path)
        return len(doc.paragraphs)
    else:
        return 0

#get file size
def get_file_size(file_path):
    # 获取文件大小
    file_size = os.path.getsize(file_path)
    # 格式化文件大小，文件大小过大的话，则用MB表示
    if file_size > 1024 * 1024:
        file_size = f"{file_size / (1024 * 1024):.2f} MB"
    else:
        file_size = f"{file_size / 1024:.2f} KB"
    return file_size