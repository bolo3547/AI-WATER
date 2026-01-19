import { clsx } from 'clsx'
import { Circle } from 'lucide-react'

type Status = 'healthy' | 'warning' | 'critical' | 'info'

interface StatusBadgeProps {
  status: Status
  label?: string
  showDot?: boolean
  size?: 'sm' | 'md'
}

export function StatusBadge({ 
  status, 
  label, 
  showDot = true,
  size = 'md' 
}: StatusBadgeProps) {
  const getStatusClass = () => {
    switch (status) {
      case 'healthy': return 'status-healthy'
      case 'warning': return 'status-warning'
      case 'critical': return 'status-critical'
      case 'info': return 'bg-blue-50 text-blue-700 border border-blue-200'
    }
  }
  
  const getDefaultLabel = () => {
    switch (status) {
      case 'healthy': return 'Healthy'
      case 'warning': return 'Warning'
      case 'critical': return 'Critical'
      case 'info': return 'Info'
    }
  }
  
  const getDotColor = () => {
    switch (status) {
      case 'healthy': return 'text-emerald-500'
      case 'warning': return 'text-amber-500'
      case 'critical': return 'text-red-500'
      case 'info': return 'text-blue-500'
    }
  }
  
  return (
    <span className={clsx(
      'status-badge',
      getStatusClass(),
      size === 'sm' && 'text-[0.6875rem] px-2 py-0.5'
    )}>
      {showDot && (
        <Circle className={clsx('w-2 h-2 fill-current', getDotColor())} />
      )}
      {label || getDefaultLabel()}
    </span>
  )
}

interface ConfidenceIndicatorProps {
  value: number // 0-100
  showLabel?: boolean
}

export function ConfidenceIndicator({ value, showLabel = true }: ConfidenceIndicatorProps) {
  const getColor = () => {
    if (value >= 80) return 'bg-status-healthy'
    if (value >= 60) return 'bg-status-info'
    if (value >= 40) return 'bg-status-warning'
    return 'bg-status-critical'
  }
  
  return (
    <div className="flex items-center gap-2">
      <div className="confidence-bar w-16">
        <div 
          className={clsx('confidence-fill', getColor())}
          style={{ width: `${value}%` }}
        />
      </div>
      {showLabel && (
        <span className="text-caption text-text-secondary font-mono">
          {value}%
        </span>
      )}
    </div>
  )
}

interface PriorityScoreProps {
  score: number // 0-100
  size?: 'sm' | 'md' | 'lg'
}

export function PriorityScore({ score, size = 'md' }: PriorityScoreProps) {
  const getColor = () => {
    if (score >= 80) return 'bg-red-500 text-white'
    if (score >= 60) return 'bg-amber-500 text-white'
    if (score >= 40) return 'bg-blue-500 text-white'
    return 'bg-slate-400 text-white'
  }
  
  const getSizeClass = () => {
    switch (size) {
      case 'sm': return 'w-8 h-8 text-caption'
      case 'md': return 'w-10 h-10 text-body'
      case 'lg': return 'w-12 h-12 text-subheading'
    }
  }
  
  return (
    <div className={clsx(
      'rounded-lg flex items-center justify-center font-semibold',
      getColor(),
      getSizeClass()
    )}>
      {score}
    </div>
  )
}
