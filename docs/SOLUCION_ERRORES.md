# 🛠️ Solución de Errores de Instalación

## ❌ Errores Encontrados

1. **ModuleNotFoundError: No module named 'psutil'**
2. **'LogLevel' object has no attribute 'upper'**  
3. **Archivo de configuración no existe: config\config.yaml**

---

## ✅ Solución Rápida

### Paso 1: Ejecutar Script de Corrección

```bash
# Ejecutar el script de corrección
install_fix.bat
```

Este script:
- ✅ Instala `psutil` y otras dependencias faltantes
- ✅ Actualiza todas las dependencias
- ✅ Crea directorios necesarios
- ✅ Verifica la instalación

### Paso 2: Verificar Corrección

```bash
python main.py --version
```

Deberías ver:
```
Bot Gastos WhatsApp v1.0.0
Python 3.x.x
Ruta del proyecto: C:\Users\vicen\...
```

---

## 🔧 Solución Manual (Si el script falla)

### Error 1: Dependencia psutil faltante

```bash
# Instalar psutil específicamente
pip install psutil>=5.9.0

# Instalar todas las dependencias
pip install -r requirements.txt
```

### Error 2: LogLevel enum

**Ya corregido automáticamente en el código.** El problema era que se intentaba llamar `.upper()` en un enum en lugar de su valor string.

### Error 3: Archivo de configuración

```bash
# El archivo config.yaml se crea automáticamente
# No necesitas hacer nada, es normal este mensaje
```

---

## 🚀 Instalación Completa Paso a Paso

### Opción A: Script Automático (Recomendado)

```bash
# 1. Abrir Command Prompt como Administrador
# 2. Navegar al directorio
cd "C:\Users\vicen\OneDrive\Escritorio\apps\en progreso\bot gastos"

# 3. Ejecutar script de corrección
install_fix.bat

# 4. Ejecutar el bot
python main.py
```

### Opción B: Instalación Manual

```bash
# 1. Crear entorno virtual (opcional pero recomendado)
python -m venv venv
venv\Scripts\activate

# 2. Actualizar pip
python -m pip install --upgrade pip

# 3. Instalar dependencias una por una
pip install selenium>=4.15.0
pip install openpyxl>=3.1.0
pip install psutil>=5.9.0
pip install pyyaml>=6.0.0
pip install requests>=2.31.0
pip install Pillow>=10.0.0
pip install flask>=2.3.0
pip install flask-cors>=4.0.0
pip install rich>=13.0.0
pip install pandas>=2.0.0
pip install scikit-learn>=1.3.0

# 4. Crear directorios
mkdir data
mkdir logs
mkdir config

# 5. Ejecutar el bot
python main.py
```

---

## 🧪 Verificación de la Instalación

### Test Básico

```bash
# Verificar versión
python main.py --version

# Verificar configuración
python main.py --config

# Probar almacenamiento
python main.py --test-storage
```

### Test de Dependencias

```bash
python -c "
import selenium
import openpyxl  
import psutil
import yaml
import requests
print('✅ Todas las dependencias principales están instaladas')
"
```

### Test de WhatsApp (Opcional)

```bash
# Solo si Chrome está instalado
python examples/test_whatsapp_integration.py
```

---

## 📋 Lista de Verificación

Después de la instalación, verifica que tengas:

- ✅ **Python 3.8+** instalado
- ✅ **Google Chrome** instalado
- ✅ **Todas las dependencias** de requirements.txt
- ✅ **Directorios** data/ y logs/ creados
- ✅ **Sin errores** al ejecutar `python main.py --version`

---

## 🐛 Solución de Problemas Adicionales

### "pip no reconocido como comando"

```bash
# Usar python -m pip en lugar de pip
python -m pip install -r requirements.txt
```

### "Permission denied" en Windows

```bash
# Ejecutar Command Prompt como Administrador
# O usar --user flag:
pip install -r requirements.txt --user
```

### "Chrome not found"

1. **Instalar Chrome**: https://www.google.com/chrome/
2. **Verificar instalación**: 
   ```bash
   chrome --version
   ```

### Error de "SSL Certificate"

```bash
# Actualizar certificates
pip install --upgrade certifi

# O usar trusted host:
pip install -r requirements.txt --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org
```

---

## 🎯 Resultado Esperado

Después de seguir estos pasos, deberías poder ejecutar:

```bash
python main.py
```

Y ver:

```
============================================================
🤖 BOT GASTOS WHATSAPP INICIADO  
============================================================
📅 Inicio: 2024-08-06 16:45:00
💾 Storage: EXCEL
💬 Chat: Gastos Personal
⏰ Intervalo: 30s
📝 Log Level: INFO
============================================================
El bot está escuchando mensajes...
Presiona Ctrl+C para detener
============================================================
```

**¡Tu bot está listo para usar! 🚀**