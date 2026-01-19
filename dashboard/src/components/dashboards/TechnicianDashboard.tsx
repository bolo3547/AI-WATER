'use client'

import { useState, useEffect, useCallback } from 'react'
import Link from 'next/link'
import { 
  MapPin, Clock, AlertTriangle, CheckCircle2, 
  Wrench, Navigation, Phone, Camera, FileText,
  ChevronRight, Circle, Play, CheckSquare, Timer,
  Truck, User, Calendar, ArrowRight, Bell, MessageSquare,
  Send, X, Upload, Image, Paperclip, AlertCircle,
  RefreshCw, Signal, Battery, ThermometerSun, Droplets,
  ClipboardList, Award, TrendingUp, Zap, Radio, Inbox
} from 'lucide-react'
import { formatRelativeTime } from '@/lib/api'
import { SectionCard } from '@/components/ui/Cards'

interface WorkOrder {
  id: string
  type: string
  priority: 'high' | 'medium' | 'low' | 'emergency'
  location: string
  address: string
  description: string
  status: 'assigned' | 'in-progress' | 'completed' | 'on-hold'
  dueDate: string
  estimatedTime: string
  assignedAt: string
  assignedBy: { name: string; role: string }
  startedAt?: string
  completedAt?: string
  coordinates: { lat: number; lng: number }
  notes?: string[]
  photos?: string[]
  parts?: { name: string; quantity: number }[]
}

interface Notification {
  id: string
  type: 'task' | 'message' | 'alert' | 'update'
  title: string
  message: string
  from: { name: string; role: string }
  timestamp: string
  read: boolean
  actionUrl?: string
  priority?: 'high' | 'normal'
}

interface Message {
  id: string
  from: { name: string; role: string }
  to: string
  content: string
  timestamp: string
  read: boolean
  workOrderId?: string
}

