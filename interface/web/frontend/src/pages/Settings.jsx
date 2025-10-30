import React, { useState } from 'react'
import { Save, Bell, Shield, Database, Palette, DollarSign } from 'lucide-react'
import { LIMITE_GASTO_MENSUAL } from '../utils/constants'
import { saveSettings, getSettings } from '../utils/settingsStorage'
import { useNotifications } from '../context/NotificationsContext'
import { t } from '../utils/i18n'

export default function Settings() {
  const { notify } = useNotifications()
  const initial = getSettings()
  const [settings, setSettings] = useState({
    monthlyLimit: initial.monthlyLimit ?? LIMITE_GASTO_MENSUAL,
    notifications: initial.notifications ?? true,
    currency: initial.currency ?? 'UYU',
    autoBackup: initial.autoBackup ?? true,
    language: initial.language ?? 'es',
  })

  const handleSave = () => {
    const oldLang = initial.language

    saveSettings(settings)

    notify({ type: 'success', title: t('settings.title'), message: t('settings.saved') })

    // Si cambió el idioma, recargar la página
    if (settings.language !== oldLang) {
      setTimeout(() => window.location.reload(), 500)
    }
  }

  const handleChange = (key, value) => {
    setSettings(prev => ({ ...prev, [key]: value }))
  }

  // Sin modo oscuro: no aplicamos clases globales

  return (
    <div className="space-y-6 animate-fade-in max-w-4xl">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">{t('settings.title')}</h1>
        <p className="text-gray-500">{t('settings.subtitle')}</p>
      </div>

      {/* General Settings */}
      <div className="card">
        <div className="flex items-center gap-3 mb-4">
          <DollarSign className="w-5 h-5 text-primary-500" />
          <h3 className="text-lg font-semibold text-gray-900">{t('settings.limitsAndCurrency')}</h3>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {t('settings.monthlyLimit')}
            </label>
            <input
              type="number"
              value={settings.monthlyLimit}
              onChange={(e) => handleChange('monthlyLimit', Number(e.target.value))}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
            <p className="text-xs text-gray-500 mt-1">
              {t('settings.monthlyLimitDesc')}
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {t('settings.currency')}
            </label>
            <select
              value={settings.currency}
              onChange={(e) => handleChange('currency', e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="UYU">UYU - Peso Uruguayo</option>
              <option value="USD">USD - Dólar</option>
            </select>
          </div>
        </div>
      </div>

      {/* Notifications */}
      <div className="card">
        <div className="flex items-center gap-3 mb-4">
          <Bell className="w-5 h-5 text-primary-500" />
          <h3 className="text-lg font-semibold text-gray-900">{t('settings.notifications')}</h3>
        </div>

        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium text-gray-900">{t('settings.limitNotifications')}</p>
              <p className="text-sm text-gray-600">{t('settings.limitNotificationsDesc')}</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={settings.notifications}
                onChange={(e) => handleChange('notifications', e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-500"></div>
            </label>
          </div>
        </div>
      </div>

      {/* Appearance (solo idioma) */}
      <div className="card">
        <div className="flex items-center gap-3 mb-4">
          <Palette className="w-5 h-5 text-primary-500" />
          <h3 className="text-lg font-semibold text-gray-900">{t('settings.appearance')}</h3>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {t('settings.language')}
            </label>
            <select
              value={settings.language}
              onChange={(e) => handleChange('language', e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="es">Español</option>
              <option value="en">English</option>
            </select>
          </div>
        </div>
      </div>

      {/* Data & Privacy */}
      <div className="card">
        <div className="flex items-center gap-3 mb-4">
          <Database className="w-5 h-5 text-primary-500" />
          <h3 className="text-lg font-semibold text-gray-900">{t('settings.dataBackup')}</h3>
        </div>

        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium text-gray-900">{t('settings.autoBackup')}</p>
              <p className="text-sm text-gray-600">{t('settings.autoBackupDesc')}</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={settings.autoBackup}
                onChange={(e) => handleChange('autoBackup', e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-500"></div>
            </label>
          </div>

          <div className="flex gap-3">
            <button className="btn btn-outline flex-1">
              {t('settings.exportData')}
            </button>
            <button className="btn btn-outline flex-1">
              {t('settings.importData')}
            </button>
          </div>
        </div>
      </div>

      {/* Save Button */}
      <div className="flex justify-end">
        <button onClick={handleSave} className="btn btn-primary">
          <Save className="w-4 h-4" />
          {t('settings.saveChanges')}
        </button>
      </div>
    </div>
  )
}
