'use client'

import { AlertTriangle, WifiOff, Database, Wifi, Activity, RefreshCw } from 'lucide-react'
import { useConnectionBanner, useSystemStatus } from '@/contexts/SystemStatusContext'

export function ConnectionBanner() {
  const banner = useConnectionBanner()
  const { refetch, isLoading } = useSystemStatus()

  if (!banner.show) return null

  const styles = {
    error: 'bg-red-600 text-white',
    warning: 'bg-amber-500 text-white',
    info: 'bg-blue-500 text-white',
    loading: 'bg-slate-600 text-white',
    success: 'bg-emerald-500 text-white'
  }

  const icons = {
    error: <Database className="w-4 h-4" />,
    warning: <AlertTriangle className="w-4 h-4" />,
    info: <Activity className="w-4 h-4" />,
    loading: <RefreshCw className="w-4 h-4 animate-spin" />,
    success: <Wifi className="w-4 h-4" />
  }

  return (
    <div className={`${styles[banner.type]} px-4 py-2 flex items-center justify-center gap-2 text-sm font-medium`}>
      {icons[banner.type]}
      <span>{banner.message}</span>
      <button 
        onClick={() => refetch()}
        disabled={isLoading}
        className="ml-2 px-2 py-0.5 rounded bg-white/20 hover:bg-white/30 transition-colors text-xs"
      >
        {isLoading ? 'Checking...' : 'Retry'}
      </button>
    </div>
  )
}

// Smaller inline status indicator
export function SystemStatusIndicator() {
  const { status, isOnline, isDataFresh } = useSystemStatus()

  if (!status) {
    return (
      <div className="flex items-center gap-2 text-xs text-slate-500">
        <RefreshCw className="w-3 h-3 animate-spin" />
        <span>Checking...</span>
      </div>
    )
  }

  const statusColor = isOnline && isDataFresh 
    ? 'bg-emerald-500' 
    : isOnline 
      ? 'bg-amber-500' 
      : 'bg-red-500'

  const statusText = isOnline && isDataFresh 
    ? 'Live' 
    : isOnline 
      ? 'Degraded' 
      : 'Offline'

  return (
    <div className="flex items-center gap-2 text-xs">
      <span className={`w-2 h-2 rounded-full ${statusColor} animate-pulse`} />
      <span className={`font-medium ${isOnline ? 'text-slate-700' : 'text-red-600'}`}>
        {statusText}
      </span>
      {status.active_sensors > 0 && (
        <span className="text-slate-500">
          • {status.active_sensors}/{status.total_sensors} sensors
        </span>
      )}
    </div>
  )
}
