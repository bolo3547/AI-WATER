'use client'

import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { 
  Plus,
  Filter,
  Search,
  Clock,
  CheckCircle,
  AlertTriangle,
  User,
  Calendar,
  MapPin,
  X,
  Send,
  Loader2,
  RefreshCw,
  Wifi,
  WifiOff
} from 'lucide-react'
import { SectionCard } from '@/components/ui/Cards'
import { Button, Tabs, Select } from '@/components/ui/Controls'
import { DataTable } from '@/components/data/DataTable'
import { StatusBadge } from '@/components/metrics/StatusIndicators'
import { formatRelativeTime } from '@/lib/api'

interface WorkOrder {
  id: string
  title: string
  dma: string
  priority: 'high' | 'medium' | 'low'
  status: 'pending' | 'in_progress' | 'completed'
  assignee: string
  created_at: string
  due_date: string
  estimated_loss: number
  source: string
  description?: string
  created_by?: string
}

// API base URL
const API_URL = '/api/work-orders'

export default function ActionsPage() {
  const router = useRouter()
  const [activeTab, setActiveTab] = useState('all')
  const [priorityFilter, setPriorityFilter] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [selectedWorkOrder, setSelectedWorkOrder] = useState<WorkOrder | null>(null)
  const [workOrders, setWorkOrders] = useState<WorkOrder[]>([])
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [showSuccess, setShowSuccess] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [isConnected, setIsConnected] = useState(true)
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date())
  
  // Form state
  const [formData, setFormData] = useState({
    title: '',
    dma: '',
    priority: 'medium' as 'high' | 'medium' | 'low',
    assignee: 'Unassigned',
    description: '',
    estimated_loss: 0
  })
  
  // Fetch work orders from API
  const fetchWorkOrders = useCallback(async () => {
    try {
      const response = await fetch(API_URL)
      const data = await response.json()
      
      if (data.success) {
        setWorkOrders(data.data)
        setIsConnected(true)
        setLastRefresh(new Date())
      }
    } catch (error) {
      console.error('Failed to fetch work orders:', error)
      setIsConnected(false)
    } finally {
      setIsLoading(false)
    }
  }, [])
  
  // Load work orders on mount
  useEffect(() => {
    fetchWorkOrders()
    
    // Poll for updates every 10 seconds
    const interval = setInterval(fetchWorkOrders, 10000)
    return () => clearInterval(interval)
  }, [fetchWorkOrders])
  
  // Create work order function - REAL API CALL
  const createWorkOrder = async () => {
    if (!formData.title || !formData.dma) {
      alert('Please fill in all required fields')
      return
    }
    
    setIsSubmitting(true)
    
    try {
      // Get current user from localStorage
      const userStr = localStorage.getItem('user')
      const user = userStr ? JSON.parse(userStr) : { username: 'Admin' }
      
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          title: formData.title,
          dma: formData.dma,
          priority: formData.priority,
          assignee: formData.assignee,
          description: formData.description,
          estimated_loss: formData.estimated_loss,
          created_by: user.name || user.username || 'Admin'
        })
      })
      
      const data = await response.json()
      
      if (data.success) {
        // Add new work order to state
        setWorkOrders(prev => [data.data, ...prev])
        setShowSuccess(true)
        
        // Reset form
        setFormData({
          title: '',
          dma: '',
          priority: 'medium',
          assignee: 'Unassigned',
          description: '',
          estimated_loss: 0
        })
        
        // Close modal after showing success
        setTimeout(() => {
          setShowSuccess(false)
          setShowCreateModal(false)
        }, 2000)
      } else {
        alert(data.error || 'Failed to create work order')
      }
    } catch (error) {
      console.error('Error creating work order:', error)
      alert('Failed to create work order. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }
  
  const tabs = [
    { id: 'all', label: 'All', count: workOrders.length },
    { id: 'pending', label: 'Pending', count: workOrders.filter(w => w.status === 'pending').length },
    { id: 'in_progress', label: 'In Progress', count: workOrders.filter(w => w.status === 'in_progress').length },
    { id: 'completed', label: 'Completed', count: workOrders.filter(w => w.status === 'completed').length },
  ]
  
  const filteredOrders = workOrders
    .filter(order => {
      if (activeTab !== 'all' && order.status !== activeTab) return false
      if (priorityFilter && order.priority !== priorityFilter) return false
      if (searchQuery && !order.title.toLowerCase().includes(searchQuery.toLowerCase()) && 
          !order.dma.toLowerCase().includes(searchQuery.toLowerCase())) return false
      return true
    })
  
  const getPriorityBadge = (priority: string) => {
    switch (priority) {
      case 'high': return <span className="px-2 py-0.5 rounded text-label font-medium bg-red-100 text-red-700">High</span>
      case 'medium': return <span className="px-2 py-0.5 rounded text-label font-medium bg-amber-100 text-amber-700">Medium</span>
      case 'low': return <span className="px-2 py-0.5 rounded text-label font-medium bg-gray-100 text-gray-700">Low</span>
      default: return null
    }
  }
  
  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'pending': return <StatusBadge status="warning" label="Pending" />
      case 'in_progress': return <StatusBadge status="healthy" label="In Progress" />
      case 'completed': return <StatusBadge status="healthy" label="Completed" />
      default: return null
    }
  }
  
  // Calculate summary stats
  const highPriorityPending = workOrders.filter(w => w.priority === 'high' && w.status === 'pending').length
  const totalEstimatedLoss = workOrders.filter(w => w.status !== 'completed').reduce((sum, w) => sum + w.estimated_loss, 0)
  const overdueCount = workOrders.filter(w => w.status !== 'completed' && new Date(w.due_date) < new Date()).length
  
  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-blue-600 animate-spin mx-auto mb-4" />
          <p className="text-slate-600">Loading work orders from server...</p>
        </div>
      </div>
    )
  }
  
  return (
    <div className="space-y-6">
      {/* Connection Status Banner */}
      <div className={`flex items-center justify-between px-4 py-2 rounded-lg ${isConnected ? 'bg-emerald-50 border border-emerald-200' : 'bg-red-50 border border-red-200'}`}>
        <div className="flex items-center gap-2">
          {isConnected ? (
            <>
              <Wifi className="w-4 h-4 text-emerald-600" />
              <span className="text-sm text-emerald-700 font-medium">Connected to Server</span>
              <span className="text-xs text-emerald-500">• Real-time sync active</span>
            </>
          ) : (
            <>
              <WifiOff className="w-4 h-4 text-red-600" />
              <span className="text-sm text-red-700 font-medium">Connection Lost</span>
              <span className="text-xs text-red-500">• Retrying...</span>
            </>
          )}
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs text-slate-500">
            Last sync: {lastRefresh.toLocaleTimeString()}
          </span>
          <button 
            onClick={fetchWorkOrders}
            className="flex items-center gap-1 text-sm text-blue-600 hover:text-blue-700"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
        </div>
      </div>
      
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 sm:gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl lg:text-display font-bold text-text-primary">Actions & Work Orders</h1>
          <p className="text-xs sm:text-sm lg:text-body text-text-secondary mt-0.5 sm:mt-1">
            Manage leak investigations and repair tasks
          </p>
        </div>
        <Button variant="primary" onClick={() => setShowCreateModal(true)}>
          <Plus className="w-4 h-4" />
          <span className="hidden sm:inline">Create Work Order</span>
          <span className="sm:hidden">Create</span>
        </Button>
      </div>
      
      {/* Summary Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-2 sm:gap-4">
        <div className="card p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-red-100 flex items-center justify-center">
              <AlertTriangle className="w-5 h-5 text-red-600" />
            </div>
            <div>
              <p className="text-label text-text-tertiary uppercase">High Priority Pending</p>
              <p className="text-heading font-bold text-text-primary">{highPriorityPending}</p>
            </div>
          </div>
        </div>
        <div className="card p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-amber-100 flex items-center justify-center">
              <Clock className="w-5 h-5 text-amber-600" />
            </div>
            <div>
              <p className="text-label text-text-tertiary uppercase">In Progress</p>
              <p className="text-heading font-bold text-text-primary">
                {workOrders.filter(w => w.status === 'in_progress').length}
              </p>
            </div>
          </div>
        </div>
        <div className="card p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center">
              <MapPin className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <p className="text-label text-text-tertiary uppercase">Est. Loss (Active)</p>
              <p className="text-heading font-bold text-text-primary">{totalEstimatedLoss} m³/day</p>
            </div>
          </div>
        </div>
        <div className="card p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-green-100 flex items-center justify-center">
              <CheckCircle className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <p className="text-label text-text-tertiary uppercase">Completed (30d)</p>
              <p className="text-heading font-bold text-text-primary">
                {workOrders.filter(w => w.status === 'completed').length}
              </p>
            </div>
          </div>
        </div>
      </div>
      
      {/* Work Orders Table */}
      <SectionCard 
        title="Work Orders"
        subtitle="All leak investigations and maintenance tasks"
        noPadding
      >
        {/* Filters */}
        <div className="p-4 border-b border-surface-border space-y-3">
          <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />
          
          <div className="flex gap-3">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-tertiary" />
              <input
                type="text"
                placeholder="Search work orders..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-3 py-2 text-body bg-white border border-surface-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>
            <Select
              value={priorityFilter}
              options={[
                { value: '', label: 'All Priorities' },
                { value: 'high', label: 'High Priority' },
                { value: 'medium', label: 'Medium Priority' },
                { value: 'low', label: 'Low Priority' },
              ]}
              onChange={setPriorityFilter}
            />
          </div>
        </div>
        
        <div className="p-4">
          <DataTable
            columns={[
              { 
                key: 'id', 
                header: 'ID',
                width: '120px',
                render: (row: any) => (
                  <span className="font-mono text-caption text-primary-600">{row.id}</span>
                )
              },
              { 
                key: 'title', 
                header: 'Task',
                render: (row: any) => (
                  <div>
                    <p className="text-body font-medium text-text-primary">{row.title}</p>
                    <p className="text-caption text-text-tertiary flex items-center gap-1 mt-0.5">
                      <MapPin className="w-3 h-3" /> {row.dma}
                    </p>
                  </div>
                )
              },
              {
                key: 'priority',
                header: 'Priority',
                width: '100px',
                render: (row: any) => getPriorityBadge(row.priority)
              },
              {
                key: 'status',
                header: 'Status',
                width: '120px',
                render: (row: any) => getStatusBadge(row.status)
              },
              {
                key: 'assignee',
                header: 'Assignee',
                width: '120px',
                render: (row: any) => (
                  <span className={row.assignee === 'Unassigned' ? 'text-text-tertiary italic' : 'text-text-primary'}>
                    {row.assignee}
                  </span>
                )
              },
              {
                key: 'due_date',
                header: 'Due',
                width: '100px',
                render: (row: any) => {
                  const isOverdue = row.status !== 'completed' && new Date(row.due_date) < new Date()
                  return (
                    <span className={isOverdue ? 'text-status-red font-medium' : 'text-text-secondary'}>
                      {formatRelativeTime(row.due_date)}
                    </span>
                  )
                }
              },
              {
                key: 'source',
                header: 'Source',
                width: '140px',
                render: (row: any) => (
                  <span className={`text-caption ${row.source === 'AI Detection' ? 'text-primary-600' : 'text-text-secondary'}`}>
                    {row.source}
                  </span>
                )
              },
              {
                key: 'actions',
                header: '',
                width: '80px',
                render: (row: any) => (
                  <Button variant="ghost" size="sm" onClick={() => setSelectedWorkOrder(row)}>View</Button>
                )
              }
            ]}
            data={filteredOrders}
            keyExtractor={(row: any) => row.id}
            onRowClick={(row: any) => setSelectedWorkOrder(row)}
          />
        </div>
      </SectionCard>
      
      {/* Create Work Order Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => !isSubmitting && setShowCreateModal(false)}>
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg mx-4" onClick={e => e.stopPropagation()}>
            {showSuccess ? (
              // Success State
              <div className="p-8 text-center">
                <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <CheckCircle className="w-8 h-8 text-emerald-600" />
                </div>
                <h2 className="text-xl font-bold text-slate-900 mb-2">Work Order Created!</h2>
                <p className="text-slate-600 mb-4">The work order has been sent to the assigned team.</p>
                <p className="text-sm text-emerald-600 font-medium">Technicians will receive a notification</p>
              </div>
            ) : (
              <>
                <div className="flex items-center justify-between p-4 border-b border-slate-200 bg-gradient-to-r from-blue-600 to-cyan-600">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-white/20 rounded-lg flex items-center justify-center">
                      <Plus className="w-5 h-5 text-white" />
                    </div>
                    <div>
                      <h2 className="text-lg font-bold text-white">Create Work Order</h2>
                      <p className="text-blue-100 text-sm">Assign task to field team</p>
                    </div>
                  </div>
                  <button onClick={() => setShowCreateModal(false)} className="p-2 hover:bg-white/20 rounded-lg transition-colors" disabled={isSubmitting}>
                    <X className="w-5 h-5 text-white" />
                  </button>
                </div>
                <div className="p-4 space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">Title <span className="text-red-500">*</span></label>
                    <input 
                      type="text" 
                      placeholder="e.g., Investigate suspected leak at Junction Rd" 
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      value={formData.title}
                      onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                      disabled={isSubmitting}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">DMA <span className="text-red-500">*</span></label>
                    <select 
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      value={formData.dma}
                      onChange={(e) => setFormData({ ...formData, dma: e.target.value })}
                      disabled={isSubmitting}
                    >
                      <option value="">Select DMA...</option>
                      <option value="Kabulonga North">Kabulonga North</option>
                      <option value="Woodlands Central">Woodlands Central</option>
                      <option value="Roma Industrial">Roma Industrial</option>
                      <option value="Matero West">Matero West</option>
                      <option value="Chilenje South">Chilenje South</option>
                    </select>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">Priority</label>
                      <select 
                        className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        value={formData.priority}
                        onChange={(e) => setFormData({ ...formData, priority: e.target.value as 'high' | 'medium' | 'low' })}
                        disabled={isSubmitting}
                      >
                        <option value="high">🔴 High - Urgent</option>
                        <option value="medium">🟡 Medium</option>
                        <option value="low">🟢 Low</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">Assign To</label>
                      <select 
                        className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        value={formData.assignee}
                        onChange={(e) => setFormData({ ...formData, assignee: e.target.value })}
                        disabled={isSubmitting}
                      >
                        <option value="Unassigned">Unassigned</option>
                        <option value="Team Alpha">Team Alpha</option>
                        <option value="Team Beta">Team Beta</option>
                        <option value="Team Gamma">Team Gamma</option>
                      </select>
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">Estimated Water Loss (m³/day)</label>
                    <input 
                      type="number" 
                      placeholder="0" 
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      value={formData.estimated_loss || ''}
                      onChange={(e) => setFormData({ ...formData, estimated_loss: parseInt(e.target.value) || 0 })}
                      disabled={isSubmitting}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">Description</label>
                    <textarea 
                      rows={3} 
                      placeholder="Provide details about the task, location specifics, safety concerns..." 
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      value={formData.description}
                      onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                      disabled={isSubmitting}
                    />
                  </div>
                </div>
                <div className="flex items-center justify-between gap-3 p-4 border-t border-slate-200 bg-slate-50">
                  <p className="text-xs text-slate-500">
                    <span className="text-red-500">*</span> Required fields
                  </p>
                  <div className="flex gap-3">
                    <Button variant="secondary" onClick={() => setShowCreateModal(false)} disabled={isSubmitting}>
                      Cancel
                    </Button>
                    <button 
                      className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all ${
                        isSubmitting 
                          ? 'bg-blue-400 text-white cursor-not-allowed' 
                          : 'bg-blue-600 hover:bg-blue-700 text-white'
                      }`}
                      onClick={createWorkOrder}
                      disabled={isSubmitting}
                    >
                      {isSubmitting ? (
                        <>
                          <Loader2 className="w-4 h-4 animate-spin" />
                          Sending...
                        </>
                      ) : (
                        <>
                          <Send className="w-4 h-4" />
                          Create & Send
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      )}
      
      {/* View Work Order Modal */}
      {selectedWorkOrder && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setSelectedWorkOrder(null)}>
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg mx-4" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between p-4 border-b border-slate-200">
              <div>
                <h2 className="text-lg font-bold text-slate-900">{selectedWorkOrder.title}</h2>
                <p className="text-sm text-slate-500 font-mono">{selectedWorkOrder.id}</p>
              </div>
              <button onClick={() => setSelectedWorkOrder(null)} className="p-1 hover:bg-slate-100 rounded-lg transition-colors">
                <X className="w-5 h-5 text-slate-500" />
              </button>
            </div>
            <div className="p-4 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-xs text-slate-500 uppercase mb-1">DMA</p>
                  <p className="text-sm font-medium text-slate-900">{selectedWorkOrder.dma}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500 uppercase mb-1">Status</p>
                  {getStatusBadge(selectedWorkOrder.status)}
                </div>
                <div>
                  <p className="text-xs text-slate-500 uppercase mb-1">Priority</p>
                  {getPriorityBadge(selectedWorkOrder.priority)}
                </div>
                <div>
                  <p className="text-xs text-slate-500 uppercase mb-1">Assignee</p>
                  <p className="text-sm font-medium text-slate-900">{selectedWorkOrder.assignee}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500 uppercase mb-1">Est. Loss</p>
                  <p className="text-sm font-medium text-slate-900">{selectedWorkOrder.estimated_loss} m³/day</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500 uppercase mb-1">Source</p>
                  <p className="text-sm font-medium text-slate-900">{selectedWorkOrder.source}</p>
                </div>
              </div>
            </div>
            <div className="flex items-center justify-end gap-3 p-4 border-t border-slate-200 bg-slate-50">
              <Button variant="secondary" onClick={() => setSelectedWorkOrder(null)}>Close</Button>
              <Button variant="primary" onClick={() => { setSelectedWorkOrder(null); alert('Work order updated!'); }}>Update Status</Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
