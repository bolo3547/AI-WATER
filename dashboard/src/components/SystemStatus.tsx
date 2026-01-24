'use client'

import { useState, useEffect } from 'react'
import { AlertTriangle, Wifi, WifiOff, Database, Clock, RefreshCw } from 'lucide-react'

interface SystemStatus {
  mqtt_connected: boolean
  database_connected: boolean
  last_sensor_seen_at: string | null
  active_sensors: number
  offline_sensors: number
  total_sensors: number
  data_fresh: boolean
  data_staleness_minutes: number | null
  system_health: 'online' | 'degraded' | 'offline'
}

export function SystemStatusBanner() {
  const [status, setStatus] = useState<SystemStatus | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const fetchStatus = async () => {
    try {
      const res = await fetch('/api/system/status')
      if (!res.ok) throw new Error('Failed to fetch status')
      const data = await res.json()
      setStatus(data)
      setError(null)
    } catch (err) {
      setError('Unable to check system status')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchStatus()
    const interval = setInterval(fetchStatus, 30000) // Check every 30 seconds
    return () => clearInterval(interval)
  }, [])

  if (isLoading) return null

  // Determine what banner to show
  const showBanner = status && (
    status.system_health === 'offline' ||
    status.system_health === 'degraded' ||
    !status.database_connected ||
    status.total_sensors === 0 ||
    !status.data_fresh
  )

  if (!showBanner && !error) return null

  // Determine banner type and message
  let bannerType: 'error' | 'warning' | 'info' = 'info'
  let message = ''
  let icon = <AlertTriangle className="w-5 h-5" />

  if (error) {
    bannerType = 'error'
    message = error
    icon = <AlertTriangle className="w-5 h-5" />
  } else if (!status?.database_connected) {
    bannerType = 'error'
    message = 'Database offline. Data cannot be saved or retrieved.'
    icon = <Database className="w-5 h-5" />
  } else if (status.total_sensors === 0) {
    bannerType = 'info'
    message = 'No sensors registered. Connect ESP32 sensors via MQTT to begin monitoring.'
    icon = <WifiOff className="w-5 h-5" />
  } else if (!status.mqtt_connected && status.active_sensors === 0) {
    bannerType = 'warning'
    message = 'MQTT offline. No live data from sensors.'
    icon = <WifiOff className="w-5 h-5" />
  } else if (!status.data_fresh && status.data_staleness_minutes !== null) {
    bannerType = 'warning'
    message = `Stale data. Last sensor reading was ${Math.round(status.data_staleness_minutes)} minutes ago.`
    icon = <Clock className="w-5 h-5" />
  } else if (status.offline_sensors > 0) {
    bannerType = 'warning'
    message = `${status.offline_sensors} of ${status.total_sensors} sensors offline.`
    icon = <Wifi className="w-5 h-5" />
  }

  const bgColors = {
    error: 'bg-red-600',
    warning: 'bg-amber-600',
    info: 'bg-blue-600'
  }

  return (
    <div className={`${bgColors[bannerType]} text-white px-4 py-2 flex items-center justify-between`}>
      <div className="flex items-center gap-3">
        {icon}
        <span className="text-sm font-medium">{message}</span>
      </div>
      <button
        onClick={fetchStatus}
        className="p-1.5 hover:bg-white/20 rounded-lg transition-colors"
        title="Refresh status"
      >
        <RefreshCw className="w-4 h-4" />
      </button>
    </div>
  )
}

// Empty state component for dashboards
interface EmptyStateProps {
  type: 'sensors' | 'dmas' | 'leaks' | 'work-orders' | 'metrics'
  message?: string
}

export function EmptyState({ type, message }: EmptyStateProps) {
  const defaultMessages = {
    sensors: 'No sensors registered. Connect ESP32 sensors to begin monitoring.',
    dmas: 'No DMAs configured. Add DMAs in the admin panel to begin monitoring.',
    leaks: 'No leaks detected. The AI system is monitoring for anomalies.',
    'work-orders': 'No work orders. Create one when a leak requires field response.',
    metrics: 'Waiting for sensor data. Connect sensors to see live metrics.'
  }

  const icons = {
    sensors: <WifiOff className="w-12 h-12 text-slate-500" />,
    dmas: <Database className="w-12 h-12 text-slate-500" />,
    leaks: <AlertTriangle className="w-12 h-12 text-green-500" />,
    'work-orders': <Clock className="w-12 h-12 text-slate-500" />,
    metrics: <RefreshCw className="w-12 h-12 text-slate-500" />
  }

  return (
    <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
      {icons[type]}
      <p className="mt-4 text-slate-400 text-sm max-w-md">
        {message || defaultMessages[type]}
      </p>
    </div>
  )
}

// Skeleton loader for cards
export function MetricCardSkeleton() {
  return (
    <div className="bg-slate-800/50 rounded-xl p-4 animate-pulse">
      <div className="h-4 bg-slate-700 rounded w-24 mb-3"></div>
      <div className="h-8 bg-slate-700 rounded w-16 mb-2"></div>
      <div className="h-3 bg-slate-700 rounded w-20"></div>
    </div>
  )
}

// Metric display that handles null/undefined values
interface MetricValueProps {
  value: number | null | undefined
  unit?: string
  placeholder?: string
  decimals?: number
}

export function MetricValue({ value, unit = '', placeholder = '--', decimals = 1 }: MetricValueProps) {
  if (value === null || value === undefined) {
    return <span className="text-slate-500">{placeholder}</span>
  }
  
  const formatted = typeof decimals === 'number' 
    ? value.toFixed(decimals) 
    : value.toLocaleString()
  
  return (
    <span>
      {formatted}
      {unit && <span className="text-slate-400 ml-1">{unit}</span>}
    </span>
  )
}
