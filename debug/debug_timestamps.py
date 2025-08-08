#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug de Timestamps

Herramienta para depurar problemas de timestamp en WhatsApp.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.append(str(Path(__file__).parent))

from infrastructure.storage.hybrid_storage import HybridStorage


def debug_timestamps():
    """Depura timestamps en la base de datos."""
    print("[DEBUG] Timestamps en Base de Datos")
    print("=" * 40)
    
    try:
        # Conectar al storage
        storage = HybridStorage("data/gastos.xlsx")
        
        # Verificar último timestamp procesado
        if hasattr(storage, 'get_last_processed_timestamp'):
            last_timestamp = storage.get_last_processed_timestamp()
            print(f"Ultimo timestamp en BD: {last_timestamp}")
            
            if last_timestamp:
                now = datetime.now()
                print(f"Hora actual:            {now}")
                print(f"Diferencia:             {now - last_timestamp}")
                
                # Verificar si es de hoy
                today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
                if last_timestamp >= today_start:
                    print("✅ El timestamp es de HOY")
                else:
                    print("⚠️ El timestamp es de un día anterior")
        
        # Obtener mensajes recientes del cache
        if hasattr(storage, 'get_recent_cached_messages'):
            recent = storage.get_recent_cached_messages(limit=10)
            print(f"\nMensajes recientes en cache:")
            for i, (text, timestamp, _) in enumerate(recent, 1):
                print(f"  {i}. {timestamp} - '{text[:30]}...'")
        
        # Verificar estadísticas
        if hasattr(storage, 'get_processing_stats'):
            stats = storage.get_processing_stats()
            print(f"\nEstadisticas de procesamiento:")
            print(f"  Total cached: {stats.get('cache', {}).get('total_cached', 0)}")
            print(f"  Gastos: {stats.get('cache', {}).get('expense_messages', 0)}")
            print(f"  Sistema: {stats.get('cache', {}).get('system_messages', 0)}")
    
    except Exception as e:
        print(f"ERROR: {e}")
        
    # Simular timestamps de mensajes recientes
    print(f"\n[SIMULACION] Comparación de Timestamps")
    print("=" * 40)
    
    # Hora de los mensajes del usuario
    user_messages = [
        ("14:44", "250 carnicería"),
        ("18:12", "500 pizza"), 
        ("18:12", "250 súper")
    ]
    
    # Hora actual
    now = datetime.now()
    print(f"Hora actual: {now}")
    
    # Simular último timestamp de BD (22:37:00)
    bd_timestamp = now.replace(hour=22, minute=37, second=0, microsecond=0)
    if bd_timestamp > now:
        bd_timestamp -= timedelta(days=1)  # Si es futuro, debe ser de ayer
    
    print(f"BD timestamp: {bd_timestamp}")
    
    # Comparar cada mensaje
    for time_str, message in user_messages:
        hour, minute = time_str.split(":")
        msg_timestamp = now.replace(hour=int(hour), minute=int(minute), second=0, microsecond=0)
        
        # Si el mensaje es futuro, debe ser de ayer
        if msg_timestamp > now:
            msg_timestamp -= timedelta(days=1)
            
        is_newer = msg_timestamp > bd_timestamp
        print(f"  '{message}' @ {msg_timestamp} -> {'NUEVO' if is_newer else 'YA PROCESADO'}")


if __name__ == "__main__":
    debug_timestamps()