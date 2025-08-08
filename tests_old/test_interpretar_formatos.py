#!/usr/bin/env python3
"""
Script para probar que el intérprete de mensajes funciona con ambos formatos
"""

import sys
from pathlib import Path
from datetime import datetime

# Agregar el directorio del proyecto al path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.services.interpretar_mensaje import InterpretarMensajeService


def test_interpreter_formats():
    """Prueba que el intérprete procese ambos formatos correctamente."""
    
    print("\n" + "="*70)
    print("PRUEBA DE INTÉRPRETE - AMBOS FORMATOS")
    print("="*70)
    
    # Inicializar servicio
    interpreter = InterpretarMensajeService()
    
    # Casos de prueba
    test_cases = [
        # Formato 1: cantidad + categoría (debería funcionar)
        ("500 internet", 500, "internet"),
        ("300 nafta", 300, "nafta"),
        ("1200 comida", 1200, "comida"),
        
        # Formato 2: categoría + cantidad (nuevo - debe funcionar ahora)
        ("internet 500", 500, "internet"), 
        ("nafta 300", 300, "nafta"),
        ("comida 1200", 1200, "comida"),
        
        # Otros formatos que ya funcionaban
        ("$600", 600, ""),
        ("gasté 400 comida", 400, "comida"),
    ]
    
    print("\nPROCESANDO MENSAJES:")
    print("-" * 50)
    
    exitosos = 0
    fallidos = 0
    
    for i, (mensaje, monto_esperado, categoria_esperada) in enumerate(test_cases, 1):
        print(f"\n{i}. PROBANDO: '{mensaje}'")
        
        # Procesar mensaje
        try:
            gasto = interpreter.procesar_mensaje(mensaje, datetime.now())
            
            if gasto:
                print(f"   OK GASTO DETECTADO:")
                print(f"      Monto: ${gasto.monto} (esperado: ${monto_esperado})")
                print(f"      Categoria: '{gasto.categoria}' (esperada: '{categoria_esperada}')")
                
                # Verificar que el monto sea correcto
                if float(gasto.monto) == monto_esperado:
                    print(f"   OK MONTO CORRECTO")
                    exitosos += 1
                else:
                    print(f"   XX MONTO INCORRECTO")
                    fallidos += 1
            else:
                print(f"   XX NO SE DETECTÓ GASTO")
                fallidos += 1
                
        except Exception as e:
            print(f"   XX ERROR: {e}")
            fallidos += 1
    
    # Resumen
    print("\n" + "="*70)
    print("RESUMEN")
    print("="*70)
    print(f"Total casos: {len(test_cases)}")
    print(f"Exitosos: {exitosos}")
    print(f"Fallidos: {fallidos}")
    print(f"Tasa de éxito: {(exitosos/len(test_cases)*100):.1f}%")
    
    # Verificar específicamente los casos problemáticos
    print(f"\nCASOS CRÍTICOS:")
    print("-" * 30)
    
    casos_criticos = [
        "internet 500",
        "500 internet", 
        "nafta 300",
        "300 nafta"
    ]
    
    criticos_exitosos = 0
    for caso in casos_criticos:
        try:
            gasto = interpreter.procesar_mensaje(caso, datetime.now())
            if gasto:
                print(f"OK '{caso}' → ${gasto.monto} - {gasto.categoria}")
                criticos_exitosos += 1
            else:
                print(f"XX '{caso}' → NO detectado")
        except Exception as e:
            print(f"XX '{caso}' → ERROR: {e}")
    
    # Resultado final
    exito_total = (exitosos == len(test_cases) and criticos_exitosos == len(casos_criticos))
    
    if exito_total:
        print(f"\nOK INTÉRPRETE FUNCIONANDO PERFECTAMENTE")
        print(f"   - Todos los formatos procesados correctamente")
        print(f"   - Casos críticos: {criticos_exitosos}/{len(casos_criticos)}")
        return True
    else:
        print(f"\nXX INTÉRPRETE NECESITA AJUSTES")
        print(f"   - Casos críticos: {criticos_exitosos}/{len(casos_criticos)}")
        return False


if __name__ == "__main__":
    try:
        print(">> Probando intérprete con ambos formatos...")
        exito = test_interpreter_formats()
        
        if exito:
            print("\n>> OK INTÉRPRETE FUNCIONANDO PARA AMBOS FORMATOS")
        else:
            print("\n>> XX INTÉRPRETE NECESITA CORRECCIONES")
            
    except Exception as e:
        print(f"\n>> Error: {e}")
        import traceback
        traceback.print_exc()