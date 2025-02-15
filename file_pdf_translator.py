# import fitz  # PyMuPDF
# from docx import Document

# def translate_pdf(translation_core, file_path, output_path, source_lang, target_lang, task):
#     # 打开PDF文档
#     pdf_document = fitz.open(file_path)
    
#     doc = Document()
    
#     # 遍历PDF文档中的每一页
#     for page_num in range(len(pdf_document)):
#         page = pdf_document.load_page(page_num)
#         # 获取页面文本
#         text = page.get_text("text")
#         # 如果页面文本不为空，则进行翻译
#         if text.strip():
#             translated_text = translation_core.translate_text(text, source_lang, target_lang)
#             # 将翻译后的文本添加到Word文档中
#             doc.add_paragraph(translated_text)
    
#     # 保存翻译后的文档
#     doc.save(output_path)