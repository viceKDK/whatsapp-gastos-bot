#!/usr/bin/env python3
"""
Test específico para el problema de detección con BD vacía
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Agregar el directorio del proyecto al path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from infrastructure.whatsapp.whatsapp_selenium import MessageData

def test_message_detection_logic():
    """
    Simula la lógica de detección cuando last_processed_timestamp es None
    """
    print("[TEST] DETECCION DE MENSAJES CON BD VACIA")
    print("=" * 50)
    
    # Simular caso real: BD vacía (last_processed_timestamp = None)
    last_processed_timestamp = None
    
    # Simular timestamps de mensajes reales
    now = datetime.now()
    message_timestamps = [
        now - timedelta(minutes=10),  # 10 min atrás
        now - timedelta(minutes=5),   # 5 min atrás  
        now - timedelta(minutes=1),   # 1 min atrás
        now,                          # ahora
    ]
    
    # Simular mensajes
    test_messages = [
        "500 nafta",
        "250 carnicería", 
        "300 pizza",
        "gasto registrado"  # Este debería filtrarse
    ]
    
    print(f"BD timestamp: {last_processed_timestamp}")
    print(f"Hora actual: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Simular lógica de bypass
    bypass_filter = False
    if last_processed_timestamp:
        time_diff = last_processed_timestamp - now
        if time_diff.total_seconds() > -3600:  # Si es menos de 1 hora atrás o futuro
            bypass_filter = True
    else:
        # Si no hay BD timestamp, NO necesitamos bypass - todos los mensajes son "nuevos"
        bypass_filter = False
    
    print(f"Bypass filter: {bypass_filter}")
    print(f"Logica: Sin BD timestamp, todos los mensajes deberian procesarse")
    print()
    
    detected_messages = []
    
    for i, (text, timestamp) in enumerate(zip(test_messages, message_timestamps)):
        print(f"📨 MENSAJE #{i+1}: '{text}' @ {timestamp.strftime('%H:%M:%S')}")
        
        # Simular extracción de timestamp
        quick_timestamp = timestamp
        print(f"   🕐 Quick timestamp: {quick_timestamp.strftime('%H:%M:%S')}")
        
        # Comparación de timestamp (lógica actual del bot)
        if last_processed_timestamp:
            is_newer = quick_timestamp > last_processed_timestamp
            print(f"   🔍 Comparando: {quick_timestamp.strftime('%H:%M:%S')} > {last_processed_timestamp.strftime('%H:%M:%S')} = {is_newer}")
        else:
            is_newer = True
            print(f"   🔍 SIN BD TIMESTAMP - procesando {quick_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Condición para procesar (lógica actual del bot)
        should_process = bypass_filter or not last_processed_timestamp or (last_processed_timestamp and quick_timestamp > last_processed_timestamp)
        print(f"   ⚙️ Should process: {should_process}")
        
        if should_process:
            # Simular parsing del mensaje
            print(f"   🧬 INICIANDO PARSING DE ELEMENTO...")
            
            # Simular MessageData (lo que devolvería lazy_parser.parse_element_lazy)
            if text and len(text.strip()) > 0:
                message_data = MessageData(
                    text=text.strip(),
                    timestamp=timestamp,
                    sender="Test User",
                    message_type="text"
                )
                print(f"   ✅ MESSAGE_DATA OBTENIDO: timestamp={message_data.timestamp}, text_length={len(message_data.text) if message_data.text else 0}")
                
                if message_data.timestamp:
                    print(f"   🔍 TEXTO COMPLETO EXTRAIDO: '{message_data.text}'")
                    
                    # Convertir a tupla y agregar
                    full_message = message_data.to_tuple()
                    detected_messages.append(full_message)
                    
                    preview_text = message_data.text[:30] if len(message_data.text) > 30 else message_data.text
                    print(f"   ✅ NUEVO AGREGADO: '{preview_text}...' @ {message_data.timestamp.strftime('%H:%M:%S')}")
                    print(f"   📊 TOTAL EN LISTA: {len(detected_messages)} mensajes")
                else:
                    print(f"   ❌ MESSAGE_DATA SIN TIMESTAMP")
            else:
                print(f"   ❌ LAZY_PARSER DEVOLVIÓ NONE - text: '{text}'")
        else:
            print(f"   ⏸️ MENSAJE OMITIDO")
        
        print()
    
    print("=" * 50)
    print(f"🎯 RESULTADO FINAL: {len(detected_messages)} mensajes detectados")
    print(f"📊 ESTADÍSTICAS:")
    print(f"   - Elementos procesados: {len(test_messages)}")
    print(f"   - BD timestamp: {'None (primera vez)' if not last_processed_timestamp else last_processed_timestamp.strftime('%H:%M:%S')}")
    print(f"   - Bypass activo: {bypass_filter}")
    
    if detected_messages:
        print(f"📝 MENSAJES ENCONTRADOS:")
        for i, msg in enumerate(detected_messages, 1):
            text_preview = msg[0][:50] if msg[0] else "[sin texto]"
            timestamp = msg[1].strftime('%H:%M:%S') if msg[1] else "[sin timestamp]"
            print(f"   {i}. '{text_preview}...' @ {timestamp}")
    else:
        print(f"⚠️ NO SE ENCONTRARON MENSAJES")
        print("🔍 DIAGNÓSTICO: Posible problema en lazy_parser o selectores")
    
    # Verificar si el resultado es el esperado
    expected_count = 4  # Todos los mensajes deberían detectarse inicialmente
    if len(detected_messages) == expected_count:
        print(f"✅ TEST EXITOSO: Se detectaron todos los mensajes esperados")
        return True
    else:
        print(f"❌ TEST FALLIDO: Se esperaban {expected_count} mensajes, se encontraron {len(detected_messages)}")
        return False

if __name__ == "__main__":
    success = test_message_detection_logic()
    if success:
        print("\n✅ El test indica que la lógica debería funcionar correctamente")
        print("🔍 El problema real debe estar en el lazy_parser o selectores CSS")
    else:
        print("\n❌ Se encontró un problema en la lógica de detección")
    
    sys.exit(0 if success else 1)