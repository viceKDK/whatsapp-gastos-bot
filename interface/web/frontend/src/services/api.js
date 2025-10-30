const API_BASE_URL = '/api'

class ApiService {
  async request(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`

    try {
      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
        ...options,
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      return data
    } catch (error) {
      console.error('API Error:', error)
      throw error
    }
  }

  // Summary stats
  async getSummary() {
    return this.request('/summary')
  }

  // Categories
  async getCategories(days = 30) {
    return this.request(`/categories?days=${days}`)
  }

  // Timeline
  async getTimeline(days = 30) {
    return this.request(`/timeline?days=${days}`)
  }

  // Recent activities
  async getRecentActivities(limit = 10) {
    return this.request(`/recent?limit=${limit}`)
  }

  // Search transactions (v2)
  async searchTransactions({ query = '', categoria = 'all', from, to, min, max, limit = 50 } = {}) {
    const params = new URLSearchParams()
    if (query) params.set('query', query)
    if (categoria && categoria !== 'all') params.set('categoria', categoria)
    if (from) params.set('from', from)
    if (to) params.set('to', to)
    if (min != null) params.set('min', String(min))
    if (max != null) params.set('max', String(max))
    if (limit) params.set('limit', String(limit))
    return this.request(`/v2/search?${params.toString()}`)
  }

  // Export transactions (v2)
  async exportTransactions({ format = 'csv', from, to } = {}) {
    const params = new URLSearchParams()
    params.set('format', format)
    if (from) params.set('from', from)
    if (to) params.set('to', to)
    // For csv, we want raw text; do a direct fetch
    const url = `/api/v2/export?${params.toString()}`
    const res = await fetch(url)
    if (!res.ok) throw new Error(`Export failed (${res.status})`)
    if (format === 'csv') {
      const blob = await res.blob()
      return { blob, filename: 'gastos.csv' }
    }
    return res.json()
  }

  // System metrics
  async getMetrics() {
    return this.request('/metrics')
  }

  // Refresh data
  async refreshData() {
    return this.request('/refresh', { method: 'GET' })
  }
}

export default new ApiService()
