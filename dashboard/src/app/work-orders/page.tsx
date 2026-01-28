'use client'

/**
 * AQUAWATCH NRW - WORK ORDERS PAGE
 * =================================
 * 
 * Production-ready work orders page with:
 * - Real API data fetching with SWR
 * - Working action buttons (Assign, Start, Complete, Cancel)
 * - Create Work Order modal with real DB save
 * - Loading skeletons and empty states
 * - No mock/fake data
 */

import React, { useState, useEffect } from 'react'
import Link from 'next/link'
import { useSearchParams } from 'next/navigation'
import useSWR from 'swr'
import {
  Wrench, MapPin, Clock, User, CheckCircle, XCircle,
  AlertTriangle, Calendar, ChevronRight, Filter, Search, Plus,
  Play, Check, RefreshCw, Loader2, Users, Pause, X,
  ClipboardList, ArrowRight, Building2
} from 'lucide-react'
import { useSystemStatus } from '@/contexts/SystemStatusContext'
import { 
  EmptyState, 
  NoSearchResults,
  ErrorState 
} from '@/components/ui/EmptyState'
import { StatCardSkeleton, ListItemSkeleton } from '@/components/ui/Skeleton'

// =============================================================================
// TYPES
// =============================================================================

type WorkOrderStatus = 'pending' | 'assigned' | 'in_progress' | 'in-progress' | 'completed' | 'cancelled'
type Priority = 'critical' | 'high' | 'medium' | 'low'
type WorkOrderType = 'leak_repair' | 'pipe_replacement' | 'valve_maintenance' | 'meter_installation' | 'inspection' | 'emergency'

interface WorkOrder {
  _id?: string
  id: string
  title: string
  type: WorkOrderType
  description: string
  dma: string
  dma_id?: string
  priority: Priority
  status: WorkOrderStatus
  assignee?: string
  assigned_to?: string
  assigned_crew?: string[]
  created_at: string
  due_date?: string
  scheduled_for?: string
  started_at?: string
  completed_at?: string
  estimated_duration_hours?: number
  actual_duration_hours?: number
  estimated_loss?: number
  cost_estimate?: number
  actual_cost?: number
  leak_id?: string
  notes?: string
  source?: string
}

interface Technician {
  _id: string
  user_id: string
  name: string
  email: string
  phone: string
  role: string
  status: 'available' | 'busy' | 'offline'
  skills: string[]
  current_work_order?: string
}

interface WorkOrdersResponse {
  success: boolean
  data: WorkOrder[]
  total: number
  source?: string
}

interface TechniciansResponse {
  success: boolean
  technicians: Technician[]
  total: number
  hasData: boolean
}

// =============================================================================
// FETCHERS
// =============================================================================

const fetcher = async (url: string) => {
  const res = await fetch(url)
  if (!res.ok) throw new Error('Failed to fetch')
  return res.json()
}

// =============================================================================
// HELPERS
// =============================================================================

const getStatusColor = (status: string): string => {
  const colors: Record<string, string> = {
    pending: 'bg-slate-100 text-slate-700',
    assigned: 'bg-blue-100 text-blue-700',
    in_progress: 'bg-amber-100 text-amber-700',
    'in-progress': 'bg-amber-100 text-amber-700',
    completed: 'bg-emerald-100 text-emerald-700',
    cancelled: 'bg-red-100 text-red-700',
  }
  return colors[status] || 'bg-slate-100 text-slate-700'
}

const getPriorityColor = (priority: string): string => {
  const colors: Record<string, string> = {
    critical: 'bg-red-500',
    high: 'bg-orange-500',
    medium: 'bg-amber-500',
    low: 'bg-blue-500',
  }
  return colors[priority] || 'bg-slate-500'
}

const getTypeLabel = (type: string): string => {
  const labels: Record<string, string> = {
    leak_repair: 'Leak Repair',
    pipe_replacement: 'Pipe Replacement',
    valve_maintenance: 'Valve Maintenance',
    meter_installation: 'Meter Installation',
    inspection: 'Inspection',
    emergency: 'Emergency',
  }
  return labels[type] || type
}

