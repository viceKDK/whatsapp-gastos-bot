import { format, formatDistance, formatRelative } from 'date-fns'
import { es, enUS } from 'date-fns/locale'
import { getCurrency, getLanguage, isSafeMode, getFxUYUperUSD } from './settingsStorage'

/**
 * Formatea un monto a formato de moneda
 */
export const formatCurrency = (amount, currency) => {
  if (isSafeMode()) return '••••'
  const lang = getLanguage()
  const cur = currency || getCurrency()
  let displayAmount = Number(amount) || 0

  // Los montos base vienen en UYU. Si el usuario eligió USD, convertimos al vuelo.
  if (cur === 'USD') {
    const fx = getFxUYUperUSD() // UYU por 1 USD
    if (isFinite(fx) && fx > 0) {
      displayAmount = displayAmount / fx
    }
  }
  const locale = lang === 'en' ? 'en-US' : 'es-UY'
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency: cur,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(displayAmount)
}

/**
 * Formatea un número sin símbolo de moneda
 */
export const formatNumber = (number, decimals = 0) => {
  if (isSafeMode()) return '••'
  const lang = getLanguage()
  const locale = lang === 'en' ? 'en-US' : 'es-UY'
  return new Intl.NumberFormat(locale, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(number)
}

/**
 * Formatea un porcentaje
 */
export const formatPercent = (value, decimals = 1) => {
  return `${value >= 0 ? '+' : ''}${value.toFixed(decimals)}%`
}

/**
 * Formatea una fecha
 */
export const formatDate = (date, formatStr = 'dd/MM/yyyy') => {
  if (!date) return ''
  const dateObj = typeof date === 'string' ? new Date(date) : date
  const lang = getLanguage()
  const loc = lang === 'en' ? enUS : es
  const pattern = formatStr || (lang === 'en' ? 'MM/dd/yyyy' : 'dd/MM/yyyy')
  return format(dateObj, pattern, { locale: loc })
}

/**
 * Formatea una fecha y hora
 */
export const formatDateTime = (date) => {
  if (!date) return ''
  const dateObj = typeof date === 'string' ? new Date(date) : date
  const lang = getLanguage()
  const loc = lang === 'en' ? enUS : es
  const pattern = lang === 'en' ? 'MM/dd/yyyy HH:mm' : 'dd/MM/yyyy HH:mm'
  return format(dateObj, pattern, { locale: loc })
}

/**
 * Formatea una fecha relativa (hace X tiempo)
 */
export const formatRelativeDate = (date) => {
  if (!date) return ''
  const dateObj = typeof date === 'string' ? new Date(date) : date
  const lang = getLanguage()
  const loc = lang === 'en' ? enUS : es
  return formatDistance(dateObj, new Date(), { addSuffix: true, locale: loc })
}

/**
 * Obtiene el color para un cambio porcentual
 */
export const getChangeColor = (change) => {
  if (change > 0) return 'text-green-600'
  if (change < 0) return 'text-red-600'
  return 'text-gray-600'
}

/**
 * Obtiene el icono para un cambio porcentual
 */
export const getChangeIcon = (change) => {
  if (change > 0) return '↑'
  if (change < 0) return '↓'
  return '→'
}

/**
 * Abrevia números grandes
 */
export const abbreviateNumber = (num) => {
  if (num >= 1000000) {
    return `${(num / 1000000).toFixed(1)}M`
  }
  if (num >= 1000) {
    return `${(num / 1000).toFixed(1)}K`
  }
  return num.toString()
}

/**
 * Capitaliza la primera letra de un string
 */
export const capitalize = (str) => {
  if (!str) return ''
  return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase()
}

/**
 * Obtiene el color para una categoría
 */
export const getCategoryColor = (category) => {
  const colors = {
    comida: 'bg-red-500',
    transporte: 'bg-blue-500',
    entretenimiento: 'bg-yellow-500',
    salud: 'bg-green-500',
    servicios: 'bg-purple-500',
    ropa: 'bg-pink-500',
    educacion: 'bg-indigo-500',
    hogar: 'bg-orange-500',
    trabajo: 'bg-teal-500',
    super: 'bg-cyan-500',
    nafta: 'bg-gray-500',
    otros: 'bg-gray-400',
  }
  return colors[category?.toLowerCase()] || 'bg-gray-400'
}

/**
 * Obtiene el icono para una categoría
 */
export const getCategoryIcon = (category) => {
  const icons = {
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
  return icons[category?.toLowerCase()] || '📦'
}
