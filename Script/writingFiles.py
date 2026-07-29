import os
import xlwt
import xlrd
import xlutils.copy

from creatingFile import _format_precio

def write_excel(file_path: str, data: list[dict[str, str]]) -> None:
    """
    Append rows to an existing .xls file, preserving the existing structure.
    If the file doesn't exist, create it with the expected structure and skip IVA prompting.

    Parameters:
    file_path (str): Path to the existing .xls file.
    data (list[dict[str, str]]): Rows as dicts with keys EAN, NOMBRE, PRECIO, CANTIDAD.
    """
    
    # Check if file exists
    if os.path.exists(file_path):
        rb = xlrd.open_workbook(file_path, formatting_info=True)
        wb = xlutils.copy.copy(rb)
        ws = wb.get_sheet(0)
        start_row = rb.sheet_by_index(0).nrows
    else:
        # Create new file if it doesn't exist
        wb = xlwt.Workbook()  # Use xlwt.Workbook for creating new files
        ws = wb.add_sheet('Sheet1')
        
        # Create headers row (row 1)
        headers = ['EAN', 'NOMBRE', 'PRECIO', 'VACIO', 'CANTIDAD']
        for col_idx, header in enumerate(headers):
            ws.write(1, col_idx, header)
        
        start_row = 2  # Data should start from row 3

    # Append data rows
    for row_idx, row in enumerate(data):
        ws.write(start_row + row_idx, 0, row.get('EAN', ''))
        ws.write(start_row + row_idx, 1, row.get('NOMBRE', ''))
        ws.write(start_row + row_idx, 2, _format_precio(row.get('PRECIO', '')))
        ws.write(start_row + row_idx, 3, row.get('VACIO', ''))
        try:
            ws.write(start_row + row_idx, 4, int(row.get('CANTIDAD', 0)))
        except (ValueError, TypeError):
            ws.write(start_row + row_idx, 4, row.get('CANTIDAD', ''))

    wb.save(file_path)

def _apply_iva(data: list[dict[str, str]], have_iva: bool) -> list[dict[str, str]]:
    if have_iva:
        for row in data:
            try:
                precio = float(row.get('PRECIO', 0))
                row['PRECIO'] = f'{precio * 1.21:.2f}'
            except (ValueError, TypeError):
                pass
    return data

