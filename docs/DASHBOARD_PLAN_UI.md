# Plan de Implementación: Dashboard UI (Frontend React)

## Objetivo
Crear la interfaz de usuario moderna del dashboard usando React + Vite + Tailwind CSS, basado en los diseños de Finery y CripioFin.

---

## Stack Tecnológico

- **Framework**: React 18 + Vite
- **Estilos**: Tailwind CSS
- **Gráficos**: Recharts
- **Iconos**: Lucide React
- **Fechas**: date-fns
- **Utilidades**: clsx

---

## Estructura de Archivos

```
interface/web/frontend/
├── package.json
├── vite.config.js
├── tailwind.config.js
├── postcss.config.js
├── index.html
├── .gitignore
│
├── src/
│   ├── main.jsx                 # Entry point
│   ├── App.jsx                  # App principal
│   ├── index.css                # Estilos globales + Tailwind
│   │
│   ├── components/              # Componentes reutilizables
│   │   ├── Sidebar.jsx          # Sidebar de navegación
│   │   ├── Header.jsx           # Header superior
│   │   ├── StatCard.jsx         # Card de estadística
│   │   ├── Chart.jsx            # Componente de gráfico
│   │   ├── ActivityTable.jsx    # Tabla de actividades
│   │   ├── CategoryCard.jsx     # Card de categoría
│   │   ├── ProgressBar.jsx      # Barra de progreso
│   │   ├── Badge.jsx            # Badge de estado
│   │   ├── SearchBar.jsx        # Barra de búsqueda
│   │   ├── FilterMenu.jsx       # Menú de filtros
│   │   ├── PeriodSelector.jsx   # Selector de periodo
│   │   └── Loading.jsx          # Spinner de carga
│   │
│   ├── pages/                   # Páginas/vistas
│   │   ├── Dashboard.jsx        # Dashboard principal
│   │   └── Analytics.jsx        # Página de analytics (futuro)
│   │
│   ├── services/                # Servicios para API
│   │   └── api.js               # Cliente API REST
│   │
│   ├── hooks/                   # Custom hooks
│   │   ├── useApi.js            # Hook para llamadas API
│   │   ├── useDashboardData.js  # Hook para datos del dashboard
│   │   └── useFilters.js        # Hook para filtros
│   │
│   └── utils/                   # Utilidades
│       ├── formatters.js        # Formato de números, fechas
│       └── constants.js         # Constantes de la app
```

---

## Fase 1: Setup Inicial (YA COMPLETADO)

### ✅ Archivos de Configuración Creados:
- [x] `package.json` - Dependencias del proyecto
- [x] `vite.config.js` - Configuración de Vite
- [x] `tailwind.config.js` - Configuración de Tailwind
- [x] `postcss.config.js` - Configuración de PostCSS
- [x] `index.html` - HTML base
- [x] `.gitignore` - Archivos a ignorar

### ✅ Archivos Base Creados:
- [x] `src/main.jsx` - Entry point de React
- [x] `src/App.jsx` - Componente principal
- [x] `src/index.css` - Estilos globales con Tailwind
- [x] `src/services/api.js` - Cliente API
- [x] `src/utils/formatters.js` - Utilidades de formato

### 📦 Instalación de Dependencias:
```bash
cd interface/web/frontend
npm install
```

### 🚀 Comandos Disponibles:
```bash
npm run dev      # Modo desarrollo (http://localhost:3000)
npm run build    # Build para producción
npm run preview  # Preview del build
```

---

## Fase 2: Componentes Base

### 2.1 Loading Component
**Archivo**: `src/components/Loading.jsx`

```jsx
import React from 'react'

export default function Loading({ size = 'md', text = 'Cargando...' }) {
  const sizes = {
    sm: 'w-6 h-6 border-2',
    md: 'w-10 h-10 border-3',
    lg: 'w-16 h-16 border-4',
  }

  return (
    <div className="flex flex-col items-center justify-center p-8">
      <div className={`spinner ${sizes[size]}`}></div>
      {text && <p className="mt-4 text-gray-600">{text}</p>}
    </div>
  )
}
```

