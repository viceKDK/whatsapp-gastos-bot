# 📖 Guía de Usuario - Bot Gastos WhatsApp

Esta guía te ayudará a usar el Bot Gastos WhatsApp de manera efectiva para automatizar el registro de tus gastos.

## 🎯 ¿Qué hace el Bot?

El Bot Gastos WhatsApp automatiza el proceso de registro de gastos personales:

1. **Lee mensajes** de un chat específico de WhatsApp Web
2. **Interpreta gastos** del texto natural que escribes
3. **Guarda automáticamente** en Excel o base de datos
4. **Organiza por categorías** tus gastos

## 💬 Cómo Escribir Mensajes de Gastos

### Formatos Soportados

El bot entiende estos formatos de mensajes:

```
gasto: 500 comida
500 super
gasté 150 nafta
compré 75 entretenimiento
pagué 1200 salud
invertí 300 educacion
```

### Elementos del Mensaje

**Monto:**
- Puede incluir decimales: `150.50`
- Sin símbolos de moneda: `500` (no `$500`)
- Rango válido: $0.01 - $1,000,000

**Categoría:**
- Una sola palabra sin espacios
- En minúsculas preferentemente
- Debe ser una categoría válida (ver lista abajo)

### Categorías Válidas

**Categorías Principales:**
- `comida` - Restaurantes, almuerzo, cena, snacks
- `transporte` - Taxi, uber, combustible, transporte público
- `entretenimiento` - Cine, streaming, juegos, diversión
- `salud` - Médico, farmacia, medicina, gimnasio
- `servicios` - Luz, gas, agua, internet, celular
- `ropa` - Vestimenta, calzado, accesorios
- `educacion` - Libros, cursos, materiales educativos
- `hogar` - Muebles, electrodomésticos, decoración
- `trabajo` - Materiales, herramientas, gastos laborales
- `otros` - Gastos que no encajan en otras categorías

**Categorías Extendidas:**
- `super` / `supermercado` - Compras de alimentos y productos
- `nafta` / `combustible` - Gasolina, gas natural
- `farmacia` - Medicamentos específicos
- `cafe` - Café, bebidas
- `impuestos` - Pagos de impuestos
- `seguros` - Pólizas de seguro

### Ejemplos Prácticos

```
# ✅ Mensajes correctos
gasto: 450 comida          → $450.00 en comida
125 nafta                  → $125.00 en nafta  
gasté 75.50 cafe          → $75.50 en cafe
compré 2500 ropa          → $2,500.00 en ropa
pagué 890 servicios       → $890.00 en servicios

# ❌ Mensajes que NO funcionan
$500 comida               → No incluir símbolo $
500 comida rapida         → Categoría con espacios
quinientos comida         → Monto debe ser numérico
500                       → Falta categoría
```

## 🔧 Configuración Básica

### Chat de WhatsApp

1. **Crea un chat** en WhatsApp (puede ser contigo mismo)
2. **Nómbralo exactamente** como está en tu configuración
3. **Envía mensajes** solo en ese chat para gastos

### Variables Importantes

En tu archivo `config/.env`:

```bash
# Nombre exacto del chat (¡muy importante!)
TARGET_CHAT_NAME=Gastos Personal

# Cada cuánto revisar mensajes (en segundos)
WHATSAPP_POLL_INTERVAL=30

# Mostrar ventana de Chrome (true) o ejecutar oculto (false)
CHROME_HEADLESS=false
```

## 📊 Ver tus Gastos

### Archivo Excel

Los gastos se guardan automáticamente en `data/gastos.xlsx`:

| Fecha      | Hora     | Monto   | Categoría | Descripción |
|------------|----------|---------|-----------|-------------|
| 2025-08-06 | 14:30:15 | $150.00 | comida    |             |
| 2025-08-06 | 16:45:30 | $75.50  | nafta     |             |

### Ver Estadísticas

```bash
# Ver estadísticas del almacenamiento
python main.py --test-storage
```

## 🚀 Uso Diario

### Rutina Típica

1. **Iniciar el bot por la mañana:**
   ```bash
   python main.py
   ```

