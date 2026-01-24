'use client'

import { useEffect, useRef, useCallback, useState } from 'react'
import { useAuth } from '@/lib/auth'

// =============================================================================
// TYPES
// =============================================================================

export type WebSocketEventType =
  // Leak events
  | 'leak.detected'
  | 'leak.updated'
  | 'leak.confirmed'
  | 'leak.resolved'
  // Work order events
  | 'work_order.created'
  | 'work_order.updated'
  | 'work_order.assigned'
  | 'work_order.completed'
  // Sensor events
  | 'sensor.offline'
  | 'sensor.online'
  | 'sensor.anomaly'
  // Alert events
  | 'alert.critical'
  | 'alert.warning'
  | 'alert.info'
  | 'alert.resolved'
  // System events
  | 'system.maintenance'
  | 'system.update'
  // Connection events
  | 'connection.established'
  | 'connection.heartbeat'
  | 'connection.error'
  | 'connection.subscription_updated'

// Base payload type that allows any properties
export type EventPayload = Record<string, unknown>

export interface TenantEvent<T extends EventPayload = EventPayload> {
  event_id: string
  event_type: WebSocketEventType
  tenant_id: string
  payload: T
  timestamp: string
  source: string
}

// Specific event payload types (extend EventPayload)
export interface LeakDetectedPayload extends EventPayload {
  leak_id: string
  dma_id: string
  location: string
  estimated_loss_m3_per_day: number
  confidence: number
  priority: 'high' | 'medium' | 'low'
  detection_method: string
  requires_immediate_attention: boolean
}

export interface LeakUpdatedPayload extends EventPayload {
  leak_id: string
  new_status: string
  updated_by: string
  changes: Record<string, unknown>
}

export interface WorkOrderCreatedPayload extends EventPayload {
  work_order_id: string
  leak_id?: string
  title: string
  priority: string
  assigned_to?: string
}

export interface SensorOfflinePayload extends EventPayload {
  sensor_id: string
  sensor_type: string
  dma_id: string
  last_seen: string
  reason?: string
  alert_level: string
}

export interface AlertCriticalPayload extends EventPayload {
  alert_id: string
  title: string
  message: string
  category: string
  action_required: boolean
  severity: string
}

export type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'error'

export interface UseTenantEventsOptions {
  /** Tenant ID to connect to */
  tenantId?: string
  /** Event types to subscribe to (empty = all) */
  eventTypes?: WebSocketEventType[]
  /** ISO timestamp to replay events from on connect */
  replaySince?: string
  /** Enable auto-reconnect (default: true) */
  autoReconnect?: boolean
  /** Reconnect delay in ms (default: 3000) */
  reconnectDelay?: number
  /** Max reconnect attempts (default: 10) */
  maxReconnectAttempts?: number
  /** Heartbeat interval in ms (default: 30000) */
  heartbeatInterval?: number
  /** Called when an event is received */
  onEvent?: (event: TenantEvent) => void
  /** Called when connection status changes */
  onStatusChange?: (status: ConnectionStatus) => void
  /** Called on connection error */
  onError?: (error: Error) => void
}

export interface UseTenantEventsReturn {
  /** Current connection status */
  status: ConnectionStatus
  /** Recent events (limited buffer) */
  events: TenantEvent[]
  /** Clear event buffer */
  clearEvents: () => void
  /** Manually disconnect */
  disconnect: () => void
  /** Manually reconnect */
  reconnect: () => void
  /** Send a message to the server */
  send: (message: Record<string, unknown>) => void
  /** Update subscription */
  subscribe: (eventTypes: WebSocketEventType[]) => void
  /** Remove subscription */
  unsubscribe: (eventTypes: WebSocketEventType[]) => void
  /** Last error if any */
  error: Error | null
  /** Reconnect attempt count */
  reconnectAttempts: number
}

// =============================================================================
// CONSTANTS
// =============================================================================

const DEFAULT_OPTIONS: Required<Omit<UseTenantEventsOptions, 'tenantId' | 'eventTypes' | 'replaySince' | 'onEvent' | 'onStatusChange' | 'onError'>> = {
  autoReconnect: true,
  reconnectDelay: 3000,
  maxReconnectAttempts: 10,
  heartbeatInterval: 30000,
}

const MAX_EVENT_BUFFER = 100

// =============================================================================
// HOOK
// =============================================================================

