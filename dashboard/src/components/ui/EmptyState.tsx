'use client'

import { WifiOff, Database, Inbox, Plus, RefreshCw, AlertCircle, Search, FileQuestion, Settings } from 'lucide-react'
import { ReactNode } from 'react'

interface EmptyStateProps {
  icon?: ReactNode
  title: string
  description: string
  action?: {
    label: string
    onClick: () => void
    icon?: ReactNode
  }
  secondaryAction?: {
    label: string
    onClick: () => void
  }
  variant?: 'default' | 'no-sensors' | 'no-data' | 'error' | 'search'
}

export function EmptyState({ 
  icon, 
  title, 
  description, 
  action, 
  secondaryAction,
  variant = 'default' 
}: EmptyStateProps) {
  const variantStyles = {
    default: {
      container: 'bg-slate-50 border-slate-200',
      icon: 'bg-slate-100 text-slate-400',
      title: 'text-slate-700',
      description: 'text-slate-500'
    },
    'no-sensors': {
      container: 'bg-amber-50 border-amber-200',
      icon: 'bg-amber-100 text-amber-500',
      title: 'text-amber-700',
      description: 'text-amber-600'
    },
    'no-data': {
      container: 'bg-blue-50 border-blue-200',
      icon: 'bg-blue-100 text-blue-500',
      title: 'text-blue-700',
      description: 'text-blue-600'
    },
    error: {
      container: 'bg-red-50 border-red-200',
      icon: 'bg-red-100 text-red-500',
      title: 'text-red-700',
      description: 'text-red-600'
    },
    search: {
      container: 'bg-slate-50 border-slate-200',
      icon: 'bg-slate-100 text-slate-400',
      title: 'text-slate-700',
      description: 'text-slate-500'
    }
  }

  const styles = variantStyles[variant]

  const defaultIcons = {
    default: <Inbox className="w-8 h-8" />,
    'no-sensors': <WifiOff className="w-8 h-8" />,
    'no-data': <Database className="w-8 h-8" />,
    error: <AlertCircle className="w-8 h-8" />,
    search: <Search className="w-8 h-8" />
  }

  const displayIcon = icon || defaultIcons[variant]

  return (
    <div className={`rounded-xl border-2 border-dashed ${styles.container} p-8 text-center`}>
      <div className={`w-16 h-16 rounded-full ${styles.icon} flex items-center justify-center mx-auto mb-4`}>
        {displayIcon}
      </div>
      <h3 className={`text-lg font-semibold ${styles.title} mb-2`}>{title}</h3>
      <p className={`${styles.description} max-w-md mx-auto mb-6`}>{description}</p>
      
      <div className="flex items-center justify-center gap-3">
        {action && (
          <button
            onClick={action.onClick}
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium text-sm"
          >
            {action.icon || <Plus className="w-4 h-4" />}
            {action.label}
          </button>
        )}
        {secondaryAction && (
          <button
            onClick={secondaryAction.onClick}
            className="inline-flex items-center gap-2 px-4 py-2 border border-slate-300 text-slate-700 rounded-lg hover:bg-slate-50 transition-colors font-medium text-sm"
          >
            {secondaryAction.label}
          </button>
        )}
      </div>
    </div>
  )
}

// Pre-built empty states for common scenarios
export function NoSensorsConnected({ onConfigure }: { onConfigure?: () => void }) {
  return (
    <EmptyState
      variant="no-sensors"
      title="No Sensors Connected"
      description="Connect your ESP32 sensors via MQTT to start receiving real-time water flow data and leak detection alerts."
      action={onConfigure ? {
        label: 'Configure Sensors',
        onClick: onConfigure,
        icon: <Settings className="w-4 h-4" />
      } : undefined}
    />
  )
}

export function WaitingForData({ onRefresh }: { onRefresh?: () => void }) {
  return (
    <EmptyState
      variant="no-data"
      title="Waiting for Sensor Data"
      description="Sensors are connected but no readings have been received yet. Data will appear here once sensors start transmitting."
      action={onRefresh ? {
        label: 'Refresh',
        onClick: onRefresh,
        icon: <RefreshCw className="w-4 h-4" />
      } : undefined}
    />
  )
}

export function NoDataAvailable({ 
  title = "No Data Available",
  description = "There's no data to display at the moment.",
  onRefresh 
}: { 
  title?: string
  description?: string
  onRefresh?: () => void 
}) {
  return (
    <EmptyState
      variant="default"
      title={title}
      description={description}
      action={onRefresh ? {
        label: 'Refresh',
        onClick: onRefresh,
        icon: <RefreshCw className="w-4 h-4" />
      } : undefined}
    />
  )
}

export function NoSearchResults({ 
  query, 
  onClearSearch 
}: { 
  query: string
  onClearSearch: () => void 
}) {
  return (
    <EmptyState
      variant="search"
      icon={<FileQuestion className="w-8 h-8" />}
      title="No Results Found"
      description={`No items match "${query}". Try adjusting your search or filters.`}
      action={{
        label: 'Clear Search',
        onClick: onClearSearch,
        icon: <Search className="w-4 h-4" />
      }}
    />
  )
}

export function ErrorState({ 
  error, 
  onRetry 
}: { 
  error: string | Error
  onRetry?: () => void 
}) {
  return (
    <EmptyState
      variant="error"
      title="Something Went Wrong"
      description={typeof error === 'string' ? error : error.message || 'An unexpected error occurred.'}
      action={onRetry ? {
        label: 'Try Again',
        onClick: onRetry,
        icon: <RefreshCw className="w-4 h-4" />
      } : undefined}
    />
  )
}
