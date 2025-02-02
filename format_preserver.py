import pandas as pd
from pptx import Presentation
from docx import Document

def save_translated_excel(df, output_path):
    df.to_excel(output_path, index=False)

def save_translated_powerpoint(prs, output_path):
    prs.save(output_path)

def save_translated_word(doc, output_path):
    doc.save(output_path)