### 2.2 Badge Component
**Archivo**: `src/components/Badge.jsx`

```jsx
import React from 'react'
import clsx from 'clsx'

export default function Badge({ children, variant = 'default', size = 'md' }) {
  const variants = {
    default: 'bg-gray-100 text-gray-700',
    success: 'bg-green-100 text-green-700',
    danger: 'bg-red-100 text-red-700',
    warning: 'bg-yellow-100 text-yellow-700',
    info: 'bg-blue-100 text-blue-700',
  }

  const sizes = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-3 py-1 text-sm',
    lg: 'px-4 py-1.5 text-base',
  }

  return (
    <span className={clsx(
      'badge inline-flex items-center gap-1 rounded-full font-semibold',
      variants[variant],
      sizes[size]
    )}>
      {children}
    </span>
  )
}
```

### 2.3 StatCard Component
**Archivo**: `src/components/StatCard.jsx`

```jsx
import React from 'react'
import { TrendingUp, TrendingDown } from 'lucide-react'
import { formatCurrency, formatPercent, getChangeColor } from '@/utils/formatters'

export default function StatCard({
  title,
  value,
  change,
  icon: Icon,
  description,
  color = 'primary'
}) {
  const isPositive = change >= 0
  const TrendIcon = isPositive ? TrendingUp : TrendingDown

  const colorClasses = {
    primary: 'bg-primary-50 text-primary-600',
    danger: 'bg-red-50 text-red-600',
    warning: 'bg-yellow-50 text-yellow-600',
    info: 'bg-blue-50 text-blue-600',
  }

  return (
    <div className="card">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-gray-600 mb-1">{title}</p>
          <h3 className="text-2xl font-bold text-gray-900 mb-2">
            {typeof value === 'number' ? formatCurrency(value) : value}
          </h3>

          {change !== undefined && (
            <div className="flex items-center gap-2">
              <span className={`flex items-center gap-1 text-sm font-medium ${getChangeColor(change)}`}>
                <TrendIcon className="w-4 h-4" />
                {formatPercent(change)}
              </span>
              {description && (
                <span className="text-xs text-gray-500">{description}</span>
              )}
            </div>
          )}
        </div>

        {Icon && (
          <div className={`p-3 rounded-xl ${colorClasses[color]}`}>
            <Icon className="w-6 h-6" />
          </div>
        )}
      </div>
    </div>
  )
}
```

### 2.4 ProgressBar Component
**Archivo**: `src/components/ProgressBar.jsx`

```jsx
import React from 'react'
import { formatCurrency } from '@/utils/formatters'

export default function ProgressBar({
  current,
  total,
  label = 'Progreso',
  showValues = true
}) {
  const percentage = Math.min((current / total) * 100, 100)
  const isWarning = percentage >= 80
  const isDanger = percentage >= 100

  const barColor = isDanger
    ? 'bg-red-500'
    : isWarning
    ? 'bg-yellow-500'
    : 'bg-primary-500'

  return (
    <div className="card">
      <div className="flex justify-between items-center mb-2">
        <span className="text-sm font-medium text-gray-700">{label}</span>
        {showValues && (
          <span className="text-sm font-semibold text-gray-900">
            {formatCurrency(current)} / {formatCurrency(total)}
          </span>
        )}
      </div>

      <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
        <div
          className={`h-full ${barColor} transition-all duration-500 ease-out rounded-full`}
          style={{ width: `${percentage}%` }}
        />
      </div>

      <div className="flex justify-between items-center mt-2">
        <span className="text-xs text-gray-500">
          {percentage.toFixed(1)}% usado
        </span>
        {isDanger && (
          <span className="text-xs font-medium text-red-600">
            ¡Límite superado!
          </span>
        )}
        {isWarning && !isDanger && (
          <span className="text-xs font-medium text-yellow-600">
            Cerca del límite
          </span>
        )}
      </div>
    </div>
  )
}
```

