# 🚀 Guía de Uso Paso a Paso - Bot de Gastos WhatsApp

## 📋 Índice
1. [Requisitos Previos](#requisitos-previos)
2. [Instalación](#instalación)
3. [Configuración Inicial](#configuración-inicial)
4. [Primera Ejecución](#primera-ejecución)
5. [Uso del Bot](#uso-del-bot)
6. [Comandos y Formatos](#comandos-y-formatos)
7. [Solución de Problemas](#solución-de-problemas)
8. [Consejos y Trucos](#consejos-y-trucos)

---

## 🔧 Requisitos Previos

### Sistema
- ✅ Windows 10/11
- ✅ Python 3.8 o superior
- ✅ Google Chrome instalado
- ✅ Conexión a Internet
- ✅ WhatsApp Web funcionando

### Verificar Requisitos
```bash
# Verificar Python
python --version
# Debe mostrar: Python 3.8.x o superior

# Verificar Chrome
chrome --version
# Debe mostrar la versión instalada
```

---

## 📥 Instalación

### Paso 1: Instalar Dependencias

Abre **Command Prompt** como administrador y ejecuta:

```bash
# Navegar al directorio del proyecto
cd "C:\Users\vicen\OneDrive\Escritorio\apps\en progreso\bot gastos"

# Instalar dependencias
pip install -r requirements.txt
```

### Paso 2: Ejecutar Script de Instalación

```bash
# Windows
install.bat

# O manualmente
python scripts/install.py
```

### Paso 3: Verificar Instalación

```bash
python main.py --version
```

Deberías ver algo como:
```
Bot Gastos WhatsApp v1.0.0
Python 3.x.x
Ruta del proyecto: C:\Users\vicen\OneDrive\...
```

---

## ⚙️ Configuración Inicial

### Paso 1: Configurar Variables de Entorno (Opcional)

Crea un archivo `.env` en el directorio raíz:

```bash
# .env
TARGET_CHAT_NAME=Gastos Personal
WHATSAPP_POLL_INTERVAL=30
CHROME_HEADLESS=false
AUTO_RESPONSES_ENABLED=true
STORAGE_MODE=excel
LOG_LEVEL=INFO
```

### Paso 2: Verificar Configuración

```bash
python main.py --config
```

Deberías ver:
```
=== CONFIGURACIÓN ACTUAL ===

Modo de almacenamiento: excel
Archivo de datos: data/gastos.xlsx
Directorio del proyecto: C:\Users\vicen\...

--- WhatsApp ---
Chat objetivo: Gastos Personal
Intervalo polling: 30s
Timeout conexión: 60s
Chrome headless: False

--- Logging ---
Nivel: INFO
Archivo: logs/bot.log
Consola: True
```

### Paso 3: Probar Almacenamiento

```bash
python main.py --test-storage
```

---

## 🎬 Primera Ejecución

### Paso 1: Ejecutar el Bot

```bash
python main.py
```

Verás esta pantalla:
```
============================================================
🤖 BOT GASTOS WHATSAPP INICIADO
============================================================
📅 Inicio: 2024-01-15 10:30:00
💾 Storage: EXCEL
💬 Chat: Gastos Personal
⏰ Intervalo: 30s
📝 Log Level: INFO
============================================================
El bot está escuchando mensajes...
Presiona Ctrl+C para detener
============================================================
```

### Paso 2: Autenticación WhatsApp

1. **Se abrirá Chrome** automáticamente
2. **WhatsApp Web** se cargará
3. **Escanea el código QR** con tu teléfono:
   - Abre WhatsApp en tu teléfono
   - Ve a **Configuración** > **Dispositivos vinculados**
   - Toca **Vincular un dispositivo**
   - Escanea el código QR

### Paso 3: Selección de Chat

1. Una vez autenticado, el bot buscará el chat **"Gastos Personal"**
2. Si no existe, créalo:
   - Busca o crea un grupo/chat con ese nombre exacto
   - O cambia `TARGET_CHAT_NAME` en la configuración

### Paso 4: Confirmación

Cuando veas esto, ¡el bot está listo!:
```
✅ WhatsApp Enhanced connector inicializado correctamente
📱 Bot iniciado. Presiona Ctrl+C para detener
```

---

## 💬 Uso del Bot

### Formatos de Mensajes Soportados

#### 1. **Gastos Simples**
```
$150 comida almuerzo
1500 transporte taxi
$45.50 entretenimiento
300 super compras
```

#### 2. **Gastos con Descripción**
```
$150 comida almuerzo en el centro
1500 transporte taxi al aeropuerto
$45.50 entretenimiento cine con amigos
300 super compras semanales del hogar
```

#### 3. **Formatos Flexibles**
```
Gasté $25 en comida
Pagué 1200 de nafta
Se fueron $80 en entretenimiento
Compré ropa por $350
```

### Categorías Válidas
- `comida` - Restaurantes, delivery, snacks
- `transporte` - Taxi, colectivo, nafta, estacionamiento  
- `entretenimiento` - Cine, streaming, juegos
- `salud` - Medicamentos, consultas, farmacia
- `servicios` - Internet, luz, agua, teléfono
- `ropa` - Vestimenta, calzado, accesorios
- `educacion` - Cursos, libros, materiales
- `hogar` - Muebles, decoración, limpieza
- `trabajo` - Materiales, herramientas
- `super` - Supermercado, almacén
- `nafta` - Combustible
- `otros` - Todo lo demás

---

## 📱 Comandos Especiales

### Ayuda
```
ayuda
help
?
```
**Respuesta:** Manual completo de uso

### Estadísticas  
```
estadisticas
stats
resumen
```
**Respuesta:** Resumen de gastos del mes

### Categorías
```
categorias
categories
```
**Respuesta:** Lista de categorías válidas

---

## 🤖 Respuestas Automáticas del Bot

### ✅ Gasto Registrado Exitosamente
```
✅ *Gasto Registrado*
💰 Monto: $150.00
📝 Categoría: comida
📅 Fecha: 15/01/2024
📄 Descripción: almuerzo en el centro
🎯 Confianza: 90%
```

### ❌ Error en el Mensaje
```
❌ *Error Procesando Mensaje*
🚨 Error: Formato no válido
📝 Mensaje: xyz123...
💡 Intenta reformular o usar: '$monto categoria descripcion'
```

### 🤔 Sugerencias (cuando hay ambigüedad)
```
🤔 *Sugerencias de Gasto*
Encontré varias opciones:

1. $45.50 - comida (85%)
2. $145.50 - entretenimiento (60%)
3. $4.50 - otros (30%)

💬 Responde con el número de la opción correcta
```

---

## 📸 Procesamiento de Imágenes

### Enviar Foto de Recibo
1. **Toma una foto** del recibo/factura
2. **Envíala al chat** configurado
3. **El bot procesará** con OCR automáticamente
4. **Recibirás la confirmación** o sugerencias

### Mejores Prácticas para Fotos
- ✅ **Buena iluminación**
- ✅ **Enfoque nítido**
- ✅ **Texto legible**
- ✅ **Recibo completo en la imagen**
- ❌ Evitar sombras
- ❌ Evitar reflejos

---

## 🛠️ Solución de Problemas

### Problema 1: "Chrome not found"
**Solución:**
```bash
# Instalar Chrome
# Descargar desde: https://www.google.com/chrome/
# O usar Chocolatey:
choco install googlechrome
```

### Problema 2: "Error conectando con WhatsApp Web"
**Solución:**
1. Verificar conexión a Internet
2. Cerrar otras sesiones de WhatsApp Web
3. Reiniciar el bot: `Ctrl+C` y volver a ejecutar
4. Limpiar cache de Chrome

### Problema 3: "No se encontró el chat"
**Solución:**
1. Verificar que el chat existe: **"Gastos Personal"**
2. Cambiar nombre del chat en configuración:
   ```bash
   set TARGET_CHAT_NAME="Mi Chat de Gastos"
   python main.py
   ```

### Problema 4: Bot no responde a mensajes
**Solución:**
1. Verificar que el chat esté seleccionado
2. Comprobar que hay mensajes nuevos (no leídos previamente)
3. Revisar logs: `logs/bot.log`
4. Verificar configuración:
   ```bash
   python main.py --config
   ```

### Problema 5: "Permission denied" o errores de archivos
**Solución:**
```bash
# Ejecutar como administrador
# O cambiar permisos:
icacls "data" /grant Users:F
icacls "logs" /grant Users:F
```

---

## 💡 Consejos y Trucos

### 1. **Modo Desarrollo**
Para debugging y más información:
```bash
python main.py --mode dev
```

### 2. **Desactivar Respuestas Automáticas**
Si solo quieres registrar sin que responda:
```bash
set AUTO_RESPONSES_ENABLED=false
python main.py
```

### 3. **Cambiar Intervalo de Polling**
Para respuestas más rápidas:
```bash
set WHATSAPP_POLL_INTERVAL=10
python main.py
```

### 4. **Modo Headless (sin ventana)**
Para ejecución en background:
```bash
set CHROME_HEADLESS=true
python main.py
```

### 5. **Ver Dashboard Web**
Para análisis visual:
```bash
python main.py --dashboard --port 5000
# Ir a: http://localhost:5000
```

### 6. **Backup Automático**
Los datos se respaldan automáticamente en `data/backups/`

### 7. **Ver Logs en Tiempo Real**
```bash
# En otra ventana de comandos:
tail -f logs/bot.log
```

---

## 🧪 Script de Pruebas

Para probar la integración paso a paso:

```bash
python examples/test_whatsapp_integration.py
```

Este script te permite:
- 🔌 Probar conexión
- 📤 Enviar mensajes de prueba
- 🧠 Probar procesamiento de mensajes
- 🔄 Modo respuestas automáticas
- 📊 Ver estadísticas
- ⚙️ Configurar parámetros en vivo

---

## 📊 Ver Resultados

### Archivo Excel
Los gastos se guardan en: `data/gastos.xlsx`
- Abre con Excel, LibreOffice o Google Sheets
- Columnas: Fecha, Monto, Categoría, Descripción

### Dashboard Web
```bash
python run_dashboard.py
# Ir a: http://localhost:5000
```

### Logs del Sistema
```bash
# Ver logs:
type logs\bot.log

# Ver últimas 50 líneas:
powershell "Get-Content logs\bot.log -Tail 50"
```

---

## 🚦 Estados del Bot

### 🟢 **Funcionando Correctamente**
```
💰 10:30:15 - $150.0 en comida
💰 10:35:22 - $45.50 en entretenimiento
📊 Estadísticas: 2h 15m ejecutando, 25 mensajes, 18 gastos, 0 errores
```

### 🟡 **Advertencias**
```
⚠️  Error enviando respuesta automática: Timeout
⚠️  Confianza OCR baja: 45%
```

### 🔴 **Errores**
```
❌ Error conectando con WhatsApp Web
❌ Demasiados errores, deteniendo bot
```

---

## 🎯 Ejemplo Completo de Uso

### 1. **Iniciar el Bot**
```bash
python main.py
```

### 2. **Escanear QR y Esperar**
```
📲 Escanea el código QR en WhatsApp Web...
✅ Login exitoso
✅ Chat seleccionado: Gastos Personal
🤖 Bot iniciado. Presiona Ctrl+C para detener
```

### 3. **Enviar Mensaje de Gasto**
En WhatsApp, envía: `$150 comida almuerzo en restaurante`

### 4. **Recibir Confirmación**
```
✅ *Gasto Registrado*
💰 Monto: $150.00
📝 Categoría: comida
📅 Fecha: 15/01/2024
📄 Descripción: almuerzo en restaurante
🎯 Confianza: 95%
```

### 5. **Ver en Consola**
```
💰 10:30:15 - $150.0 en comida
```

### 6. **Ver Estadísticas**
Envía: `estadisticas`
```
📊 *Resumen de Gastos*
📅 Desde: 2024-01-15 08:00:00
💰 Total gastado: $150.00
📝 Total gastos: 1
📈 Promedio: $150.00

🏷️ *Top Categorías:*
• comida: $150.00
```

### 7. **Detener el Bot**
Presiona `Ctrl+C`:
```
🛑 Detenido por usuario
🏁 Bot detenido después de 2:15:30
📊 Total: 18 gastos registrados, 0 errores
```

---

## 🎉 ¡Listo para Usar!

**Tu bot de gastos WhatsApp está completamente configurado y listo.**

Características principales:
- ✅ **Respuestas automáticas** con confirmaciones
- ✅ **Procesamiento inteligente** de texto e imágenes
- ✅ **Comando de ayuda** y estadísticas
- ✅ **Almacenamiento automático** en Excel
- ✅ **Dashboard web** para análisis
- ✅ **Logs detallados** para monitoring
- ✅ **Reconexión automática** si se desconecta

**¡Empieza a registrar tus gastos enviando mensajes al chat configurado! 🚀**