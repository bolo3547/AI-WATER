'use client'

import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react'

// Notification types
export type NotificationType = 'alert' | 'warning' | 'success' | 'info'
export type NotificationPriority = 'high' | 'medium' | 'low'

export interface Notification {
  id: string
  type: NotificationType
  priority: NotificationPriority
  title: string
  message: string
  timestamp: Date
  read: boolean
  source?: string
  actionUrl?: string
}

// Sensor status interface
export interface SensorStatus {
  connected: boolean
  count: number
  lastUpdate: Date | null
}

interface NotificationContextType {
  notifications: Notification[]
  unreadCount: number
  soundEnabled: boolean
  sensorStatus: SensorStatus
  addNotification: (notification: Omit<Notification, 'id' | 'timestamp' | 'read'>) => void
  markAsRead: (id: string) => void
  markAllAsRead: () => void
  clearAll: () => void
  toggleSound: () => void
  playAlertSound: (type: NotificationType) => void
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined)

// Audio frequencies for different notification types
const NOTIFICATION_SOUNDS = {
  alert: { frequency: 880, duration: 200, repeat: 3 },      // High urgent beep
  warning: { frequency: 660, duration: 300, repeat: 2 },    // Medium warning tone
  success: { frequency: 523, duration: 150, repeat: 2 },    // Pleasant ding
  info: { frequency: 440, duration: 100, repeat: 1 },       // Simple notification
}

// Create audio context for generating tones
let audioContext: AudioContext | null = null

function getAudioContext(): AudioContext | null {
  if (typeof window === 'undefined') return null
  
  if (!audioContext) {
    try {
      audioContext = new (window.AudioContext || (window as any).webkitAudioContext)()
    } catch (e) {
      console.warn('Web Audio API not supported')
      return null
    }
  }
  return audioContext
}

// Generate a beep tone
function playTone(frequency: number, duration: number, volume: number = 0.3): Promise<void> {
  return new Promise((resolve) => {
    const ctx = getAudioContext()
    if (!ctx) {
      resolve()
      return
    }

    // Resume context if suspended (browser autoplay policy)
    if (ctx.state === 'suspended') {
      ctx.resume()
    }

    const oscillator = ctx.createOscillator()
    const gainNode = ctx.createGain()

    oscillator.connect(gainNode)
    gainNode.connect(ctx.destination)

    oscillator.frequency.value = frequency
    oscillator.type = 'sine'

    // Fade in and out for smoother sound
    gainNode.gain.setValueAtTime(0, ctx.currentTime)
    gainNode.gain.linearRampToValueAtTime(volume, ctx.currentTime + 0.01)
    gainNode.gain.linearRampToValueAtTime(0, ctx.currentTime + duration / 1000)

    oscillator.start(ctx.currentTime)
    oscillator.stop(ctx.currentTime + duration / 1000)

    oscillator.onended = () => resolve()
  })
}

// Play notification sound sequence
async function playNotificationSound(type: NotificationType): Promise<void> {
  const sound = NOTIFICATION_SOUNDS[type]
  
  for (let i = 0; i < sound.repeat; i++) {
    await playTone(sound.frequency, sound.duration)
    if (i < sound.repeat - 1) {
      await new Promise(resolve => setTimeout(resolve, 100))
    }
  }
}

