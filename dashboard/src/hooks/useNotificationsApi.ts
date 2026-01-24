'use client'

import { useState, useCallback, useEffect, useRef } from 'react'
import { useAuth } from '@/lib/auth'
import { useTenantEvents, TenantEvent, WebSocketEventType } from './useTenantEvents'

// =============================================================================
// TYPES
// =============================================================================

export type NotificationSeverity = 'critical' | 'warning' | 'info' | 'success'
export type NotificationStatus = 'pending' | 'sent' | 'delivered' | 'failed' | 'read'
export type NotificationChannel = 'in_app' | 'email' | 'sms' | 'whatsapp' | 'push' | 'webhook'

export interface ApiNotification {
  id: string
  user_id?: string
  title: string
  message: string
  severity: NotificationSeverity
  channel: NotificationChannel
  status: NotificationStatus
  read: boolean
  action_url?: string
  metadata?: Record<string, unknown>
  created_at: string
  read_at?: string
}

export interface NotificationRule {
  id: string
  tenant_id: string
  name: string
  description?: string
  event_type: string
  severity: NotificationSeverity
  target_roles: string[]
  channels: NotificationChannel[]
  escalation?: {
    enabled: boolean
    levels: EscalationLevel[]
  }
  conditions?: Record<string, unknown>
  cooldown_minutes: number
  active: boolean
  created_at: string
  updated_at?: string
}

export interface EscalationLevel {
  delay_minutes: number
  target_roles: string[]
  channels: NotificationChannel[]
  message_suffix?: string
}

export interface EscalationTracker {
  id: string
  tenant_id: string
  alert_id: string
  rule_id?: string
  current_level: number
  max_level: number
  acknowledged: boolean
  acknowledged_by?: string
  acknowledged_at?: string
  resolved: boolean
  resolved_at?: string
  next_escalation_at?: string
  created_at: string
}

export interface UnreadCountResponse {
  unread_count: number
  tenant_id: string
}

export interface NotificationListResponse {
  notifications: ApiNotification[]
  total: number
  unread_count: number
  page: number
  page_size: number
  has_more: boolean
}

export interface SendNotificationRequest {
  title: string
  message: string
  severity: NotificationSeverity
  channels: NotificationChannel[]
  user_ids?: string[]
  target_roles?: string[]
  action_url?: string
  metadata?: Record<string, unknown>
}

export interface UseNotificationsApiOptions {
  /** Tenant ID (uses auth context if not provided) */
  tenantId?: string
  /** Auto-fetch notifications on mount */
  autoFetch?: boolean
  /** Enable real-time WebSocket updates */
  enableRealtime?: boolean
  /** Polling interval in ms (0 = disabled) */
  pollingInterval?: number
  /** Page size for pagination */
  pageSize?: number
}

export interface UseNotificationsApiReturn {
  // State
  notifications: ApiNotification[]
  unreadCount: number
  loading: boolean
  error: Error | null
  hasMore: boolean
  total: number
  page: number
  
  // Actions
  fetchNotifications: (options?: { page?: number; unreadOnly?: boolean }) => Promise<void>
  fetchUnreadCount: () => Promise<number>
  markAsRead: (notificationId: string) => Promise<void>
  markAllAsRead: () => Promise<void>
  sendNotification: (request: SendNotificationRequest) => Promise<ApiNotification[]>
  refreshNotifications: () => Promise<void>
  loadMore: () => Promise<void>
  
  // Rules management
  rules: NotificationRule[]
  fetchRules: () => Promise<void>
  createRule: (rule: Omit<NotificationRule, 'id' | 'tenant_id' | 'created_at'>) => Promise<NotificationRule>
  deleteRule: (ruleId: string) => Promise<void>
  
  // Escalation tracking
  escalations: EscalationTracker[]
  fetchEscalations: () => Promise<void>
  acknowledgeEscalation: (escalationId: string) => Promise<void>
  resolveEscalation: (escalationId: string) => Promise<void>
  
  // Real-time status
  realtimeConnected: boolean
}

// =============================================================================
// CONSTANTS
// =============================================================================

const DEFAULT_OPTIONS: Required<UseNotificationsApiOptions> = {
  tenantId: '',
  autoFetch: true,
  enableRealtime: true,
  pollingInterval: 0, // Disabled by default when realtime is enabled
  pageSize: 20,
}

