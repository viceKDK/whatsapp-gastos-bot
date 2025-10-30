@echo off
echo ========================================
echo  Bot Gastos - Instalador Frontend
echo ========================================
echo.

echo [1/3] Verificando Node.js...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Node.js no esta instalado
    echo Por favor instala Node.js desde: https://nodejs.org/
    pause
    exit /b 1
)
node --version
echo.

echo [2/3] Instalando dependencias...
call npm install
if %errorlevel% neq 0 (
    echo ERROR: Fallo la instalacion de dependencias
    pause
    exit /b 1
)
echo.

echo [3/3] Verificando instalacion...
if exist node_modules (
    echo ✓ Dependencias instaladas correctamente
) else (
    echo ERROR: No se encontro node_modules
    pause
    exit /b 1
)
echo.

echo ========================================
echo  Instalacion completada!
echo ========================================
echo.
echo Comandos disponibles:
echo   npm run dev      - Iniciar servidor de desarrollo
echo   npm run build    - Build para produccion
echo   npm run preview  - Preview del build
echo.
echo Para iniciar el dashboard:
echo   npm run dev
echo.
pause
