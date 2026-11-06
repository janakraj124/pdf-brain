# table_extractor.py
import pdfplumber
import pandas as pd
import os

def extract_tables(pdf_path):
    tables = []
    if not os.path.exists(pdf_path):
        return []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            page_tables = page.extract_tables()
            for table_idx, table in enumerate(page_tables, 1):
                if not table or len(table) < 2:
                    continue
                df = pd.DataFrame(table[1:], columns=table[0])
                df = df.dropna(how="all")
                df = df.loc[:, ~df.isna().all()]
                tables.append({
                    "page": page_num,
                    "index": table_idx,
                    "dataframe": df,
                    "rows": len(df),
                    "cols": len(df.columns)
                })
    return tables