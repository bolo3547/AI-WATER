'use client'

import { createContext, useContext, useEffect, useState, useCallback, ReactNode } from 'react'
import useSWR from 'swr'

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
  uptime_seconds: number
  last_check: string
  error?: string
}

interface SystemStatusContextType {
  status: SystemStatus | null
  isLoading: boolean
  error: Error | null
  refetch: () => void
  isOnline: boolean
  isDataFresh: boolean
  hasAnySensorData: boolean
  canShowRealData: boolean
}

const defaultStatus: SystemStatus = {
  mqtt_connected: false,
  database_connected: false,
  last_sensor_seen_at: null,
  active_sensors: 0,
  offline_sensors: 0,
  total_sensors: 0,
  data_fresh: false,
  data_staleness_minutes: null,
  system_health: 'offline',
  uptime_seconds: 0,
  last_check: new Date().toISOString()
}

const SystemStatusContext = createContext<SystemStatusContextType>({
  status: null,
  isLoading: true,
  error: null,
  refetch: () => {},
  isOnline: false,
  isDataFresh: false,
  hasAnySensorData: false,
  canShowRealData: false
})

const fetcher = async (url: string) => {
  const res = await fetch(url)
  if (!res.ok) {
    throw new Error('Failed to fetch system status')
  }
  return res.json()
}

export function SystemStatusProvider({ children }: { children: ReactNode }) {
  const { data, error, isLoading, mutate } = useSWR<SystemStatus>(
    '/api/system/status',
    fetcher,
    {
      refreshInterval: 10000, // Check every 10 seconds
      revalidateOnFocus: true,
      dedupingInterval: 5000,
      errorRetryCount: 3,
      errorRetryInterval: 5000
    }
  )

  const status = data || null
  
  // Derived states
  const isOnline = status?.system_health === 'online' || status?.system_health === 'degraded'
  const isDataFresh = status?.data_fresh ?? false
  const hasAnySensorData = !!status?.last_sensor_seen_at
  const canShowRealData = isOnline && hasAnySensorData

  const refetch = useCallback(() => {
    mutate()
  }, [mutate])

  return (
    <SystemStatusContext.Provider value={{
      status,
      isLoading,
      error: error || null,
      refetch,
      isOnline,
      isDataFresh,
      hasAnySensorData,
      canShowRealData
    }}>
      {children}
    </SystemStatusContext.Provider>
  )
}

export function useSystemStatus() {
  const context = useContext(SystemStatusContext)
  if (!context) {
    throw new Error('useSystemStatus must be used within SystemStatusProvider')
  }
  return context
}

// Hook for showing connection banner
export function useConnectionBanner() {
  const { status, isOnline, isDataFresh, hasAnySensorData } = useSystemStatus()
  
  if (!status) {
    return { show: false, type: 'loading' as const, message: 'Checking system status...' }
  }

  if (!status.database_connected) {
    return { 
      show: true, 
      type: 'error' as const, 
      message: 'Database connection failed. Please contact support.' 
    }
  }

  if (!status.mqtt_connected && status.total_sensors === 0) {
    return { 
      show: true, 
      type: 'warning' as const, 
      message: 'No sensors configured. Connect ESP32 sensors via MQTT to start monitoring.' 
    }
  }

  if (status.active_sensors === 0 && status.total_sensors > 0) {
    return { 
      show: true, 
      type: 'warning' as const, 
      message: `All ${status.total_sensors} sensors are offline. Check sensor connections.` 
    }
  }

  if (!hasAnySensorData) {
    return { 
      show: true, 
      type: 'info' as const, 
      message: 'Waiting for sensor data. No readings received yet.' 
    }
  }

  if (!isDataFresh && status.data_staleness_minutes) {
    return { 
      show: true, 
      type: 'warning' as const, 
      message: `Data is stale (${Math.round(status.data_staleness_minutes)} minutes old). Live updates may be delayed.` 
    }
  }

  return { show: false, type: 'success' as const, message: '' }
}
