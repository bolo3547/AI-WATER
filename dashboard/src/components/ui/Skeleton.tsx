'use client'

interface SkeletonProps {
  className?: string
}

export function Skeleton({ className = '' }: SkeletonProps) {
  return (
    <div className={`animate-pulse bg-slate-200 rounded ${className}`} />
  )
}

// Stat card skeleton
export function StatCardSkeleton() {
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-4 sm:p-6">
      <div className="flex items-start justify-between">
        <div className="space-y-3 flex-1">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-8 w-16" />
          <Skeleton className="h-3 w-32" />
        </div>
        <Skeleton className="w-10 h-10 rounded-lg" />
      </div>
    </div>
  )
}

// Multiple stat cards
export function StatsGridSkeleton({ count = 4 }: { count?: number }) {
  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
      {Array.from({ length: count }).map((_, i) => (
        <StatCardSkeleton key={i} />
      ))}
    </div>
  )
}

// Table row skeleton
export function TableRowSkeleton({ columns = 5 }: { columns?: number }) {
  return (
    <tr className="border-b border-slate-100">
      {Array.from({ length: columns }).map((_, i) => (
        <td key={i} className="px-4 py-4">
          <Skeleton className="h-4 w-full max-w-[120px]" />
        </td>
      ))}
    </tr>
  )
}

// Full table skeleton
export function TableSkeleton({ rows = 5, columns = 5 }: { rows?: number; columns?: number }) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
      {/* Header */}
      <div className="bg-slate-50 px-4 py-3 border-b border-slate-200">
        <div className="flex gap-4">
          {Array.from({ length: columns }).map((_, i) => (
            <Skeleton key={i} className="h-4 w-20" />
          ))}
        </div>
      </div>
      {/* Body */}
      <table className="w-full">
        <tbody>
          {Array.from({ length: rows }).map((_, i) => (
            <TableRowSkeleton key={i} columns={columns} />
          ))}
        </tbody>
      </table>
    </div>
  )
}

// List item skeleton
export function ListItemSkeleton() {
  return (
    <div className="flex items-center gap-4 p-4 bg-white border-b border-slate-100">
      <Skeleton className="w-10 h-10 rounded-full" />
      <div className="flex-1 space-y-2">
        <Skeleton className="h-4 w-48" />
        <Skeleton className="h-3 w-32" />
      </div>
      <Skeleton className="h-6 w-16 rounded-full" />
    </div>
  )
}

// Chart skeleton
export function ChartSkeleton({ height = 200 }: { height?: number }) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6">
      <div className="flex items-center justify-between mb-4">
        <Skeleton className="h-5 w-32" />
        <Skeleton className="h-8 w-24 rounded-lg" />
      </div>
      <Skeleton className={`w-full rounded-lg`} style={{ height }} />
    </div>
  )
}

// Card skeleton
export function CardSkeleton() {
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6 space-y-4">
      <div className="flex items-center justify-between">
        <Skeleton className="h-5 w-40" />
        <Skeleton className="w-8 h-8 rounded-lg" />
      </div>
      <Skeleton className="h-4 w-full" />
      <Skeleton className="h-4 w-3/4" />
      <Skeleton className="h-4 w-1/2" />
    </div>
  )
}

// Map skeleton
export function MapSkeleton() {
  return (
    <div className="bg-slate-100 rounded-xl border border-slate-200 flex items-center justify-center" style={{ height: 400 }}>
      <div className="text-center">
        <Skeleton className="w-16 h-16 rounded-full mx-auto mb-4" />
        <Skeleton className="h-4 w-32 mx-auto" />
      </div>
    </div>
  )
}

// Full page skeleton
export function PageSkeleton() {
  return (
    <div className="space-y-6 p-4 sm:p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <Skeleton className="h-7 w-48" />
          <Skeleton className="h-4 w-64" />
        </div>
        <Skeleton className="h-10 w-32 rounded-lg" />
      </div>
      
      {/* Stats */}
      <StatsGridSkeleton />
      
      {/* Content */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ChartSkeleton />
        <CardSkeleton />
      </div>
      
      {/* Table */}
      <TableSkeleton />
    </div>
  )
}

// Inline loading indicator
export function InlineLoader({ text = 'Loading...' }: { text?: string }) {
  return (
    <div className="flex items-center gap-2 text-sm text-slate-500">
      <div className="w-4 h-4 border-2 border-slate-300 border-t-blue-600 rounded-full animate-spin" />
      <span>{text}</span>
    </div>
  )
}

// Full screen loader
export function FullScreenLoader({ text = 'Loading...' }: { text?: string }) {
  return (
    <div className="fixed inset-0 bg-white/80 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="text-center">
        <div className="w-12 h-12 border-4 border-slate-200 border-t-blue-600 rounded-full animate-spin mx-auto mb-4" />
        <p className="text-slate-600 font-medium">{text}</p>
      </div>
    </div>
  )
}