// API base URL
const getApiBaseUrl = () => {
  if (typeof window === 'undefined') return ''
  return process.env.NEXT_PUBLIC_API_URL || ''
}

// =============================================================================
// HOOK
// =============================================================================

/**
 * React hook for managing notifications via the AquaWatch API.
 * 
 * Features:
 * - Fetch notifications with pagination
 * - Mark notifications as read
 * - Send new notifications
 * - Real-time updates via WebSocket
 * - Notification rules management
 * - Escalation tracking
 * 
 * @example
 * ```tsx
 * function NotificationCenter() {
 *   const { 
 *     notifications, 
 *     unreadCount, 
 *     markAsRead, 
 *     markAllAsRead 
 *   } = useNotificationsApi()
 * 
 *   return (
 *     <div>
 *       <Badge count={unreadCount} />
 *       {notifications.map(n => (
 *         <NotificationItem 
 *           key={n.id} 
 *           notification={n} 
 *           onRead={() => markAsRead(n.id)}
 *         />
 *       ))}
 *     </div>
 *   )
 * }
 * ```
 */
export function useNotificationsApi(
  options: UseNotificationsApiOptions = {}
): UseNotificationsApiReturn {
  const { token, user } = useAuth()
  
  const {
    tenantId: optionsTenantId,
    autoFetch = DEFAULT_OPTIONS.autoFetch,
    enableRealtime = DEFAULT_OPTIONS.enableRealtime,
    pollingInterval = DEFAULT_OPTIONS.pollingInterval,
    pageSize = DEFAULT_OPTIONS.pageSize,
  } = options
  
  // Determine tenant ID from options or default
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const userWithTenant = user as (typeof user & { tenantId?: string }) | null
  const tenantId = optionsTenantId || userWithTenant?.tenantId || 'default-tenant'
  
  // State
  const [notifications, setNotifications] = useState<ApiNotification[]>([])
  const [unreadCount, setUnreadCount] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)
  const [hasMore, setHasMore] = useState(true)
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  
  const [rules, setRules] = useState<NotificationRule[]>([])
  const [escalations, setEscalations] = useState<EscalationTracker[]>([])
  
  // Refs for cleanup
  const pollingRef = useRef<NodeJS.Timeout | null>(null)
  
  // API helpers
  const apiRequest = useCallback(async <T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> => {
    const baseUrl = getApiBaseUrl()
    const url = `${baseUrl}${endpoint}`
    
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {}),
    }
    
    const response = await fetch(url, {
      ...options,
      headers,
    })
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.detail || `API Error: ${response.status}`)
    }
    
    return response.json()
  }, [token])
  
  // =============================================================================
  // NOTIFICATIONS CRUD
  // =============================================================================
  
  const fetchNotifications = useCallback(async (
    fetchOptions: { page?: number; unreadOnly?: boolean } = {}
  ) => {
    const targetPage = fetchOptions.page || 1
    const unreadOnly = fetchOptions.unreadOnly || false
    
    setLoading(true)
    setError(null)
    
    try {
      const params = new URLSearchParams({
        page: targetPage.toString(),
        page_size: pageSize.toString(),
        ...(unreadOnly ? { unread_only: 'true' } : {}),
      })
      
      const data = await apiRequest<NotificationListResponse>(
        `/api/v1/tenants/${tenantId}/notifications?${params}`
      )
      
      if (targetPage === 1) {
        setNotifications(data.notifications)
      } else {
        setNotifications(prev => [...prev, ...data.notifications])
      }
      
      setTotal(data.total)
      setUnreadCount(data.unread_count)
      setHasMore(data.has_more)
      setPage(targetPage)
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to fetch notifications'))
    } finally {
      setLoading(false)
    }
  }, [apiRequest, tenantId, pageSize])
  
  const fetchUnreadCount = useCallback(async (): Promise<number> => {
    try {
      const data = await apiRequest<UnreadCountResponse>(
        `/api/v1/tenants/${tenantId}/notifications/unread-count`
      )
      setUnreadCount(data.unread_count)
      return data.unread_count
    } catch (err) {
      console.error('Failed to fetch unread count:', err)
      return unreadCount
    }
  }, [apiRequest, tenantId, unreadCount])
  
  const markAsRead = useCallback(async (notificationId: string) => {
    try {
      await apiRequest(
        `/api/v1/tenants/${tenantId}/notifications/${notificationId}/read`,
        { method: 'PATCH' }
      )
      
      // Update local state optimistically
      setNotifications(prev =>
        prev.map(n =>
          n.id === notificationId ? { ...n, read: true, status: 'read' as NotificationStatus } : n
        )
      )
      setUnreadCount(prev => Math.max(0, prev - 1))
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to mark as read'))
      throw err
    }
  }, [apiRequest, tenantId])
  
  const markAllAsRead = useCallback(async () => {
    try {
      await apiRequest(
        `/api/v1/tenants/${tenantId}/notifications/mark-all-read`,
        { method: 'POST' }
      )
      
      // Update local state
      setNotifications(prev => prev.map(n => ({ ...n, read: true, status: 'read' as NotificationStatus })))
      setUnreadCount(0)
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to mark all as read'))
      throw err
    }
  }, [apiRequest, tenantId])
  
  const sendNotification = useCallback(async (
    request: SendNotificationRequest
  ): Promise<ApiNotification[]> => {
    try {
      const data = await apiRequest<{ notifications: ApiNotification[] }>(
        `/api/v1/tenants/${tenantId}/notifications`,
        {
          method: 'POST',
          body: JSON.stringify(request),
        }
      )
      return data.notifications
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to send notification'))
      throw err
    }
  }, [apiRequest, tenantId])
  
  const refreshNotifications = useCallback(async () => {
    await fetchNotifications({ page: 1 })
  }, [fetchNotifications])
  
  const loadMore = useCallback(async () => {
    if (!hasMore || loading) return
    await fetchNotifications({ page: page + 1 })
  }, [fetchNotifications, hasMore, loading, page])
  
  // =============================================================================
  // RULES MANAGEMENT
  // =============================================================================
  
  const fetchRules = useCallback(async () => {
    try {
      const data = await apiRequest<{ rules: NotificationRule[] }>(
        `/api/v1/tenants/${tenantId}/notification-rules`
      )
      setRules(data.rules)
    } catch (err) {
      console.error('Failed to fetch rules:', err)
    }
  }, [apiRequest, tenantId])
  
  const createRule = useCallback(async (
    rule: Omit<NotificationRule, 'id' | 'tenant_id' | 'created_at'>
  ): Promise<NotificationRule> => {
    const data = await apiRequest<NotificationRule>(
      `/api/v1/tenants/${tenantId}/notification-rules`,
      {
        method: 'POST',
        body: JSON.stringify(rule),
      }
    )
    setRules(prev => [...prev, data])
    return data
  }, [apiRequest, tenantId])
  
  const deleteRule = useCallback(async (ruleId: string) => {
    await apiRequest(
      `/api/v1/tenants/${tenantId}/notification-rules/${ruleId}`,
      { method: 'DELETE' }
    )
    setRules(prev => prev.filter(r => r.id !== ruleId))
  }, [apiRequest, tenantId])
  
  // =============================================================================
  // ESCALATION TRACKING
  // =============================================================================
  
  const fetchEscalations = useCallback(async () => {
    try {
      const data = await apiRequest<{ escalations: EscalationTracker[] }>(
        `/api/v1/tenants/${tenantId}/escalations`
      )
      setEscalations(data.escalations)
    } catch (err) {
      console.error('Failed to fetch escalations:', err)
    }
  }, [apiRequest, tenantId])
  
  const acknowledgeEscalation = useCallback(async (escalationId: string) => {
    await apiRequest(
      `/api/v1/tenants/${tenantId}/escalations/${escalationId}/acknowledge`,
      { method: 'POST' }
    )
    setEscalations(prev =>
      prev.map(e =>
        e.id === escalationId
          ? { ...e, acknowledged: true, acknowledged_at: new Date().toISOString() }
          : e
      )
    )
  }, [apiRequest, tenantId])
  
  const resolveEscalation = useCallback(async (escalationId: string) => {
    await apiRequest(
      `/api/v1/tenants/${tenantId}/escalations/${escalationId}/resolve`,
      { method: 'POST' }
    )
    setEscalations(prev =>
      prev.map(e =>
        e.id === escalationId
          ? { ...e, resolved: true, resolved_at: new Date().toISOString() }
          : e
      )
    )
  }, [apiRequest, tenantId])
  
  // =============================================================================
  // REAL-TIME UPDATES
  // =============================================================================
  
  // Handle incoming WebSocket events for notifications
  const handleRealtimeEvent = useCallback((event: TenantEvent) => {
    // Handle notification-related events
    const notificationEvents: WebSocketEventType[] = [
      'alert.critical',
      'alert.warning',
      'alert.info',
      'leak.detected',
      'sensor.offline',
      'work_order.created',
    ]
    
    if (notificationEvents.includes(event.event_type)) {
      // Refresh notifications when relevant events occur
      fetchUnreadCount()
      
      // Add to local state if it looks like a notification
      const payload = event.payload as Record<string, unknown>
      if (payload.title && payload.message) {
        const newNotification: ApiNotification = {
          id: event.event_id,
          title: payload.title as string,
          message: payload.message as string,
          severity: mapEventToSeverity(event.event_type),
          channel: 'in_app',
          status: 'delivered',
          read: false,
          action_url: payload.action_url as string | undefined,
          metadata: payload,
          created_at: event.timestamp,
        }
        
        setNotifications(prev => {
          // Avoid duplicates
          if (prev.some(n => n.id === newNotification.id)) {
            return prev
          }
          return [newNotification, ...prev].slice(0, 100)
        })
        
        setUnreadCount(prev => prev + 1)
      }
    }
  }, [fetchUnreadCount])
  
  // Connect to WebSocket for real-time updates
  const { status: wsStatus } = useTenantEvents({
    tenantId,
    eventTypes: enableRealtime ? [
      'alert.critical',
      'alert.warning', 
      'alert.info',
      'alert.resolved',
      'leak.detected',
      'leak.resolved',
      'sensor.offline',
      'sensor.online',
      'work_order.created',
      'work_order.completed',
    ] : [],
    onEvent: handleRealtimeEvent,
  })
  
  const realtimeConnected = wsStatus === 'connected'
  
  // =============================================================================
  // EFFECTS
  // =============================================================================
  
  // Auto-fetch on mount
  useEffect(() => {
    if (autoFetch && token) {
      fetchNotifications()
      fetchRules()
    }
  }, [autoFetch, token, fetchNotifications, fetchRules])
  
  // Polling fallback when realtime is disabled
  useEffect(() => {
    if (pollingInterval > 0 && !enableRealtime && token) {
      pollingRef.current = setInterval(() => {
        fetchUnreadCount()
      }, pollingInterval)
      
      return () => {
        if (pollingRef.current) {
          clearInterval(pollingRef.current)
        }
      }
    }
  }, [pollingInterval, enableRealtime, token, fetchUnreadCount])
  
  return {
    // State
    notifications,
    unreadCount,
    loading,
    error,
    hasMore,
    total,
    page,
    
    // Actions
    fetchNotifications,
    fetchUnreadCount,
    markAsRead,
    markAllAsRead,
    sendNotification,
    refreshNotifications,
    loadMore,
    
    // Rules
    rules,
    fetchRules,
    createRule,
    deleteRule,
    
    // Escalations
    escalations,
    fetchEscalations,
    acknowledgeEscalation,
    resolveEscalation,
    
    // Real-time
    realtimeConnected,
  }
}

// =============================================================================
// HELPERS
// =============================================================================

function mapEventToSeverity(eventType: WebSocketEventType): NotificationSeverity {
  switch (eventType) {
    case 'alert.critical':
    case 'leak.detected':
    case 'sensor.offline':
      return 'critical'
    case 'alert.warning':
      return 'warning'
    case 'alert.info':
    case 'work_order.created':
      return 'info'
    default:
      return 'info'
  }
}

// Export a simpler hook for just unread count (for header/navbar)
export function useUnreadNotificationCount(): {
  count: number
  loading: boolean
  refresh: () => Promise<void>
} {
  const { unreadCount, loading, fetchUnreadCount } = useNotificationsApi({
    autoFetch: true,
    enableRealtime: true,
    pageSize: 1, // We only need count
  })
  
  return {
    count: unreadCount,
    loading,
    refresh: async () => { await fetchUnreadCount() },
  }
}
