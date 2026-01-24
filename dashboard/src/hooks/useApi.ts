// Re-export all API hooks from lib/api
export {
  useSystemStatus,
  useSystemMetrics,
  useDMAList,
  useDMADetails,
  useDMATimeSeries,
  useLeaks,
  useNRWTrend,
  type SystemStatus,
  type DMAData,
  type LeakData,
  type SystemMetrics,
  type TimeSeriesPoint
} from '@/lib/api'

// Re-export WebSocket hooks for real-time events
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

// Re-export event toast hooks
export {
  useEventToasts,
  EventToastProvider,
  type EventToastOptions,
} from './useEventToasts'
