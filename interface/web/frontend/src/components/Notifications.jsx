import React from 'react'
import { X, CheckCircle, AlertTriangle, Info } from 'lucide-react'
import { useNotifications } from '../context/NotificationsContext'

const typeStyles = {
  success: {
    bg: 'bg-green-50',
    icon: <CheckCircle className="w-5 h-5 text-green-600" />,
  },
  warning: {
    bg: 'bg-yellow-50',
    icon: <AlertTriangle className="w-5 h-5 text-yellow-600" />,
  },
  error: {
    bg: 'bg-red-50',
    icon: <AlertTriangle className="w-5 h-5 text-red-600" />,
  },
  info: {
    bg: 'bg-blue-50',
    icon: <Info className="w-5 h-5 text-blue-600" />,
  },
}

export default function Notifications() {
  const { notifications, removeNotification } = useNotifications()

  return (
    <div className="fixed top-4 right-4 z-50 space-y-2 w-80">
      {notifications.map((n) => {
        const style = typeStyles[n.type] || typeStyles.info
        return (
          <div key={n.id} className={`animate-slide-in shadow rounded-lg p-3 ${style.bg} border border-gray-200`}> 
            <div className="flex items-start gap-3">
              {style.icon}
              <div className="flex-1">
                <p className="text-sm font-semibold text-gray-900">{n.title}</p>
                {n.message && <p className="text-sm text-gray-700 mt-0.5">{n.message}</p>}
              </div>
              <button onClick={() => removeNotification(n.id)} className="p-1 hover:bg-gray-100 rounded">
                <X className="w-4 h-4 text-gray-500" />
              </button>
            </div>
          </div>
        )
      })}
    </div>
  )
}

