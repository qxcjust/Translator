import logging
from pptx import Presentation
from pptx.enum.text import PP_ALIGN
from pptx.util import Pt
from pptx.dml.color import RGBColor
import traceback
from pptx.util import Inches
import re

# 配置日志记录
logging.basicConfig(level=logging.INFO)

class TextFormat:
    """存储文本格式信息的类"""
    def __init__(self, font_name=None, font_size=None, font_bold=None, 
                 font_italic=None, font_underline=None, color=None, 
                 alignment=None, spacing=None, margin_left=None, margin_right=None):
        self.font_name = font_name
        self.font_size = font_size
        self.font_bold = font_bold
        self.font_italic = font_italic
        self.font_underline = font_underline
        self.color = color
        self.alignment = alignment
        self.spacing = spacing
        self.margin_left = margin_left
        self.margin_right = margin_right

def split_text(text, max_length=4096):
    """将长文本分割成更小的块"""
    if len(text) <= max_length:
        return [text]
    
    # 按句子分割
    sentences = re.split('([。！？.!?])', text)
    chunks = []
    current_chunk = ""
    
    for i in range(0, len(sentences), 2):
        sentence = sentences[i]
        # 添加标点符号（如果有）
        if i + 1 < len(sentences):
            sentence += sentences[i + 1]
            
        if len(current_chunk) + len(sentence) <= max_length:
            current_chunk += sentence
        else:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = sentence
            
    if current_chunk:
        chunks.append(current_chunk)
        
    return chunks

def calculate_font_size(shape, text, original_size):
    """计算适合形状的字体大小"""
    try:
        if not shape.width or not shape.height:
            return original_size
            
        # 获取形状的尺寸
        shape_width = shape.width
        shape_height = shape.height
        
        # 估算每个字符的平均宽度（使用原始字体大小）
        avg_char_width = Pt(original_size) * 1.2  # 1.2是一个经验系数
        
        # 计算每行可以容纳的字符数
        chars_per_line = shape_width / avg_char_width
        
        # 估算所需的行数
        estimated_lines = len(text) / chars_per_line
        
        # 计算每行所需的高度
        line_height = Pt(original_size) * 1.5  # 1.5是行间距系数
        
        # 计算所需的总高度
        required_height = line_height * estimated_lines
        
        # 如果所需高度超过形状高度，调整字体大小
        if required_height > shape_height:
            new_size = original_size * (shape_height / required_height)
            # 限制最小字体大小
            return max(8, new_size)
            
        return original_size
        
    except Exception as e:
        logging.warning(f"计算字体大小时出错: {str(e)}")
        return original_size

def get_text_format(run, shape=None):
    """获取文本运行的格式信息"""
    try:
        font = run.font
        format_info = TextFormat(
            font_name=font.name,
            font_size=font.size.pt if font.size else None,
            font_bold=font.bold,
            font_italic=font.italic,
            font_underline=font.underline,
            color=font.color.rgb if font.color and hasattr(font.color, 'rgb') else None
        )
        
        # 获取段落级别的格式
        if hasattr(run, '_p'):
            paragraph = run._p
            if hasattr(paragraph, 'alignment'):
                format_info.alignment = paragraph.alignment
            if hasattr(paragraph, 'spacing'):
                format_info.spacing = paragraph.spacing
            if hasattr(paragraph, 'margin_left'):
                format_info.margin_left = paragraph.margin_left
            if hasattr(paragraph, 'margin_right'):
                format_info.margin_right = paragraph.margin_right
                
        return format_info
    except Exception as e:
        logging.warning(f"获取格式信息时出错: {str(e)}")
        return TextFormat()

def apply_text_format(run, format_info, shape=None, text=None):
    """应用文本格式到运行"""
    try:
        if format_info.font_name:
            run.font.name = format_info.font_name
            
        # 计算适应形状的字体大小
        if format_info.font_size and shape and text:
            adapted_size = calculate_font_size(shape, text, format_info.font_size)
            run.font.size = Pt(adapted_size)
        elif format_info.font_size:
            run.font.size = Pt(format_info.font_size)
            
        if format_info.font_bold is not None:
            run.font.bold = format_info.font_bold
        if format_info.font_italic is not None:
            run.font.italic = format_info.font_italic
        if format_info.font_underline is not None:
            run.font.underline = format_info.font_underline
        if format_info.color:
            run.font.color.rgb = format_info.color
            
        # 应用段落级别的格式
        if hasattr(run, '_p'):
            paragraph = run._p
            if format_info.alignment is not None:
                paragraph.alignment = format_info.alignment
            if format_info.spacing is not None:
                paragraph.spacing = format_info.spacing
            if format_info.margin_left is not None:
                paragraph.margin_left = format_info.margin_left
            if format_info.margin_right is not None:
                paragraph.margin_right = format_info.margin_right
                
    except Exception as e:
        logging.warning(f"应用格式时出错: {str(e)}")

