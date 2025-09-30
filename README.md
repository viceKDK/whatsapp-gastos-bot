# 🤖 Bot Gastos WhatsApp

Bot personal ultra-rápido que automatiza el registro de gastos desde mensajes de WhatsApp Web, utilizando Python 3 con arquitectura en capas limpia.

## ✨ Características Principales

- ⚡ **Detección Instantánea**: Respuesta en <1s con polling de 1 segundo
- 🚀 **Ultra-Optimizado**: Timeouts reducidos y procesamiento acelerado
- ✅ **Automatización WhatsApp Web**: Lee mensajes automáticamente usando Selenium
- 🧠 **Procesamiento Inteligente**: Extrae monto y categoría de texto natural
- 💾 **Almacenamiento Híbrido**: SQLite cache + Excel para máxima velocidad
- 🏗️ **Arquitectura Limpia**: Separación clara de responsabilidades
- ⚙️ **Configuración Flexible**: YAML y variables de entorno
- 📝 **Logging Completo**: Sistema de logs robusto con rotación
- 🔇 **Modo Invisible**: Ejecución en segundo plano sin ventanas

## 🚀 Instalación Rápida

### Pre-requisitos

- Python 3.9 o superior
- Google Chrome instalado
- WhatsApp Web configurado en tu navegador

### 1. Instalación Automática

**Windows:**
```bash
# Ejecutar instalador automático
scripts/install/install.bat
```

**Linux/Mac:**
```bash
# Ejecutar instalador automático
bash scripts/install/install.sh
```

### 2. Instalación Manual

```bash
# Clonar repositorio
cd bot-gastos

# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

## ⚙️ Configuración

### Configuración Rápida

El archivo principal de configuración es `config/config.yaml`:

```yaml
whatsapp:
  target_chat_name: Gastos          # Nombre del chat de WhatsApp
  chrome_headless: true             # true=invisible, false=visible
  connection_timeout_seconds: 10    # Timeout de conexión
  message_polling_interval_seconds: 1  # Intervalo de polling (ultra-rápido)

storage:
  primary_storage: excel
  excel_file_path: data/gastos.xlsx

logging:
  level: INFO
  console_enabled: false            # Modo silencioso
```

### Variables de Entorno (Opcional)

También puedes usar variables de entorno que sobreescriben el YAML:

```bash
STORAGE_MODE=excel
TARGET_CHAT_NAME=Gastos Personal
WHATSAPP_POLL_INTERVAL=1
CHROME_HEADLESS=true
LOG_LEVEL=INFO
```

## 🎮 Ejecución

### Modo Normal
```bash
python main.py
```

### Modo Desarrollo (con más logs)
```bash
python main.py --mode dev
```

### Modo Invisible (Segundo Plano)
```bash
# Windows - ejecutar invisible
scripts/runners/run_hidden.vbs

# Windows - modo bajo consumo RAM
scripts/runners/run_low_ram_silent.vbs
```

### Dashboard Web (Opcional)
```bash
python main.py --dashboard --port 5000
```

## 💬 Formato de Mensajes

El bot reconoce estos formatos de mensajes:

```
gasto: 500 comida
500 super
gasté 150 nafta
compré 75 entretenimiento
pagué 1200 salud
150 comida
```

**Categorías válidas por defecto:**
`comida`, `transporte`, `entretenimiento`, `salud`, `servicios`, `ropa`, `educacion`, `hogar`, `trabajo`, `otros`, `super`, `nafta`

## 🔧 Comandos Útiles

```bash
# Mostrar configuración actual
python main.py --config

# Probar sistema de almacenamiento
python main.py --test-storage

# Validar configuración
python main.py --validate-config

# Ver versión
python main.py --version

# Ayuda completa
python main.py --help
```

## 🛠️ Scripts de Mantenimiento

```bash
# Verificar gastos con fechas futuras
python scripts/maintenance/check_future_gastos.py

# Limpiar gastos con fechas futuras
python scripts/maintenance/clean_future_gastos.py

# Resetear base de datos
python scripts/maintenance/reset_database.py

