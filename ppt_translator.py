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
        line_height = Pt(original_size) * 1.0  # 1.0是行高系数
        
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

def get_separators(language):
    if language == "Chinese":
        return '．，、：；！？”“‘’（）《》【】——…'
    elif language == "English":
        return ', : ; ! ? " \' ( ) - ...'
    elif language == "Japanese":
        return '．、：；！？”」（）『』【】ー…'
    else:
        return '. , : ;'  # 默认英文符号

def split_text_into_parts(text, num_parts, target_lang):
    avg_length = len(text) // num_parts
    split_texts = []
    start = 0

    # 正则表达式匹配分隔符（句号、逗号、冒号、分号等）
    separators_all = get_separators(target_lang)
    separators = re.compile(r'[' + separators_all + ']')

    for i in range(num_parts):
        if i == num_parts - 1:
            # 最后一部分包含剩余的所有字符
            split_texts.append(text[start:])
        else:
            # 计算预计分割位置
            end = start + avg_length
            # 从预估位置向后查找最近的符号
            match = separators.search(text, end)

            if match:
                end = match.end()  # 在符号之后分割
            else:
                # 如果找不到符号，使用平均长度位置
                end = start + avg_length

            split_texts.append(text[start:end])
            start = end  # 更新起始点

    return split_texts

# ----------------------- 新增辅助函数 -----------------------
def scan_shape(shape):
    """
    递归统计一个形状中所有文本的字符数（包括文本框、表格及组合形状内的子形状）
    """
    total = 0
    if hasattr(shape, "has_text_frame") and shape.has_text_frame:
        for paragraph in shape.text_frame.paragraphs:
            if paragraph.runs:
                for run in paragraph.runs:
                    if run.text.strip():
                        total += len(run.text)
            else:
                if paragraph.text.strip():
                    total += len(paragraph.text)
    if hasattr(shape, "has_table") and shape.has_table:
        for row in shape.table.rows:
            for cell in row.cells:
                if cell.text.strip():
                    total += len(cell.text)
    # 若为组合形状，则递归扫描内部所有子形状
    if hasattr(shape, "shapes"):
        for sub_shape in shape.shapes:
            total += scan_shape(sub_shape)
    return total

def process_text_frame(text_frame, container, translation_core, source_lang, target_lang, task, current_work, total_work):
    """
    对单个文本框（或单元格内的文本框）进行翻译，并保持格式。
    container 参数用于传递原始形状，供计算字体大小时使用。
    """
    paragraph_formats = []
    for paragraph in text_frame.paragraphs:
        alignment = paragraph.alignment
        runs_info = []
        combined_text = ""
        format_infos = []
        for run in paragraph.runs:
            if run.text:
                combined_text += run.text
                format_infos.append(get_text_format(run))
        if combined_text.strip():
            translated_text = translate_text_with_format(translation_core, combined_text, source_lang, target_lang)
            split_texts = split_text_into_parts(translated_text, len(format_infos), target_lang)
            runs_info.append((split_texts, format_infos))
            # 更新进度
            current_work[0] += len(combined_text)
            progress = (current_work[0] / total_work) * 100
            if task is not None:
                task.update_state(
                    state='PROGRESS',
                    meta={
                        'current': current_work[0],
                        'total': total_work,
                        'progress': round(progress, 1)
                    }
                )
        paragraph_formats.append((alignment, runs_info))
    
    # 清空文本框内容，但保留原始的第一个段落以避免产生多余换行
    while len(text_frame.paragraphs) > 1:
        p = text_frame.paragraphs[-1]
        p._element.getparent().remove(p._element)
    first_paragraph = text_frame.paragraphs[0]
    first_paragraph.text = ""
    
    # 应用翻译后的文本与格式
    for idx, (alignment, runs_info) in enumerate(paragraph_formats):
        if idx == 0:
            paragraph = text_frame.paragraphs[0]
        else:
            paragraph = text_frame.add_paragraph()
        if alignment is not None:
            paragraph.alignment = alignment  # 保留原始对齐方式
            if runs_info and len(runs_info) > 0 and hasattr(paragraph, 'margin_left'):
                paragraph.margin_left = runs_info[0][1][0].margin_left
        for split_texts, format_infos in runs_info:
            for split_text, format_info in zip(split_texts, format_infos):
                run = paragraph.add_run()
                run.text = split_text  # 填入翻译后的文本
                apply_text_format(run, format_info, container, split_text)

def process_table(table, translation_core, source_lang, target_lang, task, current_work, total_work):
    """
    处理表格中的每个单元格（cell）的文本框翻译
    """
    for row in table.rows:
        for cell in row.cells:
            if cell.text.strip():
                process_text_frame(cell.text_frame, cell.text_frame, translation_core, source_lang, target_lang, task, current_work, total_work)

def process_shape(shape, translation_core, source_lang, target_lang, task, current_work, total_work):
    """
    递归处理单个形状：
      - 如果形状含文本框，进行翻译
      - 如果形状为表格，处理其中所有单元格
      - 如果形状为组合形状，递归处理其所有子形状
    """
    if hasattr(shape, "has_text_frame") and shape.has_text_frame:
        process_text_frame(shape.text_frame, shape, translation_core, source_lang, target_lang, task, current_work, total_work)
    elif hasattr(shape, "has_table") and shape.has_table:
        process_table(shape.table, translation_core, source_lang, target_lang, task, current_work, total_work)
    # 若为组合形状，递归处理其内部子形状
    if hasattr(shape, "shapes"):
        for sub_shape in shape.shapes:
            process_shape(sub_shape, translation_core, source_lang, target_lang, task, current_work, total_work)

# ----------------------- 主函数 -----------------------
def translate_powerpoint(translation_core, file_path, output_path, source_lang, target_lang, task):
    """翻译PowerPoint文件并保持格式，包括对组合形状的支持"""
    logging.info(f"开始翻译PowerPoint文件: {file_path}")
    try:
        prs = Presentation(file_path)
        
        # 预扫描所有需要翻译的内容（包括组合形状内的文本）
        total_work = 0
        for slide in prs.slides:
            for shape in slide.shapes:
                total_work += scan_shape(shape)
        
        current_work = [0]  # 使用列表保存进度，便于在子函数中更新
        
        # 递归处理每个幻灯片中的所有形状
        for slide in prs.slides:
            for shape in slide.shapes:
                process_shape(shape, translation_core, source_lang, target_lang, task, current_work, total_work)
        
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
