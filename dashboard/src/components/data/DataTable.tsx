'use client'

import { clsx } from 'clsx'
import Link from 'next/link'
import { TrendingUp, TrendingDown, Minus, ChevronRight } from 'lucide-react'

interface DataTableColumn<T> {
  key: keyof T | string
  header: string
  width?: string
  align?: 'left' | 'center' | 'right'
  render?: (row: T) => React.ReactNode
}

interface DataTableProps<T> {
  columns: DataTableColumn<T>[]
  data: T[]
  keyExtractor: (row: T) => string
  onRowClick?: (row: T) => void
  loading?: boolean
  emptyMessage?: string
}

export function DataTable<T>({
  columns,
  data,
  keyExtractor,
  onRowClick,
  loading,
  emptyMessage = 'No data available'
}: DataTableProps<T>) {
  if (loading) {
    return (
      <div className="w-full">
        <div className="rounded-xl border border-slate-200 overflow-hidden">
          <table className="w-full">
            <thead className="bg-slate-50">
              <tr>
                {columns.map((col, i) => (
                  <th key={i} className="px-5 py-4 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">
                    <div className="skeleton h-4 w-20" />
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {Array.from({ length: 5 }).map((_, i) => (
                <tr key={i} className="bg-white">
                  {columns.map((_, j) => (
                    <td key={j} className="px-5 py-4">
                      <div className="skeleton h-4 w-24" />
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    )
  }
  
  if (data.length === 0) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-8 text-center">
        <p className="text-sm text-slate-500">{emptyMessage}</p>
      </div>
    )
  }
  
  return (
    <div className="w-full">
      <div className="rounded-xl border border-slate-200 overflow-hidden">
        <table className="w-full">
          <thead className="bg-gradient-to-r from-slate-50 to-slate-100">
            <tr>
              {columns.map((col, i) => (
                <th 
                  key={i} 
                  style={{ width: col.width }}
                  className={clsx(
                    'px-5 py-4 text-xs font-semibold text-slate-600 uppercase tracking-wider',
                    col.align === 'center' && 'text-center',
                    col.align === 'right' && 'text-right',
                    (!col.align || col.align === 'left') && 'text-left'
                  )}
                >
                  {col.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {data.map((row, rowIndex) => (
              <tr 
                key={keyExtractor(row)}
                onClick={() => onRowClick?.(row)}
                className={clsx(
                  'bg-white',
                  onRowClick && 'cursor-pointer hover:bg-blue-50/50 transition-colors group'
                )}
              >
                {columns.map((col, i) => (
                  <td 
                    key={i}
                    className={clsx(
                      'px-5 py-4 text-sm text-slate-700',
                      col.align === 'center' && 'text-center',
                      col.align === 'right' && 'text-right'
                    )}
                  >
                    {col.render 
                      ? col.render(row) 
                      : String((row as Record<string, unknown>)[col.key as string] ?? '')
                    }
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

interface DMAListItemProps {
  rank: number
  name: string
  nrwPercent: number
  priorityScore: number
  status: 'healthy' | 'warning' | 'critical'
  trend: 'up' | 'down' | 'stable'
  href?: string
  onClick?: () => void
}

export function DMAListItem({
  rank,
  name,
  nrwPercent,
  priorityScore,
  status,
  trend,
  href,
  onClick
}: DMAListItemProps) {
  const getStatusStyles = () => {
    switch (status) {
      case 'healthy': return { bg: 'bg-emerald-500', text: 'text-emerald-700', light: 'bg-emerald-50' }
      case 'warning': return { bg: 'bg-amber-500', text: 'text-amber-700', light: 'bg-amber-50' }
      case 'critical': return { bg: 'bg-red-500', text: 'text-red-700', light: 'bg-red-50' }
    }
  }
  
  const getPriorityStyles = () => {
    if (priorityScore >= 80) return { bg: 'bg-red-100', text: 'text-red-700' }
    if (priorityScore >= 50) return { bg: 'bg-amber-100', text: 'text-amber-700' }
    return { bg: 'bg-blue-100', text: 'text-blue-700' }
  }
  
  const getTrendIcon = () => {
    switch (trend) {
      case 'up': return <TrendingUp className="w-4 h-4 text-red-500" />
      case 'down': return <TrendingDown className="w-4 h-4 text-emerald-500" />
      case 'stable': return <Minus className="w-4 h-4 text-slate-400" />
    }
  }

  const statusStyles = getStatusStyles()
  const priorityStyles = getPriorityStyles()
  
  const content = (
    <>
      {/* Rank Badge */}
      <div className={clsx(
        'w-8 h-8 rounded-lg flex items-center justify-center font-bold text-xs flex-shrink-0',
        rank <= 3 ? 'bg-slate-900 text-white' : 'bg-slate-100 text-slate-600'
      )}>
        #{rank}
      </div>
      
      {/* Status indicator bar */}
      <div className={clsx('w-1 h-10 rounded-full flex-shrink-0', statusStyles.bg)} />
      
      {/* Name and NRW */}
      <div className="flex-1 min-w-0">
        <h4 className="font-semibold text-sm text-slate-900 group-hover:text-blue-600 transition-colors truncate">{name}</h4>
        <div className="flex items-center gap-2 mt-1">
          <span className="text-xs text-slate-500">
            <span className="font-semibold text-slate-700">{nrwPercent.toFixed(1)}%</span>
          </span>
          {getTrendIcon()}
        </div>
      </div>
      
      {/* Priority Score */}
      <div className="text-right flex-shrink-0">
        <div className={clsx(
          'inline-flex items-center justify-center w-10 h-10 rounded-lg font-bold text-sm',
          priorityStyles.bg, priorityStyles.text
        )}>
          {priorityScore}
        </div>
      </div>
      
      {/* Chevron */}
      <ChevronRight className="w-4 h-4 text-slate-300 group-hover:text-blue-500 transition-all flex-shrink-0" />
    </>
  )
  
  const className = clsx(
    'flex items-center gap-3 p-3 bg-white border border-slate-200 rounded-xl',
    'hover:border-blue-300 hover:shadow-md transition-all duration-200 group cursor-pointer'
  )
  
  if (href) {
    return (
      <Link href={href} className={className}>
        {content}
      </Link>
    )
  }
  
  return (
    <div onClick={onClick} className={className}>
      {/* Rank Badge */}
      <div className={clsx(
        'w-8 h-8 rounded-lg flex items-center justify-center font-bold text-xs flex-shrink-0',
        rank <= 3 ? 'bg-slate-900 text-white' : 'bg-slate-100 text-slate-600'
      )}>
        #{rank}
      </div>
      
      {/* Status indicator bar */}
      <div className={clsx('w-1 h-10 rounded-full flex-shrink-0', statusStyles.bg)} />
      
      {/* Name and NRW */}
      <div className="flex-1 min-w-0">
        <h4 className="font-semibold text-sm text-slate-900 group-hover:text-blue-600 transition-colors truncate">{name}</h4>
        <div className="flex items-center gap-2 mt-1">
          <span className="text-xs text-slate-500">
            <span className="font-semibold text-slate-700">{nrwPercent.toFixed(1)}%</span>
          </span>
          {getTrendIcon()}
        </div>
      </div>
      
      {/* Priority Score */}
      <div className="text-right flex-shrink-0">
        <div className={clsx(
          'inline-flex items-center justify-center w-10 h-10 rounded-lg font-bold text-sm',
          priorityStyles.bg, priorityStyles.text
        )}>
          {priorityScore}
        </div>
      </div>
      
      {content}
    </div>
  )
}