/**
 * React hook for connecting to AquaWatch real-time events via WebSocket.
 * 
 * Features:
 * - Automatic JWT authentication
 * - Auto-reconnect with exponential backoff
 * - Heartbeat keepalive
 * - Event buffering
 * - Subscription management
 * 
 * @example
 * ```tsx
 * function Dashboard() {
 *   const { status, events } = useTenantEvents({
 *     eventTypes: ['leak.detected', 'sensor.offline'],
 *     onEvent: (event) => {
 *       if (event.event_type === 'leak.detected') {
 *         toast.error(`Leak detected: ${event.payload.location}`)
 *       }
 *     }
 *   })
 * 
 *   return <div>Connection: {status}</div>
 * }
 * ```
 */
export function useTenantEvents(options: UseTenantEventsOptions = {}): UseTenantEventsReturn {
  const { token } = useAuth()
  
  const {
    tenantId,
    eventTypes,
    replaySince,
    autoReconnect = DEFAULT_OPTIONS.autoReconnect,
    reconnectDelay = DEFAULT_OPTIONS.reconnectDelay,
    maxReconnectAttempts = DEFAULT_OPTIONS.maxReconnectAttempts,
    heartbeatInterval = DEFAULT_OPTIONS.heartbeatInterval,
    onEvent,
    onStatusChange,
    onError,
  } = options

  // State
  const [status, setStatus] = useState<ConnectionStatus>('disconnected')
  const [events, setEvents] = useState<TenantEvent[]>([])
  const [error, setError] = useState<Error | null>(null)
  const [reconnectAttempts, setReconnectAttempts] = useState(0)

  // Refs
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const heartbeatIntervalRef = useRef<NodeJS.Timeout | null>(null)
  const isUnmountedRef = useRef(false)

  // Get tenant ID from token if not provided
  const effectiveTenantId = tenantId || getDefaultTenantId()

  // Update status with callback
  const updateStatus = useCallback((newStatus: ConnectionStatus) => {
    if (isUnmountedRef.current) return
    setStatus(newStatus)
    onStatusChange?.(newStatus)
  }, [onStatusChange])

  // Add event to buffer
  const addEvent = useCallback((event: TenantEvent) => {
    if (isUnmountedRef.current) return
    setEvents(prev => {
      const updated = [event, ...prev]
      return updated.slice(0, MAX_EVENT_BUFFER)
    })
    onEvent?.(event)
  }, [onEvent])

  // Clear events
  const clearEvents = useCallback(() => {
    setEvents([])
  }, [])

  // Send message
  const send = useCallback((message: Record<string, unknown>) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message))
    }
  }, [])

  // Subscribe to event types
  const subscribe = useCallback((newEventTypes: WebSocketEventType[]) => {
    send({ type: 'subscribe', event_types: newEventTypes })
  }, [send])

  // Unsubscribe from event types
  const unsubscribe = useCallback((removeEventTypes: WebSocketEventType[]) => {
    send({ type: 'unsubscribe', event_types: removeEventTypes })
  }, [send])

  // Connect to WebSocket
  const connect = useCallback(() => {
    if (!token || !effectiveTenantId) {
      console.warn('useTenantEvents: No token or tenant ID available')
      return
    }

    // Clean up existing connection
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }

    updateStatus('connecting')

    // Build WebSocket URL
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    
    const params = new URLSearchParams()
    params.append('token', token)
    
    if (eventTypes && eventTypes.length > 0) {
      params.append('event_types', eventTypes.join(','))
    }
    
    if (replaySince) {
      params.append('replay_since', replaySince)
    }

    const wsUrl = `${protocol}//${host}/ws/tenants/${effectiveTenantId}/events?${params.toString()}`

    try {
      const ws = new WebSocket(wsUrl)
      wsRef.current = ws

      ws.onopen = () => {
        if (isUnmountedRef.current) return
        console.log('WebSocket connected to tenant:', effectiveTenantId)
        updateStatus('connected')
        setError(null)
        setReconnectAttempts(0)

        // Start heartbeat
        heartbeatIntervalRef.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'heartbeat' }))
          }
        }, heartbeatInterval)
      }

      ws.onmessage = (messageEvent) => {
        if (isUnmountedRef.current) return
        
        try {
          const event = JSON.parse(messageEvent.data) as TenantEvent
          
          // Skip heartbeat responses in event buffer
          if (event.event_type !== 'connection.heartbeat') {
            addEvent(event)
          }
        } catch (e) {
          console.warn('Failed to parse WebSocket message:', e)
        }
      }

      ws.onerror = (errorEvent) => {
        if (isUnmountedRef.current) return
        console.error('WebSocket error:', errorEvent)
        const err = new Error('WebSocket connection error')
        setError(err)
        onError?.(err)
        updateStatus('error')
      }

      ws.onclose = (closeEvent) => {
        if (isUnmountedRef.current) return
        console.log('WebSocket closed:', closeEvent.code, closeEvent.reason)
        
        // Clear heartbeat
        if (heartbeatIntervalRef.current) {
          clearInterval(heartbeatIntervalRef.current)
          heartbeatIntervalRef.current = null
        }

        // Handle auth failure
        if (closeEvent.code === 4001) {
          setError(new Error('Authentication failed'))
          updateStatus('error')
          return
        }

        updateStatus('disconnected')

        // Auto-reconnect
        if (autoReconnect && reconnectAttempts < maxReconnectAttempts) {
          const delay = reconnectDelay * Math.pow(1.5, reconnectAttempts)
          console.log(`Reconnecting in ${delay}ms (attempt ${reconnectAttempts + 1}/${maxReconnectAttempts})`)
          
          reconnectTimeoutRef.current = setTimeout(() => {
            setReconnectAttempts(prev => prev + 1)
            connect()
          }, delay)
        } else if (reconnectAttempts >= maxReconnectAttempts) {
          setError(new Error('Max reconnection attempts reached'))
          updateStatus('error')
        }
      }
    } catch (e) {
      console.error('Failed to create WebSocket:', e)
      const err = e instanceof Error ? e : new Error('Failed to create WebSocket')
      setError(err)
      onError?.(err)
      updateStatus('error')
    }
  }, [
    token,
    effectiveTenantId,
    eventTypes,
    replaySince,
    autoReconnect,
    reconnectDelay,
    maxReconnectAttempts,
    heartbeatInterval,
    reconnectAttempts,
    updateStatus,
    addEvent,
    onError,
  ])

  // Disconnect
  const disconnect = useCallback(() => {
    // Clear reconnect timeout
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }

    // Clear heartbeat
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current)
      heartbeatIntervalRef.current = null
    }

    // Close WebSocket
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }

    setReconnectAttempts(0)
    updateStatus('disconnected')
  }, [updateStatus])

  // Reconnect
  const reconnect = useCallback(() => {
    setReconnectAttempts(0)
    disconnect()
    connect()
  }, [disconnect, connect])

  // Effect: Connect on mount / token change
  useEffect(() => {
    isUnmountedRef.current = false

    if (token && effectiveTenantId) {
      connect()
    }

    return () => {
      isUnmountedRef.current = true
      disconnect()
    }
  }, [token, effectiveTenantId])  // Intentionally not including connect/disconnect to avoid loops

  return {
    status,
    events,
    clearEvents,
    disconnect,
    reconnect,
    send,
    subscribe,
    unsubscribe,
    error,
    reconnectAttempts,
  }
}

