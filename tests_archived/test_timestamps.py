#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test de Timestamps

Simula el parseo de timestamps para validar la lógica.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.append(str(Path(__file__).parent))

from infrastructure.whatsapp.whatsapp_selenium import WhatsAppSeleniumConnector
from config.settings import WhatsAppConfig


def test_timestamp_parsing():
    """Test del parseo de timestamps."""
    print("[TEST] Parseo de Timestamps")
    print("=" * 30)
    
    # Crear instancia del connector (sin conectar)
    config = WhatsAppConfig()
    connector = WhatsAppSeleniumConnector(config)
    
    # Casos de prueba
    test_cases = [
        "14:44",
        "18:12", 
        "22:37",
        "06:30",  # Mañana temprano
        "23:59",  # Noche tardía
        "ayer 15:30",
        "yesterday 12:00"
    ]
    
    now = datetime.now()
    print(f"Hora actual: {now}")
    print()
    
    for time_str in test_cases:
        try:
            parsed = connector._parse_message_timestamp(time_str)
            is_today = parsed.date() == now.date()
            is_yesterday = parsed.date() == (now - timedelta(days=1)).date()
            
            day_label = "HOY" if is_today else "AYER" if is_yesterday else "OTRO DÍA"
            
            print(f"'{time_str}' -> {parsed} ({day_label})")
            
        except Exception as e:
            print(f"'{time_str}' -> ERROR: {e}")


def test_timestamp_comparison():
    """Test de comparación con timestamp de BD."""
    print(f"\n[TEST] Comparación con BD")
    print("=" * 30)
    
    # Simular timestamp de BD (ayer 22:37)
    now = datetime.now()
    bd_timestamp = now.replace(hour=22, minute=37, second=0, microsecond=0)
    if bd_timestamp > now:
        bd_timestamp -= timedelta(days=1)
    
    print(f"BD Timestamp: {bd_timestamp}")
    print()
    
    # Mensajes del usuario
    user_messages = [
        "14:44",  # Hoy 14:44
        "18:12",  # Hoy 18:12
    ]
    
    config = WhatsAppConfig() 
    connector = WhatsAppSeleniumConnector(config)
    
    for time_str in user_messages:
        parsed = connector._parse_message_timestamp(time_str)
        is_newer = parsed > bd_timestamp
        
        print(f"'{time_str}' -> {parsed}")
        print(f"  Es más nuevo que BD? {is_newer}")
        if is_newer:
            diff = parsed - bd_timestamp
            print(f"  Diferencia: {diff}")
        print()


if __name__ == "__main__":
    test_timestamp_parsing()
    test_timestamp_comparison()