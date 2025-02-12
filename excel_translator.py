import logging
from file_parsers import parse_excel
from openpyxl import load_workbook, Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.styles import Font, Fill, Border, Alignment

# 配置日志记录
logging.basicConfig(level=logging.INFO)

def translate_excel(translation_core, file_path, output_path, source_lang, target_lang, task):
    logging.info(f"Starting translation of Excel file: {file_path}")
    df, format_info = load_excel_format(file_path)  # 修改：获取格式信息
    total_rows = len(df)
    translated_df = df.applymap(lambda x: translation_core.translate_text(x, source_lang, target_lang) if isinstance(x, str) else x)
    apply_excel_format(translated_df, format_info, output_path)  # 修改：保存格式信息
    logging.info(f"Completed translation of Excel file: {file_path}")
    task.update_state(state='PROGRESS', meta={'current': total_rows, 'total': total_rows, 'progress': 100.0})

def load_excel_format(self, file_path):
    # 读取Excel文件的格式信息
    # 这里假设使用openpyxl库来读取格式信息
    wb = load_workbook(file_path)
    sheet = wb.active
    format_info = {}
    for row in sheet.iter_rows():
        for cell in row:
            format_info[cell.coordinate] = {
                'font': cell.font.copy(),
                'fill': cell.fill.copy(),
                'border': cell.border.copy(),
                'alignment': cell.alignment.copy(),
                'number_format': cell.number_format
            }
    return format_info, sheet

def apply_excel_format(self, df, format_info, output_path):
    # 将格式信息应用到翻译后的DataFrame并保存到新的Excel文件中
    wb = Workbook()
    ws = wb.active
    for r in dataframe_to_rows(df, index=False, header=True):
        ws.append(r)

    for cell in ws.iter_cells():
        if cell.coordinate in format_info:
            cell.font = format_info[cell.coordinate]['font']
            cell.fill = format_info[cell.coordinate]['fill']
            cell.border = format_info[cell.coordinate]['border']
            cell.alignment = format_info[cell.coordinate]['alignment']
            cell.number_format = format_info[cell.coordinate]['number_format']

    wb.save(output_path)