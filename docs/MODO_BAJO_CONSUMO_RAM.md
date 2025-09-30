# 🔋 Bot Gastos - Modo Bajo Consumo RAM

## ¿Qué es?

Una versión optimizada del bot que consume **60-70% menos RAM** que la versión normal:
- **Normal**: ~800MB RAM
- **Optimizado**: ~200-300MB RAM

## 🚀 Uso Rápido

### Opción 1: Totalmente invisible (recomendado)
```bash
# Doble clic en este archivo:
run_low_ram_silent.vbs
```
- ✅ No abre ventanas
- ✅ Corre 100% en segundo plano
- ✅ Consumo mínimo de RAM

### Opción 2: Con ventana (para ver logs)
```bash
# Doble clic en este archivo:
run_low_ram.bat
```
- ✅ Ventana con información
- ✅ Puedes ver el progreso
- ✅ Consumo mínimo de RAM

### Opción 3: Línea de comandos
```bash
python main_optimized.py --headless --minimal
```

## 🔧 Optimizaciones Aplicadas

### Chrome Optimizado
- ✅ Modo headless (sin interfaz gráfica)
- ✅ Imágenes deshabilitadas (solo texto)
- ✅ Plugins y extensiones deshabilitados
- ✅ GPU deshabilitada
- ✅ Cache agresivo
- ✅ Límite de memoria JS: 1GB
- ✅ Ventana pequeña (800x600) si no es headless

### Python Optimizado
- ✅ Recolección de basura agresiva
- ✅ Optimización de bytecode
- ✅ Storage SQLite (más liviano que Excel)
- ✅ Timeouts reducidos
- ✅ Menos logging

## 📊 Comparación de Consumo

| Modo | RAM Promedio | CPU | Disco |
|------|-------------|-----|-------|
| Normal | 800MB | 15-25% | Alto |
| Optimizado | 200-300MB | 5-10% | Bajo |

## ⚠️ Consideraciones

### Primera vez:
1. Ejecuta primero la versión normal para hacer login a WhatsApp
2. Una vez logueado, cambia al modo optimizado

### ¿Cuándo usar cada modo?

**Modo Normal (`main.py`):**
- ✅ Primera configuración
- ✅ Debugging/desarrollo
- ✅ Cuando necesitas ver WhatsApp Web

**Modo Optimizado (`main_optimized.py`):**
- ✅ Uso diario en producción
- ✅ Ejecutar 24/7
- ✅ Cuando la RAM es limitada
- ✅ Servidores/computadoras viejas

## 🛠️ Configuración Avanzada

El archivo `config/config.yaml` se configura automáticamente, pero puedes personalizar:

```yaml
whatsapp:
  chrome_headless: true  # Activado automáticamente
  connection_timeout_seconds: 30  # Reducido para eficiencia

performance:
  metrics_enabled: false  # Opcional: deshabilitar métricas
  alert_thresholds:
    memory_usage_mb: 300.0  # Límite de RAM más bajo
```

## 🐛 Troubleshooting

**Error: Chrome no inicia**
```bash
# Usar modo con ventana para debug
python main_optimized.py --minimal
```

**Error: No encuentra mensajes**
```bash
# Deshabilitar temporalmente --disable-images
# Editar whatsapp_selenium.py línea 1219
```

**RAM sigue alta**
```bash
# Verificar procesos de Chrome
tasklist | findstr chrome
# Matar procesos zombi
taskkill /F /IM chrome.exe /T
```

## ✅ Verificación de Funcionamiento

1. Ejecutar: `run_low_ram_silent.vbs`
2. Abrir Task Manager
3. Buscar proceso Python
4. RAM debería estar entre 200-300MB

## 🎯 Tips de Uso

- **Autostart**: Agregar `run_low_ram_silent.vbs` a inicio de Windows
- **Monitoring**: Revisar `logs/bot.log` periodicamente
- **Maintenance**: Reiniciar cada 7 días para limpiar memoria
- **Emergency stop**: `Ctrl+C` si usas el .bat, o matar proceso si usas .vbs