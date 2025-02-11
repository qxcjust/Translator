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
        self.font_size = font_size  # 单位 pt
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
    
    sentences = re.split('([。！？.!?])', text)
    chunks = []
    current_chunk = ""
    for i in range(0, len(sentences), 2):
        sentence = sentences[i]
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
    """
    根据形状尺寸（转换为 pt 单位）和文本总长度，估算合适的字体大小（只向下调整）。
    仅作为局部调整的参考，后续统一调整字体大小时采用后处理方案。
    """
    try:
        if not shape.width or not shape.height:
            return original_size
        width_pt = shape.width / 12700.0
        height_pt = shape.height / 12700.0
        avg_char_width = original_size * 1.2
        if avg_char_width == 0:
            return original_size
        chars_per_line = width_pt / avg_char_width
        if chars_per_line <= 0:
            return original_size
        estimated_lines = len(text) / chars_per_line
        line_height = original_size * 1.2
        required_height = estimated_lines * line_height
        if required_height > height_pt:
            new_size = original_size * (height_pt / required_height)
            return max(8, new_size)
        return original_size
    except Exception as e:
        logging.warning(f"计算字体大小时出错: {e}")
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
        logging.warning(f"获取格式信息时出错: {e}")
        return TextFormat()

def apply_text_format(run, format_info, shape=None, text=None):
    """应用文本格式到 run"""
    try:
        if format_info.font_name:
            run.font.name = format_info.font_name
        if format_info.font_size:
            run.font.size = Pt(format_info.font_size)
        if format_info.font_bold is not None:
            run.font.bold = format_info.font_bold
        if format_info.font_italic is not None:
            run.font.italic = format_info.font_italic
        if format_info.font_underline is not None:
            run.font.underline = format_info.font_underline
        if format_info.color:
            run.font.color.rgb = format_info.color
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
        logging.warning(f"应用格式时出错: {e}")

def translate_text_with_format(translation_core, text, source_lang, target_lang):
    """翻译文本并处理长文本"""
    if not text.strip():
        return ""
    text_chunks = split_text(text)
    translated_chunks = []
    for chunk in text_chunks:
        translated_chunk = translation_core.translate_text(chunk, source_lang, target_lang)
        translated_chunks.append(translated_chunk)
    return "".join(translated_chunks)

def get_separators(language):
    if language == "Chinese":
        return '．，、：；！？”“‘’（）《》【】——…'
    elif language == "English":
        return ', : ; ! ? " \' ( ) - ...'
    elif language == "Japanese":
        return '．、：；！？”）（）『』【】ー…'
    else:
        return '. , : ;'

def split_text_into_parts(text, num_parts, target_lang):
    avg_length = len(text) // num_parts
    split_texts = []
    start = 0
    separators_all = get_separators(target_lang)
    separators = re.compile(r'[' + separators_all + ']')
    for i in range(num_parts):
        if i == num_parts - 1:
            split_texts.append(text[start:])
        else:
            end = start + avg_length
            match = separators.search(text, end)
            if match:
                end = match.end()
            else:
                end = start + avg_length
            split_texts.append(text[start:end])
            start = end
    return split_texts

# ----------------------- 组合形状处理辅助函数 -----------------------
def scan_shape(shape):
    """
    递归统计形状中所有文本的字符数（包括文本框、表格及组合形状内的子形状）
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
    if hasattr(shape, "shapes"):
        for sub_shape in shape.shapes:
            total += scan_shape(sub_shape)
    return total

def process_text_frame(text_frame, container, translation_core, source_lang, target_lang, task, current_work, total_work):
    """
    对单个文本框（或单元格内的文本框）进行翻译，并保持格式。
    container 参数用于传递原始形状或单元格，供计算字体大小时使用。
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
    
    # 清空文本框内容，但保留第一个段落，避免产生多余换行
    while len(text_frame.paragraphs) > 1:
        p = text_frame.paragraphs[-1]
        p._element.getparent().remove(p._element)
    first_paragraph = text_frame.paragraphs[0]
    first_paragraph.text = ""
    
    # 应用翻译后的文本与格式（保持原 run 分割，不在此处统一调整字体大小）
    for idx, (alignment, runs_info) in enumerate(paragraph_formats):
        if idx == 0:
            paragraph = text_frame.paragraphs[0]
        else:
            paragraph = text_frame.add_paragraph()
        if alignment is not None:
            paragraph.alignment = alignment
            if runs_info and len(runs_info) > 0 and hasattr(paragraph, 'margin_left'):
                paragraph.margin_left = runs_info[0][1][0].margin_left
        for split_texts, format_infos in runs_info:
            for split_text, format_info in zip(split_texts, format_infos):
                run = paragraph.add_run()
                run.text = split_text
                apply_text_format(run, format_info, container, split_text)

def process_table(table, translation_core, source_lang, target_lang, task, current_work, total_work):
    """
    处理表格中每个单元格的文本翻译
    注意：容器参数改为 cell 而非 cell.text_frame
    """
    for row in table.rows:
        for cell in row.cells:
            if cell.text.strip():
                process_text_frame(cell.text_frame, cell, translation_core, source_lang, target_lang, task, current_work, total_work)

