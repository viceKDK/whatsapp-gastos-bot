import React from 'react'
import { DollarSign, TrendingUp, TrendingDown, CreditCard } from 'lucide-react'
import { useDashboardData } from '../hooks/useDashboardData'
import { useFilters } from '../hooks/useFilters'
import StatCard from '../components/StatCard'
import Chart from '../components/Chart'
import ActivityTable from '../components/ActivityTable'
import CategoryCard from '../components/CategoryCard'
import ProgressBar from '../components/ProgressBar'
import PeriodSelector from '../components/PeriodSelector'
import Loading from '../components/Loading'
import { t } from '../utils/i18n'

export default function Dashboard() {
  const { filters, updateFilter } = useFilters()
  const { summary, categories, timeline, activities, loading, error, refetch } = useDashboardData(filters.period)

  if (loading) {
    return <Loading text={t('dashboard.loading')} />
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
          <h1 className="text-2xl font-bold text-gray-900">{t('dashboard.title')}</h1>
          <p className="text-gray-500">{t('dashboard.subtitle')}</p>
        </div>
        <PeriodSelector
          value={filters.period}
          onChange={(value) => updateFilter('period', value)}
        />
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title={t('dashboard.balanceTotal')}
          value={summary?.total_monto || 0}
          change={5.2}
          description={t('dashboard.vsMesAnterior')}
          icon={DollarSign}
          color="primary"
        />
        <StatCard
          title={t('dashboard.gastosMes')}
          value={summary?.monto_este_mes || 0}
          change={-2.4}
          description={t('dashboard.vsMesAnterior')}
          icon={TrendingDown}
          color="danger"
        />
        <StatCard
          title={t('dashboard.promedioDiario')}
          value={summary?.promedio_diario || 0}
          change={1.8}
          description={t('dashboard.ultimos30')}
          icon={TrendingUp}
          color="info"
        />
        <StatCard
          title={t('dashboard.totalGastos')}
          value={String(summary?.total_gastos || 0)}
          description={t('dashboard.registrado')}
          icon={CreditCard}
          color="warning"
        />
      </div>

      {/* Spending Limit */}
      <ProgressBar
        current={summary?.monto_este_mes || 0}
        total={50000}
        label={t('dashboard.monthlyLimit')}
      />

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Chart
          data={timelineData}
          type="line"
          title={t('dashboard.timeline')}
          height={300}
        />
        <Chart
          data={categoryData}
          type="bar"
          title={t('dashboard.byCategory')}
          height={300}
        />
      </div>

      {/* Categories Grid */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-4">{t('dashboard.categories')}</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {categories?.categories?.slice(0, 6).map((cat, i) => {
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

      {/* Activities Table */}
      <ActivityTable activities={activities || []} loading={loading} />
    </div>
  )
}
