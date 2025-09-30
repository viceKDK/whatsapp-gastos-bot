#!/usr/bin/env python3
"""
Script para probar que mensajes con [ se filtran inmediatamente
"""

import sys
from pathlib import Path

# Agregar el directorio del proyecto al path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.services.message_filter import get_message_filter


def test_simple_bracket_filter():
    """Prueba que mensajes con [ se filtran inmediatamente."""
    
    print("\n" + "="*60)
    print("PRUEBA FILTRO SIMPLE - MENSAJES CON [")
    print("="*60)
    
    # Inicializar filtro
    message_filter = get_message_filter()
    
    # Mensajes que deben ser FILTRADOS (ignorados)
    mensajes_filtrar = [
        "[OK] Gasto registrado ($500 - supermercado) | Fecha: 07/08/2025",
        "[ERROR] No se pudo procesar",
        "[INFO] Sistema iniciado", 
        "[ cualquier cosa que empiece con [",
        "  [OK] incluso con espacios al inicio",
    ]
    
    # Mensajes que deben PASAR (procesarse)
    mensajes_pasar = [
        "500 nafta",
        "1200 comida", 
        "gaste 300 transporte",
        "ayuda",
        "estadisticas",
        "hola como estas",
    ]
    
    print("\n1. MENSAJES QUE DEBEN SER FILTRADOS:")
    print("-" * 50)
    
    todos_filtrados = True
    for i, mensaje in enumerate(mensajes_filtrar, 1):
        debe_procesarse = message_filter.should_process_message(mensaje)
        resultado = "FILTRADO" if not debe_procesarse else "NO FILTRADO"
        estado = "OK" if not debe_procesarse else "XX ERROR"
        
        print(f"{i}. '{mensaje[:50]}...'")
        print(f"   {estado} - {resultado}")
        
        if debe_procesarse:
            todos_filtrados = False
    
    print(f"\nRESULTADO: {len(mensajes_filtrar)} mensajes - {'TODOS FILTRADOS' if todos_filtrados else 'ALGUNOS NO FILTRADOS'}")
    
    print("\n2. MENSAJES QUE DEBEN PASAR:")
    print("-" * 50)
    
    todos_pasaron = True
    for i, mensaje in enumerate(mensajes_pasar, 1):
        debe_procesarse = message_filter.should_process_message(mensaje)
        resultado = "PROCESADO" if debe_procesarse else "FILTRADO"
        estado = "OK" if debe_procesarse else "XX ERROR"
        
        print(f"{i}. '{mensaje}'")
        print(f"   {estado} - {resultado}")
        
        if not debe_procesarse:
            todos_pasaron = False
    
    print(f"\nRESULTADO: {len(mensajes_pasar)} mensajes - {'TODOS PASARON' if todos_pasaron else 'ALGUNOS FUERON FILTRADOS'}")
    
    # Resumen final
    print("\n" + "="*60)
    print("RESUMEN FINAL")
    print("="*60)
    
    if todos_filtrados and todos_pasaron:
        print("OK FILTRO FUNCIONANDO PERFECTAMENTE")
        print("- Todos los mensajes con [ fueron filtrados")
        print("- Todos los mensajes normales pasaron")
        return True
    else:
        print("XX FILTRO TIENE PROBLEMAS")
        if not todos_filtrados:
            print("- Algunos mensajes con [ NO fueron filtrados")
        if not todos_pasaron:
            print("- Algunos mensajes normales fueron filtrados incorrectamente")
        return False


if __name__ == "__main__":
    try:
        print(">> Iniciando prueba de filtro simple...")
        exito = test_simple_bracket_filter()
        
        if exito:
            print("\n>> OK FILTRO FUNCIONA CORRECTAMENTE")
        else:
            print("\n>> XX FILTRO NECESITA AJUSTES")
            
    except Exception as e:
        print(f"\n>> Error: {e}")
        import traceback
        traceback.print_exc()