def process_shape(shape, translation_core, source_lang, target_lang, task, current_work, total_work):
    """
    递归处理单个形状：
      - 若形状具有文本框，则翻译其中的文字；
      - 若形状为表格，则处理所有单元格；
      - 若为组合形状，则递归处理其所有子形状。
    """
    if hasattr(shape, "has_text_frame") and shape.has_text_frame:
        process_text_frame(shape.text_frame, shape, translation_core, source_lang, target_lang, task, current_work, total_work)
    elif hasattr(shape, "has_table") and shape.has_table:
        process_table(shape.table, translation_core, source_lang, target_lang, task, current_work, total_work)
    if hasattr(shape, "shapes"):
        for sub_shape in shape.shapes:
            process_shape(sub_shape, translation_core, source_lang, target_lang, task, current_work, total_work)

# ----------------------- 后处理：统一调整字体大小 -----------------------
def adjust_text_frame_font_size(text_frame, container):
    """
    对单个文本框进行后处理：估算该文本框内所有文字在当前字体下所需的高度，
    如果超出容器高度，则计算统一缩放因子并按比例缩小所有 run 的字体大小，
    保证翻译后的文字全部显示在容器内。若不超出，则保持原样。
    这里 container 应该是具有 width、height 属性的对象（如 Shape 或 Table Cell）。
    """
    total_text = ""
    font_sizes = []
    for paragraph in text_frame.paragraphs:
        for run in paragraph.runs:
            if run.text.strip():
                total_text += run.text
                if run.font.size:
                    font_sizes.append(run.font.size.pt)
                else:
                    font_sizes.append(12)
    if not total_text:
        return
    avg_font_size = sum(font_sizes) / len(font_sizes)
    if not hasattr(container, 'width') or not hasattr(container, 'height'):
        return
    width_pt = container.width / 12700.0
    height_pt = container.height / 12700.0
    char_width = avg_font_size * 1.2
    if char_width == 0:
        return
    chars_per_line = width_pt / char_width
    if chars_per_line <= 0:
        return
    total_chars = len(total_text)
    estimated_lines = total_chars / chars_per_line
    line_height = avg_font_size * 1.2
    estimated_height = estimated_lines * line_height
    if estimated_height > height_pt:
        scaling_factor = height_pt / estimated_height
    else:
        scaling_factor = 1.0
    if scaling_factor < 1.0:
        for paragraph in text_frame.paragraphs:
            for run in paragraph.runs:
                if run.text.strip():
                    current_size = run.font.size.pt if run.font.size else 12
                    new_size = current_size * scaling_factor
                    new_size = max(new_size, 8)  # 确保不低于8pt
                    run.font.size = Pt(new_size)

def adjust_shape_font_size(shape):
    """
    对单个形状进行后处理：
      - 如果形状有文本框，则调整其字体大小；
      - 如果为表格，则对所有单元格执行调整；
      - 如果为组合形状，则递归处理其所有子形状。
    为避免出现 container 为 TextFrame 的情况，这里先检查 shape 是否具有 width 属性。
    """
    if not (hasattr(shape, 'width') and hasattr(shape, 'height')):
        return
    if hasattr(shape, "has_text_frame") and shape.has_text_frame:
        adjust_text_frame_font_size(shape.text_frame, shape)
    if hasattr(shape, "has_table") and shape.has_table:
        for row in shape.table.rows:
            for cell in row.cells:
                adjust_text_frame_font_size(cell.text_frame, cell)
    if hasattr(shape, "shapes"):
        for sub_shape in shape.shapes:
            adjust_shape_font_size(sub_shape)

def adjust_font_size_for_all_shapes(prs):
    """遍历所有幻灯片的所有形状，对含文本的形状统一调整字体大小"""
    for slide in prs.slides:
        for shape in slide.shapes:
            adjust_shape_font_size(shape)

# ----------------------- 主函数 -----------------------
def translate_powerpoint(translation_core, file_path, output_path, source_lang, target_lang, task):
    """
    翻译 PowerPoint 文件并保持格式（支持组合形状）。
    先按原逻辑翻译并应用格式，然后在保存前统一后处理：
      如果翻译后的文字已完全显示在容器内，则不调整；
      如果超出，则统一缩小字体大小，使得所有文字能显示在容器内。
    """
    logging.info(f"开始翻译PowerPoint文件: {file_path}")
    try:
        prs = Presentation(file_path)
        total_work = 0
        for slide in prs.slides:
            for shape in slide.shapes:
                total_work += scan_shape(shape)
        current_work = [0]
        for slide in prs.slides:
            for shape in slide.shapes:
                process_shape(shape, translation_core, source_lang, target_lang, task, current_work, total_work)
        adjust_font_size_for_all_shapes(prs)
        prs.save(output_path)
        logging.info(f"PowerPoint文件翻译完成: {output_path}")
    except Exception as e:
        logging.error(f"翻译文件时出错 {file_path}: {e}")
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
