import useSWR, { mutate as globalMutate } from 'swr'
import { useCallback } from 'react'

// Base fetcher with error handling
const fetcher = async (url: string) => {
  const res = await fetch(url)
  if (!res.ok) {
    const error = new Error('API request failed')
    const data = await res.json().catch(() => ({}))
    ;(error as any).status = res.status
    ;(error as any).info = data
    throw error
  }
  return res.json()
}

// POST/PATCH/DELETE fetcher
const mutationFetcher = async (url: string, method: string, body?: any) => {
  const res = await fetch(url, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined
  })
  if (!res.ok) {
    const error = new Error('API request failed')
    const data = await res.json().catch(() => ({}))
    ;(error as any).status = res.status
    ;(error as any).info = data
    throw error
  }
  return res.json()
}

// ============================================================
// SYSTEM STATUS
// ============================================================
export interface SystemStatus {
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

export function useSystemStatusAPI() {
  return useSWR<SystemStatus>('/api/system/status', fetcher, {
    refreshInterval: 10000,
    revalidateOnFocus: true
  })
}

// ============================================================
// LEAKS
// ============================================================
export interface Leak {
  _id: string
  id?: string
  dma_id: string
  dma_name: string
  type: string
  severity: 'critical' | 'high' | 'medium' | 'low'
  status: 'active' | 'acknowledged' | 'investigating' | 'resolved'
  location: {
    lat: number
    lng: number
    address?: string
  }
  estimated_flow_rate: number
  estimated_loss_daily: number
  detected_at: string
  acknowledged_at?: string
  resolved_at?: string
  assigned_to?: string
  work_order_id?: string
  ai_confidence: number
  ai_explanation?: string
}

export function useLeaksAPI(filters?: { status?: string; dma_id?: string; severity?: string }) {
  const params = new URLSearchParams()
  if (filters?.status) params.set('status', filters.status)
  if (filters?.dma_id) params.set('dma_id', filters.dma_id)
  if (filters?.severity) params.set('severity', filters.severity)
  
  const queryString = params.toString()
  const url = `/api/leaks${queryString ? `?${queryString}` : ''}`
  
  return useSWR<{ leaks: Leak[]; total: number; hasData: boolean }>(url, fetcher, {
    refreshInterval: 30000,
    revalidateOnFocus: true
  })
}

export function useLeakAPI(id: string | null) {
  return useSWR<Leak>(id ? `/api/leaks/${id}` : null, fetcher, {
    revalidateOnFocus: true
  })
}

export function useLeakMutations() {
  const acknowledgeLeak = useCallback(async (id: string) => {
    const result = await mutationFetcher(`/api/leaks/${id}`, 'PATCH', {
      action: 'acknowledge'
    })
    globalMutate((key: string) => typeof key === 'string' && key.startsWith('/api/leaks'))
    return result
  }, [])

  const resolveLeak = useCallback(async (id: string, notes?: string) => {
    const result = await mutationFetcher(`/api/leaks/${id}`, 'PATCH', {
      action: 'resolve',
      notes
    })
    globalMutate((key: string) => typeof key === 'string' && key.startsWith('/api/leaks'))
    return result
  }, [])

  const updateLeakStatus = useCallback(async (id: string, status: string) => {
    const result = await mutationFetcher(`/api/leaks/${id}`, 'PATCH', {
      status
    })
    globalMutate((key: string) => typeof key === 'string' && key.startsWith('/api/leaks'))
    return result
  }, [])

  const createWorkOrderFromLeak = useCallback(async (leakId: string, data: any) => {
    const result = await mutationFetcher('/api/work-orders', 'POST', {
      ...data,
      leak_id: leakId
    })
    globalMutate((key: string) => typeof key === 'string' && (key.startsWith('/api/leaks') || key.startsWith('/api/work-orders')))
    return result
  }, [])

  return { acknowledgeLeak, resolveLeak, updateLeakStatus, createWorkOrderFromLeak }
}

// ============================================================
// WORK ORDERS
// ============================================================
export interface WorkOrder {
  _id: string
  id?: string
  title: string
  description: string
  type: 'leak_repair' | 'pipe_replacement' | 'valve_maintenance' | 'meter_installation' | 'inspection' | 'emergency'
  priority: 'critical' | 'high' | 'medium' | 'low'
  status: 'pending' | 'assigned' | 'in_progress' | 'completed' | 'cancelled'
  location: {
    lat: number
    lng: number
    address: string
  }
  dma_id?: string
  leak_id?: string
  assigned_to?: string
  assigned_crew?: string[]
  estimated_duration_hours: number
  actual_duration_hours?: number
  materials_used?: string[]
  cost_estimate?: number
  actual_cost?: number
  created_at: string
  scheduled_for?: string
  started_at?: string
  completed_at?: string
  notes?: string
  photos?: string[]
}

export interface CreateWorkOrderInput {
  title: string
  description: string
  type: WorkOrder['type']
  priority: WorkOrder['priority']
  location: WorkOrder['location']
  dma_id?: string
  leak_id?: string
  assigned_to?: string
  estimated_duration_hours?: number
  scheduled_for?: string
}

export function useWorkOrdersAPI(filters?: { status?: string; priority?: string; assigned_to?: string }) {
  const params = new URLSearchParams()
  if (filters?.status) params.set('status', filters.status)
  if (filters?.priority) params.set('priority', filters.priority)
  if (filters?.assigned_to) params.set('assigned_to', filters.assigned_to)
  
  const queryString = params.toString()
  const url = `/api/work-orders${queryString ? `?${queryString}` : ''}`
  
  return useSWR<{ workOrders: WorkOrder[]; total: number; hasData: boolean }>(url, fetcher, {
    refreshInterval: 30000,
    revalidateOnFocus: true
  })
}

export function useWorkOrderAPI(id: string | null) {
  return useSWR<WorkOrder>(id ? `/api/work-orders/${id}` : null, fetcher)
}

export function useWorkOrderMutations() {
  const createWorkOrder = useCallback(async (data: CreateWorkOrderInput) => {
    const result = await mutationFetcher('/api/work-orders', 'POST', data)
    globalMutate((key: string) => typeof key === 'string' && key.startsWith('/api/work-orders'))
    return result
  }, [])

  const updateWorkOrder = useCallback(async (id: string, data: Partial<WorkOrder>) => {
    const result = await mutationFetcher(`/api/work-orders/${id}`, 'PATCH', data)
    globalMutate((key: string) => typeof key === 'string' && key.startsWith('/api/work-orders'))
    return result
  }, [])

  const assignWorkOrder = useCallback(async (id: string, assignedTo: string, crew?: string[]) => {
    const result = await mutationFetcher(`/api/work-orders/${id}`, 'PATCH', {
      action: 'assign',
      assigned_to: assignedTo,
      assigned_crew: crew,
      status: 'assigned'
    })
    globalMutate((key: string) => typeof key === 'string' && key.startsWith('/api/work-orders'))
    return result
  }, [])

  const startWorkOrder = useCallback(async (id: string) => {
    const result = await mutationFetcher(`/api/work-orders/${id}`, 'PATCH', {
      action: 'start',
      status: 'in_progress',
      started_at: new Date().toISOString()
    })
    globalMutate((key: string) => typeof key === 'string' && key.startsWith('/api/work-orders'))
    return result
  }, [])

  const completeWorkOrder = useCallback(async (id: string, notes?: string, actualCost?: number) => {
    const result = await mutationFetcher(`/api/work-orders/${id}`, 'PATCH', {
      action: 'complete',
      status: 'completed',
      completed_at: new Date().toISOString(),
      notes,
      actual_cost: actualCost
    })
    globalMutate((key: string) => typeof key === 'string' && key.startsWith('/api/work-orders'))
    return result
  }, [])

  const cancelWorkOrder = useCallback(async (id: string, reason?: string) => {
    const result = await mutationFetcher(`/api/work-orders/${id}`, 'PATCH', {
      action: 'cancel',
      status: 'cancelled',
      notes: reason
    })
    globalMutate((key: string) => typeof key === 'string' && key.startsWith('/api/work-orders'))
    return result
  }, [])

  return { 
    createWorkOrder, 
    updateWorkOrder, 
    assignWorkOrder, 
    startWorkOrder, 
    completeWorkOrder, 
    cancelWorkOrder 
  }
}

// ============================================================
// SENSORS
// ============================================================
export interface Sensor {
  _id: string
  sensor_id: string
  name: string
  type: 'flow' | 'pressure' | 'acoustic' | 'quality'
  dma_id: string
  dma_name?: string
  location: {
    lat: number
    lng: number
    address?: string
  }
  status: 'online' | 'offline' | 'maintenance' | 'error'
  last_seen: string | null
  battery_level?: number
  signal_strength?: number
  firmware_version?: string
  installed_at?: string
  last_reading?: {
    value: number
    unit: string
    timestamp: string
  }
}

export function useSensorsAPI(filters?: { status?: string; dma_id?: string; type?: string }) {
  const params = new URLSearchParams()
  if (filters?.status) params.set('status', filters.status)
  if (filters?.dma_id) params.set('dma_id', filters.dma_id)
  if (filters?.type) params.set('type', filters.type)
  
  const queryString = params.toString()
  const url = `/api/sensors${queryString ? `?${queryString}` : ''}`
  
  return useSWR<{ sensors: Sensor[]; total: number; online: number; offline: number; hasData: boolean }>(
    url, 
    fetcher, 
    { refreshInterval: 15000, revalidateOnFocus: true }
  )
}

// ============================================================
// DMAs
// ============================================================
export interface DMA {
  _id: string
  dma_id: string
  name: string
  zone: string
  area_km2: number
  population: number
  connections: number
  meters_count: number
  nrw_percentage: number
  daily_input: number
  daily_consumption: number
  daily_loss: number
  active_leaks: number
  sensors: number
  status: 'normal' | 'warning' | 'critical'
  boundary?: GeoJSON.Polygon
  center?: { lat: number; lng: number }
}

export function useDMAsAPI() {
  return useSWR<{ dmas: DMA[]; total: number; hasData: boolean }>('/api/dmas', fetcher, {
    refreshInterval: 60000,
    revalidateOnFocus: true
  })
}

export function useDMAAPI(id: string | null) {
  return useSWR<DMA>(id ? `/api/dmas/${id}` : null, fetcher)
}

// ============================================================
// METRICS
// ============================================================
export interface Metrics {
  nrw_percentage: number
  total_daily_loss_m3: number
  total_daily_input_m3: number
  active_leaks: number
  resolved_leaks_today: number
  sensors_online: number
  sensors_total: number
  critical_alerts: number
  data_available: boolean
  last_updated: string
}

export function useMetricsAPI() {
  return useSWR<Metrics>('/api/metrics', fetcher, {
    refreshInterval: 30000,
    revalidateOnFocus: true
  })
}

// ============================================================
// TECHNICIANS / USERS
// ============================================================
export interface Technician {
  _id: string
  user_id: string
  name: string
  email: string
  phone: string
  role: string
  status: 'available' | 'busy' | 'offline'
  skills: string[]
  current_work_order?: string
  completed_today: number
  location?: { lat: number; lng: number }
}

export function useTechniciansAPI() {
  return useSWR<{ technicians: Technician[]; total: number; hasData: boolean }>('/api/technicians', fetcher, {
    refreshInterval: 60000
  })
}

// ============================================================
// NOTIFICATIONS
// ============================================================
export interface Notification {
  _id: string
  type: 'leak_detected' | 'work_order_assigned' | 'sensor_offline' | 'system_alert' | 'info'
  title: string
  message: string
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info'
  read: boolean
  created_at: string
  link?: string
  metadata?: Record<string, any>
}

export function useNotificationsAPI(unreadOnly = false) {
  const url = `/api/notifications${unreadOnly ? '?unread=true' : ''}`
  return useSWR<{ notifications: Notification[]; unreadCount: number; hasData: boolean }>(url, fetcher, {
    refreshInterval: 15000,
    revalidateOnFocus: true
  })
}

export function useNotificationMutations() {
  const markAsRead = useCallback(async (id: string) => {
    const result = await mutationFetcher(`/api/notifications/${id}`, 'PATCH', { read: true })
    globalMutate((key: string) => typeof key === 'string' && key.startsWith('/api/notifications'))
    return result
  }, [])

  const markAllAsRead = useCallback(async () => {
    const result = await mutationFetcher('/api/notifications/mark-all-read', 'POST', {})
    globalMutate((key: string) => typeof key === 'string' && key.startsWith('/api/notifications'))
    return result
  }, [])

  const deleteNotification = useCallback(async (id: string) => {
    const result = await mutationFetcher(`/api/notifications/${id}`, 'DELETE', {})
    globalMutate((key: string) => typeof key === 'string' && key.startsWith('/api/notifications'))
    return result
  }, [])

  return { markAsRead, markAllAsRead, deleteNotification }
}

// ============================================================
// Re-exports for compatibility
// ============================================================
export {
  useTenantEvents,
  isLeakDetectedEvent,
  isSensorOfflineEvent,
  isWorkOrderCreatedEvent,
  isAlertCriticalEvent,
  type TenantEvent,
  type WebSocketEventType,
  type ConnectionStatus,
  type UseTenantEventsOptions,
  type UseTenantEventsReturn,
  type LeakDetectedPayload,
  type LeakUpdatedPayload,
  type WorkOrderCreatedPayload,
  type SensorOfflinePayload,
  type AlertCriticalPayload,
} from './useTenantEvents'

export {
  useEventToasts,
  EventToastProvider,
  type EventToastOptions,
} from './useEventToasts'

// ============================================================
// HELPER: Revalidate all data
// ============================================================
export function revalidateAll() {
  globalMutate((key: string) => typeof key === 'string' && key.startsWith('/api/'))
}
