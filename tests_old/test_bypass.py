#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test del Bypass de Timestamp

Prueba específicamente el bypass implementado en get_new_messages_optimized().
"""

import sys
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent))

from config.settings import get_settings
from infrastructure.whatsapp import WhatsAppEnhancedConnector
from infrastructure.storage.hybrid_storage import HybridStorage

def test_bypass_logic():
    """Prueba el bypass logic sin conectar realmente a WhatsApp."""
    print("[TEST] Bypass Logic de Timestamp")
    print("=" * 40)
    
    # Obtener último timestamp de BD
    storage = HybridStorage("data/gastos.xlsx")
    last_timestamp = storage.get_last_processed_timestamp()
    
    print(f"BD Timestamp: {last_timestamp}")
    
    now = datetime.now()
    print(f"Hora actual:  {now}")
    
    # Lógica del bypass (copiada del código real)
    bypass_filter = False
    if last_timestamp:
        time_diff = last_timestamp - now
        print(f"Diferencia:   {time_diff}")
        print(f"Segundos:     {time_diff.total_seconds()}")
        
        if time_diff.total_seconds() > -3600:  # Si es menos de 1 hora atrás o futuro
            bypass_filter = True
            print("[BYPASS] ACTIVADO - BD timestamp sospechoso")
        else:
            print("[NORMAL] BD timestamp es válido")
    else:
        bypass_filter = True
        print("[BYPASS] ACTIVADO - No hay último timestamp")
    
    return bypass_filter

def test_optimized_method():
    """Prueba el método optimizado con bypass."""
    print(f"\n[TEST] Método get_new_messages_optimized")
    print("=" * 40)
    
    try:
        settings = get_settings()
        storage = HybridStorage("data/gastos.xlsx")
        last_timestamp = storage.get_last_processed_timestamp()
        
        print(f"1. Último timestamp BD: {last_timestamp}")
        
        # Crear connector (pero NO conectar por ahora)
        connector = WhatsAppEnhancedConnector(settings.whatsapp)
        
        # Verificar si tiene el método optimizado
        if hasattr(connector, 'get_new_messages_optimized'):
            print("2. [OK] Método optimizado disponible")
            
            # Simular llamada (sin conexión real)
            print("3. Simulando lógica del bypass...")
            
            now = datetime.now()
            bypass_filter = False
            if last_timestamp:
                time_diff = last_timestamp - now
                if time_diff.total_seconds() > -3600:
                    bypass_filter = True
            
            if bypass_filter:
                print("4. [BYPASS] Se activaría el bypass")
                print("   -> Procesaría últimos 10 mensajes")
            else:
                print("4. [NORMAL] Filtrado normal por timestamp")
            
            return True
        else:
            print("2. [X] Método optimizado NO disponible")
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    print("Probando lógica de bypass sin conexión real...\n")
    
    # Test 1: Lógica del bypass
    bypass_needed = test_bypass_logic()
    
    # Test 2: Método optimizado
    method_ok = test_optimized_method()
    
    print(f"\n[RESUMEN]")
    print(f"Bypass necesario: {'SI' if bypass_needed else 'NO'}")
    print(f"Método disponible: {'SI' if method_ok else 'NO'}")
    
    if bypass_needed and method_ok:
        print("[OK] El bypass debería funcionar correctamente")
    else:
        print("[!] Puede haber problemas")