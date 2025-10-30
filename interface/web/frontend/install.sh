#!/bin/bash

echo "========================================"
echo " Bot Gastos - Instalador Frontend"
echo "========================================"
echo ""

echo "[1/3] Verificando Node.js..."
if ! command -v node &> /dev/null; then
    echo "ERROR: Node.js no está instalado"
    echo "Por favor instala Node.js desde: https://nodejs.org/"
    exit 1
fi
node --version
echo ""

echo "[2/3] Instalando dependencias..."
npm install
if [ $? -ne 0 ]; then
    echo "ERROR: Falló la instalación de dependencias"
    exit 1
fi
echo ""

echo "[3/3] Verificando instalación..."
if [ -d "node_modules" ]; then
    echo "✓ Dependencias instaladas correctamente"
else
    echo "ERROR: No se encontró node_modules"
    exit 1
fi
echo ""

echo "========================================"
echo " Instalación completada!"
echo "========================================"
echo ""
echo "Comandos disponibles:"
echo "  npm run dev      - Iniciar servidor de desarrollo"
echo "  npm run build    - Build para producción"
echo "  npm run preview  - Preview del build"
echo ""
echo "Para iniciar el dashboard:"
echo "  npm run dev"
echo ""
