import Link from 'next/link'
import { ReactNode } from 'react'
import { TrendingUp, TrendingDown } from 'lucide-react'

interface KPICardProps {
  label: string
  value: number | string
  unit?: string
  trend?: 'up' | 'down' | 'stable'
  trendValue?: number
  status?: 'healthy' | 'warning' | 'critical'
  icon?: ReactNode
  sublabel?: string
  sparkline?: number[]
  href?: string
}

export function KPICard({
  label,
  value,
  unit,
  trend,
  trendValue,
  status,
  icon,
  sublabel,
  sparkline,
  href
}: KPICardProps) {
  const getStatusColor = () => {
    switch (status) {
      case 'critical': return 'border-l-red-500'
      case 'warning': return 'border-l-amber-500'
      case 'healthy': return 'border-l-emerald-500'
      default: return 'border-l-blue-500'
    }
  }
  
  const getTrendColor = () => {
    switch (trend) {
      case 'up': return 'text-red-600 bg-red-50'
      case 'down': return 'text-emerald-600 bg-emerald-50'
      default: return 'text-slate-600 bg-slate-50'
    }
  }
  
  const content = (
    <div className={`bg-white rounded-xl p-5 border border-slate-200 border-l-4 ${getStatusColor()} hover:shadow-md transition-all ${href ? 'cursor-pointer group' : ''}`}>
      <div className="flex items-start justify-between mb-3">
        <span className="text-sm text-slate-500 font-medium">{label}</span>
        {icon && (
          <div className="w-8 h-8 rounded-lg bg-slate-100 flex items-center justify-center group-hover:bg-slate-200 transition-colors">
            {icon}
          </div>
        )}
      </div>
      
      <div className="flex items-end gap-2 mb-2">
        <span className="text-3xl font-bold text-slate-900">{value}</span>
        {unit && <span className="text-sm text-slate-500 mb-1">{unit}</span>}
      </div>
      
      {(trend && trendValue !== undefined) && (
        <div className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${getTrendColor()}`}>
          {trend === 'up' ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
          {trendValue}%
        </div>
      )}
      
      {sublabel && (
        <p className="text-xs text-slate-500 mt-2">{sublabel}</p>
      )}
      
      {sparkline && sparkline.length > 0 && (
        <div className="mt-3 h-8 flex items-end gap-0.5">
          {sparkline.map((val, i) => {
            const max = Math.max(...sparkline)
            const height = (val / max) * 100
            return (
              <div 
                key={i}
                className="flex-1 bg-blue-200 rounded-sm transition-all hover:bg-blue-400"
                style={{ height: `${height}%` }}
              />
            )
          })}
        </div>
      )}
    </div>
  )
  
  if (href) {
    return <Link href={href}>{content}</Link>
  }
  
  return content
}
