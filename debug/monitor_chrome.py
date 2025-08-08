#!/usr/bin/env python3
"""
Monitor de procesos Chrome
"""

import subprocess
import time
import sys

def get_chrome_processes():
    """Obtiene lista de procesos Chrome."""
    try:
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq chrome.exe'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            # Filtrar líneas que realmente contienen procesos
            processes = [line for line in lines if 'chrome.exe' in line]
            return processes
        return []
    except:
        return []

def get_chromedriver_processes():
    """Obtiene lista de procesos ChromeDriver."""
    try:
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq chromedriver.exe'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            processes = [line for line in lines if 'chromedriver.exe' in line]
            return processes
        return []
    except:
        return []

def monitor_processes():
    """Monitorea procesos en tiempo real."""
    print("🔍 MONITOR DE PROCESOS CHROME/CHROMEDRIVER")
    print("=" * 50)
    
    try:
        while True:
            chrome_procs = get_chrome_processes()
            driver_procs = get_chromedriver_processes()
            
            timestamp = time.strftime("%H:%M:%S")
            print(f"\n[{timestamp}]")
            print(f"Chrome processes: {len(chrome_procs)}")
            print(f"ChromeDriver processes: {len(driver_procs)}")
            
            if chrome_procs or driver_procs:
                print("🔴 PROCESOS ACTIVOS:")
                for proc in chrome_procs[:3]:  # Solo mostrar primeros 3
                    print(f"  📱 {proc.split()[:2]}")
                for proc in driver_procs:
                    print(f"  🚗 {proc.split()[:2]}")
            else:
                print("✅ No hay procesos Chrome/ChromeDriver")
            
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\n👋 Monitor detenido")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "once":
        # Ejecutar una sola vez
        chrome_procs = get_chrome_processes()
        driver_procs = get_chromedriver_processes()
        
        print(f"Chrome: {len(chrome_procs)} procesos")
        print(f"ChromeDriver: {len(driver_procs)} procesos")
        
        if chrome_procs:
            print("\nProcesos Chrome:")
            for i, proc in enumerate(chrome_procs[:5]):
                print(f"  {i+1}. {proc}")
        
        if driver_procs:
            print("\nProcesos ChromeDriver:")
            for i, proc in enumerate(driver_procs):
                print(f"  {i+1}. {proc}")
    else:
        monitor_processes()