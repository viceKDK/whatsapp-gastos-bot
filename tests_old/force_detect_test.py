#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Forzado de Detección

Intenta conectar con WhatsApp y fuerza la detección de mensajes nuevos.
"""

import sys
import time
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent))

from config.settings import get_settings
from infrastructure.whatsapp import WhatsAppEnhancedConnector
from app.services.message_processor import get_message_processor, MessageContent
from shared.logger import get_logger


def force_detect_messages():
    """Fuerza la detección de mensajes nuevos."""
    logger = get_logger(__name__)
    settings = get_settings()
    
    print("[FORCE TEST] Detección Forzada de Mensajes")
    print("=" * 50)
    
    try:
        # Crear connector
        print("1. Creando WhatsApp connector...")
        whatsapp_connector = WhatsAppEnhancedConnector(settings.whatsapp)
        
        # Intentar conectar
        print("2. Intentando conectar...")
        if not whatsapp_connector.connect():
            print("[X] ERROR: No se pudo conectar a WhatsApp")
            return False
        
        print("[OK] Conectado a WhatsApp")
        
        # Esperar un poco para que cargue
        print("3. Esperando carga completa...")
        time.sleep(3)
        
        # FORZAR obtención de mensajes SIN filtro de timestamp
        print("4. Obteniendo mensajes (TODOS)...")
        
        # Usar método básico que no filtra por timestamp
        all_messages = whatsapp_connector.get_new_messages()
        
        print(f"[OK] Encontrados {len(all_messages)} mensajes totales")
        
        # Mostrar últimos 5 mensajes
        if all_messages:
            print("\n[ULTIMOS 5 MENSAJES]")
            print("-" * 30)
            recent = all_messages[-5:]
            
            for i, (text, timestamp) in enumerate(recent, 1):
                print(f"{i}. {timestamp.strftime('%H:%M:%S')} - '{text[:50]}...'")
                
                # Buscar los mensajes específicos del usuario
                if any(keyword in text.lower() for keyword in ['pizza', 'super', 'carniceria', 'nafta']):
                    print(f"   [TARGET] MENSAJE OBJETIVO ENCONTRADO!")
                    
                    # Procesar este mensaje
                    processor = get_message_processor()
                    content = MessageContent(
                        text=text,
                        timestamp=timestamp,
                        message_type="text"
                    )
                    
                    result = processor.process_message(content)
                    if result.success and result.gasto:
                        print(f"   [EXPENSE] GASTO DETECTADO: ${result.gasto.monto} - {result.gasto.categoria}")
                    else:
                        print(f"   [X] NO SE DETECTO GASTO")
                        if result.errors:
                            print(f"      Errores: {result.errors}")
        
        else:
            print("[X] No se encontraron mensajes")
        
        # Desconectar
        print("\n5. Desconectando...")
        whatsapp_connector.disconnect()
        
        return True
        
    except Exception as e:
        logger.error(f"Error en force test: {e}")
        print(f"[X] ERROR: {e}")
        return False


if __name__ == "__main__":
    print("[!] IMPORTANTE: Este test requiere que WhatsApp Web este abierto")
    print("   y el chat 'Gastos' este disponible.\n")
    
    input("Presiona ENTER cuando WhatsApp Web esté listo...")
    
    success = force_detect_messages()
    
    if success:
        print("\n[OK] Test completado exitosamente")
    else:
        print("\n[X] Test fallo")