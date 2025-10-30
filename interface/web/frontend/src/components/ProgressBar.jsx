import React from 'react'
import { formatCurrency } from '../utils/formatters'
import { t } from '../utils/i18n'

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
          {percentage.toFixed(1)}% {t('dashboard.used') || 'usado'}
        </span>
        {isDanger && (
          <span className="text-xs font-medium text-red-600">
            {t('dashboard.limitExceeded') || '¡Límite superado!'}
          </span>
        )}
        {isWarning && !isDanger && (
          <span className="text-xs font-medium text-yellow-600">
            {t('dashboard.closeToLimit') || 'Cerca del límite'}
          </span>
        )}
      </div>
    </div>
  )
}
