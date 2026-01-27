'use client'

import { useState, useEffect, useRef } from 'react'
import Link from 'next/link'
import useSWR from 'swr'
import {
  MessageCircle, Send, Clock, CheckCircle, AlertTriangle,
  MapPin, Calendar, User, Search, Filter, RefreshCw,
  Loader2, ChevronRight, Phone, Mail, ExternalLink,
  CheckCheck, XCircle, Users, Wrench, Eye, Droplets
} from 'lucide-react'

const fetcher = (url: string) => fetch(url).then(res => res.json())

interface Report {
  _id: string
  id: string
  ticket: string
  ticket_number: string
  category: string
  description: string | null
  area_text: string | null
  latitude: number | null
  longitude: number | null
  reporter_name: string | null
  reporter_phone: string | null
  reporter_email: string | null
  status: string
  severity: string
  created_at: string
  updated_at: string
  assigned_to?: string
  timeline: Array<{ status: string; message: string; timestamp: string }>
  status_history?: Array<{ status: string; message: string; timestamp: string }>
}

interface Message {
  _id: string
  ticket_id: string
  sender_type: 'staff' | 'public'
  sender_name?: string
  content: string
  created_at: string
  read: boolean
}

interface Technician {
  _id: string
  user_id: string
  name: string
  phone?: string
  role: string
  status: string
  skills: string[]
}

const statusConfig: Record<string, { label: string; color: string; bgColor: string; icon: any }> = {
  'received': { label: 'New', color: 'text-blue-400', bgColor: 'bg-blue-500/20', icon: MessageCircle },
  'under_review': { label: 'Under Review', color: 'text-amber-400', bgColor: 'bg-amber-500/20', icon: Eye },
  'technician_assigned': { label: 'Team Assigned', color: 'text-purple-400', bgColor: 'bg-purple-500/20', icon: Users },
  'in_progress': { label: 'In Progress', color: 'text-cyan-400', bgColor: 'bg-cyan-500/20', icon: Wrench },
  'resolved': { label: 'Resolved', color: 'text-emerald-400', bgColor: 'bg-emerald-500/20', icon: CheckCircle },
  'closed': { label: 'Closed', color: 'text-slate-400', bgColor: 'bg-slate-500/20', icon: XCircle },
}

const severityConfig: Record<string, { label: string; color: string; bgColor: string }> = {
  'critical': { label: 'Critical', color: 'text-red-400', bgColor: 'bg-red-500/20' },
  'high': { label: 'High', color: 'text-orange-400', bgColor: 'bg-orange-500/20' },
  'medium': { label: 'Medium', color: 'text-amber-400', bgColor: 'bg-amber-500/20' },
  'low': { label: 'Low', color: 'text-slate-400', bgColor: 'bg-slate-500/20' },
}

const categoryConfig: Record<string, { name: string; icon: string }> = {
  'leak': { name: 'Water Leak', icon: '💧' },
  'burst': { name: 'Burst Pipe', icon: '💦' },
  'no_water': { name: 'No Water', icon: '🚫' },
  'low_pressure': { name: 'Low Pressure', icon: '📉' },
  'illegal_connection': { name: 'Illegal Connection', icon: '⚠️' },
  'overflow': { name: 'Overflow', icon: '🌊' },
  'contamination': { name: 'Water Quality', icon: '☣️' },
  'other': { name: 'Other', icon: '❓' }
}

