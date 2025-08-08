#!/usr/bin/env python3
"""
Test simple para problema de deteccion con BD vacia
"""

def test_detection_logic():
    print("=== TEST DETECCION MENSAJES ===")
    
    # BD vacia
    last_processed_timestamp = None
    
    print(f"BD timestamp: {last_processed_timestamp}")
    
    # Logica del bot
    bypass_filter = False
    if last_processed_timestamp:
        # Con timestamp de BD
        bypass_filter = False  # seria True si timestamp sospechoso
    else:
        # Sin timestamp de BD - primera ejecucion
        bypass_filter = False
    
    print(f"Bypass filter: {bypass_filter}")
    
    # Test de condiciones
    print("\n--- CONDICIONES DE PROCESAMIENTO ---")
    print(f"bypass_filter: {bypass_filter}")
    print(f"not last_processed_timestamp: {not last_processed_timestamp}")
    
    # Esta es la condicion critica del bot
    should_process = bypass_filter or not last_processed_timestamp
    print(f"should_process = {bypass_filter} OR {not last_processed_timestamp} = {should_process}")
    
    if should_process:
        print("RESULTADO: Los mensajes DEBERIAN procesarse")
        print("PROBLEMA: Si el bot muestra 'SIN BD TIMESTAMP' pero 0 mensajes,")
        print("         el problema esta en lazy_parser.parse_element_lazy()")
        return True
    else:
        print("RESULTADO: Los mensajes NO se procesarian")
        print("PROBLEMA: Error en la logica de condiciones")
        return False

if __name__ == "__main__":
    success = test_detection_logic()
    if success:
        print("\nCONCLUSION: Logica correcta - problema en lazy parser")
    else:
        print("\nCONCLUSION: Error en logica de condiciones")