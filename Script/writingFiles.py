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
    # Skip IVA when creating new file to avoid interactive prompt
    # Check if we're creating a new file (no existing structure would be present)
    create_new = not os.path.exists(file_path) or (os.path.exists(file_path) and xlrd.open_workbook(file_path).sheet_by_index(0).nrows <= 1)
    
    if create_new:
        # For new files, use IVA = False by default
        data = _apply_iva(data, interactive=False)
    else:
        # For existing files, apply IVA with user input
        data = _apply_iva(data, interactive=True)
    
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


def _calculate_total(data: list[dict[str, str]]) -> float:
    total = 0.0
    for row in data:
        try:
            precio = float(row.get('PRECIO', 0))
            cantidad = int(row.get('CANTIDAD', 0))
            total += precio * cantidad
        except (ValueError, TypeError):
            pass
    return total

def _apply_iva(data: list[dict[str, str]], interactive: bool = True) -> list[dict[str, str]]:
    total = _calculate_total(data)

    print(f'Total import: {total:.2f}')
    
    if interactive:
        answer = input('Apply IVA (21%)? 1=Yes, 0=No: ').strip()
    else:
        answer = '0'
        print('Creating new file - IVA will NOT be applied (confirmation skipped for automated operation)')

    if answer == '1':
        for row in data:
            try:
                precio = float(row.get('PRECIO', 0))
                row['PRECIO'] = f'{precio * 1.21:.2f}'
            except (ValueError, TypeError):
                pass

    return data


def _apply_iva_no_prompt(data: list[dict[str, str]]) -> list[dict[str, str]]:
    return _apply_iva(data, interactive=False)