### 2.5 CategoryCard Component
**Archivo**: `src/components/CategoryCard.jsx`

```jsx
import React from 'react'
import { formatCurrency, getCategoryColor, getCategoryIcon } from '@/utils/formatters'

export default function CategoryCard({
  category,
  amount,
  percentage,
  count
}) {
  return (
    <div className="card flex items-center gap-4">
      <div className={`p-3 rounded-xl ${getCategoryColor(category)} bg-opacity-10`}>
        <span className="text-2xl">{getCategoryIcon(category)}</span>
      </div>

      <div className="flex-1">
        <h4 className="text-sm font-semibold text-gray-900 capitalize">
          {category}
        </h4>
        <p className="text-xs text-gray-500">
          {count} {count === 1 ? 'gasto' : 'gastos'}
        </p>
      </div>

      <div className="text-right">
        <p className="text-lg font-bold text-gray-900">
          {formatCurrency(amount)}
        </p>
        {percentage !== undefined && (
          <p className="text-xs text-gray-500">
            {percentage.toFixed(1)}%
          </p>
        )}
      </div>
    </div>
  )
}
```

---

## Fase 3: Layout Components

### 3.1 Sidebar Component
**Archivo**: `src/components/Sidebar.jsx`

```jsx
import React from 'react'
import {
  LayoutDashboard,
  BarChart3,
  Receipt,
  FileText,
  Settings,
  HelpCircle,
  LogOut,
  X
} from 'lucide-react'
import clsx from 'clsx'

const menuItems = [
  { icon: LayoutDashboard, label: 'Dashboard', active: true },
  { icon: BarChart3, label: 'Analytics', badge: '28' },
  { icon: Receipt, label: 'Transacciones' },
  { icon: FileText, label: 'Reportes' },
]

const bottomItems = [
  { icon: Settings, label: 'Configuración' },
  { icon: HelpCircle, label: 'Ayuda' },
  { icon: LogOut, label: 'Salir' },
]

export default function Sidebar({ isOpen, onToggle }) {
  return (
    <>
      {/* Overlay para mobile */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={onToggle}
        />
      )}

      {/* Sidebar */}
      <aside className={clsx(
        'fixed lg:static inset-y-0 left-0 z-50',
        'w-64 bg-white border-r border-gray-200',
        'flex flex-col',
        'transition-transform duration-300 ease-in-out',
        isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
      )}>
        {/* Logo */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-primary-500 rounded-xl flex items-center justify-center">
              <span className="text-white font-bold text-xl">B</span>
            </div>
            <div>
              <h1 className="font-bold text-gray-900">Bot Gastos</h1>
              <p className="text-xs text-gray-500">Dashboard</p>
            </div>
          </div>

          {/* Botón cerrar mobile */}
          <button
            onClick={onToggle}
            className="lg:hidden p-2 hover:bg-gray-100 rounded-lg"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Menu Items */}
        <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
          <div className="mb-6">
            <p className="px-3 mb-2 text-xs font-semibold text-gray-500 uppercase">
              Menu Principal
            </p>
            {menuItems.map((item, index) => (
              <MenuItem key={index} {...item} />
            ))}
          </div>

          <div>
            <p className="px-3 mb-2 text-xs font-semibold text-gray-500 uppercase">
              General
            </p>
            {bottomItems.map((item, index) => (
              <MenuItem key={index} {...item} />
            ))}
          </div>
        </nav>

        {/* User Profile */}
        <div className="p-4 border-t border-gray-200">
          <div className="flex items-center gap-3 p-3 rounded-lg hover:bg-gray-50 cursor-pointer">
            <div className="w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center">
              <span className="text-primary-600 font-semibold">U</span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 truncate">Usuario</p>
              <p className="text-xs text-gray-500 truncate">usuario@email.com</p>
            </div>
          </div>
        </div>
      </aside>
    </>
  )
}

function MenuItem({ icon: Icon, label, active, badge }) {
  return (
    <a
      href="#"
      className={clsx(
        'flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors',
        active
          ? 'bg-primary-50 text-primary-600 font-medium'
          : 'text-gray-700 hover:bg-gray-50'
      )}
    >
      <Icon className="w-5 h-5" />
      <span className="flex-1">{label}</span>
      {badge && (
        <span className="px-2 py-0.5 text-xs font-semibold bg-primary-100 text-primary-600 rounded-full">
          {badge}
        </span>
      )}
    </a>
  )
}
```

