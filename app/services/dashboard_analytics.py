"""
Servicios de análisis y métricas para el dashboard.

Funciones utilitarias separadas para mantener el proveedor de datos liviano.
"""

from typing import Dict, List


def moving_average(values: List[float], window: int = 7) -> List[float]:
    """Calcula promedio móvil simple sobre una lista de valores.

    Args:
        values: Serie de valores.
        window: Tamaño de ventana (por defecto 7).

    Returns:
        Lista con el promedio móvil para cada posición.
    """
    if window <= 1:
        return values[:]
    out: List[float] = []
    for i in range(len(values)):
        start = max(0, i - window + 1)
        seg = values[start : i + 1]
        out.append(sum(seg) / len(seg) if seg else 0.0)
    return out

