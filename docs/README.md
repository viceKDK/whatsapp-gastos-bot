# 📚 Documentación - Bot Gastos WhatsApp

Documentación completa del Bot Personal para Registrar Gastos desde WhatsApp Web.

## 📖 Guías Disponibles

### 🚀 Para Usuarios

- **[📖 Guía de Usuario](user_guide.md)** - Cómo usar el bot día a día
  - Formatos de mensajes soportados
  - Categorías válidas
  - Configuración básica del chat
  - Análisis de gastos en Excel
  - Consejos y buenas prácticas

- **[🔧 Guía de Instalación](installation_guide.md)** - Instalación paso a paso
  - Requisitos del sistema
  - Instalación automática y manual
  - Configuración inicial
  - Verificación de funcionamiento
  - Solución de problemas de instalación

- **[⚙️ Guía de Configuración](configuration_guide.md)** - Personalizar el bot
  - Variables de entorno disponibles
  - Configuración por casos de uso
  - Configuración avanzada
  - Validación de configuración
  - Ejemplos de configuración

### 🛠️ Para Desarrolladores

- **[👨‍💻 Guía de Desarrollador](developer_guide.md)** - Desarrollo y contribución
  - Arquitectura del sistema
  - Setup del entorno de desarrollo
  - Testing y calidad de código
  - Patrones de diseño utilizados
  - Cómo contribuir al proyecto

- **[📖 API Reference](api_reference.md)** - Referencia técnica completa
  - Documentación de todas las clases y métodos
  - Domain Layer (Gasto, Monto, Categoría)
  - Application Layer (Servicios, Casos de uso)
  - Infrastructure Layer (Storage, WhatsApp)
  - Shared Components (Logger, Utils, Config)

### 🆘 Soporte y Problemas

- **[🔧 Troubleshooting](troubleshooting_guide.md)** - Solución de problemas
  - Diagnóstico rápido
  - Problemas comunes y soluciones
  - Herramientas de diagnóstico
  - Cuándo pedir ayuda
  - Scripts de diagnóstico automático

### 📋 Documentación Técnica

- **[🏗️ Arquitectura](architecture.md)** - Documentación arquitectural formal
  - Clean Architecture implementation
  - Tech Stack completo
  - Diagramas del sistema
  - Patrones arquitecturales
  - Especificaciones técnicas detalladas

---

## 🎯 Comenzar Aquí

### ¿Eres nuevo en el bot?
👉 **Comienza con [Guía de Instalación](installation_guide.md)**

### ¿Ya tienes el bot instalado?
👉 **Lee la [Guía de Usuario](user_guide.md)**

### ¿Tienes problemas?
👉 **Consulta [Troubleshooting](troubleshooting_guide.md)**

### ¿Quieres contribuir código?
👉 **Ve la [Guía de Desarrollador](developer_guide.md)**

### ¿Necesitas personalizar configuración?
👉 **Consulta [Guía de Configuración](configuration_guide.md)**

---

## 🔍 Búsqueda Rápida

### Problemas Comunes
- **Bot no procesa mensajes** → [Troubleshooting - WhatsApp](troubleshooting_guide.md#problemas-de-whatsapp)
- **Error de instalación** → [Instalación - Troubleshooting](installation_guide.md#solución-de-problemas-de-instalación)
- **Configurar categorías** → [Configuración - Categorías](configuration_guide.md#configuración-de-categorías)
- **Formato de mensajes** → [Usuario - Mensajes](user_guide.md#cómo-escribir-mensajes-de-gastos)

### Tareas Técnicas
- **Agregar nuevo storage** → [Developer - Extensibilidad](developer_guide.md#agregar-nuevo-storage)
- **API de una clase** → [API Reference](api_reference.md)
- **Validar configuración** → [Configuración - Validación](configuration_guide.md#validación-de-configuración)
- **Testing** → [Developer - Testing](developer_guide.md#testing)

---

## 📊 Estructura de la Documentación

```
docs/
├── README.md                    # 👈 Estás aquí - Índice principal
├── user_guide.md              # 📖 Guía para usuarios finales
├── installation_guide.md       # 🚀 Instalación paso a paso
├── configuration_guide.md      # ⚙️ Configuración completa
├── developer_guide.md          # 👨‍💻 Desarrollo y contribución
├── api_reference.md            # 📖 Referencia técnica API
├── troubleshooting_guide.md    # 🔧 Solución de problemas
└── architecture.md             # 🏗️ Documentación arquitectural
```

---

## 🎓 Niveles de Usuario

### 👤 Usuario Final
**Documentación recomendada:**
1. [Instalación](installation_guide.md) - Setup inicial
2. [Usuario](user_guide.md) - Uso diario
3. [Configuración](configuration_guide.md) - Personalización básica
4. [Troubleshooting](troubleshooting_guide.md) - Problemas comunes

### 🔧 Administrador/Power User
**Documentación recomendada:**
1. [Configuración](configuration_guide.md) - Configuración avanzada
2. [Troubleshooting](troubleshooting_guide.md) - Diagnóstico completo
3. [Arquitectura](architecture.md) - Entender el sistema
4. [API Reference](api_reference.md) - Referencia técnica

### 👨‍💻 Desarrollador
**Documentación recomendada:**
1. [Developer](developer_guide.md) - Setup y desarrollo
2. [API Reference](api_reference.md) - Referencia completa
3. [Arquitectura](architecture.md) - Diseño del sistema
4. [Troubleshooting](troubleshooting_guide.md) - Debugging avanzado

---

## 🔄 Actualizaciones de Documentación

### Versión 1.0.0 (2025-08-06)
- ✅ Documentación inicial completa
- ✅ 7 guías principales creadas
- ✅ API Reference completa
- ✅ Troubleshooting comprehensivo
- ✅ Ejemplos y casos de uso

### Contribuir a la Documentación

¿Encontraste algo que falta o está incorrecto?

1. **Issues menores:** Edita directamente el archivo markdown
2. **Mejoras importantes:** Sigue el proceso de contribución en [Developer Guide](developer_guide.md#contribuir)
3. **Nuevas guías:** Propón en GitHub Issues

---

## 📞 Soporte

### Recursos de Ayuda

1. **📖 Documentación** - Busca aquí primero
2. **🔧 Troubleshooting** - Problemas comunes resueltos
3. **💬 GitHub Issues** - Reportar bugs y solicitar features
4. **📧 Contacto** - Para soporte directo

### Información para Soporte

Al reportar problemas, incluye siempre:

```bash
# Información básica del sistema
python main.py --version
python main.py --validate-config

# Configuración actual (sin datos sensibles)
python main.py --config

# Logs relevantes
tail -50 logs/bot.log
```

---

## 🎯 Próximos Pasos

### Después de leer la documentación:

1. **✅ Instalar el bot** usando [Guía de Instalación](installation_guide.md)
2. **✅ Configurar** siguiendo [Guía de Configuración](configuration_guide.md)
3. **✅ Usar diariamente** con [Guía de Usuario](user_guide.md)
4. **✅ Contribuir** con [Guía de Desarrollador](developer_guide.md) (opcional)

### Mantente actualizado:

- ⭐ **Star** el repositorio en GitHub
- 📬 **Watch** para notificaciones de actualizaciones
- 🔄 **Pull** regularmente para obtener mejoras

---

**¡Bienvenido al Bot Gastos WhatsApp! Esta documentación te ayudará a aprovechar al máximo esta herramienta.** 🚀

> **Tip:** Usa `Ctrl+F` o `Cmd+F` para buscar términos específicos en cualquier documento.