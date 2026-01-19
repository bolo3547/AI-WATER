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
