import { ReactNode } from 'react'
import { clsx } from 'clsx'
import { AlertTriangle, Info, CheckCircle, XCircle, ChevronRight } from 'lucide-react'

interface SectionCardProps {
  title: string
  subtitle?: string
  children: ReactNode
  action?: ReactNode
  noPadding?: boolean
  elevated?: boolean
}

export function SectionCard({ 
  title, 
  subtitle, 
  children, 
  action,
  noPadding,
  elevated = false
}: SectionCardProps) {
  return (
    <div className={clsx(
      'bg-white rounded-xl border border-slate-200 overflow-hidden transition-all duration-200',
      elevated && 'shadow-lg hover:shadow-xl'
    )}>
      <div className="flex items-start justify-between px-6 pt-5 pb-4 border-b border-slate-100 bg-gradient-to-r from-slate-50/50 to-white">
        <div>
          <h3 className="text-base font-semibold text-slate-900">{title}</h3>
          {subtitle && (
            <p className="text-sm text-slate-500 mt-0.5">{subtitle}</p>
          )}
        </div>
        {action}
      </div>
      <div className={clsx(!noPadding && 'p-6')}>
        {children}
      </div>
    </div>
  )
}

interface AlertBannerProps {
  type: 'info' | 'warning' | 'error' | 'success'
  title: string
  message?: string
  action?: ReactNode
}

export function AlertBanner({ type, title, message, action }: AlertBannerProps) {
  const getStyles = () => {
    switch (type) {
      case 'info':
        return {
          bg: 'bg-blue-50 border-blue-200',
          icon: Info,
          iconColor: 'text-blue-600',
          iconBg: 'bg-blue-100'
        }
      case 'warning':
        return {
          bg: 'bg-amber-50 border-amber-200',
          icon: AlertTriangle,
          iconColor: 'text-amber-600',
          iconBg: 'bg-amber-100'
        }
      case 'error':
        return {
          bg: 'bg-red-50 border-red-200',
          icon: XCircle,
          iconColor: 'text-red-600',
          iconBg: 'bg-red-100'
        }
      case 'success':
        return {
          bg: 'bg-emerald-50 border-emerald-200',
          icon: CheckCircle,
          iconColor: 'text-emerald-600',
          iconBg: 'bg-emerald-100'
        }
    }
  }
  
  const styles = getStyles()
  const Icon = styles.icon
  
  return (
    <div className={clsx('rounded-xl border p-4 flex items-start gap-4', styles.bg)}>
      <div className={clsx('w-10 h-10 rounded-lg flex items-center justify-center', styles.iconBg)}>
        <Icon className={clsx('w-5 h-5', styles.iconColor)} />
      </div>
      <div className="flex-1">
        <p className="text-sm font-semibold text-slate-900">{title}</p>
        {message && (
          <p className="text-sm text-slate-600 mt-1">{message}</p>
        )}
      </div>
      {action}
    </div>
  )
}

interface EmptyStateProps {
  icon?: ReactNode
  title: string
  description?: string
  action?: ReactNode
}

export function EmptyState({ icon, title, description, action }: EmptyStateProps) {
  return (
    <div className="text-center py-12 px-6">
      {icon && (
        <div className="w-16 h-16 rounded-2xl bg-slate-100 flex items-center justify-center mx-auto mb-4">
          {icon}
        </div>
      )}
      <h3 className="text-lg font-semibold text-slate-900">{title}</h3>
      {description && (
        <p className="text-sm text-slate-500 mt-2 max-w-sm mx-auto">{description}</p>
      )}
      {action && <div className="mt-6">{action}</div>}
    </div>
  )
}

interface StatCardProps {
  label: string
  value: string | number
  change?: number
  changeLabel?: string
  icon?: ReactNode
  trend?: 'up' | 'down' | 'stable'
}

export function StatCard({ label, value, change, changeLabel, icon, trend }: StatCardProps) {
  return (
    <div className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-xl p-5 text-white relative overflow-hidden group">
      <div className="absolute top-0 right-0 w-24 h-24 bg-white/5 rounded-full -mr-12 -mt-12 group-hover:bg-white/10 transition-colors" />
      <div className="relative z-10">
        <div className="flex items-center gap-2 mb-3">
          {icon && <div className="opacity-60">{icon}</div>}
          <span className="text-sm text-slate-400">{label}</span>
        </div>
        <div className="text-3xl font-bold">{value}</div>
        {change !== undefined && (
          <div className="flex items-center gap-2 mt-2">
            <span className={clsx(
              'text-sm font-medium',
              trend === 'up' ? 'text-emerald-400' : trend === 'down' ? 'text-red-400' : 'text-slate-400'
            )}>
              {change > 0 ? '+' : ''}{change}%
            </span>
            {changeLabel && <span className="text-sm text-slate-500">{changeLabel}</span>}
          </div>
        )}
      </div>
    </div>
  )
}

interface ActionCardProps {
  title: string
  description: string
  icon?: ReactNode
  onClick?: () => void
  badge?: string
  badgeColor?: 'blue' | 'green' | 'amber' | 'red'
}

export function ActionCard({ title, description, icon, onClick, badge, badgeColor = 'blue' }: ActionCardProps) {
  const badgeColors = {
    blue: 'bg-blue-100 text-blue-700',
    green: 'bg-emerald-100 text-emerald-700',
    amber: 'bg-amber-100 text-amber-700',
    red: 'bg-red-100 text-red-700'
  }
  
  return (
    <button
      onClick={onClick}
      className="w-full text-left p-5 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 hover:border-slate-300 transition-all duration-200 group"
    >
      <div className="flex items-start gap-4">
        {icon && (
          <div className="w-12 h-12 rounded-xl bg-slate-100 flex items-center justify-center group-hover:bg-blue-100 transition-colors">
            {icon}
          </div>
        )}
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <h4 className="font-semibold text-slate-900 group-hover:text-blue-600 transition-colors">{title}</h4>
            {badge && (
              <span className={clsx('text-xs font-medium px-2 py-0.5 rounded-full', badgeColors[badgeColor])}>
                {badge}
              </span>
            )}
          </div>
          <p className="text-sm text-slate-500 mt-1">{description}</p>
        </div>
        <ChevronRight className="w-5 h-5 text-slate-400 group-hover:text-blue-500 group-hover:translate-x-1 transition-all" />
      </div>
    </button>
  )
}

interface ProgressCardProps {
  label: string
  value: number
  max?: number
  color?: 'blue' | 'green' | 'amber' | 'red'
  showPercentage?: boolean
}

export function ProgressCard({ label, value, max = 100, color = 'blue', showPercentage = true }: ProgressCardProps) {
  const percentage = Math.round((value / max) * 100)
  
  const colors = {
    blue: 'bg-blue-500',
    green: 'bg-emerald-500',
    amber: 'bg-amber-500',
    red: 'bg-red-500'
  }
  
  const bgColors = {
    blue: 'bg-blue-100',
    green: 'bg-emerald-100',
    amber: 'bg-amber-100',
    red: 'bg-red-100'
  }
  
  return (
    <div className="p-4 rounded-xl border border-slate-200 bg-white">
      <div className="flex items-center justify-between mb-3">
        <span className="text-sm font-medium text-slate-700">{label}</span>
        {showPercentage && (
          <span className="text-sm font-semibold text-slate-900">{percentage}%</span>
        )}
      </div>
      <div className={clsx('h-2 rounded-full', bgColors[color])}>
        <div 
          className={clsx('h-full rounded-full transition-all duration-500', colors[color])}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  )
}
