def _calculate_total(data: list[dict[str, str]]) -> float:
    total = 0.0
    for row in data:
        try:
            precio = float(str(row.get('PRECIO', 0)).replace(',', '.'))
            cantidad = int(str(row.get('CANTIDAD', 0)).replace(',', '.'))
            total += precio * cantidad
        except (ValueError, TypeError):
            pass
    return total