// =============================================================================
// HELPERS
// =============================================================================

/**
 * Get default tenant ID from localStorage token
 */
function getDefaultTenantId(): string | undefined {
  if (typeof window === 'undefined') return undefined
  
  const token = localStorage.getItem('access_token')
  if (!token) return undefined
  
  try {
    // Decode JWT payload (middle part)
    const parts = token.split('.')
    if (parts.length !== 3) return undefined
    
    const payload = JSON.parse(atob(parts[1]))
    return payload.tenant_id
  } catch {
    return undefined
  }
}

/**
 * Type guard for leak detected events
 */
export function isLeakDetectedEvent(event: TenantEvent): event is TenantEvent<LeakDetectedPayload> {
  return event.event_type === 'leak.detected'
}

/**
 * Type guard for sensor offline events
 */
export function isSensorOfflineEvent(event: TenantEvent): event is TenantEvent<SensorOfflinePayload> {
  return event.event_type === 'sensor.offline'
}

/**
 * Type guard for work order created events
 */
export function isWorkOrderCreatedEvent(event: TenantEvent): event is TenantEvent<WorkOrderCreatedPayload> {
  return event.event_type === 'work_order.created'
}

/**
 * Type guard for critical alert events
 */
export function isAlertCriticalEvent(event: TenantEvent): event is TenantEvent<AlertCriticalPayload> {
  return event.event_type === 'alert.critical'
}

export default useTenantEvents
