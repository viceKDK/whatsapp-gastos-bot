#!/usr/bin/env python3
"""
Script de Prueba para Logs de Debug de Detección de Gastos

Prueba el sistema de detección con mensajes de ejemplo para verificar
que los logs de debug funcionen correctamente.
"""

import sys
from pathlib import Path
from datetime import datetime

# Agregar el directorio del proyecto al path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.services.interpretar_mensaje import InterpretarMensajeService
from app.services.message_filter import get_message_filter
from shared.logger import get_logger


def test_message_detection_with_debug():
    """Prueba la detección de mensajes con logs de debug completos."""
    
    # Configurar logger para modo debug
    logger = get_logger(__name__)
    logger.info("🧪 INICIANDO PRUEBA DE DETECCIÓN CON DEBUG LOGS")
    
    # Inicializar servicios
    interpretar_service = InterpretarMensajeService()
    message_filter = get_message_filter()
    
    # Mensajes de prueba - algunos deben detectarse, otros no
    test_messages = [
        # ✅ Mensajes que DEBERÍAN detectarse como gastos
        "500 nafta",
        "gasto: 1200 comida",
        "compré 300 super",
        "gasté 150 en transporte",
        "pagué 800 por ropa",
        "$250 pizza",
        "2000 pesos en tecnología",
        "150.50 café",
        
        # ❌ Mensajes que NO deberían detectarse como gastos
        "✅ Gasto registrado exitosamente",
        "🤖 Procesando mensaje...",
        "No puedo procesar ese mensaje",
        "Ayuda",
        "Hola como estás",
        "Registrado correctamente",
        "❌ Error en formato",
        "Mensaje del sistema: usuario se unió",
        
        # 🤔 Casos límite - pueden ir en cualquier dirección
        "500",  # Solo número
        "nafta 500",  # Orden invertido
        "Ayer gasté mucho dinero",  # Sin números específicos
    ]
    
    print("\n" + "="*80)
    print("INICIANDO PRUEBAS DE DETECCION DE GASTOS")
    print("="*80)
    
    resultados = {
        'filtrados': 0,
        'procesados': 0,
        'gastos_detectados': 0,
        'gastos_fallidos': 0
    }
    
    for i, mensaje in enumerate(test_messages, 1):
        print(f"\n{'='*10} PRUEBA {i}/{len(test_messages)} {'='*10}")
        print(f"MENSAJE: '{mensaje}'")
        print("-" * 50)
        
        # FASE 1: Prueba del filtro de mensajes
        logger.info(f"\n🔸 FASE 1: FILTRO DE MENSAJES - Prueba #{i}")
        debe_procesarse = message_filter.should_process_message(mensaje)
        
        if not debe_procesarse:
            print("XX RESULTADO: Mensaje FILTRADO (no se procesa)")
            resultados['filtrados'] += 1
            continue
        
        print("OK FILTRO: Mensaje APROBADO para procesamiento")
        resultados['procesados'] += 1
        
        # FASE 2: Prueba del interpretador de mensajes
        logger.info(f"\n🔸 FASE 2: INTERPRETADOR DE MENSAJES - Prueba #{i}")
        gasto = interpretar_service.procesar_mensaje(mensaje, datetime.now())
        
        if gasto:
            print(f"OK GASTO DETECTADO:")
            print(f"   Monto: ${gasto.monto}")
            print(f"   Categoria: {gasto.categoria}")
            if gasto.descripcion:
                print(f"   Descripcion: {gasto.descripcion}")
            print(f"   Fecha: {gasto.fecha}")
            resultados['gastos_detectados'] += 1
        else:
            print("XX NO SE DETECTO GASTO")
            resultados['gastos_fallidos'] += 1
    
    # Mostrar resumen final
    print("\n" + "="*80)
    print("RESUMEN DE RESULTADOS")
    print("="*80)
    print(f"Total mensajes probados: {len(test_messages)}")
    print(f"Mensajes filtrados: {resultados['filtrados']}")
    print(f"Mensajes procesados: {resultados['procesados']}")
    print(f"Gastos detectados: {resultados['gastos_detectados']}")
    print(f"Gastos no detectados: {resultados['gastos_fallidos']}")
    
    # Calcular tasas
    if resultados['procesados'] > 0:
        tasa_deteccion = (resultados['gastos_detectados'] / resultados['procesados']) * 100
        print(f"Tasa de deteccion: {tasa_deteccion:.1f}%")
    
    # Estadísticas del filtro
    filter_stats = message_filter.get_filter_stats()
    print(f"\nEstadisticas del filtro:")
    print(f"   - Total filtrados: {filter_stats['total_filtered']}")
    print(f"   - Por confirmacion: {filter_stats['confirmation_filtered']}")
    print(f"   - Por sistema: {filter_stats['system_filtered']}")
    print(f"   - Patrones cargados: {filter_stats['patterns_loaded']}")
    
    print("\nOK PRUEBA COMPLETADA")
    return resultados


def test_specific_patterns():
    """Prueba patrones específicos que pueden estar fallando."""
    
    logger = get_logger(__name__)
    logger.info("🎯 PRUEBA ESPECÍFICA DE PATRONES PROBLEMÁTICOS")
    
    interpretar_service = InterpretarMensajeService()
    
    # Casos específicos que pueden estar fallando
    casos_problematicos = [
        "500 nafta",  # Formato básico
        "1500 comida",  # Números más grandes
        "50.5 café",  # Decimales con punto
        "75,50 transporte",  # Decimales con coma (formato argentino)
        "gasto 200 super",  # Sin dos puntos
        "gasto: 300 ropa",  # Con dos puntos
        "compré 150 para casa",  # Verbo + para
        "gasté 800 en salud",  # Verbo + en
        "pagué 1200 por servicios",  # Verbo + por
        "$400 entretenimiento",  # Con símbolo peso
    ]
    
    print("\n" + "="*60)
    print("PRUEBA DE CASOS PROBLEMATICOS")
    print("="*60)
    
    for caso in casos_problematicos:
        print(f"\nPROBANDO: '{caso}'")
        gasto = interpretar_service.procesar_mensaje(caso)
        
        if gasto:
            print(f"   OK EXITO: ${gasto.monto} - {gasto.categoria}")
        else:
            print(f"   XX FALLO: No se detecto gasto")


if __name__ == "__main__":
    try:
        # Ejecutar pruebas
        print(">> Iniciando pruebas de debug de deteccion de gastos...")
        
        resultados = test_message_detection_with_debug()
        test_specific_patterns()
        
        print("\n>> TODAS LAS PRUEBAS COMPLETADAS")
        
    except KeyboardInterrupt:
        print("\n>> Prueba interrumpida por el usuario")
    except Exception as e:
        print(f"\n>> Error en las pruebas: {e}")
        import traceback
        traceback.print_exc()