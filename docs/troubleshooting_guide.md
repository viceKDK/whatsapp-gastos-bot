# 🔧 Guía de Troubleshooting - Bot Gastos WhatsApp

Esta guía te ayudará a diagnosticar y resolver los problemas más comunes del Bot Gastos WhatsApp.

## 📋 Tabla de Contenidos

- [Diagnóstico Rápido](#diagnóstico-rápido)
- [Problemas de Instalación](#problemas-de-instalación)
- [Problemas de WhatsApp](#problemas-de-whatsapp)
- [Problemas de Procesamiento](#problemas-de-procesamiento)
- [Problemas de Almacenamiento](#problemas-de-almacenamiento)
- [Problemas de Performance](#problemas-de-performance)
- [Logs y Debugging](#logs-y-debugging)
- [Herramientas de Diagnóstico](#herramientas-de-diagnóstico)

---

## 🩺 Diagnóstico Rápido

### Checklist Básico

Antes de diagnosticar problemas específicos, verifica:

```bash
# 1. ✅ Configuración válida
python main.py --validate-config

# 2. ✅ Sistema funcionando
python main.py --test-storage

# 3. ✅ Información del sistema
python main.py --version
```

### Información del Sistema

```bash
# Información completa para diagnóstico
python -c "
import sys
print(f'Python: {sys.version}')
print(f'Platform: {sys.platform}')
"

# Verificar dependencias críticas
python -c "
try:
    import selenium; print(f'✅ Selenium: {selenium.__version__}')
except: print('❌ Selenium no disponible')

try:
    import openpyxl; print(f'✅ OpenPyXL: {openpyxl.__version__}')
except: print('❌ OpenPyXL no disponible')
"

# Verificar Chrome
google-chrome --version 2>/dev/null || chrome --version 2>/dev/null || echo "❌ Chrome no encontrado"
```

---

## 🚀 Problemas de Instalación

### Error: "python no se reconoce como comando"

**Síntoma:**
```
'python' no se reconoce como un comando interno o externo
python: command not found
```

**Causa:** Python no está instalado o no está en PATH.

**Solución:**

**Windows:**
1. Instalar Python desde [python.org](https://python.org/downloads/)
2. ✅ **Marcar "Add Python to PATH"** durante instalación
3. Reiniciar terminal/cmd
4. Alternativamente: usar `py` en lugar de `python`

**macOS:**
```bash
# Usar python3 explícitamente
python3 --version

# O instalar con Homebrew
brew install python

# Crear alias permanente
echo 'alias python=python3' >> ~/.bashrc
echo 'alias pip=pip3' >> ~/.bashrc
source ~/.bashrc
```

**Linux:**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip

# CentOS/RHEL
sudo yum install python3 python3-pip

# Crear enlaces simbólicos
sudo ln -s /usr/bin/python3 /usr/bin/python
sudo ln -s /usr/bin/pip3 /usr/bin/pip
```

---

### Error: "No module named 'app'"

**Síntoma:**
```
ModuleNotFoundError: No module named 'app'
ImportError: No module named 'domain'
```

**Causa:** Python no encuentra los módulos del proyecto.

**Solución:**
```bash
# 1. Verificar directorio correcto
pwd
ls -la          # Debe mostrar main.py, app/, domain/, etc.

# 2. Si estás en subdirectorio, subir nivel
cd ..

# 3. Agregar al PYTHONPATH (temporal)
# Linux/macOS:
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Windows:
set PYTHONPATH=%PYTHONPATH%;%cd%

# 4. Verificar estructura del proyecto
find . -name "*.py" -type f | head -10
```

---

### Error: "Permission denied"

**Síntoma:**
```
PermissionError: [Errno 13] Permission denied: 'data/gastos.xlsx'
FileNotFoundError: [Errno 2] No such file or directory: 'logs'
```

**Causa:** Permisos insuficientes para crear/modificar archivos.

**Solución:**

**Linux/macOS:**
```bash
# Cambiar propietario del directorio
sudo chown -R $USER:$USER .

# Dar permisos de escritura
chmod -R 755 .
chmod 644 config/.env

# Crear directorios necesarios
mkdir -p data logs
chmod 755 data logs
```

**Windows:**
```batch
# Ejecutar como administrador o cambiar ubicación
# Mover proyecto a carpeta del usuario
move bot-gastos %USERPROFILE%\bot-gastos
cd %USERPROFILE%\bot-gastos
```

---

### Error: "ChromeDriver not found"

**Síntoma:**
```
selenium.common.exceptions.WebDriverException: 'chromedriver' executable needs to be in PATH
```

**Causa:** ChromeDriver no disponible (aunque debería descargarse automáticamente).

**Solución:**

**Automática (Recomendada):**
```bash
# Selenium 4.15+ maneja ChromeDriver automáticamente
# Verificar que Chrome está instalado
google-chrome --version

# Limpiar cache de Selenium
rm -rf ~/.cache/selenium/  # Linux/macOS
rmdir /s %USERPROFILE%\.cache\selenium  # Windows
```

**Manual:**
```bash
# 1. Descargar ChromeDriver desde chromedriver.chromium.org
# 2. Coincidir versión con Chrome instalado
google-chrome --version
# Chrome 120.x -> ChromeDriver 120.x

# 3. Colocar en PATH o directorio del proyecto
# Linux/macOS:
sudo mv chromedriver /usr/local/bin/
chmod +x /usr/local/bin/chromedriver

# Windows:
# Colocar chromedriver.exe en carpeta del proyecto o PATH
```

---

## 💬 Problemas de WhatsApp

### WhatsApp Web no carga

**Síntoma:**
```
TimeoutException: Message: timeout: Timed out receiving message from renderer
El bot no encuentra el chat especificado
```

**Causa:** Problemas de conexión con WhatsApp Web.

**Solución:**

1. **Verificar WhatsApp Web manualmente:**
```bash
# Abrir Chrome manualmente y probar
google-chrome https://web.whatsapp.com
```

2. **Verificar conexión móvil:**
- WhatsApp móvil debe estar conectado a internet
- Verificar en móvil: Configuración > WhatsApp Web/Desktop

3. **Limpiar cache de Chrome:**
```bash
# Cerrar todas las ventanas de Chrome
# Linux/macOS:
rm -rf ~/.config/google-chrome/Default/Cache
rm -rf ~/.config/google-chrome/Default/Code\ Cache

# Windows:
# Ir a C:\Users\%USERNAME%\AppData\Local\Google\Chrome\User Data\Default
# Eliminar carpetas Cache y Code Cache
```

4. **Probar en modo no-headless:**
```bash
# Cambiar configuración
CHROME_HEADLESS=false

# Ejecutar y observar qué pasa en la ventana
python main.py --mode dev
```

---

### Bot no encuentra el chat

**Síntoma:**
```
Chat 'Gastos Personal' no encontrado
No se encontraron mensajes nuevos (siempre)
```

**Causa:** Nombre del chat no coincide exactamente.

**Solución:**

1. **Verificar nombre exacto:**
```bash
# Configuración actual
python main.py --config | grep "Chat objetivo"

# Verificar en WhatsApp Web:
# - Abrir WhatsApp Web
# - Verificar nombre exacto del chat (mayúsculas, espacios, acentos)
```

2. **Casos problemáticos comunes:**
```bash
# ❌ Errores frecuentes
TARGET_CHAT_NAME=gastos personal      # Minúsculas
TARGET_CHAT_NAME=Gastos  Personal     # Espacios extra  
TARGET_CHAT_NAME="Gastos Personal"    # Comillas
TARGET_CHAT_NAME=Gastos Personales    # Palabra extra

# ✅ Debe coincidir EXACTAMENTE
TARGET_CHAT_NAME=Gastos Personal      # Como aparece en WhatsApp
```

3. **Debug del selector de chat:**
```bash
# Ejecutar en modo debug y observar logs
DEBUG_MODE=true
LOG_LEVEL=DEBUG
python main.py --mode dev
```

---

### Mensajes no se procesan

**Síntoma:**
```
Bot ejecutándose pero no procesa mensajes enviados
Estadísticas muestran 0 gastos registrados
```

**Causa:** Mensajes no se detectan como nuevos o formato incorrecto.

**Solución:**

1. **Verificar formato de mensaje:**
```bash
# ✅ Formatos correctos
gasto: 500 comida
500 super
gasté 150 nafta

# ❌ Formatos incorrectos
$500 comida               # No usar símbolo $
500 comida rapida         # Categoría con espacios
quinientos comida         # Solo números
```

2. **Verificar categorías:**
```bash
# Ver categorías válidas
python main.py --config | grep -A5 "Categorías"

# Probar con categoría segura
gasto: 100 comida
```

3. **Activar debug para ver procesamiento:**
```bash
LOG_LEVEL=DEBUG
python main.py --mode dev

# Enviar mensaje y observar logs detallados
```

---

## 📊 Problemas de Procesamiento

### Error: "Monto inválido"

**Síntoma:**
```
ValueError: El monto debe ser positivo
Error procesando mensaje: No se puede convertir 'abc' a Decimal
```

**Causa:** Formato de monto no reconocido.

**Solución:**

1. **Formatos válidos de monto:**
```bash
# ✅ Correcto
100
150.50
1000

# ❌ Incorrecto
$100        # Sin símbolo de moneda
100,50      # Usar punto, no coma
cien        # Solo números
100.5.0     # Formato decimal inválido
```

2. **Rangos válidos:**
```bash
# Verificar límites en logs
python -c "
from shared.constants import Limits
print(f'Monto mínimo: ${Limits.MIN_AMOUNT}')
print(f'Monto máximo: ${Limits.MAX_AMOUNT:,}')
"
```

---

### Error: "Categoría inválida"

**Síntoma:**
```
ValueError: Categoría 'xyz' no es válida. ¿Quisiste decir: comida, casa?
```

**Causa:** Categoría no está en lista de válidas.

**Solución:**

1. **Ver categorías válidas:**
```bash
python main.py --config | grep "Válidas:"
```

2. **Agregar nueva categoría:**
```bash
# Editar config/.env
VALID_CATEGORIES=comida,transporte,entretenimiento,salud,servicios,ropa,educacion,hogar,trabajo,otros,super,nafta,nueva_categoria
```

3. **Permitir categorías automáticas:**
```bash
ALLOW_NEW_CATEGORIES=true
```

---

### Gastos duplicados

**Síntoma:**
```
El mismo gasto aparece múltiples veces
Warning: Gasto parece ser duplicado reciente
```

**Causa:** Mensaje procesado múltiples veces.

**Solución:**

1. **El bot tiene protección automática** (5 minutos)
2. **Verificar intervalo de polling:**
```bash
# No usar intervalos muy bajos
WHATSAPP_POLL_INTERVAL=30    # Recomendado
# No: WHATSAPP_POLL_INTERVAL=5   # Demasiado frecuente
```

3. **Limpiar duplicados manualmente:**
```bash
# Abrir Excel y filtrar por fecha/hora
# O usar script de limpieza (futuro)
```

---

## 💾 Problemas de Almacenamiento

### Error: "No se puede abrir Excel"

**Síntoma:**
```
PermissionError: [Errno 13] Permission denied: 'data/gastos.xlsx'
BadZipFile: File is not a zip file
```

**Causa:** Excel abierto en otra aplicación o archivo corrupto.

**Solución:**

1. **Cerrar Excel:**
```bash
# Cerrar Microsoft Excel completamente
# Verificar en Task Manager que no esté en segundo plano
```

2. **Verificar archivo:**
```bash
# Ver información del archivo
ls -la data/gastos.xlsx
file data/gastos.xlsx    # Linux/macOS

# Windows:
dir data\gastos.xlsx
```

3. **Recrear archivo si está corrupto:**
```bash
# Hacer backup del archivo corrupto
mv data/gastos.xlsx data/gastos_corrupto.xlsx

# El bot creará nuevo archivo automáticamente
python main.py --test-storage
```

---

### Datos no se guardan

**Síntoma:**
```
Bot procesa mensajes pero Excel está vacío
Success logs pero no hay datos
```

**Causa:** Problema en escritura o permisos.

**Solución:**

1. **Verificar permisos:**
```bash
# Linux/macOS
ls -la data/
chmod 755 data/
chmod 644 data/gastos.xlsx

# Windows - ejecutar como administrador
```

2. **Probar escritura manual:**
```bash
python -c "
from infrastructure.storage.excel_writer import ExcelStorage
from domain.models.gasto import Gasto
from decimal import Decimal
from datetime import datetime

storage = ExcelStorage('data/test_gastos.xlsx')
gasto = Gasto(Decimal('100'), 'test', datetime.now())
result = storage.guardar_gasto(gasto)
print(f'Test resultado: {result}')
"
```

3. **Verificar logs detallados:**
```bash
LOG_LEVEL=DEBUG
python main.py --mode dev
# Revisar logs/bot.log para errores específicos
```

---

## ⚡ Problemas de Performance

### Bot muy lento

**Síntoma:**
```
Operaciones tardan mucho tiempo
Warnings: "Operación lenta detectada"
```

**Causa:** Configuración no optimizada o recursos limitados.

**Solución:**

1. **Optimizar intervalos:**
```bash
# Reducir frecuencia si no es necesaria alta responsividad
WHATSAPP_POLL_INTERVAL=60     # En lugar de 10-30

# Aumentar timeout para conexiones lentas
WHATSAPP_TIMEOUT=20          # En lugar de 10
```

2. **Modo headless:**
```bash
# Usar menos recursos gráficos
CHROME_HEADLESS=true
```

3. **Optimizar logging:**
```bash
# Reducir logs si no son necesarios
LOG_LEVEL=WARNING    # En lugar de INFO/DEBUG
LOG_CONSOLE=false    # Solo archivo
```

---

### Alto uso de memoria

**Síntoma:**
```
El bot consume mucha RAM
El sistema se vuelve lento
```

**Causa:** Chrome consume memoria, acumulación de objetos.

**Solución:**

1. **Optimizar Chrome:**
```bash
# Modo headless usa menos memoria
CHROME_HEADLESS=true

# Reiniciar bot periódicamente (cron job)
# Cada 24 horas en crontab:
# 0 0 * * * /path/to/restart_bot.sh
```

2. **Monitorear memoria:**
```bash
# Linux/macOS
ps aux | grep python
top -p $(pgrep -f "python.*main.py")

# Windows
tasklist | findstr python
```

---

## 📝 Logs y Debugging

### Activar Logging Detallado

```bash
# Configurar debug completo
DEBUG_MODE=true
LOG_LEVEL=DEBUG
LOG_CONSOLE=true
python main.py --mode dev
```

### Interpretar Logs Comunes

#### Logs Normales
```
INFO - Iniciando componentes del bot...
INFO - Storage Excel inicializado: data/gastos.xlsx
INFO - Bot iniciado. Presiona Ctrl+C para detener.
INFO - 💰 Gasto registrado: $150.00 - comida
```

#### Logs de Warning
```
WARNING - Gasto parece ser duplicado reciente
WARNING - Operación lenta detectada: procesar_mensaje tomó 2.15s
WARNING - No se pudieron extraer datos del mensaje
```

#### Logs de Error
```
ERROR - Error conectando con WhatsApp
ERROR - Error guardando gasto en Excel: [Errno 13] Permission denied
ERROR - Error procesando mensaje: ValueError: El monto debe ser positivo
```

### Ubicaciones de Logs

```bash
# Archivo principal de logs
tail -f logs/bot.log

# Logs del sistema (si ejecutas como servicio)
# Linux:
journalctl -f -u bot-gastos

# Windows:
# Event Viewer > Windows Logs > Application
```

---

## 🛠️ Herramientas de Diagnóstico

### Script de Diagnóstico Automático

Crear `diagnose.py`:

```python
#!/usr/bin/env python3
"""Script de diagnóstico para Bot Gastos WhatsApp"""

import sys
import os
import subprocess
from pathlib import Path

def check_python():
    print(f"✅ Python: {sys.version}")
    return True

def check_dependencies():
    deps = ['selenium', 'openpyxl']
    for dep in deps:
        try:
            module = __import__(dep)
            version = getattr(module, '__version__', 'unknown')
            print(f"✅ {dep}: {version}")
        except ImportError:
            print(f"❌ {dep}: No instalado")
            return False
    return True

def check_chrome():
    try:
        result = subprocess.run(['google-chrome', '--version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Chrome: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass
    
    try:
        result = subprocess.run(['chrome', '--version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Chrome: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass
    
    print("❌ Chrome: No encontrado")
    return False

def check_files():
    required_files = [
        'main.py', 'requirements.txt', 'config/.env.example',
        'app/', 'domain/', 'infrastructure/', 'shared/'
    ]
    
    for file_path in required_files:
        path = Path(file_path)
        if path.exists():
            print(f"✅ {file_path}: Existe")
        else:
            print(f"❌ {file_path}: No encontrado")
            return False
    return True

def check_permissions():
    test_dirs = ['data', 'logs']
    for dir_name in test_dirs:
        try:
            os.makedirs(dir_name, exist_ok=True)
            test_file = Path(dir_name) / 'test_write'
            test_file.write_text('test')
            test_file.unlink()
            print(f"✅ {dir_name}/: Escribible")
        except Exception as e:
            print(f"❌ {dir_name}/: Error de permisos - {e}")
            return False
    return True

def main():
    print("🔍 DIAGNÓSTICO BOT GASTOS WHATSAPP")
    print("=" * 40)
    
    checks = [
        ("Python", check_python),
        ("Dependencias", check_dependencies),
        ("Chrome", check_chrome),
        ("Archivos", check_files),
        ("Permisos", check_permissions)
    ]
    
    all_good = True
    for name, check_func in checks:
        print(f"\n--- {name} ---")
        if not check_func():
            all_good = False
    
    print("\n" + "=" * 40)
    if all_good:
        print("✅ DIAGNÓSTICO EXITOSO - Todo parece estar bien")
        print("\nPrueba ejecutar:")
        print("  python main.py --validate-config")
        print("  python main.py --test-storage")
    else:
        print("❌ PROBLEMAS ENCONTRADOS - Revisar errores arriba")
    
    return 0 if all_good else 1

if __name__ == '__main__':
    exit(main())
```

```bash
# Ejecutar diagnóstico
python diagnose.py
```

### Comandos de Diagnóstico Rápido

```bash
# Diagnóstico completo
python main.py --validate-config
python main.py --config
python main.py --test-storage

# Información del sistema
python -c "
import platform
import sys
from pathlib import Path
print(f'OS: {platform.system()} {platform.release()}')
print(f'Python: {sys.version}')
print(f'Directorio: {Path.cwd()}')
print(f'Ejecutable: {sys.executable}')
"

# Estado de archivos importantes
ls -la main.py config/.env data/ logs/ 2>/dev/null || dir main.py config\.env data logs 2>nul
```

---

## 🚨 Problemas Críticos

### Bot se cierra inesperadamente

**Síntoma:**
```
Bot se detiene sin error claro
Proceso termina abruptamente
```

**Solución:**

1. **Ejecutar con logs completos:**
```bash
DEBUG_MODE=true
LOG_LEVEL=DEBUG
python main.py --mode dev 2>&1 | tee debug_output.log
```

2. **Verificar memoria disponible:**
```bash
# Linux
free -h
# macOS
vm_stat
# Windows
systeminfo | findstr Memory
```

3. **Ejecutar con supervisor:**
```bash
# Crear script que reinicie automáticamente
while true; do
    python main.py
    echo "Bot se cerró, reiniciando en 30 segundos..."
    sleep 30
done
```

---

### Datos perdidos/corruptos

**Síntoma:**
```
Archivo Excel corrupto
Datos faltantes
BadZipFile error
```

**Solución de Emergencia:**

1. **Restaurar desde backup:**
```bash
# Buscar backups automáticos
ls -la data/*backup*

# Restaurar último backup
cp data/gastos_backup_20250806_143000.xlsx data/gastos.xlsx
```

2. **Recuperar datos de logs:**
```bash
# Extraer gastos de logs
grep "Gasto registrado" logs/bot.log > gastos_recuperados.txt

# Formato típico:
# INFO - 💰 Gasto registrado: $150.00 - comida
```

3. **Prevenir corrupción futura:**
```bash
# Habilitar backups automáticos
EXCEL_AUTO_BACKUP=true
DB_BACKUP_ENABLED=true

# Verificar integridad regularmente
python main.py --test-storage
```

---

## 📞 Cuándo Pedir Ayuda

### Información para Reportar Issues

Cuando reportes un problema, incluye:

```bash
# 1. Información del sistema
python main.py --version
python main.py --validate-config

# 2. Configuración (sin datos sensibles)
python main.py --config

# 3. Logs relevantes (últimas 50 líneas)
tail -50 logs/bot.log

# 4. Comando que causa el error
# 5. Mensaje de error completo
# 6. Pasos para reproducir el problema
```

### Problemas que Requieren Soporte Inmediato

- Pérdida de datos importante
- Bot compromete seguridad del sistema
- Errores que no se resuelven con esta guía
- Bugs en funcionalidades principales

### Recursos de Soporte

- **GitHub Issues**: Para bugs y mejoras
- **Documentación**: [docs/](.) para referencia completa
- **Community**: Foros de usuarios (si están disponibles)

---

¡Con esta guía de troubleshooting deberías poder resolver la mayoría de problemas del Bot Gastos WhatsApp! 🛠️

Si encuentras un problema que no está cubierto aquí, no dudes en reportarlo para que podamos mejorar esta documentación.