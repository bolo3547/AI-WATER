import { clsx } from 'clsx'
import Link from 'next/link'
import { TrendingUp, TrendingDown, Minus, ArrowUpRight, ArrowDownRight } from 'lucide-react'

interface KPICardProps {
  label: string
  value: string | number
  unit?: string
  trend?: 'up' | 'down' | 'stable'
  trendValue?: number
  status?: 'healthy' | 'warning' | 'critical'
  sublabel?: string
  large?: boolean
  loading?: boolean
  icon?: React.ReactNode
  sparkline?: number[]
  href?: string
  onClick?: () => void
}

export function KPICard({
  label,
  value,
  unit,
  trend,
  trendValue,
  status,
  sublabel,
  large = false,
  loading = false,
  icon,
  sparkline,
  href,
  onClick
}: KPICardProps) {
  const getTrendIcon = () => {
    switch (trend) {
      case 'up': return <ArrowUpRight className="w-4 h-4" />
      case 'down': return <ArrowDownRight className="w-4 h-4" />
      case 'stable': return <Minus className="w-4 h-4" />
      default: return null
    }
  }
  
  const getTrendColor = () => {
    switch (trend) {
      case 'up': return 'text-red-600 bg-red-50'
      case 'down': return 'text-emerald-600 bg-emerald-50'
      case 'stable': return 'text-slate-500 bg-slate-50'
      default: return 'text-slate-500 bg-slate-50'
    }
  }
  
  const getStatusGradient = () => {
    switch (status) {
      case 'healthy': return 'from-emerald-500 to-emerald-600'
      case 'warning': return 'from-amber-500 to-amber-600'
      case 'critical': return 'from-red-500 to-red-600'
      default: return 'from-blue-500 to-cyan-500'
    }
  }
  
  const getStatusBg = () => {
    switch (status) {
      case 'healthy': return 'bg-emerald-50'
      case 'warning': return 'bg-amber-50'
      case 'critical': return 'bg-red-50'
      default: return 'bg-blue-50'
    }
  }

  const getStatusBorder = () => {
    switch (status) {
      case 'healthy': return '#10b981'
      case 'warning': return '#f59e0b'
      case 'critical': return '#ef4444'
      default: return '#3b82f6'
    }
  }
  
  if (loading) {
    return (
      <div className="card-premium p-5">
        <div className="skeleton h-4 w-24 mb-3" />
        <div className="skeleton h-10 w-32 mb-2" />
        <div className="skeleton h-4 w-20" />
      </div>
    )
  }

  const cardContent = (
    <>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-3">
            {icon && (
              <div className={clsx('w-9 h-9 rounded-xl flex items-center justify-center group-hover:scale-105 transition-transform', getStatusBg())}>
                {icon}
              </div>
            )}
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider truncate">{label}</p>
          </div>
          
          <div className="flex items-baseline gap-2">
            <span className={clsx(
              large ? 'hero-metric' : 'text-3xl font-bold text-slate-900 tracking-tight'
            )}>
              {value}
            </span>
            {unit && (
              <span className="text-sm font-medium text-slate-500">{unit}</span>
            )}
          </div>
        </div>
        
        {/* Mini sparkline */}
        {sparkline && (
          <div className="w-20 h-10 flex items-end gap-0.5">
            {sparkline.slice(-10).map((v, i) => (
              <div 
                key={i} 
                className={clsx(
                  'flex-1 rounded-t transition-all duration-300',
                  status === 'critical' ? 'bg-red-300' : status === 'warning' ? 'bg-amber-300' : 'bg-blue-300'
                )}
                style={{ height: `${Math.max((v / Math.max(...sparkline)) * 100, 10)}%` }}
              />
            ))}
          </div>
        )}
      </div>
      
      {(trend || sublabel) && (
        <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between">
          {trend && (
            <span className={clsx(
              'inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-semibold',
              getTrendColor()
            )}>
              {getTrendIcon()}
              {trendValue && `${trendValue}%`}
            </span>
          )}
          {sublabel && !trend && (
            <span className="text-xs text-slate-400 truncate">{sublabel}</span>
          )}
        </div>
      )}
    </>
  )

  const className = clsx(
    'card-premium p-5 group hover:shadow-xl transition-all duration-200',
    (href || onClick) && 'cursor-pointer hover:border-blue-300'
  )

  if (href) {
    return (
      <Link 
        href={href}
        className={className}
        style={{ borderTop: `3px solid ${getStatusBorder()}` }}
      >
        {cardContent}
      </Link>
    )
  }
  
  return (
    <div 
      className={className}
      style={{ borderTop: `3px solid ${getStatusBorder()}` }}
      onClick={onClick}
    >
      {cardContent}
    </div>
  )
}
