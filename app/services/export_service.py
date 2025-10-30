"""
Servicio de exportación de datos del dashboard.
"""

from typing import List, Dict


def rows_to_csv(rows: List[Dict]) -> str:
    """Convierte una lista de filas (dicts) a CSV.

    Nota: implementación simple sin dependencias externas.
    """
    if not rows:
        return "id,fecha,hora,monto,categoria,descripcion\n"

    headers = ['id', 'fecha', 'hora', 'monto', 'categoria', 'descripcion']
    out = [','.join(headers)]

    for r in rows:
        vals = [
            '' if r.get('id') is None else str(r.get('id')),
            str(r.get('fecha', '')),
            str(r.get('hora', '')),
            f"{float(r.get('monto', 0.0)):.2f}",
            str(r.get('categoria', '')),
            str(r.get('descripcion', '') or ''),
        ]
        # Escapar comillas y envolver con comillas si hay separadores
        esc = []
        for v in vals:
            vv = v.replace('"', '""')
            if (',' in vv) or ('"' in v) or (vv.strip() != vv):
                vv = f'"{vv}"'
            esc.append(vv)
        out.append(','.join(esc))

    return '\n'.join(out)

