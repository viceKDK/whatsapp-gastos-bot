# 🚀 Guía de Instalación - Bot Gastos WhatsApp

Esta guía te llevará paso a paso desde cero hasta tener el Bot Gastos WhatsApp funcionando en tu sistema.

## 📋 Requisitos del Sistema

### Sistema Operativo
- ✅ **Windows** 10/11
- ✅ **macOS** 10.14+
- ✅ **Linux** (Ubuntu 18.04+, CentOS 7+, otras distribuciones)

### Software Requerido

#### 1. Python 3.9 o superior ⭐ **OBLIGATORIO**

**Verificar si ya tienes Python:**
```bash
python --version
# o
python3 --version
```

**Si necesitas instalar Python:**

**Windows:**
1. Descargar desde [python.org](https://www.python.org/downloads/windows/)
2. ✅ **IMPORTANTE:** Marcar "Add Python to PATH" durante instalación
3. Verificar: `python --version` en cmd/PowerShell

**macOS:**
```bash
# Opción 1: Homebrew (recomendado)
brew install python

# Opción 2: Descargar desde python.org
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

**Linux (CentOS/RHEL):**
```bash
sudo yum install python3 python3-pip
# o para versiones más nuevas:
sudo dnf install python3 python3-pip
```

#### 2. Google Chrome ⭐ **OBLIGATORIO**

El bot necesita Chrome para automatizar WhatsApp Web.

**Instalar Chrome:**
- **Windows/Mac:** Descargar desde [google.com/chrome](https://www.google.com/chrome/)
- **Linux Ubuntu/Debian:**
  ```bash
  wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
  sudo sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'
  sudo apt update
  sudo apt install google-chrome-stable
  ```

**Verificar Chrome:**
```bash
# Windows
"C:\Program Files\Google\Chrome\Application\chrome.exe" --version

# macOS  
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --version

# Linux
google-chrome --version
```

#### 3. Git (Opcional pero recomendado)

Para clonar el repositorio y actualizaciones futuras.

**Windows:** Descargar desde [git-scm.com](https://git-scm.com/download/win)
**macOS:** `brew install git` o Xcode Command Line Tools
**Linux:** `sudo apt install git` (Ubuntu) o `sudo yum install git` (CentOS)

---

## 📦 Instalación del Bot

### Opción 1: Instalación Desde Repositorio (Recomendada)

#### Paso 1: Clonar el Repositorio

```bash
# Si tienes Git instalado
git clone https://github.com/usuario/bot-gastos-whatsapp.git
cd bot-gastos-whatsapp

# Si no tienes Git, descargar ZIP desde GitHub y extraer
```

#### Paso 2: Crear Entorno Virtual

**¿Por qué un entorno virtual?**
Aísla las dependencias del bot para evitar conflictos con otros proyectos Python.

```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# Windows (Command Prompt):
venv\Scripts\activate

# Windows (PowerShell):
venv\Scripts\Activate.ps1

# macOS/Linux:
source venv/bin/activate
```

**✅ Verificar activación:** Tu prompt debe mostrar `(venv)` al inicio.

#### Paso 3: Instalar Dependencias

```bash
# Actualizar pip (recomendado)
python -m pip install --upgrade pip

# Instalar dependencias del bot
pip install -r requirements.txt
```

**Dependencias que se instalarán:**
- `selenium>=4.15.0` - Automatización web
- `openpyxl>=3.1.0` - Manejo de archivos Excel
- `pytest>=7.4.0` - Framework de testing
- `black>=23.0.0` - Formateador de código
- `flake8>=6.0.0` - Linter de código

#### Paso 4: Configuración Inicial

```bash
# Copiar template de configuración
cp config/.env.example config/.env

# Editar configuración (usar tu editor preferido)
# Windows:
notepad config/.env

# macOS:
nano config/.env
# o
open -a TextEdit config/.env

# Linux:
nano config/.env
# o
gedit config/.env
```

#### Paso 5: Validar Instalación

```bash
# Validar configuración
python main.py --validate-config

# Probar sistema de almacenamiento
python main.py --test-storage

# Ver información del sistema
python main.py --version
```

**✅ Si todo está correcto, deberías ver:**
```
✅ Configuración válida
✅ Prueba de almacenamiento exitosa
Bot Gastos WhatsApp v1.0.0
```

---

### Opción 2: Instalación Manual

Si prefieres descargar archivos individualmente:

#### Paso 1: Crear Directorio del Proyecto

```bash
mkdir bot-gastos-whatsapp
cd bot-gastos-whatsapp
```

#### Paso 2: Descargar Archivos

Descarga estos archivos desde el repositorio:
- `main.py`
- `requirements.txt`
- `README.md`
- Carpeta `app/` completa
- Carpeta `domain/` completa
- Carpeta `infrastructure/` completa
- Carpeta `interface/` completa
- Carpeta `shared/` completa
- Carpeta `config/` completa
- Carpeta `docs/` completa

#### Paso 3: Continuar con Pasos 2-5 de la Opción 1

---

## ⚙️ Configuración Post-Instalación

### Configurar WhatsApp Web

#### Paso 1: Configurar Chat Objetivo

1. **Abrir WhatsApp Web** en Chrome: [web.whatsapp.com](https://web.whatsapp.com)
2. **Escanear código QR** con tu móvil
3. **Crear chat** para gastos (puedes crearte un chat contigo mismo)
4. **Nombrar el chat exactamente** como configuraste en `TARGET_CHAT_NAME`

#### Paso 2: Configurar Variables de Entorno

Edita `config/.env`:

```bash
# ⭐ CONFIGURACIÓN CRÍTICA
TARGET_CHAT_NAME=Gastos Personal    # ¡Debe coincidir exactamente!

# Configuración de almacenamiento
STORAGE_MODE=excel                  # o 'sqlite' 
EXCEL_FILE_PATH=data/gastos.xlsx

# Configuración de WhatsApp
WHATSAPP_POLL_INTERVAL=30           # Revisar cada 30 segundos
CHROME_HEADLESS=false               # true=invisible, false=ventana visible

# Configuración de logging
LOG_LEVEL=INFO                      # DEBUG para más detalle
LOG_CONSOLE=true                    # Mostrar logs en consola
```

#### Paso 3: Probar Configuración

```bash
# Ejecutar en modo desarrollo (más logs)
python main.py --mode dev

# Si todo está bien, verás:
🤖 BOT GASTOS WHATSAPP INICIADO
====================================
📅 Inicio: 2025-08-06 14:30:00
💾 Storage: EXCEL
💬 Chat: Gastos Personal
⏰ Intervalo: 30s
📝 Log Level: INFO
====================================
El bot está escuchando mensajes...
```

---

## 🧪 Verificar que Todo Funciona

### Test 1: Configuración del Sistema

```bash
python main.py --validate-config
```

**✅ Debe mostrar:** `✅ Configuración válida`

### Test 2: Almacenamiento

```bash
python main.py --test-storage
```

**✅ Debe mostrar:**
```
=== PRUEBA DE ALMACENAMIENTO ===
Modo: excel
Archivo: data/gastos.xlsx
Total gastos: 0
Monto total: $0.00
✅ Prueba de almacenamiento exitosa
```

### Test 3: Mensaje de Prueba

1. **Ejecutar el bot:**
   ```bash
   python main.py --mode dev
   ```

2. **Enviar mensaje de prueba** en WhatsApp al chat configurado:
   ```
   gasto: 100 comida
   ```

3. **Verificar que se procesó:**
   - Debe aparecer en consola: `💰 14:30:15 - $100.00 en comida`
   - Debe crearse/actualizarse `data/gastos.xlsx`

4. **Detener el bot:** `Ctrl+C`

---

## 🔧 Solución de Problemas de Instalación

### Error: "python no se reconoce como comando"

**Windows:**
1. Reinstalar Python marcando "Add Python to PATH"
2. O agregar manualmente a PATH: `C:\Users\TuUsuario\AppData\Local\Programs\Python\Python3X`
3. Reiniciar terminal

**macOS/Linux:**
- Usar `python3` en lugar de `python`
- O crear alias: `echo 'alias python=python3' >> ~/.bashrc`

### Error: "pip no se reconoce como comando"

```bash
# Windows
python -m pip install --upgrade pip

# macOS/Linux
python3 -m pip install --upgrade pip
```

### Error: "No module named 'selenium'"

```bash
# Verificar que el entorno virtual está activado
# Debe mostrar (venv) en el prompt

# Si no está activado:
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Reinstalar dependencias
pip install -r requirements.txt
```

### Error: "ChromeDriver not found"

**Solución automática (recomendada):**
El bot usa selenium-manager que descarga ChromeDriver automáticamente.

**Solución manual:**
1. Descargar ChromeDriver desde [chromedriver.chromium.org](https://chromedriver.chromium.org/)
2. Colocar en PATH o en carpeta del proyecto
3. Verificar compatibilidad con versión de Chrome

### Error de Permisos (Linux/macOS)

```bash
# Dar permisos a archivos del proyecto
chmod +x main.py
chmod -R 755 .

# Si necesitas permisos para crear archivos en data/
sudo chown -R $USER:$USER .
```

### Error: "ModuleNotFoundError: No module named 'app'"

**Causa:** Python no encuentra los módulos del proyecto.

**Solución:**
```bash
# Verificar que estás en el directorio correcto
pwd
ls -la  # Debe mostrar main.py, app/, domain/, etc.

# Si estás en subdirectorio, subir:
cd ..

# Agregar directorio actual al PYTHONPATH (temporal)
export PYTHONPATH="${PYTHONPATH}:$(pwd)"  # Linux/macOS
set PYTHONPATH=%PYTHONPATH%;%cd%          # Windows
```

### Problemas con WhatsApp Web

**WhatsApp Web no carga:**
1. Verificar conexión a internet
2. Probar WhatsApp Web manualmente en Chrome
3. Limpiar cache de Chrome
4. Verificar que WhatsApp móvil esté conectado

**Bot no encuentra mensajes:**
1. Verificar nombre exacto del chat (`TARGET_CHAT_NAME`)
2. Enviar mensajes al chat correcto
3. Verificar que WhatsApp Web esté activo en Chrome

---

## 🎯 Optimizaciones Post-Instalación

### Para Mejor Performance

#### 1. Configurar Intervalos

```bash
# Para uso intensivo (más recursos, más responsivo)
WHATSAPP_POLL_INTERVAL=10

# Para uso normal (menos recursos)
WHATSAPP_POLL_INTERVAL=30

# Para uso ocasional (mínimos recursos)
WHATSAPP_POLL_INTERVAL=60
```

#### 2. Configurar Logging

```bash
# Para desarrollo/debugging
LOG_LEVEL=DEBUG
LOG_CONSOLE=true

# Para uso normal
LOG_LEVEL=INFO
LOG_CONSOLE=true

# Para uso en servidor/producción
LOG_LEVEL=WARNING
LOG_CONSOLE=false
```

#### 3. Modo Headless

```bash
# Para ejecutar invisible (menos recursos)
CHROME_HEADLESS=true

# Para ejecutar visible (debugging más fácil)
CHROME_HEADLESS=false
```

### Para Desarrollo

Si planeas modificar el código:

```bash
# Instalar dependencias de desarrollo
pip install pytest pytest-cov black flake8 mypy

# Pre-commit hooks para calidad de código
pip install pre-commit
pre-commit install
```

---

## 📱 Uso en Diferentes Sistemas

### Windows Subsystem for Linux (WSL)

```bash
# Instalar en WSL
sudo apt update
sudo apt install python3 python3-pip python3-venv

# Problema: Chrome en WSL necesita configuración especial
# Usar Windows Chrome desde WSL o configurar X11 forwarding
```

### Servidor Linux (Sin GUI)

```bash
# Instalar dependencias para Chrome headless
sudo apt install -y wget unzip

# Chrome será usado en modo headless automáticamente
CHROME_HEADLESS=true
```

### macOS con M1/M2 (Apple Silicon)

```bash
# Usar Homebrew nativo para ARM
/opt/homebrew/bin/brew install python

# Verificar arquitectura
python -c "import platform; print(platform.machine())"
# Debe mostrar: arm64
```

---

## 🚀 Scripts de Automatización

### Script de Instalación Automática (Linux/macOS)

Crear `install.sh`:

```bash
#!/bin/bash
set -e

echo "🚀 Instalando Bot Gastos WhatsApp..."

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 no está instalado"
    exit 1
fi

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt

# Configurar
cp config/.env.example config/.env

echo "✅ Instalación completada"
echo "📝 Edita config/.env y luego ejecuta: python main.py"
```

```bash
chmod +x install.sh
./install.sh
```

### Script de Instalación Windows

Crear `install.bat`:

```batch
@echo off
echo 🚀 Instalando Bot Gastos WhatsApp...

REM Crear entorno virtual
python -m venv venv
call venv\Scripts\activate.bat

REM Instalar dependencias
python -m pip install --upgrade pip
pip install -r requirements.txt

REM Configurar
copy config\.env.example config\.env

echo ✅ Instalación completada
echo 📝 Edita config\.env y luego ejecuta: python main.py
pause
```

---

## 📞 Soporte de Instalación

Si tienes problemas con la instalación:

1. **Verifica requisitos del sistema** - Todos los programas instalados correctamente
2. **Revisa logs** - `python main.py --validate-config` muestra errores específicos
3. **Consulta troubleshooting** - Ver [troubleshooting_guide.md](troubleshooting_guide.md)
4. **Reporta issues** - Con información detallada del sistema y error

### Información Útil para Reportar Problemas

```bash
# Información del sistema
python --version
pip --version
google-chrome --version  # o chrome --version

# Información del entorno
python -c "import sys; print(sys.path)"
pip list

# Validación del bot
python main.py --validate-config
```

¡Tu Bot Gastos WhatsApp debería estar listo para usar! 🎉