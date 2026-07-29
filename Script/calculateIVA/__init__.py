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
