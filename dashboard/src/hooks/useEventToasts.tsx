'use client'

import { useEffect, useCallback, useRef } from 'react'
import { useTenantEvents, TenantEvent, isLeakDetectedEvent, isSensorOfflineEvent, isWorkOrderCreatedEvent, isAlertCriticalEvent } from '@/hooks/useTenantEvents'
import { useNotifications, NotificationType, NotificationPriority, NotificationCategory } from '@/lib/notifications'

/**
 * Options for the WebSocket event listener
 */
export interface EventToastOptions {
  /** Enable toast notifications for leak events */
  showLeakEvents?: boolean
  /** Enable toast notifications for sensor events */
  showSensorEvents?: boolean
  /** Enable toast notifications for work order events */
  showWorkOrderEvents?: boolean
  /** Enable toast notifications for alert events */
  showAlertEvents?: boolean
  /** Enable toast notifications for all event types */
  showAllEvents?: boolean
  /** Custom event handler */
  onEvent?: (event: TenantEvent) => void
}

const DEFAULT_OPTIONS: EventToastOptions = {
  showLeakEvents: true,
  showSensorEvents: true,
  showWorkOrderEvents: true,
  showAlertEvents: true,
  showAllEvents: false,
}

/**
 * Maps WebSocket events to notification properties
 */
function mapEventToNotification(event: TenantEvent): {
  type: NotificationType
  priority: NotificationPriority
  title: string
  message: string
  category: NotificationCategory
  actionUrl?: string
} | null {
  const payload = event.payload as Record<string, unknown>

  switch (event.event_type) {
    // Leak Events
    case 'leak.detected':
      return {
        type: 'alert',
        priority: (payload.priority as string) === 'high' ? 'high' : 'medium',
        title: '🚨 Leak Detected',
        message: `Potential leak detected at ${payload.location || 'unknown location'}. Estimated loss: ${payload.estimated_loss_m3_per_day || 'unknown'} m³/day. Confidence: ${Math.round((payload.confidence as number) * 100) || 'unknown'}%.`,
        category: 'leak',
        actionUrl: `/leaks/${payload.leak_id}`,
      }

    case 'leak.updated':
      return {
        type: 'info',
        priority: 'low',
        title: '📝 Leak Status Updated',
        message: `Leak ${payload.leak_id} status changed to ${payload.new_status}${payload.updated_by ? ` by ${payload.updated_by}` : ''}.`,
        category: 'leak',
        actionUrl: `/leaks/${payload.leak_id}`,
      }

    case 'leak.confirmed':
      return {
        type: 'warning',
        priority: 'high',
        title: '✅ Leak Confirmed',
        message: `Leak ${payload.leak_id} has been confirmed. Dispatch repair team.`,
        category: 'leak',
        actionUrl: `/leaks/${payload.leak_id}`,
      }

    case 'leak.resolved':
      return {
        type: 'success',
        priority: 'medium',
        title: '🔧 Leak Resolved',
        message: `Leak ${payload.leak_id} has been repaired successfully${payload.water_saved_m3 ? `. Water saved: ${payload.water_saved_m3} m³` : ''}.`,
        category: 'leak',
        actionUrl: `/leaks/${payload.leak_id}`,
      }

    // Sensor Events
    case 'sensor.offline':
      return {
        type: 'warning',
        priority: 'high',
        title: '⚠️ Sensor Offline',
        message: `Sensor ${payload.sensor_id} (${payload.sensor_type}) in DMA ${payload.dma_id} went offline. Last seen: ${payload.last_seen}.`,
        category: 'system',
        actionUrl: `/sensors/${payload.sensor_id}`,
      }

    case 'sensor.online':
      return {
        type: 'success',
        priority: 'low',
        title: '✅ Sensor Online',
        message: `Sensor ${payload.sensor_id} (${payload.sensor_type}) in DMA ${payload.dma_id} is back online.`,
        category: 'system',
        actionUrl: `/sensors/${payload.sensor_id}`,
      }

    case 'sensor.anomaly':
      return {
        type: 'warning',
        priority: 'medium',
        title: '🔍 Sensor Anomaly',
        message: `Anomaly detected on sensor ${payload.sensor_id}: ${payload.description || 'Unusual reading detected'}.`,
        category: 'system',
        actionUrl: `/sensors/${payload.sensor_id}`,
      }

    // Work Order Events
    case 'work_order.created':
      return {
        type: 'info',
        priority: (payload.priority as string) === 'high' ? 'high' : 'medium',
        title: '📋 Work Order Created',
        message: `New work order: ${payload.title}${payload.assigned_to ? ` (Assigned to ${payload.assigned_to})` : ''}.`,
        category: 'field',
        actionUrl: `/work-orders/${payload.work_order_id}`,
      }

    case 'work_order.assigned':
      return {
        type: 'info',
        priority: 'medium',
        title: '👤 Work Order Assigned',
        message: `Work order ${payload.work_order_id} assigned to ${payload.assigned_to}.`,
        category: 'field',
        actionUrl: `/work-orders/${payload.work_order_id}`,
      }

    case 'work_order.completed':
      return {
        type: 'success',
        priority: 'medium',
        title: '✅ Work Order Completed',
        message: `Work order ${payload.work_order_id} has been completed${payload.completed_by ? ` by ${payload.completed_by}` : ''}.`,
        category: 'field',
        actionUrl: `/work-orders/${payload.work_order_id}`,
      }

    // Alert Events
    case 'alert.critical':
      return {
        type: 'alert',
        priority: 'high',
        title: `🚨 ${payload.title || 'Critical Alert'}`,
        message: (payload.message as string) || 'A critical alert requires your immediate attention.',
        category: (payload.category as NotificationCategory) || 'system',
        actionUrl: `/alerts/${payload.alert_id}`,
      }

    case 'alert.warning':
      return {
        type: 'warning',
        priority: 'medium',
        title: `⚠️ ${payload.title || 'Warning'}`,
        message: (payload.message as string) || 'A warning has been issued.',
        category: (payload.category as NotificationCategory) || 'system',
        actionUrl: `/alerts/${payload.alert_id}`,
      }

    case 'alert.resolved':
      return {
        type: 'success',
        priority: 'low',
        title: `✅ Alert Resolved`,
        message: `Alert ${payload.alert_id} has been resolved.`,
        category: 'system',
        actionUrl: `/alerts/${payload.alert_id}`,
      }

    // System Events
    case 'system.maintenance':
      return {
        type: 'info',
        priority: 'medium',
        title: '🔧 System Maintenance',
        message: (payload.message as string) || 'System maintenance scheduled.',
        category: 'system',
      }

    case 'system.update':
      return {
        type: 'info',
        priority: 'low',
        title: '📢 System Update',
        message: (payload.message as string) || 'A system update is available.',
        category: 'system',
      }

    default:
      return null
  }
}

