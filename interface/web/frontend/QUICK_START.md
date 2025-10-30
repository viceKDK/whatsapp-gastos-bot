# Quick Start - Dashboard Frontend

Guía rápida para poner en marcha el dashboard en 3 pasos.

## 1️⃣ Instalar Dependencias

```bash
cd interface/web/frontend
npm install
```

Esto instalará:
- React 18
- Vite
- Tailwind CSS
- Recharts
- Lucide React
- date-fns
- clsx

## 2️⃣ Iniciar Backend

En una terminal separada, iniciar el servidor Flask:

```bash
# Desde la raíz del proyecto
python main.py --dashboard --port 5000
```

El backend debe estar corriendo en `http://localhost:5000`

## 3️⃣ Iniciar Frontend

```bash
# Desde interface/web/frontend
npm run dev
```

El dashboard estará disponible en `http://localhost:3000`

---

## Verificación Rápida

### Backend funcionando ✅
Abrir en el navegador:
```
http://localhost:5000/api/summary
```

Debería retornar JSON con estadísticas.

### Frontend funcionando ✅
Abrir en el navegador:
```
http://localhost:3000
```

Debería mostrar el dashboard con:
- 4 tarjetas de estadísticas
- Barra de límite de gasto
- 2 gráficos (línea y barras)
- Grid de categorías
- Tabla de actividades recientes

---

## Comandos Útiles

```bash
# Desarrollo
npm run dev

# Build para producción
npm run build

# Preview del build
npm run preview

# Linting
npm run lint
```

---

## Problemas Comunes

### ❌ Error: ECONNREFUSED al llamar a la API
**Solución**: Asegurarse de que el backend esté corriendo en el puerto 5000

### ❌ Error: Module not found
**Solución**:
```bash
rm -rf node_modules package-lock.json
npm install
```

### ❌ Puerto 3000 ocupado
**Solución**: Cambiar puerto en `vite.config.js`:
```javascript
server: {
  port: 3001,
}
```

---

## Estructura Visual del Dashboard

```
┌─────────────────────────────────────────────────┐
│  🏠 Dashboard                    [7d 30d 90d 1y]│
├─────────────────────────────────────────────────┤
│                                                  │
│  ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐      │
│  │ Total │ │ Mes   │ │ Prom  │ │ Count │      │
│  │ $XXX  │ │ $XXX  │ │ $XXX  │ │  XXX  │      │
│  └───────┘ └───────┘ └───────┘ └───────┘      │
│                                                  │
│  ────────────────────────────────               │
│  Límite Mensual: $XXX / $50,000  [████    ] 80%│
│  ────────────────────────────────               │
│                                                  │
│  ┌────────────────┐  ┌────────────────┐        │
│  │  Gastos en el  │  │  Gastos por    │        │
│  │     Tiempo     │  │   Categoría    │        │
│  │                │  │                │        │
│  │  [Line Chart]  │  │  [Bar Chart]   │        │
│  │                │  │                │        │
│  └────────────────┘  └────────────────┘        │
│                                                  │
│  Categorías                                     │
│  ┌────┐ ┌────┐ ┌────┐                          │
│  │🍽️ │ │🚗 │ │🎬 │                          │
│  │$XX │ │$XX │ │$XX │                          │
│  └────┘ └────┘ └────┘                          │
│                                                  │
│  Actividades Recientes                          │
│  ┌──────────────────────────────────────┐      │
│  │ Cat   │ Desc      │ Monto  │ Fecha   │      │
│  ├──────────────────────────────────────┤      │
│  │ 🍽️   │ Almuerzo  │ $500   │ 15/01  │      │
│  │ 🚗   │ Uber      │ $300   │ 15/01  │      │
│  └──────────────────────────────────────┘      │
│                                                  │
└─────────────────────────────────────────────────┘
```

---

## Siguiente Paso

Una vez que el dashboard esté funcionando, revisar:
- `README.md` para documentación completa
- `docs/DASHBOARD_PLAN_UI.md` para detalles de implementación
- `src/components/` para ver código de componentes

---

¡Listo para usar! 🚀
