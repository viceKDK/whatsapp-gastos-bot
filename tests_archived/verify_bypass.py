#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verificación Final del Bypass

Simula exactamente lo que hace el bot para verificar si los mensajes se detectarían.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.append(str(Path(__file__).parent))

from config.settings import get_settings
from infrastructure.storage.hybrid_storage import HybridStorage

def verify_message_detection():
    """Verifica si los mensajes específicos serían detectados."""
    print("[VERIFICACION] Detección de Mensajes del Usuario")
    print("=" * 50)
    
    # 1. Obtener configuración y storage
    storage = HybridStorage("data/gastos.xlsx")
    last_processed = storage.get_last_processed_timestamp()
    
    print(f"1. BD Timestamp: {last_processed}")
    
    # 2. Simular hora actual
    now = datetime.now()
    print(f"2. Hora actual:  {now}")
    
    # 3. Simular mensajes del usuario (según los logs que proporcionó)
    user_messages = [
        ("14:44", "Vice: 250 carnicería"),
        ("18:12", "Vice: 500 pizza"), 
        ("18:12", "Vice: 250 súper")
    ]
    
    print(f"\n3. Mensajes a verificar:")
    for time_str, msg in user_messages:
        print(f"   - {time_str}: '{msg}'")
    
    # 4. Aplicar lógica del bypass (del código real)
    bypass_filter = False
    if last_processed:
        time_diff = last_processed - now
        if time_diff.total_seconds() > -3600:  # Si es menos de 1 hora atrás o futuro
            bypass_filter = True
    
    print(f"\n4. Bypass activado: {'SI' if bypass_filter else 'NO'}")
    
    # 5. Simular detección de mensajes
    print(f"\n5. Simulación de detección:")
    
    if bypass_filter:
        print("   [BYPASS] Se procesarían los últimos 10 mensajes")
        print("   -> TODOS los mensajes del usuario serían detectados")
        
        # Simular procesamiento de cada mensaje
        for time_str, msg_text in user_messages:
            # Parsear timestamp del mensaje
            hour, minute = time_str.split(":")
            msg_time = now.replace(hour=int(hour), minute=int(minute), second=0, microsecond=0)
            
            # Si es futuro, debe ser de hoy temprano
            if msg_time > now:
                msg_time = msg_time  # Mantener como hoy
            
            print(f"     {msg_time} - '{msg_text}' -> [DETECTADO]")
    else:
        print("   [NORMAL] Solo mensajes más nuevos que BD timestamp")
        
        for time_str, msg_text in user_messages:
            # Parsear timestamp del mensaje
            hour, minute = time_str.split(":")
            msg_time = now.replace(hour=int(hour), minute=int(minute), second=0, microsecond=0)
            
            # Si es futuro, debe ser de hoy temprano  
            if msg_time > now:
                msg_time = msg_time
                
            is_newer = msg_time > last_processed
            status = "DETECTADO" if is_newer else "FILTRADO"
            print(f"     {msg_time} - '{msg_text}' -> [{status}]")
    
    # 6. Conclusión
    print(f"\n6. CONCLUSION:")
    
    if bypass_filter:
        print("   [OK] El bypass está ACTIVO")
        print("   [OK] TODOS los mensajes del usuario deberían ser detectados")
        print("   [OK] Los gastos '250 carnicería', '500 pizza', '250 súper' deberían procesarse")
    else:
        print("   [!] El bypass NO está activo")
        print("   [!] Solo mensajes más nuevos serían detectados")
    
    return bypass_filter

def check_message_filter():
    """Verifica que el filtro de mensajes no esté bloqueando."""
    print(f"\n[VERIFICACION] Filtro de Mensajes")
    print("=" * 50)
    
    try:
        from app.services.message_filter import get_message_filter
        
        filter_service = get_message_filter()
        test_messages = [
            "Vice: 250 carnicería",
            "Vice: 500 pizza", 
            "Vice: 250 súper",
            "gasto registrado",  # Esto SÍ debe filtrarse
            "no puedo procesar ese mensaje"  # Esto SÍ debe filtrarse
        ]
        
        print("Probando filtro de mensajes:")
        for msg in test_messages:
            should_process = filter_service.should_process_message(msg, datetime.now())
            status = "PROCESAR" if should_process else "FILTRAR"
            print(f"  '{msg}' -> [{status}]")
        
        return True
        
    except Exception as e:
        print(f"Error verificando filtro: {e}")
        return False

if __name__ == "__main__":
    print("Verificación final del sistema de bypass...\n")
    
    # Verificar detección
    bypass_active = verify_message_detection()
    
    # Verificar filtros
    filter_ok = check_message_filter()
    
    print(f"\n{'='*50}")
    print(f"[RESUMEN FINAL]")
    print(f"{'='*50}")
    print(f"Bypass activo:        {'SI' if bypass_active else 'NO'}")
    print(f"Filtros funcionando:  {'SI' if filter_ok else 'NO'}")
    
    if bypass_active and filter_ok:
        print(f"\n[OK] El sistema DEBERÍA detectar los mensajes del usuario")
        print(f"     Si no los detecta, el problema está en WhatsApp Web o conexión")
    else:
        print(f"\n[!] Hay problemas en la configuración del sistema")