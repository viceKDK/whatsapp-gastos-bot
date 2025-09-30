#!/bin/bash

echo "=========================================="
echo " Bot Gastos WhatsApp - Instalador Unix"  
echo "=========================================="
echo

# Verificar si Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 no encontrado"
    echo "Por favor instala Python 3.8+ usando tu gestor de paquetes"
    echo "  Ubuntu/Debian: sudo apt install python3 python3-pip"
    echo "  Fedora: sudo dnf install python3 python3-pip"
    echo "  macOS: brew install python3"
    exit 1
fi

echo "Python encontrado, iniciando instalación..."
echo

# Hacer ejecutable el instalador
chmod +x scripts/install.py

# Ejecutar instalador Python
python3 scripts/install.py

echo
echo "Instalación completada!"
echo
echo "Para ejecutar el bot:"
echo "  ./run_bot.sh"
echo