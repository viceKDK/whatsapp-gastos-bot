import { useState, useEffect } from 'react'
import api from '../services/api'

export function useDashboardData(period = 30) {
  const [data, setData] = useState({
    summary: null,
    categories: null,
    timeline: null,
    activities: null,
  })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchAllData = async () => {
    try {
      setLoading(true)
      setError(null)

      const [summary, categories, timeline, activities] = await Promise.all([
        api.getSummary(),
        api.getCategories(period),
        api.getTimeline(period),
        api.getRecentActivities(10),
      ])

      setData({
        summary: summary.data,
        categories: categories.data,
        timeline: timeline.data,
        activities: activities.data,
      })
    } catch (err) {
      setError(err.message)
      console.error('Dashboard data error:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchAllData()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [period])

  return { ...data, loading, error, refetch: fetchAllData }
}
