'use client'

import { clsx } from 'clsx'

// Full page loading spinner
export function PageLoader() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-900">
      <div className="text-center">
        <div className="relative w-16 h-16 mx-auto mb-4">
          <div className="absolute inset-0 border-4 border-blue-200 dark:border-blue-900 rounded-full"></div>
          <div className="absolute inset-0 border-4 border-transparent border-t-blue-600 rounded-full animate-spin"></div>
        </div>
        <p className="text-slate-600 dark:text-slate-400 font-medium">Loading...</p>
      </div>
    </div>
  )
}

// Section loading spinner
export function SectionLoader({ message = 'Loading...' }: { message?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-12">
      <div className="relative w-10 h-10 mb-3">
        <div className="absolute inset-0 border-3 border-slate-200 dark:border-slate-700 rounded-full"></div>
        <div className="absolute inset-0 border-3 border-transparent border-t-blue-600 rounded-full animate-spin"></div>
      </div>
      <p className="text-sm text-slate-500 dark:text-slate-400">{message}</p>
    </div>
  )
}

// Inline loading spinner
export function Spinner({ size = 'md', className = '' }: { size?: 'sm' | 'md' | 'lg', className?: string }) {
  const sizes = {
    sm: 'w-4 h-4 border-2',
    md: 'w-6 h-6 border-2',
    lg: 'w-8 h-8 border-3'
  }
  
  return (
    <div className={clsx(
      'rounded-full border-slate-200 dark:border-slate-700 border-t-blue-600 animate-spin',
      sizes[size],
      className
    )} />
  )
}

// Skeleton loaders for different content types
export function SkeletonText({ lines = 3, className = '' }: { lines?: number, className?: string }) {
  return (
    <div className={clsx('space-y-2', className)}>
      {Array.from({ length: lines }).map((_, i) => (
        <div
          key={i}
          className={clsx(
            'h-4 bg-slate-200 dark:bg-slate-700 rounded animate-pulse',
            i === lines - 1 ? 'w-3/4' : 'w-full'
          )}
        />
      ))}
    </div>
  )
}

export function SkeletonCard({ className = '', children }: { className?: string, children?: React.ReactNode }) {
  return (
    <div className={clsx(
      'bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-4',
      className
    )}>
      {children || (
        <>
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 bg-slate-200 dark:bg-slate-700 rounded-lg animate-pulse" />
            <div className="flex-1">
              <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-1/2 mb-2 animate-pulse" />
              <div className="h-3 bg-slate-200 dark:bg-slate-700 rounded w-1/3 animate-pulse" />
            </div>
          </div>
          <SkeletonText lines={2} />
        </>
      )}
    </div>
  )
}

export function SkeletonTable({ rows = 5, cols = 4 }: { rows?: number, cols?: number }) {
  return (
    <div className="overflow-hidden rounded-xl border border-slate-200 dark:border-slate-700">
      {/* Header */}
      <div className="flex bg-slate-50 dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700 p-3">
        {Array.from({ length: cols }).map((_, i) => (
          <div key={i} className="flex-1 px-2">
            <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded animate-pulse" />
          </div>
        ))}
      </div>
      {/* Rows */}
      {Array.from({ length: rows }).map((_, rowIdx) => (
        <div
          key={rowIdx}
          className="flex border-b border-slate-100 dark:border-slate-700/50 p-3"
        >
          {Array.from({ length: cols }).map((_, colIdx) => (
            <div key={colIdx} className="flex-1 px-2">
              <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded animate-pulse" />
            </div>
          ))}
        </div>
      ))}
    </div>
  )
}

export function SkeletonChart({ height = 200 }: { height?: number }) {
  return (
    <div 
      className="bg-slate-100 dark:bg-slate-800 rounded-xl animate-pulse flex items-end justify-around p-4"
      style={{ height }}
    >
      {Array.from({ length: 7 }).map((_, i) => (
        <div
          key={i}
          className="bg-slate-200 dark:bg-slate-700 rounded-t w-8"
          style={{ height: `${30 + Math.random() * 50}%` }}
        />
      ))}
    </div>
  )
}

export function SkeletonMetricCard() {
  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="w-8 h-8 bg-slate-200 dark:bg-slate-700 rounded animate-pulse" />
        <div className="w-12 h-4 bg-slate-200 dark:bg-slate-700 rounded animate-pulse" />
      </div>
      <div className="h-8 bg-slate-200 dark:bg-slate-700 rounded w-2/3 mb-2 animate-pulse" />
      <div className="h-3 bg-slate-200 dark:bg-slate-700 rounded w-1/2 animate-pulse" />
    </div>
  )
}

// Dashboard skeleton loader
export function DashboardSkeleton() {
  return (
    <div className="space-y-6 p-4 sm:p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="h-8 bg-slate-200 dark:bg-slate-700 rounded w-48 mb-2 animate-pulse" />
          <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-32 animate-pulse" />
        </div>
        <div className="flex gap-2">
          <div className="w-24 h-10 bg-slate-200 dark:bg-slate-700 rounded-lg animate-pulse" />
          <div className="w-24 h-10 bg-slate-200 dark:bg-slate-700 rounded-lg animate-pulse" />
        </div>
      </div>
      
      {/* Metrics Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <SkeletonMetricCard />
        <SkeletonMetricCard />
        <SkeletonMetricCard />
        <SkeletonMetricCard />
      </div>
      
      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <SkeletonCard className="p-6">
          <div className="h-5 bg-slate-200 dark:bg-slate-700 rounded w-1/3 mb-4 animate-pulse" />
          <SkeletonChart height={250} />
        </SkeletonCard>
        <SkeletonCard className="p-6">
          <div className="h-5 bg-slate-200 dark:bg-slate-700 rounded w-1/3 mb-4 animate-pulse" />
          <SkeletonChart height={250} />
        </SkeletonCard>
      </div>
      
      {/* Table */}
      <SkeletonCard className="p-6">
        <div className="h-5 bg-slate-200 dark:bg-slate-700 rounded w-1/4 mb-4 animate-pulse" />
        <SkeletonTable rows={5} cols={5} />
      </SkeletonCard>
    </div>
  )
}

// List skeleton
export function ListSkeleton({ items = 5 }: { items?: number }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: items }).map((_, i) => (
        <div 
          key={i}
          className="flex items-center gap-3 p-3 bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700"
        >
          <div className="w-10 h-10 bg-slate-200 dark:bg-slate-700 rounded-full animate-pulse" />
          <div className="flex-1">
            <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-1/2 mb-2 animate-pulse" />
            <div className="h-3 bg-slate-200 dark:bg-slate-700 rounded w-3/4 animate-pulse" />
          </div>
          <div className="w-16 h-6 bg-slate-200 dark:bg-slate-700 rounded animate-pulse" />
        </div>
      ))}
    </div>
  )
}
