#!/usr/bin/env python3
"""
Script para encontrar y corregir gastos con timestamps futuros en Excel
"""

import sys
import os
from datetime import datetime, date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from infrastructure.storage.excel_writer import ExcelStorage

def check_future_gastos():
    """Encuentra gastos con timestamps futuros."""
    
    excel_storage = ExcelStorage('data/gastos.xlsx')
    
    # Obtener gastos de hoy
    today = date.today()
    gastos = excel_storage.obtener_gastos(today, today)
    
    print(f"Gastos de hoy ({today}):")
    now = datetime.now()
    
    future_gastos = []
    for i, gasto in enumerate(gastos):
        timestamp_str = gasto.fecha.strftime('%H:%M:%S')
        if gasto.fecha > now:
            future_gastos.append((i, gasto))
            print(f"  FUTURO {i+1}: {timestamp_str} - ${gasto.monto} - {gasto.categoria} - {gasto.descripcion}")
        else:
            print(f"  {i+1}: {timestamp_str} - ${gasto.monto} - {gasto.categoria} - {gasto.descripcion}")
    
    print(f"\nGastos futuros encontrados: {len(future_gastos)}")
    print(f"Hora actual: {now.strftime('%H:%M:%S')}")
    
    if future_gastos:
        print("\nESTOS GASTOS CAUSAN EL PROBLEMA DE PROCESAMIENTO INFINITO")
        print("Necesitan ser eliminados o corregidos manualmente en Excel")
        
        for i, gasto in future_gastos:
            print(f"  - Fila aprox {i+2} en Excel: {gasto.fecha} - ${gasto.monto} - {gasto.categoria}")

if __name__ == "__main__":
    check_future_gastos()