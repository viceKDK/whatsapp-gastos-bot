import React from 'react'
import clsx from 'clsx'

const periods = [
  { value: 7, label: '7 días' },
  { value: 30, label: '30 días' },
  { value: 90, label: '90 días' },
  { value: 365, label: '1 año' },
]

export default function PeriodSelector({ value, onChange }) {
  return (
    <div className="inline-flex bg-white rounded-lg border border-gray-300 p-1">
      {periods.map((period) => (
        <button
          key={period.value}
          onClick={() => onChange(period.value)}
          className={clsx(
            'px-4 py-2 text-sm font-medium rounded-md transition-colors',
            value === period.value
              ? 'bg-primary-500 text-white'
              : 'text-gray-700 hover:bg-gray-100'
          )}
        >
          {period.label}
        </button>
      ))}
    </div>
  )
}
