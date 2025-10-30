"""Script para poblar datos de prueba en el dashboard (Excel).

Genera gastos aleatorios en los últimos N días para pruebas del dashboard.
"""

from pathlib import Path
from datetime import datetime, timedelta
from decimal import Decimal
import random

from domain.models.gasto import Gasto

try:
    from infrastructure.storage.excel_writer import ExcelStorage
except Exception as e:
    print("ERROR: openpyxl requerido para generar datos en Excel.")
    print("Instala dependencias: pip install openpyxl")
    raise


CATEGORIAS = [
    'comida', 'transporte', 'entretenimiento', 'salud', 'servicios',
    'ropa', 'educacion', 'hogar', 'super', 'nafta', 'otros'
]

DESCRIPCIONES = {
    'comida': ['Almuerzo', 'Cena', 'Desayuno', 'Snacks', 'Cafe'],
    'transporte': ['Uber', 'Taxi', 'Nafta', 'Estacionamiento', 'Peaje'],
    'entretenimiento': ['Cine', 'Streaming', 'Juegos', 'Salidas'],
    'salud': ['Farmacia', 'Medico', 'Gimnasio'],
    'super': ['Mercado', 'Almacen', 'Verduleria'],
}


def generate_test_gastos(num_dias=60, gastos_por_dia=3):
    gastos = []
    now = datetime.now()
    for i in range(num_dias):
        fecha_base = now - timedelta(days=i)
        for _ in range(random.randint(1, gastos_por_dia)):
            categoria = random.choice(CATEGORIAS)
            monto = Decimal(str(round(random.uniform(50, 5000), 2)))
            hora = random.randint(7, 22)
            minuto = random.randint(0, 59)
            fecha = fecha_base.replace(hour=hora, minute=minuto, second=0, microsecond=0)
            if categoria in DESCRIPCIONES:
                descripcion = random.choice(DESCRIPCIONES[categoria])
            else:
                descripcion = f"Gasto {categoria}"
            gastos.append(Gasto(monto=monto, categoria=categoria, fecha=fecha, descripcion=descripcion))
    return gastos


def main():
    excel_path = Path('data/gastos.xlsx')
    storage = ExcelStorage(str(excel_path))

    gastos = generate_test_gastos(num_dias=60, gastos_por_dia=4)
    print(f"Guardando {len(gastos)} gastos en {excel_path}...")
    ok = 0
    for g in gastos:
        if storage.guardar_gasto(g):
            ok += 1
    print(f"Listo. {ok} gastos guardados.")


if __name__ == '__main__':
    main()

