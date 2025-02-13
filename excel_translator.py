import logging
from openpyxl import load_workbook, Workbook
from openpyxl.utils import get_column_letter
from openpyxl.styles import Font, Fill, Border, Alignment

logging.basicConfig(level=logging.INFO)

def translate_excel(translation_core, file_path, output_path, source_lang, target_lang, task):
    """翻译Excel文件并保持原始格式和结构"""
    logging.info(f"Starting translation of Excel file: {file_path}")
    
    # 加载原始工作簿和创建翻译后的工作簿
    original_wb = load_workbook(file_path)
    translated_wb = Workbook()
    translated_wb.remove(translated_wb.active)  # 移除默认创建的空白Sheet

    total_sheets = len(original_wb.sheetnames)
    
    for sheet_idx, sheet_name in enumerate(original_wb.sheetnames, 1):
        # 获取原始Sheet并创建对应的翻译Sheet
        original_sheet = original_wb[sheet_name]
        translated_sheet = translated_wb.create_sheet(sheet_name)
        
        # 复制行高和列宽
        _copy_row_heights(original_sheet, translated_sheet)
        _copy_column_widths(original_sheet, translated_sheet)
        
        # 处理合并单元格
        for merged_range in original_sheet.merged_cells.ranges:
            translated_sheet.merge_cells(str(merged_range))
        
        # 计算当前Sheet的总单元格数
        total_cells = original_sheet.max_row * original_sheet.max_column
        
        # 翻译单元格内容并复制格式
        for row_idx, row in enumerate(original_sheet.iter_rows(), 1):
            for cell_idx, cell in enumerate(row, 1):
                translated_value = _translate_cell_value(cell, translation_core, source_lang, target_lang)
                translated_cell = translated_sheet.cell(row=cell.row, column=cell.column, value=translated_value)
                _copy_cell_style(cell, translated_cell)
                
                # 更新单元格翻译进度
                cell_progress = ((row_idx - 1) * original_sheet.max_column + cell_idx) / total_cells * 100
                if task is not None:
                    task.update_state(
                        state='PROGRESS',
                        meta={
                            'current': sheet_idx,
                            'total': total_sheets,
                            'cell_progress': cell_progress,
                            'sheet_progress': (sheet_idx - 1) / total_sheets * 100,
                            'progress': ((sheet_idx - 1) + cell_progress / 100) / total_sheets * 100
                        }
                    )
        
        # 更新任务进度
        sheet_progress = (sheet_idx / total_sheets) * 100
        if task is not None:
            task.update_state(
                state='PROGRESS',
                meta={
                    'current': sheet_idx,
                    'total': total_sheets,
                    'cell_progress': 100,
                    'sheet_progress': sheet_progress,
                    'progress': sheet_progress
                }
            )
        logging.info(f"Progress: {sheet_progress:.1f}% - Translated sheet '{sheet_name}'")

    # 保存翻译后的工作簿
    translated_wb.save(output_path)
    logging.info(f"Completed translation. Saved to: {output_path}")

def _translate_cell_value(cell, translator, src_lang, tgt_lang):
    """翻译单元格文本内容"""
    try:
        return translator.translate_text(cell.value, src_lang, tgt_lang) if isinstance(cell.value, str) else cell.value
    except Exception as e:
        logging.error(f"Translation error at {cell.coordinate}: {str(e)}")
        return cell.value  # 出错时返回原值

def _copy_cell_style(src_cell, dest_cell):
    """深度复制单元格样式"""
    dest_cell.font = src_cell.font.copy()
    dest_cell.fill = src_cell.fill.copy()
    dest_cell.border = src_cell.border.copy()
    dest_cell.alignment = src_cell.alignment.copy()
    dest_cell.number_format = src_cell.number_format

def _copy_row_heights(src_sheet, dest_sheet):
    """复制行高设置"""
    for row_idx, src_row in src_sheet.row_dimensions.items():
        dest_row = dest_sheet.row_dimensions[row_idx]
        dest_row.height = src_row.height

def _copy_column_widths(src_sheet, dest_sheet):
    """复制列宽设置"""
    for col_letter, src_col in src_sheet.column_dimensions.items():
        dest_col = dest_sheet.column_dimensions[col_letter]
        dest_col.width = src_col.width