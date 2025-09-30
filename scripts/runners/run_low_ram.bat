@echo off
title Bot Gastos - Modo Bajo Consumo RAM
echo 🔋 INICIANDO BOT GASTOS - MODO OPTIMIZADO
echo.
echo ✅ Chrome headless (sin ventana)
echo ✅ Imágenes deshabilitadas
echo ✅ Plugins y extensiones deshabilitados
echo ✅ Límites de memoria estrictos
echo ✅ Recolección de basura agresiva
echo ✅ Configuración mínima de RAM
echo.
echo 📊 RAM estimada: ~200-300MB vs ~800MB normal
echo 💡 Para detener: Ctrl+C
echo 📄 Logs: logs\bot.log
echo.

REM Configurar variables de entorno para optimización
set PYTHONOPTIMIZE=1
set PYTHONDONTWRITEBYTECODE=1

REM Ejecutar la versión optimizada con parámetros de bajo consumo
python main_optimized.py --headless --minimal

echo.
echo ✅ Bot finalizado
pause