### 3.2 Header Component
**Archivo**: `src/components/Header.jsx`

```jsx
import React from 'react'
import { Search, Bell, Menu, RefreshCw } from 'lucide-react'
import SearchBar from './SearchBar'

export default function Header({ onMenuClick, onRefresh }) {
  return (
    <header className="bg-white border-b border-gray-200 sticky top-0 z-30">
      <div className="flex items-center justify-between px-6 py-4">
        {/* Left: Menu button + Search */}
        <div className="flex items-center gap-4 flex-1">
          <button
            onClick={onMenuClick}
            className="lg:hidden p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <Menu className="w-5 h-5" />
          </button>

          <SearchBar />
        </div>

        {/* Right: Actions */}
        <div className="flex items-center gap-3">
          {/* Refresh button */}
          <button
            onClick={onRefresh}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            title="Refrescar datos"
          >
            <RefreshCw className="w-5 h-5 text-gray-600" />
          </button>

          {/* Notifications */}
          <button className="relative p-2 hover:bg-gray-100 rounded-lg transition-colors">
            <Bell className="w-5 h-5 text-gray-600" />
            <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
          </button>

          {/* User avatar */}
          <button className="w-9 h-9 bg-primary-100 rounded-full flex items-center justify-center hover:bg-primary-200 transition-colors">
            <span className="text-primary-600 font-semibold text-sm">U</span>
          </button>
        </div>
      </div>
    </header>
  )
}
```

### 3.3 SearchBar Component
**Archivo**: `src/components/SearchBar.jsx`

```jsx
import React, { useState } from 'react'
import { Search } from 'lucide-react'

export default function SearchBar({ onSearch }) {
  const [query, setQuery] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    if (onSearch) {
      onSearch(query)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="relative w-full max-w-md">
      <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Buscar transacciones..."
        className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
      />
    </form>
  )
}
```

---

## Fase 4: Componentes de Datos

### 4.1 ActivityTable Component
**Archivo**: `src/components/ActivityTable.jsx`

```jsx
import React from 'react'
import { formatCurrency, formatDate, getCategoryIcon, capitalize } from '@/utils/formatters'
import Badge from './Badge'

export default function ActivityTable({ activities = [], loading = false }) {
  if (loading) {
    return (
      <div className="card">
        <div className="animate-pulse space-y-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="flex gap-4">
              <div className="w-10 h-10 bg-gray-200 rounded-lg"></div>
              <div className="flex-1 space-y-2">
                <div className="h-4 bg-gray-200 rounded w-1/4"></div>
                <div className="h-3 bg-gray-200 rounded w-1/2"></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Actividades Recientes</h3>
        <button className="text-sm text-primary-600 hover:text-primary-700 font-medium">
          Ver todas
        </button>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-200">
              <th className="text-left py-3 px-4 text-xs font-semibold text-gray-600 uppercase">
                Categoría
              </th>
              <th className="text-left py-3 px-4 text-xs font-semibold text-gray-600 uppercase">
                Descripción
              </th>
              <th className="text-right py-3 px-4 text-xs font-semibold text-gray-600 uppercase">
                Monto
              </th>
              <th className="text-right py-3 px-4 text-xs font-semibold text-gray-600 uppercase">
                Fecha
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {activities.map((activity, index) => (
              <tr key={index} className="hover:bg-gray-50 transition-colors">
                <td className="py-3 px-4">
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">{getCategoryIcon(activity.categoria)}</span>
                    <span className="font-medium text-gray-900 capitalize">
                      {activity.categoria}
                    </span>
                  </div>
                </td>
                <td className="py-3 px-4">
                  <span className="text-sm text-gray-600">
                    {activity.descripcion || '-'}
                  </span>
                </td>
                <td className="py-3 px-4 text-right">
                  <span className="font-semibold text-gray-900">
                    {formatCurrency(activity.monto)}
                  </span>
                </td>
                <td className="py-3 px-4 text-right">
                  <span className="text-sm text-gray-500">
                    {formatDate(activity.fecha)}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {activities.length === 0 && !loading && (
        <div className="text-center py-8">
          <p className="text-gray-500">No hay actividades recientes</p>
        </div>
      )}
    </div>
  )
}
```

