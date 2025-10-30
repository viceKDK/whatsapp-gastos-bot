import React from 'react'
import { formatCurrency, getCategoryColor, getCategoryIcon } from '../utils/formatters'
import { t } from '../utils/i18n'

export default function CategoryCard({
  category,
  amount,
  percentage,
  count
}) {
  return (
    <div className="card flex items-center gap-4">
      <div className={`p-3 rounded-xl ${getCategoryColor(category)} bg-opacity-10`}>
        <span className="text-2xl">{getCategoryIcon(category)}</span>
      </div>

      <div className="flex-1">
        <h4 className="text-sm font-semibold text-gray-900 capitalize">
          {category}
        </h4>
        <p className="text-xs text-gray-500">
          {count} {count === 1 ? t('components.itemSingular') : t('components.itemPlural')}
        </p>
      </div>

      <div className="text-right">
        <p className="text-lg font-bold text-gray-900">
          {formatCurrency(amount)}
        </p>
        {percentage !== undefined && (
          <p className="text-xs text-gray-500">
            {percentage.toFixed(1)}%
          </p>
        )}
      </div>
    </div>
  )
}
