import React, { createContext, useContext, useCallback, useState } from 'react'

const NotificationsContext = createContext(null)

export function NotificationsProvider({ children }) {
  const [notifications, setNotifications] = useState([])

  const removeNotification = useCallback((id) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id))
  }, [])

  const notify = useCallback((payload) => {
    const id = `${Date.now()}-${Math.random().toString(36).slice(2)}`
    const n = {
      id,
      type: payload.type || 'info',
      title: payload.title || 'Notificación',
      message: payload.message || '',
      timeout: payload.timeout ?? 4000,
    }
    setNotifications((prev) => [n, ...prev].slice(0, 20))
    if (n.timeout > 0) {
      setTimeout(() => removeNotification(id), n.timeout)
    }
    return id
  }, [removeNotification])

  return (
    <NotificationsContext.Provider value={{ notifications, notify, removeNotification }}>
      {children}
    </NotificationsContext.Provider>
  )
}

export function useNotifications() {
  const ctx = useContext(NotificationsContext)
  if (!ctx) throw new Error('useNotifications must be used within NotificationsProvider')
  return ctx
}

