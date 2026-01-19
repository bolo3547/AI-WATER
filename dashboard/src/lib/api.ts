'use client'

import useSWR from 'swr'

// Fetcher function for SWR
const fetcher = (url: string) => fetch(url).then(res => {
  if (!res.ok) throw new Error('Network response was not ok')
  return res.json()
})

// API base URL - configured in next.config.js to proxy to backend
const API_BASE = '/api'

// Types matching the backend API
export interface SystemStatus {
  status: string
  timestamp: string
  components: {
    database: string
    ai_engine: string
    sensors: string
  }
}

export interface DMAData {
  dma_id: string
  name: string
  nrw_percent: number
  real_losses: number
  priority_score: number
  status: 'healthy' | 'warning' | 'critical'
  trend: 'up' | 'down' | 'stable'
  inflow: number
  consumption: number
  leak_count: number
  confidence: number
  last_updated: string
}

export interface LeakData {
  id: string
  dma_id: string
  location: string
  estimated_loss: number
  priority: 'high' | 'medium' | 'low'
  status: 'detected' | 'investigating' | 'confirmed' | 'repaired'
  confidence: number
  detected_at: string
  method: string
  explanation: string
}

export interface SystemMetrics {
  total_nrw_percent: number
  total_nrw_trend: 'up' | 'down' | 'stable'
  total_real_losses: number
  water_recovered_30d: number
  revenue_recovered_30d: number
  active_high_priority_leaks: number
  ai_status: 'operational' | 'degraded' | 'offline'
  ai_confidence: number
  dma_count: number
  sensor_count: number
  last_data_received: string
}

export interface TimeSeriesPoint {
  timestamp: string
  nrw?: number
  target?: number
  inflow?: number
  consumption?: number
  minimumNightFlow?: number
  [key: string]: string | number | undefined
}

// Hook for system status
export function useSystemStatus() {
  return useSWR<SystemStatus>(`${API_BASE}/status`, fetcher, {
    refreshInterval: 30000, // Refresh every 30 seconds
    revalidateOnFocus: true
  })
}

// Hook for system-wide metrics (Executive Dashboard)
export function useSystemMetrics() {
  return useSWR<SystemMetrics>(`${API_BASE}/metrics`, fetcher, {
    refreshInterval: 60000 // Refresh every minute
  })
}

// Hook for DMA list
export function useDMAList() {
  return useSWR<DMAData[]>(`${API_BASE}/dmas`, fetcher, {
    refreshInterval: 60000
  })
}

// Hook for single DMA details
export function useDMADetails(dmaId: string) {
  return useSWR<DMAData>(
    dmaId ? `${API_BASE}/dmas/${dmaId}` : null, 
    fetcher,
    { refreshInterval: 30000 }
  )
}

// Hook for DMA time series data
export function useDMATimeSeries(dmaId: string, period: '24h' | '7d' | '30d' = '24h') {
  return useSWR<TimeSeriesPoint[]>(
    dmaId ? `${API_BASE}/dmas/${dmaId}/timeseries?period=${period}` : null,
    fetcher,
    { refreshInterval: 60000 }
  )
}

// Hook for leaks (optionally filtered by DMA)
export function useLeaks(dmaId?: string, status?: string) {
  const params = new URLSearchParams()
  if (dmaId) params.append('dma_id', dmaId)
  if (status) params.append('status', status)
  
  const queryString = params.toString()
  const url = `${API_BASE}/leaks${queryString ? `?${queryString}` : ''}`
  
  return useSWR<LeakData[]>(url, fetcher, {
    refreshInterval: 30000
  })
}

// Hook for NRW trend data
export function useNRWTrend(period: '24h' | '7d' | '30d' | '90d' = '30d') {
  return useSWR<TimeSeriesPoint[]>(
    `${API_BASE}/analytics/nrw-trend?period=${period}`,
    fetcher,
    { refreshInterval: 300000 } // Refresh every 5 minutes
  )
}

// Utility: Format timestamp for display
export function formatTimestamp(timestamp: string): string {
  const date = new Date(timestamp)
  return date.toLocaleString('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// Utility: Format relative time
export function formatRelativeTime(timestamp: string): string {
  const date = new Date(timestamp)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  
  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins}m ago`
  
  const diffHours = Math.floor(diffMins / 60)
  if (diffHours < 24) return `${diffHours}h ago`
  
  const diffDays = Math.floor(diffHours / 24)
  return `${diffDays}d ago`
}

// Utility: Format large numbers
export function formatNumber(value: number, decimals: number = 0): string {
  if (value >= 1000000) {
    return `${(value / 1000000).toFixed(1)}M`
  }
  if (value >= 1000) {
    return `${(value / 1000).toFixed(1)}K`
  }
  return value.toFixed(decimals)
}

// Utility: Format currency (Zambian Kwacha)
export function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-ZM', {
    style: 'currency',
    currency: 'ZMW',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(value)
}