export default function TicketsPage() {
  const [selectedTicket, setSelectedTicket] = useState<Report | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [newMessage, setNewMessage] = useState('')
  const [sending, setSending] = useState(false)
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [updatingStatus, setUpdatingStatus] = useState(false)
  const [technicians, setTechnicians] = useState<Technician[]>([])
  const [showAssignModal, setShowAssignModal] = useState(false)
  const [selectedTechnician, setSelectedTechnician] = useState<string>('')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Fetch reports
  const { data, error, isLoading, mutate } = useSWR(
    `/api/public-reports?tenant_id=lwsc-zambia&page_size=50${statusFilter !== 'all' ? `&status=${statusFilter}` : ''}`,
    fetcher,
    { refreshInterval: 30000 }
  )

  const reports: Report[] = data?.items || []

  // Filter by search
  const filteredReports = reports.filter(report => {
    if (!searchQuery) return true
    const query = searchQuery.toLowerCase()
    const ticketNum = report.ticket_number || report.ticket || ''
    return (
      ticketNum.toLowerCase().includes(query) ||
      report.description?.toLowerCase().includes(query) ||
      report.area_text?.toLowerCase().includes(query) ||
      report.reporter_name?.toLowerCase().includes(query) ||
      report.reporter_phone?.includes(query)
    )
  })

  // Fetch technicians on mount
  useEffect(() => {
    fetchTechnicians()
  }, [])

  const fetchTechnicians = async () => {
    try {
      const response = await fetch('/api/technicians')
      if (response.ok) {
        const data = await response.json()
        setTechnicians(data.technicians || data || [])
      }
    } catch (error) {
      console.error('Failed to fetch technicians:', error)
    }
  }

  const handleAssignTechnician = async (technicianName: string) => {
    if (!selectedTicket || !technicianName) return

    setUpdatingStatus(true)
    try {
      const ticketId = selectedTicket.ticket_number || selectedTicket.ticket
      const response = await fetch(`/api/public-reports/${ticketId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          status: 'technician_assigned',
          assigned_to: technicianName
        })
      })

      if (response.ok) {
        mutate()
        setSelectedTicket(prev => prev ? { ...prev, status: 'technician_assigned', assigned_to: technicianName } : null)
        setShowAssignModal(false)
        setSelectedTechnician('')
      }
    } catch (error) {
      console.error('Failed to assign technician:', error)
    } finally {
      setUpdatingStatus(false)
    }
  }

  // Fetch messages when ticket is selected
  useEffect(() => {
    if (selectedTicket) {
      const ticketId = selectedTicket.ticket_number || selectedTicket.ticket
      fetchMessages(ticketId)
    }
  }, [selectedTicket])

  // Scroll to bottom of messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const fetchMessages = async (ticketId: string) => {
    try {
      const response = await fetch(`/api/ticket/${ticketId}`)
      if (response.ok) {
        const data = await response.json()
        setMessages(data.messages || [])
      }
    } catch (error) {
      console.error('Failed to fetch messages:', error)
    }
  }

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newMessage.trim() || !selectedTicket) return

    setSending(true)
    try {
      const userStr = localStorage.getItem('user')
      const user = userStr ? JSON.parse(userStr) : { username: 'Staff' }
      const ticketId = selectedTicket.ticket_number || selectedTicket.ticket

      const response = await fetch(`/api/ticket/${ticketId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content: newMessage,
          sender_type: 'staff',
          sender_name: user.username || 'LWSC Support',
          sender_id: user.id
        })
      })

      if (response.ok) {
        setNewMessage('')
        fetchMessages(ticketId)
      }
    } catch (error) {
      console.error('Failed to send message:', error)
    } finally {
      setSending(false)
    }
  }

  const handleStatusUpdate = async (newStatus: string) => {
    if (!selectedTicket) return

    setUpdatingStatus(true)
    try {
      const ticketId = selectedTicket.ticket_number || selectedTicket.ticket
      const response = await fetch(`/api/public-reports/${ticketId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus })
      })

      if (response.ok) {
        mutate()
        setSelectedTicket(prev => prev ? { ...prev, status: newStatus } : null)
      }
    } catch (error) {
      console.error('Failed to update status:', error)
    } finally {
      setUpdatingStatus(false)
    }
  }

  // Safe date formatting
  const formatDate = (dateString: string | undefined | null) => {
    if (!dateString) return 'N/A'
    try {
      const date = new Date(dateString)
      if (isNaN(date.getTime())) return 'N/A'
      return date.toLocaleDateString('en-ZM', {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    } catch {
      return 'N/A'
    }
  }

  const formatShortDate = (dateString: string | undefined | null) => {
    if (!dateString) return ''
    try {
      const date = new Date(dateString)
      if (isNaN(date.getTime())) return ''
      return date.toLocaleDateString('en-ZM', {
        day: 'numeric',
        month: 'short',
        hour: '2-digit',
        minute: '2-digit'
      })
    } catch {
      return ''
    }
  }

  const getTimeAgo = (dateString: string | undefined | null) => {
    if (!dateString) return ''
    try {
      const date = new Date(dateString)
      if (isNaN(date.getTime())) return ''
      const now = new Date()
      const diff = now.getTime() - date.getTime()
      const mins = Math.floor(diff / 60000)
      const hours = Math.floor(diff / 3600000)
      const days = Math.floor(diff / 86400000)

      if (mins < 1) return 'Just now'
      if (mins < 60) return `${mins}m ago`
      if (hours < 24) return `${hours}h ago`
      if (days < 7) return `${days}d ago`
      return formatShortDate(dateString)
    } catch {
      return ''
    }
  }

  // Get ticket display number
  const getTicketNumber = (report: Report) => report.ticket_number || report.ticket || 'N/A'

  // Stats
  const stats = {
    total: reports.length,
    new: reports.filter(r => r.status === 'received').length,
    inProgress: reports.filter(r => ['under_review', 'technician_assigned', 'in_progress'].includes(r.status)).length,
    resolved: reports.filter(r => r.status === 'resolved').length
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Header */}
      <header className="bg-slate-800/50 backdrop-blur-sm border-b border-white/10 sticky top-0 z-10">
        <div className="px-6 py-4">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-500/20 rounded-xl">
                <Droplets className="w-6 h-6 text-blue-400" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-white">Public Tickets</h1>
                <p className="text-slate-400 text-sm">Manage and respond to reports</p>
              </div>
            </div>
            <button
              onClick={() => mutate()}
              className="flex items-center justify-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-xl transition-all shadow-lg shadow-blue-500/20 hover:shadow-blue-500/40"
            >
              <RefreshCw className="w-4 h-4" />
              <span>Refresh</span>
            </button>
          </div>

          {/* Stats Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-5">
            <div className="bg-slate-700/50 backdrop-blur rounded-xl p-4 border border-white/5">
              <div className="flex items-center justify-between">
                <p className="text-slate-400 text-sm font-medium">Total</p>
                <MessageCircle className="w-5 h-5 text-slate-500" />
              </div>
              <p className="text-2xl font-bold text-white mt-1">{stats.total}</p>
            </div>
            <div className="bg-blue-500/10 backdrop-blur rounded-xl p-4 border border-blue-500/20">
              <div className="flex items-center justify-between">
                <p className="text-blue-400 text-sm font-medium">New</p>
                <AlertTriangle className="w-5 h-5 text-blue-400" />
              </div>
              <p className="text-2xl font-bold text-blue-400 mt-1">{stats.new}</p>
            </div>
            <div className="bg-amber-500/10 backdrop-blur rounded-xl p-4 border border-amber-500/20">
              <div className="flex items-center justify-between">
                <p className="text-amber-400 text-sm font-medium">In Progress</p>
                <Clock className="w-5 h-5 text-amber-400" />
              </div>
              <p className="text-2xl font-bold text-amber-400 mt-1">{stats.inProgress}</p>
            </div>
            <div className="bg-emerald-500/10 backdrop-blur rounded-xl p-4 border border-emerald-500/20">
              <div className="flex items-center justify-between">
                <p className="text-emerald-400 text-sm font-medium">Resolved</p>
                <CheckCircle className="w-5 h-5 text-emerald-400" />
              </div>
              <p className="text-2xl font-bold text-emerald-400 mt-1">{stats.resolved}</p>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex h-[calc(100vh-220px)]">
        {/* Tickets List */}
        <div className="w-full md:w-[380px] lg:w-[420px] border-r border-white/10 flex flex-col bg-slate-800/30">
          {/* Search & Filters */}
          <div className="p-4 space-y-3 border-b border-white/10">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search by ticket, location, phone..."
                className="w-full pl-10 pr-4 py-2.5 bg-slate-700/50 border border-white/10 rounded-xl text-white placeholder:text-slate-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500/50 text-sm"
              />
            </div>
            <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-thin">
              {['all', 'received', 'in_progress', 'resolved', 'closed'].map((status) => (
                <button
                  key={status}
                  onClick={() => setStatusFilter(status)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-all ${
                    statusFilter === status
                      ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/30'
                      : 'bg-slate-700/50 text-slate-400 hover:bg-slate-700 hover:text-white'
                  }`}
                >
                  {status === 'all' ? 'All Tickets' : statusConfig[status]?.label || status}
                </button>
              ))}
            </div>
          </div>

          {/* Tickets List */}
          <div className="flex-1 overflow-y-auto">
            {isLoading ? (
              <div className="flex flex-col items-center justify-center h-40 text-slate-400">
                <Loader2 className="w-8 h-8 text-blue-400 animate-spin mb-2" />
                <p className="text-sm">Loading tickets...</p>
              </div>
            ) : filteredReports.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-40 text-slate-400">
                <MessageCircle className="w-10 h-10 mb-3 opacity-30" />
                <p className="font-medium">No tickets found</p>
                <p className="text-xs mt-1">Try adjusting your filters</p>
              </div>
            ) : (
              <div className="divide-y divide-white/5">
                {filteredReports.map((report) => {
                  const ticketNum = getTicketNumber(report)
                  const category = categoryConfig[report.category] || { name: report.category, icon: '📋' }
                  const isSelected = (selectedTicket?.ticket_number || selectedTicket?.ticket) === ticketNum

                  return (
                    <button
                      key={report._id}
                      onClick={() => setSelectedTicket(report)}
                      className={`w-full p-4 text-left transition-all hover:bg-white/5 ${
                        isSelected 
                          ? 'bg-blue-500/10 border-l-4 border-l-blue-500' 
                          : 'border-l-4 border-l-transparent'
                      }`}
                    >
                      <div className="flex items-start gap-3">
                        {/* Category Icon */}
                        <div className={`flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center text-lg ${
                          isSelected ? 'bg-blue-500/20' : 'bg-slate-700/50'
                        }`}>
                          {category.icon}
                        </div>

                        {/* Content */}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="font-mono text-sm font-semibold text-blue-400">{ticketNum}</span>
                            <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${statusConfig[report.status]?.bgColor} ${statusConfig[report.status]?.color}`}>
                              {statusConfig[report.status]?.label || report.status}
                            </span>
                          </div>
                          <p className="text-white font-medium text-sm truncate">{category.name}</p>
                          <div className="flex items-center gap-1.5 mt-1">
                            <MapPin className="w-3 h-3 text-slate-500 flex-shrink-0" />
                            <p className="text-slate-400 text-xs truncate">
                              {report.area_text || 'Location not specified'}
                            </p>
                          </div>
                        </div>

                        {/* Meta */}
                        <div className="flex-shrink-0 text-right">
                          <span className={`inline-block px-1.5 py-0.5 rounded text-[10px] font-medium ${severityConfig[report.severity]?.bgColor || 'bg-slate-500/20'} ${severityConfig[report.severity]?.color || 'text-slate-400'}`}>
                            {severityConfig[report.severity]?.label || 'Medium'}
                          </span>
                          <p className="text-[11px] text-slate-500 mt-1.5">{getTimeAgo(report.created_at)}</p>
                        </div>
                      </div>
                    </button>
                  )
                })}
              </div>
            )}
          </div>
        </div>

        {/* Ticket Detail Panel */}
        <div className="hidden md:flex flex-1 flex-col bg-slate-900/50">
          {selectedTicket ? (
            <>
              {/* Detail Header */}
              <div className="p-6 border-b border-white/10 bg-slate-800/30">
                {/* Ticket Title Row */}
                <div className="flex items-start justify-between gap-4 mb-4">
                  <div className="flex items-center gap-3">
                    <div className="p-3 bg-blue-500/20 rounded-xl">
                      <span className="text-2xl">{categoryConfig[selectedTicket.category]?.icon || '📋'}</span>
                    </div>
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <h2 className="text-xl font-bold text-white font-mono">{getTicketNumber(selectedTicket)}</h2>
                        <span className={`px-2 py-1 rounded-lg text-xs font-semibold ${statusConfig[selectedTicket.status]?.bgColor} ${statusConfig[selectedTicket.status]?.color}`}>
                          {statusConfig[selectedTicket.status]?.label}
                        </span>
                      </div>
                      <p className="text-slate-300 font-medium">
                        {categoryConfig[selectedTicket.category]?.name || selectedTicket.category}
                      </p>
                    </div>
                  </div>
                  <a
                    href={`/track/${getTicketNumber(selectedTicket)}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1.5 px-3 py-2 bg-slate-700/50 hover:bg-slate-700 text-slate-300 hover:text-white rounded-lg text-sm transition-colors"
                  >
                    <ExternalLink className="w-4 h-4" />
                    Public View
                  </a>
                </div>

                {/* Info Grid */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                  {/* Left: Location & Time */}
                  <div className="bg-slate-700/30 rounded-xl p-4 space-y-3">
                    <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Report Details</h3>
                    <div className="flex items-start gap-3">
                      <MapPin className="w-4 h-4 text-blue-400 mt-0.5 flex-shrink-0" />
                      <div>
                        <p className="text-xs text-slate-500">Location</p>
                        <p className="text-sm text-white">{selectedTicket.area_text || 'Not specified'}</p>
                      </div>
                    </div>
                    <div className="flex items-start gap-3">
                      <Calendar className="w-4 h-4 text-blue-400 mt-0.5 flex-shrink-0" />
                      <div>
                        <p className="text-xs text-slate-500">Reported</p>
                        <p className="text-sm text-white">{formatDate(selectedTicket.created_at)}</p>
                      </div>
                    </div>
                    {selectedTicket.description && (
                      <div className="pt-2 border-t border-white/5">
                        <p className="text-xs text-slate-500 mb-1">Description</p>
                        <p className="text-sm text-slate-300">{selectedTicket.description}</p>
                      </div>
                    )}
                  </div>

                  {/* Right: Reporter Info */}
                  <div className="bg-slate-700/30 rounded-xl p-4 space-y-3">
                    <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Reporter Information</h3>
                    <div className="flex items-start gap-3">
                      <User className="w-4 h-4 text-emerald-400 mt-0.5 flex-shrink-0" />
                      <div>
                        <p className="text-xs text-slate-500">Name</p>
                        <p className="text-sm text-white">{selectedTicket.reporter_name || 'Anonymous'}</p>
                      </div>
                    </div>
                    <div className="flex items-start gap-3">
                      <Phone className="w-4 h-4 text-emerald-400 mt-0.5 flex-shrink-0" />
                      <div>
                        <p className="text-xs text-slate-500">Phone</p>
                        {selectedTicket.reporter_phone ? (
                          <a href={`tel:${selectedTicket.reporter_phone}`} className="text-sm text-blue-400 hover:text-blue-300">
                            {selectedTicket.reporter_phone}
                          </a>
                        ) : (
                          <p className="text-sm text-slate-500">Not provided</p>
                        )}
                      </div>
                    </div>
                    <div className="flex items-start gap-3">
                      <AlertTriangle className="w-4 h-4 text-amber-400 mt-0.5 flex-shrink-0" />
                      <div>
                        <p className="text-xs text-slate-500">Priority</p>
                        <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${severityConfig[selectedTicket.severity]?.bgColor || 'bg-slate-500/20'} ${severityConfig[selectedTicket.severity]?.color || 'text-slate-400'}`}>
                          {severityConfig[selectedTicket.severity]?.label || 'Medium'}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Assigned To Section */}
                {selectedTicket.assigned_to && (
                  <div className="mt-4 p-3 bg-purple-500/10 border border-purple-500/20 rounded-xl">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-purple-500/20 rounded-full flex items-center justify-center">
                        <Users className="w-5 h-5 text-purple-400" />
                      </div>
                      <div className="flex-1">
                        <p className="text-xs text-purple-400">Assigned To</p>
                        <p className="text-sm font-medium text-white">{selectedTicket.assigned_to}</p>
                      </div>
                      <button
                        onClick={() => setShowAssignModal(true)}
                        className="text-xs text-purple-400 hover:text-purple-300"
                      >
                        Reassign
                      </button>
                    </div>
                  </div>
                )}

                {/* Status Actions */}
                <div className="flex flex-wrap gap-2 mt-4 pt-4 border-t border-white/10">
                  <span className="text-xs text-slate-500 py-2 mr-2">Update Status:</span>
                  {selectedTicket.status === 'received' && (
                    <button
                      onClick={() => handleStatusUpdate('under_review')}
                      disabled={updatingStatus}
                      className="flex items-center gap-1.5 px-3 py-2 bg-amber-500/20 text-amber-400 rounded-lg text-sm font-medium hover:bg-amber-500/30 transition-all disabled:opacity-50"
                    >
                      <Eye className="w-4 h-4" />
                      Start Review
                    </button>
                  )}
                  {['received', 'under_review'].includes(selectedTicket.status) && !selectedTicket.assigned_to && (
                    <button
                      onClick={() => setShowAssignModal(true)}
                      disabled={updatingStatus}
                      className="flex items-center gap-1.5 px-3 py-2 bg-purple-500/20 text-purple-400 rounded-lg text-sm font-medium hover:bg-purple-500/30 transition-all disabled:opacity-50"
                    >
                      <Users className="w-4 h-4" />
                      Assign Team Member
                    </button>
                  )}
                  {['technician_assigned', 'under_review'].includes(selectedTicket.status) && (
                    <button
                      onClick={() => handleStatusUpdate('in_progress')}
                      disabled={updatingStatus}
                      className="flex items-center gap-1.5 px-3 py-2 bg-cyan-500/20 text-cyan-400 rounded-lg text-sm font-medium hover:bg-cyan-500/30 transition-all disabled:opacity-50"
                    >
                      <Wrench className="w-4 h-4" />
                      Start Work
                    </button>
                  )}
                  {['in_progress', 'technician_assigned'].includes(selectedTicket.status) && (
                    <button
                      onClick={() => handleStatusUpdate('resolved')}
                      disabled={updatingStatus}
                      className="flex items-center gap-1.5 px-3 py-2 bg-emerald-500/20 text-emerald-400 rounded-lg text-sm font-medium hover:bg-emerald-500/30 transition-all disabled:opacity-50"
                    >
                      <CheckCircle className="w-4 h-4" />
                      Mark Resolved
                    </button>
                  )}
                  {selectedTicket.status === 'resolved' && (
                    <button
                      onClick={() => handleStatusUpdate('closed')}
                      disabled={updatingStatus}
                      className="flex items-center gap-1.5 px-3 py-2 bg-slate-500/20 text-slate-400 rounded-lg text-sm font-medium hover:bg-slate-500/30 transition-all disabled:opacity-50"
                    >
                      <XCircle className="w-4 h-4" />
                      Close Ticket
                    </button>
                  )}
                  {updatingStatus && <Loader2 className="w-5 h-5 text-blue-400 animate-spin ml-2" />}
                </div>
              </div>

              {/* Premium Chat Section - iOS iMessage Style */}
              <div className="flex-1 flex flex-col min-h-0 bg-[#000000]">
                {/* Chat Header - iOS Style */}
                <div className="relative px-4 py-4 bg-[#1c1c1e]/95 backdrop-blur-xl border-b border-white/5">
                  <div className="flex items-center justify-center">
                    <div className="flex flex-col items-center">
                      {/* Avatar */}
                      <div className="relative mb-2">
                        <div className="w-14 h-14 bg-gradient-to-br from-green-400 via-emerald-500 to-teal-600 rounded-full flex items-center justify-center shadow-lg shadow-emerald-500/30">
                          <span className="text-xl font-bold text-white">
                            {(selectedTicket.reporter_name || 'R').charAt(0).toUpperCase()}
                          </span>
                        </div>
                        <div className="absolute -bottom-0.5 -right-0.5 w-4 h-4 bg-green-500 rounded-full border-2 border-[#1c1c1e]"></div>
                      </div>
                      <h3 className="text-base font-semibold text-white">
                        {selectedTicket.reporter_name || 'Reporter'}
                      </h3>
                      <p className="text-xs text-[#8e8e93]">
                        {selectedTicket.reporter_phone ? `📱 ${selectedTicket.reporter_phone}` : 'Water Issue Report'}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Messages Container - iOS Dark Mode */}
                <div 
                  className="flex-1 overflow-y-auto px-3 py-4"
                  style={{ 
                    background: '#000000',
                  }}
                >
                  {messages.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-full">
                      <div className="w-20 h-20 bg-[#1c1c1e] rounded-full flex items-center justify-center mb-4 shadow-xl">
                        <MessageCircle className="w-10 h-10 text-[#8e8e93]" />
                      </div>
                      <p className="text-lg font-semibold text-white mb-1">No Messages Yet</p>
                      <p className="text-sm text-[#8e8e93] text-center max-w-[240px]">
                        Start a conversation with the reporter about ticket {getTicketNumber(selectedTicket)}
                      </p>
                    </div>
                  ) : (
                    <div className="space-y-1">
                      {messages.map((message, index) => {
                        const isStaff = message.sender_type === 'staff'
                        const prevMessage = messages[index - 1]
                        const nextMessage = messages[index + 1]
                        const showDate = index === 0 || 
                          new Date(message.created_at).toDateString() !== 
                          new Date(prevMessage?.created_at).toDateString()
                        const isFirstInGroup = !prevMessage || prevMessage.sender_type !== message.sender_type
                        const isLastInGroup = !nextMessage || nextMessage.sender_type !== message.sender_type
                        
                        // Determine bubble border radius based on position in group
                        const getBubbleRadius = () => {
                          if (isStaff) {
                            if (isFirstInGroup && isLastInGroup) return 'rounded-[22px] rounded-br-[6px]'
                            if (isFirstInGroup) return 'rounded-[22px] rounded-br-[6px]'
                            if (isLastInGroup) return 'rounded-[22px] rounded-tr-[6px] rounded-br-[6px]'
                            return 'rounded-[22px] rounded-r-[6px]'
                          } else {
                            if (isFirstInGroup && isLastInGroup) return 'rounded-[22px] rounded-bl-[6px]'
                            if (isFirstInGroup) return 'rounded-[22px] rounded-bl-[6px]'
                            if (isLastInGroup) return 'rounded-[22px] rounded-tl-[6px] rounded-bl-[6px]'
                            return 'rounded-[22px] rounded-l-[6px]'
                          }
                        }
                        
                        return (
                          <div key={message._id || index}>
                            {/* Date Separator - iOS Style */}
                            {showDate && (
                              <div className="flex justify-center my-4">
                                <span className="px-3 py-1 bg-[#1c1c1e] rounded-full text-[11px] text-[#8e8e93] font-medium shadow-sm">
                                  {formatShortDate(message.created_at) || 'Today'}
                                </span>
                              </div>
                            )}
                            
                            {/* Message Row */}
                            <div className={`flex ${isStaff ? 'justify-end' : 'justify-start'} ${isFirstInGroup ? 'mt-3' : 'mt-0.5'}`}>
                              <div className={`max-w-[75%] flex flex-col ${isStaff ? 'items-end' : 'items-start'}`}>
                                {/* Message Bubble */}
                                <div
                                  className={`relative px-4 py-2 ${getBubbleRadius()} ${
                                    isStaff
                                      ? 'bg-[#0b93f6] text-white'
                                      : 'bg-[#262628] text-white'
                                  }`}
                                  style={{
                                    boxShadow: isStaff 
                                      ? '0 1px 2px rgba(11, 147, 246, 0.3)' 
                                      : '0 1px 2px rgba(0,0,0,0.3)'
                                  }}
                                >
                                  <p className="text-[16px] leading-[22px] whitespace-pre-wrap break-words">
                                    {message.content}
                                  </p>
                                </div>
                                
                                {/* Timestamp & Read Receipt - Only show on last message in group */}
                                {isLastInGroup && (
                                  <div className={`flex items-center gap-1 mt-1 px-2 ${isStaff ? 'flex-row-reverse' : ''}`}>
                                    <span className="text-[11px] text-[#8e8e93]">
                                      {new Date(message.created_at).toLocaleTimeString('en-US', {
                                        hour: 'numeric',
                                        minute: '2-digit',
                                        hour12: true
                                      })}
                                    </span>
                                    {isStaff && (
                                      <span className="text-[11px] text-[#0b93f6] font-medium">Delivered</span>
                                    )}
                                  </div>
                                )}
                              </div>
                            </div>
                          </div>
                        )
                      })}
                      <div ref={messagesEndRef} />
                    </div>
                  )}
                </div>

                {/* Message Input - iOS Style */}
                <div className="px-3 py-2 bg-[#1c1c1e] border-t border-white/5">
                  <form onSubmit={handleSendMessage} className="flex items-center gap-2">
                    {/* Input Field */}
                    <div className="flex-1 relative">
                      <input
                        type="text"
                        value={newMessage}
                        onChange={(e) => setNewMessage(e.target.value)}
                        placeholder={selectedTicket.status === 'closed' ? 'Ticket closed' : 'iMessage'}
                        className="w-full px-4 py-2.5 bg-[#262628] border border-[#3a3a3c] rounded-full text-white text-[16px] placeholder:text-[#8e8e93] focus:outline-none focus:border-[#0b93f6] disabled:opacity-40 transition-colors"
                        disabled={selectedTicket.status === 'closed'}
                      />
                    </div>
                    
                    {/* Send Button - iOS Blue Arrow */}
                    <button
                      type="submit"
                      disabled={!newMessage.trim() || sending || selectedTicket.status === 'closed'}
                      className={`w-9 h-9 rounded-full flex items-center justify-center transition-all transform ${
                        newMessage.trim() && !sending
                          ? 'bg-[#0b93f6] scale-100 hover:scale-105 active:scale-95'
                          : 'bg-[#262628] scale-90 opacity-50'
                      }`}
                    >
                      {sending ? (
                        <Loader2 className="w-4 h-4 text-white animate-spin" />
                      ) : (
                        <svg 
                          className={`w-4 h-4 ${newMessage.trim() ? 'text-white' : 'text-[#8e8e93]'}`} 
                          fill="currentColor" 
                          viewBox="0 0 24 24"
                        >
                          <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
                        </svg>
                      )}
                    </button>
                  </form>
                  
                  {/* iOS Safe Area */}
                  <div className="h-1"></div>
                </div>
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center">
                <div className="p-6 bg-slate-700/30 rounded-3xl inline-block mb-4">
                  <MessageCircle className="w-12 h-12 text-slate-500" />
                </div>
                <h3 className="text-lg font-semibold text-white mb-1">Select a Ticket</h3>
                <p className="text-slate-400 text-sm max-w-xs mx-auto">
                  Choose a ticket from the list to view details and respond to the reporter
                </p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Assign Team Member Modal */}
      {showAssignModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-800 rounded-2xl w-full max-w-md shadow-2xl border border-white/10">
            {/* Modal Header */}
            <div className="p-6 border-b border-white/10">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2.5 bg-purple-500/20 rounded-xl">
                    <Users className="w-5 h-5 text-purple-400" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-white">Assign Team Member</h3>
                    <p className="text-sm text-slate-400">Select who should handle this ticket</p>
                  </div>
                </div>
                <button
                  onClick={() => {
                    setShowAssignModal(false)
                    setSelectedTechnician('')
                  }}
                  className="p-2 hover:bg-white/10 rounded-lg transition-colors"
                >
                  <XCircle className="w-5 h-5 text-slate-400" />
                </button>
              </div>
            </div>

            {/* Team Members List */}
            <div className="p-4 max-h-96 overflow-y-auto">
              {technicians.length > 0 ? (
                <div className="space-y-2">
                  {technicians.map((tech) => (
                    <button
                      key={tech._id}
                      onClick={() => setSelectedTechnician(tech.name)}
                      className={`w-full p-4 rounded-xl transition-all flex items-center gap-4 ${
                        selectedTechnician === tech.name
                          ? 'bg-purple-500/20 border-2 border-purple-500'
                          : 'bg-slate-700/50 hover:bg-slate-700 border-2 border-transparent'
                      }`}
                    >
                      <div className={`w-12 h-12 rounded-full flex items-center justify-center text-lg font-bold ${
                        tech.status === 'available' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-amber-500/20 text-amber-400'
                      }`}>
                        {tech.name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)}
                      </div>
                      <div className="flex-1 text-left">
                        <p className="font-medium text-white">{tech.name}</p>
                        <p className="text-sm text-slate-400 capitalize">{tech.role?.replace('_', ' ') || 'Technician'}</p>
                        {tech.phone && (
                          <p className="text-xs text-slate-500">{tech.phone}</p>
                        )}
                      </div>
                      <div className="flex flex-col items-end gap-1">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          tech.status === 'available'
                            ? 'bg-emerald-500/20 text-emerald-400'
                            : 'bg-amber-500/20 text-amber-400'
                        }`}>
                          {tech.status === 'available' ? '● Available' : '● Busy'}
                        </span>
                        {selectedTechnician === tech.name && (
                          <CheckCircle className="w-5 h-5 text-purple-400" />
                        )}
                      </div>
                    </button>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <Users className="w-12 h-12 text-slate-500 mx-auto mb-3" />
                  <p className="text-slate-400">No team members found</p>
                  <p className="text-sm text-slate-500 mt-1">Add technicians in the system settings</p>
                </div>
              )}
            </div>

            {/* Modal Actions */}
            <div className="p-4 border-t border-white/10 flex gap-3">
              <button
                onClick={() => {
                  setShowAssignModal(false)
                  setSelectedTechnician('')
                }}
                className="flex-1 px-4 py-3 bg-slate-700 text-white rounded-xl font-medium hover:bg-slate-600 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => handleAssignTechnician(selectedTechnician)}
                disabled={!selectedTechnician || updatingStatus}
                className="flex-1 px-4 py-3 bg-purple-600 text-white rounded-xl font-medium hover:bg-purple-500 transition-colors disabled:opacity-50 disabled:hover:bg-purple-600 flex items-center justify-center gap-2"
              >
                {updatingStatus ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Assigning...
                  </>
                ) : (
                  <>
                    <Users className="w-4 h-4" />
                    Assign Ticket
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