### 4.2 Chart Component (con Recharts)
**Archivo**: `src/components/Chart.jsx`

```jsx
import React from 'react'
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import { formatCurrency } from '@/utils/formatters'

const COLORS = ['#10B981', '#3B82F6', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899']

export default function Chart({
  data = [],
  type = 'line',
  title,
  height = 300
}) {
  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 rounded-lg shadow-lg border border-gray-200">
          <p className="font-semibold text-gray-900">{payload[0].payload.name}</p>
          <p className="text-primary-600 font-medium">
            {formatCurrency(payload[0].value)}
          </p>
        </div>
      )
    }
    return null
  }

  if (type === 'line') {
    return (
      <div className="card">
        {title && <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>}
        <ResponsiveContainer width="100%" height={height}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
            <XAxis dataKey="name" stroke="#6B7280" style={{ fontSize: '12px' }} />
            <YAxis stroke="#6B7280" style={{ fontSize: '12px' }} />
            <Tooltip content={<CustomTooltip />} />
            <Line
              type="monotone"
              dataKey="value"
              stroke="#10B981"
              strokeWidth={3}
              dot={{ fill: '#10B981', r: 4 }}
              activeDot={{ r: 6 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    )
  }

  if (type === 'bar') {
    return (
      <div className="card">
        {title && <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>}
        <ResponsiveContainer width="100%" height={height}>
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
            <XAxis dataKey="name" stroke="#6B7280" style={{ fontSize: '12px' }} />
            <YAxis stroke="#6B7280" style={{ fontSize: '12px' }} />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey="value" radius={[8, 8, 0, 0]}>
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    )
  }

  if (type === 'pie') {
    return (
      <div className="card">
        {title && <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>}
        <ResponsiveContainer width="100%" height={height}>
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={(entry) => entry.name}
              outerRadius={80}
              fill="#8884d8"
              dataKey="value"
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
          </PieChart>
        </ResponsiveContainer>
      </div>
    )
  }

  return null
}
```

---

## Fase 5: Custom Hooks

### 5.1 useApi Hook
**Archivo**: `src/hooks/useApi.js`

```js
import { useState, useEffect } from 'react'

export function useApi(apiCall, dependencies = []) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchData = async () => {
    try {
      setLoading(true)
      setError(null)
      const result = await apiCall()
      setData(result.data || result)
    } catch (err) {
      setError(err.message)
      console.error('API Error:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, dependencies)

  const refetch = () => {
    fetchData()
  }

  return { data, loading, error, refetch }
}
```

### 5.2 useDashboardData Hook
**Archivo**: `src/hooks/useDashboardData.js`