/**
 * Hook that bridges WebSocket events to the notification system.
 * 
 * This hook:
 * 1. Connects to the WebSocket for real-time events
 * 2. Converts events to notifications with appropriate types/priorities
 * 3. Plays alert sounds based on event severity
 * 
 * @example
 * ```tsx
 * function App() {
 *   useEventToasts({
 *     showLeakEvents: true,
 *     showSensorEvents: true,
 *   })
 *   return <Dashboard />
 * }
 * ```
 */
export function useEventToasts(options: EventToastOptions = {}) {
  const opts = { ...DEFAULT_OPTIONS, ...options }
  const { addNotification, playAlertSound } = useNotifications()
  const processedEventsRef = useRef<Set<string>>(new Set())

  // Handle incoming events
  const handleEvent = useCallback((event: TenantEvent) => {
    // Skip connection events
    if (event.event_type.startsWith('connection.')) {
      return
    }

    // Deduplicate events
    if (processedEventsRef.current.has(event.event_id)) {
      return
    }
    processedEventsRef.current.add(event.event_id)

    // Limit deduplication set size
    if (processedEventsRef.current.size > 1000) {
      const arr = Array.from(processedEventsRef.current)
      processedEventsRef.current = new Set(arr.slice(-500))
    }

    // Check if this event type should be shown
    const eventCategory = event.event_type.split('.')[0]
    const shouldShow =
      opts.showAllEvents ||
      (eventCategory === 'leak' && opts.showLeakEvents) ||
      (eventCategory === 'sensor' && opts.showSensorEvents) ||
      (eventCategory === 'work_order' && opts.showWorkOrderEvents) ||
      (eventCategory === 'alert' && opts.showAlertEvents)

    if (!shouldShow) {
      // Still call custom handler even if not showing toast
      opts.onEvent?.(event)
      return
    }

    // Map event to notification
    const notification = mapEventToNotification(event)
    
    if (notification) {
      // Add notification
      addNotification({
        type: notification.type,
        priority: notification.priority,
        title: notification.title,
        message: notification.message,
        source: event.source,
        actionUrl: notification.actionUrl,
        category: notification.category,
      })
    }

    // Call custom handler
    opts.onEvent?.(event)
  }, [addNotification, opts])

  // Connect to WebSocket
  const { status, events, error, reconnectAttempts } = useTenantEvents({
    onEvent: handleEvent,
    autoReconnect: true,
    maxReconnectAttempts: 10,
  })

  // Log connection status changes
  useEffect(() => {
    if (status === 'connected') {
      console.log('Real-time events connected')
    } else if (status === 'error' && error) {
      console.error('Real-time events error:', error.message)
    } else if (status === 'disconnected' && reconnectAttempts > 0) {
      console.log(`Real-time events reconnecting (attempt ${reconnectAttempts})...`)
    }
  }, [status, error, reconnectAttempts])

  return {
    status,
    error,
    reconnectAttempts,
    recentEvents: events,
  }
}

/**
 * Provider component that enables real-time event toasts throughout the app.
 * 
 * @example
 * ```tsx
 * // In your app layout
 * function RootLayout({ children }) {
 *   return (
 *     <NotificationProvider>
 *       <EventToastProvider>
 *         {children}
 *       </EventToastProvider>
 *     </NotificationProvider>
 *   )
 * }
 * ```
 */
export function EventToastProvider({
  children,
  options = {},
}: {
  children: React.ReactNode
  options?: EventToastOptions
}) {
  useEventToasts(options)
  return <>{children}</>
}

export default useEventToasts
