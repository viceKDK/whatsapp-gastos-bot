@echo off
title Bot Gastos - Segundo Plano
echo 🤖 Iniciando Bot Gastos en Segundo Plano...
echo.
echo ✅ Chrome ejecutándose sin ventana (headless)
echo ✅ Logs guardándose en logs/bot.log  
echo ✅ Minimiza esta ventana para dejarlo en segundo plano
echo.
echo 💡 Para detener: Ctrl+C
echo 📊 Para ver logs: type logs\bot.log
echo.
python main.py
pause