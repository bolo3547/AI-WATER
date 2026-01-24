'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { 
  Wrench, 
  Clock, 
  AlertTriangle, 
  CheckCircle, 
  ChevronRight,
  MapPin,
  Calendar,
  RefreshCw,
  Wifi,
  WifiOff,
  Play,
  Cloud
} from 'lucide-react'
import { clsx } from 'clsx'
import { useSync } from '@/lib/sync-service'
import { useAuth } from '@/lib/auth'
import { 
  getAllWorkOrders, 
  getOfflineStats,
  WorkOrder, 
  Priority 
} from '@/lib/indexeddb'

// =============================================================================
// TECHNICIAN HOME PAGE
// =============================================================================
// Mobile-first dashboard showing:
// - Today's assignments summary
// - Quick actions
// - Recent activity
// - Sync status
// =============================================================================

export default function TechHomePage() {
  const { user } = useAuth()
  const { isOnline, isSyncing, pendingCount, lastSync, sync, fetchWorkOrders } = useSync()
  
  const [workOrders, setWorkOrders] = useState<WorkOrder[]>([])
  const [stats, setStats] = useState({
    total: 0,
    pending: 0,
    inProgress: 0,
    completed: 0,
  })
  const [offlineStats, setOfflineStats] = useState({
    workOrderCount: 0,
    pendingActionCount: 0,
    lastSync: null as string | null,
  })
  const [loading, setLoading] = useState(true)
  
  // Load work orders
  useEffect(() => {
    loadData()
  }, [])
  
  const loadData = async () => {
    setLoading(true)
    try {
      // Fetch from API or IndexedDB
      const orders = await fetchWorkOrders()
      setWorkOrders(orders)
      
      // Calculate stats
      setStats({
        total: orders.length,
        pending: orders.filter(o => o.status === 'pending' || o.status === 'assigned').length,
        inProgress: orders.filter(o => o.status === 'in-progress').length,
        completed: orders.filter(o => o.status === 'completed').length,
      })
      
      // Get offline stats
      const offline = await getOfflineStats()
      setOfflineStats(offline)
    } catch (error) {
      console.error('Failed to load data:', error)
      // Try loading from IndexedDB
      const cached = await getAllWorkOrders()
      setWorkOrders(cached)
    } finally {
      setLoading(false)
    }
  }
  
  // Get today's orders
  const today = new Date().toISOString().split('T')[0]
  const todaysOrders = workOrders.filter(o => 
    o.scheduledDate?.startsWith(today) || o.createdAt?.startsWith(today)
  )
  
  // Get urgent orders (critical/high priority, not completed)
  const urgentOrders = workOrders.filter(o => 
    (o.priority === 'critical' || o.priority === 'high') && 
    o.status !== 'completed' && 
    o.status !== 'cancelled'
  )
  
  // Format last sync time
  const formatLastSync = (dateStr: string | null): string => {
    if (!dateStr) return 'Never'
    const date = new Date(dateStr)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    
    if (diff < 60000) return 'Just now'
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`
    return date.toLocaleDateString()
  }
  
  return (
    <div className="p-4 space-y-6">
      {/* Welcome Header */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-700 rounded-2xl p-5 text-white">
        <p className="text-blue-100">Good {getGreeting()},</p>
        <h1 className="text-2xl font-bold mt-1">{user?.username || 'Technician'}</h1>
        <p className="text-blue-200 text-sm mt-2">
          {stats.pending > 0 
            ? `You have ${stats.pending} pending work order${stats.pending !== 1 ? 's' : ''}`
            : 'No pending work orders'}
        </p>
      </div>
      
      {/* Quick Stats */}
      <div className="grid grid-cols-3 gap-3">
        <StatCard 
          label="Pending" 
          value={stats.pending} 
          icon={<Clock className="w-5 h-5 text-amber-500" />}
          bgColor="bg-amber-50"
        />
        <StatCard 
          label="In Progress" 
          value={stats.inProgress} 
          icon={<Play className="w-5 h-5 text-blue-500" />}
          bgColor="bg-blue-50"
        />
        <StatCard 
          label="Completed" 
          value={stats.completed} 
          icon={<CheckCircle className="w-5 h-5 text-emerald-500" />}
          bgColor="bg-emerald-50"
        />
      </div>
      
      {/* Sync Status Card */}
      <div className="bg-white rounded-xl p-4 border border-slate-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {isOnline ? (
              <div className="w-10 h-10 bg-emerald-100 rounded-full flex items-center justify-center">
                <Wifi className="w-5 h-5 text-emerald-600" />
              </div>
            ) : (
              <div className="w-10 h-10 bg-amber-100 rounded-full flex items-center justify-center">
                <WifiOff className="w-5 h-5 text-amber-600" />
              </div>
            )}
            <div>
              <p className="font-medium text-slate-900">
                {isOnline ? 'Online' : 'Offline Mode'}
              </p>
              <p className="text-sm text-slate-500">
                Last sync: {formatLastSync(lastSync || offlineStats.lastSync)}
              </p>
            </div>
          </div>
          
          <button
            onClick={() => sync()}
            disabled={isSyncing || !isOnline}
            className={clsx(
              'p-3 rounded-xl transition-colors',
              isOnline 
                ? 'bg-blue-100 text-blue-600 hover:bg-blue-200'
                : 'bg-slate-100 text-slate-400'
            )}
          >
            <RefreshCw className={clsx('w-5 h-5', isSyncing && 'animate-spin')} />
          </button>
        </div>
        
        {pendingCount > 0 && (
          <div className="mt-3 pt-3 border-t border-slate-100 flex items-center gap-2 text-sm">
            <Cloud className="w-4 h-4 text-amber-500" />
            <span className="text-amber-700">
              {pendingCount} change{pendingCount !== 1 ? 's' : ''} waiting to sync
            </span>
          </div>
        )}
      </div>
      
      {/* Urgent Orders */}
      {urgentOrders.length > 0 && (
        <div>
          <div className="flex items-center gap-2 mb-3">
            <AlertTriangle className="w-5 h-5 text-red-500" />
            <h2 className="font-semibold text-slate-900">Urgent</h2>
          </div>
          <div className="space-y-3">
            {urgentOrders.slice(0, 3).map(order => (
              <WorkOrderCard key={order.id} order={order} />
            ))}
          </div>
        </div>
      )}
      
      {/* Today's Orders */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Calendar className="w-5 h-5 text-blue-500" />
            <h2 className="font-semibold text-slate-900">Today&apos;s Schedule</h2>
          </div>
          <Link 
            href="/tech/orders"
            className="text-sm text-blue-600 font-medium flex items-center"
          >
            View All
            <ChevronRight className="w-4 h-4" />
          </Link>
        </div>
        
        {loading ? (
          <div className="text-center py-8">
            <RefreshCw className="w-6 h-6 text-slate-400 mx-auto animate-spin" />
            <p className="text-sm text-slate-500 mt-2">Loading...</p>
          </div>
        ) : todaysOrders.length === 0 ? (
          <div className="bg-slate-50 rounded-xl p-6 text-center">
            <Wrench className="w-10 h-10 text-slate-300 mx-auto mb-2" />
            <p className="text-slate-500">No orders scheduled for today</p>
          </div>
        ) : (
          <div className="space-y-3">
            {todaysOrders.slice(0, 5).map(order => (
              <WorkOrderCard key={order.id} order={order} />
            ))}
          </div>
        )}
      </div>
      
      {/* Quick Actions */}
      <div>
        <h2 className="font-semibold text-slate-900 mb-3">Quick Actions</h2>
        <div className="grid grid-cols-2 gap-3">
          <QuickAction
            href="/tech/orders?status=in-progress"
            icon={<Play className="w-6 h-6" />}
            label="Continue Work"
            color="blue"
          />
          <QuickAction
            href="/tech/orders?status=assigned"
            icon={<Wrench className="w-6 h-6" />}
            label="Start New Order"
            color="emerald"
          />
        </div>
      </div>
    </div>
  )
}

// =============================================================================
// SUB-COMPONENTS
// =============================================================================

function getGreeting(): string {
  const hour = new Date().getHours()
  if (hour < 12) return 'morning'
  if (hour < 17) return 'afternoon'
  return 'evening'
}

interface StatCardProps {
  label: string
  value: number
  icon: React.ReactNode
  bgColor: string
}

function StatCard({ label, value, icon, bgColor }: StatCardProps) {
  return (
    <div className={clsx('rounded-xl p-4', bgColor)}>
      <div className="flex items-center justify-between">
        {icon}
        <span className="text-2xl font-bold text-slate-900">{value}</span>
      </div>
      <p className="text-sm text-slate-600 mt-1">{label}</p>
    </div>
  )
}

interface WorkOrderCardProps {
  order: WorkOrder
}

function WorkOrderCard({ order }: WorkOrderCardProps) {
  const priorityColors: Record<Priority, string> = {
    critical: 'bg-red-100 text-red-700 border-red-200',
    high: 'bg-amber-100 text-amber-700 border-amber-200',
    medium: 'bg-blue-100 text-blue-700 border-blue-200',
    low: 'bg-slate-100 text-slate-700 border-slate-200',
  }
  
  const statusColors: Record<string, string> = {
    pending: 'text-slate-500',
    assigned: 'text-blue-600',
    'in-progress': 'text-amber-600',
    completed: 'text-emerald-600',
    cancelled: 'text-red-600',
  }
  
  return (
    <Link
      href={`/tech/orders/${order.id}`}
      className="block bg-white rounded-xl p-4 border border-slate-200 hover:border-blue-300 hover:shadow-sm transition-all"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className={clsx(
              'px-2 py-0.5 text-xs font-medium rounded-full border',
              priorityColors[order.priority]
            )}>
              {order.priority}
            </span>
            <span className={clsx('text-xs font-medium capitalize', statusColors[order.status])}>
              {order.status.replace('-', ' ')}
            </span>
          </div>
          
          <h3 className="font-medium text-slate-900 mt-2 truncate">{order.title}</h3>
          
          <div className="flex items-center gap-1 text-sm text-slate-500 mt-1">
            <MapPin className="w-3.5 h-3.5 flex-shrink-0" />
            <span className="truncate">{order.location || order.dma}</span>
          </div>
          
          {order.estimatedDuration && (
            <div className="flex items-center gap-1 text-xs text-slate-400 mt-1">
              <Clock className="w-3 h-3" />
              <span>Est. {order.estimatedDuration}h</span>
            </div>
          )}
        </div>
        
        <ChevronRight className="w-5 h-5 text-slate-400 flex-shrink-0" />
      </div>
      
      {/* Offline indicator */}
      {order._syncStatus === 'pending' && (
        <div className="mt-2 pt-2 border-t border-slate-100 flex items-center gap-1 text-xs text-amber-600">
          <Cloud className="w-3 h-3" />
          <span>Pending sync</span>
        </div>
      )}
    </Link>
  )
}

interface QuickActionProps {
  href: string
  icon: React.ReactNode
  label: string
  color: 'blue' | 'emerald' | 'amber'
}

function QuickAction({ href, icon, label, color }: QuickActionProps) {
  const colors = {
    blue: 'bg-blue-50 text-blue-600 hover:bg-blue-100',
    emerald: 'bg-emerald-50 text-emerald-600 hover:bg-emerald-100',
    amber: 'bg-amber-50 text-amber-600 hover:bg-amber-100',
  }
  
  return (
    <Link
      href={href}
      className={clsx(
        'flex flex-col items-center justify-center p-4 rounded-xl transition-colors',
        colors[color]
      )}
    >
      {icon}
      <span className="text-sm font-medium mt-2">{label}</span>
    </Link>
  )
}
