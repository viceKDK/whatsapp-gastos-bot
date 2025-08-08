#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug de Mensajes - Ver exactamente qué llega al filtro

Modificar temporalmente el filtro para mostrar todos los mensajes que recibe.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from app.services.message_filter import get_message_filter
from datetime import datetime

def debug_filter():
    """Debug específico del filtro de mensajes."""
    print("[DEBUG] Filtro de Mensajes")
    print("=" * 40)
    
    filter_service = get_message_filter()
    
    # Mensajes de prueba basados en los logs
    test_messages = [
        "14:44",  # Solo timestamp (como aparece en logs)
        "Vice: 250 carnicería",  # Mensaje completo
        "Vice: 500 pizza",
        "Vice: 250 súper", 
        "18:12",  # Solo timestamp
        "gasto registrado",  # Confirmación (debe filtrarse)
    ]
    
    print("Probando mensajes que podrían estar llegando al filtro:")
    
    for msg in test_messages:
        should_process = filter_service.should_process_message(msg, datetime.now())
        status = "[PROCESAR]" if should_process else "[FILTRAR]"
        print(f"  '{msg}' -> {status}")
        
        # Mostrar detalles del filtro para mensajes que se filtran
        if not should_process:
            print(f"    -> Razón: Mensaje filtrado por el sistema")

def check_expense_detection():
    """Verificar detección específica de gastos."""
    print(f"\n[DEBUG] Detección de Gastos")
    print("=" * 40)
    
    filter_service = get_message_filter()
    
    # Mensajes que DEFINITIVAMENTE deberían procesarse
    expense_messages = [
        "300 nafta",
        "250 carnicería", 
        "500 pizza",
        "250 súper",
        "100 comida",
        "50 café",
    ]
    
    print("Mensajes que DEBEN ser procesados como gastos:")
    
    for msg in expense_messages:
        should_process = filter_service.should_process_message(msg, datetime.now())
        
        # También probar el método interno de detección rápida
        looks_like_expense = filter_service._looks_like_expense(msg.lower())
        
        status = "[PROCESAR]" if should_process else "[FILTRAR]"
        expense_status = "[GASTO]" if looks_like_expense else "[NO GASTO]"
        
        print(f"  '{msg}' -> {status} {expense_status}")
        
        if not should_process:
            print(f"    [ERROR] Este mensaje debería procesarse!")

def simulate_bot_flow():
    """Simular el flujo completo del bot."""
    print(f"\n[DEBUG] Simulación Flujo del Bot")
    print("=" * 40)
    
    # Simular lo que el bot está detectando
    detected_messages = [
        ("14:44", datetime.now()),  # Solo timestamp (problema?)
        ("Vice: 250 carnicería", datetime.now()),  # Mensaje completo
        ("18:12", datetime.now()),  # Solo timestamp
        ("Vice: 500 pizza", datetime.now()),  # Mensaje completo
    ]
    
    filter_service = get_message_filter()
    
    print("Simulando procesamiento de mensajes detectados:")
    
    processed_count = 0
    filtered_count = 0
    
    for text, timestamp in detected_messages:
        should_process = filter_service.should_process_message(text, timestamp)
        
        if should_process:
            processed_count += 1
            print(f"  [OK] '{text}' -> PROCESADO")
        else:
            filtered_count += 1
            print(f"  [X] '{text}' -> FILTRADO")
    
    print(f"\nResumen: {processed_count} procesados, {filtered_count} filtrados")
    
    if filtered_count > processed_count:
        print("[PROBLEMA] Más mensajes filtrados que procesados!")
        print("El filtro puede estar siendo demasiado agresivo.")

if __name__ == "__main__":
    debug_filter()
    check_expense_detection() 
    simulate_bot_flow()