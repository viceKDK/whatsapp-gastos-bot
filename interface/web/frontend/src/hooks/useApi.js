import { useState, useEffect } from 'react'
import { useNotifications } from '../context/NotificationsContext'

export function useApi(apiCall, dependencies = []) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const { notify } = useNotifications()

  const fetchData = async () => {
    try {
      setLoading(true)
      setError(null)
      const result = await apiCall()
      setData(result.data || result)
    } catch (err) {
      setError(err.message)
      console.error('API Error:', err)
      notify({ type: 'error', title: 'Error de API', message: err.message })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, dependencies)

  const refetch = () => {
    fetchData()
  }

  return { data, loading, error, refetch }
}