```js
import { useState, useEffect } from 'react'
import api from '@/services/api'

export function useDashboardData(period = 30) {
  const [data, setData] = useState({
    summary: null,
    categories: null,
    timeline: null,
    activities: null,
  })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchAllData = async () => {
    try {
      setLoading(true)
      setError(null)

      const [summary, categories, timeline, activities] = await Promise.all([
        api.getSummary(),
        api.getCategories(period),
        api.getTimeline(period),
        api.getRecentActivities(10),
      ])

      setData({
        summary: summary.data,
        categories: categories.data,
        timeline: timeline.data,
        activities: activities.data,
      })
    } catch (err) {
      setError(err.message)
      console.error('Dashboard data error:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchAllData()
  }, [period])

  return { ...data, loading, error, refetch: fetchAllData }
}
```

### 5.3 useFilters Hook
**Archivo**: `src/hooks/useFilters.js`

```js
import { useState } from 'react'

export function useFilters(initialFilters = {}) {
  const [filters, setFilters] = useState({
    period: 30,
    category: 'all',
    dateFrom: null,
    dateTo: null,
    ...initialFilters,
  })

  const updateFilter = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }))
  }

  const updateFilters = (newFilters) => {
    setFilters(prev => ({ ...prev, ...newFilters }))
  }

  const resetFilters = () => {
    setFilters(initialFilters)
  }

  return {
    filters,
    updateFilter,
    updateFilters,
    resetFilters,
  }
}
```

---

## Fase 6: Dashboard Page

### Dashboard Principal
**Archivo**: `src/pages/Dashboard.jsx`

```jsx
import React from 'react'
import { DollarSign, TrendingUp, TrendingDown, CreditCard } from 'lucide-react'
import { useDashboardData } from '@/hooks/useDashboardData'
import { useFilters } from '@/hooks/useFilters'
import StatCard from '@/components/StatCard'
import Chart from '@/components/Chart'
import ActivityTable from '@/components/ActivityTable'
import CategoryCard from '@/components/CategoryCard'
import ProgressBar from '@/components/ProgressBar'
import PeriodSelector from '@/components/PeriodSelector'
import Loading from '@/components/Loading'

export default function Dashboard() {
  const { filters, updateFilter } = useFilters()
  const { summary, categories, timeline, activities, loading, error, refetch } = useDashboardData(filters.period)

  if (loading) {
    return <Loading text="Cargando dashboard..." />
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600 mb-4">Error cargando datos: {error}</p>
        <button onClick={refetch} className="btn btn-primary">
          Reintentar
        </button>
      </div>
    )
  }

  // Preparar datos para gráficos
  const timelineData = timeline?.dates?.map((date, i) => ({
    name: date,
    value: timeline.amounts[i],
  })) || []

  const categoryData = categories?.categories?.map((cat, i) => ({
    name: cat,
    value: categories.amounts[i],
  })) || []

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-500">Resumen de tus gastos y estadísticas</p>
        </div>
        <PeriodSelector
          value={filters.period}
          onChange={(value) => updateFilter('period', value)}
        />
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Balance Total"
          value={summary?.total_monto || 0}
          change={5.2}
          description="vs mes anterior"
          icon={DollarSign}
          color="primary"
        />
        <StatCard
          title="Gastos Este Mes"
          value={summary?.monto_este_mes || 0}
          change={-2.4}
          description="vs mes anterior"
          icon={TrendingDown}
          color="danger"
        />
        <StatCard
          title="Promedio Diario"
          value={summary?.promedio_diario || 0}
          change={1.8}
          description="últimos 30 días"
          icon={TrendingUp}
          color="info"
        />
        <StatCard
          title="Total Gastos"
          value={summary?.total_gastos || 0}
          description="registrados"
          icon={CreditCard}
          color="warning"
        />
      </div>

      {/* Spending Limit */}
      <ProgressBar
        current={summary?.monto_este_mes || 0}
        total={50000}
        label="Límite de Gasto Mensual"
      />

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Chart
          data={timelineData}
          type="line"
          title="Gastos en el Tiempo"
          height={300}
        />
        <Chart
          data={categoryData}
          type="bar"
          title="Gastos por Categoría"
          height={300}
        />
      </div>

      {/* Categories Grid */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Categorías</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {categories?.categories?.slice(0, 6).map((cat, i) => {
            const totalAmount = categories.amounts.reduce((a, b) => a + b, 0)
            const percentage = (categories.amounts[i] / totalAmount) * 100

            return (
              <CategoryCard
                key={cat}
                category={cat}
                amount={categories.amounts[i]}
                percentage={percentage}
                count={10}
              />
            )
          })}
        </div>
      </div>

      {/* Activities Table */}
      <ActivityTable activities={activities || []} loading={loading} />
    </div>
  )
}
```