# Arreglar timestamps incorrectos
python scripts/maintenance/fix_timestamps.py
```

## 📊 Uso Paso a Paso

1. **Configurar WhatsApp**: Asegúrate de que WhatsApp Web esté funcionando
2. **Crear Chat**: Crea un chat llamado exactamente como `TARGET_CHAT_NAME` (ej: "Gastos")
3. **Ejecutar Bot**: `python main.py` o usar scripts de ejecución
4. **Escanear QR**: La primera vez, escanea el código QR de WhatsApp Web
5. **Enviar Mensajes**: Envía mensajes de gastos al chat configurado
6. **Ver Resultados**: Los gastos se guardan automáticamente en `data/gastos.xlsx`

### Ejemplo de Uso

```
🤖 Tú envías: "gasto: 150 comida"
⚡ Bot detecta: En <1 segundo
📝 Bot procesa: Monto=$150, Categoría=comida, Fecha=ahora
💾 Se guarda en Excel automáticamente
```

## 🏗️ Arquitectura del Proyecto

```
bot-gastos/
├── app/                    # Casos de uso y servicios
│   ├── services/          # Procesadores de mensajes, NLP, etc.
│   └── usecases/          # Casos de uso del negocio
├── config/                # Configuración
│   ├── config.yaml        # Configuración principal
│   └── settings.py        # Settings de Python
├── data/                  # Datos y bases de datos
│   ├── gastos.xlsx        # Excel de salida
│   └── gastos.db          # Cache SQLite
├── docs/                  # Documentación
├── domain/                # Entidades y reglas de negocio
│   ├── models/           # Modelos de dominio
│   └── value_objects/    # Objetos de valor
├── infrastructure/        # Implementaciones técnicas
│   ├── caching/          # Cache Redis (opcional)
│   ├── clustering/       # Clustering (experimental)
│   ├── storage/          # Excel, SQLite, híbrido
│   └── whatsapp/         # Conector WhatsApp Selenium
├── interface/             # Interfaces de usuario
│   ├── cli/              # Interfaz línea de comandos
│   └── web/              # Dashboard web (opcional)
├── logs/                  # Logs de ejecución
├── scripts/               # Scripts de utilidad
│   ├── install/          # Scripts de instalación
│   ├── maintenance/      # Scripts de mantenimiento
│   └── runners/          # Scripts de ejecución
├── shared/                # Utilidades compartidas
├── tests/                 # Tests actuales
├── tests_archived/        # Tests antiguos (referencia)
└── main.py               # Punto de entrada principal
```

## ⚡ Optimizaciones de Rendimiento

El bot está altamente optimizado para velocidad:

- **Polling ultra-rápido**: 1 segundo (antes 15s)
- **Detección instantánea**: 0.2s de verificación de login
- **Respuestas rápidas**: <0.3s de delay
- **Timeouts reducidos**: 10s conexión (antes 60s)
- **Cache híbrido**: SQLite + Excel para máxima velocidad
- **Extractor ultra-rápido**: Procesamiento optimizado de mensajes

Ver `docs/MODO_BAJO_CONSUMO_RAM.md` para modo de bajo consumo.

## 🧪 Testing

```bash
# Ejecutar tests
pytest

# Con cobertura
pytest --cov=app --cov=domain --cov=infrastructure

# Test específico
pytest tests/test_hash_optimization.py -v
```

## 🔍 Troubleshooting

### Problemas Comunes

**Error: "ChromeDriver not found"**
- El bot descarga ChromeDriver automáticamente
- Asegúrate de tener Chrome instalado

**Error: "WhatsApp Web no carga"**
- Verifica que WhatsApp Web funcione manualmente
- Revisa la configuración de `TARGET_CHAT_NAME` en `config/config.yaml`
- Ejecuta con `--mode dev` para ver más logs

**Error: "No se pueden procesar mensajes"**
- Verifica el formato de mensajes
- Activa logging con nivel DEBUG en `config/config.yaml`
- Revisa logs en `logs/bot_gastos.log`

**Bot no encuentra mensajes**
- El nombre del chat debe coincidir exactamente con `target_chat_name`
- Verifica que el chat tenga mensajes nuevos
- Asegúrate de que estás enviando mensajes con formato válido

**Problemas de memoria**
- Usa el modo bajo consumo: `scripts/runners/run_low_ram_silent.vbs`
- Ajusta configuraciones en `config/config.yaml`

### Logs y Debugging

```bash
# Ver logs en tiempo real (Linux/Mac)
tail -f logs/bot_gastos.log

# Ver logs en tiempo real (Windows PowerShell)
Get-Content logs\bot_gastos.log -Wait

# Ejecutar con debug completo
python main.py --mode dev
```

## 🚧 Estado del Proyecto

**✅ Implementado:**
- Detección ultra-rápida de mensajes (<1s)
- Procesamiento inteligente de gastos
- Almacenamiento híbrido optimizado
- Sistema de caché avanzado
- Modo invisible y bajo consumo
- Logging completo
- Sistema de hash para evitar duplicados

**🔮 Futuro:**
- OCR para tickets de compra (parcialmente implementado)
- Estadísticas y dashboard mejorado
- API REST para integración externa
- Soporte multi-chat
- Notificaciones automáticas

## 📝 Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/amazing-feature`)
3. Commit tus cambios (`git commit -m 'Add amazing feature'`)
4. Push a la rama (`git push origin feature/amazing-feature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto es de uso personal. Ver archivo `LICENSE` para detalles.

## 📞 Soporte

- 📖 **Documentación Técnica**: Ver `docs/architecture.md`
- 📚 **Guía de Uso**: Ver `GUIA_USO_PASO_A_PASO.md`
- 🔧 **Configuración**: Ver `docs/configuration_guide.md`
- 🐛 **Issues**: Crear issue en GitHub
- 💬 **Preguntas**: Contactar al desarrollador

## 🙏 Agradecimientos

Construido con:
- Selenium WebDriver
- Python 3.9+
- openpyxl para Excel
- SQLite para caché

---

**¿Necesitas ayuda?** Ejecuta `python main.py --help` para ver todas las opciones disponibles.

**Tip:** Para mejor rendimiento, usa `message_polling_interval_seconds: 1` en `config/config.yaml`