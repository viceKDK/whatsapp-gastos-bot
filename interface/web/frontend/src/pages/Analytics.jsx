import React from 'react'
import { TrendingUp, TrendingDown, PieChart, Calendar } from 'lucide-react'
import { useDashboardData } from '../hooks/useDashboardData'
import { useFilters } from '../hooks/useFilters'
import StatCard from '../components/StatCard'
import Chart from '../components/Chart'
import CategoryCard from '../components/CategoryCard'
import PeriodSelector from '../components/PeriodSelector'
import Loading from '../components/Loading'
import { formatCurrency } from '../utils/formatters'
import { t } from '../utils/i18n'

export default function Analytics() {
  const { filters, updateFilter } = useFilters()
  const { summary, categories, timeline, loading, error } = useDashboardData(filters.period)

  if (loading) {
    return <Loading text={t('analytics.loading')} />
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600 mb-4">Error cargando datos: {error}</p>
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

  // Calcular tendencia
  const trend = summary?.cambio_porcentual || 0
  const trendText = trend > 0 ? (t('analytics.trendGeneral') + ' +') : trend < 0 ? (t('analytics.trendGeneral') + ' -') : 'OK'

  // Calcular gasto total del periodo
  const gastoTotalPeriodo = timeline?.amounts?.reduce((sum, amount) => sum + amount, 0) || 0

  // Calcular promedio diario del periodo
  const diasConGastos = timeline?.dates?.length || 0
  const promedioDiarioPeriodo = diasConGastos > 0 ? gastoTotalPeriodo / diasConGastos : 0

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{t('analytics.title')}</h1>
          <p className="text-gray-500">{t('analytics.subtitle')}</p>
        </div>
        <PeriodSelector
          value={filters.period}
          onChange={(value) => updateFilter('period', value)}
        />
      </div>

      {/* Trend Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatCard
          title={t('analytics.trendGeneral')}
          value={trendText}
          change={trend}
          description={t('analytics.vsPeriodoAnterior')}
          icon={trend >= 0 ? TrendingUp : TrendingDown}
          color={trend >= 0 ? 'danger' : 'primary'}
        />
        <StatCard
          title={t('analytics.categoriaPrincipal')}
          value={summary?.categoria_mas_comun || 'N/A'}
          description={t('analytics.masFrecuente')}
          icon={PieChart}
          color="info"
        />
        <StatCard
          title={t('analytics.gastoTotal')}
          value={gastoTotalPeriodo}
          description={t('analytics.ultimosNDias')(filters.period)}
          icon={Calendar}
          color="warning"
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Chart
          data={timelineData}
          type="line"
          title={t('analytics.tendenciaTemporal')}
          height={350}
        />
        <Chart
          data={categoryData}
          type="pie"
          title={t('analytics.distribucionCategoria')}
          height={350}
        />
      </div>

      {/* Detailed Categories */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-4">{t('analytics.analisisCategoria')}</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {categories?.categories?.map((cat, i) => {
            const totalAmount = categories.amounts.reduce((a, b) => a + b, 0)
            const percentage = totalAmount > 0 ? (categories.amounts[i] / totalAmount) * 100 : 0

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

      {/* Summary Stats */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">{t('analytics.resumenPeriodo')}</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <p className="text-sm text-gray-600">{t('analytics.totalGastado')}</p>
            <p className="text-xl font-bold text-gray-900">
              {formatCurrency(gastoTotalPeriodo)}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600">{t('analytics.promedioDiario')}</p>
            <p className="text-xl font-bold text-gray-900">
              {formatCurrency(promedioDiarioPeriodo)}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600">{t('analytics.diasConGastos')}</p>
            <p className="text-xl font-bold text-gray-900">
              {diasConGastos}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600">{t('analytics.categoriasActivas')}</p>
            <p className="text-xl font-bold text-gray-900">
              {categories?.categories?.length || 0}
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
