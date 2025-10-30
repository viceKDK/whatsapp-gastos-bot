import React from 'react'
import { TrendingUp, TrendingDown } from 'lucide-react'
import { formatCurrency, formatPercent, getChangeColor } from '../utils/formatters'

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

          {change !== undefined ? (
            <div className="flex items-center gap-2">
              <span className={`flex items-center gap-1 text-sm font-medium ${getChangeColor(change)}`}>
                <TrendIcon className="w-4 h-4" />
                {formatPercent(change)}
              </span>
              {description && (
                <span className="text-xs text-gray-500">{description}</span>
              )}
            </div>
          ) : description ? (
            <p className="text-sm text-gray-500">{description}</p>
          ) : null}
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
