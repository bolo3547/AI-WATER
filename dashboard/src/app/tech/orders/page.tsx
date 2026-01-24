'use client'

import { useState, useEffect, useCallback } from 'react'
import Link from 'next/link'
import { useSearchParams } from 'next/navigation'
import { 
  Wrench, 
  Clock, 
  AlertTriangle, 
  CheckCircle, 
  ChevronRight,
  MapPin,
  Filter,
  Search,
  RefreshCw,
  X,
  Play,
  Pause,
  Cloud
} from 'lucide-react'
import { clsx } from 'clsx'
import { useSync } from '@/lib/sync-service'
import { 
  getAllWorkOrders, 
  WorkOrder, 
  WorkOrderStatus, 
  Priority 
} from '@/lib/indexeddb'

// =============================================================================
// WORK ORDERS LIST PAGE
// =============================================================================
// Mobile-optimized list of assigned work orders with:
// - Filter by status
// - Search
// - Pull to refresh
// =============================================================================

export default function TechOrdersPage() {
  const searchParams = useSearchParams()
  const initialStatus = searchParams.get('status') as WorkOrderStatus | null
  
  const { isOnline, isSyncing, fetchWorkOrders, sync } = useSync()
  
  const [workOrders, setWorkOrders] = useState<WorkOrder[]>([])
  const [filteredOrders, setFilteredOrders] = useState<WorkOrder[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState<WorkOrderStatus | 'all'>(initialStatus || 'all')
  const [priorityFilter, setPriorityFilter] = useState<Priority | 'all'>('all')
  const [showFilters, setShowFilters] = useState(false)
  
  // Load work orders
  useEffect(() => {
    loadData()
  }, [])
  
  const loadData = async () => {
    setLoading(true)
    try {
      const orders = await fetchWorkOrders()
      setWorkOrders(orders)
    } catch (error) {
      console.error('Failed to fetch:', error)
      const cached = await getAllWorkOrders()
      setWorkOrders(cached)
    } finally {
      setLoading(false)
    }
  }
  
  // Filter orders
  useEffect(() => {
    let filtered = [...workOrders]
    
    // Status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter(o => o.status === statusFilter)
    }
    
    // Priority filter
    if (priorityFilter !== 'all') {
      filtered = filtered.filter(o => o.priority === priorityFilter)
    }
    
    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      filtered = filtered.filter(o => 
        o.title.toLowerCase().includes(query) ||
        o.id.toLowerCase().includes(query) ||
        o.location?.toLowerCase().includes(query) ||
        o.dma?.toLowerCase().includes(query) ||
        o.description?.toLowerCase().includes(query)
      )
    }
    
    // Sort: in-progress first, then by priority, then by date
    filtered.sort((a, b) => {
      // In-progress first
      if (a.status === 'in-progress' && b.status !== 'in-progress') return -1
      if (b.status === 'in-progress' && a.status !== 'in-progress') return 1
      
      // Then by priority
      const priorityOrder: Record<Priority, number> = { critical: 0, high: 1, medium: 2, low: 3 }
      const priorityDiff = priorityOrder[a.priority] - priorityOrder[b.priority]
      if (priorityDiff !== 0) return priorityDiff
      
      // Then by scheduled date
      return new Date(a.scheduledDate || a.createdAt).getTime() - 
             new Date(b.scheduledDate || b.createdAt).getTime()
    })
    
    setFilteredOrders(filtered)
  }, [workOrders, statusFilter, priorityFilter, searchQuery])
  
  const handleRefresh = useCallback(async () => {
    if (isOnline) {
      await sync()
    }
    await loadData()
  }, [isOnline, sync])
  
  const clearFilters = () => {
    setStatusFilter('all')
    setPriorityFilter('all')
    setSearchQuery('')
  }
  
  const hasActiveFilters = statusFilter !== 'all' || priorityFilter !== 'all' || searchQuery !== ''
  
  return (
    <div className="flex flex-col h-full">
      {/* Search Header */}
      <div className="bg-white border-b border-slate-200 p-4 space-y-3 sticky top-0 z-10">
        {/* Search Bar */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
          <input
            type="text"
            placeholder="Search work orders..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-10 py-3 bg-slate-100 border-0 rounded-xl text-sm focus:ring-2 focus:ring-blue-500 focus:bg-white transition-colors"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="absolute right-3 top-1/2 -translate-y-1/2"
            >
              <X className="w-5 h-5 text-slate-400" />
            </button>
          )}
        </div>
        
        {/* Filter Chips */}
        <div className="flex items-center gap-2 overflow-x-auto pb-1 -mx-1 px-1">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={clsx(
              'flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium whitespace-nowrap transition-colors',
              showFilters || hasActiveFilters
                ? 'bg-blue-100 text-blue-700'
                : 'bg-slate-100 text-slate-600'
            )}
          >
            <Filter className="w-4 h-4" />
            Filters
            {hasActiveFilters && (
              <span className="w-5 h-5 bg-blue-600 text-white text-xs rounded-full flex items-center justify-center">
                {(statusFilter !== 'all' ? 1 : 0) + (priorityFilter !== 'all' ? 1 : 0)}
              </span>
            )}
          </button>
          
          {/* Quick status filters */}
          {(['all', 'assigned', 'in-progress', 'completed'] as const).map(status => (
            <button
              key={status}
              onClick={() => setStatusFilter(status)}
              className={clsx(
                'px-3 py-1.5 rounded-full text-sm font-medium whitespace-nowrap transition-colors',
                statusFilter === status
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              )}
            >
              {status === 'all' ? 'All' : status.replace('-', ' ')}
            </button>
          ))}
        </div>
        
        {/* Extended Filters */}
        {showFilters && (
          <div className="bg-slate-50 rounded-xl p-3 space-y-3">
            <div>
              <p className="text-xs font-medium text-slate-500 mb-2">Priority</p>
              <div className="flex flex-wrap gap-2">
                {(['all', 'critical', 'high', 'medium', 'low'] as const).map(priority => (
                  <button
                    key={priority}
                    onClick={() => setPriorityFilter(priority)}
                    className={clsx(
                      'px-3 py-1 rounded-lg text-xs font-medium transition-colors capitalize',
                      priorityFilter === priority
                        ? 'bg-blue-600 text-white'
                        : 'bg-white border border-slate-200 text-slate-600'
                    )}
                  >
                    {priority}
                  </button>
                ))}
              </div>
            </div>
            
            {hasActiveFilters && (
              <button
                onClick={clearFilters}
                className="text-sm text-red-600 font-medium"
              >
                Clear all filters
              </button>
            )}
          </div>
        )}
      </div>
      
      {/* Results Count */}
      <div className="px-4 py-2 flex items-center justify-between text-sm">
        <span className="text-slate-500">
          {filteredOrders.length} order{filteredOrders.length !== 1 ? 's' : ''}
        </span>
        <button
          onClick={handleRefresh}
          disabled={isSyncing}
          className="flex items-center gap-1 text-blue-600 font-medium"
        >
          <RefreshCw className={clsx('w-4 h-4', isSyncing && 'animate-spin')} />
          Refresh
        </button>
      </div>
      
      {/* Work Orders List */}
      <div className="flex-1 overflow-y-auto px-4 pb-4 space-y-3">
        {loading ? (
          <div className="text-center py-12">
            <RefreshCw className="w-8 h-8 text-slate-400 mx-auto animate-spin" />
            <p className="text-slate-500 mt-3">Loading work orders...</p>
          </div>
        ) : filteredOrders.length === 0 ? (
          <div className="text-center py-12">
            <Wrench className="w-12 h-12 text-slate-300 mx-auto" />
            <p className="text-slate-500 font-medium mt-3">No work orders found</p>
            {hasActiveFilters && (
              <button
                onClick={clearFilters}
                className="mt-2 text-sm text-blue-600 font-medium"
              >
                Clear filters
              </button>
            )}
          </div>
        ) : (
          filteredOrders.map(order => (
            <WorkOrderCard key={order.id} order={order} />
          ))
        )}
      </div>
    </div>
  )
}

