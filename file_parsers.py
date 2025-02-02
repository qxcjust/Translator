import pandas as pd
from pptx import Presentation
from openpyxl import load_workbook
from docx import Document

def parse_excel(file_path):
    return pd.read_excel(file_path)

def parse_powerpoint(file_path):
    return Presentation(file_path)

def parse_word(file_path):
    return Document(file_path)