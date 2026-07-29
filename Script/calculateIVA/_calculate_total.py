def _calculate_total(data: list[dict[str, str]]) -> float:
    total = 0.0
    for row in data:
        try:
            precio = float(str(row.get('PRECIO', 0)).replace(',', '.'))
            cantidad = int(str(row.get('CANTIDAD', 0)).replace(',', '.'))
            total += round(precio * cantidad, 2)
        except (ValueError, TypeError):
            pass
    return round(total, 2)
