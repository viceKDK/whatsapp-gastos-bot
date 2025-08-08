#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test del Filtro de Mensajes

Valida que los mensajes de confirmación sean filtrados correctamente.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from app.services.message_filter import MessageFilter


def test_message_filter():
    """Test del filtro de mensajes de confirmación."""
    print("[TEST] Filtro de Mensajes de Confirmacion")
    print("=" * 45)
    
    filter_instance = MessageFilter()
    
    # Mensajes que DEBEN ser filtrados (omitidos)
    messages_to_filter = [
        "gasto registrado",
        "no puedo procesar ese mensaje", 
        "gasto registrado exitosamente",
        "guardado correctamente",
        "procesando...",
        "espera un momento",
        "registro exitoso",
        "se guardo el gasto",
        "formato incorrecto",
        "mensaje no valido",
        "ayuda",
        "comandos disponibles",
        "analizando mensaje...",
        "entendido",
        "recibido"
    ]
    
    # Mensajes que NO deben ser filtrados (deben procesarse)
    messages_to_process = [
        "300 nafta",
        "250 carnicería", 
        "compré 150 comida",
        "gasté 200 en super",
        "pagué 75 otros",
        "$500 transporte",
        "gasto: 100 entretenimiento",
        "necesito registrar un gasto de 80 en salud"
    ]
    
    print("\n[FASE 1] Mensajes que DEBEN ser filtrados:")
    filtered_count = 0
    for i, message in enumerate(messages_to_filter, 1):
        should_process = filter_instance.should_process_message(message)
        if not should_process:
            print(f"  [OK] '{message}' -> FILTRADO correctamente")
            filtered_count += 1
        else:
            print(f"  [FAIL] '{message}' -> NO filtrado (ERROR)")
    
    filter_rate = (filtered_count / len(messages_to_filter)) * 100
    print(f"\nTasa de filtrado: {filtered_count}/{len(messages_to_filter)} ({filter_rate:.1f}%)")
    
    print(f"\n[FASE 2] Mensajes que NO deben ser filtrados:")
    processed_count = 0
    for i, message in enumerate(messages_to_process, 1):
        should_process = filter_instance.should_process_message(message)
        if should_process:
            print(f"  [OK] '{message}' -> PROCESADO correctamente")
            processed_count += 1
        else:
            print(f"  [FAIL] '{message}' -> FILTRADO incorrectamente (ERROR)")
    
    process_rate = (processed_count / len(messages_to_process)) * 100
    print(f"\nTasa de procesamiento: {processed_count}/{len(messages_to_process)} ({process_rate:.1f}%)")
    
    # Estadísticas del filtro
    stats = filter_instance.get_filter_stats()
    
    print(f"\n" + "=" * 45)
    print("[REPORTE] Filtro de Mensajes")
    print("=" * 45)
    
    total_messages = len(messages_to_filter) + len(messages_to_process)
    correct_decisions = filtered_count + processed_count
    accuracy = (correct_decisions / total_messages) * 100
    
    print(f"Mensajes probados: {total_messages}")
    print(f"Decisiones correctas: {correct_decisions}")
    print(f"Precision del filtro: {accuracy:.1f}%")
    
    print(f"\nEstadisticas del filtro:")
    print(f"  Total filtrado: {stats['total_filtered']}")
    print(f"  Confirmaciones: {stats['confirmation_filtered']}")
    print(f"  Sistema: {stats['system_filtered']}")
    print(f"  Patrones cargados: {stats['patterns_loaded']}")
    print(f"  Frases exactas: {stats['exact_phrases_loaded']}")
    
    if accuracy >= 90:
        print(f"\n[EXCELENTE] {accuracy:.1f}% precision - Filtro funcionando perfectamente")
        grade = "A+"
    elif accuracy >= 80:
        print(f"\n[MUY BUENO] {accuracy:.1f}% precision - Filtro funcionando bien")
        grade = "A"
    elif accuracy >= 70:
        print(f"\n[ACEPTABLE] {accuracy:.1f}% precision - Necesita ajustes menores")
        grade = "B"
    else:
        print(f"\n[PROBLEMA] {accuracy:.1f}% precision - Filtro necesita revision")
        grade = "C"
    
    print(f"Calificacion: {grade}")
    
    # Test adicional de casos edge
    print(f"\n[FASE 3] Casos Edge:")
    edge_cases = [
        ("", False, "texto vacio"),
        ("   ", False, "solo espacios"), 
        ("ok", False, "muy corto"),
        ("OK", False, "texto muy corto"),
        ("300", False, "solo numero"),
        ("300 ", True, "numero con espacio"),
        ("300 x", True, "numero con letra")
    ]
    
    edge_correct = 0
    for text, expected, description in edge_cases:
        result = filter_instance.should_process_message(text)
        if result == expected:
            print(f"  [OK] {description}: '{text}' -> {'PROCESAR' if result else 'FILTRAR'}")
            edge_correct += 1
        else:
            print(f"  [FAIL] {description}: '{text}' -> {'PROCESAR' if result else 'FILTRAR'} (esperado: {'PROCESAR' if expected else 'FILTRAR'})")
    
    edge_rate = (edge_correct / len(edge_cases)) * 100
    print(f"\nCasos edge: {edge_correct}/{len(edge_cases)} ({edge_rate:.1f}%)")
    
    # Resultado final
    final_accuracy = ((correct_decisions + edge_correct) / (total_messages + len(edge_cases))) * 100
    print(f"\n[PRECISION FINAL]: {final_accuracy:.1f}%")
    
    return final_accuracy


if __name__ == "__main__":
    accuracy = test_message_filter()
    
    # Exit code basado en precisión
    if accuracy >= 80:
        sys.exit(0)
    else:
        sys.exit(1)