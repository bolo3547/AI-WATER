'use client'

import { useEffect, useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import HippoSplash from './HippoSplash'

export type LoaderState = 
  | 'authenticating'
  | 'loading-dashboard'
  | 'connecting-sensors'
  | 'waiting-data'
  | 'route-loading'
  | 'custom'

interface LiveStatus {
  mqtt_connected: boolean
  data_fresh: boolean
  last_sensor_seen_at: string | null
}

interface AppLoaderProps {
  isLoading: boolean
  state?: LoaderState
  customMessage?: string
  minDisplayTime?: number // Minimum time to show loader (ms)
  showDelay?: number // Delay before showing loader (ms)
  checkLiveStatus?: boolean // Whether to check sensor status
  tenantId?: string
  onComplete?: () => void
}

const stateMessages: Record<LoaderState, string> = {
  'authenticating': 'Authenticating…',
  'loading-dashboard': 'Loading dashboard…',
  'connecting-sensors': 'Connecting to sensors…',
  'waiting-data': 'Waiting for data…',
  'route-loading': 'Loading AquaWatch…',
  'custom': ''
}

export default function AppLoader({
  isLoading,
  state = 'route-loading',
  customMessage,
  minDisplayTime = 800,
  showDelay = 200,
  checkLiveStatus = false,
  tenantId,
  onComplete
}: AppLoaderProps) {
  const [shouldShow, setShouldShow] = useState(false)
  const [canHide, setCanHide] = useState(false)
  const [liveStatus, setLiveStatus] = useState<LiveStatus>({
    mqtt_connected: true,
    data_fresh: true,
    last_sensor_seen_at: null
  })
  const [startTime, setStartTime] = useState<number | null>(null)

  // Fetch live status if enabled
  const fetchLiveStatus = useCallback(async () => {
    if (!checkLiveStatus) return
    
    try {
      const endpoint = tenantId 
        ? `/api/tenants/${tenantId}/system/live-status`
        : '/api/system/live-status'
      
      const response = await fetch(endpoint)
      if (response.ok) {
        const data = await response.json()
        setLiveStatus({
          mqtt_connected: data.mqtt_connected ?? true,
          data_fresh: data.data_fresh ?? true,
          last_sensor_seen_at: data.last_sensor_seen_at ?? null
        })
      }
    } catch (error) {
      console.warn('[AppLoader] Failed to fetch live status:', error)
    }
  }, [checkLiveStatus, tenantId])

  // Show delay logic - prevents flash for quick loads
  useEffect(() => {
    let showTimer: NodeJS.Timeout
    
    if (isLoading) {
      setStartTime(Date.now())
      showTimer = setTimeout(() => {
        setShouldShow(true)
      }, showDelay)
    } else {
      setShouldShow(false)
      setStartTime(null)
    }

    return () => clearTimeout(showTimer)
  }, [isLoading, showDelay])

  // Minimum display time logic
  useEffect(() => {
    if (!shouldShow || !startTime) {
      setCanHide(true)
      return
    }

    setCanHide(false)
    const elapsed = Date.now() - startTime
    const remaining = Math.max(0, minDisplayTime - elapsed)

    const timer = setTimeout(() => {
      setCanHide(true)
    }, remaining)

    return () => clearTimeout(timer)
  }, [shouldShow, startTime, minDisplayTime])

  // Fetch live status periodically when loading
  useEffect(() => {
    if (!shouldShow || !checkLiveStatus) return

    fetchLiveStatus()
    const interval = setInterval(fetchLiveStatus, 2000)
    
    return () => clearInterval(interval)
  }, [shouldShow, checkLiveStatus, fetchLiveStatus])

  // Lock body scroll when visible
  useEffect(() => {
    if (shouldShow) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }
    
    return () => {
      document.body.style.overflow = ''
    }
  }, [shouldShow])

  const handleComplete = useCallback(() => {
    if (canHide && onComplete) {
      onComplete()
    }
  }, [canHide, onComplete])

  const message = customMessage || stateMessages[state]
  const isVisible = shouldShow && (isLoading || !canHide)

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          className="fixed inset-0 z-[9999] bg-slate-950"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.4, ease: "easeOut" }}
        >
          <HippoSplash
            isOnline={liveStatus.mqtt_connected}
            dataFresh={liveStatus.data_fresh}
            message={message}
            onComplete={handleComplete}
          />
        </motion.div>
      )}
    </AnimatePresence>
  )
}

// Hook for easy integration with data fetching
export function useAppLoader(initialLoading: boolean = false) {
  const [isLoading, setIsLoading] = useState(initialLoading)
  const [state, setState] = useState<LoaderState>('route-loading')
  const [customMessage, setCustomMessage] = useState<string>('')

  const startLoading = useCallback((newState?: LoaderState, message?: string) => {
    if (newState) setState(newState)
    if (message) setCustomMessage(message)
    setIsLoading(true)
  }, [])

  const stopLoading = useCallback(() => {
    setIsLoading(false)
    setCustomMessage('')
  }, [])

  return {
    isLoading,
    state,
    customMessage,
    startLoading,
    stopLoading,
    setLoaderState: setState,
    setLoaderMessage: setCustomMessage,
    LoaderComponent: () => (
      <AppLoader 
        isLoading={isLoading} 
        state={state} 
        customMessage={customMessage}
      />
    )
  }
}
