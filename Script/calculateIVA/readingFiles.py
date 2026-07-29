import os
from typing import Any
import pandas as pd

def read_excel(file_path: str) -> list[dict[str, Any]]:
    """
    Read a single file or an entire directory, detect the file types by binary 
    signatures, and return a unified, JSON-sanitized list of dictionaries.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The specified path does not exist: {file_path}")
    
    all_dataframes: list[pd.DataFrame] = []
    
    # --- Case 1: Single File Processing ---
    if os.path.isfile(file_path):
        detected_type = _detect_file_type(file_path)
        df = _analyzing_file(detected_type, file_path)
        return _sanitize_dataframe(df)

    # --- Case 2: Directory Processing ---
    # Expanded extension support to match your parser capabilities
    SUPPORTED_EXTENSIONS = ('.xls', '.xlsx', '.csv', '.html', '.htm')
    
    for file in os.listdir(file_path):
        if file.startswith('.'):  # Skip hidden files (like .DS_Store)
            continue
            
        if file.lower().endswith(SUPPORTED_EXTENSIONS):
            aux_path = os.path.join(file_path, file)
            try:
                detected_type = _detect_file_type(aux_path)
                df = _analyzing_file(detected_type, aux_path)
                all_dataframes.append(df)
            except Exception as e:
                print(f"Warning: Skipping file {file} due to error: {e}")

    # Guard against an empty directory or no readable files
    if not all_dataframes:
        return []
        
    # Merge all extracted dataframes into a single dataset
    combined_df = pd.concat(all_dataframes, ignore_index=True)
    return _sanitize_dataframe(combined_df)


def _detect_file_type(file_path: str) -> str:
    """Detect the actual content type of the file based on its binary signature."""
    with open(file_path, 'rb') as f:
        header = f.read(8)
    
    if header.startswith(b'\xd0\xcf\x11\xe0'):
        return 'xls'
    elif header.startswith(b'PK\x03\x04'):
        return 'xlsx'
    
    # Fallback: check text context for HTML or CSV delimeters
    with open(file_path, 'rb') as f:
        header_text = f.read(500).lower()

    if b'<html' in header_text or b'<!doctype html' in header_text or b'<table' in header_text:
        return "html"
    elif b';' in header_text:
        return ";"
    elif b',' in header_text:
        return ","
        
    return "unknown"


def _analyzing_file(detected_type: str, file: str) -> pd.DataFrame:
    """Parse the file using the appropriate Pandas engine based on signature."""
    match detected_type:
        case 'xls':
            return pd.read_excel(file, engine='xlrd')
        case 'xlsx':
            return pd.read_excel(file, engine='openpyxl')
        case 'html':
            # read_html returns a list of dataframes; extract the primary data table
            dfs = pd.read_html(file)
            if not dfs:
                raise ValueError(f"No HTML tables found in {file}")
            return dfs[0]
        case ',' | ';':
            return pd.read_csv(file, sep=detected_type)
        case _:
            raise ValueError(f"Unsupported binary file type: {detected_type}")


def _sanitize_dataframe(df: pd.DataFrame) -> list[dict[str, Any]]:
    """
    CRITICAL FOR GEMINI TOOL CALLING: 
    Converts a DataFrame into standard Python dictionaries, replacing any 
    float('nan') values with Python None so it translates cleanly to valid JSON nulls.
    """
    records = df.to_dict(orient='records')
    return [
        {k: (None if pd.isna(v) else v) for k, v in record.items()}
        for record in records
    ]







