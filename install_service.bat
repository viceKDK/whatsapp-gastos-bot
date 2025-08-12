@echo off
echo 🚀 Instalando Bot Gastos como Servicio de Windows...
echo.
echo REQUISITO: Ejecutar como Administrador
echo.

REM Instalar nssm si no existe
if not exist "nssm.exe" (
    echo ⚠️  Descargando NSSM para crear servicio...
    powershell -Command "Invoke-WebRequest -Uri 'https://nssm.cc/release/nssm-2.24.zip' -OutFile 'nssm.zip'"
    powershell -Command "Expand-Archive -Path 'nssm.zip' -DestinationPath '.'"
    copy "nssm-2.24\win64\nssm.exe" .
    del nssm.zip
    rmdir /s /q nssm-2.24
)

REM Crear servicio
echo 📦 Creando servicio 'BotGastos'...
nssm install BotGastos "%cd%\venv\Scripts\python.exe" "%cd%\main.py"
nssm set BotGastos DisplayName "Bot Gastos WhatsApp"
nssm set BotGastos Description "Automatiza registro de gastos desde WhatsApp"
nssm set BotGastos Start SERVICE_AUTO_START
nssm set BotGastos AppDirectory "%cd%"
nssm set BotGastos AppStdout "%cd%\logs\service.log"
nssm set BotGastos AppStderr "%cd%\logs\service_error.log"

echo ✅ Servicio creado exitosamente!
echo.
echo 📋 COMANDOS ÚTILES:
echo    net start BotGastos     - Iniciar servicio
echo    net stop BotGastos      - Detener servicio
echo    nssm remove BotGastos   - Eliminar servicio
echo.
pause