export function NotificationProvider({ children }: { children: ReactNode }) {
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [soundEnabled, setSoundEnabled] = useState(true)
  const [sensorStatus, setSensorStatus] = useState<SensorStatus>({
    connected: false,
    count: 0,
    lastUpdate: null
  })

  // Load sound preference from localStorage
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('notification_sound')
      if (saved !== null) {
        setSoundEnabled(saved === 'true')
      }
    }
  }, [])

  // Check for real sensor connections
  useEffect(() => {
    const checkSensors = async () => {
      try {
        // Check for real sensor data from the API
        const response = await fetch('/api/realtime?type=sensors')
        if (response.ok) {
          const data = await response.json()
          
          // Check if we have real sensor data (not just mock data)
          const sensors = data.data || []
          const realSensors = sensors.filter((s: any) => 
            // Real sensors should have recent timestamps and actual readings
            s.lastReading && 
            new Date(s.lastReading).getTime() > Date.now() - 5 * 60 * 1000 && // Last 5 minutes
            s.status === 'active'
          )
          
          setSensorStatus({
            connected: realSensors.length > 0,
            count: realSensors.length,
            lastUpdate: new Date()
          })
          
          // If sensors just connected, add a welcome notification
          if (realSensors.length > 0 && !sensorStatus.connected) {
            const welcomeNotification: Notification = {
              id: `sensor-connected-${Date.now()}`,
              type: 'success',
              priority: 'low',
              title: 'Sensors Connected',
              message: `${realSensors.length} sensor(s) are now online and transmitting data.`,
              timestamp: new Date(),
              read: false,
              source: 'Sensor Network'
            }
            setNotifications(prev => [welcomeNotification, ...prev].slice(0, 50))
            if (soundEnabled) {
              playNotificationSound('success')
            }
          }
        } else {
          setSensorStatus({
            connected: false,
            count: 0,
            lastUpdate: new Date()
          })
        }
      } catch (error) {
        console.log('Sensor check failed:', error)
        setSensorStatus({
          connected: false,
          count: 0,
          lastUpdate: new Date()
        })
      }
    }

    // Check immediately and then every 30 seconds
    checkSensors()
    const interval = setInterval(checkSensors, 30000)
    return () => clearInterval(interval)
  }, [soundEnabled, sensorStatus.connected])

  // Only generate real alerts when sensors are connected
  useEffect(() => {
    if (!sensorStatus.connected) {
      // No sensors connected - don't generate any alerts
      return
    }

    // Poll for real alerts from connected sensors
    const checkForAlerts = async () => {
      try {
        const response = await fetch('/api/alerts')
        if (response.ok) {
          const data = await response.json()
          const alerts = data.alerts || []
          
          // Process only new alerts from real sensors
          alerts.forEach((alert: any) => {
            // Check if this alert already exists
            const exists = notifications.some(n => n.id === alert.id || n.id === `alert-${alert.id}`)
            
            if (!exists && alert.status === 'active') {
              const newNotification: Notification = {
                id: `alert-${alert.id}`,
                type: alert.severity === 'critical' ? 'alert' : 
                      alert.severity === 'high' ? 'alert' :
                      alert.severity === 'medium' ? 'warning' : 'info',
                priority: alert.severity === 'critical' || alert.severity === 'high' ? 'high' :
                         alert.severity === 'medium' ? 'medium' : 'low',
                title: alert.title || 'System Alert',
                message: alert.description || alert.message || 'An alert was triggered by the sensor network.',
                timestamp: new Date(alert.timestamp || Date.now()),
                read: false,
                source: alert.source || 'Sensor Network',
                actionUrl: alert.actionUrl || '/actions'
              }
              
              setNotifications(prev => [newNotification, ...prev].slice(0, 50))
              
              if (soundEnabled) {
                playNotificationSound(newNotification.type)
              }
            }
          })
        }
      } catch (error) {
        console.log('Alert check failed:', error)
      }
    }

    // Check for alerts every 30 seconds when sensors are connected
    const interval = setInterval(checkForAlerts, 30000)
    checkForAlerts() // Check immediately
    
    return () => clearInterval(interval)
  }, [sensorStatus.connected, soundEnabled, notifications])

  const addNotification = useCallback((notification: Omit<Notification, 'id' | 'timestamp' | 'read'>) => {
    const newNotification: Notification = {
      ...notification,
      id: Date.now().toString(),
      timestamp: new Date(),
      read: false
    }
    
    setNotifications(prev => [newNotification, ...prev].slice(0, 50))
    
    if (soundEnabled) {
      playNotificationSound(notification.type)
    }
  }, [soundEnabled])

  const markAsRead = useCallback((id: string) => {
    setNotifications(prev => 
      prev.map(n => n.id === id ? { ...n, read: true } : n)
    )
  }, [])

  const markAllAsRead = useCallback(() => {
    setNotifications(prev => prev.map(n => ({ ...n, read: true })))
  }, [])

  const clearAll = useCallback(() => {
    setNotifications([])
  }, [])

  const toggleSound = useCallback(() => {
    setSoundEnabled(prev => {
      const newValue = !prev
      if (typeof window !== 'undefined') {
        localStorage.setItem('notification_sound', String(newValue))
      }
      return newValue
    })
  }, [])

  const playAlertSound = useCallback((type: NotificationType) => {
    if (soundEnabled) {
      playNotificationSound(type)
    }
  }, [soundEnabled])

  const unreadCount = notifications.filter(n => !n.read).length

  return (
    <NotificationContext.Provider value={{
      notifications,
      unreadCount,
      soundEnabled,
      sensorStatus,
      addNotification,
      markAsRead,
      markAllAsRead,
      clearAll,
      toggleSound,
      playAlertSound
    }}>
      {children}
    </NotificationContext.Provider>
  )
}

export function useNotifications() {
  const context = useContext(NotificationContext)
  if (!context) {
    throw new Error('useNotifications must be used within NotificationProvider')
  }
  return context
}
