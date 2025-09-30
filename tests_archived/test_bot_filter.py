#!/usr/bin/env python3
"""
Script de Prueba del Filtro de Mensajes del Bot

Verifica que los mensajes del bot se filtren correctamente.
"""

import sys
from pathlib import Path

# Agregar el directorio del proyecto al path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.services.message_filter import get_message_filter
from shared.logger import get_logger


def test_bot_message_filtering():
    """Prueba específica para filtro de mensajes del bot."""
    
    logger = get_logger(__name__)
    logger.info("🧪 INICIANDO PRUEBA DE FILTRO DE MENSAJES DEL BOT")
    
    # Inicializar filtro
    message_filter = get_message_filter()
    
    # Mensajes que DEBERÍAN ser filtrados (mensajes del bot)
    mensajes_bot = [
        "[OK] Gasto registrado ($500 - supermercado) | Fecha: 07/08/2025",
        "[OK] Gasto registrado ($300 - transporte) | Fecha: 08/08/2025 | Desc: taxi",
        "[ERROR] No se pudo procesar el mensaje",
        "[INFO] Sistema iniciado",
        "Gasto registrado correctamente",
        "No pude procesar ese mensaje",
        "Usa el formato: $monto categoria descripcion",
        "registrado ($500 - categoria)",
    ]
    
    # Mensajes que NO deberían ser filtrados (mensajes del usuario)
    mensajes_usuario = [
        "500 nafta",
        "1200 comida",
        "compré 300 super",
        "gasté 150 transporte",
        "$250 pizza",
        "hola como estas",
        "ayuda",
        "estadisticas",
    ]
    
    print("\n" + "="*70)
    print("PRUEBA DE FILTRO DE MENSAJES DEL BOT")
    print("="*70)
    
    # Probar mensajes del bot - DEBERÍAN ser filtrados
    print("\nPROBANDO MENSAJES DEL BOT (deberian ser FILTRADOS):")
    print("-" * 60)
    
    filtrados_correctamente = 0
    for i, mensaje in enumerate(mensajes_bot, 1):
        print(f"\n{i}. '{mensaje}'")
        debe_procesarse = message_filter.should_process_message(mensaje)
        
        if not debe_procesarse:
            print("   OK CORRECTO: Mensaje FILTRADO")
            filtrados_correctamente += 1
        else:
            print("   XX ERROR: Mensaje NO filtrado (deberia haber sido filtrado)")
    
    print(f"\nResultado: {filtrados_correctamente}/{len(mensajes_bot)} mensajes del bot filtrados correctamente")
    
    # Probar mensajes del usuario - NO deberían ser filtrados
    print("\nPROBANDO MENSAJES DEL USUARIO (NO deberian ser filtrados):")
    print("-" * 60)
    
    pasaron_correctamente = 0
    for i, mensaje in enumerate(mensajes_usuario, 1):
        print(f"\n{i}. '{mensaje}'")
        debe_procesarse = message_filter.should_process_message(mensaje)
        
        if debe_procesarse:
            print("   OK CORRECTO: Mensaje PROCESADO")
            pasaron_correctamente += 1
        else:
            print("   XX ERROR: Mensaje FILTRADO (deberia haber pasado)")
    
    print(f"\nResultado: {pasaron_correctamente}/{len(mensajes_usuario)} mensajes del usuario pasaron correctamente")
    
    # Resumen
    print("\n" + "="*70)
    print("RESUMEN")
    print("="*70)
    print(f"Mensajes del bot filtrados: {filtrados_correctamente}/{len(mensajes_bot)} ({(filtrados_correctamente/len(mensajes_bot)*100):.1f}%)")
    print(f"Mensajes del usuario procesados: {pasaron_correctamente}/{len(mensajes_usuario)} ({(pasaron_correctamente/len(mensajes_usuario)*100):.1f}%)")
    
    # Éxito total
    exito_total = filtrados_correctamente == len(mensajes_bot) and pasaron_correctamente == len(mensajes_usuario)
    
    if exito_total:
        print("\nOK PRUEBA EXITOSA: El filtro funciona correctamente")
        print("   - Todos los mensajes del bot fueron filtrados")
        print("   - Todos los mensajes del usuario pasaron el filtro")
    else:
        print("\nXX PRUEBA CON PROBLEMAS: Revisar la logica del filtro")
        
        if filtrados_correctamente < len(mensajes_bot):
            print(f"   - {len(mensajes_bot) - filtrados_correctamente} mensajes del bot NO fueron filtrados")
            
        if pasaron_correctamente < len(mensajes_usuario):
            print(f"   - {len(mensajes_usuario) - pasaron_correctamente} mensajes del usuario fueron filtrados incorrectamente")
    
    return exito_total


if __name__ == "__main__":
    try:
        print(">> Iniciando prueba de filtro de mensajes del bot...")
        exito = test_bot_message_filtering()
        
        if exito:
            print("\n>> OK FILTRO FUNCIONANDO CORRECTAMENTE")
        else:
            print("\n>> XX FILTRO TIENE PROBLEMAS")
            
    except KeyboardInterrupt:
        print("\n>> Prueba interrumpida por el usuario")
    except Exception as e:
        print(f"\n>> Error en la prueba: {e}")
        import traceback
        traceback.print_exc()