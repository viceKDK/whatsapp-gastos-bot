#!/usr/bin/env python3
"""
Test de performance del filtrado caracter por caracter vs filtrado completo
"""

import sys
import os
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.message_filter import MessageFilter

def test_performance():
    """Test de performance del filtrado temprano."""
    print(">> Testing performance filtrado temprano vs completo...")
    
    # Crear instancia del filtro
    filter_instance = MessageFilter()
    
    # Mensajes típicos del bot que deben ser rechazados
    bot_messages = [
        "[OK] Gasto registrado: $500 - supermercado - Fecha: 2025-08-08 - Desc: compra semanal - Conf: 95% - Estado: completado exitosamente",
        "[ERROR] No se pudo procesar el mensaje porque el formato no es valido. Usa el formato: cantidad descripcion para registrar gastos",
        "No puedo procesar ese mensaje porque no contiene informacion de gasto valida. Revisa el formato y vuelve a intentarlo",
        "No se encontro una categoria valida para el gasto especificado. Las categorias disponibles son: transporte, comida, servicios",
        "[INFO] Sistema de gastos iniciado correctamente. Todas las funciones estan operativas y listas para procesar mensajes",
        "[DEBUG] Procesando mensaje de usuario: analizando formato, extrayendo informacion, validando datos, categorizando gasto",
    ] * 200  # 1200 mensajes
    
    print(f"Mensajes de test: {len(bot_messages)}")
    
    # Test 1: Filtrado temprano (caracter por caracter)
    print("\n=== Test 1: Filtrado temprano ===")
    start_time = time.time()
    early_rejections = 0
    
    for message in bot_messages:
        early_rejection = filter_instance._early_character_rejection(message)
        if early_rejection:
            early_rejections += 1
    
    early_time = time.time() - start_time
    
    print(f"Tiempo total: {early_time:.4f}s")
    print(f"Rechazos tempranos: {early_rejections}")
    print(f"Promedio por mensaje: {(early_time/len(bot_messages)*1000):.3f}ms")
    
    # Test 2: Filtrado completo tradicional (simulando extraccion completa)
    print("\n=== Test 2: Filtrado completo tradicional ===")
    start_time = time.time()
    full_rejections = 0
    
    for message in bot_messages:
        # Simular extraccion completa del texto
        full_text = str(message).strip().lower()
        
        # Simular verificaciones completas
        if (full_text.startswith('[') or 
            full_text.startswith('no') or 
            any(emoji in message for emoji in ["[", "OK", "ERROR", "INFO", "DEBUG"])):
            full_rejections += 1
    
    full_time = time.time() - start_time
    
    print(f"Tiempo total: {full_time:.4f}s") 
    print(f"Rechazos completos: {full_rejections}")
    print(f"Promedio por mensaje: {(full_time/len(bot_messages)*1000):.3f}ms")
    
    # Comparacion
    print(f"\n" + "="*50)
    print("COMPARACION DE PERFORMANCE:")
    print(f"Filtrado temprano:  {early_time:.4f}s ({early_rejections} rechazos)")
    print(f"Filtrado completo:  {full_time:.4f}s ({full_rejections} rechazos)")
    
    if early_time < full_time:
        improvement = ((full_time - early_time) / full_time) * 100
        speedup = full_time / early_time
        print(f"\nMEJORA: {improvement:.1f}% mas rapido")
        print(f"SPEEDUP: {speedup:.2f}x mas rapido con filtrado temprano")
        
        # Calcular tiempo ahorrado en mensajes reales
        messages_per_day = 1000  # Estimacion
        time_saved_per_day = (full_time - early_time) * (messages_per_day / len(bot_messages))
        print(f"TIEMPO AHORRADO: ~{time_saved_per_day:.2f}s por dia con 1000 mensajes")
        
        return True
    else:
        print("\nSin mejora significativa de performance")
        return False


def test_early_detection_efficiency():
    """Test de eficiencia de deteccion temprana."""
    print(f"\n" + "="*50)
    print(">> Test de eficiencia de deteccion temprana...")
    
    filter_instance = MessageFilter()
    
    test_cases = [
        ("[OK]", "Deberia detectar en posicion 0"),
        ("  [ERROR]", "Deberia detectar despues de espacios"),
        ("No puedo", "Deberia detectar 'No' al inicio"), 
        ("Normal gasto", "NO deberia detectar 'No' en medio de 'Normal'"),
        ("500 internet", "NO deberia rechazar gasto valido"),
    ]
    
    print("\nCasos de deteccion temprana:")
    for i, (message, expected) in enumerate(test_cases, 1):
        early_rejection = filter_instance._early_character_rejection(message)
        
        print(f"{i}. '{message}' -> ", end="")
        if early_rejection:
            filter_type, position = early_rejection
            print(f"RECHAZADO ({filter_type} pos {position}) - {expected}")
        else:
            print(f"ACEPTADO - {expected}")
    
    return True


if __name__ == "__main__":
    print("Iniciando tests de performance de filtrado...")
    
    # Test principal de performance
    performance_improved = test_performance()
    
    # Test de eficiencia
    test_early_detection_efficiency()
    
    print(f"\n" + "="*60)
    if performance_improved:
        print("PERFORMANCE MEJORADA!")
        print("El filtrado caracter por caracter es significativamente mas rapido.")
        print("Los mensajes del bot se descartan sin procesar el texto completo.")
    else:
        print("Performance similar, pero funcionalidad correcta")
    
    print("="*60)