### PeriodSelector Component
**Archivo**: `src/components/PeriodSelector.jsx`

```jsx
import React from 'react'
import clsx from 'clsx'

const periods = [
  { value: 7, label: '7 días' },
  { value: 30, label: '30 días' },
  { value: 90, label: '90 días' },
  { value: 365, label: '1 año' },
]

export default function PeriodSelector({ value, onChange }) {
  return (
    <div className="inline-flex bg-white rounded-lg border border-gray-300 p-1">
      {periods.map((period) => (
        <button
          key={period.value}
          onClick={() => onChange(period.value)}
          className={clsx(
            'px-4 py-2 text-sm font-medium rounded-md transition-colors',
            value === period.value
              ? 'bg-primary-500 text-white'
              : 'text-gray-700 hover:bg-gray-100'
          )}
        >
          {period.label}
        </button>
      ))}
    </div>
  )
}
```

---

## Fase 7: Instalación y Ejecución

### Paso 1: Instalar Dependencias
```bash
cd interface/web/frontend
npm install
```

### Paso 2: Iniciar Dev Server
```bash
npm run dev
```

El dashboard estará disponible en `http://localhost:3000`

### Paso 3: Build para Producción
```bash
npm run build
```

Los archivos de producción estarán en `interface/web/dist/`

---

## Integración con Backend

El frontend se conectará con el backend Flask a través del proxy configurado en `vite.config.js`:

```javascript
proxy: {
  '/api': {
    target: 'http://localhost:5000',
    changeOrigin: true,
  },
}
```

Asegurarse de que el backend esté corriendo en `http://localhost:5000` antes de iniciar el frontend.

---

## Checklist de Implementación

### ✅ Completado
- [x] Setup de Vite + React + Tailwind
- [x] Estructura de carpetas
- [x] Archivos de configuración
- [x] Utilidades y formatters
- [x] Cliente API

### 🔄 Por Implementar
- [ ] Todos los componentes base (StatCard, Badge, etc.)
- [ ] Layout components (Sidebar, Header)
- [ ] Componentes de datos (Chart, ActivityTable)
- [ ] Custom hooks (useApi, useDashboardData, useFilters)
- [ ] Dashboard page completo
- [ ] PeriodSelector component
- [ ] Responsive design testing
- [ ] Optimización de performance

---

## Testing

### Testing Manual
1. Verificar que todos los componentes renderizan correctamente
2. Probar filtros y selectores de periodo
3. Verificar responsividad en mobile/tablet/desktop
4. Probar carga de datos desde API
5. Verificar que los gráficos se actualizan correctamente

### Testing de Integración
1. Backend corriendo en puerto 5000
2. Frontend corriendo en puerto 3000
3. Verificar que las llamadas API funcionan
4. Verificar CORS configurado correctamente
5. Probar refresh de datos

---

## Próximos Pasos

1. **Completar componentes faltantes** según este plan
2. **Integrar con backend** una vez que los endpoints estén listos
3. **Agregar funcionalidades extras**:
   - Exportación a CSV/PDF
   - Sistema de notificaciones
   - Modo oscuro
   - Más filtros avanzados

---

**Documento creado**: 2025-10-29
**Estado**: En desarrollo - UI base creada
**Siguiente**: Completar componentes y página Dashboard
