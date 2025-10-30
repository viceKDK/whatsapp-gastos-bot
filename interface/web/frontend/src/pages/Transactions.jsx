import React, { useMemo, useState } from 'react'
import { Search, Download, Calendar, ChevronLeft, ChevronRight } from 'lucide-react'
import { useApi } from '../hooks/useApi'
import api from '../services/api'
import { formatCurrency, formatDate, getCategoryIcon } from '../utils/formatters'
import { isSafeMode } from '../utils/settingsStorage'
import { t } from '../utils/i18n'
import Loading from '../components/Loading'
import Badge from '../components/Badge'
import { useNotifications } from '../context/NotificationsContext'

export default function Transactions() {
  const { notify } = useNotifications()
  const [searchQuery, setSearchQuery] = useState('')
  const [categoryFilter, setCategoryFilter] = useState('all')
  const [selectedMonth, setSelectedMonth] = useState(() => {
    const now = new Date()
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
  })

  // Build stable deps key to trigger refetch on filters change
  const depsKey = useMemo(() => JSON.stringify({ searchQuery, categoryFilter, selectedMonth }), [searchQuery, categoryFilter, selectedMonth])

  const monthRange = useMemo(() => {
    if (!selectedMonth) return {}
    const [y, m] = selectedMonth.split('-').map(Number)
    const first = new Date(y, m - 1, 1)
    const last = new Date(y, m, 0)
    const from = first.toISOString().slice(0, 10)
    const to = last.toISOString().slice(0, 10)
    return { from, to }
  }, [selectedMonth])

  const { data: activities, loading, error, refetch } = useApi(
    () => api.searchTransactions({
      query: searchQuery,
      categoria: categoryFilter,
      from: monthRange.from,
      to: monthRange.to,
      limit: 50,
    }),
    [depsKey]
  )

  if (loading) {
    return <Loading text={t('transactions.title') + '...'} />
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600 mb-4">Error: {error}</p>
        <button onClick={refetch} className="btn btn-primary">
          Reintentar
        </button>
      </div>
    )
  }

  const filteredActivities = activities || []

  // Obtener categorías únicas
  const uniqueCategories = [...new Set(activities?.map(a => a.categoria) || [])]

  

  const handleExport = async () => {
    try {
      const { blob, filename } = await api.exportTransactions({ format: 'csv', from: monthRange.from, to: monthRange.to })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      a.remove()
      window.URL.revokeObjectURL(url)
      notify({ type: 'success', title: 'Exportación lista', message: 'Se descargó gastos.csv' })
    } catch (e) {
      notify({ type: 'error', title: 'Error exportando', message: e.message })
    }
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{t('transactions.title')}</h1>
          <p className="text-gray-500">{t('transactions.subtitle')}</p>
        </div>
        <button className="btn btn-primary" onClick={handleExport}>
          <Download className="w-4 h-4" />
          {t('transactions.export')}
        </button>
      </div>

      {/* Filters */}
      <div className="card">
        <div className="flex flex-col md:flex-row gap-4">
          {/* Search */}
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder={t('transactions.searchPlaceholder')}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>

          {/* Category Filter */}
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value="all">{t('transactions.allCategories')}</option>
            {uniqueCategories.map(cat => (
              <option key={cat} value={cat}>{cat}</option>
            ))}
          </select>

          {/* Filtro por mes */}
          <div className="flex items-center gap-2">
            <button
              type="button"
              className="p-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              title="Mes anterior"
              onClick={() => {
                const [y, m] = selectedMonth.split('-').map(Number)
                const d = new Date(y, m - 2, 1)
                setSelectedMonth(`${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2,'0')}`)
              }}
            >
              <ChevronLeft className="w-4 h-4" title={t('transactions.monthPrev')} />
            </button>
            <input
              type="month"
              value={selectedMonth}
              onChange={(e) => setSelectedMonth(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg"
            />
            <button
              type="button"
              className="p-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              title="Siguiente mes"
              onClick={() => {
                const [y, m] = selectedMonth.split('-').map(Number)
                const d = new Date(y, m, 1)
                setSelectedMonth(`${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2,'0')}`)
              }}
            >
              <ChevronRight className="w-4 h-4" title={t('transactions.monthNext')} />
            </button>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card">
          <p className="text-sm text-gray-600 mb-1">{t('transactions.statsTotal')}</p>
          <p className="text-2xl font-bold text-gray-900">{filteredActivities.length}</p>
        </div>
        <div className="card">
          <p className="text-sm text-gray-600 mb-1">{t('transactions.statsSpent')}</p>
          <p className="text-2xl font-bold text-gray-900">
            {formatCurrency(filteredActivities.reduce((sum, a) => sum + a.monto, 0))}
          </p>
        </div>
        <div className="card">
          <p className="text-sm text-gray-600 mb-1">{t('transactions.statsAvg')}</p>
          <p className="text-2xl font-bold text-gray-900">
            {formatCurrency(
              filteredActivities.length > 0
                ? filteredActivities.reduce((sum, a) => sum + a.monto, 0) / filteredActivities.length
                : 0
            )}
          </p>
        </div>
      </div>

      {/* Transactions Table */}
      <div className="card">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-600 uppercase">{t('transactions.table.date')}</th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-600 uppercase">{t('transactions.table.category')}</th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-600 uppercase">{t('transactions.table.description')}</th>
                <th className="text-right py-3 px-4 text-xs font-semibold text-gray-600 uppercase">{t('transactions.table.amount')}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {filteredActivities.map((activity, index) => (
                <tr key={index} className="hover:bg-gray-50 transition-colors">
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-2">
                      <Calendar className="w-4 h-4 text-gray-400" />
                      <span className="text-sm text-gray-600">
                        {formatDate(activity.fecha)}
                      </span>
                    </div>
                  </td>
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
                      {isSafeMode() ? '••••' : (activity.descripcion || '-')}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-right">
                    <span className="font-semibold text-gray-900">
                      {formatCurrency(activity.monto)}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {filteredActivities.length === 0 && (
          <div className="text-center py-8">
            <p className="text-gray-500">{t('transactions.empty')}</p>
          </div>
        )}
      </div>
    </div>
  )
}
