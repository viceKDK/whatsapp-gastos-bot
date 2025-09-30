@echo off
echo =================================
echo   BOT GASTOS WHATSAPP - FIX
echo =================================
echo.

echo [1/4] Instalando dependencias faltantes...
pip install psutil>=5.9.0
if errorlevel 1 (
    echo ERROR: No se pudo instalar psutil
    pause
    exit /b 1
)

echo [2/4] Actualizando todas las dependencias...
pip install -r requirements.txt --upgrade
if errorlevel 1 (
    echo ERROR: No se pudieron instalar las dependencias
    pause
    exit /b 1
)

echo [3/4] Creando directorios necesarios...
if not exist "data" mkdir data
if not exist "logs" mkdir logs
if not exist "config" mkdir config

echo [4/4] Verificando instalacion...
python -c "import psutil, selenium, openpyxl; print('✅ Dependencias principales OK')"
if errorlevel 1 (
    echo ERROR: Verificacion fallida
    pause
    exit /b 1
)

echo.
echo ✅ INSTALACION COMPLETA
echo.
echo Ahora puedes ejecutar:
echo   python main.py
echo.
pause