const getStatusIcon = (status: string) => {
  const icons: Record<string, React.ReactNode> = {
    pending: <Clock className="w-4 h-4" />,
    assigned: <User className="w-4 h-4" />,
    in_progress: <Play className="w-4 h-4" />,
    'in-progress': <Play className="w-4 h-4" />,
    completed: <CheckCircle className="w-4 h-4" />,
    cancelled: <XCircle className="w-4 h-4" />,
  }
  return icons[status] || <Clock className="w-4 h-4" />
}

function formatDate(dateString: string | undefined): string {
  if (!dateString) return '--'
  const date = new Date(dateString)
  return date.toLocaleDateString('en-ZM', { month: 'short', day: 'numeric', year: 'numeric' })
}

function getTimeSince(dateString: string): string {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMins / 60)
  const diffDays = Math.floor(diffHours / 24)

  if (diffDays > 0) return `${diffDays}d ago`
  if (diffHours > 0) return `${diffHours}h ago`
  if (diffMins > 0) return `${diffMins}m ago`
  return 'Just now'
}

// =============================================================================
// CREATE WORK ORDER MODAL
// =============================================================================

interface CreateModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
  leakId?: string | null
}

function CreateWorkOrderModal({ isOpen, onClose, onSuccess, leakId }: CreateModalProps) {
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [form, setForm] = useState({
    title: '',
    description: '',
    type: 'leak_repair' as WorkOrderType,
    priority: 'medium' as Priority,
    dma: '',
    scheduled_for: '',
    estimated_duration_hours: 2,
  })

  useEffect(() => {
    if (leakId) {
      setForm(prev => ({
        ...prev,
        title: `Leak Repair - ${leakId}`,
        type: 'leak_repair',
        priority: 'high'
      }))
    }
  }, [leakId])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!form.title.trim() || !form.dma.trim()) {
      setError('Title and DMA are required')
      return
    }

    setIsSubmitting(true)
    setError(null)

    try {
      const res = await fetch('/api/work-orders', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...form,
          leak_id: leakId,
          source: leakId ? 'Leak Alert' : 'Manual'
        })
      })

      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.error || 'Failed to create work order')
      }

      onSuccess()
      onClose()
      setForm({
        title: '',
        description: '',
        type: 'leak_repair',
        priority: 'medium',
        dma: '',
        scheduled_for: '',
        estimated_duration_hours: 2,
      })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create work order')
    } finally {
      setIsSubmitting(false)
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-slate-200">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-slate-900">Create Work Order</h2>
            <button onClick={onClose} className="p-2 hover:bg-slate-100 rounded-lg">
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
              {error}
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Title *</label>
            <input
              type="text"
              value={form.title}
              onChange={(e) => setForm(prev => ({ ...prev, title: e.target.value }))}
              className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
              placeholder="e.g., Leak Repair at Cairo Road"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Type</label>
              <select
                value={form.type}
                onChange={(e) => setForm(prev => ({ ...prev, type: e.target.value as WorkOrderType }))}
                className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20"
              >
                <option value="leak_repair">Leak Repair</option>
                <option value="pipe_replacement">Pipe Replacement</option>
                <option value="valve_maintenance">Valve Maintenance</option>
                <option value="meter_installation">Meter Installation</option>
                <option value="inspection">Inspection</option>
                <option value="emergency">Emergency</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Priority</label>
              <select
                value={form.priority}
                onChange={(e) => setForm(prev => ({ ...prev, priority: e.target.value as Priority }))}
                className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20"
              >
                <option value="critical">Critical</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">DMA / Location *</label>
            <input
              type="text"
              value={form.dma}
              onChange={(e) => setForm(prev => ({ ...prev, dma: e.target.value }))}
              className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
              placeholder="e.g., Chilenje South"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Description</label>
            <textarea
              value={form.description}
              onChange={(e) => setForm(prev => ({ ...prev, description: e.target.value }))}
              rows={3}
              className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
              placeholder="Details about the work to be done..."
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Scheduled Date</label>
              <input
                type="date"
                value={form.scheduled_for}
                onChange={(e) => setForm(prev => ({ ...prev, scheduled_for: e.target.value }))}
                className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Est. Duration (hrs)</label>
              <input
                type="number"
                value={form.estimated_duration_hours}
                onChange={(e) => setForm(prev => ({ ...prev, estimated_duration_hours: parseInt(e.target.value) || 2 }))}
                min={1}
                className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20"
              />
            </div>
          </div>

          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-slate-200 text-slate-700 rounded-lg hover:bg-slate-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Creating...
                </>
              ) : (
                <>
                  <Plus className="w-4 h-4" />
                  Create Work Order
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

// =============================================================================
// ASSIGN MODAL
// =============================================================================

interface AssignModalProps {
  isOpen: boolean
  onClose: () => void
  onAssign: (technicianName: string) => void
  workOrderId: string
  technicians: Technician[]
  isLoading: boolean
}

function AssignModal({ isOpen, onClose, onAssign, workOrderId, technicians, isLoading }: AssignModalProps) {
  const [selectedTech, setSelectedTech] = useState<string>('')

  if (!isOpen) return null

  const availableTechs = technicians.filter(t => t.status === 'available')

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl max-w-md w-full">
        <div className="p-6 border-b border-slate-200">
          <h2 className="text-lg font-semibold text-slate-900">Assign Work Order</h2>
          <p className="text-sm text-slate-500">{workOrderId}</p>
        </div>

        <div className="p-6">
          {technicians.length === 0 ? (
            <div className="text-center py-6">
              <Users className="w-12 h-12 text-slate-300 mx-auto mb-3" />
              <p className="text-slate-500">No technicians configured.</p>
              <p className="text-sm text-slate-400">Add technicians in Admin settings.</p>
            </div>
          ) : availableTechs.length === 0 ? (
            <div className="text-center py-6">
              <Users className="w-12 h-12 text-amber-300 mx-auto mb-3" />
              <p className="text-slate-500">All technicians are busy.</p>
            </div>
          ) : (
            <div className="space-y-2 max-h-60 overflow-y-auto">
              {availableTechs.map(tech => (
                <label
                  key={tech._id}
                  className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                    selectedTech === tech.name 
                      ? 'border-blue-500 bg-blue-50' 
                      : 'border-slate-200 hover:bg-slate-50'
                  }`}
                >
                  <input
                    type="radio"
                    name="technician"
                    value={tech.name}
                    checked={selectedTech === tech.name}
                    onChange={(e) => setSelectedTech(e.target.value)}
                    className="w-4 h-4 text-blue-600"
                  />
                  <div className="flex-1">
                    <p className="font-medium text-slate-900">{tech.name}</p>
                    <p className="text-xs text-slate-500">{tech.role} • {tech.phone || 'No phone'}</p>
                  </div>
                  <span className="px-2 py-1 bg-emerald-100 text-emerald-700 rounded-full text-xs">
                    Available
                  </span>
                </label>
              ))}
            </div>
          )}
        </div>

        <div className="p-6 border-t border-slate-200 flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2 border border-slate-200 text-slate-700 rounded-lg hover:bg-slate-50"
          >
            Cancel
          </button>
          <button
            onClick={() => selectedTech && onAssign(selectedTech)}
            disabled={!selectedTech || isLoading}
            className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <User className="w-4 h-4" />}
            Assign
          </button>
        </div>
      </div>
    </div>
  )
}

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export default function WorkOrdersPage() {
  const searchParams = useSearchParams()
  const leakId = searchParams.get('leak_id')
  
  const [filter, setFilter] = useState<string>('all')
  const [search, setSearch] = useState('')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showAssignModal, setShowAssignModal] = useState<string | null>(null)
  const [actionLoading, setActionLoading] = useState<string | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)

  // System status
  const { status: systemStatus, isLoading: systemLoading } = useSystemStatus()

  // Fetch work orders from real API
  const { data: workOrdersData, error: workOrdersError, isLoading, mutate } = useSWR<WorkOrdersResponse>(
    '/api/work-orders',
    fetcher,
    { refreshInterval: 30000, revalidateOnFocus: true }
  )

  // Fetch technicians for assignment
  const { data: techData } = useSWR<TechniciansResponse>(
    '/api/technicians',
    fetcher,
    { refreshInterval: 60000 }
  )

  const workOrders = workOrdersData?.data || []
  const technicians = techData?.technicians || []
  const hasData = workOrders.length > 0

  // Open create modal if leak_id is in URL
  useEffect(() => {
    if (leakId) {
      setShowCreateModal(true)
    }
  }, [leakId])

  // =============================================================================
  // ACTION HANDLERS
  // =============================================================================

  const handleAssign = async (workOrderId: string, technicianName: string) => {
    setActionLoading(workOrderId)
    setActionError(null)

    try {
      const res = await fetch('/api/work-orders', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          id: workOrderId,
          assignee: technicianName,
          status: 'assigned'
        })
      })

      if (!res.ok) throw new Error('Failed to assign work order')
      
      await mutate()
      setShowAssignModal(null)
    } catch (err) {
      setActionError('Failed to assign work order')
    } finally {
      setActionLoading(null)
    }
  }

  const handleStart = async (workOrderId: string) => {
    setActionLoading(workOrderId)
    setActionError(null)

    try {
      const res = await fetch('/api/work-orders', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          id: workOrderId,
          status: 'in-progress',
          started_at: new Date().toISOString()
        })
      })

      if (!res.ok) throw new Error('Failed to start work order')
      await mutate()
    } catch (err) {
      setActionError('Failed to start work order')
    } finally {
      setActionLoading(null)
    }
  }

  const handleComplete = async (workOrderId: string) => {
    setActionLoading(workOrderId)
    setActionError(null)

    try {
      const res = await fetch('/api/work-orders', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          id: workOrderId,
          status: 'completed',
          completed_at: new Date().toISOString()
        })
      })

      if (!res.ok) throw new Error('Failed to complete work order')
      await mutate()
    } catch (err) {
      setActionError('Failed to complete work order')
    } finally {
      setActionLoading(null)
    }
  }

  const handleCancel = async (workOrderId: string) => {
    if (!confirm('Are you sure you want to cancel this work order?')) return

    setActionLoading(workOrderId)
    setActionError(null)

    try {
      const res = await fetch('/api/work-orders', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          id: workOrderId,
          status: 'cancelled'
        })
      })

      if (!res.ok) throw new Error('Failed to cancel work order')
      await mutate()
    } catch (err) {
      setActionError('Failed to cancel work order')
    } finally {
      setActionLoading(null)
    }
  }

  // =============================================================================
  // FILTERING
  // =============================================================================

  const filteredOrders = workOrders
    .filter(wo => {
      if (filter !== 'all' && wo.status !== filter && wo.status !== filter.replace('-', '_')) return false
      if (search) {
        const q = search.toLowerCase()
        return wo.id?.toLowerCase().includes(q) || 
               wo.title?.toLowerCase().includes(q) ||
               wo.dma?.toLowerCase().includes(q)
      }
      return true
    })
    .sort((a, b) => {
      // Sort by priority first, then by date
      const priorityOrder = { critical: 0, high: 1, medium: 2, low: 3 }
      const pA = priorityOrder[a.priority] ?? 4
      const pB = priorityOrder[b.priority] ?? 4
      if (pA !== pB) return pA - pB
      return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    })

  // Stats
  const stats = {
    total: workOrders.length,
    pending: workOrders.filter(wo => wo.status === 'pending').length,
    assigned: workOrders.filter(wo => wo.status === 'assigned').length,
    inProgress: workOrders.filter(wo => wo.status === 'in_progress' || wo.status === 'in-progress').length,
    completed: workOrders.filter(wo => wo.status === 'completed').length,
  }

  // =============================================================================
  // RENDER
  // =============================================================================

  if (!systemLoading && systemStatus && !systemStatus.database_connected) {
    return (
      <div className="bg-slate-50">
        <div className="max-w-full">
          <ErrorState 
            error="Unable to connect to the database. Please check your connection."
            onRetry={() => mutate()}
          />
        </div>
      </div>
    )
  }

  return (
    <div className="bg-slate-50 min-h-[calc(100vh-120px)]">
      <div className="max-w-full space-y-3 sm:space-y-4 lg:space-y-6">
        {/* Header */}
        <div className="flex flex-col gap-3 sm:flex-row sm:justify-between sm:items-center">
          <div className="min-w-0">
            <h1 className="text-xl sm:text-2xl font-bold text-slate-900 truncate">Work Orders</h1>
            <p className="text-sm text-slate-500 truncate">
              {hasData 
                ? `${stats.total} total • ${stats.inProgress} in progress`
                : 'No work orders yet'}
            </p>
          </div>
          <div className="flex items-center gap-2 w-full sm:w-auto">
            <button 
              onClick={() => mutate()}
              disabled={isLoading}
              className="flex-1 sm:flex-none flex items-center justify-center gap-2 px-3 py-2 border border-slate-200 text-slate-700 rounded-lg hover:bg-slate-50 disabled:opacity-50 text-sm"
            >
              <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
              <span className="hidden xs:inline">Refresh</span>
            </button>
            <button 
              onClick={() => setShowCreateModal(true)}
              className="flex-1 sm:flex-none flex items-center justify-center gap-2 px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm"
            >
              <Plus className="w-4 h-4" />
              <span>New Order</span>
            </button>
          </div>
        </div>

        {/* Error Alert */}
        {actionError && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex items-center justify-between">
            <span>{actionError}</span>
            <button onClick={() => setActionError(null)} className="text-red-500 hover:text-red-700">×</button>
          </div>
        )}

        {/* API Error */}
        {workOrdersError && (
          <ErrorState 
            error={workOrdersError.message || 'Failed to load work orders'}
            onRetry={() => mutate()}
          />
        )}

        {/* Loading */}
        {isLoading && (
          <div className="space-y-6">
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-4">
              {[...Array(5)].map((_, i) => <StatCardSkeleton key={i} />)}
            </div>
            <div className="space-y-3">
              {[...Array(4)].map((_, i) => <ListItemSkeleton key={i} />)}
            </div>
          </div>
        )}

        {/* Content */}
        {!isLoading && !workOrdersError && (
          <>
            {/* Stats */}
            <div className="grid grid-cols-2 xs:grid-cols-3 lg:grid-cols-5 gap-2 sm:gap-3">
              <div className="bg-white rounded-lg sm:rounded-xl border border-slate-200 p-2.5 sm:p-4">
                <div className="flex items-center gap-2 sm:block">
                  <div className="w-7 h-7 sm:w-8 sm:h-8 sm:hidden rounded-lg bg-slate-100 flex items-center justify-center flex-shrink-0">
                    <ClipboardList className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-slate-600" />
                  </div>
                  <div className="min-w-0">
                    <div className="text-lg sm:text-2xl font-bold text-slate-900">{hasData ? stats.total : '--'}</div>
                    <div className="text-[10px] sm:text-sm text-slate-500">Total</div>
                  </div>
                </div>
              </div>
              <div className="bg-slate-50 rounded-lg sm:rounded-xl border border-slate-200 p-2.5 sm:p-4">
                <div className="flex items-center gap-2 sm:block">
                  <div className="w-7 h-7 sm:w-8 sm:h-8 sm:hidden rounded-lg bg-slate-200 flex items-center justify-center flex-shrink-0">
                    <Clock className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-slate-600" />
                  </div>
                  <div className="min-w-0">
                    <div className="text-lg sm:text-2xl font-bold text-slate-600">{hasData ? stats.pending : '--'}</div>
                    <div className="text-[10px] sm:text-sm text-slate-500">Pending</div>
                  </div>
                </div>
              </div>
              <div className="bg-blue-50 rounded-lg sm:rounded-xl border border-blue-200 p-2.5 sm:p-4">
                <div className="flex items-center gap-2 sm:block">
                  <div className="w-7 h-7 sm:w-8 sm:h-8 sm:hidden rounded-lg bg-blue-100 flex items-center justify-center flex-shrink-0">
                    <User className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-blue-600" />
                  </div>
                  <div className="min-w-0">
                    <div className="text-lg sm:text-2xl font-bold text-blue-600">{hasData ? stats.assigned : '--'}</div>
                    <div className="text-[10px] sm:text-sm text-blue-600">Assigned</div>
                  </div>
                </div>
              </div>
              <div className="bg-amber-50 rounded-lg sm:rounded-xl border border-amber-200 p-2.5 sm:p-4">
                <div className="flex items-center gap-2 sm:block">
                  <div className="w-7 h-7 sm:w-8 sm:h-8 sm:hidden rounded-lg bg-amber-100 flex items-center justify-center flex-shrink-0">
                    <Play className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-amber-600" />
                  </div>
                  <div className="min-w-0">
                    <div className="text-lg sm:text-2xl font-bold text-amber-600">{hasData ? stats.inProgress : '--'}</div>
                    <div className="text-[10px] sm:text-sm text-amber-600">In Progress</div>
                  </div>
                </div>
              </div>
              <div className="bg-emerald-50 rounded-lg sm:rounded-xl border border-emerald-200 p-2.5 sm:p-4 col-span-2 xs:col-span-1">
                <div className="flex items-center gap-2 sm:block">
                  <div className="w-7 h-7 sm:w-8 sm:h-8 sm:hidden rounded-lg bg-emerald-100 flex items-center justify-center flex-shrink-0">
                    <CheckCircle className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-emerald-600" />
                  </div>
                  <div className="min-w-0">
                    <div className="text-lg sm:text-2xl font-bold text-emerald-600">{hasData ? stats.completed : '--'}</div>
                    <div className="text-[10px] sm:text-sm text-emerald-600">Completed</div>
                  </div>
                </div>
              </div>
            </div>

            {/* Filters */}
            <div className="bg-white rounded-lg sm:rounded-xl border border-slate-200 p-3 sm:p-4">
              <div className="flex flex-col sm:flex-row gap-2 sm:gap-4">
                <div className="flex-1 relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <input 
                    type="text"
                    placeholder="Search by ID, title, or location..."
                    className="w-full pl-10 pr-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                  />
                </div>
                <select 
                  value={filter} 
                  onChange={(e) => setFilter(e.target.value)}
                  className="px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                >
                  <option value="all">All Status</option>
                  <option value="pending">Pending</option>
                  <option value="assigned">Assigned</option>
                  <option value="in-progress">In Progress</option>
                  <option value="completed">Completed</option>
                  <option value="cancelled">Cancelled</option>
                </select>
              </div>
            </div>

            {/* Empty State */}
            {!hasData && (
              <EmptyState
                icon={<ClipboardList className="w-8 h-8" />}
                title="No Work Orders"
                description="Create your first work order to start managing field operations. Work orders can also be auto-generated from leak alerts."
                action={{
                  label: 'Create Work Order',
                  onClick: () => setShowCreateModal(true),
                  icon: <Plus className="w-4 h-4" />
                }}
              />
            )}

            {/* No search results */}
            {hasData && filteredOrders.length === 0 && (search || filter !== 'all') && (
              <NoSearchResults 
                query={search || filter}
                onClearSearch={() => { setSearch(''); setFilter('all'); }}
              />
            )}

            {/* Work Orders List */}
            {filteredOrders.length > 0 && (
              <div className="space-y-3">
                {filteredOrders.map((wo) => (
                  <div 
                    key={wo._id || wo.id}
                    className="bg-white rounded-xl border border-slate-200 hover:shadow-md hover:border-slate-300 transition-all"
                  >
                    <div className="p-3 sm:p-4">
                      <div className="flex items-start gap-2 sm:gap-4">
                        {/* Priority */}
                        <div className={`w-1 self-stretch rounded-full flex-shrink-0 ${getPriorityColor(wo.priority)}`} />
                        
                        {/* Content */}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-1.5 sm:gap-2 flex-wrap mb-1">
                            <span className="font-semibold text-slate-900 text-sm sm:text-base">{wo.id}</span>
                            <span className={`inline-flex items-center gap-1 px-1.5 sm:px-2 py-0.5 rounded-full text-[10px] sm:text-xs font-medium ${getStatusColor(wo.status)}`}>
                              {getStatusIcon(wo.status)}
                              <span className="capitalize">{wo.status.replace('_', ' ')}</span>
                            </span>
                            <span className="px-1.5 sm:px-2 py-0.5 bg-slate-100 text-slate-600 rounded-full text-[10px] sm:text-xs font-medium hidden sm:inline">
                              {getTypeLabel(wo.type)}
                            </span>
                          </div>
                          
                          <p className="font-medium text-slate-800 mb-1 text-sm sm:text-base line-clamp-1">{wo.title}</p>
                          
                          <div className="flex items-center gap-2 sm:gap-4 text-xs sm:text-sm text-slate-500 flex-wrap">
                            <span className="flex items-center gap-1">
                              <Building2 className="w-3 h-3 flex-shrink-0" />
                              {wo.dma}
                            </span>
                            {wo.assignee && (
                              <span className="flex items-center gap-1">
                                <User className="w-3 h-3" />
                                {wo.assignee}
                              </span>
                            )}
                            <span className="flex items-center gap-1">
                              <Clock className="w-3 h-3" />
                              {getTimeSince(wo.created_at)}
                            </span>
                          </div>

                          {/* Actions */}
                          <div className="flex items-center gap-1.5 sm:gap-2 mt-2 sm:mt-3 flex-wrap">
                            {wo.status === 'pending' && (
                              <button
                                onClick={() => setShowAssignModal(wo.id)}
                                disabled={actionLoading === wo.id}
                                className="flex items-center gap-1 px-2 sm:px-3 py-1 sm:py-1.5 bg-blue-100 text-blue-700 rounded-lg text-[10px] sm:text-xs font-medium hover:bg-blue-200 disabled:opacity-50 transition-colors"
                              >
                                {actionLoading === wo.id ? <Loader2 className="w-3 h-3 animate-spin" /> : <User className="w-3 h-3" />}
                                Assign
                              </button>
                            )}
                            {wo.status === 'assigned' && (
                              <button
                                onClick={() => handleStart(wo.id)}
                                disabled={actionLoading === wo.id}
                                className="flex items-center gap-1 px-2 sm:px-3 py-1 sm:py-1.5 bg-amber-100 text-amber-700 rounded-lg text-[10px] sm:text-xs font-medium hover:bg-amber-200 disabled:opacity-50 transition-colors"
                              >
                                {actionLoading === wo.id ? <Loader2 className="w-3 h-3 animate-spin" /> : <Play className="w-3 h-3" />}
                                Start
                              </button>
                            )}
                            {(wo.status === 'in_progress' || wo.status === 'in-progress') && (
                              <button
                                onClick={() => handleComplete(wo.id)}
                                disabled={actionLoading === wo.id}
                                className="flex items-center gap-1 px-2 sm:px-3 py-1 sm:py-1.5 bg-emerald-100 text-emerald-700 rounded-lg text-[10px] sm:text-xs font-medium hover:bg-emerald-200 disabled:opacity-50 transition-colors"
                              >
                                {actionLoading === wo.id ? <Loader2 className="w-3 h-3 animate-spin" /> : <Check className="w-3 h-3" />}
                                Complete
                              </button>
                            )}
                            {wo.status !== 'completed' && wo.status !== 'cancelled' && (
                              <button
                                onClick={() => handleCancel(wo.id)}
                                disabled={actionLoading === wo.id}
                                className="flex items-center gap-1 px-2 sm:px-3 py-1 sm:py-1.5 bg-slate-100 text-slate-600 rounded-lg text-[10px] sm:text-xs font-medium hover:bg-slate-200 disabled:opacity-50 transition-colors"
                              >
                                <XCircle className="w-3 h-3" />
                                Cancel
                              </button>
                            )}
                          </div>
                        </div>

                        {/* Meta */}
                        <div className="text-right text-xs sm:text-sm flex-shrink-0 hidden sm:block">
                          <div className="font-medium text-slate-700 capitalize">{wo.priority}</div>
                          <div className="text-xs text-slate-500">
                            {wo.due_date ? formatDate(wo.due_date) : '--'}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </div>

      {/* Modals */}
      <CreateWorkOrderModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onSuccess={() => mutate()}
        leakId={leakId}
      />

      {showAssignModal && (
        <AssignModal
          isOpen={true}
          onClose={() => setShowAssignModal(null)}
          onAssign={(name) => handleAssign(showAssignModal, name)}
          workOrderId={showAssignModal}
          technicians={technicians}
          isLoading={actionLoading === showAssignModal}
        />
      )}
    </div>
  )
}
