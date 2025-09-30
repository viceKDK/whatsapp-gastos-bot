#!/usr/bin/env python3
"""
Script para arreglar timestamps futuros incorrectos en la BD
"""

import sys
import os
import sqlite3
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def fix_future_timestamps():
    """Corrige timestamps futuros en la base de datos."""
    
    db_path = "data/gastos.cache.db"
    
    print("=== ARREGLANDO TIMESTAMPS FUTUROS ===")
    
    if not os.path.exists(db_path):
        print(f"Base de datos no existe: {db_path}")
        return
    
    now = datetime.now()
    print(f"Timestamp actual: {now}")
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # 1. Verificar gastos con timestamps futuros
            cursor.execute("""
                SELECT id, fecha FROM gastos 
                WHERE fecha > ?
                ORDER BY fecha DESC
            """, (now.isoformat(),))
            
            future_gastos = cursor.fetchall()
            print(f"\nGastos con timestamps futuros: {len(future_gastos)}")
            
            for gasto_id, fecha in future_gastos:
                print(f"  ID {gasto_id}: {fecha}")
            
            # 2. Verificar mensajes procesados con timestamps futuros
            cursor.execute("""
                SELECT id, message_timestamp FROM processed_messages 
                WHERE message_timestamp > ?
                ORDER BY message_timestamp DESC
            """, (now.isoformat(),))
            
            future_messages = cursor.fetchall()
            print(f"\nMensajes con timestamps futuros: {len(future_messages)}")
            
            for msg_id, timestamp in future_messages:
                print(f"  ID {msg_id}: {timestamp}")
            
            # 3. Arreglar timestamps futuros
            if future_gastos or future_messages:
                print(f"\n¿Arreglar timestamps futuros? (s/n): ", end="")
                response = input().lower()
                
                if response in ['s', 'si', 'yes', 'y']:
                    # Establecer timestamp seguro (hace 1 hora)
                    safe_timestamp = (now - timedelta(hours=1)).isoformat()
                    
                    # Arreglar gastos
                    if future_gastos:
                        cursor.execute("""
                            UPDATE gastos 
                            SET fecha = ?
                            WHERE fecha > ?
                        """, (safe_timestamp, now.isoformat()))
                        print(f"✅ Arreglados {len(future_gastos)} gastos")
                    
                    # Arreglar mensajes
                    if future_messages:
                        cursor.execute("""
                            UPDATE processed_messages 
                            SET message_timestamp = ?
                            WHERE message_timestamp > ?
                        """, (safe_timestamp, now.isoformat()))
                        print(f"✅ Arreglados {len(future_messages)} mensajes")
                    
                    conn.commit()
                    print("✅ Timestamps arreglados correctamente")
                else:
                    print("❌ No se arreglaron timestamps")
            else:
                print("✅ No hay timestamps futuros para arreglar")
            
            # 4. Mostrar último timestamp después del arreglo
            cursor.execute("""
                SELECT MAX(message_timestamp) FROM processed_messages
            """)
            result = cursor.fetchone()
            
            if result[0]:
                print(f"\nÚltimo timestamp en BD: {result[0]}")
            else:
                print("\nNo hay mensajes en BD")
                
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    fix_future_timestamps()