export function TechnicianDashboard() {
  const [currentTime, setCurrentTime] = useState(new Date())
  const [workOrders, setWorkOrders] = useState<WorkOrder[]>([])
  const [completedOrders, setCompletedOrders] = useState<WorkOrder[]>([])
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [messages, setMessages] = useState<Message[]>([])
  const [showNotifications, setShowNotifications] = useState(false)
  const [showMessages, setShowMessages] = useState(false)
  const [showReportModal, setShowReportModal] = useState(false)
  const [selectedTask, setSelectedTask] = useState<WorkOrder | null>(null)
  const [reportText, setReportText] = useState('')
  const [messageInput, setMessageInput] = useState('')
  const [activeChat, setActiveChat] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  
  // Calculate stats from REAL data only
  const stats = {
    assigned: workOrders.filter(w => w.status === 'assigned').length,
    inProgress: workOrders.filter(w => w.status === 'in-progress').length,
    completedToday: completedOrders.length,
    avgRating: '0'
  }

  const unreadNotifications = notifications.filter(n => !n.read).length
  const unreadMessages = messages.filter(m => !m.read).length
  
  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000)
    return () => clearInterval(timer)
  }, [])

  // Load data from REAL API only - NO mock data
  const fetchWorkOrders = useCallback(async () => {
    try {
      const response = await fetch('/api/work-orders')
      const data = await response.json()
      
      if (data.success && data.data) {
        // Convert API work orders to TechnicianDashboard format
        const apiOrders: WorkOrder[] = data.data.map((order: any) => ({
          id: order.id,
          type: order.source || 'Work Order',
          priority: order.priority as any,
          location: order.dma,
          address: order.title,
          description: order.description || order.title,
          status: order.status === 'pending' ? 'assigned' : order.status === 'in_progress' ? 'in-progress' : order.status === 'completed' ? 'completed' : 'assigned',
          dueDate: order.due_date,
          estimatedTime: '2-3 hours',
          assignedAt: order.created_at,
          assignedBy: { name: order.created_by || order.assignee || 'Control Room', role: 'Admin' },
          coordinates: { lat: -15.4167, lng: 28.2833 },
          notes: order.notes ? [order.notes] : []
        }))
        
        // Separate active and completed orders
        const active = apiOrders.filter(o => o.status !== 'completed')
        const completed = apiOrders.filter(o => o.status === 'completed')
        
        setWorkOrders(active)
        setCompletedOrders(completed)
        
        // Create notifications for new pending orders
        const newNotifs: Notification[] = active
          .filter(o => o.status === 'assigned')
          .map(order => ({
            id: `notif-${order.id}`,
            type: 'task' as const,
            title: `📋 New Task: ${order.type}`,
            message: order.description.substring(0, 100),
            from: order.assignedBy,
            timestamp: order.assignedAt,
            read: false,
            priority: order.priority === 'high' || order.priority === 'emergency' ? 'high' as const : 'normal' as const
          }))
        
        setNotifications(newNotifs)
      } else {
        // No data - show empty state
        setWorkOrders([])
        setCompletedOrders([])
        setNotifications([])
      }
    } catch (error) {
      console.error('Failed to fetch work orders:', error)
      setWorkOrders([])
      setCompletedOrders([])
      setNotifications([])
    }
    
    setMessages([])
    setLoading(false)
  }, [])

  useEffect(() => {
    fetchWorkOrders()
    const pollInterval = setInterval(fetchWorkOrders, 10000)
    return () => clearInterval(pollInterval)
  }, [fetchWorkOrders])

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'emergency': return 'bg-red-600 text-white border-red-600 animate-pulse'
      case 'high': return 'bg-red-100 text-red-700 border-red-200'
      case 'medium': return 'bg-amber-100 text-amber-700 border-amber-200'
      case 'low': return 'bg-blue-100 text-blue-700 border-blue-200'
      default: return 'bg-slate-100 text-slate-700 border-slate-200'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'assigned': return <Circle className="w-4 h-4 text-blue-500" />
      case 'in-progress': return <Play className="w-4 h-4 text-amber-500" />
      case 'completed': return <CheckCircle2 className="w-4 h-4 text-emerald-500" />
      case 'on-hold': return <AlertCircle className="w-4 h-4 text-orange-500" />
      default: return <Circle className="w-4 h-4 text-slate-400" />
    }
  }

  const handleStartTask = async (wo: WorkOrder) => {
    try {
      await fetch('/api/work-orders', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          id: wo.id,
          status: 'in_progress',
          notes: `Task started by technician at ${new Date().toLocaleTimeString()}`
        })
      })
      
      setWorkOrders(prev => prev.map(w => 
        w.id === wo.id ? { ...w, status: 'in-progress', startedAt: new Date().toISOString() } : w
      ))
    } catch (e) {
      console.error('Failed to update work order:', e)
    }
  }

  const handleCompleteTask = (wo: WorkOrder) => {
    setSelectedTask(wo)
    setShowReportModal(true)
  }

  const handleSubmitReport = async () => {
    if (selectedTask) {
      try {
        await fetch('/api/work-orders', {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            id: selectedTask.id,
            status: 'completed',
            notes: reportText || 'Task completed successfully'
          })
        })
        
        const completedTask = { 
          ...selectedTask, 
          status: 'completed' as const, 
          completedAt: new Date().toISOString() 
        }
        
        setWorkOrders(prev => prev.filter(w => w.id !== selectedTask.id))
        setCompletedOrders(prev => [completedTask, ...prev])
        
      } catch (e) {
        console.error('Failed to update work order:', e)
      }
      
      setShowReportModal(false)
      setSelectedTask(null)
      setReportText('')
    }
  }

  const handleSendMessage = async (toRole: string) => {
    if (!messageInput.trim()) return
    
    const newMsg: Message = {
      id: `msg-${Date.now()}`,
      from: { name: 'You', role: 'Technician' },
      to: toRole,
      content: messageInput,
      timestamp: new Date().toISOString(),
      read: true,
      workOrderId: activeChat || undefined
    }
    
    try {
      const user = typeof window !== 'undefined' ? JSON.parse(localStorage.getItem('user') || '{}') : {}
      await fetch('/api/messages', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          from_user: user.username || 'technician',
          to_user: toRole,
          content: messageInput,
          work_order_id: activeChat || undefined
        })
      })
    } catch (e) {
      console.error('Failed to send message:', e)
    }
    
    setMessages(prev => [...prev, newMsg])
    setMessageInput('')
  }

  const markNotificationsRead = () => {
    setNotifications(prev => prev.map(n => ({ ...n, read: true })))
  }

  const currentTask = workOrders.find(wo => wo.status === 'in-progress')
  const emergencyTasks = workOrders.filter(wo => wo.priority === 'emergency' && wo.status === 'assigned')
  const assignedTasks = workOrders.filter(wo => wo.status === 'assigned')

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <RefreshCw className="w-10 h-10 animate-spin text-orange-600 mx-auto mb-4" />
          <p className="text-slate-600">Loading work orders...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Emergency Alert Banner - only if real emergency tasks exist */}
      {emergencyTasks.length > 0 && (
        <div className="bg-gradient-to-r from-red-600 to-red-700 rounded-xl p-3 sm:p-4 text-white animate-pulse">
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3 sm:gap-4">
            <div className="w-10 h-10 sm:w-12 sm:h-12 bg-white/20 rounded-full flex items-center justify-center flex-shrink-0">
              <AlertTriangle className="w-5 sm:w-7 h-5 sm:h-7" />
            </div>
            <div className="flex-1">
              <h3 className="font-bold text-base sm:text-lg">🚨 EMERGENCY TASK</h3>
              <p className="text-red-100 text-sm">{emergencyTasks[0].type} at {emergencyTasks[0].location}</p>
            </div>
            <button 
              onClick={() => handleStartTask(emergencyTasks[0])}
              className="w-full sm:w-auto px-4 sm:px-6 py-2 sm:py-3 bg-white text-red-600 font-bold rounded-lg hover:bg-red-50 transition-colors text-sm sm:text-base"
            >
              RESPOND NOW
            </button>
          </div>
        </div>
      )}

      {/* Technician Hero Section */}
      <div className="relative overflow-hidden rounded-xl sm:rounded-2xl bg-gradient-to-br from-orange-800 via-slate-800 to-slate-900 p-4 sm:p-6 text-white">
        <div className="absolute inset-0 bg-[url('/grid.svg')] opacity-10" />
        <div className="absolute top-0 right-0 w-64 h-64 bg-orange-500/20 rounded-full blur-3xl" />
        
        <div className="relative z-10">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 sm:gap-0 mb-4 sm:mb-6">
            <div>
              <div className="flex flex-wrap items-center gap-2 sm:gap-3 mb-2">
                <div className="px-2 sm:px-3 py-1 bg-orange-500/20 rounded-full border border-orange-400/30">
                  <span className="text-[10px] sm:text-xs font-semibold text-orange-300 uppercase tracking-wider">Field Tech</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" />
                  <span className="text-[10px] sm:text-xs text-emerald-400 uppercase">On Duty</span>
                </div>
              </div>
              <h1 className="text-xl sm:text-2xl font-bold">My Work Orders</h1>
              <p className="text-slate-400 text-xs sm:text-sm">Real-time task assignments</p>
            </div>
            <div className="text-left sm:text-right">
              <div className="text-xl sm:text-3xl font-mono font-bold text-white/90">
                {currentTime.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}
              </div>
              <div className="text-[10px] sm:text-xs text-slate-400 mt-1">
                {currentTime.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}
              </div>
            </div>
          </div>
          
          {/* Quick Stats - Responsive Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 sm:gap-4">
            <div className="bg-white/5 backdrop-blur rounded-lg sm:rounded-xl p-3 sm:p-4 border border-white/10">
              <div className="flex items-center gap-1.5 sm:gap-2 mb-1 sm:mb-2">
                <ClipboardList className="w-4 sm:w-5 h-4 sm:h-5 text-blue-400" />
                <span className="text-[10px] sm:text-xs text-slate-400">Assigned</span>
              </div>
              <div className="text-lg sm:text-2xl font-bold">{stats.assigned}</div>
            </div>
            
            <div className="bg-white/5 backdrop-blur rounded-lg sm:rounded-xl p-3 sm:p-4 border border-white/10">
              <div className="flex items-center gap-1.5 sm:gap-2 mb-1 sm:mb-2">
                <Play className="w-4 sm:w-5 h-4 sm:h-5 text-amber-400" />
                <span className="text-[10px] sm:text-xs text-slate-400">In Progress</span>
              </div>
              <div className="text-lg sm:text-2xl font-bold text-amber-400">{stats.inProgress}</div>
            </div>
            
            <div className="bg-white/5 backdrop-blur rounded-lg sm:rounded-xl p-3 sm:p-4 border border-white/10">
              <div className="flex items-center gap-1.5 sm:gap-2 mb-1 sm:mb-2">
                <CheckCircle2 className="w-4 sm:w-5 h-4 sm:h-5 text-emerald-400" />
                <span className="text-[10px] sm:text-xs text-slate-400">Completed</span>
              </div>
              <div className="text-lg sm:text-2xl font-bold text-emerald-400">{stats.completedToday}</div>
            </div>
            
            <div className="bg-white/5 backdrop-blur rounded-lg sm:rounded-xl p-3 sm:p-4 border border-white/10">
              <div className="flex items-center gap-1.5 sm:gap-2 mb-1 sm:mb-2">
                <Bell className="w-4 sm:w-5 h-4 sm:h-5 text-purple-400" />
                <span className="text-[10px] sm:text-xs text-slate-400">Alerts</span>
              </div>
              <div className="text-lg sm:text-2xl font-bold">{unreadNotifications}</div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content Grid - Responsive */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6">
        {/* Current Task */}
        <div className="lg:col-span-2 space-y-4 sm:space-y-6">
          {currentTask ? (
            <SectionCard 
              title="Currently Working On"
              subtitle={`Started ${formatRelativeTime(currentTask.startedAt || currentTask.assignedAt)}`}
            >
              <div className="p-1">
                <div className="flex items-start gap-4">
                  <div className={`w-14 h-14 rounded-xl flex items-center justify-center ${getPriorityColor(currentTask.priority)}`}>
                    <Wrench className="w-7 h-7" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-bold text-slate-900">{currentTask.id}</span>
                      <span className={`px-2 py-0.5 text-xs font-semibold rounded-full ${getPriorityColor(currentTask.priority)}`}>
                        {currentTask.priority.toUpperCase()}
                      </span>
                    </div>
                    <p className="text-sm text-slate-500 mb-1">Assigned by {currentTask.assignedBy.name}</p>
                    <h3 className="text-lg font-semibold text-slate-900">{currentTask.type}</h3>
                    <p className="text-slate-600 mt-1">{currentTask.description}</p>
                    
                    <div className="flex items-center gap-4 mt-4 text-sm text-slate-500">
                      <span className="flex items-center gap-1">
                        <MapPin className="w-4 h-4" />
                        {currentTask.address}
                      </span>
                      <span className="flex items-center gap-1">
                        <Timer className="w-4 h-4" />
                        Est. {currentTask.estimatedTime}
                      </span>
                    </div>
                    
                    {currentTask.notes && currentTask.notes.length > 0 && (
                      <div className="mt-4 bg-amber-50 rounded-lg p-3 border border-amber-200">
                        <p className="text-xs font-semibold text-amber-700 mb-1">Notes from Control:</p>
                        <ul className="text-sm text-amber-800">
                          {currentTask.notes.map((note, i) => (
                            <li key={i}>• {note}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    
                    <div className="flex flex-col sm:flex-row gap-2 sm:gap-3 mt-4 sm:mt-6">
                      <button 
                        onClick={() => handleCompleteTask(currentTask)}
                        className="flex-1 px-3 sm:px-4 py-2.5 sm:py-3 bg-emerald-600 text-white font-semibold rounded-lg sm:rounded-xl hover:bg-emerald-700 transition-colors flex items-center justify-center gap-2 text-sm sm:text-base"
                      >
                        <CheckCircle2 className="w-4 sm:w-5 h-4 sm:h-5" />
                        Complete & Report
                      </button>
                      <button className="px-3 sm:px-4 py-2.5 sm:py-3 bg-slate-100 text-slate-700 font-semibold rounded-lg sm:rounded-xl hover:bg-slate-200 transition-colors flex items-center justify-center gap-2 text-sm sm:text-base">
                        <Camera className="w-4 sm:w-5 h-4 sm:h-5" />
                        <span className="sm:inline">Photo</span>
                      </button>
                      <button className="px-3 sm:px-4 py-2.5 sm:py-3 bg-slate-100 text-slate-700 font-semibold rounded-lg sm:rounded-xl hover:bg-slate-200 transition-colors flex items-center justify-center gap-2 text-sm sm:text-base">
                        <MessageSquare className="w-4 sm:w-5 h-4 sm:h-5" />
                        <span className="sm:inline">Message</span>
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </SectionCard>
          ) : (
            <SectionCard 
              title="No Active Task"
              subtitle="Start a task from your assigned work orders"
            >
              <div className="p-8 text-center">
                <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Inbox className="w-8 h-8 text-slate-400" />
                </div>
                <h3 className="text-lg font-semibold text-slate-700 mb-2">Ready for Tasks</h3>
                <p className="text-slate-500">
                  {assignedTasks.length > 0 
                    ? `You have ${assignedTasks.length} task(s) waiting. Start one below.`
                    : 'No tasks assigned. Check back later or contact Control Room.'}
                </p>
              </div>
            </SectionCard>
          )}

          {/* Assigned Work Orders */}
          <SectionCard 
            title="Assigned Work Orders"
            subtitle={assignedTasks.length > 0 ? "Tasks from Admin & Operators" : "No tasks assigned"}
            action={
              <button onClick={fetchWorkOrders} className="text-sm text-orange-600 hover:text-orange-700 font-medium flex items-center gap-1">
                <RefreshCw className="w-4 h-4" />
                Refresh
              </button>
            }
            noPadding
          >
            {assignedTasks.length === 0 ? (
              <div className="p-8 text-center">
                <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <CheckCircle2 className="w-8 h-8 text-emerald-600" />
                </div>
                <h3 className="text-lg font-semibold text-slate-900 mb-2">All Caught Up!</h3>
                <p className="text-slate-500 max-w-md mx-auto">
                  No pending work orders. New tasks will appear here when assigned by Control Room.
                </p>
              </div>
            ) : (
              <div className="divide-y divide-slate-100">
                {assignedTasks.map((wo) => (
                  <div key={wo.id} className="p-4 hover:bg-slate-50/50 transition-colors">
                    <div className="flex items-start gap-4">
                      <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${getPriorityColor(wo.priority)}`}>
                        {wo.priority === 'emergency' ? (
                          <AlertTriangle className="w-6 h-6" />
                        ) : (
                          <Wrench className="w-6 h-6" />
                        )}
                      </div>
                      
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-bold text-slate-900">{wo.id}</span>
                          <span className={`px-2 py-0.5 text-xs font-semibold rounded-full ${getPriorityColor(wo.priority)}`}>
                            {wo.priority === 'emergency' ? '🚨 EMERGENCY' : wo.priority.toUpperCase()}
                          </span>
                        </div>
                        <p className="text-xs text-slate-500">{wo.assignedBy.name} ({wo.assignedBy.role})</p>
                        <h4 className="font-semibold text-slate-900 mt-1">{wo.type}</h4>
                        <p className="text-sm text-slate-600 line-clamp-2">{wo.description}</p>
                        
                        <div className="flex items-center gap-4 mt-2 text-xs text-slate-500">
                          <span className="flex items-center gap-1">
                            <MapPin className="w-3 h-3" />
                            {wo.location}
                          </span>
                          <span className="flex items-center gap-1">
                            <Timer className="w-3 h-3" />
                            Est. {wo.estimatedTime}
                          </span>
                          <span className="flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            Due: {new Date(wo.dueDate).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}
                          </span>
                        </div>
                        
                        {wo.parts && wo.parts.length > 0 && (
                          <div className="mt-2 text-xs text-slate-500">
                            <span className="font-medium">Parts needed: </span>
                            {wo.parts.map((p, i) => (
                              <span key={i}>{p.name} x{p.quantity}{i < wo.parts!.length - 1 ? ', ' : ''}</span>
                            ))}
                          </div>
                        )}
                        
                        <div className="flex gap-2 mt-3">
                          <button 
                            onClick={() => handleStartTask(wo)}
                            className={`px-4 py-2 font-semibold rounded-lg transition-colors flex items-center gap-1 ${
                              wo.priority === 'emergency' 
                                ? 'bg-red-600 text-white hover:bg-red-700' 
                                : 'bg-orange-600 text-white hover:bg-orange-700'
                            }`}
                          >
                            <Play className="w-4 h-4" />
                            Start Task
                          </button>
                          <button className="px-3 py-2 bg-slate-100 text-slate-700 font-medium rounded-lg hover:bg-slate-200 transition-colors flex items-center gap-1">
                            <Navigation className="w-4 h-4" />
                            Navigate
                          </button>
                          <button className="px-3 py-2 bg-slate-100 text-slate-700 font-medium rounded-lg hover:bg-slate-200 transition-colors flex items-center gap-1">
                            <MessageSquare className="w-4 h-4" />
                            Ask Question
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </SectionCard>
        </div>

        {/* Side Panel */}
        <div className="space-y-6">
          {/* Quick Actions */}
          <SectionCard title="Quick Actions" noPadding>
            <div className="grid grid-cols-2 gap-2 p-4">
              <Link href="/dma" className="p-4 bg-slate-50 rounded-xl hover:bg-slate-100 transition-colors text-center block">
                <MapPin className="w-6 h-6 text-blue-600 mx-auto mb-2" />
                <span className="text-sm font-medium text-slate-700">Field Map</span>
                <p className="text-xs text-slate-500 mt-1">Work locations</p>
              </Link>
              <Link href="/health" className="p-4 bg-slate-50 rounded-xl hover:bg-slate-100 transition-colors text-center block">
                <Radio className="w-6 h-6 text-emerald-600 mx-auto mb-2" />
                <span className="text-sm font-medium text-slate-700">Equipment</span>
                <p className="text-xs text-slate-500 mt-1">Sensor status</p>
              </Link>
              <Link href="/ai" className="p-4 bg-slate-50 rounded-xl hover:bg-slate-100 transition-colors text-center block">
                <FileText className="w-6 h-6 text-purple-600 mx-auto mb-2" />
                <span className="text-sm font-medium text-slate-700">Knowledge Base</span>
                <p className="text-xs text-slate-500 mt-1">Repair guides</p>
              </Link>
              <button 
                onClick={() => setShowReportModal(true)}
                className="p-4 bg-slate-50 rounded-xl hover:bg-slate-100 transition-colors text-center"
              >
                <AlertCircle className="w-6 h-6 text-red-600 mx-auto mb-2" />
                <span className="text-sm font-medium text-slate-700">Report Issue</span>
                <p className="text-xs text-slate-500 mt-1">Field problems</p>
              </button>
            </div>
          </SectionCard>

          {/* Completed Today */}
          <SectionCard 
            title="Completed Today"
            subtitle="Tasks finished this shift"
            noPadding
          >
            {completedOrders.length === 0 ? (
              <div className="p-6 text-center">
                <div className="w-12 h-12 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-3">
                  <CheckSquare className="w-6 h-6 text-slate-400" />
                </div>
                <p className="text-sm text-slate-500">No completed tasks yet</p>
              </div>
            ) : (
              <div className="divide-y divide-slate-100">
                {completedOrders.map((wo) => (
                  <div key={wo.id} className="p-4 hover:bg-slate-50/50 transition-colors">
                    <div className="flex items-center gap-3">
                      <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-slate-900">{wo.id}</span>
                          <span className="text-sm text-slate-600">{wo.type}</span>
                        </div>
                        <p className="text-sm text-slate-500">{wo.location}</p>
                      </div>
                      <span className="text-sm text-slate-400">{formatRelativeTime(wo.completedAt || wo.assignedAt)}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </SectionCard>
        </div>
      </div>
      
      {/* Footer */}
      <div className="flex items-center justify-between py-3 px-5 bg-orange-50 rounded-xl border border-orange-200">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <User className="w-4 h-4 text-orange-600" />
            <span className="text-sm font-medium text-orange-700">Field Tech Session Active</span>
          </div>
          <div className="h-4 w-px bg-orange-300" />
          <span className="flex items-center gap-1 text-sm text-slate-600">
            <Signal className="w-4 h-4 text-emerald-500" />
            GPS Active
          </span>
          <span className="flex items-center gap-1 text-sm text-slate-600">
            <Battery className="w-4 h-4 text-emerald-500" />
            Connected
          </span>
        </div>
        <div className="flex items-center gap-3 text-sm text-slate-500">
          <span>Emergency Line: <strong className="text-red-600">211</strong></span>
        </div>
      </div>

      {/* Completion Report Modal */}
      {showReportModal && selectedTask && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg overflow-hidden">
            <div className="bg-gradient-to-r from-emerald-600 to-green-600 p-5 text-white">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-xl font-bold">Complete Task</h2>
                  <p className="text-emerald-100 text-sm">{selectedTask.id} - {selectedTask.type}</p>
                </div>
                <button onClick={() => setShowReportModal(false)} className="p-2 hover:bg-white/20 rounded-lg">
                  <X className="w-6 h-6" />
                </button>
              </div>
            </div>
            
            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-2">Completion Report *</label>
                <textarea
                  value={reportText}
                  onChange={(e) => setReportText(e.target.value)}
                  placeholder="Describe work completed, any issues found, materials used..."
                  className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500/50 h-32 resize-none"
                />
              </div>
              
              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-2">Attach Photos</label>
                <div className="border-2 border-dashed border-slate-200 rounded-xl p-6 text-center hover:border-emerald-500 transition-colors cursor-pointer">
                  <Upload className="w-8 h-8 text-slate-400 mx-auto mb-2" />
                  <p className="text-sm text-slate-500">Click to upload or drag photos</p>
                  <p className="text-xs text-slate-400 mt-1">Before/after photos recommended</p>
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-semibold text-slate-700 mb-2">Materials Used</label>
                  <input
                    type="text"
                    placeholder="e.g., 2x pipe clamps"
                    className="w-full px-4 py-2 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500/50"
                  />
                </div>
                <div>
                  <label className="block text-sm font-semibold text-slate-700 mb-2">Time Spent</label>
                  <input
                    type="text"
                    placeholder="e.g., 2.5 hours"
                    className="w-full px-4 py-2 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500/50"
                  />
                </div>
              </div>
              
              <div className="flex gap-3 pt-4">
                <button
                  onClick={() => setShowReportModal(false)}
                  className="flex-1 py-3 border border-slate-200 text-slate-700 rounded-xl font-semibold hover:bg-slate-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSubmitReport}
                  disabled={!reportText.trim()}
                  className="flex-1 py-3 bg-emerald-600 text-white rounded-xl font-semibold hover:bg-emerald-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  <CheckCircle2 className="w-5 h-5" />
                  Submit Report
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
