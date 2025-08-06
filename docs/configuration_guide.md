# ⚙️ Guía de Configuración - Bot Gastos WhatsApp

Esta guía detalla todas las opciones de configuración disponibles para personalizar el comportamiento del Bot Gastos WhatsApp.

## 📋 Tabla de Contenidos

- [Configuración Rápida](#configuración-rápida)
- [Variables de Entorno](#variables-de-entorno)
- [Configuración Avanzada](#configuración-avanzada)
- [Ejemplos de Configuración](#ejemplos-de-configuración)
- [Validación de Configuración](#validación-de-configuración)

---

## 🚀 Configuración Rápida

### Paso 1: Crear Archivo de Configuración

```bash
# Copiar template de configuración
cp config/.env.example config/.env

# Editar con tu editor favorito
nano config/.env        # Linux/macOS
notepad config/.env     # Windows
```

### Paso 2: Configuración Mínima

```bash
# Configuración básica que DEBES cambiar
TARGET_CHAT_NAME=Mi Chat de Gastos    # ¡Importante: nombre exacto!
STORAGE_MODE=excel                    # o 'sqlite'
CHROME_HEADLESS=false                 # true=invisible, false=visible
```

### Paso 3: Verificar Configuración

```bash
python main.py --validate-config
```

---

## 🔧 Variables de Entorno

### 📊 Configuración de Almacenamiento

#### `STORAGE_MODE`
**Propósito:** Define qué sistema de almacenamiento usar.
**Valores:** `excel` | `sqlite`
**Default:** `excel`
**Ejemplo:**
```bash
STORAGE_MODE=excel
```

#### `EXCEL_FILE_PATH`
**Propósito:** Ruta del archivo Excel donde guardar gastos.
**Default:** `data/gastos.xlsx`
**Ejemplo:**
```bash
EXCEL_FILE_PATH=data/mis_gastos.xlsx
EXCEL_FILE_PATH=/home/usuario/Documents/gastos.xlsx  # Ruta absoluta
```

#### `SQLITE_FILE_PATH`
**Propósito:** Ruta de la base de datos SQLite.
**Default:** `data/gastos.db`
**Ejemplo:**
```bash
SQLITE_FILE_PATH=data/gastos.db
```

#### `DB_BACKUP_ENABLED`
**Propósito:** Habilitar backups automáticos de base de datos.
**Valores:** `true` | `false`
**Default:** `true`
**Ejemplo:**
```bash
DB_BACKUP_ENABLED=true
```

#### `EXCEL_AUTO_BACKUP`
**Propósito:** Habilitar backups automáticos de Excel.
**Valores:** `true` | `false`
**Default:** `true`
**Ejemplo:**
```bash
EXCEL_AUTO_BACKUP=true
```

---

### 💬 Configuración de WhatsApp

#### `TARGET_CHAT_NAME` ⭐ **CRÍTICO**
**Propósito:** Nombre exacto del chat a monitorear.
**Importante:** Debe coincidir EXACTAMENTE con el nombre en WhatsApp Web.
**Ejemplo:**
```bash
TARGET_CHAT_NAME=Gastos Personal
TARGET_CHAT_NAME=Mis Gastos
TARGET_CHAT_NAME=Expense Tracker
```

**🚨 Errores Comunes:**
```bash
# ❌ Incorrecto
TARGET_CHAT_NAME=gastos personal      # Mayúsculas/minúsculas importan
TARGET_CHAT_NAME="Gastos Personal"    # No usar comillas en .env
TARGET_CHAT_NAME=Gastos  Personal     # Espacios extra

# ✅ Correcto
TARGET_CHAT_NAME=Gastos Personal      # Exactamente como aparece en WhatsApp
```

#### `WHATSAPP_POLL_INTERVAL`
**Propósito:** Segundos entre verificaciones de mensajes nuevos.
**Rango:** 5-300 segundos
**Default:** `30`
**Ejemplo:**
```bash
WHATSAPP_POLL_INTERVAL=30    # Verificar cada 30 segundos (recomendado)
WHATSAPP_POLL_INTERVAL=10    # Más responsivo (más recursos)
WHATSAPP_POLL_INTERVAL=60    # Menos recursos (menos responsivo)
```

#### `WHATSAPP_TIMEOUT`
**Propósito:** Timeout en segundos para operaciones de WhatsApp.
**Rango:** 5-60 segundos
**Default:** `10`
**Ejemplo:**
```bash
WHATSAPP_TIMEOUT=10          # 10 segundos (recomendado)
WHATSAPP_TIMEOUT=20          # Para conexiones lentas
```

#### `CHROME_HEADLESS`
**Propósito:** Ejecutar Chrome en modo invisible.
**Valores:** `true` | `false`
**Default:** `false`
**Ejemplo:**
```bash
CHROME_HEADLESS=false        # Ventana visible (debugging fácil)
CHROME_HEADLESS=true         # Invisible (menos recursos)
```

**💡 Cuándo usar cada modo:**
- `false`: Desarrollo, debugging, primera configuración
- `true`: Producción, servidores, uso automático

---

### 📝 Configuración de Logging

#### `LOG_LEVEL`
**Propósito:** Nivel de detalle en logs.
**Valores:** `DEBUG` | `INFO` | `WARNING` | `ERROR`
**Default:** `INFO`
**Ejemplo:**
```bash
LOG_LEVEL=INFO               # Nivel normal
LOG_LEVEL=DEBUG              # Máximo detalle (desarrollo)
LOG_LEVEL=WARNING            # Solo advertencias y errores
LOG_LEVEL=ERROR              # Solo errores críticos
```

#### `LOG_FILE_PATH`
**Propósito:** Archivo donde guardar logs.
**Default:** `logs/bot.log`
**Ejemplo:**
```bash
LOG_FILE_PATH=logs/bot.log
LOG_FILE_PATH=/var/log/bot_gastos.log    # Ruta del sistema
```

#### `LOG_CONSOLE`
**Propósito:** Mostrar logs también en consola.
**Valores:** `true` | `false`
**Default:** `true`
**Ejemplo:**
```bash
LOG_CONSOLE=true             # Ver logs en tiempo real
LOG_CONSOLE=false            # Solo archivo de log
```

---

### 🏷️ Configuración de Categorías

#### `VALID_CATEGORIES`
**Propósito:** Lista de categorías válidas (separadas por comas).
**Default:** `comida,transporte,entretenimiento,salud,servicios,ropa,educacion,hogar,trabajo,otros,super,nafta`
**Ejemplo:**
```bash
# Categorías por defecto
VALID_CATEGORIES=comida,transporte,entretenimiento,salud,servicios,ropa,educacion,hogar,trabajo,otros,super,nafta

# Categorías personalizadas
VALID_CATEGORIES=comida,transporte,casa,trabajo,personal,entretenimiento

# Categorías en inglés
VALID_CATEGORIES=food,transport,entertainment,health,services,shopping,home,work,others
```

#### `ALLOW_NEW_CATEGORIES`
**Propósito:** Permitir crear nuevas categorías automáticamente.
**Valores:** `true` | `false`
**Default:** `true`
**Ejemplo:**
```bash
ALLOW_NEW_CATEGORIES=true    # Flexible: acepta nuevas categorías
ALLOW_NEW_CATEGORIES=false   # Estricto: solo categorías predefinidas
```

#### `STRICT_CATEGORY_VALIDATION`
**Propósito:** Validación estricta de categorías.
**Valores:** `true` | `false`
**Default:** `false`
**Ejemplo:**
```bash
STRICT_CATEGORY_VALIDATION=false    # Permite variantes similares
STRICT_CATEGORY_VALIDATION=true     # Solo categorías exactas
```

---

### 🔧 Configuración General

#### `DEBUG_MODE`
**Propósito:** Habilitar modo debug con información adicional.
**Valores:** `true` | `false`
**Default:** `false`
**Ejemplo:**
```bash
DEBUG_MODE=false             # Modo normal
DEBUG_MODE=true              # Información extra, logs detallados
```

---

## 🎛️ Configuración Avanzada

### Configuración Programática

Además de variables de entorno, puedes configurar el sistema programáticamente:

```python
# config/custom_settings.py
from config.settings import Settings, StorageMode, LogLevel

def get_custom_settings() -> Settings:
    settings = Settings()
    
    # Configuración personalizada
    settings.storage_mode = StorageMode.EXCEL
    settings.whatsapp.poll_interval_seconds = 15
    settings.logging.level = LogLevel.DEBUG
    
    # Categorías personalizadas
    settings.categorias.categorias_validas.add('streaming')
    settings.categorias.categorias_validas.add('mascotas')
    
    return settings
```

### Configuración por Perfil

Crear diferentes archivos de configuración para distintos entornos:

**`.env.development`:**
```bash
DEBUG_MODE=true
LOG_LEVEL=DEBUG
CHROME_HEADLESS=false
WHATSAPP_POLL_INTERVAL=10
LOG_CONSOLE=true
```

**`.env.production`:**
```bash
DEBUG_MODE=false
LOG_LEVEL=WARNING
CHROME_HEADLESS=true
WHATSAPP_POLL_INTERVAL=30
LOG_CONSOLE=false
```

**Uso:**
```bash
# Copiar configuración según entorno
cp .env.development .env      # Para desarrollo
cp .env.production .env       # Para producción
```

---

## 📋 Ejemplos de Configuración

### Configuración para Usuario Casual

Uso ocasional, pocas transacciones diarias:

```bash
# Almacenamiento simple
STORAGE_MODE=excel
EXCEL_FILE_PATH=data/gastos.xlsx

# WhatsApp relajado
TARGET_CHAT_NAME=Mis Gastos
WHATSAPP_POLL_INTERVAL=60
CHROME_HEADLESS=false

# Logging básico
LOG_LEVEL=INFO
LOG_CONSOLE=true

# Categorías flexibles
VALID_CATEGORIES=comida,transporte,entretenimiento,salud,otros
ALLOW_NEW_CATEGORIES=true
```

### Configuración para Usuario Power

Uso intensivo, muchas transacciones:

```bash
# Base de datos para mejor performance
STORAGE_MODE=sqlite
SQLITE_FILE_PATH=data/gastos.db
DB_BACKUP_ENABLED=true

# WhatsApp responsivo
TARGET_CHAT_NAME=Gastos Personales
WHATSAPP_POLL_INTERVAL=15
CHROME_HEADLESS=true

# Logging detallado
LOG_LEVEL=INFO
LOG_CONSOLE=false
LOG_FILE_PATH=logs/gastos.log

# Categorías específicas y estrictas
VALID_CATEGORIES=comida,almuerzo,cena,transporte,uber,taxi,super,farmacia,ropa,entretenimiento,servicios,combustible
ALLOW_NEW_CATEGORIES=false
STRICT_CATEGORY_VALIDATION=true
```

### Configuración para Servidor/Producción

Ejecutándose en servidor sin interfaz gráfica:

```bash
# Configuración de servidor
DEBUG_MODE=false
CHROME_HEADLESS=true

# Almacenamiento robusto
STORAGE_MODE=sqlite
SQLITE_FILE_PATH=/var/lib/bot-gastos/gastos.db
DB_BACKUP_ENABLED=true

# WhatsApp optimizado
WHATSAPP_POLL_INTERVAL=30
WHATSAPP_TIMEOUT=15

# Logging para servidor
LOG_LEVEL=WARNING
LOG_CONSOLE=false
LOG_FILE_PATH=/var/log/bot-gastos/bot.log

# Configuración estable
ALLOW_NEW_CATEGORIES=false
STRICT_CATEGORY_VALIDATION=true
```

### Configuración para Desarrollo/Debug

Para desarrolladores trabajando en el código:

```bash
# Desarrollo
DEBUG_MODE=true
CHROME_HEADLESS=false

# Almacenamiento de prueba
STORAGE_MODE=excel
EXCEL_FILE_PATH=data/test_gastos.xlsx

# WhatsApp para testing
TARGET_CHAT_NAME=Test Gastos
WHATSAPP_POLL_INTERVAL=5
WHATSAPP_TIMEOUT=30

# Logging máximo
LOG_LEVEL=DEBUG
LOG_CONSOLE=true

# Categorías de prueba
VALID_CATEGORIES=test1,test2,test3,comida,transporte
ALLOW_NEW_CATEGORIES=true
```

---

## ✅ Validación de Configuración

### Comando de Validación

```bash
# Validar configuración completa
python main.py --validate-config
```

**Salida exitosa:**
```
=== VALIDACIÓN DE CONFIGURACIÓN ===
✅ Configuración válida
```

**Salida con errores:**
```
=== VALIDACIÓN DE CONFIGURACIÓN ===
❌ Errores encontrados:
  - El intervalo de polling no puede ser menor a 5 segundos
  - Ruta de almacenamiento inválida: [Errno 2] No such file or directory
```

### Validaciones Automáticas

El sistema valida automáticamente:

#### Intervalos de Tiempo
- `WHATSAPP_POLL_INTERVAL` >= 5 segundos
- `WHATSAPP_TIMEOUT` >= 5 segundos

#### Rutas de Archivos
- Directorio padre existe o se puede crear
- Permisos de escritura disponibles

#### Categorías
- Al menos una categoría válida definida
- Formato correcto (sin espacios, caracteres especiales)

#### Configuración Lógica
- Consistencia entre modo de almacenamiento y rutas
- Configuración de logging válida

### Validación Manual

```python
from config.settings import get_settings

# Obtener configuración
settings = get_settings()

# Validar manualmente
errors = settings.validate_configuration()

if errors:
    print("Errores encontrados:")
    for error in errors:
        print(f"  - {error}")
else:
    print("✅ Configuración válida")
```

---

## 🔍 Diagnosticar Problemas de Configuración

### Ver Configuración Actual

```bash
# Mostrar toda la configuración
python main.py --config
```

**Salida típica:**
```
=== CONFIGURACIÓN ACTUAL ===

Modo de almacenamiento: excel
Archivo de datos: data/gastos.xlsx
Directorio del proyecto: /home/user/bot-gastos
Modo debug: false

--- WhatsApp ---
Chat objetivo: Gastos Personal
Intervalo polling: 30s
Timeout conexión: 10s
Chrome headless: false

--- Logging ---
Nivel: INFO
Archivo: logs/bot.log
Consola: true

--- Categorías ---
Válidas: comida, educacion, entretenimiento, hogar, nafta, otros, ropa, salud, servicios, super, trabajo, transporte
Permitir nuevas: true
Validación estricta: false
```

### Probar Almacenamiento

```bash
# Probar sistema de almacenamiento
python main.py --test-storage
```

### Variables de Entorno Activas

```bash
# Ver variables de entorno del bot
env | grep -E "(STORAGE|WHATSAPP|LOG|TARGET|CHROME|VALID)" | sort
```

---

## 🔧 Configuración Dinámica

### Cambiar Configuración en Runtime

Algunas configuraciones se pueden cambiar sin reiniciar el bot:

```python
# En modo desarrollo, puedes modificar configuración
from config.settings import get_settings, reload_settings

# Modificar variable de entorno
import os
os.environ['LOG_LEVEL'] = 'DEBUG'

# Recargar configuración
settings = reload_settings()
```

### Hot Reload de Categorías

```python
from domain.value_objects.categoria import Categoria

# Agregar nueva categoría dinámicamente
Categoria.agregar_categoria_valida("streaming")
Categoria.agregar_categoria_valida("mascotas")

# Verificar
print(Categoria.obtener_categorias_validas())
```

---

## 📊 Configuración por Casos de Uso

### Caso: Familia con Múltiples Usuarios

```bash
# Usar chat familiar
TARGET_CHAT_NAME=Gastos Familia

# Categorías familiares
VALID_CATEGORIES=comida,super,casa,niños,colegio,salud,transporte,servicios,entretenimiento,mascotas

# Backup habilitado
EXCEL_AUTO_BACKUP=true
DB_BACKUP_ENABLED=true
```

### Caso: Freelancer/Autónomo

```bash
# Categorías de negocio
VALID_CATEGORIES=trabajo,oficina,equipos,transporte,comida,servicios,impuestos,seguros,capacitacion

# Logging detallado para impuestos
LOG_LEVEL=INFO
DEBUG_MODE=true

# Respaldo robusto
STORAGE_MODE=sqlite
DB_BACKUP_ENABLED=true
```

### Caso: Estudiante

```bash
# Categorías estudiantiles
VALID_CATEGORIES=comida,transporte,libros,universidad,entretenimiento,ropa,salud

# Almacenamiento simple
STORAGE_MODE=excel
EXCEL_FILE_PATH=data/gastos_estudiante.xlsx

# Recursos mínimos
WHATSAPP_POLL_INTERVAL=60
CHROME_HEADLESS=true
LOG_LEVEL=WARNING
```

---

## 🔒 Configuración de Seguridad

### Variables Sensibles

**❌ NUNCA incluir en .env:**
- Contraseñas
- Tokens de API
- Información personal identificable

**✅ Para información sensible:**
```bash
# Usar variables de entorno del sistema
export SENSITIVE_VAR=valor_secreto

# O archivos de configuración separados con permisos restrictivos
chmod 600 config/secrets.env
```

### Permisos de Archivos

```bash
# Configuración segura de permisos
chmod 600 config/.env          # Solo owner puede leer/escribir
chmod 755 data/                # Directorio accesible
chmod 644 data/gastos.xlsx     # Archivo legible por owner y grupo
chmod 600 logs/bot.log         # Log privado
```

---

## 📞 Soporte de Configuración

### Preguntas Frecuentes

**Q: ¿Puedo cambiar la configuración sin reiniciar el bot?**
A: Algunas configuraciones sí (categorías), otras requieren reinicio (almacenamiento, WhatsApp).

**Q: ¿Cómo resetear a configuración por defecto?**
A: `cp config/.env.example config/.env`

**Q: ¿El bot funciona sin archivo .env?**
A: Sí, usa valores por defecto, pero necesita configuración mínima de WhatsApp.

**Q: ¿Puedo tener múltiples configuraciones?**
A: Sí, crea múltiples archivos .env y copia el que necesites.

### Información para Soporte

Si necesitas ayuda con configuración, incluye esta información:

```bash
# Información del sistema
python main.py --version
python main.py --validate-config
python main.py --config

# Variables de entorno (sin información sensible)
env | grep -E "(STORAGE|LOG|TARGET)" | sort
```

---

¡Con esta configuración personalizada, tu Bot Gastos WhatsApp estará optimizado para tus necesidades específicas! 🎯