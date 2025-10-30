import React from 'react'
import { FileText, Download, Calendar, TrendingUp } from 'lucide-react'
import { useDashboardData } from '../hooks/useDashboardData'
import { formatCurrency, formatDate } from '../utils/formatters'
import Chart from '../components/Chart'
import Loading from '../components/Loading'
import { t } from '../utils/i18n'

export default function Reports() {
  const { summary, categories, timeline, loading } = useDashboardData(30)

  if (loading) {
    return <Loading text={t('reports.loading')} />
  }

  const timelineData = timeline?.dates?.map((date, i) => ({
    name: date,
    value: timeline.amounts[i],
  })) || []

  const categoryData = categories?.categories?.map((cat, i) => ({
    name: cat,
    value: categories.amounts[i],
  })) || []

  const handleExport = (format) => {
    alert(`Exportando reporte en formato ${format}...`)
    // Aquí irá la lógica de exportación
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{t('reports.title')}</h1>
          <p className="text-gray-500">{t('reports.subtitle')}</p>
        </div>
      </div>

      {/* Export Options */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">{t('reports.exportar')}</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button
            onClick={() => handleExport('PDF')}
            className="p-4 border-2 border-gray-300 rounded-lg hover:border-primary-500 hover:bg-primary-50 transition-all"
          >
            <FileText className="w-8 h-8 text-primary-500 mb-2" />
            <h4 className="font-semibold text-gray-900 mb-1">{t('reports.reportePdf')}</h4>
            <p className="text-sm text-gray-600">{t('reports.pdfDesc')}</p>
          </button>

          <button
            onClick={() => handleExport('Excel')}
            className="p-4 border-2 border-gray-300 rounded-lg hover:border-primary-500 hover:bg-primary-50 transition-all"
          >
            <Download className="w-8 h-8 text-primary-500 mb-2" />
            <h4 className="font-semibold text-gray-900 mb-1">{t('reports.excel')}</h4>
            <p className="text-sm text-gray-600">{t('reports.excelDesc')}</p>
          </button>

          <button
            onClick={() => handleExport('CSV')}
            className="p-4 border-2 border-gray-300 rounded-lg hover:border-primary-500 hover:bg-primary-50 transition-all"
          >
            <FileText className="w-8 h-8 text-primary-500 mb-2" />
            <h4 className="font-semibold text-gray-900 mb-1">{t('reports.csv')}</h4>
            <p className="text-sm text-gray-600">{t('reports.csvDesc')}</p>
          </button>
        </div>
      </div>

      {/* Summary Report */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">{t('reports.resumenMensual')}</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          <div>
            <p className="text-sm text-gray-600 mb-1">{t('reports.totalGastos')}</p>
            <p className="text-2xl font-bold text-gray-900">
              {summary?.gastos_este_mes || 0}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600 mb-1">{t('reports.montoTotal')}</p>
            <p className="text-2xl font-bold text-gray-900">
              {formatCurrency(summary?.monto_este_mes || 0)}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600 mb-1">{t('reports.promedioDiario')}</p>
            <p className="text-2xl font-bold text-gray-900">
              {formatCurrency(summary?.promedio_diario || 0)}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600 mb-1">{t('reports.categorias')}</p>
            <p className="text-2xl font-bold text-gray-900">
              {categories?.categories?.length || 0}
            </p>
          </div>
        </div>
      </div>

      {/* Charts for Report */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Chart
          data={timelineData}
          type="line"
          title={t('reports.evolucion')}
          height={300}
        />
        <Chart
          data={categoryData}
          type="bar"
          title={t('reports.gastosCategoria')}
          height={300}
        />
      </div>

      {/* Category Breakdown */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">{t('reports.desgloseCategoria')}</h3>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-600 uppercase">{t('reports.colCategoria')}</th>
                <th className="text-right py-3 px-4 text-xs font-semibold text-gray-600 uppercase">{t('reports.colMonto')}</th>
                <th className="text-right py-3 px-4 text-xs font-semibold text-gray-600 uppercase">{t('reports.colPorcentaje')}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {categories?.categories?.map((cat, i) => {
                const totalAmount = categories.amounts.reduce((a, b) => a + b, 0)
                const percentage = totalAmount > 0 ? (categories.amounts[i] / totalAmount) * 100 : 0

                return (
                  <tr key={cat} className="hover:bg-gray-50">
                    <td className="py-3 px-4 font-medium text-gray-900 capitalize">{cat}</td>
                    <td className="py-3 px-4 text-right font-semibold text-gray-900">
                      {formatCurrency(categories.amounts[i])}
                    </td>
                    <td className="py-3 px-4 text-right text-gray-600">
                      {percentage.toFixed(1)}%
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
