// Constantes de la aplicación

export const CATEGORIAS = [
  'comida',
  'transporte',
  'entretenimiento',
  'salud',
  'servicios',
  'ropa',
  'educacion',
  'hogar',
  'trabajo',
  'otros',
  'super',
  'nafta',
]

export const PERIODOS = [
  { value: 7, label: '7 días' },
  { value: 30, label: '30 días' },
  { value: 90, label: '90 días' },
  { value: 365, label: '1 año' },
]

export const COLORES_CATEGORIAS = {
  comida: '#EF4444',
  transporte: '#3B82F6',
  entretenimiento: '#F59E0B',
  salud: '#10B981',
  servicios: '#8B5CF6',
  ropa: '#EC4899',
  educacion: '#6366F1',
  hogar: '#F97316',
  trabajo: '#14B8A6',
  super: '#06B6D4',
  nafta: '#6B7280',
  otros: '#9CA3AF',
}

export const ICONOS_CATEGORIAS = {
  comida: '🍽️',
  transporte: '🚗',
  entretenimiento: '🎬',
  salud: '🏥',
  servicios: '🔧',
  ropa: '👕',
  educacion: '📚',
  hogar: '🏠',
  trabajo: '💼',
  super: '🛒',
  nafta: '⛽',
  otros: '📦',
}

export const API_ENDPOINTS = {
  SUMMARY: '/api/summary',
  CATEGORIES: '/api/categories',
  TIMELINE: '/api/timeline',
  RECENT: '/api/recent',
  METRICS: '/api/metrics',
  REFRESH: '/api/refresh',
}

export const LIMITE_GASTO_MENSUAL = 50000

export const UMBRALES_ALERTA = {
  WARNING: 80, // 80% del límite
  DANGER: 100, // 100% del límite
}
