import os
import xlwt
import datetime
def create_excel(name: str, data: list[dict[str, str]]) -> str:
    """
    Create an .xls file with a timestamped filename and return the path.

    Structure: row 0 blank, row 1 has [EAN, NOMBRE, PRECIO, (empty), CANTIDAD],
    data starts from row 2. The dict keys expected: 'EAN', 'NOMBRE', 'PRECIO', 'CANTIDAD'.

    Parameters:
    name (str): Base name for the file (e.g. 'report').
    data (list[dict[str, str]]): Rows as dicts with keys EAN, NOMBRE, PRECIO, CANTIDAD.

    Returns:
    str: The full path of the created file.
    """
    now = datetime.now()
    filename = f"{name}_{now.strftime('%d%m%y')}.xls"

    wb = xlwt.Workbook()
    ws = wb.add_sheet('Sheet1')

    headers = ['EAN', 'NOMBRE', 'PRECIO', 'VACIO', 'CANTIDAD']
    for col_idx, header in enumerate(headers):
        ws.write(1, col_idx, header)

    for row_idx, row in enumerate(data):
        ws.write(row_idx + 2, 0, row.get('EAN', ''))
        ws.write(row_idx + 2, 1, row.get('NOMBRE', ''))
        ws.write(row_idx + 2, 2, _format_precio(row.get('PRECIO', '')))
        ws.write(row_idx + 2, 3, row.get('VACIO', ''))
        try:
            ws.write(row_idx + 2, 4, int(row.get('CANTIDAD', 0)))
        except (ValueError, TypeError):
            ws.write(row_idx + 2, 4, row.get('CANTIDAD', ''))

    wb.save(filename)
    return os.path.abspath(filename)

def _format_precio(value: str) -> str:
    try:
        return f"{float(value):.2f}"
    except (ValueError, TypeError):
        return value
