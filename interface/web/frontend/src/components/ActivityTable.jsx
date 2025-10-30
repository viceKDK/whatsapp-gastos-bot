import React from 'react'
import { formatCurrency, formatDate, getCategoryIcon } from '../utils/formatters'
import { isSafeMode } from '../utils/settingsStorage'
import { t } from '../utils/i18n'

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
        <h3 className="text-lg font-semibold text-gray-900">{t('transactions.title')}</h3>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-200">
              <th className="text-left py-3 px-4 text-xs font-semibold text-gray-600 uppercase">{t('transactions.table.category')}</th>
              <th className="text-left py-3 px-4 text-xs font-semibold text-gray-600 uppercase">{t('transactions.table.description')}</th>
              <th className="text-right py-3 px-4 text-xs font-semibold text-gray-600 uppercase">{t('transactions.table.amount')}</th>
              <th className="text-right py-3 px-4 text-xs font-semibold text-gray-600 uppercase">{t('transactions.table.date')}</th>
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
                    {isSafeMode() ? '••••' : (activity.descripcion || '-')}
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
          <p className="text-gray-500">{t('transactions.empty')}</p>
        </div>
      )}
    </div>
  )
}
