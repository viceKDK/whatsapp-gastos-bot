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
