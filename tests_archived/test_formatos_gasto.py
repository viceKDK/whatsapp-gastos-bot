#!/usr/bin/env python3
"""
Script para probar que ambos formatos de gasto se detecten correctamente
"""

import sys
from pathlib import Path

# Agregar el directorio del proyecto al path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.services.message_filter import get_message_filter


def test_expense_formats():
    """Prueba ambos formatos de gastos: cantidad-categoria y categoria-cantidad."""
    
    print("\n" + "="*70)
    print("PRUEBA DE FORMATOS DE GASTOS")
    print("="*70)
    
    # Inicializar filtro
    message_filter = get_message_filter()
    
    # Mensajes de prueba - AMBOS formatos
    test_messages = [
        # Formato: CANTIDAD + CATEGORIA
        "500 internet",
        "300 nafta", 
        "1200 comida",
        "150 transporte",
        "800 servicios",
        
        # Formato: CATEGORIA + CANTIDAD
        "internet 500",
        "nafta 300",
        "comida 1200", 
        "transporte 150",
        "servicios 800",
        
        # Otros formatos válidos
        "$600",
        "gasté 400",
        "compré 250",
        
        # Mensajes que NO son gastos
        "hola como estas",
        "ayuda",
        "estadisticas",
    ]
    
    print("\nPROBANDO DETECCIÓN DE GASTOS:")
    print("-" * 50)
    
    gastos_detectados = 0
    no_gastos_detectados = 0
    
    for i, mensaje in enumerate(test_messages, 1):
        print(f"\n{i:2d}. '{mensaje}'")
        
        # Probar si se detecta como gasto
        es_gasto = message_filter._looks_like_expense(mensaje.lower())
        
        if es_gasto:
            print(f"    OK GASTO DETECTADO")
            gastos_detectados += 1
        else:
            print(f"    XX NO detectado como gasto")
            no_gastos_detectados += 1
    
    # Análisis de resultados
    print("\n" + "="*70)
    print("ANÁLISIS DE RESULTADOS")
    print("="*70)
    
    # Contar cuántos deberían ser gastos vs no gastos
    mensajes_esperados_gastos = [
        "500 internet", "300 nafta", "1200 comida", "150 transporte", "800 servicios",
        "internet 500", "nafta 300", "comida 1200", "transporte 150", "servicios 800",
        "$600", "gasté 400", "compré 250"
    ]
    
    mensajes_esperados_no_gastos = [
        "hola como estas", "ayuda", "estadisticas"
    ]
    
    print(f"Mensajes esperados como gastos: {len(mensajes_esperados_gastos)}")
    print(f"Mensajes esperados como NO gastos: {len(mensajes_esperados_no_gastos)}")
    print(f"Gastos detectados: {gastos_detectados}")
    print(f"No gastos detectados: {no_gastos_detectados}")
    
    # Verificar específicamente los dos formatos principales
    print(f"\nVERIFICACIÓN DE FORMATOS ESPECÍFICOS:")
    print("-" * 40)
    
    formato1_ejemplos = ["500 internet", "300 nafta", "1200 comida"]
    formato2_ejemplos = ["internet 500", "nafta 300", "comida 1200"]
    
    formato1_exitosos = 0
    formato2_exitosos = 0
    
    print(f"\nFORMATO 1 (cantidad + categoría):")
    for msg in formato1_ejemplos:
        detectado = message_filter._looks_like_expense(msg.lower())
        estado = "OK" if detectado else "XX"
        print(f"  {estado} '{msg}' → {'DETECTADO' if detectado else 'NO DETECTADO'}")
        if detectado:
            formato1_exitosos += 1
    
    print(f"\nFORMATO 2 (categoría + cantidad):")
    for msg in formato2_ejemplos:
        detectado = message_filter._looks_like_expense(msg.lower())
        estado = "OK" if detectado else "XX"
        print(f"  {estado} '{msg}' → {'DETECTADO' if detectado else 'NO DETECTADO'}")
        if detectado:
            formato2_exitosos += 1
    
    # Resultado final
    print("\n" + "="*70)
    print("RESULTADO FINAL")
    print("="*70)
    
    ambos_formatos_funcionan = (formato1_exitosos == len(formato1_ejemplos) and 
                               formato2_exitosos == len(formato2_ejemplos))
    
    if ambos_formatos_funcionan:
        print("OK AMBOS FORMATOS FUNCIONAN CORRECTAMENTE")
        print(f"  - Formato 1 (cantidad + categoría): {formato1_exitosos}/{len(formato1_ejemplos)}")
        print(f"  - Formato 2 (categoría + cantidad): {formato2_exitosos}/{len(formato2_ejemplos)}")
        return True
    else:
        print("XX PROBLEMAS CON LA DETECCIÓN")
        print(f"  - Formato 1 (cantidad + categoría): {formato1_exitosos}/{len(formato1_ejemplos)}")
        print(f"  - Formato 2 (categoría + cantidad): {formato2_exitosos}/{len(formato2_ejemplos)}")
        return False


if __name__ == "__main__":
    try:
        print(">> Probando detección de formatos de gastos...")
        exito = test_expense_formats()
        
        if exito:
            print("\n>> OK DETECCIÓN FUNCIONANDO PARA AMBOS FORMATOS")
        else:
            print("\n>> XX DETECCIÓN NECESITA AJUSTES")
            
    except Exception as e:
        print(f"\n>> Error: {e}")
        import traceback
        traceback.print_exc()