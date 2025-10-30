# Bot Gastos - Dashboard Frontend

Dashboard moderno y profesional construido con React para visualizar y analizar gastos personales.

## Stack Tecnológico

- **React 18** - Framework UI
- **Vite** - Build tool ultra-rápido
- **Tailwind CSS** - Utility-first CSS
- **Recharts** - Librería de gráficos
- **Lucide React** - Iconos modernos
- **date-fns** - Manipulación de fechas
- **clsx** - Utilidad para clases CSS

## Instalación

```bash
# Navegar al directorio frontend
cd interface/web/frontend

# Instalar dependencias
npm install
```

## Comandos Disponibles

```bash
# Modo desarrollo (http://localhost:3000)
npm run dev

# Build para producción
npm run build

# Preview del build
npm run preview

# Linting
npm run lint
```

## Estructura del Proyecto

```
src/
├── components/          # Componentes reutilizables
│   ├── ActivityTable.jsx
│   ├── Badge.jsx
│   ├── CategoryCard.jsx
│   ├── Chart.jsx
│   ├── Header.jsx
│   ├── Loading.jsx
│   ├── PeriodSelector.jsx
│   ├── ProgressBar.jsx
│   ├── SearchBar.jsx
│   ├── Sidebar.jsx
│   └── StatCard.jsx
│
├── pages/              # Páginas/vistas
│   └── Dashboard.jsx
│
├── hooks/              # Custom React hooks
│   ├── useApi.js
│   ├── useDashboardData.js
│   └── useFilters.js
│
├── services/           # Servicios externos
│   └── api.js
│
├── utils/              # Utilidades
│   ├── constants.js
│   └── formatters.js
│
├── App.jsx             # Componente raíz
├── main.jsx            # Entry point
└── index.css           # Estilos globales
```

## Configuración del Backend

El frontend espera que el backend Flask esté corriendo en `http://localhost:5000`.

La configuración de proxy en `vite.config.js` redirige automáticamente las llamadas `/api/*` al backend:

```javascript
proxy: {
  '/api': {
    target: 'http://localhost:5000',
    changeOrigin: true,
  },
}
```

## Desarrollo

### 1. Iniciar Backend (Terminal 1)
```bash
cd "C:\Users\vicen\OneDrive\Escritorio\apps\hechos\bot gastos"
python main.py --dashboard --port 5000
```

### 2. Iniciar Frontend (Terminal 2)
```bash
cd "interface/web/frontend"
npm run dev
```

### 3. Abrir en el navegador
```
http://localhost:3000
```

## Componentes Principales

### StatCard
Tarjeta para mostrar estadísticas con cambios porcentuales.

```jsx
<StatCard
  title="Balance Total"
  value={10000}
  change={5.2}
  description="vs mes anterior"
  icon={DollarSign}
  color="primary"
/>
```

### Chart
Componente de gráficos con soporte para line, bar y pie charts.

```jsx
<Chart
  data={[{ name: 'Ene', value: 1000 }, ...]}
  type="line"
  title="Gastos Mensuales"
  height={300}
/>
```

### ActivityTable
Tabla de actividades recientes con formateo automático.

```jsx
<ActivityTable
  activities={[
    { categoria: 'comida', monto: 500, fecha: '2025-01-15', descripcion: 'Almuerzo' }
  ]}
  loading={false}
/>
```

### ProgressBar
Barra de progreso para límites de gasto.

```jsx
<ProgressBar
  current={35000}
  total={50000}
  label="Límite Mensual"
/>
```

## Custom Hooks

### useDashboardData
Hook principal para cargar todos los datos del dashboard.

```jsx
const { summary, categories, timeline, activities, loading, error, refetch } = useDashboardData(30)
```

### useFilters
Hook para manejar filtros del dashboard.

```jsx
const { filters, updateFilter, resetFilters } = useFilters()
```

### useApi
Hook genérico para llamadas a la API.

```jsx
const { data, loading, error, refetch } = useApi(() => api.getSummary(), [])
```

## Formatters

Utilidades para formatear números, fechas y moneda:

```javascript
import { formatCurrency, formatDate, formatPercent } from '@/utils/formatters'

formatCurrency(1500)        // "$1,500.00"
formatDate('2025-01-15')    // "15/01/2025"
formatPercent(5.2)          // "+5.2%"
```

## Personalización

### Colores
Editar `tailwind.config.js` para cambiar la paleta de colores:

```javascript
colors: {
  primary: {
    500: '#10B981',  // Verde principal
    ...
  },
}
```

### Límite de Gasto
Editar `src/utils/constants.js`:

```javascript
export const LIMITE_GASTO_MENSUAL = 50000
```

### Categorías
Agregar nuevas categorías en `src/utils/constants.js`:

```javascript
export const CATEGORIAS = [
  'comida',
  'transporte',
  // ... agregar más
]
```

## Build para Producción

```bash
# Generar build optimizado
npm run build

# Los archivos estáticos se generan en:
# interface/web/dist/
```

Para servir el build:
```bash
npm run preview
```

O usar cualquier servidor estático:
```bash
npx serve -s dist
```

## Integración con Flask

Para servir el frontend desde Flask en producción, configurar en `dashboard_app.py`:

```python
@app.route('/')
def index():
    return send_from_directory('../dist', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('../dist', path)
```

## Performance

- **Lazy loading** de gráficos con Intersection Observer
- **Memoización** de componentes con React.memo
- **Debouncing** en búsquedas (300ms)
- **Code splitting** automático con Vite
- **Tree shaking** para optimizar bundle size

## Troubleshooting

### Error: Cannot find module 'vite'
```bash
rm -rf node_modules package-lock.json
npm install
```

### Puerto 3000 ocupado
Cambiar puerto en `vite.config.js`:
```javascript
server: {
  port: 3001,
}
```

### CORS errors
Verificar que el backend tenga CORS habilitado:
```python
from flask_cors import CORS
CORS(app)
```

## Próximas Mejoras

- [ ] Modo oscuro
- [ ] Exportación a PDF
- [ ] Filtros avanzados
- [ ] Gráficos comparativos
- [ ] Notificaciones push
- [ ] PWA support

## Licencia

Uso personal

---

**Versión**: 1.0.0
**Última actualización**: 2025-10-29
