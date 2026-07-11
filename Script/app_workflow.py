import sys
import json
import os
import tempfile
import pickle

import xlrd
import xlwt
import xlutils.copy
import pandas as pd

from readingFiles import read_excel, create_excel, write_excel, _calculate_total
from gemini_client import generate_with_tools
from prompts import MAIN_PROMPT


def action_process(source_path: str, name: str) -> dict:
    from readingFiles import _apply_iva as orig_apply_iva

    state = {"total": 0.0, "output_path": None, "data": None}

    def silent_apply_iva(data):
        state["total"] = _calculate_total(data)
        state["data"] = data
        return data

    import readingFiles as sfe
    sfe._apply_iva = silent_apply_iva

    prompt = f'{MAIN_PROMPT}\n\nSource file: {source_path}\nCompany name: {name}'
    try:
        result_text = generate_with_tools(prompt)
    finally:
        sfe._apply_iva = orig_apply_iva

    output_files = [f for f in os.listdir('.') if f.startswith(f"{name}_") and f.endswith('.xls')]
    if output_files:
        newest = max(output_files, key=os.path.getctime)
        state["output_path"] = os.path.abspath(newest)

    temp_data = tempfile.NamedTemporaryFile(delete=False, suffix='.pkl', mode='wb')
    pickle.dump({"data": state["data"], "output_path": state["output_path"], "name": name}, temp_data)
    temp_path = temp_data.name
    temp_data.close()

    return {
        "status": "iva_question" if state["total"] > 0 else "done",
        "total": state["total"],
        "temp_state": temp_path,
        "output_path": state["output_path"],
        "message": result_text,
    }


def action_apply_iva(temp_state_path: str, apply_iva: bool) -> dict:
    with open(temp_state_path, 'rb') as f:
        state = pickle.load(f)

    data = state["data"]
    output_path = state["output_path"]

    if apply_iva and data:
        import xlrd
        import xlutils.copy
        for row in data:
            try:
                precio = float(row.get('PRECIO', 0))
                row['PRECIO'] = f'{precio * 1.21:.2f}'
            except (ValueError, TypeError):
                pass

        if output_path and os.path.exists(output_path):
            rb = xlrd.open_workbook(output_path, formatting_info=True)
            wb = xlutils.copy.copy(rb)
            ws = wb.get_sheet(0)
            rb_sheet = rb.sheet_by_index(0)
            for row_idx, row in enumerate(data):
                ws.write(row_idx + 2, 0, row.get('EAN', ''))
                ws.write(row_idx + 2, 1, row.get('NOMBRE', ''))
                ws.write(row_idx + 2, 2, f"{float(row.get('PRECIO', 0)):.2f}" if row.get('PRECIO') else '')
                ws.write(row_idx + 2, 3, row.get('VACIO', ''))
                try:
                    ws.write(row_idx + 2, 4, int(row.get('CANTIDAD', 0)))
                except (ValueError, TypeError):
                    ws.write(row_idx + 2, 4, row.get('CANTIDAD', ''))
            wb.save(output_path)

    os.unlink(temp_state_path)

    return {
        "status": "done",
        "output_path": output_path,
    }


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"status": "error", "message": "No action specified"}))
        sys.exit(1)

    action = sys.argv[1]

    if action == "process":
        if len(sys.argv) < 4:
            print(json.dumps({"status": "error", "message": "Usage: process <source_path> <name>"}))
            sys.exit(1)
        result = action_process(sys.argv[2], sys.argv[3])
        print(json.dumps(result))

    elif action == "apply_iva":
        if len(sys.argv) < 4:
            print(json.dumps({"status": "error", "message": "Usage: apply_iva <temp_state_path> <1|0>"}))
            sys.exit(1)
        result = action_apply_iva(sys.argv[2], sys.argv[3] == "1")
        print(json.dumps(result))

    else:
        print(json.dumps({"status": "error", "message": f"Unknown action: {action}"}))
        sys.exit(1)


if __name__ == "__main__":
    main()
