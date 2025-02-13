import os
from docx import Document

def translate_word(translation_core, file_path, output_path, source_lang, target_lang, task):
    # 打开Word文档
    doc = Document(file_path)
    
    # 遍历文档中的每个段落
    for para in doc.paragraphs:
        # 获取段落文本
        text = para.text
        # 如果段落不为空，则进行翻译
        if text.strip():
            translated_text = translation_core.translate_text(text, source_lang, target_lang)
            # 替换段落文本为翻译后的文本
            para.text = translated_text
    
    # 遍历文档中的每个表格
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                # 获取单元格文本
                text = cell.text
                # 如果单元格文本不为空，则进行翻译
                if text.strip():
                    translated_text = translation_core.translate_text(text, source_lang, target_lang)
                    # 替换单元格文本为翻译后的文本
                    cell.text = translated_text
    
    # 保存翻译后的文档
    doc.save(output_path)