def translate_text_with_format(translation_core, text, source_lang, target_lang):
    """翻译文本并处理长文本"""
    if not text.strip():
        return ""
        
    # 分割长文本
    text_chunks = split_text(text)
    translated_chunks = []
    
    # 翻译每个文本块
    for chunk in text_chunks:
        translated_chunk = translation_core.translate_text(chunk, source_lang, target_lang)
        translated_chunks.append(translated_chunk)
        
    # 合并翻译结果
    return "".join(translated_chunks)

def translate_powerpoint(translation_core, file_path, output_path, source_lang, target_lang, task):
    """翻译PowerPoint文件并保持格式"""
    logging.info(f"开始翻译PowerPoint文件: {file_path}")
    try:
        prs = Presentation(file_path)
        
        # 计算总工作量
        total_work = 0
        current_work = 0
        
        # 预扫描所有需要翻译的内容
        for slide in prs.slides:
            for shape in slide.shapes:
                if shape.has_text_frame:
                    for paragraph in shape.text_frame.paragraphs:
                        if len(paragraph.runs) > 0:
                            for run in paragraph.runs:
                                if run.text.strip():
                                    total_work += len(run.text)
                        else:
                            if paragraph.text.strip():
                                total_work += len(paragraph.text)
                elif shape.has_table:
                    for row in shape.table.rows:
                        for cell in row.cells:
                            if cell.text.strip():
                                total_work += len(cell.text)

        for slide in prs.slides:
            for shape in slide.shapes:
                # 处理文本框
                if shape.has_text_frame:
                    text_frame = shape.text_frame
                    paragraph_formats = []
                    for paragraph in text_frame.paragraphs:
                        alignment = paragraph.alignment
                        runs_info = []

                        # 合并所有run的文本并记录格式信息
                        combined_text = ""
                        format_infos = []
                        for run in paragraph.runs:
                            if run.text.strip():
                                combined_text += run.text
                                format_infos.append(get_text_format(run))

                        if combined_text.strip():
                            translated_text = translate_text_with_format(
                                translation_core, combined_text, source_lang, target_lang
                            )
                            runs_info.append((translated_text, format_infos))
                            # 更新进度
                            current_work += len(combined_text)
                            progress = (current_work / total_work) * 100
                            if task is not None:
                                task.update_state(
                                    state='PROGRESS',
                                    meta={
                                        'current': current_work,
                                        'total': total_work,
                                        'progress': round(progress, 1)
                                    }
                                )

                        paragraph_formats.append((alignment, runs_info))
                    
                    # 应用翻译和格式
                    text_frame.clear()
                    for alignment, runs_info in paragraph_formats:
                        p = text_frame.add_paragraph()
                        if alignment is not None:
                            p.alignment = alignment
                        for text, format_infos in runs_info:
                            # 将翻译后的文本按原始run数量拆分
                            split_texts = [text[i:i+len(text)//len(format_infos)] for i in range(0, len(text), len(text)//len(format_infos))]
                            for split_text, format_info in zip(split_texts, format_infos):
                                run = p.add_run()
                                run.text = split_text
                                apply_text_format(run, format_info, shape, split_text)

                # 处理表格
                elif shape.has_table:
                    for row in shape.table.rows:
                        for cell in row.cells:
                            if cell.text.strip():
                                cell_formats = []
                                for paragraph in cell.text_frame.paragraphs:
                                    alignment = paragraph.alignment
                                    runs_info = []
                                    combined_text = ""
                                    format_infos = []
                                    for run in paragraph.runs:
                                        if run.text.strip():
                                            combined_text += run.text
                                            format_infos.append(get_text_format(run))

                                    if combined_text.strip():
                                        translated_text = translate_text_with_format(
                                            translation_core, combined_text, source_lang, target_lang
                                        )
                                        runs_info.append((translated_text, format_infos))
                                        # 更新进度
                                        current_work += len(combined_text)
                                        progress = (current_work / total_work) * 100
                                        if task is not None:
                                            task.update_state(
                                                state='PROGRESS',
                                                meta={
                                                    'current': current_work,
                                                    'total': total_work,
                                                    'progress': round(progress, 1)
                                                }
                                            )

                                    cell_formats.append((alignment, runs_info))
                                
                                # 应用翻译和格式
                                cell.text_frame.clear()
                                for alignment, runs_info in cell_formats:
                                    p = cell.text_frame.add_paragraph()
                                    if alignment is not None:
                                        p.alignment = alignment
                                    for text, format_infos in runs_info:
                                        # 将翻译后的文本按原始run数量拆分
                                        split_texts = [text[i:i+len(text)//len(format_infos)] for i in range(0, len(text), len(text)//len(format_infos))]
                                        for split_text, format_info in zip(split_texts, format_infos):
                                            run = p.add_run()
                                            run.text = split_text
                                            apply_text_format(run, format_info)

        # 保存翻译后的文件
        prs.save(output_path)
        logging.info(f"PowerPoint文件翻译完成: {output_path}")

    except Exception as e:
        logging.error(f"翻译文件时出错 {file_path}: {str(e)}")
        logging.error(traceback.format_exc())
        if task is not None:
            task.update_state(
                state='FAILURE',
                meta={
                    'exc_type': type(e).__name__,
                    'exc_message': str(e),
                    'traceback': traceback.format_exc()
                }
            )
        raise