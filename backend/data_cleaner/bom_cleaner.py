import os
import pandas as pd
from rapidfuzz import process, fuzz
import tabula
import pdfplumber
from langdetect import detect
from googletrans import Translator
import re

MPN_CANDIDATES = [
    "MPN", "Part Number", "Manufacturer Part Number", "Teilenummer", "Mfg. Part Number #", "Numéro de pièce", "Número de parte"
]
ALT_CANDIDATES = ["Alternative", "Alt Part Number", "Alternativ", "Ersatzteil"]
DESC_CANDIDATES = ["Description", "Beschreibung", "Desc"]

translator = Translator()

# Dummy known part numbers for typo correction (replace with real data or Octopart API)
KNOWN_PARTS = ["2015P", "SN74LS00N", "LM358", "NE555", "ATMEGA328P"]

def detect_header_row_xlsx(file_path, candidates, max_rows=10):
    import openpyxl
    wb = openpyxl.load_workbook(file_path, read_only=True)
    ws = wb.active
    for i, row in enumerate(ws.iter_rows(min_row=1, max_row=max_rows, values_only=True)):
        for cell in row:
            if cell and any(str(cell).strip() == c for c in candidates):
                return i  # 0-based index for pandas
    return 0  # fallback to first row

def detect_header_row_xls(file_path, candidates, max_rows=10):
    import xlrd
    wb = xlrd.open_workbook(file_path)
    ws = wb.sheet_by_index(0)
    for i in range(min(max_rows, ws.nrows)):
        row = ws.row_values(i)
        for cell in row:
            if cell and any(str(cell).strip() == c for c in candidates):
                return i  # 0-based index for pandas
    return 0  # fallback to first row

def read_bom(file_path):
    if file_path.endswith('.csv'):
        return pd.read_csv(file_path)
    elif file_path.endswith('.xlsx'):
        header_row = detect_header_row_xlsx(file_path, MPN_CANDIDATES)
        return pd.read_excel(file_path, header=header_row)
    elif file_path.endswith('.xls'):
        header_row = detect_header_row_xls(file_path, MPN_CANDIDATES)
        return pd.read_excel(file_path, header=header_row)
    elif file_path.endswith('.pdf'):
        try:
            dfs = tabula.read_pdf(file_path, pages='all', multiple_tables=True)
            return pd.concat(dfs, ignore_index=True)
        except Exception:
            with pdfplumber.open(file_path) as pdf:
                all_text = []
                for page in pdf.pages:
                    all_text.append(page.extract_text())
                # Fallback: return as a DataFrame with one column
                return pd.DataFrame({'RawText': all_text})
    else:
        raise ValueError("Unsupported file type")

def find_column(columns, candidates):
    # Try exact match first
    for candidate in candidates:
        if candidate in columns:
            return candidate
    # Fuzzy match
    for candidate in candidates:
        match, score, idx = process.extractOne(candidate, columns, scorer=fuzz.partial_ratio)
        if score > 80:
            return match
    return None

def extract_part_from_description(desc):
    # Dummy: extract first word with a digit (very naive)
    match = re.search(r'\b\w*\d+\w*\b', str(desc))
    return match.group(0) if match else None

def clean_mpn_value(value):
    if pd.isna(value):
        return value
    # Remove all non-alphanumeric characters
    return re.sub(r'[^A-Za-z0-9]', '', str(value))

def correct_typos(value, known_values):
    if pd.isna(value):
        return value
    # Clean the value first
    cleaned = clean_mpn_value(value)
    match, score, idx = process.extractOne(cleaned, known_values, scorer=fuzz.ratio)
    if score > 80:
        return match
    return cleaned

def translate_text(text, dest='en'):
    try:
        detected = detect(str(text))
        if detected != dest:
            return translator.translate(str(text), src=detected, dest=dest).text
        return text
    except Exception:
        return text

def clean_bom(df):
    # Standardize MPN column
    mpn_col = find_column(df.columns, MPN_CANDIDATES)
    if not mpn_col:
        raise ValueError("Could not find a Manufacturing Part Number column.")
    df = df.rename(columns={mpn_col: 'MPN'})

    # Standardize alternative and description columns
    alt_col = find_column(df.columns, ALT_CANDIDATES)
    desc_col = find_column(df.columns, DESC_CANDIDATES)
    if alt_col:
        df = df.rename(columns={alt_col: 'ALT'})
    if desc_col:
        df = df.rename(columns={desc_col: 'DESC'})

    # Fill missing MPNs only from alternative, not from description
    for idx, row in df.iterrows():
        if pd.isna(row['MPN']) or str(row['MPN']).strip() == '':
            # Try alternative
            if 'ALT' in df.columns and not pd.isna(row['ALT']):
                df.at[idx, 'MPN'] = row['ALT']
            # Do NOT use description to fill MPN

    # Save rows with missing MPNs before cleaning
    missing_mpn_df = df[df['MPN'].isna() | (df['MPN'].astype(str).str.strip() == '')].copy()

    # Clean and correct typos in MPN
    df['MPN'] = df['MPN'].apply(lambda x: correct_typos(x, KNOWN_PARTS))

    # Translate descriptions to English
    if 'DESC' in df.columns:
        df['DESC_EN'] = df['DESC'].apply(lambda x: translate_text(x, dest='en'))

    # Drop irrelevant rows (e.g., all NaN in MPN)
    cleaned_df = df[df['MPN'].notna() & (df['MPN'].astype(str).str.strip() != '')].reset_index(drop=True)
    return cleaned_df, missing_mpn_df

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Clean and standardize BOM files.')
    parser.add_argument('input', help='Path to BOM file (csv, xlsx, xls, pdf)')
    parser.add_argument('-o', '--output', help='Path to save cleaned BOM (csv)', default='cleaned_bom.csv')
    parser.add_argument('-m', '--missing', help='Path to save missing MPNs (csv)', default=None)
    args = parser.parse_args()

    print(f"Reading: {args.input}")
    df = read_bom(args.input)
    print(f"Initial columns: {list(df.columns)}")
    df_clean, df_missing = clean_bom(df)
    print(f"Cleaned columns: {list(df_clean.columns)}")
    df_clean.to_csv(args.output, index=False)
    print(f"Cleaned BOM saved to {args.output}")

    # Generate missingMPN file name if not specified
    if args.missing is None:
        base, ext = os.path.splitext(args.input)
        args.missing = f"{base}_missingMPN.csv"
    df_missing.to_csv(args.missing, index=False)
    print(f"Rows with missing MPN saved to {args.missing}")

# if __name__ == '__main__':
#     main() 

def start_cleaner(input_file, output_file='backend\\api\\clean_output\\cleaned_bom.csv', missing_file='backend\\api\\clean_output\\cleaned_missing_bom.csv'):
    """
    Start the BOM cleaner as a script.
    """


    print(f"Reading: {input_file}")
    df = read_bom(input_file)
    print(f"Initial columns: {list(df.columns)}")
    df_clean, df_missing = clean_bom(df)
    print(f"Cleaned columns: {list(df_clean.columns)}")
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    df_clean.to_csv(output_file, index=False)
    print(f"Cleaned BOM saved to {output_file}")

    # Generate missingMPN file name if not specified
    if missing_file is None:
        base, ext = os.path.splitext(input_file)
        missing_file = f"{base}_missingMPN.csv"
    df_missing.to_csv(missing_file, index=False)
    print(f"Rows with missing MPN saved to {missing_file}")
    return output_file, missing_file