import React from 'react'
import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  BarChart3,
  Receipt,
  FileText,
  Settings,
  X
} from 'lucide-react'
import clsx from 'clsx'
import { t } from '../utils/i18n'

const menuItems = [
  { icon: LayoutDashboard, labelKey: 'menu.dashboard', to: '/' },
  { icon: BarChart3, labelKey: 'menu.analytics', to: '/analytics', badge: '28' },
  { icon: Receipt, labelKey: 'menu.transactions', to: '/transacciones' },
]

const bottomItems = [
  { icon: Settings, labelKey: 'menu.settings', to: '/configuracion' },
]

export default function Sidebar({ isOpen, onToggle }) {
  return (
    <>
      {/* Overlay para mobile */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={onToggle}
        />
      )}

      {/* Sidebar */}
      <aside className={clsx(
        'fixed lg:static inset-y-0 left-0 z-50',
        'w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700',
        'flex flex-col',
        'transition-transform duration-300 ease-in-out',
        isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
      )}>
        {/* Logo */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-primary-500 rounded-xl flex items-center justify-center">
              <span className="text-white font-bold text-xl">B</span>
            </div>
            <div>
              <h1 className="font-bold text-gray-900 dark:text-white">Bot Gastos</h1>
              <p className="text-xs text-gray-500 dark:text-gray-400">Dashboard</p>
            </div>
          </div>

          {/* Botón cerrar mobile */}
          <button
            onClick={onToggle}
            className="lg:hidden p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
          >
            <X className="w-5 h-5 dark:text-gray-300" />
          </button>
        </div>

        {/* Menu Items */}
        <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
          <div className="mb-6">
            <p className="px-3 mb-2 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">
              {t('menu.main')}
            </p>
            {menuItems.map((item, index) => (
              <MenuItem key={index} {...item} />
            ))}
          </div>

          <div>
            <p className="px-3 mb-2 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">
              {t('menu.general')}
            </p>
            {bottomItems.map((item, index) => (
              <MenuItem key={index} {...item} />
            ))}
          </div>
        </nav>

        {/* User Profile */}
        <div className="p-4 border-t border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-3 p-3 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer">
            <div className="w-10 h-10 bg-primary-100 dark:bg-primary-900 rounded-full flex items-center justify-center">
              <span className="text-primary-600 dark:text-primary-300 font-semibold">U</span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 dark:text-white truncate">Usuario</p>
              <p className="text-xs text-gray-500 dark:text-gray-400 truncate">usuario@email.com</p>
            </div>
          </div>
        </div>
      </aside>
    </>
  )
}

function MenuItem({ icon: Icon, label, labelKey, to, badge }) {
  const text = labelKey ? t(labelKey) : label
  return (
    <NavLink
      to={to}
      className={({ isActive }) => clsx(
        'flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors',
        isActive
          ? 'bg-primary-50 dark:bg-primary-900 text-primary-600 dark:text-primary-300 font-medium'
          : 'text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
      )}
    >
      <Icon className="w-5 h-5" />
      <span className="flex-1">{text}</span>
      {badge && (
        <span className="px-2 py-0.5 text-xs font-semibold bg-primary-100 dark:bg-primary-900 text-primary-600 dark:text-primary-300 rounded-full">
          {badge}
        </span>
      )}
    </NavLink>
  )
}
