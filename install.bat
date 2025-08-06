@echo off
echo ==========================================
echo  Bot Gastos WhatsApp - Instalador Windows
echo ==========================================
echo.

REM Verificar si Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no encontrado en el PATH
    echo Por favor instala Python 3.8+ desde https://python.org
    pause
    exit /b 1
)

echo Python encontrado, iniciando instalacion...
echo.

REM Ejecutar instalador Python
python scripts\install.py

echo.
echo Instalacion completada!
echo.
echo Para ejecutar el bot:
echo   run_bot.bat
echo.
pause