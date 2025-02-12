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

class pptTextFormat:
    """Store text format information"""
    def __init__(self, font_name=None, font_size=None, font_bold=None, 
                 font_italic=None, font_underline=None, color=None, 
                 alignment=None, spacing=None, margin_left=None, margin_right=None):
        self.font_name = font_name
        self.font_size = font_size  # in pt
        self.font_bold = font_bold
        self.font_italic = font_italic
        self.font_underline = font_underline
        self.color = color
        self.alignment = alignment
        self.spacing = spacing
        self.margin_left = margin_left
        self.margin_right = margin_right

def split_text(text, max_length=4096):
    """Split long text into smaller chunks"""
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
    Estimate an appropriate font size based on the shape dimensions (converted to pt) and the total length of the text.
    Only used as a reference for local adjustments; a unified font size adjustment will be applied later.
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
        logging.warning(f"Error calculating font size: {e}")
        return original_size

def get_text_format(run, shape=None):
    """Get format information for a text run"""
    try:
        font = run.font
        format_info = pptTextFormat(
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
        logging.warning(f"Error getting format information: {e}")
        return pptTextFormat()

def apply_text_format(run, format_info, shape=None, text=None):
    """Apply text format to run"""
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
        logging.warning(f"Error applying format: {e}")

def translate_text_with_format(translation_core, text, source_lang, target_lang):
    """Translate text and handle long text"""
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

# ----------------------- Helper functions for grouped shapes -----------------------
def scan_shape(shape):
    """
    Recursively count the number of characters in all text within the shape (including text frames, tables, and sub-shapes within grouped shapes)
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
    Translate a single text frame (or text frame within a cell) and maintain the format.
    The container parameter is used to pass the original shape or cell for font size calculations.
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
    
    # Clear the text frame content, but retain the first paragraph to avoid extra line breaks
    while len(text_frame.paragraphs) > 1:
        p = text_frame.paragraphs[-1]
        p._element.getparent().remove(p._element)
    first_paragraph = text_frame.paragraphs[0]
    first_paragraph.text = ""
    
    # Apply translated text and format (keep original run divisions, do not adjust font size here)
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
    Process the text in each cell of the table
    Note: The container parameter is changed from cell.text_frame to cell
    """
    for row in table.rows:
        for cell in row.cells:
            if cell.text.strip():
                process_text_frame(cell.text_frame, cell, translation_core, source_lang, target_lang, task, current_work, total_work)

def process_shape(shape, translation_core, source_lang, target_lang, task, current_work, total_work):
    """
    Recursively process a single shape:
      - If the shape has a text frame, translate the text within it;
      - If the shape is a table, process all cells;
      - If it is a grouped shape, recursively process all sub-shapes.
    """
    if hasattr(shape, "has_text_frame") and shape.has_text_frame:
        process_text_frame(shape.text_frame, shape, translation_core, source_lang, target_lang, task, current_work, total_work)
    elif hasattr(shape, "has_table") and shape.has_table:
        process_table(shape.table, translation_core, source_lang, target_lang, task, current_work, total_work)
    if hasattr(shape, "shapes"):
        for sub_shape in shape.shapes:
            process_shape(sub_shape, translation_core, source_lang, target_lang, task, current_work, total_work)

# ----------------------- Post-processing: Unified font size adjustment -----------------------
def adjust_text_frame_font_size(text_frame, container):
    """
    Post-process a single text frame: estimate the total height required for all text in the text frame at the current font size,
    if it exceeds the container height, calculate a uniform scaling factor and proportionally reduce the font size of all runs,
    ensuring that the translated text fits within the container. If it does not exceed, keep the original size.
    Here, container should be an object with width and height attributes (such as Shape or Table Cell).
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
                    new_size = max(new_size, 8)  # Ensure no less than 8pt
                    run.font.size = Pt(new_size)

def adjust_shape_font_size(shape):
    """
    Post-process a single shape:
      - If the shape has a text frame, adjust its font size;
      - If it is a table, adjust all cells;
      - If it is a grouped shape, recursively process all sub-shapes.
    To avoid the case where container is TextFrame, check if shape has width attribute first.
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
    """Traverse all shapes in all slides and uniformly adjust the font size for text-containing shapes"""
    for slide in prs.slides:
        for shape in slide.shapes:
            adjust_shape_font_size(shape)

# ----------------------- Main function -----------------------
def translate_powerpoint(translation_core, file_path, output_path, source_lang, target_lang, task):
    """
    Translate a PowerPoint file and maintain the format (supports grouped shapes).
    First, translate and apply formats according to the original logic, then uniformly adjust font sizes before saving:
      If the translated text is completely displayed within the container, do not adjust;
      If it exceeds, uniformly reduce the font size so that all text can be displayed within the container.
    """
    logging.info(f"Start translating PowerPoint file: {file_path}")
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
        logging.info(f"PowerPoint file translation completed: {output_path}")
    except Exception as e:
        logging.error(f"Error translating file {file_path}: {e}")
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
