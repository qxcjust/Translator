import os
from docx import Document
from docx.shared import Pt
from pptx.dml.color import RGBColor
from docx.table import Table
from docx.text.paragraph import Paragraph

# 遍历文档中的表格
def extract_table_text(translation_core, source_lang, target_lang, task, current_work, total_work, table, level=0):
    """
    递归提取表格中的文本，包括嵌套表格
    :param table: Word 文档中的表格对象
    :param level: 嵌套层级（用于格式化输出）
    """
    for row in table.rows:
        for cell in row.cells:
            # 获取单元格文本
            text = cell.text
            # 如果单元格文本不为空，则进行翻译
            if text.strip():
                translated_text = translation_core.translate_text(text, source_lang, target_lang)
                # 替换单元格文本为翻译后的文本
                cell.text = translated_text
                current_work += len(text)
                update_progress(task, current_work, total_work)
                # 输出当前单元格文本（缩进表示层级）
                # print("    " * level + cell.tex )
            # 检查单元格是否包含嵌套表格
            if cell.tables:
                for nested_table in cell.tables:
                     # 递归处理嵌套表格
                    extract_table_text(translation_core, source_lang, target_lang, task, current_work, total_work, nested_table, level + 1)


def translate_word(translation_core, file_path, output_path, source_lang, target_lang, task):
    # 打开Word文档
    doc = Document(file_path)
    
    # 计算总工作量
    total_work = sum(len(para.text) for para in doc.paragraphs) + \
                 sum(len(cell.text) for table in doc.tables for row in table.rows for cell in row.cells)

    current_work = 0
    

    # 遍历文档中的每个段落
    for para in doc.paragraphs:
        # 获取段落文本
        text = para.text
        # 如果段落不为空，则进行翻译
        if text.strip():
            translated_text = translation_core.translate_text(text, source_lang, target_lang)
            # 替换段落文本为翻译后的文本
            para.text = translated_text
            current_work += len(text)
            update_progress(task, current_work, total_work)


    # 遍历文档中的样式表格
    for table in doc.tables:
        extract_table_text(translation_core, source_lang, target_lang, task, current_work, total_work, table, 0)

    # 遍历文档中的每个形状
    for shape in doc.inline_shapes:
        if shape.has_text_frame:
            for paragraph in shape.text_frame.paragraphs:
                for run in paragraph.runs:
                    text = run.text
                    if text.strip():
                        translated_text = translation_core.translate_text(text, source_lang, target_lang)
                        run.text = translated_text
                        current_work += len(text)
                        update_progress(task, current_work, total_work)

    # 保存翻译后的文档
    doc.save(output_path)

def update_progress(task, current_work, total_work):
    """更新翻译进度"""
    if task is not None:
        progress = (current_work / total_work) * 100
        task.update_state(
            state='PROGRESS',
            meta={
                'current': current_work,
                'total': total_work,
                'progress': round(progress, 1)
            }
        )