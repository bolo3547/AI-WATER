// Re-export utilities from lib/api
export {
  formatTimestamp,
  formatRelativeTime,
  formatNumber,
  formatCurrency
} from '@/lib/api'

// Additional utility functions
export function cn(...classes: (string | undefined | null | false)[]): string {
  return classes.filter(Boolean).join(' ')
}

export function getStatusColor(status: string): string {
  switch (status) {
    case 'critical':
    case 'offline':
      return 'bg-red-500'
    case 'warning':
    case 'degraded':
      return 'bg-amber-500'
    case 'healthy':
    case 'online':
    case 'operational':
      return 'bg-emerald-500'
    default:
      return 'bg-slate-400'
  }
}

export function getPriorityColor(priority: string): string {
  switch (priority) {
    case 'high':
      return 'text-red-600 bg-red-100'
    case 'medium':
      return 'text-amber-600 bg-amber-100'
    case 'low':
      return 'text-blue-600 bg-blue-100'
    default:
      return 'text-slate-600 bg-slate-100'
  }
}

export function getTrendIcon(trend: 'up' | 'down' | 'stable'): string {
  switch (trend) {
    case 'up':
      return '↑'
    case 'down':
      return '↓'
    case 'stable':
    default:
      return '→'
  }
}
