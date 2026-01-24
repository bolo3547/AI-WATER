'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import {
  ArrowLeft,
  MapPin,
  Clock,
  Calendar,
  User,
  AlertTriangle,
  Wrench,
  Play,
  Pause,
  CheckCircle,
  X,
  Plus,
  Send,
  RefreshCw,
  Cloud,
  CloudOff,
  FileText,
  Camera,
  Package,
  ChevronDown,
  ChevronUp,
  Phone,
  Navigation
} from 'lucide-react'
import { clsx } from 'clsx'
import { useSync } from '@/lib/sync-service'
import {
  getWorkOrder,
  updateWorkOrderStatusOffline,
  addNoteOffline,
  completeWorkOrderOffline,
  WorkOrder,
  Priority,
  WorkOrderStatus
} from '@/lib/indexeddb'

// =============================================================================
// WORK ORDER DETAIL PAGE
// =============================================================================
// Mobile-optimized detail view with:
// - Full work order information
// - Offline status updates
// - Add notes
// - Complete work order
// =============================================================================

export default function WorkOrderDetailPage() {
  const params = useParams()
  const router = useRouter()
  const orderId = params.id as string
  
  const { isOnline, isSyncing, sync, pendingCount } = useSync()
  
  const [order, setOrder] = useState<WorkOrder | null>(null)
  const [loading, setLoading] = useState(true)
  const [updating, setUpdating] = useState(false)
  const [showNoteInput, setShowNoteInput] = useState(false)
  const [noteText, setNoteText] = useState('')
  const [showCompleteModal, setShowCompleteModal] = useState(false)
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    details: true,
    notes: true,
    materials: false,
    history: false
  })
  
  // Load work order
  useEffect(() => {
    loadOrder()
  }, [orderId])
  
  const loadOrder = async () => {
    setLoading(true)
    try {
      // Try from IndexedDB first (offline-first)
      const cached = await getWorkOrder(orderId)
      if (cached) {
        setOrder(cached)
        setLoading(false)
      }
      
      // Fetch fresh data if online
      if (navigator.onLine) {
        const res = await fetch(`/api/technician/work-orders/${orderId}`)
        if (res.ok) {
          const data = await res.json()
          setOrder(data.workOrder)
        }
      }
    } catch (error) {
      console.error('Failed to load work order:', error)
    } finally {
      setLoading(false)
    }
  }
  
  const handleStatusChange = async (newStatus: WorkOrderStatus) => {
    if (!order) return
    setUpdating(true)
    
    try {
      await updateWorkOrderStatusOffline(
        order.id,
        newStatus,
        `Status changed to ${newStatus}`
      )
      
      // Reload to reflect changes
      await loadOrder()
      
      // Sync if online
      if (isOnline) {
        await sync()
      }
    } catch (error) {
      console.error('Failed to update status:', error)
      alert('Failed to update status. Please try again.')
    } finally {
      setUpdating(false)
    }
  }
  
  const handleAddNote = async () => {
    if (!order || !noteText.trim()) return
    setUpdating(true)
    
    try {
      await addNoteOffline(order.id, noteText.trim())
      setNoteText('')
      setShowNoteInput(false)
      
      // Reload to reflect changes
      await loadOrder()
      
      // Sync if online
      if (isOnline) {
        await sync()
      }
    } catch (error) {
      console.error('Failed to add note:', error)
      alert('Failed to add note. Please try again.')
    } finally {
      setUpdating(false)
    }
  }
  
  const handleComplete = async (actualDuration?: number) => {
    if (!order) return
    setUpdating(true)
    
    try {
      await completeWorkOrderOffline(order.id, actualDuration)
      setShowCompleteModal(false)
      
      // Reload to reflect changes
      await loadOrder()
      
      // Sync if online
      if (isOnline) {
        await sync()
      }
    } catch (error) {
      console.error('Failed to complete work order:', error)
      alert('Failed to complete. Please try again.')
    } finally {
      setUpdating(false)
    }
  }
  
  const toggleSection = (section: string) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }))
  }
  
  const openMaps = () => {
    if (order?.coordinates) {
      const url = `https://www.google.com/maps/dir/?api=1&destination=${order.coordinates.lat},${order.coordinates.lng}`
      window.open(url, '_blank')
    } else if (order?.location) {
      const url = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(order.location)}`
      window.open(url, '_blank')
    }
  }
  
  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <RefreshCw className="w-8 h-8 text-blue-600 animate-spin" />
      </div>
    )
  }
  
  if (!order) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-4 text-center">
        <AlertTriangle className="w-12 h-12 text-amber-500 mb-4" />
        <h2 className="text-lg font-semibold text-slate-900">Work Order Not Found</h2>
        <p className="text-slate-500 mt-2">This work order may have been deleted or you don't have access.</p>
        <Link
          href="/tech/orders"
          className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-xl font-medium"
        >
          Back to Orders
        </Link>
      </div>
    )
  }
  
  const priorityColors: Record<Priority, { bg: string; text: string; border: string }> = {
    critical: { bg: 'bg-red-100', text: 'text-red-700', border: 'border-red-300' },
    high: { bg: 'bg-amber-100', text: 'text-amber-700', border: 'border-amber-300' },
    medium: { bg: 'bg-blue-100', text: 'text-blue-700', border: 'border-blue-300' },
    low: { bg: 'bg-slate-100', text: 'text-slate-600', border: 'border-slate-300' },
  }
  
  const priority = priorityColors[order.priority]
  
  return (
    <div className="flex flex-col h-full bg-slate-50">
      {/* Header */}
      <div className="bg-white border-b border-slate-200 px-4 py-3 sticky top-0 z-10">
        <div className="flex items-center gap-3">
          <button
            onClick={() => router.back()}
            className="p-2 -ml-2 hover:bg-slate-100 rounded-xl"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div className="flex-1 min-w-0">
            <p className="text-xs text-slate-500">{order.id}</p>
            <h1 className="font-semibold text-slate-900 truncate">{order.title}</h1>
          </div>
          {/* Sync indicator */}
          {order._syncStatus === 'pending' && (
            <span className="flex items-center gap-1 px-2 py-1 bg-amber-100 text-amber-700 text-xs font-medium rounded-lg">
              <CloudOff className="w-3.5 h-3.5" />
              Pending sync
            </span>
          )}
        </div>
      </div>
      
      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        {/* Status & Priority Banner */}
        <div className={clsx(
          'px-4 py-4 border-b flex items-center justify-between',
          priority.bg, priority.border
        )}>
          <div className="flex items-center gap-3">
            <StatusBadge status={order.status} />
            <span className={clsx(
              'px-2.5 py-1 text-xs font-semibold rounded-lg capitalize',
              priority.text, priority.bg, priority.border, 'border'
            )}>
              {order.priority} priority
            </span>
          </div>
          {order.priority === 'critical' && (
            <AlertTriangle className="w-6 h-6 text-red-500" />
          )}
        </div>
        
        {/* Quick Info */}
        <div className="bg-white px-4 py-4 space-y-3 border-b border-slate-200">
          {/* Location with navigation */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm text-slate-600">
              <MapPin className="w-4 h-4 text-slate-400" />
              <span>{order.location || order.dma || 'Location not set'}</span>
            </div>
            {(order.coordinates || order.location) && (
              <button
                onClick={openMaps}
                className="flex items-center gap-1 px-3 py-1.5 bg-blue-100 text-blue-700 text-xs font-medium rounded-lg"
              >
                <Navigation className="w-3.5 h-3.5" />
                Navigate
              </button>
            )}
          </div>
          
          {/* Scheduled time */}
          {order.scheduledDate && (
            <div className="flex items-center gap-2 text-sm text-slate-600">
              <Calendar className="w-4 h-4 text-slate-400" />
              <span>Scheduled: {new Date(order.scheduledDate).toLocaleString()}</span>
            </div>
          )}
          
          {/* Estimated duration */}
          <div className="flex items-center gap-2 text-sm text-slate-600">
            <Clock className="w-4 h-4 text-slate-400" />
            <span>Estimated: {order.estimatedDuration || '?'} hours</span>
          </div>
          
          {/* Type */}
          {order.type && (
            <div className="flex items-center gap-2 text-sm text-slate-600">
              <Wrench className="w-4 h-4 text-slate-400" />
              <span className="capitalize">{order.type.replace('_', ' ')}</span>
            </div>
          )}
        </div>
        
        {/* Action Buttons */}
        {order.status !== 'completed' && order.status !== 'cancelled' && (
          <div className="bg-white px-4 py-4 border-b border-slate-200">
            <p className="text-xs font-medium text-slate-500 mb-3">Quick Actions</p>
            <div className="grid grid-cols-2 gap-3">
              {order.status === 'assigned' && (
                <ActionButton
                  icon={<Play className="w-5 h-5" />}
                  label="Start Work"
                  onClick={() => handleStatusChange('in-progress')}
                  disabled={updating}
                  variant="primary"
                />
              )}
              {order.status === 'in-progress' && (
                <>
                  <ActionButton
                    icon={<Pause className="w-5 h-5" />}
                    label="Pause"
                    onClick={() => handleStatusChange('assigned')}
                    disabled={updating}
                    variant="secondary"
                  />
                  <ActionButton
                    icon={<CheckCircle className="w-5 h-5" />}
                    label="Complete"
                    onClick={() => setShowCompleteModal(true)}
                    disabled={updating}
                    variant="success"
                  />
                </>
              )}
              <ActionButton
                icon={<FileText className="w-5 h-5" />}
                label="Add Note"
                onClick={() => setShowNoteInput(true)}
                disabled={updating}
                variant="outline"
              />
              {order.status === 'assigned' && (
                <ActionButton
                  icon={<X className="w-5 h-5" />}
                  label="Cancel"
                  onClick={() => handleStatusChange('cancelled')}
                  disabled={updating}
                  variant="danger"
                />
              )}
            </div>
          </div>
        )}
        
        {/* Details Section */}
        <CollapsibleSection
          title="Details"
          icon={<FileText className="w-4 h-4" />}
          expanded={expandedSections.details}
          onToggle={() => toggleSection('details')}
        >
          <div className="space-y-4">
            {order.description && (
              <div>
                <p className="text-xs font-medium text-slate-500 mb-1">Description</p>
                <p className="text-sm text-slate-700">{order.description}</p>
              </div>
            )}
            
            {order.dma && (
              <div>
                <p className="text-xs font-medium text-slate-500 mb-1">DMA Zone</p>
                <p className="text-sm text-slate-700">{order.dma}</p>
              </div>
            )}
            
            {order.relatedLeakId && (
              <div>
                <p className="text-xs font-medium text-slate-500 mb-1">Related Leak</p>
                <p className="text-sm text-blue-600 font-mono">{order.relatedLeakId}</p>
              </div>
            )}
            
            {order.assignedTo && (
              <div>
                <p className="text-xs font-medium text-slate-500 mb-1">Assigned To</p>
                <div className="flex items-center gap-2">
                  <User className="w-4 h-4 text-slate-400" />
                  <span className="text-sm text-slate-700">{order.assignedTo}</span>
                </div>
              </div>
            )}
          </div>
        </CollapsibleSection>
        
        {/* Notes Section */}
        <CollapsibleSection
          title={`Notes (${order.notes?.length || 0})`}
          icon={<FileText className="w-4 h-4" />}
          expanded={expandedSections.notes}
          onToggle={() => toggleSection('notes')}
        >
          <div className="space-y-3">
            {order.notes && order.notes.length > 0 ? (
              order.notes.map((note, i) => (
                <div key={i} className="bg-slate-50 rounded-xl p-3">
                  <p className="text-sm text-slate-700">{note}</p>
                </div>
              ))
            ) : (
              <p className="text-sm text-slate-500 italic">No notes yet</p>
            )}
            
            {!showNoteInput && (
              <button
                onClick={() => setShowNoteInput(true)}
                className="flex items-center gap-2 text-sm text-blue-600 font-medium"
              >
                <Plus className="w-4 h-4" />
                Add Note
              </button>
            )}
          </div>
        </CollapsibleSection>
        
        {/* Materials Section */}
        <CollapsibleSection
          title={`Materials (${order.materialsUsed?.length || 0})`}
          icon={<Package className="w-4 h-4" />}
          expanded={expandedSections.materials}
          onToggle={() => toggleSection('materials')}
        >
          <div className="space-y-3">
            {order.materialsUsed && order.materialsUsed.length > 0 ? (
              order.materialsUsed.map((mat, i) => (
                <div key={i} className="flex items-center justify-between bg-slate-50 rounded-xl p-3">
                  <span className="text-sm text-slate-700">{mat.name}</span>
                  <span className="text-sm font-medium text-slate-600">x{mat.quantity}</span>
                </div>
              ))
            ) : (
              <p className="text-sm text-slate-500 italic">No materials recorded</p>
            )}
          </div>
        </CollapsibleSection>
        
        {/* Timestamps */}
        <div className="bg-white px-4 py-4 mt-2">
          <p className="text-xs text-slate-400">
            Created: {new Date(order.createdAt).toLocaleString()}
          </p>
          <p className="text-xs text-slate-400">
            Last updated: {new Date(order.updatedAt).toLocaleString()}
          </p>
        </div>
        
        {/* Spacer for bottom action bar */}
        <div className="h-24" />
      </div>
      
      {/* Note Input Modal */}
      {showNoteInput && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-end">
          <div className="bg-white w-full rounded-t-3xl p-4 animate-slide-up">
            <h3 className="font-semibold text-lg mb-3">Add Note</h3>
            <textarea
              value={noteText}
              onChange={(e) => setNoteText(e.target.value)}
              placeholder="Enter your note..."
              rows={4}
              className="w-full p-3 border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              autoFocus
            />
            <div className="flex gap-3 mt-4">
              <button
                onClick={() => {
                  setShowNoteInput(false)
                  setNoteText('')
                }}
                className="flex-1 py-3 bg-slate-100 text-slate-700 font-medium rounded-xl"
              >
                Cancel
              </button>
              <button
                onClick={handleAddNote}
                disabled={!noteText.trim() || updating}
                className="flex-1 py-3 bg-blue-600 text-white font-medium rounded-xl flex items-center justify-center gap-2 disabled:opacity-50"
              >
                <Send className="w-4 h-4" />
                Save Note
              </button>
            </div>
          </div>
        </div>
      )}
      
      {/* Complete Modal */}
      {showCompleteModal && (
        <CompleteWorkOrderModal
          order={order}
          onClose={() => setShowCompleteModal(false)}
          onComplete={handleComplete}
          updating={updating}
        />
      )}
    </div>
  )
}

// =============================================================================
// HELPER COMPONENTS
// =============================================================================

interface StatusBadgeProps {
  status: WorkOrderStatus
}

function StatusBadge({ status }: StatusBadgeProps) {
  const config: Record<string, { icon: React.ReactNode; color: string; label: string }> = {
    pending: { icon: <Clock className="w-4 h-4" />, color: 'bg-slate-100 text-slate-600', label: 'Pending' },
    assigned: { icon: <Wrench className="w-4 h-4" />, color: 'bg-blue-100 text-blue-700', label: 'Assigned' },
    'in-progress': { icon: <Play className="w-4 h-4" />, color: 'bg-amber-100 text-amber-700', label: 'In Progress' },
    completed: { icon: <CheckCircle className="w-4 h-4" />, color: 'bg-emerald-100 text-emerald-700', label: 'Completed' },
    cancelled: { icon: <X className="w-4 h-4" />, color: 'bg-red-100 text-red-700', label: 'Cancelled' },
  }
  
  const { icon, color, label } = config[status] || config.pending
  
  return (
    <span className={clsx('flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium rounded-xl', color)}>
      {icon}
      {label}
    </span>
  )
}

interface ActionButtonProps {
  icon: React.ReactNode
  label: string
  onClick: () => void
  disabled?: boolean
  variant: 'primary' | 'secondary' | 'success' | 'danger' | 'outline'
}

function ActionButton({ icon, label, onClick, disabled, variant }: ActionButtonProps) {
  const variants = {
    primary: 'bg-blue-600 text-white hover:bg-blue-700',
    secondary: 'bg-slate-200 text-slate-700 hover:bg-slate-300',
    success: 'bg-emerald-600 text-white hover:bg-emerald-700',
    danger: 'bg-red-600 text-white hover:bg-red-700',
    outline: 'bg-white text-slate-700 border border-slate-200 hover:bg-slate-50'
  }
  
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={clsx(
        'flex items-center justify-center gap-2 py-3 px-4 rounded-xl font-medium transition-colors disabled:opacity-50 active:scale-95',
        variants[variant]
      )}
    >
      {icon}
      {label}
    </button>
  )
}

interface CollapsibleSectionProps {
  title: string
  icon: React.ReactNode
  expanded: boolean
  onToggle: () => void
  children: React.ReactNode
}

function CollapsibleSection({ title, icon, expanded, onToggle, children }: CollapsibleSectionProps) {
  return (
    <div className="bg-white border-b border-slate-200">
      <button
        onClick={onToggle}
        className="w-full px-4 py-3 flex items-center justify-between"
      >
        <div className="flex items-center gap-2 text-sm font-medium text-slate-700">
          {icon}
          {title}
        </div>
        {expanded ? (
          <ChevronUp className="w-5 h-5 text-slate-400" />
        ) : (
          <ChevronDown className="w-5 h-5 text-slate-400" />
        )}
      </button>
      {expanded && (
        <div className="px-4 pb-4">
          {children}
        </div>
      )}
    </div>
  )
}

interface CompleteWorkOrderModalProps {
  order: WorkOrder
  onClose: () => void
  onComplete: (actualDuration?: number) => void
  updating: boolean
}

function CompleteWorkOrderModal({ order, onClose, onComplete, updating }: CompleteWorkOrderModalProps) {
  const [actualHours, setActualHours] = useState<string>(order.estimatedDuration?.toString() || '')
  
  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white w-full max-w-sm rounded-2xl p-5 animate-fade-in">
        <div className="text-center mb-4">
          <div className="w-14 h-14 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-3">
            <CheckCircle className="w-8 h-8 text-emerald-600" />
          </div>
          <h3 className="font-semibold text-lg">Complete Work Order?</h3>
          <p className="text-sm text-slate-500 mt-1">This action will mark the work order as completed.</p>
        </div>
        
        <div className="mb-4">
          <label className="block text-sm font-medium text-slate-700 mb-2">
            Actual Duration (hours)
          </label>
          <input
            type="number"
            value={actualHours}
            onChange={(e) => setActualHours(e.target.value)}
            placeholder="Enter hours worked"
            step="0.5"
            min="0"
            className="w-full p-3 border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
          />
        </div>
        
        <div className="flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 py-3 bg-slate-100 text-slate-700 font-medium rounded-xl"
          >
            Cancel
          </button>
          <button
            onClick={() => onComplete(actualHours ? parseFloat(actualHours) : undefined)}
            disabled={updating}
            className="flex-1 py-3 bg-emerald-600 text-white font-medium rounded-xl flex items-center justify-center gap-2 disabled:opacity-50"
          >
            <CheckCircle className="w-4 h-4" />
            Complete
          </button>
        </div>
      </div>
    </div>
  )
}
