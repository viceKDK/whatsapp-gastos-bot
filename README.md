# 🤖 Bot Gastos WhatsApp

Bot personal que automatiza el registro de gastos desde mensajes de WhatsApp Web, utilizando Python 3 con arquitectura en capas limpia.

## 📋 Características

- ✅ **Automatización WhatsApp Web**: Lee mensajes automáticamente usando Selenium
- ✅ **Procesamiento Inteligente**: Extrae monto y categoría de texto natural
- ✅ **Almacenamiento Dual**: Soporte para Excel y SQLite
- ✅ **Arquitectura Limpia**: Separación clara de responsabilidades
- ✅ **Configuración Flexible**: Variables de entorno y archivos de configuración
- ✅ **Logging Completo**: Sistema de logs robusto con rotación
- ✅ **Modo Headless**: Ejecución invisible o visible según configuración

## 🚀 Instalación Rápida

### Pre-requisitos

- Python 3.9 o superior
- Google Chrome instalado
- WhatsApp Web configurado en tu navegador

### 1. Clonar y Configurar

```bash
# Clonar repositorio (o descargar archivos)
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

### 2. Configuración

```bash
# Copiar archivo de configuración
cp config/.env.example config/.env

# Editar configuración (usar tu editor favorito)
notepad config/.env  # Windows
nano config/.env     # Linux/Mac
```

### 3. Ejecutar

```bash
# Probar configuración
python main.py --validate-config

# Ejecutar bot
python main.py

# Ejecutar en modo desarrollo (más logs)
python main.py --mode dev
```

## 💬 Formato de Mensajes

El bot reconoce estos formatos de mensajes:

```
gasto: 500 comida
500 super
gasté 150 nafta
compré 75 entretenimiento
pagué 1200 salud
```

**Categorías válidas por defecto:**
`comida`, `transporte`, `entretenimiento`, `salud`, `servicios`, `ropa`, `educacion`, `hogar`, `trabajo`, `otros`, `super`, `nafta`

## ⚙️ Configuración

### Variables de Entorno Importantes

```bash
# Almacenamiento
STORAGE_MODE=excel              # 'excel' o 'sqlite'
EXCEL_FILE_PATH=data/gastos.xlsx

# WhatsApp
TARGET_CHAT_NAME=Gastos Personal  # Nombre exacto del chat
WHATSAPP_POLL_INTERVAL=30        # Intervalo en segundos
CHROME_HEADLESS=false            # true=invisible, false=visible

# Logging
LOG_LEVEL=INFO                   # DEBUG, INFO, WARNING, ERROR
LOG_CONSOLE=true                 # Mostrar logs en consola
```

### Estructura de Archivos

```
data/gastos.xlsx    # Archivo Excel con gastos (se crea automáticamente)
logs/bot.log        # Archivo de logs
config/.env         # Tu configuración (crear desde .env.example)
```

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

## 📊 Uso

1. **Configurar WhatsApp**: Asegúrate de que WhatsApp Web esté funcionando
2. **Crear Chat**: Crea un chat llamado exactamente como `TARGET_CHAT_NAME`
3. **Ejecutar Bot**: `python main.py`
4. **Enviar Mensajes**: Envía mensajes de gastos al chat configurado
5. **Ver Resultados**: Los gastos se guardan automáticamente en `data/gastos.xlsx`

### Ejemplo de Uso

```
🤖 Tú envías: "gasto: 150 comida"
📝 Bot procesa: Monto=$150, Categoría=comida, Fecha=ahora
💾 Se guarda en Excel automáticamente
```

## 🏗️ Arquitectura

El proyecto usa arquitectura en capas:

```
├── domain/          # Entidades y reglas de negocio
├── app/            # Casos de uso y servicios
├── infrastructure/ # Implementaciones (WhatsApp, Excel, etc.)
├── interface/      # Interfaces (CLI, GUI futuro)
├── shared/         # Utilidades compartidas
└── config/         # Configuración
```

## 🧪 Testing

```bash
# Ejecutar tests
pytest

# Con cobertura
pytest --cov=app --cov=domain --cov=infrastructure

# Test específico
pytest tests/domain/test_gasto.py -v
```

## 🔍 Troubleshooting

### Problemas Comunes

**Error: "ChromeDriver not found"**
- El bot descarga ChromeDriver automáticamente
- Asegúrate de tener Chrome instalado

**Error: "WhatsApp Web no carga"**
- Verifica que WhatsApp Web funcione manualmente
- Revisa la configuración de `TARGET_CHAT_NAME`

**Error: "No se pueden procesar mensajes"**
- Verifica el formato de mensajes
- Activa `DEBUG_MODE=true` para más información

**Bot no encuentra mensajes**
- El nombre del chat debe coincidir exactamente
- Verifica que el chat tenga mensajes nuevos

### Logs y Debugging

```bash
# Activar modo debug
export DEBUG_MODE=true
python main.py --mode dev

# Ver logs en tiempo real
tail -f logs/bot.log
```

## 🚧 Estado del Proyecto en el futuro

**🔮 Futuro:**
- OCR para tickets de compra
- Estadísticas automáticas
- API REST


## 📝 Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/amazing-feature`)
3. Commit tus cambios (`git commit -m 'Add amazing feature'`)
4. Push a la rama (`git push origin feature/amazing-feature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto es de uso personal. Ver archivo `LICENSE` para detalles.

## 📞 Soporte

- 📖 **Documentación**: Ver `docs/architecture.md` para detalles técnicos
- 🐛 **Issues**: Crear issue en GitHub
- 💬 **Preguntas**: Contactar al desarrollador

---

**¿Necesitas ayuda?** Ejecuta `python main.py --help` para ver todas las opciones disponibles.
