"""
Agregación de datos para el dashboard (por categoría y resúmenes).
"""

from typing import Any, Dict, List, Tuple


def aggregate_category_details(gastos) -> Dict[str, Any]:
    """Agrupa gastos por categoría y calcula estadísticas.

    Args:
        gastos: Iterable de gastos con atributos (categoria, monto).

    Returns:
        Dict con keys: categories, amounts, details, total_amount.
    """
    categoria_data: Dict[str, Dict[str, Any]] = {}
    for gasto in gastos:
        cat = gasto.categoria
        monto = float(gasto.monto)
        if cat not in categoria_data:
            categoria_data[cat] = {
                'total': 0.0,
                'count': 0,
                'promedio': 0.0,
                'max': 0.0,
                'min': float('inf'),
            }
        d = categoria_data[cat]
        d['total'] += monto
        d['count'] += 1
        d['max'] = max(d['max'], monto)
        d['min'] = min(d['min'], monto)

    total_amount = sum(d['total'] for d in categoria_data.values())
    for cat in categoria_data:
        d = categoria_data[cat]
        d['promedio'] = (d['total'] / d['count']) if d['count'] > 0 else 0.0
        d['porcentaje'] = (d['total'] / total_amount * 100) if total_amount > 0 else 0.0

    sorted_items: List[Tuple[str, Dict[str, Any]]] = sorted(
        categoria_data.items(), key=lambda x: x[1]['total'], reverse=True
    )

    categories = [k for k, _ in sorted_items]
    amounts = [v['total'] for _, v in sorted_items]
    details = [
        {
            'categoria': cat,
            'total': d['total'],
            'count': d['count'],
            'promedio': d['promedio'],
            'max': d['max'],
            'min': (0.0 if d['min'] == float('inf') else d['min']),
            'porcentaje': d['porcentaje'],
        }
        for cat, d in sorted_items
    ]

    return {
        'categories': categories,
        'amounts': amounts,
        'details': details,
        'total_amount': total_amount,
    }