2. **Durante el día, enviar mensajes:**
   ```
   gasto: 250 comida       # Almuerzo
   45 cafe                 # Café de la tarde  
   500 super               # Compras del supermercado
   ```

3. **El bot procesa automáticamente** y guarda en Excel

4. **Al final del día** puedes ver el resumen en Excel

### Consejos de Uso

**✅ Buenas Prácticas:**
- Envía gastos inmediatamente después de realizarlos
- Usa categorías consistentes
- Revisa el archivo Excel semanalmente
- Mantén el chat solo para gastos

**⚠️ Evitar:**
- Mensajes muy largos con múltiples gastos
- Cambiar el nombre del chat frecuentemente
- Usar el chat para conversaciones normales
- Cerrar WhatsApp Web mientras el bot está activo

## 📱 Uso en Móvil

Puedes enviar mensajes desde tu móvil al chat configurado, el bot los procesará cuando se sincronicen con WhatsApp Web.

**Importante:** WhatsApp Web debe estar abierto y conectado para que el bot funcione.

## 🔍 Verificación de Gastos

### Comprobar si un Gasto se Registró

1. **Buscar en Excel:** Abre `data/gastos.xlsx` y busca tu gasto
2. **Ver logs:** Revisa `logs/bot.log` para mensajes de confirmación
3. **Usar comando:** `python main.py --test-storage` muestra estadísticas

### Mensajes de Confirmación

Cuando el bot está en modo visible, muestra confirmaciones:

```
💰 14:30:15 - $150.00 en comida
💰 16:45:30 - $75.50 en nafta
```

## 🚨 Qué Hacer si Algo No Funciona

### Problemas Comunes

**El bot no procesa mensajes:**
1. Verifica que WhatsApp Web esté abierto
2. Confirma el nombre exacto del chat
3. Revisa que Chrome esté actualizado

**Mensajes no se interpretan:**
1. Usa el formato correcto: `monto categoría`
2. Verifica que la categoría sea válida
3. Asegúrate de que el monto sea numérico

**Excel no se actualiza:**
1. Cierra Excel si está abierto durante el procesamiento
2. Verifica permisos de escritura en la carpeta `data/`
3. Revisa los logs para errores específicos

### Obtener Ayuda

```bash
# Ver configuración actual
python main.py --config

# Validar configuración
python main.py --validate-config

# Ver logs detallados
python main.py --mode dev
```

## 📈 Análisis de Gastos

### En Excel

1. **Tablas dinámicas:** Crea resúmenes por categoría y fecha
2. **Gráficos:** Visualiza tendencias de gastos
3. **Filtros:** Analiza períodos específicos
4. **Fórmulas:** Calcula totales y promedios

### Preguntas Útiles para Análisis

- ¿En qué categoría gasto más dinero?
- ¿Cuál es mi promedio de gastos diarios?
- ¿Cómo varían mis gastos por mes?
- ¿Qué días de la semana gasto más?

## 🎯 Consejos Avanzados

### Optimizar Categorías

Si frecuentemente usas categorías similares, puedes:

1. **Estandarizar nombres:** Usa siempre `comida` en lugar de `almuerzo`
2. **Crear aliases:** El bot puede mapear `restaurant` → `comida`
3. **Agregar nuevas categorías** modificando la configuración

### Backup Automático

El bot crea backups automáticos de tu archivo Excel:
- Ubicación: misma carpeta que el archivo principal
- Formato: `gastos_backup_YYYYMMDD_HHMMSS.xlsx`
- Frecuencia: configurable

### Integración con Otros Sistemas

Los datos en Excel se pueden exportar fácilmente a:
- Aplicaciones de finanzas personales
- Sistemas de contabilidad
- Herramientas de análisis (Power BI, Tableau)

## 📞 Soporte

Si tienes problemas:

1. **Revisa esta guía** para soluciones comunes
2. **Consulta los logs** en `logs/bot.log`
3. **Usa modo debug** con `python main.py --mode dev`
4. **Contacta al desarrollador** con información específica del error