import React from 'react'
import { Bell, Menu, RefreshCw } from 'lucide-react'
import SearchBar from './SearchBar'
import { useNotifications } from '../context/NotificationsContext'

export default function Header({ onMenuClick, onRefresh }) {
  const { notifications } = useNotifications()
  return (
    <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 sticky top-0 z-30">
      <div className="flex items-center justify-between px-6 py-4">
        {/* Left: Menu button + Search */}
        <div className="flex items-center gap-4 flex-1">
          {/* Hamburger menu - Solo visible en mobile */}
          <button
            onClick={onMenuClick}
            className="lg:hidden p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
            aria-label="Abrir menú"
          >
            <Menu className="w-5 h-5 dark:text-gray-300" />
          </button>

          <SearchBar />
        </div>

        {/* Right: Actions */}
        <div className="flex items-center gap-3">
          {/* Refresh button */}
          <button
            onClick={onRefresh}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
            title="Refrescar datos"
          >
            <RefreshCw className="w-5 h-5 text-gray-600 dark:text-gray-300" />
          </button>

          {/* Notifications */}
          <div className="relative">
            <button className="relative p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors" title="Notificaciones">
              <Bell className="w-5 h-5 text-gray-600 dark:text-gray-300" />
              {notifications.length > 0 && (
                <span className="absolute -top-0.5 -right-0.5 min-w-[18px] h-[18px] px-1 bg-red-500 text-white text-[10px] leading-[18px] rounded-full text-center">
                  {notifications.length}
                </span>
              )}
            </button>
          </div>

          {/* User avatar */}
          <button className="w-9 h-9 bg-primary-100 dark:bg-primary-900 rounded-full flex items-center justify-center hover:bg-primary-200 dark:hover:bg-primary-800 transition-colors">
            <span className="text-primary-600 dark:text-primary-300 font-semibold text-sm">U</span>
          </button>
        </div>
      </div>
    </header>
  )
}
