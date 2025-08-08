#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test de Detección de Gastos

Prueba la detección correcta de gastos simples como "300 nafta" y "250 carnicería"
"""

import sys
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent))

from app.services.interpretar_mensaje import InterpretarMensajeService
from app.services.message_processor import AdvancedMessageProcessor, MessageContent


def test_simple_expense_detection():
    """Test de detección de gastos simples."""
    print("[TEST] Detección de Gastos Simples")
    print("=" * 40)
    
    # Crear interpretador
    interpreter = InterpretarMensajeService()
    
    # Casos de prueba simples
    test_cases = [
        "300 nafta",
        "250 carnicería", 
        "150 comida",
        "500 super",
        "compré 200 transporte",
        "gasté 100 entretenimiento",
        "pagué 75 otros"
    ]
    
    results = {}
    
    for i, test_message in enumerate(test_cases, 1):
        print(f"\n[{i}] Probando: '{test_message}'")
        
        try:
            # Procesar con interpreter directo
            gasto = interpreter.procesar_mensaje(test_message)
            
            if gasto:
                print(f"    [OK] DETECTADO: ${gasto.monto} - {gasto.categoria}")
                print(f"       Descripcion: '{gasto.descripcion}'")
                results[test_message] = {
                    'detected': True,
                    'amount': gasto.monto,
                    'category': gasto.categoria,
                    'description': gasto.descripcion
                }
            else:
                print(f"    [FAIL] NO DETECTADO")
                results[test_message] = {'detected': False}
                
        except Exception as e:
            print(f"    [ERROR] ERROR: {e}")
            results[test_message] = {'detected': False, 'error': str(e)}
    
    # Probar también con procesador avanzado
    print(f"\n" + "=" * 40)
    print("[TEST] Procesador Avanzado")
    print("=" * 40)
    
    processor = AdvancedMessageProcessor()
    
    for i, test_message in enumerate(test_cases, 1):
        print(f"\n[{i}] Probando con procesador: '{test_message}'")
        
        try:
            content = MessageContent(
                text=test_message,
                timestamp=datetime.now(),
                message_type="text"
            )
            
            result = processor.process_message(content)
            
            if result.success and result.gasto:
                print(f"    [OK] PROCESADOR OK: ${result.gasto.monto} - {result.gasto.categoria}")
                print(f"       Confianza: {result.confidence:.2f}")
            else:
                print(f"    [FAIL] PROCESADOR FALLO")
                if result.errors:
                    print(f"       Errores: {result.errors}")
                
        except Exception as e:
            print(f"    [ERROR] ERROR PROCESADOR: {e}")
    
    # Reporte final
    print(f"\n" + "=" * 40)
    print("[REPORTE] Detección de Gastos")
    print("=" * 40)
    
    detected_count = sum(1 for r in results.values() if r.get('detected', False))
    total_tests = len(results)
    success_rate = (detected_count / total_tests) * 100
    
    print(f"Tests ejecutados: {total_tests}")
    print(f"Gastos detectados: {detected_count}")
    print(f"Tasa de éxito: {success_rate:.1f}%")
    
    print(f"\nResultados detallados:")
    for message, result in results.items():
        if result.get('detected'):
            print(f"  [OK] '{message}' -> ${result['amount']} - {result['category']}")
        else:
            error = result.get('error', 'No detectado')
            print(f"  [FAIL] '{message}' -> {error}")
    
    if success_rate >= 80:
        print(f"\n[EXCELENTE] {success_rate:.1f}% de deteccion exitosa")
    elif success_rate >= 60:
        print(f"\n[ACEPTABLE] {success_rate:.1f}% de deteccion")
    else:
        print(f"\n[PROBLEMA] Solo {success_rate:.1f}% de deteccion")
    
    return success_rate


def test_regex_patterns():
    """Test específico de patrones regex."""
    print(f"\n" + "=" * 40)
    print("[TEST] Patrones Regex Específicos")
    print("=" * 40)
    
    from app.services.interpretar_mensaje import OptimizedRegexEngine
    
    regex_engine = OptimizedRegexEngine()
    
    test_messages = [
        "300 nafta",
        "250 carnicería",
        "compré 200 comida",
        "$150 super",
        "gasto: 100 otros"
    ]
    
    print("Probando motor regex optimizado:")
    for msg in test_messages:
        result = regex_engine.extract_fast(msg)
        if result:
            print(f"  [OK] '{msg}' -> {result['monto']} | '{result['descripcion']}'")
        else:
            print(f"  [FAIL] '{msg}' -> No match")


if __name__ == "__main__":
    success_rate = test_simple_expense_detection()
    test_regex_patterns()
    
    # Exit code basado en tasa de éxito
    if success_rate >= 80:
        sys.exit(0)
    else:
        sys.exit(1)