// =============================================================================
// WORK ORDER CARD COMPONENT
// =============================================================================

interface WorkOrderCardProps {
  order: WorkOrder
}

function WorkOrderCard({ order }: WorkOrderCardProps) {
  const priorityColors: Record<Priority, { bg: string; text: string; border: string }> = {
    critical: { bg: 'bg-red-100', text: 'text-red-700', border: 'border-red-200' },
    high: { bg: 'bg-amber-100', text: 'text-amber-700', border: 'border-amber-200' },
    medium: { bg: 'bg-blue-100', text: 'text-blue-700', border: 'border-blue-200' },
    low: { bg: 'bg-slate-100', text: 'text-slate-600', border: 'border-slate-200' },
  }
  
  const statusConfig: Record<string, { icon: React.ReactNode; color: string; label: string }> = {
    pending: { 
      icon: <Clock className="w-4 h-4" />, 
      color: 'text-slate-500 bg-slate-100',
      label: 'Pending'
    },
    assigned: { 
      icon: <Wrench className="w-4 h-4" />, 
      color: 'text-blue-600 bg-blue-100',
      label: 'Assigned'
    },
    'in-progress': { 
      icon: <Play className="w-4 h-4" />, 
      color: 'text-amber-600 bg-amber-100',
      label: 'In Progress'
    },
    completed: { 
      icon: <CheckCircle className="w-4 h-4" />, 
      color: 'text-emerald-600 bg-emerald-100',
      label: 'Completed'
    },
    cancelled: { 
      icon: <X className="w-4 h-4" />, 
      color: 'text-red-600 bg-red-100',
      label: 'Cancelled'
    },
  }
  
  const priority = priorityColors[order.priority]
  const status = statusConfig[order.status] || statusConfig.pending
  
  return (
    <Link
      href={`/tech/orders/${order.id}`}
      className="block bg-white rounded-2xl p-4 border border-slate-200 hover:border-blue-300 hover:shadow-md transition-all active:scale-[0.98]"
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2 flex-wrap">
          <span className={clsx(
            'px-2.5 py-1 text-xs font-semibold rounded-lg border capitalize',
            priority.bg, priority.text, priority.border
          )}>
            {order.priority}
          </span>
          <span className={clsx(
            'flex items-center gap-1 px-2.5 py-1 text-xs font-medium rounded-lg',
            status.color
          )}>
            {status.icon}
            {status.label}
          </span>
        </div>
        <span className="text-xs text-slate-400 whitespace-nowrap">{order.id}</span>
      </div>
      
      {/* Title */}
      <h3 className="font-semibold text-slate-900 mt-3 leading-tight">{order.title}</h3>
      
      {/* Description */}
      {order.description && (
        <p className="text-sm text-slate-500 mt-1 line-clamp-2">{order.description}</p>
      )}
      
      {/* Location */}
      <div className="flex items-center gap-1.5 text-sm text-slate-600 mt-3">
        <MapPin className="w-4 h-4 text-slate-400 flex-shrink-0" />
        <span className="truncate">{order.location || order.dma}</span>
      </div>
      
      {/* Footer */}
      <div className="flex items-center justify-between mt-3 pt-3 border-t border-slate-100">
        <div className="flex items-center gap-3 text-xs text-slate-500">
          <span className="flex items-center gap-1">
            <Clock className="w-3.5 h-3.5" />
            {order.estimatedDuration || '?'}h est.
          </span>
          {order.type && (
            <span className="capitalize">{order.type.replace('_', ' ')}</span>
          )}
        </div>
        
        <div className="flex items-center gap-2">
          {/* Sync status indicator */}
          {order._syncStatus === 'pending' && (
            <span className="flex items-center gap-1 text-xs text-amber-600">
              <Cloud className="w-3.5 h-3.5" />
              Pending
            </span>
          )}
          <ChevronRight className="w-5 h-5 text-slate-400" />
        </div>
      </div>
    </Link>
  )
}
